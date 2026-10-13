"""AI owner routing: small static pages, exact coverage and bounded MCP."""
from __future__ import annotations
import json
import unittest

from repoorbit import agent, build_owner_index, mcp
from repoorbit.owner_lookup import owner_repos


class OwnerRouterTests(unittest.TestCase):
    def test_approved_corpus_is_covered_once(self):
        docs = build_owner_index.build()
        self.assertEqual(build_owner_index.main([]), 0)
        self.assertEqual(sum(group[1] for group in docs["index.json"]["groups"]), 1215)
        self.assertEqual(len(docs["index.json"]["groups"]), 29)
        paths = [row[0].casefold() for key, obj in docs.items()
                 if key != "index.json" and not key.endswith("/index.json")
                 for row in obj["r"]]
        self.assertEqual(len(paths), 1215)
        self.assertEqual(len(set(paths)), 1215)
        checked = sum(row[2] for key, obj in docs.items()
                      if key != "index.json" and not key.endswith("/index.json")
                      for row in obj["r"])
        self.assertEqual(checked, 54)

    def test_page_size_and_byte_bound_applies_to_every_page(self):
        docs = build_owner_index.build()
        for key, payload in docs.items():
            if key.endswith("index.json"):
                continue
            with self.subTest(key=key):
                self.assertLessEqual(len(payload["r"]), 64)
                self.assertLessEqual(len(build_owner_index.encode(payload).encode("utf-8")),
                                     build_owner_index.MAX_BYTES)

    def test_owner_route_needs_only_first_character_and_small_page(self):
        results = owner_repos("sindresorhus", limit=2)
        self.assertGreaterEqual(results["n"], 2)
        self.assertEqual(len(results["items"]), 2)
        self.assertLess(len(json.dumps(results)), 650)
        self.assertTrue(all(x["r"].lower().startswith("sindresorhus/") for x in results["items"]))
        self.assertEqual(build_owner_index.bucket("sindresorhus"), "s")

    def test_missing_owner_returns_empty_not_invented(self):
        answer = owner_repos("owner-does-not-exist-12345")
        self.assertEqual(answer["n"], 0)
        self.assertEqual(answer["items"], [])

    def test_verified_filter_uses_github_existence_only(self):
        answer = owner_repos("axios", verified_only=True)
        self.assertGreaterEqual(answer["n"], 1)
        self.assertTrue(all(x["v"] == "exists" for x in answer["items"]))
        self.assertNotIn("functional", answer)
        self.assertNotIn("free", answer)

    def test_mcp_respects_paging_and_input_validation(self):
        reply = mcp.dispatch({"jsonrpc": "2.0", "id": 5, "method": "tools/call",
                              "params": {"name": "owner_repos", "arguments": {
                                  "owner": "sindresorhus", "limit": 1}}})
        self.assertIs(reply["result"]["isError"], False)
        payload = json.loads(reply["result"]["content"][0]["text"])
        self.assertEqual(len(payload["items"]), 1)
        self.assertLess(len(reply["result"]["content"][0]["text"]), 450)
        for owner in ("../evil", "evil/other", "https://evil.com", ""):
            with self.subTest(owner=owner), self.assertRaises(ValueError):
                owner_repos(owner)

    def test_synthetic_40000_references_stay_in_small_pages(self):
        fake = [{"r": f"test-owner/repo-{i:06d}", "role": "reference",
                 "v": "not_checked"} for i in range(40000)]
        docs = build_owner_index.build(fake)
        group = docs["index.json"]["groups"]
        self.assertEqual(group, [["t", 40000, 625]])
        pages = [v for k,v in docs.items() if k.endswith(".json")
                 and not k.endswith("index.json")]
        self.assertEqual(sum(len(v["r"]) for v in pages), 40000)
        self.assertTrue(all(len(v["r"]) <= 64 for v in pages))
        self.assertTrue(all(len(build_owner_index.encode(v).encode("utf-8")) <= 16384 for v in pages))
        self.assertLess(len(build_owner_index.encode(docs["index.json"]).encode("utf-8")), 1000)

    def test_duplicate_canonical_paths_fail(self):
        fake = [
            {"r":"Foo/Bar", "role":"reference", "v":"not_checked"},
            {"r":"foo/bar", "role":"reference", "v":"not_checked"},
        ]
        with self.assertRaisesRegex(ValueError, "duplicate"):
            build_owner_index.build(fake)


if __name__ == "__main__":
    unittest.main()
