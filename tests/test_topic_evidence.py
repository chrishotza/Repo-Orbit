"""README-backed categories are documentary statements, not runtime tests."""
from __future__ import annotations

import json
import unittest

from repoorbit import agent, audit_topics, build_taxonomy_index, mcp, taxonomy, topic_evidence
from repoorbit.refresh import _blob_sha


class TopicEvidenceTests(unittest.TestCase):
    def test_twelve_reviewed_readmes_link_to_previously_checked_ids(self):
        data = topic_evidence.load()
        self.assertEqual(len(data), 23)
        self.assertEqual(len({x["github_id"] for x in data.values()}), 23)
        self.assertTrue(all(len(x["readme_blob_sha"]) == 40 for x in data.values()))
        self.assertTrue(all(x["execution_test"] == "not_run" and x["cost"] == "unknown"
                            for x in data.values()))

    def test_documentation_promotes_topic_not_functionality(self):
        examples = {
            "axios/axios": "developer-tools",
            "Automattic/mongoose": "data-storage",
            "agenda/agenda": "automation",
            "bee-queue/bee-queue": "automation",
            "apostrophecms/apostrophe": "web-apps",
            "amplication/amplication": "cloud-devops",
        }
        for slug, cat in examples.items():
            with self.subTest(slug=slug):
                result = taxonomy.classify(slug)
                self.assertEqual(result["category"], cat)
                self.assertEqual(result["basis"], "readme_topic_evidence")
                self.assertEqual(result["v"], "exists")
                self.assertEqual(len(result["readme_evidence"]["sha"]), 40)
                self.assertGreater(result["readme_evidence"]["line"], 0)

    def test_exact_immutable_evidence_pointer_and_human_readable_link(self):
        info = taxonomy.classify("axios/axios")["readme_evidence"]
        self.assertTrue(info["blob_api"].endswith("/git/blobs/e305c5927833a31f5fcf274a02e71150a3c087c0"))
        self.assertIn("/blob/v1.x/README.md#L472", info["readme_url"])
        self.assertEqual(info["observed"], "2026-10-13")
        self.assertIn("HTTP", info["summary"])

    def test_unknown_reference_still_abstains(self):
        item = taxonomy.classify("0pandadev/awesome-windows")
        self.assertEqual(item["basis"], "slug_keyword_hint")
        self.assertNotIn("readme_evidence", item)

    def test_preexisting_editorial_seed_has_precedence(self):
        result = taxonomy.classify("ollama/ollama")
        self.assertEqual(result["basis"], "editorial_seed_subject")

    def test_every_readme_category_is_in_reproducible_shard(self):
        docs = build_taxonomy_index.build()
        self.assertEqual(build_taxonomy_index.main([]), 0)
        reviewed = [(bucket, r) for bucket, content in docs.items()
                    if bucket != "index.json"
                    for r in content["r"] if r[3] == "d"]
        self.assertEqual(len(reviewed), 23)
        for slug, fact in topic_evidence.load().items():
            self.assertIn((fact["category"] + ".json",
                           next(row for row in docs[fact["category"] + ".json"]["r"]
                                if row[0].casefold() == slug)), reviewed)
        self.assertEqual(len(docs["unclassified.json"]["r"]), 1153)
        self.assertEqual(sum(len(v["r"]) for k,v in docs.items() if k != "index.json"), 1462)

    def test_readme_labels_have_no_faked_security_or_cost(self):
        result = taxonomy.classify("ai/nanoid")
        self.assertNotIn("cost", result)
        self.assertNotIn("working", result)
        self.assertEqual(agent.stats()["cost_free_verified"], 0)
        self.assertEqual(agent.stats()["working_verified"], 0)

    def test_compact_mcp_classify_exposes_source_pointer(self):
        response = mcp.dispatch({
            "jsonrpc": "2.0", "id": 44, "method": "tools/call",
            "params": {"name": "classify", "arguments": {"repo": "axios/axios"}}
        })
        self.assertIs(response["result"]["isError"], False)
        raw = response["result"]["content"][0]["text"]
        self.assertLess(len(raw), 1300)
        item = json.loads(raw)
        self.assertEqual(item["basis"], "readme_topic_evidence")
        self.assertEqual(item["readme_evidence"]["line"], 472)

    def test_offline_audit_registry_validation_never_uses_network(self):
        self.assertEqual(audit_topics.main(["--check"]), 0)

    def test_audit_exact_bytes_and_line_offline(self):
        real = next(iter(topic_evidence.load().values()))
        raw = b"\n" * (real["line"] - 1) + real["anchor"].encode("utf-8") + b"\n"
        row = dict(real, readme_blob_sha=_blob_sha(raw))
        report = audit_topics.audit([row], lambda _: raw)
        self.assertEqual(report["audited"], 1)
        self.assertEqual(report["items"][0]["status"], "exact_blob_and_line_verified")

    def test_audit_wrong_anchor_rejected(self):
        real = next(iter(topic_evidence.load().values()))
        raw = b"Different source content\n"
        row = dict(real, readme_blob_sha=_blob_sha(raw), line=1)
        with self.assertRaisesRegex(audit_topics.TopicAuditError, "fingerprint mismatch"):
            audit_topics.audit([row], lambda _: raw)

    def test_audit_wrong_git_sha_rejected(self):
        real = next(iter(topic_evidence.load().values()))
        with self.assertRaisesRegex(audit_topics.TopicAuditError, "Git hash changed"):
            audit_topics.audit([real], lambda _: b"tampered")

    def test_audit_rejects_unbounded_requests(self):
        with self.assertRaises(audit_topics.TopicAuditError):
            audit_topics.audit([], lambda _: b"")
        with self.assertRaises(audit_topics.TopicAuditError):
            audit_topics.audit([{}] * 26, lambda _: b"")


if __name__ == "__main__":
    unittest.main()
