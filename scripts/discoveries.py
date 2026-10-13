#!/usr/bin/env python3
"""Inspect and reproduce licensed GitHub-link discovery snapshots.

Offline, stdlib-only. This extracts *references*, not target-project validation.
"""
from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
import re
import sys

from corpus import ROOT, CorpusError, canonical_id, github_url, load_sources

DISCOVERY_DIR = ROOT / "data" / "discoveries"
GH_LINK = re.compile(r"https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)", re.I)
SHA = re.compile(r"^[0-9a-f]{40}$")
RESERVED = {
    "topics", "search", "features", "orgs", "organizations", "settings",
    "sponsors", "login", "logout", "signup", "about", "site", "explore",
    "marketplace", "enterprise", "pricing", "issues", "pulls", "apps", "new",
    "users", "trending"
}
ALLOWED_LICENSES = {"CC0-1.0"}


def extract_references(
    text: str, source_repo: str, source_sha: str, observed_at: str,
    source_license: str
) -> list[dict]:
    if not SHA.fullmatch(source_sha):
        raise CorpusError("source SHA must be a 40-character hexadecimal blob SHA")
    if source_license not in ALLOWED_LICENSES:
        raise CorpusError("source license requires reviewed, explicit support")
    try:
        date.fromisoformat(observed_at)
    except ValueError as exc:
        raise CorpusError("observed_at must be an ISO date") from exc
    known = {x["repository"].casefold() for x in load_sources()}
    if source_repo.casefold() not in known:
        raise CorpusError("source is not registered")
    source_id = canonical_id(source_repo)
    found = {}
    for line_no, line in enumerate(text.splitlines(), start=1):
        for match in GH_LINK.finditer(line):
            if match.group(1).casefold() in RESERVED:
                continue
            repo = match.group(1) + "/" + match.group(2).rstrip(".,;:")
            ident = canonical_id(repo)
            if ident == source_id or ident in found:
                continue
            found[ident] = {
                "source_id": source_id,
                "source_path": "readme.md",
                "source_line": line_no,
                "source_blob_sha": source_sha,
                "source_license": source_license,
                "target_id": ident,
                "target_full_name": repo,
                "target_url": github_url(repo),
                "observed_at": observed_at,
                "target_verification": "not_checked",
                "extraction_method": "github_link_regex_v0.1",
            }
    return sorted(found.values(), key=lambda x: x["target_id"])


def validate_snapshot(path: Path, registered_sources: set[str]) -> int:
    count, seen = 0, set()
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise CorpusError(f"{path}: {exc}") from exc
    if not lines:
        raise CorpusError(f"{path}: empty snapshot")
    for line_no, line in enumerate(lines, start=1):
        try:
            row = json.loads(line)
        except (ValueError, TypeError) as exc:
            raise CorpusError(f"{path}:{line_no}: invalid JSON") from exc
        if not isinstance(row, dict):
            raise CorpusError(f"{path}:{line_no}: expected object")
        source_id = row.get("source_id")
        target_id = row.get("target_id")
        full = row.get("target_full_name")
        if source_id not in registered_sources:
            raise CorpusError(f"{path}:{line_no}: source is not registered")
        if not isinstance(full, str) or target_id != canonical_id(full):
            raise CorpusError(f"{path}:{line_no}: target identity mismatch")
        if row.get("target_url") != github_url(full):
            raise CorpusError(f"{path}:{line_no}: target URL mismatch")
        if row.get("target_verification") != "not_checked":
            raise CorpusError(f"{path}:{line_no}: unsupported validation claim")
        if row.get("source_license") not in ALLOWED_LICENSES:
            raise CorpusError(f"{path}:{line_no}: unsupported license assertion")
        if row.get("extraction_method") != "github_link_regex_v0.1":
            raise CorpusError(f"{path}:{line_no}: unknown extraction method")
        sha = row.get("source_blob_sha")
        if not isinstance(sha, str) or not SHA.fullmatch(sha):
            raise CorpusError(f"{path}:{line_no}: invalid source blob SHA")
        if row.get("source_path") != "readme.md":
            raise CorpusError(f"{path}:{line_no}: unrecognized source path")
        if type(row.get("source_line")) is not int or row["source_line"] < 1:
            raise CorpusError(f"{path}:{line_no}: invalid source line")
        try:
            date.fromisoformat(row.get("observed_at", ""))
        except (TypeError, ValueError) as exc:
            raise CorpusError(f"{path}:{line_no}: invalid observation date") from exc
        key = (source_id, sha, target_id)
        if key in seen:
            raise CorpusError(f"{path}:{line_no}: duplicate edge")
        seen.add(key)
        count += 1
    return count


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="RepoOrbit discovery snapshots")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate")
    sub.add_parser("stats")
    extract = sub.add_parser("extract", help="Parse already downloaded, licensed README links")
    extract.add_argument("--input", type=Path, required=True)
    extract.add_argument("--output", type=Path, required=True)
    extract.add_argument("--source-repo", required=True)
    extract.add_argument("--source-sha", required=True)
    extract.add_argument("--source-license", default="CC0-1.0")
    extract.add_argument("--date", required=True, dest="observed_at")
    args = parser.parse_args(argv)
    try:
        source_ids = {x["id"] for x in load_sources()}
        if args.command in {"validate", "stats"}:
            files = sorted(DISCOVERY_DIR.glob("*.jsonl"))
            if not files:
                raise CorpusError("no discovery snapshots found")
            counts = {str(p.relative_to(ROOT)): validate_snapshot(p, source_ids) for p in files}
            if args.command == "stats":
                print(json.dumps({"snapshots": counts, "total_unverified_references": sum(counts.values())}, indent=2))
            else:
                print(f"OK: {len(files)} discovery snapshots, {sum(counts.values())} unverified references")
            return 0
        if args.output.resolve() in {
            (ROOT / "data" / "sources.json").resolve(),
            (ROOT / "data" / "repositories.jsonl").resolve(),
        }:
            raise CorpusError("refusing to overwrite seed inputs")
        try:
            content = args.input.read_text(encoding="utf-8")
        except OSError as exc:
            raise CorpusError(str(exc)) from exc
        edges = extract_references(
            content, args.source_repo, args.source_sha,
            args.observed_at, args.source_license
        )
        if not edges:
            raise CorpusError("no GitHub links found")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in edges),
            encoding="utf-8",
        )
        print(f"Wrote {len(edges)} UNVERIFIED references to {args.output}")
        return 0
    except CorpusError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
