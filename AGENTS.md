# RepoOrbit — minimal AI agent instructions (v0.8)

Primary contract: `agent.json`. **Do not read the full corpus, all READMEs or source snapshots to answer a query.**

## Route by user intent

- `recommend({q,limit})`: 8 documentary EN/ES task intents; only documentation-backed seeds. `strict_free=true` excludes everything until actual free-execution evidence exists.
- `categories({})`: bilingual subject IDs and exact counts.
- `browse({category,limit,offset,verified_only})`: <=20 compact results; `verified_only` means GitHub path existed, not functional execution.
- `classify({repo})`: one category and its evidence basis (`editorial_seed_subject`, `slug_keyword_hint`, `ambiguous_slug_keywords` or `no_subject_evidence`).
- `search({q,limit})`: lexical fallback for names, not semantic retrieval.
- `resolve({repo})`: exact seed/reference, numeric `id:<number>` where checked, catalog source/blob SHA/line and cost unknowns.
- `stats({})`: compact repository counts and verification statuses.

Without MCP: `ai/categories/index.json` -> **only** `ai/categories/{id}.json`. Other routes: `ai/intent.json`, `ai/index.json`, `ai/terms/{first_letter}.json`, `ai/status.json`, `ai/identities.json`, `ai/verified-targets.json`.

Classification is an editorial or lexical **subject hint**, never a proven software capability. 30 seeds were assigned editorial labels; 178 references carry lexical subject hints; ambiguous/unmatched links stay unclassified. Never promote a raw URL into a tested, secure or no-cost project. `v=exists` confirms only observed GitHub-path existence.

Prefer 1–5 hits, request detailed evidence only for selected repositories. Preserve original catalog provenance and stable numeric IDs; source-repository license does not authorize reusing linked project code. No paid APIs, LLM or embeddings required for local lookup.
