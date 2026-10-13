# RepoOrbit implementation roadmap

Goal: **the simplest trustworthy interface for discovering useful repositories**.

| Stage | Deliverable | Acceptance criteria |
|---|---|---|
| 0. Corpus foundation | Verified discovery roots, project seeds, 672 licensed index references, schemas, provenance policy, CLI and offline tests | Seeds linked to canonical URLs; dedup and validation; unknown costs remain unknown |
| 1. Reliable metadata | Incremental GitHub API ingestion with rate-aware retry, caching, rename detection and snapshots | Deterministic, resumable sync; no lost provenance; age and error metrics reported |
| 2. Catalog adapters | Explicitly permitted adapters for selected discovery directories | Per-source license/terms review, attribution, URL-level references, parser tests, extraction counts |
| 3. Search | Keyword search, taxonomy and human-reviewed evaluation set | Search works without an account, measurable query success; transparent filters |
| 4. Verification | Independent checks of installation requirements, free tiers and reproducible examples | Every strong claim points to dated evidence; errors and unknowns shown |
| 5. Accessible website | One natural-language search field and clear result comparisons | Keyboard and screen-reader accessible; visible source, date, license and cost uncertainty |
| 6. Sustainable scale | Contributor workflows, scheduled checks, quality dashboards | Monitored freshness and coverage with no misleading total-GitHub claims |

## Shipped AI-first layer (v0.2)

- \`AGENTS.md\`, \`SKILL.md\` and \`agent.json\` give concise machine-first navigation, without making a human walkthrough the entrypoint.
- \`repoorbit.agent\` provides bounded, deterministic offline \`search\`, \`resolve\` and \`stats\` functions.
- \`repoorbit.mcp\` exposes those functions as local MCP stdio tools; **not** a hosted MCP endpoint.
- \`ai/index.json\` and \`ai/terms/[a-z].json\` are 26 self-contained remote-readable lexical shards, generated from the 692 unique paths currently known across all roles.
- \`repoorbit.build_index\` supports deterministic regeneration and CI staleness checking.
- Automated Python tests cover MCP shape, provenance, bounded output, and generated index integrity. Remote CI success has not yet been independently confirmed.

### v0.3 bilingual routing shipped

- Reviewed eight upstream README snapshots, recorded exact Git blob fingerprints and default branches.
- Added eight conservative task intents in Spanish and English with no model/API dependency.
- Added the bounded `recommend` MCP tool and a 1.9 KB remote-readable `ai/intent.json` manifest.
- Added regression tests for supported task matching, missing intents, false-free assertions and strict-free abstention.
- Added deterministic intent-manifest CI verification. **Remote CI outcome remains unconfirmed** until we can inspect an actual workflow result.

### Next acceptance gate

1. Observe green GitHub Actions results on both configured Python versions, repairing any failures.
2. Build a held-out multilingual task evaluation set (not copied from the curated aliases), measure precision/recall and explicit abstention, and fix high-impact gaps before scaling.
3. Introduce evidence-based capabilities; only then add query-expansion or semantic retrieval without falsely implying support.
4. Make upstream discovery incremental and rights-aware, with stable GitHub numeric IDs and cached rate-limited refresh.
5. Keep the machine manifest compact, stable and versioned as the corpus grows.

## Immediate engineering priorities

1. Run offline unit tests and create a CI job that enforces them.
2. Add schema-validation tooling and fixture-based parser tests, while retaining a dependency-free base CLI.
3. Build an idempotent GitHub metadata worker with ETag caching, retry/backoff, rate-limit telemetry and stable numeric-ID reconciliation.
4. Create a **discovery edge** store: which catalog entry pointed to which project, when, and under what license/policy.
5. Implement a thin, user-first search prototype against a small fully indexed corpus; establish a baseline benchmark before scaling.
6. Agree on public code and original-data licenses with the repository owner.

## Rejected shortcuts

- Bulk-forking thousands of upstream repositories.
- Equating stars with quality.
- Marking public code as open source when no usable license is known.
- Labelling a project free based solely on a free download.
- Presenting README promises as executed validation.
- Declaring comprehensive coverage using only a small set of Awesome lists.
- Putting API secrets in commits, examples or generated snapshots.

## Definition of done for a feature

A feature requires documented inputs/outputs, tests, provenance preservation, failure behavior, measured limitations, and an example that actually runs. UI polish alone is not completion.
