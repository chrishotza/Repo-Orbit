# RepoOrbit

**One search. Every repository.**

RepoOrbit is an open, evidence-first index for discovering GitHub projects and the catalogs that reference them. It aims to make finding useful software simple without confusing popularity with quality or source availability with free operation.

> **Project status: corpus and agent tooling v0.7.** RepoOrbit includes two approved discovery feeds, four local MCP tools, compact machine indexes and reviewable bot proposals. It is not a full GitHub index, hosted search engine, or independently verified software installer.


## AI-first access (the primary interface)

**Agents: read [AGENTS.md](AGENTS.md) (short) or [agent.json](agent.json) (machine-readable). Do not ingest this README, discovery JSONL snapshots, or upstream catalogs into context just to answer a query.**

Three token-efficient access modes are shipped. Additionally, **54 individually checked GitHub numeric IDs** are available for exact lookup, regardless of changes to a repository's name:

| Mode | Entry point | What is returned |
|---|---|---|
| **Task intent (EN/ES, no LLM)** | `recommend` via MCP or `ai/intent.json` without a runtime | Short suggestions grounded in 8 reviewed README snapshots; costs and execution remain unknown |
| **MCP, no network required** | \`python3 -m repoorbit.mcp\` as a configured stdio tool, not an interactive human workflow | Bounded \`search\`, exact \`resolve\`, compact \`stats\` |
| **Static, remote-readable** | \`ai/index.json\` then only \`ai/terms/{letter}.json\` | One small per-letter lexical reference shard |

**MCP host configuration** (set \`cwd\` to a checkout of this repository; the agent host starts this, not the human):

\`\`\`json
{"mcpServers":{"repoorbit":{"command":"python3","args":["-m","repoorbit.mcp"],"cwd":"/path/to/Repo-Orbit"}}}
\`\`\`

\`search({"q":"python","limit":3})\` gives only up to 3 terse records rather than loading the underlying corpus. \`resolve({"repo":"Comfy-Org/ComfyUI"})\` returns an exact project record with provenance, uncertainty and existence date. Lexical search **is not semantic understanding** and does not verify execution, pricing, or source-code safety.

The bilingual matcher currently supports **8 curated task intents**, not general semantic understanding. Unknown requests return no invented matches and can fall back to lexical search. The static lexical index still contains **1,215 unique GitHub paths across all roles** (2026-10-13). For the active, dynamically approved total, consult [ai/status.json](ai/status.json), with 26 independently addressable alphabetic shards. It is a partial corpus, not a crawl of GitHub. Only 24 discovered references have had their GitHub numeric identity checked; 1,161 reference-only paths remain unchecked. A verified ID proves neither software functionality nor free operation.

See [checked reference evidence](docs/TARGET_VERIFICATION.md), [stable GitHub identity rules](docs/IDENTITIES.md) and [AI protocol specification](docs/AI_PROTOCOL.md), [current corpus status](ai/status.json), and [static shard format](ai/index.json).

## What makes it different

- **Find things by purpose**, not just by repository name (planned).
- **Aggregate catalogs**, but preserve attribution and source-specific reuse policies.
- **One canonical project record** with all discovered references and no accidental duplicates.
- **Evidence over advertising**: a GitHub repository existing does not prove that its software runs, is safe, or costs nothing.
- **Explain costs honestly**: unknown is not free. APIs, hardware, hosting, models, and licenses are separate dimensions.
- **Zero mandatory paid services** for the core corpus maintenance scripts.

## Maintenance (automated)

Both existing CI workflows now pass officially on Python 3.10 (corpus integrity also passes on 3.12). A daily scheduled workflow rechecks two allowlisted CC0 catalogs and publishes read-only staging artifacts. A separate weekly workflow can **propose draft PRs** for conservative, verified reference changes without merging automatically. Approved snapshots are versioned; historical snapshots do not inflate the active corpus. Developers can find optional reproducibility procedures in [CORPUS.md](docs/CORPUS.md), [AI_PROTOCOL.md](docs/AI_PROTOCOL.md), [promotion safeguards](docs/PROMOTION.md), and [CONTRIBUTING.md](CONTRIBUTING.md). End users and agents do not need a shell or API credentials to read the static index.

## Layout

```text
AGENTS.md                    Minimal context instructions for agent runtimes
SKILL.md                     Agent skill entry point
agent.json                   Machine-readable tool and route manifest
ai/
  index.json                 Static shard format and routing
  terms/[a-z].json           Small self-contained lexical lookup shards
repoorbit/
  agent.py                   Deterministic offline tools (bounded JSON)
  mcp.py                     MCP stdio server
  build_index.py             Reproducible static index generator
  identity.py                Stable ID lookup and rename/transfer analysis
  identity_watch.py          Read-only GitHub drift monitor
  verified.py                Checked discovery evidence registry
  check_targets.py           Bounded, resumable staged GitHub checks
data/
  sources.json               Verified catalog and discovery-source registry
  repositories.jsonl         Small, traceable starting set of project references
  discoveries/              Unverified upstream references with provenance
  snapshots/                Generated enrichment output (not committed)
schemas/
  source.schema.json         Source registry record contract
  repository.schema.json     Repository record contract
scripts/
  corpus.py                  Offline validation, stats, on-demand metadata sync
  discoveries.py             License-gated URL extraction and discovery validation
tests/
  test_corpus.py             Corpus invariants and normalization checks
  test_discoveries.py        Discovery edge provenance tests
docs/
  CORPUS.md                  Data model, pipeline, quality and coverage definitions
  PROVENANCE.md              Attribution, licensing and claims policy
  ROADMAP.md                 Measurable implementation milestones
CONTRIBUTING.md              Rules for adding/reviewing records
```

## Real provenance-linked discovery snapshots

The corpus currently records **1,199 source-to-target references** from two independently checked CC0-licensed Awesome directories: 672 from `sindresorhus/awesome` and 527 from `sindresorhus/awesome-nodejs`. Four targets overlap across those two snapshots. At the 2026-10-13 audit, this resulted in **1,215 unique GitHub paths** including 22 catalog seeds and 8 individually existence-checked project seeds. Subsequent approved totals are in [ai/status.json](ai/status.json). **References are unverified URLs, not confirmed living projects or tested tools.** Every edge retains the source blob SHA and line number.

## Principles

1. **Never fabricate metrics or validation.** A missing measurement remains `null` or `unknown`.
2. **Preserve evidence.** Every seed reference has a source, verification date, and confidence state.
3. **Favor reproducible ingestion.** Canonical identities, validation, stable sorting, and auditable diffs.
4. **Respect creators.** Prefer links and API metadata; never bulk-mirror README text or code without checking rights and applicable platform terms.
5. **Prefer discoverability over gatekeeping.** Do not hide projects merely for low star counts; expose user-controlled filters.
6. **Keep search approachable.** End-user experience should eventually fit into one simple search field.

## Current limitations

The initial seed set is not an exhaustive census. `repository_exists` means only that the repository path was confirmed when seeded; it is **not** a test of installation, execution, security, maintainership, cost, or license compatibility. Catalog ingestion, semantic search, UI, and automated installation tests are later milestones.

See [corpus specification](docs/CORPUS.md), [provenance policy](docs/PROVENANCE.md), and [roadmap](docs/ROADMAP.md).

**Licensing:** Project code and original dataset licensing are pending a maintainer decision. Do not assume that publicly visible content from this or any upstream project is automatically licensed for redistribution.
