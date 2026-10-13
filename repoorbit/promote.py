"""Safe promotion of licensed, staged sources into versioned approved snapshots.

The scheduled collector never changes main. This process is intended for a
reviewable bot branch/PR, and fails closed on missing evidence, unexpected
mass deletions, duplicate identities, incorrect baseline accounting or
untrusted paths. Older approved snapshots stay in Git history and in-tree.
"""
from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
import re
import sys

from . import agent, build_index, build_owner_index, build_status, incremental_delta, refresh, snapshots

SLUG = re.compile(r"^github:[a-z0-9_.-]+/[a-z0-9_.-]+$")
SHA = re.compile(r"^[0-9a-f]{40}$")
STAGED = re.compile(r"^data/snapshots/staged/[a-z0-9-]+\.jsonl$")
MAX_ADDED = 200
MAX_REMOVED = 50
MAX_REMOVAL_FRACTION = 0.15


class PromotionError(ValueError):
    """A source update cannot safely become an approved PR."""


def _parse_rows(path: Path, feed: dict, sha: str) -> list[dict]:
    if not path.is_file():
        raise PromotionError("staged snapshot missing")
    result, seen = [], set()
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            e = json.loads(line)
        except ValueError as exc:
            raise PromotionError("malformed staged JSONL") from exc
        ident = e.get("target_id")
        name = e.get("target_full_name")
        if not isinstance(ident, str) or not SLUG.fullmatch(ident):
            raise PromotionError("invalid staged GitHub identity")
        if not isinstance(name, str) or ident != "github:" + name.casefold():
            raise PromotionError("noncanonical staged identity")
        if ident in seen:
            raise PromotionError("duplicate staged repository identity")
        seen.add(ident)
        if (
            e.get("source_id") != feed["id"]
            or e.get("source_path") != "readme.md"
            or e.get("source_blob_sha") != sha
            or e.get("source_license") != "CC0-1.0"
            or e.get("target_url") != "https://github.com/" + name
            or e.get("target_verification") != "not_checked"
            or e.get("extraction_method") != "github_link_regex_v0.1"
            or type(e.get("source_line")) is not int
            or e["source_line"] < 1
        ):
            raise PromotionError("staged source provenance mismatch")
        try:
            date.fromisoformat(e["observed_at"])
        except (KeyError, TypeError, ValueError) as exc:
            raise PromotionError("invalid staged observation date") from exc
        result.append(e)
    if not result:
        raise PromotionError("cannot promote empty discovery snapshot")
    if result != sorted(result, key=lambda row: row["target_id"]):
        raise PromotionError("staged references must be deterministically sorted")
    return result


