"""Bilingual intent routing tests. No network, no embeddings, no fake free claims."""
import json
import unittest

from repoorbit import agent, mcp, build_intent_index
from repoorbit.recommend import normalize, recommend, _registry


class IntentTests(unittest.TestCase):
    def test_static_manifest_matches_verified_registry(self):
        self.assertEqual(build_intent_index.main([]), 0)
        from pathlib import Path
        manifest = json.loads((Path(agent.ROOT) / "ai" / "intent.json").read_text(encoding="utf-8"))
        self.assertEqual(len(manifest["a"]), 8)
        self.assertIs(manifest["cost_verified"], False)

    def test_eight_manual_tasks_have_traced_sources(self):
        data = _registry()
        self.assertEqual(len(data["intents"]), 8)
        self.assertEqual(len(data["repositories"]), 8)
        for fact in data["repositories"].values():
            self.assertEqual(len(fact["readme_blob_sha"]), 40)
            self.assertEqual(fact["cost"], "unknown")
            self.assertIs(fact["tested"], False)

    def test_spanish_video_generation(self):
        result = recommend("Quiero generar videos con IA gratis")
        self.assertIn("generate-video", result["intents"])
        self.assertIn("Comfy-Org/ComfyUI", [x["r"] for x in result["items"]])
        self.assertEqual(result["warning"], "cost_not_verified")
        self.assertTrue(result["free_requested"])
        self.assertIs(result["free_verified"], False)
        self.assertTrue(all(x["cost"] == "unknown" and x["tested"] is False for x in result["items"]))

    def test_spanish_accents(self):
        self.assertEqual(normalize("Generación de IMÁGENES"), "generacion de imagenes")
        result = recommend("Necesito generación de imágenes")
        self.assertEqual(result["intents"][0], "generate-images")

    def test_local_models(self):
        result = recommend("Quiero ejecutar modelos locales sin pagar APIs")
        self.assertIn("local-llm", result["intents"])
        self.assertEqual({x["r"] for x in result["items"]}, {
            "ollama/ollama", "ggml-org/llama.cpp"
        })
        self.assertTrue(result["free_requested"])

    def test_automation(self):
        result = recommend("Busco automatizar tareas", limit=1)
        self.assertEqual(result["intents"], ["automate-workflows"])
        self.assertEqual(result["items"][0]["r"], "n8n-io/n8n")

    def test_english_serving(self):
        result = recommend("Need an LLM serving framework")
        self.assertIn("serve-llm", result["intents"])
        self.assertIn("vllm-project/vllm", [x["r"] for x in result["items"]])

    def test_no_guess_for_unknown_query(self):
        result = recommend("simular la tectónica de placas")
        self.assertEqual(result["items"], [])
        self.assertEqual(result["warning"], "no_curated_intent_match")

    def test_strict_free_fails_closed(self):
        result = recommend("generar videos gratis", strict_free=True)
        self.assertEqual(result["items"], [])
        self.assertEqual(result["n"], 0)
        self.assertEqual(result["warning"], "no_verified_free_candidates")

    def test_bounded_output(self):
        result = recommend("crear aplicaciones de IA", limit=1)
        self.assertEqual(len(result["items"]), 1)
        self.assertTrue(result["more"])
        with self.assertRaises(ValueError):
            recommend("generar videos", limit=100)
        with self.assertRaises(ValueError):
            recommend("generar videos", strict_free="yes")

    def test_mcp_recommend_tool(self):
        result = mcp.dispatch({
            "jsonrpc": "2.0", "id": 7, "method": "tools/call",
            "params": {"name": "recommend", "arguments": {"q": "generar videos gratis", "limit": 1}}
        })
        self.assertFalse(result["result"]["isError"])
        payload = result["result"]["content"][0]["text"]
        self.assertLess(len(payload), 1200)
        self.assertEqual(json.loads(payload)["items"][0]["r"], "Comfy-Org/ComfyUI")

    def test_recommend_is_invocable_as_pure_function(self):
        result = agent.call("recommend", {"q": "interfaces en python", "limit": 1})
        self.assertEqual(result["items"][0]["r"], "gradio-app/gradio")
        with self.assertRaises(ValueError):
            agent.call("recommend", {"q": "video", "untrusted": True})

    def test_no_fabricated_capabilities_for_unknown_terms(self):
        # A generic term is not sufficient proof of a supported task.
        self.assertEqual(recommend("video")["items"], [])
        self.assertEqual(recommend("AI")["items"], [])


if __name__ == "__main__":
    unittest.main()
