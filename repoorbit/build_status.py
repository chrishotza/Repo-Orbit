"""Build a compact, reproducible AI-readable corpus status manifest."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import sys

from .agent import ROOT, _load
from .identity import load as load_verified_identities
from .snapshots import approved_discoveries

DEST = ROOT / "ai" / "status.json"
SOURCES = ROOT / "data" / "sources.json"
PROJECTS = ROOT / "data" / "repositories.jsonl"
FEEDS = ROOT / "data" / "feeds.json"


def build() -> dict:
    sources = json.loads(SOURCES.read_text(encoding="utf-8"))["sources"]
    projects = [json.loads(line) for line in PROJECTS.read_text(encoding="utf-8").splitlines() if line.strip()]
    feeds = json.loads(FEEDS.read_text(encoding="utf-8"))["sources"]
    counts: Counter[str] = Counter()
    by_target: defaultdict[str, set[str]] = defaultdict(set)
    observed_dates = []
    for path in approved_discoveries():
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            edge = json.loads(line)
            counts[edge["source_id"]] += 1
            by_target[edge["target_id"]].add(edge["source_id"])
            observed_dates.append(edge["observed_at"])
    records = _load()
    return {
        "v": 1,
        "as_of": max(observed_dates),
        "scope": "partial_repository_reference_index",
        "unique_slugs": len(records),
        "catalog_seeds": len(sources),
        "project_seeds_existence_checked": len(projects),
        "numeric_seed_ids_checked": len(load_verified_identities()[0]),
        "unverified_only": sum(x["v"] == "not_checked" for x in records.values()),
        "discovery_edges": sum(counts.values()),
        "shared_targets_across_feeds": sum(len(v) > 1 for v in by_target.values()),
        "source_edges": dict(sorted(counts.items())),
        "licensed_refresh_feeds": sum(x.get("enabled") is True for x in feeds),
        "functional_tests_passed": sum(x.get("working") == "passed" for x in records.values()),
        "free_execution_verified": sum(x.get("cost") == "free_verified" for x in records.values()),
        "staged_only": True,
        "hint": "References do not imply actual project existence; seed existence does not imply working or free.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify/rebuild compact AI corpus status")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    encoded = json.dumps(build(), ensure_ascii=False, separators=(",", ":")) + "\n"
    if args.write:
        DEST.parent.mkdir(parents=True, exist_ok=True)
        DEST.write_text(encoded, encoding="utf-8")
    elif not DEST.is_file() or DEST.read_text(encoding="utf-8") != encoded:
        print("ERROR: ai/status.json missing or stale", file=sys.stderr)
        return 1
    print(json.dumps({"bytes": len(encoded.encode("utf-8")), "checked": not args.write}, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
