"""Rights-gated, incremental discovery refresh. Stages artifacts; never auto-pushes.

A GitHub Actions job can invoke this tool. It only contacts two explicitly
allowlisted CC0 sources, verifies each Git blob SHA and current CC0 license,
calculates deltas against its pinned approved baseline, and writes a staged report. Standard lib only.
"""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from .agent import ROOT

FEEDS = ROOT / "data" / "feeds.json"
SOURCES = ROOT / "data" / "sources.json"
STAGING = ROOT / "data" / "snapshots" / "staged"
SHA = re.compile(r"^[0-9a-f]{40}$")
SLUG = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
LINK = re.compile(r"https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)", re.I)
RESERVED = {
    "topics", "search", "features", "orgs", "organizations", "settings",
    "sponsors", "login", "logout", "signup", "about", "site", "explore",
    "marketplace", "enterprise", "pricing", "issues", "pulls", "apps", "new",
    "users", "trending",
}
MAX_FILE_BYTES = 8 * 1024 * 1024


class RefreshError(ValueError):
    """Cannot safely refresh this source or baseline."""


def _blob_sha(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def _github_contents(repository: str, path: str, token: str | None) -> tuple[bytes, str]:
    if not SLUG.fullmatch(repository) or not re.fullmatch(r"[A-Za-z0-9_.-]+", path):
        raise RefreshError("unsafe source repository or file path")
    url = f"https://api.github.com/repos/{repository}/contents/{quote(path)}"
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "RepoOrbit-licensed-feed-refresh/0.1",
    }
    if token:
        headers["Authorization"] = "Bearer " + token
    req = Request(url, headers=headers)
    try:
        with urlopen(req, timeout=20) as response:
            data = response.read(MAX_FILE_BYTES * 2)
    except HTTPError as exc:
        if exc.code in (403, 429):
            raise RefreshError("GitHub API rate limit/permission restriction") from exc
        raise RefreshError(f"GitHub API HTTP {exc.code} for {repository}/{path}") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise RefreshError(f"GitHub API error for {repository}/{path}: {exc}") from exc
    try:
        payload = json.loads(data)
        if not isinstance(payload, dict) or payload.get("encoding") != "base64":
            raise RefreshError("unexpected GitHub contents encoding")
        raw = base64.b64decode(payload["content"], validate=False)
        sha = payload["sha"]
    except (KeyError, TypeError, ValueError) as exc:
        raise RefreshError("malformed GitHub content response") from exc
    if len(raw) > MAX_FILE_BYTES or not isinstance(sha, str) or not SHA.fullmatch(sha):
        raise RefreshError("invalid file size or Git SHA")
    if _blob_sha(raw) != sha:
        raise RefreshError("Git blob hash mismatch, refusing snapshot")
    return raw, sha


def load_feeds() -> list[dict]:
    registry = json.loads(FEEDS.read_text(encoding="utf-8"))
    known = {s["id"] for s in json.loads(SOURCES.read_text(encoding="utf-8"))["sources"]}
    if registry.get("schema_version") != "0.1.0":
        raise RefreshError("unknown feed registry schema version")
    seen = set()
    active = []
    for feed in registry.get("sources", []):
        name = feed.get("repository")
        if not isinstance(name, str) or not SLUG.fullmatch(name):
            raise RefreshError("invalid feed repository")
        source_id = "github:" + name.casefold()
        if feed.get("id") != source_id or source_id not in known or source_id in seen:
            raise RefreshError("unregistered, mismatched or duplicate discovery feed")
        seen.add(source_id)
        if feed.get("license") != "CC0-1.0" or not feed.get("reviewed_at"):
            raise RefreshError("feed requires manually recorded CC0 rights review")
        if feed.get("readme_path") != "readme.md" or feed.get("license_path") != "license":
            raise RefreshError("unsupported upstream file path; requires human review")
        base = feed.get("baseline")
        if not isinstance(base, str) or not re.fullmatch(r"data/discoveries/[a-z0-9-]+\.jsonl", base):
            raise RefreshError("baseline must be a local tracked discovery snapshot")
        if not (ROOT / base).is_file():
            raise RefreshError("missing baseline " + base)
        if feed.get("enabled") is True:
            active.append(feed)
        elif feed.get("enabled") is not False:
            raise RefreshError("feed enabled field must be boolean")
    if not active:
        raise RefreshError("no enabled, rights-reviewed feeds")
    return active


