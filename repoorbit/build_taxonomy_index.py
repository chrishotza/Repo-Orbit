"""Build compact category-specific shards for static-only AI navigation."""
from __future__ import annotations

import argparse
import json
import sys

from .agent import ROOT
from .taxonomy import categories, index

DEST = ROOT / "ai" / "categories"
ROLES = {"catalog": "c", "project": "p", "reference": "r"}
METHODS = {
    "editorial_seed_subject": "e",
    "slug_keyword_hint": "h",
    "ambiguous_slug_keywords": "a",
    "no_subject_evidence": "u",
}


def encode(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n"


def build() -> dict[str, dict]:
    descriptor = categories()
    buckets = index()
    outputs = {"index.json": {
        "v": 1,
        "scope": "subject_hints_not_capability_verification",
        "total": descriptor["total"],
        "cats": [[x["id"], x["en"], x["es"], x["n"]] for x in descriptor["categories"]],
        "row_format": "[repository_slug,role(c/p/r),exists(0/1),basis(e/h/a/u)]",
        "note": "Editorial seed topics and slug hints are not proof of purpose, function, license or cost.",
    }}
    for cat in descriptor["categories"]:
        name = cat["id"]
        rows = [
            [row["r"], ROLES[row["role"]], 1 if row["v"] == "exists" else 0,
             METHODS[reason["basis"]]]
            for row, reason in buckets[name]
        ]
        outputs[name + ".json"] = {"v": 1, "c": name, "r": rows}
    if sum(len(x["r"]) for key, x in outputs.items() if key != "index.json") != descriptor["total"]:
        raise ValueError("taxonomy output lost or duplicated a repository")
    return outputs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify/rebuild compact taxonomy shards")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    outputs = build()
    mismatches = []
    for name, data in outputs.items():
        path = DEST / name
        expected = encode(data)
        if args.write:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(expected, encoding="utf-8")
        elif not path.is_file() or path.read_text(encoding="utf-8") != expected:
            mismatches.append(name)
    if mismatches:
        print("ERROR: stale taxonomy shards: " + ",".join(mismatches), file=sys.stderr)
        return 1
    print(json.dumps({"files": len(outputs), "total": outputs["index.json"]["total"],
                      "checked": not args.write}, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
