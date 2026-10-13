# RepoOrbit implementation roadmap

Goal: **the simplest trustworthy interface for discovering useful repositories**.

| Stage | Deliverable | Acceptance criteria |
|---|---|---|
| 0. Corpus foundation | Verified discovery roots, project seeds, 1,199 licensed discovery edges from two sources, schemas, provenance policy, CLI and offline tests | Seeds linked to canonical URLs; dedup and validation; unknown costs remain unknown |
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
- \`ai/index.json\` and \`ai/terms/[a-z].json\` are 26 self-contained remote-readable lexical shards, generated from the 1,215 unique paths currently known across all roles.
- \`repoorbit.build_index\` supports deterministic regeneration and CI staleness checking.
- Automated Python tests cover MCP shape, provenance, bounded output, and generated index integrity. Both workflows were officially observed passing on 2026-10-13, after fixing pytest packaging/imports.

### v0.3 bilingual routing shipped

- Reviewed eight upstream README snapshots, recorded exact Git blob fingerprints and default branches.
- Added eight conservative task intents in Spanish and English with no model/API dependency.
- Added the bounded `recommend` MCP tool and a 1.9 KB remote-readable `ai/intent.json` manifest.
- Added regression tests for supported task matching, missing intents, false-free assertions and strict-free abstention.
- Added deterministic intent-manifest CI verification. **Remote CI was observed passing** on 2026-10-13; future bot PR runs must be checked separately.

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

## v0.4 staged source refresh

- Added a second verified CC0 discovery source (527 Node.js links).
- Published 1,199 total discovery edges and reindexed 1,215 unique GitHub slugs.
- Added two-source CC0 allowlist, exact Git blob hash validation, license rechecking and per-source incremental differences.
- Added a read-only scheduled GitHub Actions workflow that emits artifacts. It does **not** auto-push unreviewed data.
- Added offline regression cases for deduplication, license rejection, empty-source rejection and delta arithmetic.
- Next gate: obtain/inspect real green CI, perform an actual scheduled/dispatch refresh and review deltas; then build a safe promotion PR mechanism with numeric GitHub-ID reconciliation.

**Baseline limitation:** current daily monitoring compares against the approved pinned snapshot, not the previous workflow run. Add persistent timestamped reviewed state or auto-generated promotion pull requests before calling it a true last-run incremental feed.

## v0.5 approved-snapshot history and draft proposal automation

- Fixed the failing Python application CI by declaring a package build and installing it before pytest; the official Python 3.10 and corpus Python 3.10/3.12 runs are green.
- Added `repoorbit.snapshots` as the sole approved-snapshot pointer reader. Historical snapshots remain in Git, but are no longer indexed as current duplicate records.
- Added `repoorbit.promote` with staged-report consistency checks, immutable versioned snapshots, churn limits, and automatic index regeneration.
- Added a weekly, draft-only GitHub Actions bot PR workflow. It never merges automatically and refuses to supersede a pending proposal.
- Added adversarial offline promotion tests. Future promotion CI is verified independently, but automated PR creation has **not yet been observed** in a scheduled run.
- Current approved counts are machine-readable in `ai/status.json`; fixed numbers in this document describe earlier audit snapshots only.

## v0.6 immutable GitHub identity coverage

- Verified numeric GitHub IDs for all 30 seed repository paths (22 catalogs, 8 projects); checked three inverse ID-only GitHub lookups.
- Implemented identity-sidecar validation, numeric-ID resolution via the existing MCP `resolve` tool and a small `ai/identities.json` machine index.
- Added read-only GitHub identity drift monitoring, distinguishing name changes, ownership transfers, unresolved URLs and ID collisions. Identity changes are **not** automatically merged.
- Added negative tests and CI gates for the numeric registry, remote index and exact MCP lookup.
- Still pending: verified IDs for reference-only paths, meaningful corpus-wide rename cases, actual successful scheduled identity-watch run, persistent reviewed alias promotion, and semantic task quality benchmarking.

## v0.7 verified discovery targets

- Checked 24 real referenced GitHub repos, recording numeric IDs and original catalog provenance without creating new paths or verified-cost claims.
- 30 seed IDs plus 24 checked reference IDs; 1,161 references remain unchecked out of 1,215 unique slugs.
- Read-only GitHub verification worker selects up to 25 unverified links in deterministic batches. Scheduled GitHub Actions checks up to 12 and stages evidence without modifying main.
- Checked-target status is surfaced via exact MCP resolve, token-compact static index, and corpus status; original discovery roles and source hashes remain available.
- Next acceptance gates: observe real live GitHub Actions check; review and promote staged batches without manual JSON handcrafting; introduce stable alias state and paginated progression for all references.

## v0.8 bilingual subject classification and agent-first presentation

- Designed 14 controlled bilingual topical subjects, plus explicit unclassified; 30 seed labels are editorial, 178 discovery slugs have low-trust lexical hints, 1,007 remain unclassified (13 ambiguous, 994 no specific terms).
- Added `categories`, `classify`, and `browse` as bounded, offline AI/MCP entrypoints; generated 16 independently readable JSON shards covering 1,215 known paths exactly once.
- Reworked GitHub README into an agent-first atlas with visible trust definitions and current audit counts.
- Acceptance: official CI on Python 3.10 and 3.12; no model-token or semantic-understanding claims from byte savings.
- Next gate: review upstream README evidence and improve actual topical coverage/precision without asserting untested capabilities.

## v0.9 traceable README topics

- Reviewed original upstream README files for 12 existence-checked catalog references, pinned exact Git blob SHA, source line and a short self-description fingerprint per category.
- Moved only those 12 from unclassified into categories. Corpus remains 1,215 unique GitHub paths, 220 subject-labeled and 995 unclassified (30 editorial, 12 README-backed, 178 lexical).
- Added `readme_topic_evidence` as an explicit trust tier, static shard code `d`, source pointers in `classify`, a deterministic count and anti-tamper tests.
- Added a read-only GitHub Git Blob SHA/line audit: PR checks 3 pinned blobs; weekly checks all 12. Run results must be observed before claiming end-to-end success.
- Next priority: repeat with independently reviewed evidence for more unclassified references, measure held-out topic accuracy, improve multidimensional capability facets.

## v0.10 automated review input and controlled bilingual routing

- Reviewed 11 additional GitHub README source lines (now 23), with immutable blob hashes and identity checks, leaving 984 unclassified of 1,215 indexed paths. This is *documented subject*, not functional or cost validation.
- Added `stage_readmes` to gather tiny, SHA-verified, short upstream source excerpts in read-only batches of up to 5, stored as **unreviewed staging**. It rejects duplicate IDs and obvious prompt injection. No classifier or PR auto-approval follows from that report.
- Added `route_topic` as a bounded EN/ES controlled phrase router with explicit abstention for unsupported/ambiguous phrasing.
- Added 32 reproducible bilingual phrase contract probes, including unknown and ambiguous cases; not a held-out semantic quality metric.
- Next gate: complete live GitHub checks and stage report inspection, then define reviewed promotion PR logic and a genuinely independent multilingual human-labeled benchmark.

## v0.11 rotating evidence coverage and freshness

- Replaced the repeating first-page scheduled checks with deterministic UTC-day rotating windows, bounded at 25 metadata checks and 5 README candidates per day. The review workflow remains read-only and never auto-promotes.
- For a stable queue of 1,161 currently unchecked slugs: 47 identity pages and 233 README review pages. These are theoretical attempted-coverage windows, not confirmed success; actual GitHub API budgets, missed runs and changing inputs remain limitations.
- Built `evidence_age` agent/MCP lookup for checked numeric IDs: actual observed-on date, UTC age, archived-when-checked and separate README self-description source SHA/date. Unchecked links carry no invented last-checked date.
- Added 370-byte `ai/evidence-dates.json` for reproducible historical evidence-date counts, distinct from live repository activity.
- Added synthetic 250,000-slug planner regression; this **does not** represent 250,000 indexed repositories or measured GitHub throughput.
- Next: durable source partitions, re-observation checkpoints, rights-filtered update PR generation and truly independent accuracy evaluation.

## v0.12 global source deltas and owner-sharded AI routing

- Deduplicate new paths across every rights-reviewed source while preserving each source blob SHA, line and membership changes. Source removals do not mean deleted repos. Global differences are staged and independently checked before draft proposals.
- Deterministic `ai/owners/` routing: 622-byte root, 29 owner groups and 35 bounded leaf pages for the 1,215 approved paths. All 54 checked numeric identities stay distinct from unchecked catalog references.
- Bounded `owner_repos` MCP tool and reproducibility checks. The 40,000-slug owner-index stress test is SYNTHETIC, not additional corpus coverage.
- Future bot feed proposals regenerate owner shards, lexical shards and status together before review; no automatic approval or merge.
- Next: add more independently rights-reviewed catalogs, durable discovery checkpoints, numeric alias resolution and held-out EN/ES retrieval benchmarks.
