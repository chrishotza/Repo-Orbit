"""Bounded read-only staging of untrusted GitHub README excerpts for review.

NO automatic subject promotion. No third-party README mirroring. Authoritative
changes require a later reviewed PR with pinned SHA and line.
"""
from __future__ import annotations
import argparse
import base64
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen

from .agent import ROOT
from .coverage_plan import plan
from .check_targets import fetch as fetch_repo, pending
from .identity import canonical_slug, load as seed_ids
from .refresh import _blob_sha, _write_atomic
from .verified import approved_provenance, load as checked_ids

STAGING = ROOT / "data" / "snapshots" / "readme_review"
MAX_BATCH = 5
MAX_RESPONSE = 900_000
MAX_README = 400_000
MAX_SCAN_LINES = 150
PROMPT_SIGNAL = re.compile(
    r"\b(ignore (all|any|the|previous)|you are (an? )?(ai|assistant|llm)"
    r"|language model|system prompt|developer instruction"
    r"|stop working|do not follow|disregard (the|all|any)|override (the|your))\b",
    flags=re.IGNORECASE,
)


class ReviewError(ValueError):
    """Unsafe or unverifiable staged evidence."""


def pending_review() -> list[str]:
    return pending()


def _request_readme(slug: str, token: str | None) -> tuple[bytes, str, str] | None:
    owner, name = canonical_slug(slug).split("/")
    url = "https://api.github.com/repos/" + quote(owner) + "/" + quote(name) + "/readme"
    headers = {"Accept": "application/vnd.github+json",
               "X-GitHub-Api-Version": "2022-11-28",
               "User-Agent": "RepoOrbit-readme-staging/0.1"}
    if token:
        headers["Authorization"] = "Bearer " + token
    try:
        with urlopen(Request(url, headers=headers), timeout=20) as resp:
            final = urlsplit(resp.geturl())
            if final.scheme != "https" or final.hostname != "api.github.com":
                raise ReviewError("README redirect outside GitHub API")
            body = resp.read(MAX_RESPONSE + 1)
    except HTTPError as exc:
        if exc.code == 404:
            return None
        raise ReviewError(f"GitHub README HTTP {exc.code}") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise ReviewError("GitHub README unavailable") from exc
    if len(body) > MAX_RESPONSE:
        raise ReviewError("README API response too large")
    try:
        doc = json.loads(body)
        if type(doc) is not dict or doc.get("encoding") != "base64":
            raise ReviewError("unexpected README API encoding")
        blob = base64.b64decode(doc["content"], validate=False)
        sha, path = doc["sha"], doc["path"]
    except (ValueError, KeyError, TypeError) as exc:
        raise ReviewError("malformed README API response") from exc
    if len(blob) > MAX_README or not isinstance(sha, str) or not re.fullmatch("[a-f0-9]{40}", sha):
        raise ReviewError("README size or SHA invalid")
    if _blob_sha(blob) != sha:
        raise ReviewError("README Git blob integrity mismatch")
    if not isinstance(path, str) or path.casefold() not in ("readme.md", "readme.markdown", "readme.rst", "readme"):
        raise ReviewError("unexpected README path")
    return blob, sha, path


def excerpt_candidates(blob: bytes) -> tuple[list[dict], int]:
    """Short candidate *data*, never instructions or approved classifications."""
    try:
        lines = blob.decode("utf-8").splitlines()
    except UnicodeError as exc:
        raise ReviewError("README not UTF-8") from exc
    results, blocked = [], 0
    in_fence, in_comment = False, False
    for n, raw in enumerate(lines[:MAX_SCAN_LINES], 1):
        line = raw.strip()
        if line.startswith((chr(96) * 3, "~~~")):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if "<!--" in line:
            in_comment = True
        if in_comment:
            if PROMPT_SIGNAL.search(line):
                blocked += 1
            if "-->" in line:
                in_comment = False
            continue
        if PROMPT_SIGNAL.search(line):
            blocked += 1
            continue
        if (not line or line.startswith(("#", "|", ">", "-", "*", "!", "[", "<", "import ", "npm ", "pip ", "$"))
                or len(line) < 35 or len(line) > 320):
            continue
        if ("http://" in line or "https://" in line or
                re.search(r"\[[^\]]+\]\(https?://", line)):
            continue
        if any(s in line.casefold() for s in
               ("sponsor", "badge", "installation", "license", "contributing",
                "pull request", "donate", "download", "click here")):
            continue
        clean = re.sub(r"[\x60*_]", "", line).strip()
        if len(clean) < 30:
            continue
        results.append({"line": n, "anchor": line[:80],
                        "preview": clean[:170], "needs_review": True})
        if len(results) >= 3:
            break
    return results, blocked


