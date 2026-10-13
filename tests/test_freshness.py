"""Historical observation age is not proof of current repository health."""
from __future__ import annotations
import json
import unittest

from repoorbit import agent, freshness, build_evidence_dates, mcp


class FreshnessTests(unittest.TestCase):
    def test_checked_seed_age_and_staleness_are_explicit(self):
        values = [
            ("2026-10-13", 0, "recent_observation"),
            ("2026-11-12", 30, "recent_observation"),
            ("2026-11-13", 31, "aging_observation"),
            ("2027-01-11", 90, "aging_observation"),
            ("2027-01-12", 91, "stale_observation"),
        ]
        for today, age, state in values:
            with self.subTest(today=today):
                result = freshness.inspect("id:589831718", today)
                self.assertEqual(result["identity_status"], state)
                self.assertEqual(result["age_days"], age)
                self.assertEqual(result["scope"], "historical_metadata_only")
                self.assertNotIn("current_stars", result)
                self.assertNotIn("works", result)

    def test_checked_reference_has_authentic_archived_flag_and_documentary_date(self):
        item = freshness.inspect("bestiejs/benchmark.js", "2026-10-13")
        self.assertEqual(item["github_id"], 1800451)
        self.assertTrue(item["archived_when_checked"])
        self.assertEqual(item["readme_subject_observed_on"], "2026-10-13")
        self.assertEqual(len(item["readme_subject_sha"]), 40)

    def test_unchecked_reference_does_not_get_fabricated_age(self):
        item = freshness.inspect("vsouza/awesome-ios", "2026-10-13")
        self.assertTrue(item["found"])
        self.assertEqual(item["identity_status"], "not_individually_checked")
        self.assertNotIn("age_days", item)
        self.assertNotIn("github_id", item)

    def test_unknown_repository_is_not_false_positive(self):
        self.assertEqual(freshness.inspect("imaginary/does-not-exist", "2026-10-13"),
                         {"found": False, "status": "not_in_approved_corpus"})

    def test_future_dated_observation_fails_closed(self):
        item = freshness.inspect("axios/axios", "2026-10-12")
        self.assertEqual(item["identity_status"], "future_dated_evidence_invalid")
        self.assertEqual(item["age_days"], -1)

    def test_manifest_exactly_rebuilds_54_and_23(self):
        data = freshness.snapshot()
        self.assertEqual(data["checked_numeric_ids"], 58)
        self.assertEqual(data["readme_subjects"], 23)
        self.assertEqual(data["identity_observations_by_date"], [["2026-10-13", 58]])
        self.assertEqual(data["documentary_subjects_by_date"], [["2026-10-13", 23]])
        self.assertIn("not_live_health", data["scope"])
        self.assertEqual(build_evidence_dates.main([]), 0)

    def test_mcp_returns_compact_age_and_refuses_extra_arguments(self):
        result = mcp.dispatch({
            "jsonrpc": "2.0", "id": 4, "method": "tools/call",
            "params": {"name": "evidence_age", "arguments": {"repo": "id:23088740"}},
        })
        self.assertIs(result["result"]["isError"], False)
        payload = result["result"]["content"][0]["text"]
        self.assertLess(len(payload), 800)
        record = json.loads(payload)
        self.assertEqual(record["github_id"], 23088740)
        self.assertIn(record["identity_status"],
                      ["recent_observation", "aging_observation", "stale_observation"])
        with self.assertRaises(ValueError):
            agent.call("evidence_age", {"repo": "axios/axios", "as_of": "2026-10-13"})

    def test_invalid_date_not_accepted(self):
        for stamp in ("2026-10-0", "next friday", "2026-13-01", 8):
            with self.subTest(stamp=stamp):
                with self.assertRaises(ValueError):
                    freshness.inspect("axios/axios", stamp)

if __name__ == "__main__":
    unittest.main()
