"""Proof that promotion is review-gated, identity-stable and immutable."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from repoorbit import promote, refresh


def prepare_fixture(root: Path, *, mutate: str = "none") -> Path:
    feeds = refresh.load_feeds()
    staged = root / "staged"
    staged.mkdir()
    report = {"schema_version": "0.1.0", "status": "staged_unreviewed_no_auto_commit", "results": []}
    for i, feed in enumerate(feeds):
        rows = [json.loads(x) for x in (refresh.ROOT / feed["baseline"]).read_text().splitlines()]
        old = {x["target_id"] for x in rows}
        if i == 0 and mutate == "added":
            extra = dict(rows[0])
            extra["target_id"] = "github:repoorbit-fixture/unseen-project"
            extra["target_full_name"] = "repoorbit-fixture/unseen-project"
            extra["target_url"] = "https://github.com/repoorbit-fixture/unseen-project"
            rows.append(extra)
            rows.sort(key=lambda e: e["target_id"])
        if i == 0 and mutate == "removed":
            rows = rows[:20]
        path = feed["repository"].replace("/", "-").casefold() + ".jsonl"
        (staged / path).write_text("".join(json.dumps(e) + "\n" for e in rows))
        ids = {e["target_id"] for e in rows}
        report["results"].append({
            "source_id": feed["id"],
            "source_license": "CC0-1.0",
            "source_blob_sha": rows[0]["source_blob_sha"],
            "baseline": feed["baseline"],
            "staged_snapshot": "data/snapshots/staged/" + path,
            "baseline_count": len(old),
            "current_count": len(ids),
            "added": len(ids - old),
            "removed": len(old - ids),
            "unchanged": len(ids & old),
        })
    (staged / "report.json").write_text(json.dumps(report))
    return staged


class PromotionTests(unittest.TestCase):
    def test_no_differences_creates_no_changes(self):
        with tempfile.TemporaryDirectory() as folder:
            stage = prepare_fixture(Path(folder))
            self.assertEqual(promote.plan_promotions(refresh.load_feeds(), stage), [])

    def test_one_new_reference_is_plan_only(self):
        with tempfile.TemporaryDirectory() as folder:
            stage = prepare_fixture(Path(folder), mutate="added")
            changes = promote.plan_promotions(refresh.load_feeds(), stage)
            self.assertEqual(len(changes), 1)
            self.assertEqual(changes[0]["added"], 1)
            self.assertEqual(changes[0]["removed"], 0)
            self.assertIn("sindresorhus-awesome-", changes[0]["path"])
            self.assertNotIn("/staged/", changes[0]["path"])

    def test_rejects_bulk_removal(self):
        with tempfile.TemporaryDirectory() as folder:
            stage = prepare_fixture(Path(folder), mutate="removed")
            with self.assertRaisesRegex(promote.PromotionError, "excessive discovery churn"):
                promote.plan_promotions(refresh.load_feeds(), stage)

    def test_report_count_forgery_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            stage = prepare_fixture(Path(folder))
            doc = json.loads((stage / "report.json").read_text())
            doc["results"][0]["added"] = 999
            (stage / "report.json").write_text(json.dumps(doc))
            with self.assertRaisesRegex(promote.PromotionError, "report counts disagree"):
                promote.plan_promotions(refresh.load_feeds(), stage)

    def test_rejects_unexpected_snapshot_location(self):
        with tempfile.TemporaryDirectory() as folder:
            stage = prepare_fixture(Path(folder))
            doc = json.loads((stage / "report.json").read_text())
            doc["results"][0]["staged_snapshot"] = "../../secrets.env"
            (stage / "report.json").write_text(json.dumps(doc))
            with self.assertRaisesRegex(promote.PromotionError, "untrusted snapshot location"):
                promote.plan_promotions(refresh.load_feeds(), stage)

    def test_rejects_false_working_verification(self):
        with tempfile.TemporaryDirectory() as folder:
            stage = prepare_fixture(Path(folder))
            path = stage / "sindresorhus-awesome.jsonl"
            entries = [json.loads(x) for x in path.read_text().splitlines()]
            entries[0]["target_verification"] = "tested_working"
            path.write_text("".join(json.dumps(e) + "\n" for e in entries))
            with self.assertRaisesRegex(promote.PromotionError, "staged source provenance mismatch"):
                promote.plan_promotions(refresh.load_feeds(), stage)

    def test_rejects_repeat_rows(self):
        with tempfile.TemporaryDirectory() as folder:
            stage = prepare_fixture(Path(folder))
            path = stage / "sindresorhus-awesome.jsonl"
            path.write_text(path.read_text() + path.read_text().splitlines()[0] + "\n")
            with self.assertRaisesRegex(promote.PromotionError, "duplicate staged repository identity"):
                promote.plan_promotions(refresh.load_feeds(), stage)

    def test_approved_snapshots_are_exactly_the_pinned_baselines(self):
        from repoorbit.snapshots import approved_discoveries
        listed = {str(p.relative_to(refresh.ROOT)) for p in approved_discoveries()}
        selected = {f["baseline"] for f in refresh.load_feeds()}
        self.assertEqual(listed, selected)


if __name__ == "__main__":
    unittest.main()
