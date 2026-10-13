"""Deterministic, small, remote-readable numeric ID index for AI-only clients."""
from __future__ import annotations

import argparse
import json
import sys

from .agent import ROOT
from .identity import load

OUT = ROOT / "ai" / "identities.json"


def build() -> dict:
    records, _ = load()
    ordered = [records[k] for k in sorted(records)]
    return {
        "v": 1,
        "as_of": max(row["observed_on"] for row in ordered),
        "scope": "individually_checked_seed_repositories_only",
        "n": len(ordered),
        "r": [
            [item["github_id"], item["canonical_slug"],
             "c" if item["role"] == "catalog" else "p"]
            for item in ordered
        ],
        "note": "Numeric identity only; no execution, license or cost validation.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify/publish small AI numeric-ID index")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    encoded = json.dumps(build(), ensure_ascii=False, separators=(",", ":")) + "\n"
    if args.write:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(encoded, encoding="utf-8")
    elif not OUT.is_file() or OUT.read_text(encoding="utf-8") != encoded:
        print("ERROR: ai/identities.json missing or stale", file=sys.stderr)
        return 1
    print(json.dumps({
        "identities": build()["n"],
        "bytes": len(encoded.encode("utf-8")),
        "checked": not args.write,
    }, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
