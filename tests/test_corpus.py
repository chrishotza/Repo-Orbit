"""Offline invariants for the RepoOrbit seed corpus (standard library only)."""
from contextlib import redirect_stdout, redirect_stderr
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import corpus


class CorpusTests(unittest.TestCase):
    def test_seed_registry_is_valid(self):
        sources, repos = corpus.validate()
        self.assertGreater(len(sources), 0)
        self.assertGreater(len(repos), 0)

    def test_canonical_ids_are_case_insensitive(self):
        self.assertEqual(corpus.canonical_id("Comfy-Org/ComfyUI"),
                         corpus.canonical_id("comfy-org/comfyui"))

    def test_invalid_repository_name_rejected(self):
        for invalid in ("", "owner", "owner/repo/extra", "../repo", "owner/../repo", "user/a space"):
            with self.subTest(invalid=invalid):
                with self.assertRaises(corpus.CorpusError):
                    corpus.assert_repository_name(invalid, "test")

    def test_unknown_values_are_not_converted_to_free_or_working(self):
        seed = corpus.load_repositories()[0]
        now = datetime(2026, 10, 12, tzinfo=timezone.utc)
        github = {
            "id": 123, "full_name": seed["full_name"], "stargazers_count": 10,
            "language": "Python", "archived": False, "updated_at": "2026-10-12T00:00:00Z",
            "license": {"spdx_id": "NOASSERTION"}
        }
        enriched = corpus.enrich(seed, github, now)
        self.assertEqual(enriched["cost"], "unknown")
        self.assertEqual(enriched["functional_test"], "not_run")
        self.assertIsNone(enriched["license_spdx"])
        self.assertEqual(enriched["stars"], 10)
        self.assertEqual(enriched["metadata_fetched_at"], "2026-10-12T00:00:00Z")
        self.assertEqual(seed["stars"], None)

    def test_duplicate_sources_rejected(self):
        doc = json.loads(corpus.SOURCES.read_text(encoding="utf-8"))
        duplicate = dict(doc["sources"][0])
        duplicate["repository"] = duplicate["repository"].upper()
        duplicate["id"] = corpus.canonical_id(duplicate["repository"])
        duplicate["url"] = corpus.github_url(duplicate["repository"])
        doc["sources"].append(duplicate)
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "sources.json"
            path.write_text(json.dumps(doc), encoding="utf-8")
            with self.assertRaisesRegex(corpus.CorpusError, "duplicate"):
                corpus.load_sources(path)

    def test_duplicate_projects_rejected(self):
        original = corpus.REPOSITORIES.read_text(encoding="utf-8").strip()
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "repos.jsonl"
            path.write_text(original + "\n" + original.splitlines()[0] + "\n", encoding="utf-8")
            with self.assertRaisesRegex(corpus.CorpusError, "duplicate"):
                corpus.load_repositories(path)

    def test_atomic_write_is_sorted(self):
        records = [
            {"id": "github:z/repo", "full_name": "z/repo"},
            {"id": "github:a/repo", "full_name": "a/repo"}
        ]
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "new" / "snapshot.jsonl"
            corpus.write_jsonl_atomic(path, records)
            saved = [json.loads(line) for line in path.read_text().splitlines()]
            self.assertEqual(saved[0]["id"], "github:a/repo")
            self.assertEqual(saved[1]["id"], "github:z/repo")

    def test_cli_offline_commands(self):
        for cmd in ("validate", "stats"):
            with self.subTest(cmd=cmd):
                out = io.StringIO()
                with redirect_stdout(out):
                    self.assertEqual(corpus.main([cmd]), 0)
                self.assertTrue(out.getvalue().strip())

    def test_dry_run_does_not_call_network(self):
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(corpus.main(["sync", "--limit", "2", "--dry-run"]), 0)
        self.assertEqual(len(out.getvalue().splitlines()), 2)

    def test_seed_inputs_cannot_be_overwritten(self):
        err = io.StringIO()
        with redirect_stderr(err):
            result = corpus.main(["sync", "--output", str(corpus.REPOSITORIES)])
        self.assertEqual(result, 1)
        self.assertIn("refusing to overwrite", err.getvalue())

    def test_missing_license_does_not_imply_open_source(self):
        seed = corpus.load_repositories()[0]
        enriched = corpus.enrich(seed, {"id": 1, "license": None}, datetime.now(timezone.utc))
        self.assertIsNone(enriched["license_spdx"])


if __name__ == "__main__":
    unittest.main()
