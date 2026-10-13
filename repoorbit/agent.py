"""Token-frugal, offline repository discovery API for AI agents.

No network, no dependencies, no fabricated capability/cost/safety claims.
A compact JSON result is returned; large upstream documents stay out of context.
"""
from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path
import re
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
WORD = re.compile(r"[a-z0-9]+", re.I)
STOP = {"github", "com", "repo", "repository", "repositories", "the", "for", "and", "with"}
MAX_LIMIT = 20
MAX_QUERY = 200
MAX_OFFSET = 10000


def tokenize(text: str) -> tuple[str, ...]:
    """Split camel case, punctuation and separators without network/LLM calls."""
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text)
    return tuple(WORD.findall(text.casefold()))


def _canonical(text: str) -> str:
    value = text.strip().removeprefix("https://github.com/").rstrip("/")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", value):
        raise ValueError("expected a GitHub owner/repository path or URL")
    return value.casefold()


@lru_cache(maxsize=1)
def _load() -> dict[str, dict[str, Any]]:
    """Index on first call, once per process. No full README reads."""
    table: dict[str, dict[str, Any]] = {}
    source_path = ROOT / "data" / "sources.json"
    source_data = json.loads(source_path.read_text(encoding="utf-8"))
    for source in source_data["sources"]:
        key = _canonical(source["repository"])
        table[key] = {
            "r": source["repository"], "role": "catalog", "v": "exists",
            "tags": source["topics"], "source": None,
            "catalog_kind": source["type"],
            "evidence_date": source["verified_at"],
        }
    for line in (ROOT / "data" / "repositories.jsonl").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        project = json.loads(line)
        key = _canonical(project["full_name"])
        current = table.get(key, {})
        table[key] = {
            "r": project["full_name"], "role": "project", "v": "exists",
            "tags": project["topics"], "source": current.get("source"),
            "catalog_kind": current.get("catalog_kind"),
            "evidence_date": project["last_verified_at"],
            "cost": project["cost"], "working": project["functional_test"],
        }
    for path in sorted((ROOT / "data" / "discoveries").glob("*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            edge = json.loads(line)
            key = _canonical(edge["target_full_name"])
            existing = table.get(key)
            if existing is None:
                existing = {
                    "r": edge["target_full_name"], "role": "reference",
                    "v": "not_checked", "tags": [], "source": [],
                }
                table[key] = existing
            if existing.get("source") is None:
                existing["source"] = []
            pointer = {
                "s": edge["source_id"], "line": edge["source_line"],
                "sha": edge["source_blob_sha"],
            }
            if pointer not in existing["source"]:
                existing["source"].append(pointer)
    return table


def _score(query: tuple[str, ...], record: dict[str, Any]) -> int:
    slug = record["r"].casefold()
    tokens = set(tokenize(record["r"] + " " + " ".join(record["tags"])))
    terms = [x for x in query if x not in STOP] or list(query)
    if not terms:
        return 0
    hits = sum(1 for term in terms if term in tokens)
    if hits == 0:
        return 0
    score = hits * 10 - (len(terms) - hits) * 3
    if len(terms) == hits:
        score += 7
    if slug == " ".join(query) or slug == "/".join(query):
        score += 50
    if record["v"] == "exists":
        score += 2
    return max(0, score)


def _tiny(record: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {"r": record["r"], "role": record["role"], "v": record["v"]}
    if record.get("tags"):
        result["tags"] = record["tags"]
    return result


def search(q: str, limit: int = 5, offset: int = 0, role: str | None = None) -> dict:
    """Deterministic lexical search; deliberately not semantic or functional validation."""
    if not isinstance(q, str) or not q.strip() or len(q) > MAX_QUERY:
        raise ValueError("q must be 1..200 characters")
    if type(limit) is not int or not 1 <= limit <= MAX_LIMIT:
        raise ValueError("limit must be 1..20")
    if type(offset) is not int or not 0 <= offset <= MAX_OFFSET:
        raise ValueError("offset must be 0..10000")
    if role not in (None, "project", "catalog", "reference"):
        raise ValueError("role must be project, catalog or reference")
    terms = tokenize(q)
    scored = []
    for record in _load().values():
        if role is not None and record["role"] != role:
            continue
        relevance = _score(terms, record)
        if relevance:
            scored.append((relevance, record))
    scored.sort(key=lambda item: (-item[0], item[1]["r"].casefold()))
    chosen = scored[offset:offset + limit]
    return {
        "q": q, "n": len(scored), "offset": offset,
        "items": [_tiny(row) for _, row in chosen],
        "more": offset + limit < len(scored),
        "semantics": "lexical_not_functionally_verified",
    }


def resolve(repo: str) -> dict:
    """Exact lookup by GitHub owner/repo or URL, no scanning by the agent."""
    key = _canonical(repo)
    row = _load().get(key)
    if row is None:
        return {"found": False, "r": key, "note": "not_in_seed_or_discoveries"}
    result = dict(row)
    result["found"] = True
    result["url"] = "https://github.com/" + row["r"]
    if row["v"] == "not_checked":
        result["warning"] = "upstream_link_only_not_validated"
    elif row["role"] == "project":
        result["warning"] = "existence_verified_not_function_or_cost"
    return result


def stats() -> dict:
    records = list(_load().values())
    return {
        "unique": len(records),
        "catalogs": sum(x["role"] == "catalog" for x in records),
        "verified_project_seeds": sum(x["role"] == "project" for x in records),
        "unverified_only": sum(x["v"] == "not_checked" for x in records),
        "working_verified": sum(x.get("working") == "passed" for x in records),
        "cost_free_verified": sum(x.get("cost") == "free_verified" for x in records),
        "method": "offline_seed_and_discovery_refs",
    }


def call(tool: str, args: dict | None = None) -> dict:
    """Pure function entry point for other agent integrations."""
    args = args or {}
    if not isinstance(args, dict):
        raise ValueError("arguments must be an object")
    if tool == "search":
        if set(args) - {"q", "limit", "offset", "role"}:
            raise ValueError("unrecognized search arguments")
        return search(**args)
    if tool == "resolve":
        if set(args) != {"repo"}:
            raise ValueError("resolve requires repo")
        return resolve(**args)
    if tool == "stats":
        if args:
            raise ValueError("stats does not take arguments")
        return stats()
    raise ValueError("unknown tool")
