"""Evidence-aware subject classification for AI agents; offline, no models/APIs.

The taxonomy is an editorial map for 34 individually checked editorial seed subjects, plus
conservative slug-keyword *hints* for discovered references. An unclassified
record is a valid outcome; keyword matching is never a software capability test.
"""
from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path
import re
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
TAXONOMY = ROOT / "data" / "taxonomy.json"
MAX_RESULTS = 20
MAX_OFFSET = 10000


def normalize(value: str) -> str:
    folded = unicodedata.normalize("NFKD", value.casefold())
    folded = "".join(c for c in folded if not unicodedata.combining(c))
    folded = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", folded)
    return " ".join(re.findall(r"[a-z0-9]+", folded))


@lru_cache(maxsize=1)
def registry() -> dict:
    data = json.loads(TAXONOMY.read_text(encoding="utf-8"))
    if data.get("schema_version") != "1.0.0":
        raise ValueError("unsupported taxonomy version")
    subjects = data.get("categories")
    if not isinstance(subjects, list) or len(subjects) < 3:
        raise ValueError("invalid taxonomy categories")
    names = set()
    triggers = {}
    for item in subjects:
        name = item.get("id")
        if not isinstance(name, str) or not re.fullmatch(r"[a-z][a-z0-9-]+", name):
            raise ValueError("invalid category id")
        if name in names:
            raise ValueError("duplicate category")
        names.add(name)
        if not item.get("en") or not item.get("es"):
            raise ValueError("bilingual display names required")
        words = item.get("triggers")
        if not isinstance(words, list) or not words:
            raise ValueError("each category needs lexical keywords")
        for word in words:
            token = normalize(word)
            if not token or token != word or token in triggers:
                raise ValueError("duplicate or non-normalized lexical keyword")
            triggers[token] = name
    if data.get("unknown_id") != "unclassified" or "unclassified" in names:
        raise ValueError("invalid abstention marker")
    for key, name in data.get("seed_subjects", {}).items():
        from .agent import _load
        seed = _load().get(key)
        if (name not in names or key != key.casefold() or
                seed is None or seed["role"] not in ("catalog", "project")):
            raise ValueError("untrusted editorial label or non-seed target")
    if len(data["seed_subjects"]) != 34:
        raise ValueError("only the 34 checked seed subjects are editorial")
    formats = data.get("format_hints")
    if not isinstance(formats, dict):
        raise ValueError("missing format hints")
    for terms in formats.values():
        if not isinstance(terms, list) or any(normalize(w) != w for w in terms):
            raise ValueError("format keyword must be normalized")
    return data


def classify_record(row: dict, data: dict | None = None) -> dict:
    """Return a narrow editorial label, keyword hint, or explicit abstention."""
    data = data or registry()
    slug = row["r"]
    key = slug.casefold()
    if key in data["seed_subjects"]:
        return {
            "category": data["seed_subjects"][key],
            "basis": "editorial_seed_subject",
            "matched": [],
            "format_hint": "known_catalog" if row["role"] == "catalog" else "known_project",
        }
    # A reviewed immutable README statement outranks filename keywords.
    # It still describes a self-reported subject, not demonstrated behavior.
    from .topic_evidence import load as reviewed_topics
    fact = reviewed_topics().get(key)
    if fact is not None:
        return {
            "category": fact["category"],
            "basis": "readme_topic_evidence",
            "matched": [fact["summary"]],
            "format_hint": "unknown",
        }
    # Avoid interpreting owner names as the subject of a project.
    repo_name = slug.split("/", 1)[-1]
    words = " " + normalize(repo_name) + " "
    hits: dict[str, tuple[int, str]] = {}
    for cat in data["categories"]:
        for trigger in cat["triggers"]:
            if " " + trigger + " " not in words:
                continue
            specificity = len(trigger.split())
            prior = hits.get(cat["id"])
            if prior is None or specificity > prior[0]:
                hits[cat["id"]] = (specificity, trigger)
    if hits:
        strength = max(info[0] for info in hits.values())
        possible = sorted(k for k, info in hits.items() if info[0] == strength)
        if len(possible) == 1:
            category = possible[0]
            basis = "slug_keyword_hint"
            matched = [hits[category][1]]
        else:
            category = "unclassified"
            basis = "ambiguous_slug_keywords"
            matched = possible[:4]
    else:
        category = "unclassified"
        basis = "no_subject_evidence"
        matched = []
    fmt = "unknown"
    for group, keys in data["format_hints"].items():
        if any(" " + token + " " in words for token in keys):
            fmt = group
            break
    return {"category": category, "basis": basis, "matched": matched, "format_hint": fmt}


