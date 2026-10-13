"""Deterministic minimal index of individually checked catalog references."""
from __future__ import annotations

import argparse
import json
import sys

from .agent import ROOT
from .verified import load

DEST = ROOT / "ai" / "verified-targets.json"


def build() -> dict:
    ids, _ = load()
    rows = [ids[k] for k in sorted(ids)]
    return {
        "v": 1,
        "scope": "existence_checked_references_only",
        "n": len(rows),
        "r": [
            [row["github_id"], row["requested_slug"],
             row["canonical_slug"] if row["canonical_slug"].casefold() != row["requested_slug"].casefold() else "",
             1 if row["archived"] else 0]
            for row in rows
        ],
        "note": "GitHub existence checks only. Archived=1 is a warning, not a verdict. Cost, execution and security unverified.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate/check compact verified reference index")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    expected = json.dumps(build(), ensure_ascii=False, separators=(",", ":")) + "\n"
    if args.write:
        DEST.parent.mkdir(parents=True, exist_ok=True)
        DEST.write_text(expected, encoding="utf-8")
    elif not DEST.is_file() or DEST.read_text(encoding="utf-8") != expected:
        print("ERROR: verified target AI index missing/stale", file=sys.stderr)
        return 1
    print(json.dumps({"checked": not args.write, "references": build()["n"],
                      "bytes": len(expected.encode("utf-8"))}, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
