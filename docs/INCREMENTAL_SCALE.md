# RepoOrbit v0.12 · Global incremental discovery and bounded owner routing

## Evidence boundaries

The approved baseline still contains **1,215 GitHub paths**, **1,199 catalog edges from two individually rights-reviewed CC0 sources**, **54 separately checked numeric IDs** and **23 documentary README subject observations**. This release improves infrastructure; it does **not** add invented repository volume, functional tests or zero-cost certifications.

## Global cross-source delta

The daily `repoorbit.refresh` stages `data/snapshots/staged/global-delta.json` alongside each unchanged source snapshot. All approved source streams are compared together. A case-insensitive owner/repo path linked from two catalogs is **one path** with two source pointers, not two repositories.

| State | Interpretation |
|---|---|
| `new_unverified_paths` | New catalog path; GitHub numeric identity still unknown |
| `new_links_to_known_paths` | A newly linked slug already exists in the checked seed/reference registry |
| `source_membership_changes` | Existing path was added to or removed from individual catalogs |
| `source_evidence_refreshed` | Source blob SHA or cited README line changed while membership remained |
| `removed_from_sources_not_deleted` | Catalogs no longer link it; no deletion conclusion |
| `unchanged_paths` | Same source pointers and IDs in approved and proposed catalogs |

The report preserves original and proposed source IDs, and pinned SHA/line pointers. Path-normalized deduplication is NOT numeric GitHub identity reconciliation: two different names can point to one ID, and a reused name can point to a different ID. Both require later GitHub-ID evidence and review.

The refresh job stays read-only. The draft-only promotion pipeline independently reconstructs the source-global report from candidate snapshots and fails closed if it is missing or forged. It regenerates static owner, term and status indexes in the same reviewed draft PR. No automatic merge.

## Agent-first owner sharding

- `ai/owners/index.json`: 622-byte root with bucket counts.
- `ai/owners/{initial}/index.json`: page boundaries, number of entries and file names.
- `ai/owners/{initial}/{0000}.json`: <=64 repository paths and <=16 KiB per page, with role and previously observed GitHub-existence flag.
- `owner_repos({owner,limit,offset,verified_only})`: bounded local MCP response (at most 20 rows).

At the current 1,215-path baseline: 29 owner buckets, 35 leaves and exactly 54 historical existence-checked paths. Any unchecked reference remains explicitly unchecked. A synthetic stress regression generates 40,000 **fake test names** to check bounded pagination; this is NOT a 40,000-project corpus, GitHub ingestion throughput, or proof of 250,000 real repositories.

## Honest limits

The source refresh still downloads two CC0 files and compares them with approved pinned baselines; it does not yet perform HTTP conditional fetching or persistent cursor updates. Adding more feeds requires individual legal/source review. Link existence does not prove runtime behavior, security, license compatibility, maintenance quality or truly free execution. AI token usage is bounded by small JSON records but cannot be literally zero.

Next scale milestones: authenticated GitHub API budget telemetry, persistent source checkpoints, numeric ID alias review, deeper partition budgets, more license-approved catalogs, and independently labeled multilingual retrieval benchmarks.
