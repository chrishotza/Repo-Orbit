"""Conservative EN/ES topical phrase routing, standard library only.

This maps user wording to a topic ID. It DOES NOT semantically understand
requests or claim repository functionality. Unknown/ambiguous wording abstains.
"""
from __future__ import annotations

from functools import lru_cache
import json
import re
import unicodedata

from .agent import ROOT
from .taxonomy import registry


def normalize(text: str) -> str:
    deaccent = unicodedata.normalize("NFKD", text.casefold())
    return " ".join(re.findall(
        r"[a-z0-9]+",
        "".join(c for c in deaccent if not unicodedata.combining(c)),
    ))


@lru_cache(maxsize=1)
def aliases() -> dict[str, tuple[str, ...]]:
    raw = json.loads((ROOT / "data/topic_aliases.json").read_text(encoding="utf-8"))
    if raw.get("v") != 1:
        raise ValueError("unsupported bilingual routing table")
    categories = {x["id"] for x in registry()["categories"]}
    table = raw.get("aliases")
    if not isinstance(table, dict) or set(table) != categories:
        raise ValueError("routing table must cover all controlled categories")
    unique = {}
    result = {}
    for category, phrases in table.items():
        if not isinstance(phrases, list) or not 2 <= len(phrases) <= 30:
            raise ValueError("invalid routing phrases")
        normalized = []
        for phrase in phrases:
            if (not isinstance(phrase, str) or not 2 <= len(phrase) <= 80
                    or phrase != normalize(phrase)):
                raise ValueError("routing phrase must be normalized")
            if phrase in unique and unique[phrase] != category:
                raise ValueError("cross-category alias collision")
            if phrase in normalized:
                raise ValueError("duplicate routing phrase")
            unique[phrase] = category
            normalized.append(phrase)
        result[category] = tuple(normalized)
    return result


def route_topic(q: str) -> dict:
    if not isinstance(q, str) or not q.strip() or len(q) > 200:
        raise ValueError("query must be 1..200 characters")
    normalized = " " + normalize(q) + " "
    hits = {}
    for category, phrases in aliases().items():
        matched = [phrase for phrase in phrases if " " + phrase + " " in normalized]
        if matched:
            best = max(matched, key=lambda s: (len(s.split()), len(s)))
            hits[category] = {"phrase": best, "score": len(best.split())}
    if not hits:
        return {"found": False, "status": "no_supported_phrase",
                "category": None, "semantics": "controlled_phrase_only"}
    high = max(v["score"] for v in hits.values())
    winners = sorted(x for x, v in hits.items() if v["score"] == high)
    if len(winners) != 1:
        return {"found": False, "status": "ambiguous_supported_phrases",
                "category": None, "candidates": winners,
                "semantics": "controlled_phrase_only"}
    winner = winners[0]
    return {"found": True, "category": winner, "basis": "curated_bilingual_phrase",
            "matched": hits[winner]["phrase"],
            "semantics": "controlled_phrase_only_not_semantic_search",
            "notice": "Topic routing alone does not prove any repository works or is free."}
