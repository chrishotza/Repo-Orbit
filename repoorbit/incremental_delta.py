"""Global, source-aware incremental discovery delta. Staging ONLY.

Compares all approved source snapshots with all newly observed source snapshots
in a single pass, deduplicating target paths across catalogs while preserving
every exact source/blob/line pointer.

No GitHub-path existence, immutable numeric ID, functionality or free-cost
claim is inferred. An upstream removal is never proof of repository deletion.
"""
from __future__ import annotations

from collections import defaultdict
import json
import re

from .agent import ROOT
from .identity import canonical_slug
from .snapshots import approved_discoveries

SHA = re.compile(r"^[0-9a-f]{40}$")
MAX_EDGES = 1_000_000


class DeltaError(ValueError):
    """Invalid/ambiguous licensed source evidence; refuse proposed promotion."""


def _collect(streams: list[tuple[str, list[dict]]], allowed: set[str]) -> dict[str, dict]:
    indexed = {}
    edge_count = 0
    for source, records in streams:
        if source not in allowed or not isinstance(records, list):
            raise DeltaError("unapproved source stream")
        source_seen = set()
        for edge in records:
            edge_count += 1
            if edge_count > MAX_EDGES:
                raise DeltaError("too many discovery edges for this staging run")
            if not isinstance(edge, dict) or edge.get("source_id") != source:
                raise DeltaError("source mismatch in discovery edge")
            if edge.get("source_license") != "CC0-1.0":
                raise DeltaError("unreviewed source license")
            if edge.get("target_verification") != "not_checked":
                raise DeltaError("catalog edges cannot claim functional verification")
            name = edge.get("target_full_name")
            key = canonical_slug(name)
            if edge.get("target_id") != "github:" + key:
                raise DeltaError("target slug and identity do not agree")
            if edge.get("target_url") != "https://github.com/" + name:
                raise DeltaError("target URL does not match source name")
            sha = edge.get("source_blob_sha")
            line = edge.get("source_line")
            if not isinstance(sha, str) or not SHA.fullmatch(sha):
                raise DeltaError("missing pinned source blob")
            if type(line) is not int or line <= 0:
                raise DeltaError("missing source line evidence")
            if key in source_seen:
                raise DeltaError("duplicate target within one source")
            source_seen.add(key)
            entry = indexed.setdefault(key, {"r": name, "sources": {}})
            entry["sources"][source] = {"s": source, "sha": sha, "line": line}
    return indexed


def _approved() -> list[tuple[str, list[dict]]]:
    streams = []
    for path in approved_discoveries():
        with path.open(encoding="utf-8") as inp:
            rows = [json.loads(line) for line in inp if line.strip()]
        if not rows:
            raise DeltaError("empty authoritative source snapshot")
        streams.append((rows[0]["source_id"], rows))
    return streams


def compare(plans: list[tuple[dict, list[dict], dict]],
            baselines: list[tuple[str, list[dict]]] | None = None) -> dict:
    """Produce a bounded change-only review report across *all* source feeds.

    Plans are the return value of refresh.plan_refresh(). No network or writes.
    An optional test-only baseline parameter avoids touching the real corpus.
    """
    from .refresh import load_feeds
    permitted = {row["id"] for row in load_feeds()}
    expected = {feed["id"] for feed in load_feeds()}
    if not isinstance(plans, list) or len(plans) != len(expected):
        raise DeltaError("all approved feeds must be examined together")
    current_streams = []
    source_ids = set()
    for feed, edges, detail in plans:
        if not isinstance(feed, dict) or feed.get("id") not in expected:
            raise DeltaError("unapproved proposed feed")
        source = feed["id"]
        if source in source_ids:
            raise DeltaError("duplicate proposed source")
        source_ids.add(source)
        if not isinstance(detail, dict) or detail.get("source_id") != source:
            raise DeltaError("source report mismatch")
        current_streams.append((source, edges))
    if source_ids != permitted:
        raise DeltaError("missing approved feed in proposed snapshot")
    old_streams = _approved() if baselines is None else baselines
    if {source for source, _ in old_streams} != permitted or len(old_streams) != len(permitted):
        raise DeltaError("baseline does not contain each approved source exactly once")
    old = _collect(old_streams, permitted)
    new = _collect(current_streams, permitted)
    from .identity import load as seed_load
    from .verified import load as target_load
    _, seed_aliases = seed_load()
    _, checked_aliases = target_load()
    changes = []
    counts = {"new_unverified_paths": 0, "new_links_to_known_paths": 0,
              "removed_from_sources_not_deleted": 0, "source_membership_changes": 0,
              "unchanged_paths": 0}
    for slug in sorted(set(old) | set(new)):
        before = old.get(slug)
        after = new.get(slug)
        before_sources = set(before["sources"]) if before else set()
        after_sources = set(after["sources"]) if after else set()
        if before_sources == after_sources:
            counts["unchanged_paths"] += 1
            continue
        if not before:
            category = ("new_links_to_known_paths" if slug in seed_aliases
                        or slug in checked_aliases else "new_unverified_paths")
        elif not after:
            category = "removed_from_sources_not_deleted"
        else:
            category = "source_membership_changes"
        counts[category] += 1
        provenance = after["sources"] if after else {}
        changes.append({
            "r": (after or before)["r"], "change": category,
            "previous_sources": sorted(before_sources),
            "proposed_sources": sorted(after_sources),
            "new_evidence": [provenance[s] for s in sorted(provenance)],
            "identity": "not_individually_checked" if category == "new_unverified_paths"
                        else "not_derived_from_feed_change",
        })
    return {
        "v": 1, "status": "unreviewed_global_source_delta",
        "baseline_unique_paths": len(old),
        "proposed_unique_paths": len(new),
        "baseline_edges": sum(len(row["sources"]) for row in old.values()),
        "proposed_edges": sum(len(row["sources"]) for row in new.values()),
        "counts": counts, "changes": changes,
        "note": "Source-link changes only: no automatic approvals; removals do not imply deleted repos; new names may redirect to known numeric IDs.",
    }


def encode(report: dict) -> str:
    """Compact machine-readable delta; current source row identifiers only."""
    return json.dumps(report, ensure_ascii=False, separators=(",", ":")) + "\n"
