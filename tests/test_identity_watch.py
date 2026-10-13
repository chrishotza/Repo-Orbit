"""Identity watcher: only GitHub IDs establish continuity, no automated rewrites."""
from __future__ import annotations

import io
import json
from unittest.mock import patch
import unittest

from repoorbit import identity, identity_watch


class IdentityWatchTests(unittest.TestCase):
    def test_all_thirty_seed_ids_resolve_in_mocked_observation(self):
        def fake_fetch(slug):
            row = identity.lookup(slug)
            return {"github_id": row["github_id"], "canonical_slug": row["canonical_slug"]}
        result = identity_watch.observe(fake_fetch, delay=0)
        self.assertEqual(result["registered"], 30)
        self.assertEqual(result["resolved"], 30)
        self.assertEqual(result["unresolved"], [])
        self.assertEqual(result["drift"]["unchanged"], 30)
        self.assertEqual(result["drift"]["missing_ids"], [])

    def test_rename_detected_only_with_unchanged_numeric_id(self):
        def fake_fetch(slug):
            row = identity.lookup(slug)
            actual = row["canonical_slug"]
            if row["github_id"] == 589831718:
                actual = "Comfy-Org/ComfyUI-new-name"
            return {"github_id": row["github_id"], "canonical_slug": actual}
        result = identity_watch.observe(fake_fetch)
        self.assertEqual(result["drift"]["renamed"], 1)
        self.assertEqual(result["drift"]["transferred"], 0)

    def test_transfer_detected_with_same_numeric_id(self):
        def fake_fetch(slug):
            row = identity.lookup(slug)
            actual = row["canonical_slug"]
            if row["github_id"] == 589831718:
                actual = "Future-Org/ComfyUI"
            return {"github_id": row["github_id"], "canonical_slug": actual}
        result = identity_watch.observe(fake_fetch)
        self.assertEqual(result["drift"]["transferred"], 1)

    def test_404_is_unknown_not_a_deletion(self):
        def fake_fetch(slug):
            row = identity.lookup(slug)
            if row["github_id"] == 589831718:
                return None
            return {"github_id": row["github_id"], "canonical_slug": row["canonical_slug"]}
        result = identity_watch.observe(fake_fetch)
        self.assertEqual(result["resolved"], 29)
        self.assertEqual(len(result["unresolved"]), 1)
        self.assertEqual(result["drift"]["not_checked_this_run"], 1)

    def test_reused_slug_with_wrong_numeric_id_is_blocked(self):
        def fake_fetch(slug):
            row = identity.lookup(slug)
            return {"github_id": row["github_id"] + 123, "canonical_slug": row["canonical_slug"]}
        with self.assertRaisesRegex(identity_watch.IdentityWatchError, "slug-to-ID collision"):
            identity_watch.observe(fake_fetch)

    def test_offline_check_no_network(self):
        output = io.StringIO()
        with patch("sys.stdout", output):
            self.assertEqual(identity_watch.main(["--check"]), 0)
        self.assertEqual(json.loads(output.getvalue())["verified_seed_ids"], 30)

    def test_sampled_watch_does_not_claim_non_sampled_repositories_are_gone(self):
        invoked = []
        def fake_fetch(slug):
            invoked.append(slug)
            row = identity.lookup(slug)
            return {"github_id": row["github_id"], "canonical_slug": row["canonical_slug"]}
        result = identity_watch.observe(fake_fetch, delay=0, limit=3)
        self.assertEqual(len(invoked), 3)
        self.assertEqual(result["registered"], 30)
        self.assertEqual(result["resolved"], 3)
        self.assertEqual(result["drift"]["not_checked_this_run"], 27)
        self.assertIs(result["sampled"], True)

    def test_invalid_sample_limits_fail_closed(self):
        for limit in (-1, 31, True, "3"):
            with self.subTest(limit=limit):
                with self.assertRaises(ValueError):
                    identity_watch.observe(lambda _: None, limit=limit)

    def test_negative_delay_rejected(self):
        with self.assertRaisesRegex(ValueError, "delay cannot be negative"):
            identity_watch.observe(lambda _: None, delay=-1)

    def test_identity_watch_does_not_modify_approved_identity_registry(self):
        before = identity.REGISTRY.read_bytes()
        def fake_fetch(slug):
            row = identity.lookup(slug)
            return {"github_id": row["github_id"], "canonical_slug": "new-owner/new-name"
                    if row["github_id"] == 589831718 else row["canonical_slug"]}
        identity_watch.observe(fake_fetch)
        self.assertEqual(before, identity.REGISTRY.read_bytes())


if __name__ == "__main__":
    unittest.main()
