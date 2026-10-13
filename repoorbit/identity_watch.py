"""Read-only GitHub identity drift monitor for the 30 verified seed repositories.

Uses documented GET /repos/{owner}/{repo} and verifies the returned immutable
numeric ID; GitHub redirects can reveal renames/transfers. If an old slug is
reused by another repo, an ID mismatch blocks the report. No automatic writes
to the approved identity registry. Standard library only.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen

from . import identity
from .refresh import _write_atomic

DEFAULT_OUT = identity.ROOT / "data" / "snapshots" / "identity_watch"
PUBLIC_API = "https://api.github.com"


class IdentityWatchError(ValueError):
    """Unsafe or unverifiable GitHub identity response."""


def fetch_by_slug(slug: str, token: str | None = None) -> dict | None:
    """Return GitHub API facts; 404 becomes unknown, not 'deleted'."""
    key = identity.canonical_slug(slug)
    owner, name = key.split("/")
    url = f"{PUBLIC_API}/repos/{quote(owner)}/{quote(name)}"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "RepoOrbit-identity-watch/0.1",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = "Bearer " + token
    try:
        with urlopen(Request(url, headers=headers), timeout=20) as response:
            if urlsplit(response.geturl()).hostname != "api.github.com":
                raise IdentityWatchError("GitHub API redirect left approved host")
            payload = json.load(response)
    except HTTPError as exc:
        if exc.code == 404:
            return None
        if exc.code in (403, 429):
            raise IdentityWatchError("GitHub API forbidden/rate-limited; do not infer deletion") from exc
        raise IdentityWatchError(f"GitHub API unexpected HTTP {exc.code}") from exc
    except (URLError, TimeoutError, OSError, ValueError) as exc:
        raise IdentityWatchError(f"GitHub API request failed: {exc}") from exc
    if not isinstance(payload, dict):
        raise IdentityWatchError("non-object GitHub repository response")
    ident = payload.get("id")
    name = payload.get("full_name")
    if type(ident) is not int or ident < 1:
        raise IdentityWatchError("missing numeric GitHub ID")
    try:
        identity.canonical_slug(name)
    except ValueError as exc:
        raise IdentityWatchError("invalid GitHub canonical repository slug") from exc
    if payload.get("private") is True:
        raise IdentityWatchError("seed repository became private; manual review required")
    return {
        "github_id": ident,
        "canonical_slug": name,
        "archived": payload.get("archived") is True,
    }


def observe(fetch=fetch_by_slug, delay: float = 0, limit: int = 0) -> dict:
    """Compare each current seed with GitHub; never mutate approved records."""
    if delay < 0:
        raise ValueError("delay cannot be negative")
    records, _ = identity.load()
    if type(limit) is not int or limit < 0 or limit > len(records):
        raise ValueError("limit must be 0..verified ID count (0 = all)")
    selected = list(records.values())[:limit] if limit else list(records.values())
    checks = []
    unresolved = []
    for index, row in enumerate(selected):
        try:
            fresh = fetch(row["slug"])
        except IdentityWatchError:
            raise
        if fresh is None:
            unresolved.append({"github_id": row["github_id"], "slug": row["slug"], "status": "unresolved_404"})
        else:
            if type(fresh.get("github_id")) is not int or fresh["github_id"] != row["github_id"]:
                raise IdentityWatchError(
                    f"slug-to-ID collision for {row['slug']}; manual review before any index update"
                )
            checks.append(fresh)
        if delay and index < len(selected) - 1:
            time.sleep(delay)
    analysis = identity.reconcile(checks)
    return {
        "schema_version": "0.1.0",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "registered": len(records),
        "resolved": len(checks),
        "sampled": bool(limit),
        "unresolved": unresolved,
        "drift": analysis,
        "policy": "read_only_no_automatic_alias_or_seed_changes",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check GitHub seed identity drift without changing corpus")
    parser.add_argument("--check", action="store_true", help="Only validate identity registry offline")
    parser.add_argument("--delay", type=float, default=0.4)
    parser.add_argument("--limit", type=int, default=0, help="0 = all checked seed IDs, PR smoke checks 3")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)
    try:
        ids, _ = identity.load()
        if args.check:
            print(json.dumps({"verified_seed_ids": len(ids), "network": False}))
            return 0
        if not args.output_dir.resolve().is_relative_to(DEFAULT_OUT.resolve()):
            raise IdentityWatchError("output must be inside ignored identity staging")
        if args.delay < 0:
            raise IdentityWatchError("delay must not be negative")
        token = os.environ.get("GITHUB_TOKEN")
        report = observe(lambda slug: fetch_by_slug(slug, token), args.delay, args.limit)
        output = args.output_dir.resolve()
        output.mkdir(parents=True, exist_ok=True)
        _write_atomic(output / "report.json", json.dumps(report, indent=2) + "\n")
        print(json.dumps({
            "registered": report["registered"],
            "resolved": report["resolved"],
            "unresolved": len(report["unresolved"]),
            "sampled": report["sampled"],
            "renamed": report["drift"]["renamed"],
            "transferred": report["drift"]["transferred"],
            "status": "read_only_staged",
        }, separators=(",", ":")))
        return 0
    except (IdentityWatchError, OSError, ValueError) as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
