"""Bilingual topic routing contract: visible scope and honest abstention."""
from __future__ import annotations

import json
import unittest

from repoorbit import agent, evaluate_topics, mcp, route_topic


class TopicRoutingTests(unittest.TestCase):
    def test_all_fourteen_bilingual_domains_have_aliases(self):
        alias = route_topic.aliases()
        self.assertEqual(len(alias), 14)
        self.assertEqual(len({word for values in alias.values() for word in values}),
                         sum(len(v) for v in alias.values()))

    def test_known_spanish_accented_topic(self):
        result = route_topic.route_topic("Quiero AUTOMATIZACIÓN DE TAREAS")
        self.assertTrue(result["found"])
        self.assertEqual(result["category"], "automation")
        self.assertEqual(result["basis"], "curated_bilingual_phrase")

    def test_bilingual_input_no_false_semantic_claim(self):
        result = route_topic.route_topic("I need database management software")
        self.assertEqual(result["category"], "data-storage")
        self.assertEqual(result["semantics"], "controlled_phrase_only_not_semantic_search")

    def test_unknown_query_abstains(self):
        result = route_topic.route_topic("qué cosa linda encuentro hoy")
        self.assertFalse(result["found"])
        self.assertIsNone(result["category"])
        self.assertEqual(result["status"], "no_supported_phrase")

    def test_two_equal_topic_phrases_require_abstention(self):
        result = route_topic.route_topic("Necesito automatizacion de tareas y bases de datos")
        self.assertFalse(result["found"])
        self.assertEqual(result["status"], "ambiguous_supported_phrases")
        self.assertEqual(set(result["candidates"]), {"automation", "data-storage"})

    def test_input_is_bounded(self):
        for q in ("", " ", "a" * 201, None, 12):
            with self.subTest(q=q):
                with self.assertRaises(ValueError):
                    route_topic.route_topic(q)

    def test_mcp_exposes_route_tool_without_extra_repo_metadata(self):
        names = {t["name"] for t in mcp.TOOLS}
        self.assertIn("route_topic", names)
        reply = mcp.dispatch({
            "jsonrpc": "2.0", "id": 3, "method": "tools/call",
            "params": {"name": "route_topic", "arguments": {"q": "quiero ciberseguridad"}}
        })
        self.assertFalse(reply["result"]["isError"])
        result = json.loads(reply["result"]["content"][0]["text"])
        self.assertEqual(result["category"], "security")
        self.assertNotIn("working", result)
        self.assertNotIn("cost", result)

    def test_agent_still_maintains_separate_evidence_layers(self):
        result = agent.call("route_topic", {"q": "smart contracts"})
        self.assertEqual(result["category"], "blockchain")
        self.assertNotIn("r", result)

    def test_32_regression_cases_are_reproducible_not_general_accuracy(self):
        self.assertEqual(evaluate_topics.main([]), 0)
        result = evaluate_topics.evaluate()
        self.assertEqual(result["total"], 32)
        self.assertEqual(result["correct"], 32)
        self.assertEqual(result["abstention_cases"], 4)
        self.assertEqual(result["correct_abstentions"], 4)
        self.assertEqual(result["languages"]["es_total"], 16)
        self.assertEqual(result["languages"]["en_total"], 16)
        self.assertIn("not_semantic_accuracy", result["scope"])


if __name__ == "__main__":
    unittest.main()