def plan_promotions(feeds: list[dict], staged: Path) -> list[dict]:
    report_file = staged / "report.json"
    try:
        report = json.loads(report_file.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise PromotionError("missing or invalid refresh report") from exc
    if report.get("status") != "staged_unreviewed_no_auto_commit" or report.get("schema_version") != "0.2.0":
        raise PromotionError("unexpected staged refresh schema/status")
    reported = report.get("results")
    if not isinstance(reported, list) or len(reported) != len(feeds):
        raise PromotionError("refresh report must describe every licensed feed exactly once")
    by_id = {r.get("source_id"): r for r in reported if isinstance(r, dict)}
    if len(by_id) != len(feeds):
        raise PromotionError("duplicate or missing source reports")
    changes = []
    proposed = []
    for feed in feeds:
        result = by_id.get(feed["id"])
        if result is None:
            raise PromotionError("unknown source in refresh report")
        sha = result.get("source_blob_sha")
        staged_rel = result.get("staged_snapshot")
        if not isinstance(sha, str) or not SHA.fullmatch(sha):
            raise PromotionError("invalid source blob SHA")
        expected_name = feed["repository"].replace("/", "-").casefold() + ".jsonl"
        expected_rel = "data/snapshots/staged/" + expected_name
        if staged_rel != expected_rel or STAGED.fullmatch(staged_rel) is None:
            raise PromotionError("untrusted snapshot location")
        if result.get("source_license") != "CC0-1.0" or result.get("baseline") != feed["baseline"]:
            raise PromotionError("unexpected source license or pinned baseline")
        rows = _parse_rows(staged / expected_name, feed, sha)
        proposed.append((feed, rows, {"source_id": feed["id"]}))
        old = refresh._baseline_ids(feed)
        new = {e["target_id"] for e in rows}
        added, removed, unchanged = len(new - old), len(old - new), len(new & old)
        expected = {
            "baseline_count": len(old), "current_count": len(new),
            "added": added, "removed": removed, "unchanged": unchanged,
        }
        if any(result.get(key) != value for key, value in expected.items()):
            raise PromotionError("staged report counts disagree with independent baseline comparison")
        if added == 0 and removed == 0:
            continue
        if added > MAX_ADDED or removed > MAX_REMOVED or removed > max(5, int(len(old) * MAX_REMOVAL_FRACTION)):
            raise PromotionError("excessive discovery churn requires manual investigation")
        day = max(e["observed_at"] for e in rows)
        basename = feed["repository"].replace("/", "-").casefold()
        new_path = f"data/discoveries/{basename}-{day}-{sha[:12]}.jsonl"
        if not re.fullmatch(r"data/discoveries/[a-z0-9-]+\.jsonl", new_path):
            raise PromotionError("invalid destination snapshot path")
        target = refresh.ROOT / new_path
        if target.exists():
            raise PromotionError("destination snapshot already exists; refusing overwrite")
        changes.append({
            "source_id": feed["id"], "path": new_path, "rows": rows,
            "added": added, "removed": removed, "previous": feed["baseline"],
        })
    try:
        staged_global = json.loads((staged / "global-delta.json").read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        raise PromotionError("missing or invalid global source delta") from exc
    expected_global = incremental_delta.compare(proposed)
    if staged_global != expected_global:
        raise PromotionError("global source delta differs from independently reconstructed source evidence")
    expected_summary = {
        "report": "global-delta.json",
        "counts": expected_global["counts"],
        "baseline_unique_paths": expected_global["baseline_unique_paths"],
        "proposed_unique_paths": expected_global["proposed_unique_paths"],
    }
    if report.get("global_delta") != expected_summary:
        raise PromotionError("global source delta summary mismatch")
    return changes


def apply(changes: list[dict]) -> dict:
    if not changes:
        return {"status": "no_change", "sources": 0}
    feeds_path = refresh.FEEDS
    data = json.loads(feeds_path.read_text(encoding="utf-8"))
    changes_by_id = {c["source_id"]: c for c in changes}
    for item in data["sources"]:
        change = changes_by_id.get(item["id"])
        if change is None:
            continue
        destination = refresh.ROOT / change["path"]
        content = "".join(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n" for row in change["rows"])
        refresh._write_atomic(destination, content)
        item["baseline"] = change["path"]
    refresh._write_atomic(feeds_path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    # The agent model caches the old registry for this process; clear before generating.
    agent._load.cache_clear()
    build_index.main(["--write"])
    build_owner_index.main(["--write"])
    build_status.main(["--write"])
    return {
        "status": "prepared_for_review",
        "sources": len(changes),
        "added": sum(c["added"] for c in changes),
        "removed": sum(c["removed"] for c in changes),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare approved-feed update for review")
    parser.add_argument("--apply", action="store_true", help="Write a reviewable local change set")
    parser.add_argument("--staged-dir", type=Path, default=refresh.STAGING)
    args = parser.parse_args(argv)
    try:
        staged = args.staged_dir.resolve()
        if not staged.is_relative_to(refresh.STAGING.resolve()):
            raise PromotionError("staged directory must remain under the ignored staging root")
        plans = plan_promotions(refresh.load_feeds(), staged)
        result = (
            apply(plans) if args.apply else
            {"status": "dry_run", "sources": len(plans),
             "added": sum(c["added"] for c in plans),
             "removed": sum(c["removed"] for c in plans)}
        )
        print(json.dumps(result, separators=(",", ":")))
        return 0
    except (PromotionError, refresh.RefreshError, ValueError, OSError) as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
