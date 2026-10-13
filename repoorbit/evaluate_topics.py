"""Versioned bilingual phrase-contract smoke tests, not semantic accuracy.

These examples are human-authored with knowledge of the curated aliases; they
measure routing consistency only. Do not report as held-out real-world quality.
"""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path
import sys

from .agent import ROOT
from .route_topic import route_topic, aliases

DATA = ROOT / "data" / "topic_route_probes.jsonl"


def evaluate() -> dict:
    rows = [json.loads(line) for line in DATA.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not 20 <= len(rows) <= 100:
        raise ValueError("bilingual probe set must contain 20..100 cases")
    used = set()
    mistakes = []
    counts = Counter()
    langs = Counter()
    for row in rows:
        if not isinstance(row, dict) or row.get("scope") != "curated_phrase_contract_regression":
            raise ValueError("unsupported evaluation scope")
        ident = row.get("id")
        lang = row.get("lang")
        q = row.get("q")
        expected = row.get("expected")
        if (not isinstance(ident, str) or ident in used or lang not in ("en", "es")
                or not isinstance(q, str) or not q.strip() or len(q) > 200
                or (expected is not None and expected not in aliases())):
            raise ValueError("invalid or repeated probe")
        used.add(ident)
        response = route_topic(q)
        observed = response.get("category")
        good = observed == expected and response.get("found") == (expected is not None)
        counts["total"] += 1
        counts["correct"] += int(good)
        counts["abstention_probes"] += int(expected is None)
        counts["correct_abstentions"] += int(expected is None and good)
        langs[lang + "_total"] += 1
        langs[lang + "_correct"] += int(good)
        if not good:
            mistakes.append({"id": ident, "expected": expected, "received": observed,
                             "status": response.get("status", "routed")})
    return {
        "v": 1, "scope": "in_distribution_alias_regression_not_semantic_accuracy",
        "total": counts["total"], "correct": counts["correct"],
        "abstention_cases": counts["abstention_probes"],
        "correct_abstentions": counts["correct_abstentions"],
        "languages": dict(sorted(langs.items())), "mistakes": mistakes,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate bilingual category phrase contract")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    report = evaluate()
    out = ROOT / "ai" / "topic-route-eval.json"
    encoded = json.dumps(report, separators=(",", ":"), ensure_ascii=False) + "\n"
    if args.write:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(encoded, encoding="utf-8")
    elif not out.is_file() or out.read_text(encoding="utf-8") != encoded:
        print("ERROR: stale bilingual regression report", file=sys.stderr)
        return 1
    print(json.dumps({"total": report["total"], "correct": report["correct"],
                      "scope": report["scope"]}, separators=(",", ":")))
    return 0 if not report["mistakes"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
