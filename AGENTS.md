# RepoOrbit: agent-first entry (do not read the corpus)

Read `agent.json` for the machine contract. Route user tasks to `recommend` first; use `search` for exact lexical discovery, `resolve` for repository-level provenance, and `stats` for inventory. Request 1–5 results; avoid passing large datasets to the model.

With MCP: `repoorbit.mcp` is a **local stdio** server and needs no network at query time. Without a runtime: read `ai/intent.json` for eight EN/ES task intents, or `ai/index.json` and only the relevant `ai/terms/{letter}.json` for names.

Evidence: intent matches are **documented upstream capabilities**, not execution tests. `v=exists` means GitHub path existed when seeded; `v=not_checked` means a source linked it but the target was not checked. `free_requested` does **not** mean free verified. `strict_free=true` deliberately returns no results until independently checked pricing exists.

Never infer zero-cost operation, security, availability or full GitHub coverage. Preserve source IDs, README blob hashes, line numbers, and observation dates. Do not mirror external README bodies by default.

Daily licensed-feed monitoring remains read-only. A separate weekly automation may create **draft PRs only**, using immutable historical snapshots, approval pointers, index regeneration and strict churn limits; no automatic merge. Read `ai/status.json` for the current approved count rather than reusing an older hardcoded count. Never equate discovery references with verified working tools.

When only corpus size or verification status is needed, fetch `ai/status.json` (under 1 KB) instead of a large registry. Its counts are derived from the authoritative snapshots and checked in CI.

For exact seed resolution, prefer stable numeric IDs when known: `resolve({"repo":"id:589831718"})`. The 30 checked numeric IDs are indexed in `ai/identities.json`; 24 catalog references also have independently checked numeric IDs; 1,161 remaining reference-only paths do not. A rename is only recognized by an unchanged GitHub numeric ID. Identity monitoring is read-only and never automatically promotes a reference.

For checked discovery references use the exact `resolve` tool with slug or `id:23088740`; the returned role remains `reference`, with preserved catalog origin. `ai/verified-targets.json` holds 24 checked IDs (including archived metadata) in compact form. Do not infer working software or zero cost from this evidence.
