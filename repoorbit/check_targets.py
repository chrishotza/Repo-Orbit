"""Bounded read-only GitHub REST verification of discovered repository references.

Staging only. Never automatically marks a catalog link as installable, free,
safe, or even approved: a separate human-reviewable promotion is required.
No third-party dependencies, no LLM calls, no README downloads.
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

from .agent import ROOT
from .identity import canonical_slug, load as seed_identities
from .refresh import _write_atomic
from .verified import approved_targets, load as checked_targets

STAGE = ROOT / "data" / "snapshots" / "target_checks"
API = "https://api.github.com"
MAX_BATCH = 25
MAX_BYTES = 1024 * 1024


class TargetCheckError(ValueError):
    """Unsafe request, inconsistent identity, or failed API verification."""


def pending() -> list[str]:
    """Stable deterministic queue; no duplicates, excludes all checked IDs."""
    _, seeded = seed_identities()
    _, approved = checked_targets()
    return sorted(approved_targets() - set(seeded) - set(approved))


def fetch(slug: str, token: str | None = None) -> dict | None:
    """Resolve a public target slug through GitHub REST, not web scraping."""
    key = canonical_slug(slug)
    owner, name = key.split("/")
    url = f"{API}/repos/{quote(owner)}/{quote(name)}"
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "RepoOrbit-reference-verification/0.1",
    }
    if token:
        headers["Authorization"] = "Bearer " + token
    try:
        with urlopen(Request(url, headers=headers), timeout=20) as response:
            final = urlsplit(response.geturl())
            if final.scheme != "https" or final.hostname != "api.github.com":
                raise TargetCheckError("redirect outside the verified GitHub REST origin")
            content = response.read(MAX_BYTES + 1)
    except HTTPError as exc:
        if exc.code in (404, 410):
            return None
        if exc.code in (403, 429):
            raise TargetCheckError("GitHub API rate limit/permission error; no inference") from exc
        raise TargetCheckError(f"GitHub API HTTP {exc.code}; no inference") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise TargetCheckError(f"GitHub API unreachable: {exc}") from exc
    if len(content) > MAX_BYTES:
        raise TargetCheckError("GitHub response exceeds safety bound")
    try:
        payload = json.loads(content)
    except (ValueError, UnicodeError) as exc:
        raise TargetCheckError("GitHub response is not valid JSON") from exc
    if not isinstance(payload, dict):
        raise TargetCheckError("GitHub API response is not an object")
    ident = payload.get("id")
    full = payload.get("full_name")
    if type(ident) is not int or ident <= 0:
        raise TargetCheckError("GitHub API response lacks a numeric repository ID")
    try:
        canonical_slug(full)
    except ValueError as exc:
        raise TargetCheckError("GitHub response has an invalid canonical name") from exc
    if payload.get("private") is True:
        raise TargetCheckError("private repository requires explicit review")
    branch = payload.get("default_branch")
    if not isinstance(branch, str) or not branch:
        raise TargetCheckError("GitHub response lacks a default branch")
    if type(payload.get("archived")) is not bool:
        raise TargetCheckError("GitHub response lacks archival status")
    return {
        "github_id": ident,
        "canonical_slug": full,
        "archived": payload["archived"],
        "default_branch": branch,
    }


def examine(slugs: list[str], fetcher, observed_on: str) -> dict:
    """Validate a small batch without mutating the authoritative corpus."""
    seeds, seed_names = seed_identities()
    checked, checked_names = checked_targets()
    allowed = approved_targets()
    if not isinstance(slugs, list) or not 1 <= len(slugs) <= MAX_BATCH:
        raise TargetCheckError("batch must contain 1..25 repositories")
    seen_slug = set()
    seen_id = {}
    passed = []
    unresolved = []
    for slug in slugs:
        key = canonical_slug(slug)
        if key in seen_slug or key not in allowed:
            raise TargetCheckError("duplicate or unapproved discovery target")
        seen_slug.add(key)
        if key in seed_names or key in checked_names:
            raise TargetCheckError("batch includes an already checked repository")
        item = fetcher(slug)
        if item is None:
            unresolved.append({"requested_slug": slug, "reason": "unresolved_404_not_confirmed_deleted"})
            continue
        ident = item.get("github_id")
        full = item.get("canonical_slug")
        if type(ident) is not int or ident <= 0:
            raise TargetCheckError("invalid numeric repository ID")
        canonical = canonical_slug(full)
        if ident in seeds:
            raise TargetCheckError("discovery target redirects to an already checked seed; manual review")
        if ident in checked:
            raise TargetCheckError("discovery target shares an already checked reference ID; manual review")
        if canonical in seed_names or canonical in checked_names:
            raise TargetCheckError("slug-to-ID collision with checked repository; manual review")
        if ident in seen_id:
            raise TargetCheckError("two requested paths map to one numeric GitHub ID; manual alias review")
        seen_id[ident] = key
        if type(item.get("archived")) is not bool:
            raise TargetCheckError("archival status not observed")
        if not isinstance(item.get("default_branch"), str) or not item["default_branch"]:
            raise TargetCheckError("default branch not observed")
        passed.append({
            "github_id": ident,
            "requested_slug": slug,
            "canonical_slug": full,
            "archived": item["archived"],
            "default_branch": item["default_branch"],
            "observed_on": observed_on,
            "source": "github_rest_repo",
            "verification": "repository_exists",
            "function_test": "not_run",
            "cost": "unknown",
        })
    return {
        "schema_version": "0.1.0",
        "status": "staged_only_requires_review",
        "attempted": len(slugs),
        "checked": len(passed),
        "unresolved": len(unresolved),
        "observed_on": observed_on,
        "verified": sorted(passed, key=lambda x: x["github_id"]),
        "unresolved_items": unresolved,
        "note": "metadata only: existence is not executable, safe or free",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Small, rights-provenanced GitHub target batch check")
    parser.add_argument("--check", action="store_true", help="Validate approved reference queue offline")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--after", type=str, default=None, help="Continue after an alphabetically sorted slug")
    parser.add_argument("--delay", type=float, default=0.4)
    parser.add_argument("--output-dir", type=Path, default=STAGE)
    args = parser.parse_args(argv)
    try:
        if type(args.limit) is not int or not 1 <= args.limit <= MAX_BATCH:
            raise TargetCheckError("limit must be 1..25")
        if args.delay < 0:
            raise TargetCheckError("delay must not be negative")
        todo = pending()
        if args.after is not None:
            cursor = canonical_slug(args.after)
            todo = [name for name in todo if name > cursor]
        selection = todo[:args.limit]
        if args.check:
            print(json.dumps({"pending": len(pending()), "next_selection": len(selection), "network": False}))
            return 0
        if not selection:
            print(json.dumps({"status": "no_pending_targets", "checked": 0}))
            return 0
        if not args.output_dir.resolve().is_relative_to(STAGE.resolve()):
            raise TargetCheckError("output must stay in ignored target-check staging directory")
        token = os.environ.get("GITHUB_TOKEN")
        def api(slug: str) -> dict | None:
            result = fetch(slug, token)
            if args.delay:
                time.sleep(args.delay)
            return result
        result = examine(selection, api, datetime.now(timezone.utc).date().isoformat())
        result["next_cursor"] = selection[-1]
        output = args.output_dir.resolve()
        _write_atomic(output / "report.json", json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        _write_atomic(
            output / "verified.jsonl",
            "".join(json.dumps(x, ensure_ascii=False, sort_keys=True) + "\n" for x in result["verified"]),
        )
        print(json.dumps({
            "status": result["status"],
            "attempted": result["attempted"],
            "checked": result["checked"],
            "unresolved": result["unresolved"],
            "next_cursor": result["next_cursor"],
        }, separators=(",", ":")))
        return 0
    except (TargetCheckError, ValueError, OSError) as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
