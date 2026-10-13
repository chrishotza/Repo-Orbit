"""Compact, offline listing of known repositories by GitHub owner."""
from __future__ import annotations

from functools import lru_cache
import re

from .agent import _load


@lru_cache(maxsize=1)
def _owners() -> dict[str, list[dict]]:
    owners = {}
    for record in _load().values():
        owner = record["r"].split("/", 1)[0].casefold()
        owners.setdefault(owner, []).append(record)
    for items in owners.values():
        items.sort(key=lambda x: x["r"].casefold())
    return owners


def owner_repos(owner: str, limit: int = 5, offset: int = 0,
                verified_only: bool = False) -> dict:
    if not isinstance(owner, str) or not re.fullmatch(
        r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})", owner
    ):
        raise ValueError("owner must be a simple GitHub login")
    if type(limit) is not int or not 1 <= limit <= 20:
        raise ValueError("limit must be 1..20")
    if type(offset) is not int or not 0 <= offset <= 1_000_000:
        raise ValueError("offset must be 0..1000000")
    if type(verified_only) is not bool:
        raise ValueError("verified_only must be boolean")
    records = _owners().get(owner.casefold(), [])
    if verified_only:
        records = [x for x in records if x["v"] == "exists"]
    shown = records[offset:offset + limit]
    return {
        "owner": owner, "n": len(records), "offset": offset,
        "items": [{"r": x["r"], "role": x["role"], "v": x["v"]} for x in shown],
        "more": offset + limit < len(records),
        "scope": "approved_corpus_only_github_existence_not_functionality",
    }