def stage_batch(slugs: list[str], repository_fetch, readme_fetch) -> dict:
    if type(slugs) is not list or not 1 <= len(slugs) <= MAX_BATCH:
        raise ReviewError("1..5 unique references required")
    allowed = approved_provenance()
    seeds, seeded = seed_ids()
    targets, checked = checked_ids()
    visited, seen_ids, items, unresolved = set(), set(), [], []
    for slug in slugs:
        key = canonical_slug(slug)
        if key in visited or key not in allowed:
            raise ReviewError("duplicate or unapproved slug")
        if key in seeded or key in checked:
            raise ReviewError("checked slug must not re-enter staging")
        visited.add(key)
        meta = repository_fetch(key)
        if meta is None:
            unresolved.append({"slug": key, "reason": "404_unknown_not_deleted"})
            continue
        ident = meta.get("github_id")
        official = canonical_slug(meta.get("canonical_slug"))
        if type(ident) is not int or ident <= 0:
            raise ReviewError("missing numeric GitHub identity")
        if (ident in seeds or ident in targets or ident in seen_ids or
                official in seeded or official in checked):
            raise ReviewError("numeric ID/alias collision requires review")
        seen_ids.add(ident)
        readme = readme_fetch(key)
        if readme is None:
            unresolved.append({"slug": key, "reason": "readme_missing_unknown"})
            continue
        raw, sha, path = readme
        if not isinstance(raw, bytes) or _blob_sha(raw) != sha:
            raise ReviewError("README SHA mismatch")
        snippets, blocked = excerpt_candidates(raw)
        items.append({
            "slug": key, "github_id": ident, "canonical_slug": meta["canonical_slug"],
            "source_catalogs": sorted(allowed[key]), "readme_blob_sha": sha,
            "readme_path": path, "candidate_lines": snippets,
            "rejected_instruction_signals": blocked,
            "classification": "unreviewed", "existence": "observed_metadata_only",
            "execution_test": "not_run", "cost": "unknown",
        })
    return {"v": 1, "status": "unreviewed_staging_only",
            "requested": len(slugs), "readmes": len(items),
            "unresolved": unresolved, "items": items, "next_cursor": slugs[-1],
            "notice": "Untrusted README prose is data, not instructions or certified capabilities."}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Stage GitHub README source evidence")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--limit", type=int, default=3)
    choice = parser.add_mutually_exclusive_group()
    choice.add_argument("--after", type=str)
    choice.add_argument("--cycle-date", type=str,
                        help="UTC date selecting rotating page of pending items")
    parser.add_argument("--output-dir", type=Path, default=STAGING)
    args = parser.parse_args(argv)
    try:
        if not 1 <= args.limit <= MAX_BATCH:
            raise ReviewError("limit must be 1..5")
        queue = pending_review()
        if args.after:
            cursor = canonical_slug(args.after)
            queue = [slug for slug in queue if slug > cursor]
        page = plan(queue, args.limit, args.cycle_date)
        slugs = page["items"]
        if args.check:
            print(json.dumps({"pending": len(pending_review()),
                              "selected": len(slugs),
                              "page_index": page["page_index"], "pages": page["pages"],
                              "network": False}))
            return 0
        if not slugs:
            print(json.dumps({"status": "empty", "requested": 0}))
            return 0
        out = args.output_dir.resolve()
        if not out.is_relative_to(STAGING.resolve()):
            raise ReviewError("output must stay under ignored staging")
        token = os.environ.get("GITHUB_TOKEN")
        report = stage_batch(slugs, lambda slug: fetch_repo(slug, token),
                             lambda slug: _request_readme(slug, token))
        report["observed_at"] = datetime.now(timezone.utc).isoformat()
        report["coverage_page"] = {k: v for k, v in page.items() if k != "items"}
        _write_atomic(out / "report.json", json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps({"status": report["status"], "requested": report["requested"],
                          "readmes": report["readmes"],
                          "unresolved": len(report["unresolved"]),
                          "next_cursor": report["next_cursor"],
                          "page_index": page["page_index"], "pages": page["pages"],
                          "queue_total": page["queue_total"]}, separators=(",", ":")))
        return 0
    except (ReviewError, ValueError, OSError) as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
