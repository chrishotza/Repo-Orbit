"""Evidence-linked bilingual intent routing for the eight curated project seeds.

Not an LLM, embedding model, natural-language guarantee or functional test.
Only explicit aliases can produce results. Unsupported requests fail closed.
"""
from __future__ import annotations

from functools import lru_cache
import json
import re
import unicodedata

from .agent import ROOT, _load, MAX_QUERY

FREE_PHRASES = (
    "gratis", "gratuito", "gratuita", "sin pagar", "sin costo",
    "sin costes", "free", "without paying", "no paid", "free of charge",
)
MAX_ITEMS = 10


def normalize(value: str) -> str:
    """Lowercase, remove accents and punctuation, preserve word boundaries."""
    folded = unicodedata.normalize("NFKD", value.casefold())
    ascii_text = "".join(ch for ch in folded if not unicodedata.combining(ch))
    return " ".join(re.findall(r"[a-z0-9]+", ascii_text))


@lru_cache(maxsize=1)
def _registry() -> dict:
    data = json.loads((ROOT / "data" / "intent_map.json").read_text(encoding="utf-8"))
    if data.get("schema_version") != "0.1.0":
        raise ValueError("unsupported intent registry version")
    project_seeds = _load()
    seen_intents = set()
    for item in data.get("intents", []):
        task_id = item.get("id")
        if not isinstance(task_id, str) or not task_id or task_id in seen_intents:
            raise ValueError("invalid or duplicate intent")
        seen_intents.add(task_id)
        if not isinstance(item.get("aliases"), list) or not item["aliases"]:
            raise ValueError("intent aliases missing")
        if not isinstance(item.get("repositories"), list) or not item["repositories"]:
            raise ValueError("intent project candidates missing")
        for phrase in item["aliases"]:
            if not isinstance(phrase, str) or len(normalize(phrase)) < 3:
                raise ValueError("invalid intent alias")
        for repo in item["repositories"]:
            if not isinstance(repo, str) or repo.casefold() not in data.get("repositories", {}):
                raise ValueError("missing upstream evidence for intent candidate")
            seed = project_seeds.get(repo.casefold())
            if seed is None or seed["role"] != "project" or seed["v"] != "exists":
                raise ValueError("intent points outside individually checked project seeds")
    for key, fact in data.get("repositories", {}).items():
        if key != fact.get("repo", "").casefold():
            raise ValueError("mismatched intent project key")
        if fact.get("evidence_type") != "upstream_documentation":
            raise ValueError("unsupported evidence type")
        if not re.fullmatch(r"[0-9a-f]{40}", fact.get("readme_blob_sha", "")):
            raise ValueError("upstream evidence missing blob identifier")
        if fact.get("cost") != "unknown" or fact.get("tested") is not False:
            raise ValueError("intent map must not claim independent cost or execution verification")
        branch = fact.get("readme_branch")
        if branch not in ("main", "master"):
            raise ValueError("upstream README branch missing or unsupported")
        if fact.get("readme_url") != f"https://github.com/{fact['repo']}/blob/{branch}/README.md":
            raise ValueError("untrusted or inconsistent evidence URL")
    return data


def recommend(q: str, limit: int = 5, strict_free: bool = False) -> dict:
    """Route known EN/ES intents without inventing unknown capabilities or free tiers.

    strict_free=True requires independently verified no-cost execution evidence.
    Since the current corpus has none, strict-free queries return zero candidates.
    """
    if not isinstance(q, str) or not q.strip() or len(q) > MAX_QUERY:
        raise ValueError("q must be 1..200 characters")
    if type(limit) is not int or not 1 <= limit <= MAX_ITEMS:
        raise ValueError("limit must be 1..10")
    if type(strict_free) is not bool:
        raise ValueError("strict_free must be boolean")
    query = normalize(q)
    padded = " " + query + " "
    requires_free = any(" " + needle + " " in padded for needle in FREE_PHRASES)
    data = _registry()
    hits = []
    for task in data["intents"]:
        matched = [
            normalize(alias) for alias in task["aliases"]
            if " " + normalize(alias) + " " in padded
        ]
        if matched:
            longest = max(matched, key=lambda a: (len(a.split()), len(a)))
            hits.append((len(longest.split()), len(longest), task["id"], task))
    hits.sort(key=lambda x: (-x[0], -x[1], x[2]))
    items, seen = [], set()
    for _, _, _, task in hits:
        for repo in task["repositories"]:
            key = repo.casefold()
            if key in seen:
                continue
            seen.add(key)
            fact = data["repositories"][key]
            # Intentionally no "free" promotion from documentation or a public URL.
            if strict_free:
                continue
            record = _load()[key]
            items.append({
                "r": fact["repo"],
                "why": fact["why"],
                "ev": "readme@" + fact["readme_blob_sha"][:10],
                "v": record["v"],
                "cost": "unknown",
                "tested": False,
            })
    returned = items[:limit]
    return {
        "intents": [item[2] for item in hits],
        "n": 0 if strict_free else len(items),
        "items": returned,
        "more": not strict_free and len(items) > limit,
        "free_requested": requires_free or strict_free,
        "free_verified": False,
        "warning": (
            "no_verified_free_candidates" if strict_free else
            "cost_not_verified" if requires_free and items else
            "no_curated_intent_match" if not hits else
            "documented_capabilities_not_functionally_tested"
        ),
        "method": "curated_bilingual_aliases_v0.1",
    }
