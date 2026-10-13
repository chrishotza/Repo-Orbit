"""Separate historical evidence age from live repository health.

All dates are immutable observations in approved registries; nothing here
contacts GitHub or measures whether a project currently works, is safe or free.
"""
from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timezone
import json

from .identity import load as seed_load, lookup as seed_lookup
from .verified import load as target_load, lookup as target_lookup
from .topic_evidence import load as topics_load


def _reference_day(as_of: str | None) -> date:
    if as_of is None:
        return datetime.now(timezone.utc).date()
    if type(as_of) is not str:
        raise ValueError("as_of must be YYYY-MM-DD")
    try:
        day = date.fromisoformat(as_of)
    except ValueError as exc:
        raise ValueError("invalid as_of date") from exc
    if day.isoformat() != as_of:
        raise ValueError("as_of must be canonical YYYY-MM-DD")
    return day


def inspect(repo: str, as_of: str | None = None) -> dict:
    """Small per-repository freshness report for agents.

    as_of exists only as a deterministic Python test input; the MCP tool
    intentionally exposes repo alone and evaluates dates in UTC at runtime.
    """
    from .agent import resolve
    if not isinstance(repo, str) or not 1 <= len(repo) <= 240:
        raise ValueError("repo must be a GitHub slug, URL or id:<number>")
    day = _reference_day(as_of)
    known = resolve(repo)
    if not known["found"]:
        return {"found": False, "status": "not_in_approved_corpus"}
    result = {"found": True, "r": known["r"], "role": known["role"],
              "as_of_utc": day.isoformat(), "scope": "historical_metadata_only"}
    if "github_id" not in known:
        result.update({"identity_status": "not_individually_checked",
                       "note": "Catalog link only; no GitHub ID or current functionality evidence."})
        return result
    evidence = seed_lookup(repo)
    if not evidence["found"]:
        evidence = target_lookup(repo)
    if not evidence["found"] or evidence["github_id"] != known["github_id"]:
        raise ValueError("checked numeric identity has missing/conflicting evidence")
    observed = date.fromisoformat(known["identity_observed_on"])
    age = (day - observed).days
    if age < 0:
        status = "future_dated_evidence_invalid"
    elif age <= 30:
        status = "recent_observation"
    elif age <= 90:
        status = "aging_observation"
    else:
        status = "stale_observation"
    result.update({
        "identity_status": status, "github_id": known["github_id"],
        "observed_on": observed.isoformat(), "age_days": age,
        "archived_when_checked": evidence["archived"],
        "note": "This is the age of a past GitHub metadata check, not live health or functionality.",
    })
    subject = topics_load().get(known["r"].casefold())
    if subject:
        result["readme_subject_observed_on"] = subject["observed_on"]
        result["readme_subject_sha"] = subject["readme_blob_sha"]
    return result


def snapshot() -> dict:
    """Reproducible aggregate of dated evidence, intentionally no current age."""
    seeds, _ = seed_load()
    targets, _ = target_load()
    subjects = topics_load()
    unique_ids = set(seeds) | set(targets)
    if len(unique_ids) != len(seeds) + len(targets):
        raise ValueError("identity collision between checked seeds and references")
    observed = Counter(row["observed_on"] for row in list(seeds.values()) + list(targets.values()))
    document_days = Counter(row["observed_on"] for row in subjects.values())
    return {
        "v": 1, "scope": "pinned_observation_dates_not_live_health",
        "checked_numeric_ids": len(unique_ids),
        "readme_subjects": len(subjects),
        "identity_observations_by_date": [[day, n] for day, n in sorted(observed.items())],
        "documentary_subjects_by_date": [[day, n] for day, n in sorted(document_days.items())],
        "fresh_max_age_days": 30, "aging_max_age_days": 90,
        "note": "Age is computed on demand in UTC. This does not assert recent repo activity, functionality or zero cost.",
    }