def extract_references(text: str, feed: dict, sha: str, day: str) -> list[dict]:
    seen = set()
    rows = []
    source_id = feed["id"]
    for line_number, line in enumerate(text.splitlines(), 1):
        for m in LINK.finditer(line):
            if m.group(1).casefold() in RESERVED:
                continue
            full = m.group(1) + "/" + m.group(2).rstrip(".,;:")
            ident = "github:" + full.casefold()
            if ident in seen or ident == source_id:
                continue
            seen.add(ident)
            rows.append({
                "source_id": source_id,
                "source_path": "readme.md",
                "source_line": line_number,
                "source_blob_sha": sha,
                "source_license": "CC0-1.0",
                "target_id": ident,
                "target_full_name": full,
                "target_url": "https://github.com/" + full,
                "observed_at": day,
                "target_verification": "not_checked",
                "extraction_method": "github_link_regex_v0.1",
            })
    return sorted(rows, key=lambda item: item["target_id"])


def _baseline_ids(feed: dict) -> set[str]:
    baseline = ROOT / feed["baseline"]
    seen = set()
    with baseline.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                raise RefreshError("blank record in baseline")
            row = json.loads(line)
            if row.get("source_id") != feed["id"] or row.get("target_verification") != "not_checked":
                raise RefreshError("baseline has conflicting provenance or verification")
            key = row["target_id"]
            if key in seen:
                raise RefreshError("duplicate baseline discovery edge")
            seen.add(key)
    return seen


def plan_refresh(
    feeds: list[dict], fetch: Callable[[str, str], tuple[bytes, str]],
    at: datetime | None = None,
) -> list[tuple[dict, list[dict], dict]]:
    """Pure-to-disk planning. A failed source prevents writes for every source."""
    now = at or datetime.now(timezone.utc)
    day = now.astimezone(timezone.utc).date().isoformat()
    plans = []
    for feed in feeds:
        lic_data, _ = fetch(feed["repository"], feed["license_path"])
        license_head = lic_data[:1500].decode("utf-8", "replace")
        if "CC0 1.0 Universal" not in license_head:
            raise RefreshError("source no longer has reviewed CC0 text: " + feed["repository"])
        source, sha = fetch(feed["repository"], feed["readme_path"])
        content = source.decode("utf-8")  # fail closed if data is not valid UTF-8
        current = extract_references(content, feed, sha, day)
        if not current:
            raise RefreshError("empty extraction; refusing destructive refresh")
        old = _baseline_ids(feed)
        new = {row["target_id"] for row in current}
        info = {
            "source_id": feed["id"],
            "source_blob_sha": sha,
            "source_license": "CC0-1.0",
            "observed_at": now.astimezone(timezone.utc).isoformat(),
            "baseline": feed["baseline"],
            "comparison": "approved_pinned_baseline_not_previous_daily_run",
            "baseline_count": len(old),
            "current_count": len(new),
            "added": len(new - old),
            "removed": len(old - new),
            "unchanged": len(new & old),
            "note": "references only; target existence/cost/function unverified; staging-only; changes measured against pinned baseline",
        }
        plans.append((feed, current, info))
    return plans


def _write_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", dir=path.parent, encoding="utf-8", delete=False, suffix=".tmp"
    ) as tmp:
        tmp.write(content)
        tmp.flush()
        os.fsync(tmp.fileno())
        name = tmp.name
    os.replace(name, path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="RepoOrbit rights-reviewed staged feed refresh")
    parser.add_argument("--check", action="store_true", help="Validate allowlist and baselines without networking")
    parser.add_argument("--output-dir", type=Path, default=STAGING)
    args = parser.parse_args(argv)
    try:
        feeds = load_feeds()
        baseline_total = sum(len(_baseline_ids(f)) for f in feeds)
        if args.check:
            print(json.dumps({"feeds": len(feeds), "baseline_edges": baseline_total, "network": False}))
            return 0
        token = os.environ.get("GITHUB_TOKEN")
        def fetch(repository: str, path: str) -> tuple[bytes, str]:
            return _github_contents(repository, path, token)
        plans = plan_refresh(feeds, fetch)
        out = args.output_dir.resolve()
        # Prevent a scheduled job from overwriting authoritative tracked data.
        if not out.is_relative_to(STAGING.resolve()):
            raise RefreshError("output must remain under gitignored data/snapshots/staged")
        summaries = []
        for feed, edges, result in plans:
            name = feed["repository"].replace("/", "-").casefold() + ".jsonl"
            snapshot = out / name
            text = "".join(json.dumps(x, sort_keys=True, ensure_ascii=False) + "\n" for x in edges)
            _write_atomic(snapshot, text)
            result["staged_snapshot"] = str(snapshot.relative_to(ROOT))
            summaries.append(result)
        _write_atomic(out / "report.json", json.dumps({
            "schema_version": "0.1.0",
            "status": "staged_unreviewed_no_auto_commit",
            "results": summaries,
        }, indent=2) + "\n")
        print(json.dumps({"status": "staged", "results": summaries}, separators=(",", ":")))
        return 0
    except (RefreshError, UnicodeError, OSError, ValueError) as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
