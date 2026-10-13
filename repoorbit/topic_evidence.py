"""Small, separately reviewed README subject-evidence layer.

A subject statement from a versioned upstream README is *documentary evidence
of what the authors say their repository is about*, never independent proof of
correct behavior, security, license compatibility, or no-cost operation.
"""
from __future__ import annotations

from datetime import date
from functools import lru_cache
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "data" / "topic_evidence.jsonl"
SHA = re.compile(r"^[a-f0-9]{40}$")
SLUG = re.compile(r"^[a-z0-9_.-]+/[a-z0-9_.-]+$")


@lru_cache(maxsize=1)
def load() -> dict[str, dict]:
    from .verified import load as verified_load
    source_rows, _ = verified_load()
    subjects = {
        item["id"] for item in
        json.loads((ROOT / "data" / "taxonomy.json").read_text(encoding="utf-8"))["categories"]
    }
    result = {}
    last_id = 0
    for i, line in enumerate(EVIDENCE.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            raise ValueError(f"README evidence {i}: blank line")
        row = json.loads(line)
        if not isinstance(row, dict):
            raise ValueError(f"README evidence {i}: expected object")
        ident = row.get("github_id")
        if type(ident) is not int or ident <= last_id or ident not in source_rows:
            raise ValueError(f"README evidence {i}: duplicate, unsorted or unverified numeric ID")
        last_id = ident
        repo = row.get("repo")
        if not isinstance(repo, str) or not SLUG.fullmatch(repo.casefold()):
            raise ValueError("invalid evidence repository name")
        key = repo.casefold()
        if key != source_rows[ident]["requested_slug"].casefold() or key in result:
            raise ValueError("README evidence must match unique checked target numeric identity")
        if row.get("category") not in subjects:
            raise ValueError("README evidence has unrecognized topical category")
        if row.get("readme_path") not in ("README.md", "readme.md"):
            raise ValueError("unsupported README path")
        if not SHA.fullmatch(row.get("readme_blob_sha", "")):
            raise ValueError("invalid Git blob SHA")
        if type(row.get("line")) is not int or not 1 <= row["line"] <= 100000:
            raise ValueError("invalid README line number")
        for field, max_len in (("anchor", 72), ("summary", 100)):
            value = row.get(field)
            if not isinstance(value, str) or not 2 <= len(value) <= max_len:
                raise ValueError(f"invalid {field} bound")
            if "\n" in value or "\r" in value or "<" in value or ">" in value:
                raise ValueError(f"{field} may not contain markup")
        if row.get("source") != "upstream_readme_self_description":
            raise ValueError("unsupported README evidence source")
        if row.get("classification") != "reviewed_readme_subject":
            raise ValueError("unreviewed category asserted")
        if row.get("execution_test") != "not_run" or row.get("cost") != "unknown":
            raise ValueError("topic evidence cannot assert execution or pricing")
        observed = row.get("observed_on")
        try:
            if type(observed) is not str:
                raise ValueError("missing date")
            date.fromisoformat(observed)
        except ValueError as exc:
            raise ValueError("invalid README observation date") from exc
        result[key] = row
    return result


def evidence_pointer(row: dict) -> dict:
    """Compact immutable, self-contained pointer to the reviewed README line."""
    from .verified import load as verified_load
    upstream = verified_load()[0][row["github_id"]]
    return {
        "sha": row["readme_blob_sha"],
        "line": row["line"],
        "path": row["readme_path"],
        "blob_api": (
            "https://api.github.com/repos/" + row["repo"]
            + "/git/blobs/" + row["readme_blob_sha"]
        ),
        "readme_url": (
            "https://github.com/" + row["repo"] + "/blob/"
            + upstream["default_branch"] + "/" + row["readme_path"]
            + "#L" + str(row["line"])
        ),
        "observed": row["observed_on"],
        "summary": row["summary"],
    }


def stats() -> dict:
    rows = load()
    return {
        "readme_subjects_reviewed": len(rows),
        "source": "versioned_upstream_readme_line",
        "functional_tests_passed": 0,
        "cost_verified_free": 0,
    }
