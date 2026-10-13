"""Stable GitHub repository identities. Standard-library only, offline at query time.

A GitHub owner/repo slug is a mutable address, *not* the repository identity.
An authenticated GitHub REST repository ID survives ordinary renames/transfers.
A fork has a different ID, even when its name/content resembles another repo.
"""
from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path
import re
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "identities.jsonl"
SLUG = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SAFE_ID = re.compile(r"^[1-9][0-9]{0,15}$")


def canonical_slug(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("GitHub repository slug must be a string")
    name = value.strip().removeprefix("https://github.com/").rstrip("/")
    if not SLUG.fullmatch(name):
        raise ValueError("expected GitHub owner/repository or canonical URL")
    if name.split("/")[0] in (".", "..") or name.split("/")[1] in (".", ".."):
        raise ValueError("invalid GitHub owner or repository")
    return name.casefold()


@lru_cache(maxsize=1)
def load() -> tuple[dict[int, dict[str, Any]], dict[str, int]]:
    """Validate the immutable sampled ID table, then index IDs and aliases."""
    ids: dict[int, dict[str, Any]] = {}
    aliases: dict[str, int] = {}
    content = REGISTRY.read_text(encoding="utf-8")
    if not content.strip():
        raise ValueError("identity registry is empty")
    for line_no, line in enumerate(content.splitlines(), 1):
        row = json.loads(line)
        if not isinstance(row, dict):
            raise ValueError(f"identity line {line_no}: expected object")
        ident = row.get("github_id")
        if type(ident) is not int or ident <= 0 or ident > 999_999_999_999_999:
            raise ValueError(f"identity line {line_no}: invalid numeric GitHub ID")
        if ident in ids:
            raise ValueError(f"identity line {line_no}: duplicate GitHub ID")
        if row.get("role") not in ("catalog", "project"):
            raise ValueError(f"identity line {line_no}: invalid seed role")
        if row.get("source") != "github_rest_repo" or row.get("evidence") != "public_repository_metadata_only":
            raise ValueError(f"identity line {line_no}: unsupported evidence assertion")
        if not isinstance(row.get("default_branch"), str) or not row["default_branch"]:
            raise ValueError(f"identity line {line_no}: missing observed default branch")
        if type(row.get("archived")) is not bool:
            raise ValueError(f"identity line {line_no}: missing archived flag")
        observed = row.get("observed_on")
        if not isinstance(observed, str) or not DATE.fullmatch(observed):
            raise ValueError(f"identity line {line_no}: invalid observation date")
        for field in ("slug", "canonical_slug"):
            key = canonical_slug(row.get(field))
            if key in aliases and aliases[key] != ident:
                raise ValueError(f"identity line {line_no}: slug collision across different IDs")
            aliases[key] = ident
        ids[ident] = row
    return ids, aliases


def lookup(value: str | int) -> dict[str, Any]:
    """Resolve exact slug or ID; never performs a network lookup."""
    ids, aliases = load()
    if type(value) is int:
        ident = value
    elif isinstance(value, str):
        query = value.strip()
        if query.startswith("id:"):
            query = query[3:]
            if not SAFE_ID.fullmatch(query):
                raise ValueError("malformed numeric GitHub ID")
            ident = int(query)
        elif SAFE_ID.fullmatch(query):
            ident = int(query)
        else:
            ident = aliases.get(canonical_slug(query))
    else:
        raise ValueError("expected GitHub slug or positive numeric ID")
    row = ids.get(ident)
    if row is None:
        return {"found": False, "status": "not_in_verified_identity_registry"}
    return {
        "found": True,
        "github_id": row["github_id"],
        "slug": row["slug"],
        "canonical_slug": row["canonical_slug"],
        "role": row["role"],
        "observed_on": row["observed_on"],
        "archived": row["archived"],
        "verification": "github_repository_metadata_only",
    }


def reconcile(observations: list[dict]) -> dict:
    """Compare a new GitHub-by-ID snapshot to the previous registry.

    Rename or transfer is determined solely by the *same numeric ID*,
    never by matching names. Missing IDs remain unknown, not deleted.
    Cross-ID reuse of a recorded slug is an explicit review blocker.
    """
    if not isinstance(observations, list):
        raise ValueError("observations must be a list")
    old, alias = load()
    seen_ids: set[int] = set()
    current_names: dict[str, int] = {}
    changes = []
    for row in observations:
        if not isinstance(row, dict) or type(row.get("github_id")) is not int:
            raise ValueError("malformed identity observation")
        ident = row["github_id"]
        slug = row.get("canonical_slug")
        name = canonical_slug(slug)
        if ident in seen_ids:
            raise ValueError("duplicate observed numeric ID")
        seen_ids.add(ident)
        if name in current_names and current_names[name] != ident:
            raise ValueError("two observed IDs share the same slug")
        current_names[name] = ident
        if name in alias and alias[name] != ident:
            raise ValueError("slug reused by another GitHub repository ID; manual review required")
        previous = old.get(ident)
        if previous is None:
            changes.append({"github_id": ident, "status": "new_id_unreviewed", "current": slug})
            continue
        former = previous["canonical_slug"]
        if name == canonical_slug(former):
            status = "same_identity"
        elif name.split("/")[0] != canonical_slug(former).split("/")[0]:
            status = "transferred"
        else:
            status = "renamed"
        changes.append({
            "github_id": ident,
            "status": status,
            "previous": former,
            "current": slug,
        })
    missing = sorted(set(old) - seen_ids)
    return {
        "observed": len(changes),
        "unchanged": sum(x["status"] == "same_identity" for x in changes),
        "renamed": sum(x["status"] == "renamed" for x in changes),
        "transferred": sum(x["status"] == "transferred" for x in changes),
        "new_unreviewed": sum(x["status"] == "new_id_unreviewed" for x in changes),
        "not_checked_this_run": len(missing),
        "items": changes,
        "missing_ids": missing,
        "note": "missing means not checked, not deleted; forks are separate IDs",
    }
