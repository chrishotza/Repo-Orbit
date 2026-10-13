"""Agent-facing JSON, MCP stdio contract and pinned index regression tests."""
import json
import unittest

from repoorbit import agent, build_index, build_status, mcp


class AgentTests(unittest.TestCase):
    def test_status_json_matches_loaded_two_source_corpus(self):
        self.assertEqual(build_status.main([]), 0)
        status = build_status.build()
        self.assertEqual(status["unique_slugs"], agent.stats()["unique"])
        self.assertEqual(status["unverified_only"], agent.stats()["unverified_only"])
        self.assertEqual(status["discovery_edges"], sum(status["source_edges"].values()))
        self.assertGreaterEqual(status["discovery_edges"], 1000)
        self.assertLessEqual(status["shared_targets_across_feeds"], status["discovery_edges"])
        self.assertEqual(status["functional_tests_passed"], 0)

    def test_inventory_is_explicit_not_github_coverage(self):
        stats = agent.stats()
        self.assertEqual(stats["catalogs"], 22)
        self.assertEqual(stats["verified_project_seeds"], 8)
        self.assertGreaterEqual(stats["unverified_only"], 600)
        self.assertEqual(stats["working_verified"], 0)
        self.assertEqual(stats["cost_free_verified"], 0)

    def test_resolve_verified_seed(self):
        result = agent.resolve("https://github.com/Comfy-Org/ComfyUI")
        self.assertTrue(result["found"])
        self.assertEqual(result["v"], "exists")
        self.assertEqual(result["cost"], "unknown")
        self.assertEqual(result["working"], "not_run")

    def test_resolve_catalog_source(self):
        result = agent.resolve("sindresorhus/awesome")
        self.assertEqual(result["role"], "catalog")
        self.assertEqual(result["v"], "exists")

    def test_unverified_reference_provenance(self):
        result = agent.resolve("vsouza/awesome-ios")
        self.assertTrue(result["found"])
        self.assertEqual(result["v"], "not_checked")
        self.assertTrue(result["source"])
        self.assertEqual(result["source"][0]["s"], "github:sindresorhus/awesome")
        self.assertGreater(result["source"][0]["line"], 0)
        self.assertEqual(len(result["source"][0]["sha"]), 40)

    def test_search_is_bounded_and_not_semantic(self):
        result = agent.search("mcp", limit=3)
        self.assertLessEqual(len(result["items"]), 3)
        self.assertGreater(result["n"], 0)
        self.assertTrue(all(set(item).issubset({"r", "role", "v", "tags"})
                            for item in result["items"]))
        self.assertEqual(result["semantics"], "lexical_not_functionally_verified")

    def test_search_pagination_is_stable(self):
        page = agent.search("python", limit=3)
        next_page = agent.search("python", limit=3, offset=3)
        if next_page["items"]:
            self.assertNotEqual(page["items"][0]["r"], next_page["items"][0]["r"])
        self.assertEqual(page["n"], next_page["n"])

    def test_search_cannot_grow_unbounded(self):
        with self.assertRaises(ValueError):
            agent.search("a", limit=100000)
        with self.assertRaises(ValueError):
            agent.search("a" * 201)
        with self.assertRaises(ValueError):
            agent.resolve("not-a-repository")

    def test_tool_call_rejects_extra_fields(self):
        with self.assertRaises(ValueError):
            agent.call("stats", {"secret": "no"})
        with self.assertRaises(ValueError):
            agent.call("search", {"q": "mcp", "hidden": True})

    def test_mcp_initialize_and_list(self):
        initialize = mcp.dispatch({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
        self.assertEqual(initialize["result"]["serverInfo"]["name"], "repoorbit")
        tools = mcp.dispatch({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})["result"]["tools"]
        self.assertEqual({x["name"] for x in tools}, {"search", "resolve", "recommend", "stats", "categories", "classify", "browse"})

    def test_mcp_call_returns_compact_json(self):
        result = mcp.dispatch({"jsonrpc": "2.0", "id": 5, "method": "tools/call",
                               "params": {"name": "search", "arguments": {"q": "mcp", "limit": 2}}})
        self.assertFalse(result["result"]["isError"])
        payload = result["result"]["content"][0]["text"]
        self.assertLess(len(payload), 1000)
        self.assertLessEqual(len(json.loads(payload)["items"]), 2)

    def test_mcp_validation_errors_do_not_crash(self):
        result = mcp.dispatch({"jsonrpc": "2.0", "id": 5, "method": "tools/call",
                               "params": {"name": "search", "arguments": {"limit": 2}}})
        self.assertTrue(result["result"]["isError"])
        self.assertIsNone(mcp.dispatch({"jsonrpc": "2.0", "method": "notifications/initialized"}))

    def test_static_shards_equal_generator_output(self):
        self.assertEqual(build_index.main([]), 0)

    def test_static_term_index_resolves_existing_pointer(self):
        import pathlib
        p = pathlib.Path(agent.ROOT) / "ai" / "terms" / "m.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
        self.assertEqual(doc["v"], 1)
        self.assertIn("mcp", doc["t"])
        self.assertTrue(all(0 <= i < len(doc["r"]) for i in doc["t"]["mcp"]))
        self.assertTrue(any("mcp" in doc["r"][i][0].lower() for i in doc["t"]["mcp"]))


if __name__ == "__main__":
    unittest.main()
