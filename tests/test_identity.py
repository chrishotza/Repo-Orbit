"""Stable-ID lookup and adversarial rename/transfer guards (no network)."""
from __future__ import annotations

import json
import unittest

from repoorbit import agent, build_identity_index, identity, mcp


class StableIdentityTests(unittest.TestCase):
    def test_verified_ids_cover_all_individually_checked_seeds(self):
        ids, aliases = identity.load()
        self.assertEqual(len(ids), 34)
        self.assertEqual(len(aliases), 34)
        self.assertEqual(sum(row["role"] == "catalog" for row in ids.values()), 26)
        self.assertEqual(sum(row["role"] == "project" for row in ids.values()), 8)
        self.assertEqual(len({row["github_id"] for row in ids.values()}), 34)

    def test_all_registered_names_are_real_seed_references(self):
        sources = json.loads((agent.ROOT / "data/sources.json").read_text())["sources"]
        repos = [json.loads(line) for line in
                 (agent.ROOT / "data/repositories.jsonl").read_text().splitlines()]
        expected = {x["repository"].casefold() for x in sources} | {
            x["full_name"].casefold() for x in repos
        }
        _, aliases = identity.load()
        self.assertEqual(set(aliases), expected)

    def test_numeric_and_slug_lookup_agree(self):
        slug = identity.lookup("Comfy-Org/ComfyUI")
        ident = identity.lookup("id:589831718")
        self.assertEqual(slug, ident)
        self.assertEqual(ident, identity.lookup(589831718))
        self.assertEqual(ident["observed_on"], "2026-10-13")

    def test_agent_resolves_verified_numeric_id(self):
        result = agent.resolve("id:589831718")
        self.assertTrue(result["found"])
        self.assertEqual(result["r"], "Comfy-Org/ComfyUI")
        self.assertEqual(result["github_id"], 589831718)
        self.assertEqual(result["cost"], "unknown")
        self.assertEqual(result["working"], "not_run")
        self.assertEqual(result["v"], "exists")

    def test_unverified_links_do_not_gain_fake_numeric_ids(self):
        result = agent.resolve("vsouza/awesome-ios")
        self.assertTrue(result["found"])
        self.assertNotIn("github_id", result)
        self.assertEqual(result["v"], "not_checked")

    def test_unknown_id_fails_closed(self):
        result = agent.resolve("id:99999999999999")
        self.assertFalse(result["found"])
        self.assertEqual(result["note"], "numeric_id_not_in_verified_registry")
        self.assertFalse(identity.lookup("id:99999999999999")["found"])

    def test_invalid_id_and_url_rejected(self):
        for invalid in ("id:-1", "id:0", "id:xyz", "https://evil.com/a/b",
                        "owner/repo/branch", "id:1/2"):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    identity.lookup(invalid)

    def test_id_remains_same_when_name_changes(self):
        info = identity.reconcile([{
            "github_id": 589831718,
            "canonical_slug": "Comfy-Org/ComfyUI-renamed",
        }])
        self.assertEqual(info["renamed"], 1)
        self.assertEqual(info["transferred"], 0)
        self.assertEqual(info["items"][0]["github_id"], 589831718)
        self.assertEqual(info["not_checked_this_run"], 33)

    def test_transfer_requires_same_numeric_identity(self):
        info = identity.reconcile([{
            "github_id": 589831718, "canonical_slug": "Other-Owner/ComfyUI",
        }])
        self.assertEqual(info["transferred"], 1)
        self.assertEqual(info["new_unreviewed"], 0)

    def test_reused_slug_with_different_id_is_blocked(self):
        with self.assertRaisesRegex(ValueError, "slug reused"):
            identity.reconcile([{
                "github_id": 999999999, "canonical_slug": "Comfy-Org/ComfyUI",
            }])

    def test_duplicate_observations_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate observed"):
            identity.reconcile([
                {"github_id": 589831718, "canonical_slug": "Comfy-Org/ComfyUI"},
                {"github_id": 589831718, "canonical_slug": "Comfy-Org/ComfyUI-copy"},
            ])

    def test_different_id_is_not_auto_merged_as_fork(self):
        result = identity.reconcile([{
            "github_id": 888888888888,
            "canonical_slug": "someone/ComfyUI",
        }])
        self.assertEqual(result["new_unreviewed"], 1)
        self.assertNotEqual(result["items"][0]["github_id"], 589831718)

    def test_manifest_is_exactly_reproducible(self):
        self.assertEqual(build_identity_index.main([]), 0)
        doc = build_identity_index.build()
        self.assertEqual(doc["n"], 34)
        self.assertEqual(doc["r"][0][0], min(identity.load()[0]))
        self.assertLess(len(json.dumps(doc)), 1700)

    def test_mcp_exact_resolution_uses_numeric_id(self):
        result = mcp.dispatch({
            "jsonrpc": "2.0", "id": 3, "method": "tools/call",
            "params": {"name": "resolve", "arguments": {"repo": "id:589831718"}},
        })
        self.assertFalse(result["result"]["isError"])
        payload = json.loads(result["result"]["content"][0]["text"])
        self.assertEqual(payload["github_id"], 589831718)
        self.assertLess(len(result["result"]["content"][0]["text"]), 700)


if __name__ == "__main__":
    unittest.main()
