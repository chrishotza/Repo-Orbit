"""Deterministic, bounded owner-prefix pages for remote-only AI readers.

Routing requires only the first ASCII letter/digit of a GitHub owner. A
lightweight bucket manifest gives page boundaries. An agent downloads exactly
one page, never a giant README or the full corpus.

This is a discovery index, not a statement that a linked repository exists.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import re
import sys

from .agent import ROOT, _load

DEST = ROOT / "ai" / "owners"
PAGE_SIZE = 64
MAX_BYTES = 16384
ROLE = {"catalog": "c", "project": "p", "reference": "r"}


def encode(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n"


def bucket(owner: str) -> str:
    if not isinstance(owner, str) or not owner:
        raise ValueError("owner required")
    first = owner[0].casefold()
    return first if re.fullmatch(r"[a-z0-9]", first) else "_"


def build(records: list[dict] | None = None) -> dict[str, dict]:
    """Optional synthetic records for stress tests; corpus unchanged."""
    source = list(_load().values()) if records is None else records
    groups: dict[str, list[list]] = defaultdict(list)
    seen = set()
    for record in source:
        slug = record.get("r")
        if not isinstance(slug, str) or slug.count("/") != 1:
            raise ValueError("owner pages require owner/repository slugs")
        owner, name = slug.split("/")
        if not owner or not name:
            raise ValueError("empty owner or repo")
        canonical = slug.casefold()
        if canonical in seen:
            raise ValueError("duplicate canonical GitHub path in owner index")
        seen.add(canonical)
        role = ROLE.get(record.get("role"))
        if role is None or record.get("v") not in ("exists", "not_checked"):
            raise ValueError("invalid role or GitHub-existence assertion")
        groups[bucket(owner)].append(
            [slug, role, 1 if record["v"] == "exists" else 0]
        )
    output = {}
    root_groups = []
    for prefix in sorted(groups):
        entries = sorted(groups[prefix], key=lambda r: r[0].casefold())
        segments = []
        buffer = []
        for row in entries:
            candidate = buffer + [row]
            page = {"v": 1, "b": prefix, "i": len(segments), "r": candidate}
            if buffer and (len(candidate) > PAGE_SIZE or len(encode(page).encode("utf-8")) > MAX_BYTES):
                segments.append(buffer)
                buffer = [row]
            else:
                buffer = candidate
            if len(encode({"v": 1, "b": prefix, "i": len(segments),
                           "r": buffer}).encode("utf-8")) > MAX_BYTES:
                raise ValueError("single repository record exceeds page-byte budget")
        if buffer:
            segments.append(buffer)
        pages = []
        for ix, rows in enumerate(segments):
            filename = f"{ix:04d}.json"
            output[f"{prefix}/{filename}"] = {"v": 1, "b": prefix, "i": ix, "r": rows}
            pages.append([rows[0][0], rows[-1][0], len(rows), filename])
        output[f"{prefix}/index.json"] = {
            "v": 1, "b": prefix, "n": len(entries), "p": pages,
            "note": "Use first/last slug bounds to select one 64-record maximum page.",
        }
        root_groups.append([prefix, len(entries), len(segments)])
    output["index.json"] = {
        "v": 1, "route": "ai/owners/{first_lowercase_owner_character}/index.json",
        "page_max_rows": PAGE_SIZE, "page_max_bytes": MAX_BYTES,
        "groups": root_groups,
        "page_row_format": "[owner/repo,role(c/p/r),github_existence_checked(0/1)]",
        "note": "0=upstream reference only; 1=GitHub path previously checked. No runtime or free-cost guarantees.",
    }
    if sum(row[1] for row in root_groups) != len(source):
        raise ValueError("owner index lost a repository")
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify/build bounded AI owner index")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    docs = build()
    expected = set(docs)
    existing = {path.relative_to(DEST).as_posix()
                for path in DEST.rglob("*.json")} if DEST.exists() else set()
    if args.write:
        for stale in sorted(existing - expected):
            (DEST / stale).unlink()
        for name, doc in docs.items():
            path = DEST / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(encode(doc), encoding="utf-8")
    else:
        if existing != expected:
            print("ERROR: owner shards missing or stale", file=sys.stderr)
            return 1
        for name, doc in docs.items():
            if (DEST / name).read_text(encoding="utf-8") != encode(doc):
                print("ERROR: owner shard content stale: " + name, file=sys.stderr)
                return 1
    print(json.dumps({
        "pages": sum(name.endswith(".json") and
                     not name.endswith("index.json") for name in docs),
        "buckets": len(docs["index.json"]["groups"]),
        "records": sum(row[1] for row in docs["index.json"]["groups"]),
        "checked": not args.write,
    }, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