@lru_cache(maxsize=1)
def index() -> dict[str, list[tuple[dict, dict]]]:
    from .agent import _load
    data = registry()
    result = {c["id"]: [] for c in data["categories"]}
    result["unclassified"] = []
    for record in sorted(_load().values(), key=lambda r: r["r"].casefold()):
        category = classify_record(record, data)
        result[category["category"]].append((record, category))
    return result


def categories() -> dict:
    data = registry()
    results = index()
    return {
        "v": 1, "categories": [
            {"id": cat["id"], "en": cat["en"], "es": cat["es"],
             "n": len(results[cat["id"]])}
            for cat in data["categories"]
        ] + [{"id": "unclassified", "en": "Unclassified", "es": "Sin clasificar",
              "n": len(results["unclassified"])}],
        "total": sum(len(x) for x in results.values()),
        "policy": "editorial_seeds_or_lexical_hints_no_capability_verification",
    }


def classify(repo: str) -> dict:
    from .agent import _canonical, _load
    if not isinstance(repo, str) or not repo or len(repo) > 240:
        raise ValueError("repo must be a GitHub slug or canonical URL")
    key = _canonical(repo)
    row = _load().get(key)
    if row is None:
        return {"found": False, "status": "not_in_corpus"}
    result = classify_record(row)
    from .topic_evidence import load as reviewed_topics, evidence_pointer
    evidence = reviewed_topics().get(key)
    return {
        "found": True, "r": row["r"], "role": row["role"], "v": row["v"],
        **result,
        **({"readme_evidence": evidence_pointer(evidence)} if evidence else {}),
        "source_catalogs": sorted({x["s"] for x in (row.get("source") or [])}),
        "notice": "subject_label_not_functional_or_cost_verification",
    }


def browse(category: str, limit: int = 5, offset: int = 0,
           verified_only: bool = False, source: str | None = None) -> dict:
    if not isinstance(category, str) or category not in index():
        raise ValueError("unknown category")
    if type(limit) is not int or not 1 <= limit <= MAX_RESULTS:
        raise ValueError("limit must be 1..20")
    if type(offset) is not int or not 0 <= offset <= MAX_OFFSET:
        raise ValueError("offset must be 0..10000")
    if type(verified_only) is not bool:
        raise ValueError("verified_only must be boolean")
    if source is not None:
        approved = json.loads((ROOT / "data" / "feeds.json").read_text(encoding="utf-8"))
        ids = {item["id"] for item in approved["sources"] if item["enabled"] is True}
        if not isinstance(source, str) or source not in ids:
            raise ValueError("source must be a currently approved discovery feed ID")
    records = index()[category]
    if source is not None:
        records = [
            (row, cat) for row, cat in records
            if any(pointer["s"] == source for pointer in (row.get("source") or []))
        ]
    if verified_only:
        records = [x for x in records if x[0]["v"] == "exists"]
    selected = records[offset:offset + limit]
    return {
        "category": category, "n": len(records), "offset": offset,
        "source": source,
        "items": [
            {"r": row["r"], "role": row["role"], "v": row["v"],
             "basis": cat["basis"]}
            for row, cat in selected
        ],
        "more": offset + limit < len(records),
        "notice": "classification_is_subject_hint_not_functional_validation",
    }
