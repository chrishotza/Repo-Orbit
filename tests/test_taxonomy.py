"""Subject taxonomy: explicitly uncertain, token-frugal, reproducible."""
from __future__ import annotations

import json
import unittest

from repoorbit import agent, mcp, build_taxonomy_index, taxonomy


class TaxonomyTests(unittest.TestCase):
    def test_registry_is_bilingual_and_editorial_seeds_are_bounded(self):
        rules = taxonomy.registry()
        self.assertEqual(len(rules["categories"]), 14)
        self.assertEqual(len(rules["seed_subjects"]), 34))
        self.assertTrue(all(c["en"] and c["es"] for c in rules["categories"]))

    def test_every_known_repository_is_counted_exactly_once(self):
        overview = taxonomy.categories()
        self.assertEqual(overview["total"], agent.stats()["unique"])
        self.assertEqual(sum(x["n"] for x in overview["categories"]), 1462)
        keys = [row["r"].casefold() for rows in taxonomy.index().values()
                for row, _ in rows]
        self.assertEqual(len(keys), len(set(keys)))

    def test_curated_subject_is_not_a_functional_test(self):
        item = taxonomy.classify("Comfy-Org/ComfyUI")
        self.assertTrue(item["found"])
        self.assertEqual(item["category"], "creative-media")
        self.assertEqual(item["basis"], "editorial_seed_subject")
        self.assertEqual(item["v"], "exists")
        self.assertIn("not_functional_or_cost_verification", item["notice"])

    def test_catalogs_preserve_document_type(self):
        record = taxonomy.classify("vinta/awesome-python")
        self.assertEqual(record["category"], "developer-tools")
        self.assertEqual(record["role"], "catalog")
        self.assertEqual(record["format_hint"], "known_catalog")

    def test_keyword_slug_hint_does_not_claim_capability(self):
        example = taxonomy.classify("micromata/awesome-css-learning")
        self.assertEqual(example["basis"], "ambiguous_slug_keywords")
        self.assertEqual(example["category"], "unclassified")
        self.assertGreaterEqual(len(example["matched"]), 2)

    def test_catalog_source_is_an_independent_grounded_facet(self):
        record = taxonomy.classify("axios/axios")
        self.assertEqual(record["category"], "developer-tools")
        self.assertEqual(record["basis"], "readme_topic_evidence")
        self.assertIn("github:sindresorhus/awesome-nodejs", record["source_catalogs"])
        result = taxonomy.browse("unclassified", limit=3,
                                 source="github:sindresorhus/awesome-nodejs")
        self.assertGreater(result["n"], 0)
        self.assertEqual(result["source"], "github:sindresorhus/awesome-nodejs")

    def test_source_filter_never_accepts_unapproved_feeds(self):
        with self.assertRaises(ValueError):
            taxonomy.browse("ai-ml", source="github:invented/unreviewed")
        with self.assertRaises(ValueError):
            taxonomy.browse("ai-ml", source=123)
    def test_no_topic_evidence_must_abstain(self):
        example = taxonomy.classify("0xnr/awesome-bigdata")
        self.assertTrue(example["found"])
        self.assertEqual(example["category"], "unclassified")
        self.assertEqual(example["basis"], "no_subject_evidence")

    def test_missing_repository_is_not_misclassified(self):
        self.assertFalse(taxonomy.classify("imaginary-team/not-indexed")["found"])

    def test_category_browse_is_bounded_and_stable(self):
        data = taxonomy.browse("developer-tools", limit=2)
        self.assertEqual(len(data["items"]), 2)
        self.assertGreaterEqual(data["n"], 2)
        later = taxonomy.browse("developer-tools", limit=2, offset=2)
        self.assertEqual(data["n"], later["n"])
        self.assertNotEqual(data["items"][0]["r"], later["items"][0]["r"])

    def test_category_verification_filter_is_real(self):
        result = taxonomy.browse("web-apps", limit=10, verified_only=True)
        self.assertTrue(all(x["v"] == "exists" for x in result["items"]))
        self.assertLessEqual(result["n"], taxonomy.browse("web-apps")["n"])

    def test_conservative_validation(self):
        with self.assertRaises(ValueError):
            taxonomy.browse("made-up")
        with self.assertRaises(ValueError):
            taxonomy.browse("ai-ml", limit=21)
        with self.assertRaises(ValueError):
            taxonomy.browse("ai-ml", verified_only="yes")
        with self.assertRaises(ValueError):
            taxonomy.classify("../escape")

    def test_static_shards_match_live_taxonomy_exactly(self):
        self.assertEqual(build_taxonomy_index.main([]), 0)
        docs = build_taxonomy_index.build()
        self.assertEqual(len(docs), 16)
        self.assertEqual(sum(len(x["r"]) for key, x in docs.items()
                             if key != "index.json"), 1462)
        self.assertEqual(docs["index.json"]["total"], 1462)

    def test_zero_claims_about_free_or_running(self):
        results = taxonomy.browse("ai-ml", limit=20)
        for row in results["items"]:
            self.assertNotIn("cost", row)
            self.assertNotIn("working", row)
        self.assertEqual(agent.stats()["cost_free_verified"], 0)
        self.assertEqual(agent.stats()["working_verified"], 0)

    def test_agent_and_mcp_expose_all_three_new_tools(self):
        self.assertEqual(agent.call("classify", {"repo": "ollama/ollama"})["category"], "ai-ml")
        self.assertIn("categories", agent.call("categories", {}))
        self.assertIn("items", agent.call("browse", {"category": "ai-ml", "limit": 2}))
        names = {x["name"] for x in mcp.TOOLS}
        self.assertTrue({"classify", "categories", "browse"}.issubset(names))
        result = mcp.dispatch({
            "jsonrpc": "2.0", "id": 21, "method": "tools/call",
            "params": {"name": "browse", "arguments": {
                "category": "ai-ml", "limit": 2}},
        })
        self.assertIs(result["result"]["isError"], False)
        payload = result["result"]["content"][0]["text"]
        self.assertLess(len(payload), 750)
        self.assertEqual(len(json.loads(payload)["items"]), 2)

    def test_no_category_regression_in_normal_search(self):
        result = agent.search("python", limit=2)
        self.assertEqual(len(result["items"]), 2)
        self.assertEqual(result["semantics"], "lexical_not_functionally_verified")


if __name__ == "__main__":
    unittest.main()
