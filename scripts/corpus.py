#!/usr/bin/env python3
"""RepoOrbit corpus CLI: validate, summarize, and enrich a small verified seed set.

Python 3.10+. Standard library only. Never copies third-party README content.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import date, datetime, timezone
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "data" / "sources.json"
REPOSITORIES = ROOT / "data" / "repositories.jsonl"
DEFAULT_SNAPSHOT = ROOT / "data" / "snapshots" / "latest.jsonl"
SOURCE_TYPES = {"meta_index", "curated_catalog", "collection"}
VERIFICATION = {"repository_exists"}
COST = {"unknown", "free_verified", "free_with_limits", "paid_required", "mixed"}
FUNCTIONAL = {"not_run", "passed", "failed", "inconclusive"}
REPO_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
API_ROOT = "https://api.github.com"


class CorpusError(Exception):
    """An actionable validation or sync failure."""


def canonical_id(repository: str) -> str:
    return "github:" + repository.casefold()


def github_url(repository: str) -> str:
    return "https://github.com/" + repository


def assert_date(value: object, field: str) -> None:
    if not isinstance(value, str):
        raise CorpusError(f"{field}: expected ISO date string")
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise CorpusError(f"{field}: invalid ISO date {value!r}") from exc


def assert_repository_name(value: object, field: str) -> str:
    if not isinstance(value, str) or not REPO_PATTERN.fullmatch(value):
        raise CorpusError(f"{field}: expected GitHub owner/repository")
    if value.split("/")[0] in {".", ".."} or value.split("/")[1] in {".", ".."}:
        raise CorpusError(f"{field}: invalid owner/repository")
    return value


def assert_topics(value: object, field: str) -> None:
    if not isinstance(value, list) or not value:
        raise CorpusError(f"{field}: expected a nonempty array")
    if any(not isinstance(x, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", x) for x in value):
        raise CorpusError(f"{field}: topics must be nonempty lower-case slugs")
    if len(value) != len(set(value)):
        raise CorpusError(f"{field}: duplicate topics")


def load_sources(path: Path = SOURCES) -> list[dict]:
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise CorpusError(f"{path}: {exc}") from exc
    if doc.get("schema_version") != "0.1.0" or not isinstance(doc.get("sources"), list):
        raise CorpusError("sources registry: invalid schema_version or sources")
    if not doc["sources"]:
        raise CorpusError("sources registry is empty")
    assert_date(doc.get("generated_at"), "generated_at")
    seen = set()
    for i, item in enumerate(doc["sources"], 1):
        key = f"source #{i}"
        if not isinstance(item, dict):
            raise CorpusError(f"{key}: expected object")
        name = assert_repository_name(item.get("repository"), f"{key}.repository")
        unique = name.casefold()
        if unique in seen:
            raise CorpusError(f"{key}: duplicate canonical repository {name}")
        seen.add(unique)
        if item.get("id") != canonical_id(name) or item.get("url") != github_url(name):
            raise CorpusError(f"{key}: invalid stable id or canonical URL")
        if item.get("type") not in SOURCE_TYPES:
            raise CorpusError(f"{key}: invalid type")
        assert_topics(item.get("topics"), f"{key}.topics")
        if item.get("source_class") != "github_repository":
            raise CorpusError(f"{key}: unexpected source_class")
        if item.get("verification") not in VERIFICATION:
            raise CorpusError(f"{key}: unsupported verification claim")
        assert_date(item.get("verified_at"), f"{key}.verified_at")
        if item.get("reuse_mode") != "links_and_metadata_only":
            raise CorpusError(f"{key}: unsafe/unsupported reuse mode")
        if item.get("catalog_ingestion_enabled") is not False:
            raise CorpusError(f"{key}: catalog ingestion must not be silently enabled")
        if not isinstance(item.get("scope"), str) or not item["scope"].strip():
            raise CorpusError(f"{key}: scope is required")
    return doc["sources"]


def load_repositories(path: Path = REPOSITORIES) -> list[dict]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise CorpusError(f"{path}: {exc}") from exc
    records = []
    seen = set()
    for i, line in enumerate(lines, 1):
        if not line.strip():
            raise CorpusError(f"repository line {i}: blank records are not allowed")
        try:
            item = json.loads(line)
        except json.JSONDecodeError as exc:
            raise CorpusError(f"repository line {i}: invalid JSON: {exc}") from exc
        if not isinstance(item, dict):
            raise CorpusError(f"repository line {i}: expected object")
        name = assert_repository_name(item.get("full_name"), f"repository line {i}.full_name")
        unique = name.casefold()
        if unique in seen:
            raise CorpusError(f"repository line {i}: duplicate canonical repository {name}")
        seen.add(unique)
        if item.get("id") != canonical_id(name) or item.get("url") != github_url(name):
            raise CorpusError(f"repository line {i}: invalid stable id or URL")
        assert_topics(item.get("topics"), f"repository line {i}.topics")
        if item.get("verification") not in VERIFICATION:
            raise CorpusError(f"repository line {i}: unsupported verification claim")
        assert_date(item.get("last_verified_at"), f"repository line {i}.last_verified_at")
        if not isinstance(item.get("discovered_via"), list) or not item["discovered_via"] or any(
            not isinstance(s, str) or not s.strip() for s in item["discovered_via"]
        ):
            raise CorpusError(f"repository line {i}: missing provenance")
        if item.get("cost") not in COST or item.get("functional_test") not in FUNCTIONAL:
            raise CorpusError(f"repository line {i}: invalid cost/test status")
        for key in ("stars", "github_id"):
            val = item.get(key)
            if val is not None and (type(val) is not int or val < 0):
                raise CorpusError(f"repository line {i}: invalid {key}")
        if item.get("archived") is not None and type(item["archived"]) is not bool:
            raise CorpusError(f"repository line {i}: invalid archived")
        for key in ("language", "license_spdx", "updated_at", "metadata_fetched_at"):
            val = item.get(key)
            if val is not None and not isinstance(val, str):
                raise CorpusError(f"repository line {i}: invalid {key}")
        records.append(item)
    if not records:
        raise CorpusError("repository corpus has no records")
    return records


def validate() -> tuple[list[dict], list[dict]]:
    sources, records = load_sources(), load_repositories()
    overlap = {r["id"] for r in records} & {s["id"] for s in sources}
    if overlap:
        raise CorpusError(f"source/project seed overlap: {sorted(overlap)}")
    return sources, records


def fetch_metadata(full_name: str, token: str | None, timeout: float = 15) -> dict:
    req = Request(
        f"{API_ROOT}/repos/{full_name}",
        headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "RepoOrbit-Corpus/0.1 (+https://github.com/chrishotza/Repo-Orbit)",
            **({"Authorization": f"Bearer {token}"} if token else {}),
        },
    )
    try:
        with urlopen(req, timeout=timeout) as response:
            payload = json.load(response)
    except HTTPError as exc:
        detail = exc.reason
        if exc.code in (403, 429):
            detail = "rate-limited or access forbidden: check GITHUB_TOKEN and API limits"
        raise CorpusError(f"GitHub API {full_name}: HTTP {exc.code}: {detail}") from exc
    except (URLError, TimeoutError, ValueError, OSError) as exc:
        raise CorpusError(f"GitHub API {full_name}: {exc}") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("id"), int):
        raise CorpusError(f"GitHub API {full_name}: unexpected response")
    return payload


def enrich(seed: dict, payload: dict, now: datetime) -> dict:
    item = dict(seed)
    item["github_id"] = payload["id"]
    item["github_full_name"] = payload.get("full_name")
    item["stars"] = payload.get("stargazers_count")
    item["archived"] = payload.get("archived")
    item["language"] = payload.get("language")
    item["updated_at"] = payload.get("updated_at")
    license_info = payload.get("license") or {}
    spdx = license_info.get("spdx_id") if isinstance(license_info, dict) else None
    item["license_spdx"] = spdx if spdx and spdx != "NOASSERTION" else None
    item["metadata_fetched_at"] = now.isoformat().replace("+00:00", "Z")
    item["last_verified_at"] = now.date().isoformat()
    # Neither availability nor an SPDX label proves that a project runs or is free.
    item["verification"] = "repository_exists"
    return item


def write_jsonl_atomic(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, prefix=".repoorbit-",
        suffix=".tmp", delete=False
    ) as handle:
        temp = Path(handle.name)
        try:
            for item in sorted(records, key=lambda r: r["id"]):
                handle.write(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        except BaseException:
            temp.unlink(missing_ok=True)
            raise
    os.replace(temp, path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="RepoOrbit seed corpus utility")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate", help="Validate identity, provenance and seed invariants offline")
    sub.add_parser("stats", help="Report truthful offline corpus counts")
    sync = sub.add_parser("sync", help="Fetch public GitHub metadata for seed projects")
    sync.add_argument("--limit", type=int, default=10, help="Seed count; 0 means all")
    sync.add_argument("--output", type=Path, default=DEFAULT_SNAPSHOT)
    sync.add_argument("--delay", type=float, default=1, help="Pause between requests in seconds")
    sync.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    try:
        sources, records = validate()
        if args.command == "validate":
            print(f"OK: {len(sources)} verified discovery roots, {len(records)} project seeds")
            return 0
        if args.command == "stats":
            print(json.dumps({
                "schema_version": "0.1.0",
                "verified_source_repositories": len(sources),
                "seed_project_repositories": len(records),
                "source_types": dict(sorted(Counter(x["type"] for x in sources).items())),
                "verified_functional_projects": sum(x["functional_test"] == "passed" for x in records),
                "verified_free_projects": sum(x["cost"] == "free_verified" for x in records),
                "catalogs_parsed": sum(x["catalog_ingestion_enabled"] for x in sources),
                "coverage_claim": "seed_only_not_comprehensive",
            }, indent=2))
            return 0
        if args.limit < 0 or args.delay < 0:
            raise CorpusError("--limit and --delay must not be negative")
        target = args.output.resolve()
        if target in {SOURCES.resolve(), REPOSITORIES.resolve()}:
            raise CorpusError("refusing to overwrite immutable seed inputs")
        selection = sorted(records, key=lambda r: r["id"])
        if args.limit:
            selection = selection[:args.limit]
        if args.dry_run:
            for entry in selection:
                print(entry["full_name"])
            return 0
        token = os.environ.get("GITHUB_TOKEN")
        now = datetime.now(timezone.utc)
        enriched = []
        for i, entry in enumerate(selection, 1):
            print(f"[{i}/{len(selection)}] {entry['full_name']}", file=sys.stderr)
            enriched.append(enrich(entry, fetch_metadata(entry["full_name"], token), now))
            if i < len(selection) and args.delay:
                time.sleep(args.delay)
        write_jsonl_atomic(target, enriched)
        print(f"Wrote {len(enriched)} metadata-enriched records to {target}")
        return 0
    except CorpusError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
