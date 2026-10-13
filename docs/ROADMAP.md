# RepoOrbit implementation roadmap

Goal: **the simplest trustworthy interface for discovering useful repositories**.

| Stage | Deliverable | Acceptance criteria |
|---|---|---|
| 0. Corpus foundation | Verified discovery roots, project seeds, schemas, provenance policy, CLI and offline tests | Seeds linked to canonical URLs; dedup and validation; unknown costs remain unknown |
| 1. Reliable metadata | Incremental GitHub API ingestion with rate-aware retry, caching, rename detection and snapshots | Deterministic, resumable sync; no lost provenance; age and error metrics reported |
| 2. Catalog adapters | Explicitly permitted adapters for selected discovery directories | Per-source license/terms review, attribution, URL-level references, parser tests, extraction counts |
| 3. Search | Keyword search, taxonomy and human-reviewed evaluation set | Search works without an account, measurable query success; transparent filters |
| 4. Verification | Independent checks of installation requirements, free tiers and reproducible examples | Every strong claim points to dated evidence; errors and unknowns shown |
| 5. Accessible website | One natural-language search field and clear result comparisons | Keyboard and screen-reader accessible; visible source, date, license and cost uncertainty |
| 6. Sustainable scale | Contributor workflows, scheduled checks, quality dashboards | Monitored freshness and coverage with no misleading total-GitHub claims |

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
