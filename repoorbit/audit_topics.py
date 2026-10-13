"""Recheck immutable upstream README Git blobs for curated subject evidence.

Uses official GitHub REST git/blob GET; read-only, bounded and fail-closed.
A passing check validates a historical self-description *quote*, not whether
the software actually provides its claimed functionality.
"""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen

from .refresh import _blob_sha, _write_atomic
from .topic_evidence import ROOT, load

STAGE = ROOT / "data" / "snapshots" / "topic_audit"
MAX_BLOB_BYTES = 2 * 1024 * 1024
MAX_RESPONSE_BYTES = 4 * 1024 * 1024


class TopicAuditError(ValueError):
    """A pinned source quote could not be independently substantiated."""


def fetch_blob(row: dict, token: str | None = None) -> bytes:
    """Retrieve content by *blob SHA*, not by mutable branch name."""
    repo = row["repo"]
    sha = row["readme_blob_sha"]
    url = "https://api.github.com/repos/" + "/".join(
        quote(segment, safe="") for segment in repo.split("/")
    ) + "/git/blobs/" + sha
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "RepoOrbit-evidence-audit/0.1",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = "Bearer " + token
    try:
        with urlopen(Request(url, headers=headers), timeout=25) as resp:
            redirected = urlsplit(resp.geturl())
            if redirected.scheme != "https" or redirected.hostname != "api.github.com":
                raise TopicAuditError("unsafe blob redirect")
            response = resp.read(MAX_RESPONSE_BYTES + 1)
    except HTTPError as exc:
        raise TopicAuditError(f"GitHub evidence endpoint HTTP {exc.code}; no inferred result") from exc
    except (URLError, OSError, TimeoutError) as exc:
        raise TopicAuditError(f"upstream blob unavailable: {exc}") from exc
    if len(response) > MAX_RESPONSE_BYTES:
        raise TopicAuditError("upstream blob API response exceeds bound")
    try:
        body = json.loads(response)
        if not isinstance(body, dict) or body.get("encoding") != "base64":
            raise TopicAuditError("unexpected blob response format")
        if body.get("sha") != sha:
            raise TopicAuditError("server returned a different Git blob")
        content = base64.b64decode(body["content"], validate=False)
    except (ValueError, KeyError, TypeError) as exc:
        raise TopicAuditError("invalid Git blob encoding") from exc
    if len(content) > MAX_BLOB_BYTES or _blob_sha(content) != sha:
        raise TopicAuditError("Git blob size or cryptographic integrity mismatch")
    return content


def audit(rows: list[dict], fetcher) -> dict:
    """Check exact pinned line and textual fingerprint for each reviewed label."""
    if not isinstance(rows, list) or not 1 <= len(rows) <= 25:
        raise TopicAuditError("1..25 reviewed README records required")
    results = []
    for entry in rows:
        contents = fetcher(entry)
        if not isinstance(contents, bytes):
            raise TopicAuditError("expected raw README blob bytes")
        if _blob_sha(contents) != entry["readme_blob_sha"]:
            raise TopicAuditError("source README Git hash changed")
        try:
            source_lines = contents.decode("utf-8").splitlines()
        except UnicodeError as exc:
            raise TopicAuditError("invalid UTF-8 README") from exc
        lineno = entry["line"]
        if lineno > len(source_lines) or entry["anchor"] not in source_lines[lineno - 1]:
            raise TopicAuditError(
                f"README fingerprint mismatch for {entry['repo']} line {lineno}"
            )
        results.append({
            "repo": entry["repo"],
            "github_id": entry["github_id"],
            "category": entry["category"],
            "readme_blob_sha": entry["readme_blob_sha"],
            "line": lineno,
            "status": "exact_blob_and_line_verified",
        })
    return {
        "schema_version": "1.0.0",
        "status": "read_only_evidence_audited",
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "audited": len(results),
        "items": results,
        "notice": "upstream self-descriptions, not independently tested capabilities",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify versioned README subject evidence")
    parser.add_argument("--check", action="store_true", help="Validate evidence registry offline")
    parser.add_argument("--limit", type=int, default=0, help="0 = all; 1..25 = bounded sample")
    parser.add_argument("--output-dir", type=Path, default=STAGE)
    args = parser.parse_args(argv)
    try:
        registered = list(load().values())
        if type(args.limit) is not int or not 0 <= args.limit <= 25:
            raise TopicAuditError("limit must be 0..25")
        selected = registered[:args.limit] if args.limit else registered
        if args.check:
            print(json.dumps({"readme_subjects": len(registered), "network": False}))
            return 0
        output = args.output_dir.resolve()
        if not output.is_relative_to(STAGE.resolve()):
            raise TopicAuditError("audit artifacts must remain under ignored staging root")
        token = os.environ.get("GITHUB_TOKEN")
        report = audit(selected, lambda row: fetch_blob(row, token))
        _write_atomic(output / "report.json", json.dumps(report, indent=2) + "\n")
        print(json.dumps({
            "status": report["status"], "audited": report["audited"],
            "full": len(selected) == len(registered),
        }, separators=(",", ":")))
        return 0
    except (TopicAuditError, OSError, ValueError) as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
