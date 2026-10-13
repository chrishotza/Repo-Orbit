"""Independent reference-existence checks, offline AI contracts and fail-closed batches."""
from __future__ import annotations

import json
from pathlib import Path
import unittest

from repoorbit import agent, check_targets, verified, build_verified_index, mcp


class VerifiedReferencesTests(unittest.TestCase):
    def test_24_numeric_ids_are_unique_and_traceable(self):
        ids, aliases = verified.load()
        self.assertEqual(len(ids), 24)
        self.assertGreaterEqual(len(aliases), 24)
        self.assertTrue(all(row["discovered_via"] for row in ids.values()))
        self.assertTrue(all(row["verification"] == "repository_exists" for row in ids.values()))
        self.assertTrue(all(row["cost"] == "unknown" and row["function_test"] == "not_run" for row in ids.values()))

    def test_new_ids_dont_overlap_seeds(self):
        from repoorbit.identity import load
        seeds, _ = load()
        self.assertTrue(set(seeds).isdisjoint(verified.load()[0]))

    def test_archived_repo_remains_discoverable_with_flag(self):
        info = agent.resolve("bestiejs/benchmark.js")
        self.assertTrue(info["found"])
        self.assertEqual(info["role"], "reference")
        self.assertEqual(info["v"], "exists")
        self.assertEqual(info["github_id"], 1800451)
        self.assertTrue(info["archived"])
        self.assertEqual(info["warning"], "existence_only_function_cost_unverified")

    def test_case_variation_is_same_numeric_repo(self):
        self.assertEqual(verified.lookup("0PandaDEV/awesome-windows")["github_id"], 849611230)
        self.assertEqual(verified.lookup("0pandadev/awesome-windows")["github_id"], 849611230)

    def test_checked_slug_keeps_exact_catalog_discovery_provenance(self):
        info = agent.resolve("axios/axios")
        self.assertEqual(info["github_id"], 23088740)
        self.assertEqual(info["role"], "reference")
        self.assertTrue(info["source"])
        self.assertEqual(info["source"][0]["s"], "github:sindresorhus/awesome-nodejs")
        self.assertEqual(info["v"], "exists")

    def test_numeric_lookup_works_through_existing_mcp_tool(self):
        output = mcp.dispatch({
            "jsonrpc": "2.0", "id": 2, "method": "tools/call",
            "params": {"name": "resolve", "arguments": {"repo": "id:23088740"}},
        })
        self.assertFalse(output["result"]["isError"])
        data = json.loads(output["result"]["content"][0]["text"])
        self.assertEqual(data["r"], "axios/axios")
        self.assertEqual(data["github_id"], 23088740)

    def test_incomplete_reference_remains_unverified(self):
        result = agent.resolve("vsouza/awesome-ios")
        self.assertTrue(result["found"])
        self.assertEqual(result["v"], "not_checked")
        self.assertNotIn("github_id", result)

    def test_free_or_functional_claims_still_zero(self):
        stats = agent.stats()
        self.assertEqual(stats["checked_reference_ids"], 24)
        self.assertEqual(stats["working_verified"], 0)
        self.assertEqual(stats["cost_free_verified"], 0)
        self.assertEqual(stats["unique"], 1215)
        self.assertEqual(stats["unverified_only"], 1161)

    def test_remote_index_is_exactly_reproducible(self):
        self.assertEqual(build_verified_index.main([]), 0)
        doc = build_verified_index.build()
        self.assertEqual(doc["n"], 24)
        self.assertEqual(sum(row[3] for row in doc["r"]), 1)


class TargetBatchTests(unittest.TestCase):
    def test_pending_excludes_all_54_checked_ids(self):
        q = check_targets.pending()
        self.assertEqual(len(q), 1161)
        self.assertEqual(q, sorted(set(q)))
        self.assertNotIn("axios/axios", q)
        self.assertNotIn("comfy-org/comfyui", q)

    def test_offline_check_does_not_use_api(self):
        self.assertEqual(check_targets.main(["--check", "--limit", "5"]), 0)

    def test_valid_two_item_batch_preserves_unknown_cost(self):
        queue = check_targets.pending()[:2]
        results = [
            {"github_id": 999001, "canonical_slug": queue[0],
             "archived": False, "default_branch": "main"},
            {"github_id": 999002, "canonical_slug": queue[1],
             "archived": True, "default_branch": "master"},
        ]
        consumed = iter(results)
        report = check_targets.examine(queue, lambda _: next(consumed), "2026-10-13")
        self.assertEqual(report["checked"], 2)
        self.assertEqual(report["unresolved"], 0)
        self.assertEqual(report["verified"][1]["cost"], "unknown")
        self.assertTrue(report["verified"][1]["archived"])

    def test_404_is_unresolved_not_confirmed_deleted(self):
        q = check_targets.pending()[:2]
        result = check_targets.examine(q, lambda _: None, "2026-10-13")
        self.assertEqual(result["unresolved"], 2)
        self.assertEqual(result["checked"], 0)
        self.assertTrue(all("not_confirmed_deleted" in item["reason"]
                            for item in result["unresolved_items"]))

    def test_two_slugs_same_id_require_alias_review(self):
        q = check_targets.pending()[:2]
        def fake(slug):
            return {"github_id": 111001, "canonical_slug": slug, "archived": False,
                    "default_branch": "main"}
        with self.assertRaisesRegex(check_targets.TargetCheckError, "two requested paths"):
            check_targets.examine(q, fake, "2026-10-13")

    def test_slug_reuse_collision_blocks(self):
        q = check_targets.pending()[:1]
        def fake(_):
            return {"github_id": 111001, "canonical_slug": "axios/axios",
                    "archived": False, "default_branch": "main"}
        with self.assertRaisesRegex(check_targets.TargetCheckError, "slug-to-ID collision"):
            check_targets.examine(q, fake, "2026-10-13")

    def test_an_existing_numeric_id_is_never_reused(self):
        q = check_targets.pending()[:1]
        def fake(slug):
            return {"github_id": 23088740, "canonical_slug": slug,
                    "archived": False, "default_branch": "main"}
        with self.assertRaisesRegex(check_targets.TargetCheckError, "already checked reference ID"):
            check_targets.examine(q, fake, "2026-10-13")

    def test_requested_unapproved_or_previously_checked_paths_fail_closed(self):
        with self.assertRaises(check_targets.TargetCheckError):
            check_targets.examine(["not-here/fake"], lambda _: None, "2026-10-13")
        with self.assertRaises(check_targets.TargetCheckError):
            check_targets.examine(["axios/axios"], lambda _: None, "2026-10-13")

    def test_batch_size_is_explicitly_bounded(self):
        with self.assertRaises(check_targets.TargetCheckError):
            check_targets.examine([], lambda _: None, "2026-10-13")
        with self.assertRaises(check_targets.TargetCheckError):
            check_targets.examine(check_targets.pending()[:26], lambda _: None, "2026-10-13")
        self.assertEqual(check_targets.MAX_BATCH, 25)

    def test_api_input_slug_doesnt_permit_arbitrary_hosts(self):
        for invalid in ("https://evil.example.com/a/b", "../secret",
                        "owner/repo/extra", "owner name/project"):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    from repoorbit.identity import canonical_slug
                    canonical_slug(invalid)


if __name__ == "__main__":
    unittest.main()
