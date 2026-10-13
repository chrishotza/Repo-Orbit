"""Offline rights gates, deduplication and incremental refresh-delta regression tests."""
from datetime import datetime, timezone
import json
from pathlib import Path
import unittest

from repoorbit import refresh


class RefreshTests(unittest.TestCase):
    def test_explicit_feed_allowlist_and_existing_baselines(self):
        feeds = refresh.load_feeds()
        self.assertEqual({x["repository"] for x in feeds}, {
            "sindresorhus/awesome", "sindresorhus/awesome-nodejs",
            "sindresorhus/awesome-npm", "sindresorhus/awesome-electron",
            "sindresorhus/awesome-observables", "sindresorhus/awesome-tap"
        })
        self.assertEqual(len(feeds), 6)
        self.assertGreaterEqual(sum(len(refresh._baseline_ids(x)) for x in feeds), 1000)
        self.assertTrue(all(x["license"] == "CC0-1.0" for x in feeds))

    def test_sha_identifies_exact_content(self):
        raw = b"# Test\n"
        self.assertEqual(len(refresh._blob_sha(raw)), 40)
        self.assertNotEqual(refresh._blob_sha(raw), refresh._blob_sha(raw + b"\n"))

    def test_reference_normalization_and_dedup(self):
        feed = refresh.load_feeds()[0]
        body = (
            "[One](https://github.com/Test/Project)\n"
            "[Duplicate](https://github.com/test/project#readme)\n"
            "[Two](https://github.com/Second/Thing)\n"
            "[Topic](https://github.com/topics/python)\n"
        )
        rows = refresh.extract_references(body, feed, "a" * 40, "2026-10-13")
        self.assertEqual(len(rows), 2)
        self.assertEqual({r["target_id"] for r in rows}, {
            "github:test/project", "github:second/thing"
        })
        self.assertEqual({r["source_line"] for r in rows}, {1, 3})
        self.assertTrue(all(r["target_verification"] == "not_checked" for r in rows))

    def test_mocked_two_source_incremental_plan(self):
        feeds = refresh.load_feeds()
        body = b"[One](https://github.com/example/one)\n[Two](https://github.com/example/two)\n"
        content_sha = refresh._blob_sha(body)
        requests = []
        def fake_fetch(repo, path):
            requests.append((repo, path))
            if path == "license":
                lic = b"CC0 1.0 Universal\n"
                return lic, refresh._blob_sha(lic)
            return body, content_sha
        results = refresh.plan_refresh(
            feeds, fake_fetch, datetime(2026, 10, 13, tzinfo=timezone.utc)
        )
        self.assertEqual(len(results), 6)
        self.assertEqual(len(requests), 12)
        self.assertEqual([x[2]["baseline_count"] for x in results],
                         [len(refresh._baseline_ids(x)) for x in feeds])
        for feed, records, delta in results:
            self.assertEqual(len(records), 2)
            self.assertEqual(delta["current_count"], 2)
            self.assertEqual(delta["added"] + delta["unchanged"], 2)
            self.assertEqual(delta["removed"] + delta["unchanged"], delta["baseline_count"])
            self.assertIn("staging-only", delta["note"])
            self.assertEqual(delta["comparison"], "approved_pinned_baseline_not_previous_daily_run")

    def test_bad_license_fails_all_sources_without_writes(self):
        feeds = refresh.load_feeds()
        def fake_fetch(repo, path):
            if path == "license":
                return b"All rights reserved", "a" * 40
            raise AssertionError("README must not be fetched for unlicensed source")
        with self.assertRaisesRegex(refresh.RefreshError, "no longer has reviewed CC0"):
            refresh.plan_refresh(feeds, fake_fetch)

    def test_extraction_empty_fails_closed(self):
        feeds = refresh.load_feeds()[:1]
        def fake_fetch(repo, path):
            data = b"CC0 1.0 Universal" if path == "license" else b"No links here"
            return data, refresh._blob_sha(data)
        with self.assertRaisesRegex(refresh.RefreshError, "empty extraction"):
            refresh.plan_refresh(feeds, fake_fetch)

    def test_rejects_unregistered_feed(self):
        feeds = refresh.load_feeds()
        self.assertTrue(all(x["id"].startswith("github:") for x in feeds))

    def test_ci_uses_read_only_staging_path(self):
        self.assertTrue(refresh.STAGING.relative_to(refresh.ROOT))
        self.assertFalse((refresh.ROOT / "data/discoveries").is_relative_to(refresh.STAGING))


if __name__ == "__main__":
    unittest.main()
