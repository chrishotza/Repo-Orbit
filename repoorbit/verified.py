"""Independently GitHub-checked discovery targets (not functional validation).

Separate from immutable catalog references and 30 verified seed identities.
A checked reference keeps its discovery-role and provenance, but gains a
stable numeric GitHub ID and repository-existence status.

Standard library only, offline at agent query time.
"""
from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path
from typing import Any

from .identity import canonical_slug, load as load_seed_ids
from .snapshots import approved_discoveries

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "verified_targets.jsonl"


def approved_targets() -> set[str]:
    """Exactly the slugs referred to in approved source snapshots."""
    result: set[str] = set()
    for path in approved_discoveries():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                edge = json.loads(line)
                result.add(canonical_slug(edge["target_full_name"]))
    return result


@lru_cache(maxsize=1)
def load() -> tuple[dict[int, dict[str, Any]], dict[str, int]]:
    """Reject collisions, missing evidence or fabricated stronger claims."""
    seeded_ids, seeded_aliases = load_seed_ids()
    allowed = approved_targets()
    by_id: dict[int, dict[str, Any]] = {}
    by_slug: dict[str, int] = {}
    last_id = 0
    for line_no, line in enumerate(REGISTRY.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            raise ValueError(f"verified target line {line_no}: blank row")
        row = json.loads(line)
        if not isinstance(row, dict):
            raise ValueError(f"verified target line {line_no}: expected object")
        ident = row.get("github_id")
        if type(ident) is not int or ident <= last_id:
            raise ValueError(f"verified target line {line_no}: numeric IDs must be unique and sorted")
        if ident in seeded_ids:
            raise ValueError("target identity already registered as a checked seed")
        last_id = ident
        original = canonical_slug(row.get("requested_slug"))
        canonical = canonical_slug(row.get("canonical_slug"))
        if original not in allowed:
            raise ValueError("verified target is not referenced by any approved source")
        for alias in (original, canonical):
            if alias in seeded_aliases and seeded_aliases[alias] != ident:
                raise ValueError("verified target collides with seed identity")
            if alias in by_slug and by_slug[alias] != ident:
                raise ValueError("verified target slug collision")
            by_slug[alias] = ident
        if row.get("source") != "github_rest_repo" or row.get("verification") != "repository_exists":
            raise ValueError("verified targets require real GitHub metadata observations")
        if row.get("function_test") != "not_run" or row.get("cost") != "unknown":
            raise ValueError("repository existence is not a functional/cost test")
        if type(row.get("archived")) is not bool:
            raise ValueError("missing archived flag")
        if not isinstance(row.get("default_branch"), str) or not row["default_branch"]:
            raise ValueError("default branch must be a nonempty observed string")
        observed = row.get("observed_on")
        from datetime import date
        if not isinstance(observed, str):
            raise ValueError("observation date required")
        date.fromisoformat(observed)
        cited = row.get("discovered_via")
        if not isinstance(cited, list) or not cited or not all(
            isinstance(s, str) and s.startswith("github:") for s in cited
        ):
            raise ValueError("verified target requires catalog provenance")
        by_id[ident] = row
    return by_id, by_slug


def lookup(value: str | int) -> dict:
    ids, aliases = load()
    if type(value) is int:
        ident = value
    elif isinstance(value, str):
        q = value.strip()
        if q.startswith("id:"):
            q = q[3:]
            if not q.isdecimal() or q.startswith("0") or len(q) > 16:
                raise ValueError("malformed numeric GitHub ID")
            ident = int(q)
        else:
            ident = aliases.get(canonical_slug(q))
    else:
        raise ValueError("expected repository slug or positive numeric ID")
    row = ids.get(ident)
    if row is None:
        return {"found": False, "status": "target_id_not_checked"}
    return {
        "found": True,
        "github_id": row["github_id"],
        "slug": row["requested_slug"],
        "canonical_slug": row["canonical_slug"],
        "archived": row["archived"],
        "observed_on": row["observed_on"],
        "role": "reference",
        "verification": "github_repository_metadata_only",
    }


def status() -> dict:
    rows, _ = load()
    return {
        "numeric_references_checked": len(rows),
        "checked_archived": sum(row["archived"] for row in rows.values()),
        "evidence": "github_rest_repo",
        "functionally_verified": 0,
        "free_execution_verified": 0,
    }
