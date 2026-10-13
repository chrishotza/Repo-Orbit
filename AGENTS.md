# RepoOrbit: agent-first entry (do not read the corpus)

Read `agent.json` for the machine contract. Route user tasks to `recommend` first; use `search` for exact lexical discovery, `resolve` for repository-level provenance, and `stats` for inventory. Request 1–5 results; avoid passing large datasets to the model.

With MCP: `repoorbit.mcp` is a **local stdio** server and needs no network at query time. Without a runtime: read `ai/intent.json` for eight EN/ES task intents, or `ai/index.json` and only the relevant `ai/terms/{letter}.json` for names.

Evidence: intent matches are **documented upstream capabilities**, not execution tests. `v=exists` means GitHub path existed when seeded; `v=not_checked` means a source linked it but the target was not checked. `free_requested` does **not** mean free verified. `strict_free=true` deliberately returns no results until independently checked pricing exists.

Never infer zero-cost operation, security, availability or full GitHub coverage. Preserve source IDs, README blob hashes, line numbers, and observation dates. Do not mirror external README bodies by default.
