"""Progressive page selection invariants including 250,000 fake corpus links.

Pure synthetic tests; they are NOT 250,000 actual discovered/verified repos.
"""
from __future__ import annotations
from datetime import date, timedelta
import unittest

from repoorbit import coverage_plan, check_targets, stage_readmes


class CalendarCoverageTests(unittest.TestCase):
    def test_first_two_days_visit_disjoint_pending_pages(self):
        q = check_targets.pending()
        self.assertEqual(len(q), 1161)
        a = coverage_plan.plan(q, 25, "2026-10-13")
        b = coverage_plan.plan(q, 25, "2026-10-14")
        self.assertEqual((a["page_index"], b["page_index"]), (0, 1))
        self.assertEqual((a["pages"], a["queue_total"]), (47, 1161))
        self.assertEqual(len(a["items"]), 25)
        self.assertEqual(len(b["items"]), 25)
        self.assertTrue(set(a["items"]).isdisjoint(b["items"]))

    def test_full_stable_cycle_covers_each_pending_once(self):
        q = check_targets.pending()
        selected = []
        for i in range(47):
            day = (coverage_plan.BASE_DATE + timedelta(days=i)).isoformat()
            selected.extend(coverage_plan.plan(q, 25, day)["items"])
        self.assertEqual(len(selected), 1161)
        self.assertEqual(set(selected), set(q))
        self.assertEqual(len(set(selected)), len(selected))

    def test_second_cycle_wraps_without_inventing_targets(self):
        q = check_targets.pending()
        start = coverage_plan.plan(q, 25, "2026-10-13")
        wrapped = coverage_plan.plan(q, 25, (coverage_plan.BASE_DATE + timedelta(days=47)).isoformat())
        self.assertEqual(start["items"], wrapped["items"])
        self.assertEqual(wrapped["page_index"], 0)

    def test_stage_readmes_uses_five_distinct_calendar_pages(self):
        q = stage_readmes.pending_review()
        a = coverage_plan.plan(q, 5, "2026-10-13")
        b = coverage_plan.plan(q, 5, "2026-10-14")
        self.assertEqual(a["pages"], 233)
        self.assertEqual(b["page_index"], 1)
        self.assertTrue(set(a["items"]).isdisjoint(b["items"]))

    def test_synthetic_250k_queue_has_bounded_small_pages(self):
        q = [f"synthetic-owner/repo-{i:06d}" for i in range(250000)]
        first = coverage_plan.plan(q, 25, "2026-10-13")
        distant = coverage_plan.plan(q, 25, "2026-11-12")
        self.assertEqual(first["queue_total"], 250000)
        self.assertEqual(first["pages"], 10000)
        self.assertEqual(len(first["items"]), 25)
        self.assertEqual(len(distant["items"]), 25)
        self.assertTrue(set(first["items"]).isdisjoint(distant["items"]))
        self.assertNotIn("working_verified", first)

    def test_invalid_pages_fail_closed(self):
        for values, limit, stamp in [
            (["x", "x"], 1, None), (["z", "a"], 1, None),
            (["a"], 0, None), (["a"], 26, None), (["a"], True, None),
            (["a"], 1, "2026-10-12"), (["a"], 1, "tomorrow"),
            (["a"], 1, 1234), ([None], 1, None),
        ]:
            with self.subTest(values=values, limit=limit, stamp=stamp):
                with self.assertRaises(ValueError):
                    coverage_plan.plan(values, limit, stamp)

    def test_empty_queue_is_honest(self):
        result = coverage_plan.plan([], 5, "2026-10-13")
        self.assertEqual(result["pages"], 0)
        self.assertEqual(result["items"], [])
        self.assertIsNone(result["next_page_index"])

    def test_offline_cli_plans_rotating_pages(self):
        self.assertEqual(check_targets.main(
            ["--check", "--limit", "25", "--cycle-date", "2026-10-14"]), 0)
        self.assertEqual(stage_readmes.main(
            ["--check", "--limit", "5", "--cycle-date", "2026-10-14"]), 0)

    def test_manual_cursor_remains_available_but_cannot_mix_with_calendar(self):
        self.assertEqual(check_targets.main(
            ["--check", "--after", "0xnr/awesome-bigdata", "--limit", "2"]), 0)
        self.assertEqual(stage_readmes.main(
            ["--check", "--after", "0xnr/awesome-bigdata", "--limit", "2"]), 0)

if __name__ == "__main__":
    unittest.main()
