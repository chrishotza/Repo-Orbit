"""Global incremental catalog deltas must deduplicate without inventing identities."""
from __future__ import annotations
import unittest

from repoorbit import incremental_delta, refresh


class GlobalDeltaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.feeds = refresh.load_feeds()
        cls.a, cls.b = cls.feeds[:2]

    def edge(self, feed, slug, sha="a"*40, line=8):
        return {
            "source_id": feed["id"], "source_path": "readme.md",
            "source_line": line, "source_blob_sha": sha, "source_license": "CC0-1.0",
            "target_full_name": slug, "target_id": "github:" + slug.casefold(),
            "target_url": "https://github.com/" + slug,
            "target_verification": "not_checked",
            "extraction_method": "github_link_regex_v0.1",
        }

    def plans(self, data):
        return [(feed, rows, {"source_id": feed["id"]})
                for feed, rows in zip(self.feeds, data + [[] for _ in range(len(self.feeds) - len(data))])]

    def baseline(self, data):
        return [(feed["id"], rows) for feed, rows in zip(self.feeds, data)]

    def test_one_target_linked_twice_counts_once_globally(self):
        a,b = self.feeds
        old = self.baseline([
            [self.edge(a, "hello/shared"), self.edge(a, "hello/removed")],
            [self.edge(b, "hello/shared")],
        ])
        new = self.plans([
            [self.edge(a, "hello/shared"), self.edge(a, "hello/new")],
            [self.edge(b, "Hello/New")],
        ])
        report = incremental_delta.compare(new, old)
        self.assertEqual(report["baseline_unique_paths"], 2)
        self.assertEqual(report["proposed_unique_paths"], 2)
        self.assertEqual(report["baseline_edges"], 3)
        self.assertEqual(report["proposed_edges"], 3)
        kinds = report["counts"]
        self.assertEqual(kinds["new_unverified_paths"], 1)
        self.assertEqual(kinds["removed_from_sources_not_deleted"], 1)
        self.assertEqual(kinds["source_membership_changes"], 1)
        self.assertEqual(len(report["changes"]), 3)
        added = next(x for x in report["changes"] if x["change"] == "new_unverified_paths")
        self.assertEqual(set(added["proposed_sources"]), {a["id"], b["id"]})
        self.assertEqual(len(added["new_evidence"]), 2)
        self.assertEqual(added["identity"], "not_individually_checked")
        removed = next(x for x in report["changes"]
                       if x["change"] == "removed_from_sources_not_deleted")
        self.assertEqual(removed["proposed_sources"], [])
        self.assertIn("not_deleted", removed["change"])

    def test_same_slug_two_sources_is_not_two_new_repos(self):
        a,b = self.feeds
        empty = self.baseline([[], []])
        report = incremental_delta.compare(self.plans([
            [self.edge(a, "One/Repo")], [self.edge(b, "one/repo")]
        ]), empty)
        self.assertEqual(report["counts"]["new_unverified_paths"], 1)
        self.assertEqual(report["proposed_edges"], 2)
        self.assertEqual(report["proposed_unique_paths"], 1)

    def test_known_seed_link_does_not_count_as_new_unknown(self):
        a,b = self.feeds
        report = incremental_delta.compare(self.plans([
            [self.edge(a, "Comfy-Org/ComfyUI")], []
        ]), self.baseline([[], []]))
        self.assertEqual(report["counts"]["new_links_to_known_paths"], 1)
        self.assertEqual(report["counts"]["new_unverified_paths"], 0)

    def test_bad_license_or_false_verification_fails(self):
        a,b = self.feeds
        for field,value in [("source_license","MIT"),
                            ("target_verification","fully_working"),
                            ("source_line",True)]:
            item = self.edge(a,"new/repo")
            item[field] = value
            with self.subTest(field=field):
                with self.assertRaises(incremental_delta.DeltaError):
                    incremental_delta.compare(self.plans([[item],[]]),
                                              self.baseline([[],[]]))

    def test_duplicate_slug_in_one_feed_blocks_even_with_case_variation(self):
        a,b = self.feeds
        with self.assertRaisesRegex(incremental_delta.DeltaError, "duplicate"):
            incremental_delta.compare(self.plans([[
                self.edge(a,"hello/world"),self.edge(a,"Hello/World")
            ],[]]),self.baseline([[],[]]))

    def test_missing_feed_or_unregistered_source_blocks(self):
        a,b=self.feeds
        with self.assertRaises(incremental_delta.DeltaError):
            incremental_delta.compare([(a,[],{"source_id":a["id"]})],
                                      self.baseline([[],[]]))
        with self.assertRaises(incremental_delta.DeltaError):
            incremental_delta.compare(self.plans([[],[]]),
                                      [(a["id"],[]),("github:evil/fake",[])])

    def test_actual_baseline_vs_itself_reports_zero_differences(self):
        streams=incremental_delta._approved()
        report=incremental_delta.compare(
            self.plans([rows for _,rows in streams]), streams)
        self.assertEqual(report["proposed_edges"], 1463)
        self.assertEqual(report["counts"]["new_unverified_paths"], 0)
        self.assertEqual(len(report["changes"]), 0)
        self.assertEqual(report["baseline_unique_paths"],
                         report["proposed_unique_paths"])
        self.assertEqual(report["counts"]["unchanged_paths"],
                         report["baseline_unique_paths"])


if __name__=="__main__":
    unittest.main()
