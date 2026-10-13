# English/Spanish routing contract, not a semantic search benchmark

RepoOrbit v0.10 adds `route_topic({"q":"necesito herramientas de ciberseguridad"})`, which maps supported phrases to one of the 14 controlled subject IDs. Clients can then call `browse({"category":"security","limit":5})`. Nothing about a repository's functionality or price follows from a routed topic.

## Conservative routing

- Explicit, versioned aliases are stored in `data/topic_aliases.json` for all 14 subjects. The router normalizes case, punctuation and accents.
- Whole phrases are matched. The longest match in words wins only when it belongs to a **single** category.
- If multiple categories have equally specific supported phrases, the router returns `ambiguous_supported_phrases` with no winning category.
- Unknown text returns `no_supported_phrase`. There are no invented fallback recommendations, embeddings, models, hosted API calls or web searches at runtime.
- Aliases are editable and fully visible; the matching algorithm is deterministic and bounded to a 200-character input.

## What was measured

`data/topic_route_probes.jsonl` contains 32 manually authored contract examples: 16 Spanish, 16 English, with 28 category matches and 4 explicit abstentions. `repoorbit.evaluate_topics` regenerates `ai/topic-route-eval.json` with errors and language counts and is enforced by CI.

**The current 32/32 result is in-distribution contract compliance, not held-out generalization accuracy.** The authors knew the aliases when preparing the cases. It cannot support a claim that RepoOrbit understands arbitrary Spanish or English requests, achieves a certain semantic relevance score, or discovers every suitable GitHub repository.

A genuine independent benchmark needs people labeling previously unseen queries and judging actual retrieved results, with precision@k, recall@k, ranking quality, confusion matrices, abstention calibration and failure cases by language, subject and project type.

## Agent workflow

Use a short query to select an area, then request a small bounded category page. For a shortlisted project call `classify` and `resolve` separately to inspect subject confidence, source evidence, stable GitHub ID, archival flags, and unknown cost/functionality. `route_topic` must not weaken verification rules.
