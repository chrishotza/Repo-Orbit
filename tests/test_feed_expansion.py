"""Four new audited CC0 directories enlarge *reference* coverage, not capabilities."""
from __future__ import annotations
from collections import Counter, defaultdict
import json
import unittest

from repoorbit import agent, build_identity_index, build_owner_index, build_status
from repoorbit import build_taxonomy_index, freshness, refresh, snapshots, taxonomy


class FourReviewedFeedTests(unittest.TestCase):
    SOURCES = {
        "sindresorhus/awesome-npm": (64, "497964a13119c80967ba63cc674f0b797606e7e3", 49596056),
        "sindresorhus/awesome-electron": (145, "a16961f2067a5950570ea8ca2b0ed48ce4029c65", 34453060),
        "sindresorhus/awesome-observables": (13, "b1ecef932b4a73f7f9c44a5d5dc0ab32a5847375", 57965762),
        "sindresorhus/awesome-tap": (42, "5d5ba058b8994af81288aa509be3fc0024add0e0", 48281676),
    }

    def test_four_additions_are_enabled_rights_reviewed_and_immutable(self):
        feeds = refresh.load_feeds()
        self.assertEqual(len(feeds), 6)
        by_name = {f["repository"]: f for f in feeds}
        for name, (count, sha, _) in self.SOURCES.items():
            with self.subTest(name=name):
                feed = by_name[name]
                self.assertTrue(feed["enabled"])
                self.assertEqual(feed["license"], "CC0-1.0")
                self.assertEqual(feed["reviewed_at"], "2026-10-13")
                rows = [json.loads(t) for t in (agent.ROOT / feed["baseline"])
                        .read_text(encoding="utf-8").splitlines()]
                self.assertEqual(len(rows), count)
                self.assertEqual({r["source_blob_sha"] for r in rows}, {sha})
                self.assertTrue(all(r["source_license"] == "CC0-1.0"
                                    and r["target_verification"] == "not_checked"
                                    and type(r["source_line"]) is int
                                    and r["source_line"] >= 1 for r in rows))
                self.assertEqual(len({r["target_id"] for r in rows}), len(rows))

    def test_checked_catalog_seed_ids_are_exact(self):
        ids = build_identity_index.build()["r"]
        self.assertEqual(len(ids), 34)
        by_slug = {entry[1].lower(): entry for entry in ids}
        for slug, (_, __, number) in self.SOURCES.items():
            with self.subTest(slug=slug):
                self.assertEqual(by_slug[slug], [number, slug, "c"])
                self.assertEqual(agent.resolve(slug)["github_id"], number)

    def test_cross_source_dedup_preserves_edges(self):
        status = build_status.build()
        self.assertEqual(status["discovery_edges"], 1463)
        self.assertEqual(status["unique_slugs"], 1462)
        self.assertEqual(status["shared_targets_across_feeds"], 19)
        self.assertEqual(status["numeric_seed_ids_checked"], 34)
        self.assertEqual(status["numeric_reference_ids_checked"], 24)
        self.assertEqual(status["licensed_refresh_feeds"], 6)
        self.assertEqual(status["unverified_only"], 1404)
        self.assertEqual(status["functional_tests_passed"], 0)
        self.assertEqual(status["free_execution_verified"], 0)

    def test_all_derived_indexes_match_and_do_not_inflate_evidence(self):
        self.assertEqual(build_status.main([]), 0)
        self.assertEqual(build_identity_index.main([]), 0)
        self.assertEqual(build_owner_index.main([]), 0)
        self.assertEqual(build_taxonomy_index.main([]), 0)
        self.assertEqual(taxonomy.categories()["total"], 1462)
        self.assertEqual(freshness.snapshot()["checked_numeric_ids"], 58)
        self.assertEqual(agent.stats()["working_verified"], 0)
        self.assertEqual(agent.stats()["cost_free_verified"], 0)

    def test_existence_flag_is_not_promoted_for_discovered_links(self):
        example = "agalwood/Motrix"
        rec = agent.resolve(example)
        self.assertTrue(rec["found"])
        self.assertEqual(rec["role"], "reference")
        self.assertEqual(rec["v"], "not_checked")
        self.assertIn("github:sindresorhus/awesome-electron",
                      {x["s"] for x in rec["source"]})
        self.assertNotIn("github_id", rec)

    def test_source_specific_browse_retains_exact_provenance(self):
        result = taxonomy.browse("mobile-desktop", limit=5,
                                  source="github:sindresorhus/awesome-electron")
        self.assertGreater(result["n"], 0)
        self.assertLessEqual(len(result["items"]), 5)
        self.assertTrue(all(x["v"] in ("exists", "not_checked") for x in result["items"]))

    def test_tracked_snapshot_paths_equal_feed_allowlist(self):
        paths = snapshots.approved_discoveries()
        self.assertEqual(len(paths), 6)
        self.assertEqual(len({p.resolve() for p in paths}), 6)


if __name__ == "__main__":
    unittest.main()
