"""Reproducible tiny static index of historical evidence observation dates."""
from __future__ import annotations
import argparse
import json
import sys

from .agent import ROOT
from .freshness import snapshot

DEST = ROOT / "ai" / "evidence-dates.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify historical evidence-date manifest")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    encoded = json.dumps(snapshot(), ensure_ascii=False, separators=(",", ":")) + "\n"
    if args.write:
        DEST.parent.mkdir(parents=True, exist_ok=True)
        DEST.write_text(encoded, encoding="utf-8")
    elif not DEST.is_file() or DEST.read_text(encoding="utf-8") != encoded:
        print("ERROR: stale ai/evidence-dates.json", file=sys.stderr)
        return 1
    result = snapshot()
    print(json.dumps({"checked": not args.write, "numeric_ids": result["checked_numeric_ids"],
                      "documentary_subjects": result["readme_subjects"],
                      "bytes": len(encoded.encode())}, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
