"""Generate and validate tiny, independently addressable static AI term indexes.

These are lexical navigation aids, not verified search results. Rebuild from
existing licensed references; never add unverified facts.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import string
import sys

from .agent import ROOT, STOP, _load, tokenize

LETTERS = string.ascii_lowercase + string.digits
SKIP = STOP | {"awesome", "list", "lists", "project", "projects", "code", "tool", "tools"}
DEST = ROOT / "ai" / "terms"


def build() -> dict[str, dict]:
    records = sorted(_load().values(), key=lambda x: x["r"].casefold())
    by_letter: dict[str, dict[str, set[str]]] = {
        letter: defaultdict(set) for letter in LETTERS
    }
    names = {x["r"].casefold(): x for x in records}
    for row in records:
        terms = set(tokenize(row["r"] + " " + " ".join(row.get("tags", []))))
        for term in terms:
            if len(term) < 2 or term in SKIP or term[0] not in LETTERS:
                continue
            by_letter[term[0]][term].add(row["r"].casefold())
    output = {}
    for letter in LETTERS:
        groups = by_letter[letter]
        in_bucket = sorted(set().union(*groups.values()) if groups else set())
        idx = {name: pos for pos, name in enumerate(in_bucket)}
        rows = [
            [names[name]["r"],
             {"catalog": "c", "project": "p", "reference": "u"}[names[name]["role"]],
             1 if names[name]["v"] == "exists" else 0]
            for name in in_bucket
        ]
        terms = {term: sorted(idx[x] for x in groups[term]) for term in sorted(groups)}
        output[letter] = {"v": 1, "r": rows, "t": terms}
    return output


def encode(doc: dict) -> str:
    return json.dumps(doc, ensure_ascii=False, separators=(",", ":")) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check or refresh RepoOrbit machine-only static index")
    parser.add_argument("--write", action="store_true", help="Rebuild deterministic term shards")
    args = parser.parse_args(argv)
    output = build()
    errors = []
    for letter, doc in output.items():
        path = DEST / (letter + ".json")
        expected = encode(doc)
        if args.write:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(expected, encoding="utf-8")
        else:
            if not path.is_file() or path.read_text(encoding="utf-8") != expected:
                errors.append(letter)
    if errors:
        print("ERROR: missing or stale AI index shards: " + ",".join(errors), file=sys.stderr)
        return 1
    print(json.dumps({
        "shards": len(output),
        "terms": sum(len(x["t"]) for x in output.values()),
        "rows_across_shards": sum(len(x["r"]) for x in output.values()),
        "checked": not args.write,
    }, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
