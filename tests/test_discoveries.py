"""Offline tests for provenance-preserving discovery edges."""
from pathlib import Path
import json
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import corpus
import discoveries


class DiscoveryTests(unittest.TestCase):
    def test_saved_snapshot_validates(self):
        ids = {source["id"] for source in corpus.load_sources()}
        paths = sorted(discoveries.DISCOVERY_DIR.glob("*.jsonl"))
        self.assertTrue(paths)
        self.assertGreaterEqual(sum(discoveries.validate_snapshot(p, ids) for p in paths), 600)

    def test_parser_keeps_only_unique_repo_references(self):
        sample = (
            "[A](https://github.com/Org/Repo#readme)\n"
            "[B](https://github.com/org/repo)\n"
            "[Topic](https://github.com/topics/python)\n"
            "[C](https://github.com/Another/Tool/blob/main/README.md)\n"
        )
        rows = discoveries.extract_references(
            sample, "sindresorhus/awesome", "a" * 40,
            "2026-10-12", "CC0-1.0"
        )
        self.assertEqual(len(rows), 2)
        self.assertEqual({x["target_id"] for x in rows},
                         {"github:org/repo", "github:another/tool"})
        self.assertTrue(all(x["target_verification"] == "not_checked" for x in rows))
        self.assertTrue(all(x["source_blob_sha"] == "a" * 40 for x in rows))

    def test_wrong_license_rejected(self):
        with self.assertRaises(corpus.CorpusError):
            discoveries.extract_references("", "sindresorhus/awesome",
                                            "a" * 40, "2026-10-12", "unknown")

    def test_duplicate_edges_rejected(self):
        edge = discoveries.extract_references(
            "https://github.com/Org/Repo", "sindresorhus/awesome",
            "f" * 40, "2026-10-12", "CC0-1.0"
        )[0]
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "edges.jsonl"
            p.write_text(json.dumps(edge) + "\n" + json.dumps(edge) + "\n")
            with self.assertRaisesRegex(corpus.CorpusError, "duplicate edge"):
                discoveries.validate_snapshot(p, {"github:sindresorhus/awesome"})

    def test_validation_rejects_false_check_claim(self):
        edge = discoveries.extract_references(
            "https://github.com/Org/Repo", "sindresorhus/awesome",
            "f" * 40, "2026-10-12", "CC0-1.0"
        )[0]
        edge["target_verification"] = "verified_working"
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "bad.jsonl"
            p.write_text(json.dumps(edge) + "\n")
            with self.assertRaisesRegex(corpus.CorpusError, "unsupported validation"):
                discoveries.validate_snapshot(p, {"github:sindresorhus/awesome"})


if __name__ == "__main__":
    unittest.main()
