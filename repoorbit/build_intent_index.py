"""Deterministic tiny static bilingual intent routing index.

The generated file is deliberately limited to explicitly reviewed aliases.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .agent import ROOT

SOURCE = ROOT / "data" / "intent_map.json"
TARGET = ROOT / "ai" / "intent.json"


def build() -> dict:
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    if data.get("schema_version") != "0.1.0":
        raise ValueError("unsupported intent schema")
    return {
        "v": 1,
        "semantics": "curated_bilingual_upstream_documentation_not_runtime_verified",
        "a": [[item["id"], item["aliases"], item["repositories"]] for item in data["intents"]],
        "cost_verified": False,
        "use": "match normalized words/phrases; return linked repo paths only; never infer free execution; no match means no known intent",
        "provenance": "data/intent_map.json",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Rebuild/verify compact agent intent manifest")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    expected = json.dumps(build(), ensure_ascii=False, separators=(",", ":")) + "\n"
    if args.write:
        TARGET.parent.mkdir(parents=True, exist_ok=True)
        TARGET.write_text(expected, encoding="utf-8")
    elif not TARGET.is_file() or TARGET.read_text(encoding="utf-8") != expected:
        print("ERROR: ai/intent.json is stale or missing", file=sys.stderr)
        return 1
    print(json.dumps({"intents": len(build()["a"]), "bytes": len(expected.encode("utf-8")), "checked": not args.write}, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
