# RepoOrbit corpus specification (v0.1)

## Purpose and scope

The corpus is an **auditable reference and evidence graph**, not an indiscriminate dump of GitHub. The initial version distinguishes **discovery sources** (catalogs, indexes and collections) from **project records**. A source repository existing does not mean we have parsed its contents. A project existing does not mean its tool works.

**Current seed inventory:** 22 independently confirmed source repositories and 8 independently confirmed project repositories, all checked on 2026-10-12. These are small starting references, not coverage estimates or an exhaustive sample. The initial source registry has catalog ingestion disabled until adapters, rights checks, and tests exist.

## Ontology

| Object | Identity | Meaning |
|---|---|---|
| DiscoverySource | \`github:owner/repo\` | Repository that references or collects further material |
| Project | \`github:owner/repo\` | Individual project discoverable by purpose |
| DiscoveryEdge (planned) | source + target + evidence hash | Where a particular project reference was seen |
| MetadataSnapshot | project + fetch timestamp | A particular GitHub API observation |
| Evidence (planned) | claim + method + source + time | Reviewable support for a statement |
| Capability (planned) | project + capability + evidence | What a user can reasonably do with the project |
| CostDimension (planned) | project + environment + condition | Licensing, APIs, compute, storage and hosting costs separately |

**Do not merge source repos into projects** merely because both are GitHub repositories. These are different roles and may later overlap in the knowledge graph without losing those roles.

### Stable identity

- v0.1 IDs are \`github:\` followed by the case-folded full path.
- v0.1 deduplication uses this ID within each registry; duplicates cause validation failure.
- Names are not globally permanent: GitHub allows repository renames and transfers.
- Future ingestion must prefer GitHub's numeric repository ID once fetched, maintain an alias table for old slugs, and avoid treating rename redirects as new projects.
- Do not collapse forks, unrelated namesakes, or mirrors automatically: represent their relationship instead.

## Evidence levels

**Repository existence**: the GitHub repository endpoint resolved for that path on the verification date.

**Metadata observed**: an API response returned a dated value, e.g., stars, archive flag, last update, language, or detected license.

**Documentation claim**: a feature or pricing condition is asserted by upstream documentation; not independently tested.

**Functional test**: an installation or execution test has a captured command, environment, version, timestamp and reproducible result.

**Cost verified**: conditions, environment, and date establish what is actually free. The cost can differ by hardware or workload.

The v0.1 corpus includes only *repository existence* and optional *metadata observations*. It has no functional test evidence. In particular, **stars are not a quality score, a license identifier is not legal analysis, and public visibility is not proof of free use**.

## Data stores

- \`data/sources.json\`: source registry with GitHub URL, topics, scope, verification and conservative reuse policy.
- \`data/repositories.jsonl\`: immutable, hand-checked project seed references with dates and unknowns preserved.
- \`data/snapshots/latest.jsonl\`: generated point-in-time enrichment from the GitHub API. Intentionally gitignored until a publishing strategy exists.
- \`schemas/\`: machine-readable JSON Schema contracts for one source or one project.
- \`scripts/corpus.py\`: no-dependency CLI. Offline validation and stats are independent of any API credentials.

The JSON Schemas are **declarative contracts**. The bundled zero-dependency validator manually enforces core identity, type, provenance, uniqueness and safety rules; it is not a full JSON Schema interpreter. Full schema enforcement is a later CI milestone.

## Pipeline

\`\`\`text
Verify source repository exists
  -> register discovery source with verified date and permitted reuse mode
  -> (future) check license/terms and select supported parser
  -> (future) extract URL references with source locator, without mirroring content
  -> normalize GitHub repository URL and resolve canonical GitHub identity
  -> deduplicate by numeric GitHub ID while preserving discovery edges
  -> fetch API metadata respecting rate limits and backoff
  -> (future) collect reproducible evidence for feature/cost claims
  -> (future) index searchable record and expose understandable filters
\`\`\`

### Technical invariants

1. Sources and projects are distinct seed roles. Current seed sets must be disjoint.
2. Every seed has a canonical URL, normalized ID, verification date and explicit provenance.
3. Never replace unknown values with positive claims. \`null\` and \`unknown\` are valid and expected.
4. Sync must preserve cost and functionality uncertainty, fail on errors and never overwrite seed inputs.
5. Generated files sort records by canonical ID and write atomically.
6. Never store access tokens, personal data dumps, or mirrored upstream source files in the corpus.
7. Include timestamp and origin for new evidence. Historical observations should not be silently rewritten.
8. Partial catalog parsing must be reported as partial, not complete coverage.

## Offline commands

\`\`\`bash
python3 scripts/corpus.py validate
python3 scripts/corpus.py stats
python3 scripts/corpus.py sync --dry-run --limit 8
python3 -m unittest discover -s tests -v
\`\`\`

## Online metadata refresh

\`\`\`bash
export GITHUB_TOKEN="your_token_here"   # optional; never commit it
python3 scripts/corpus.py sync --limit 0 --delay 1
\`\`\`

The \`sync\` command fetches only the **8 project seed repositories**. \`--limit 0\` means all seeds, not all GitHub repositories. The API enriches GitHub ID, stars, archived status, primary language, repository update timestamp, and recognized SPDX license when available.

Do not interpret \`updated_at\` as evidence that source code or releases were recently updated. Do not interpret a detected SPDX identifier as a dependency license audit.

## Meaningful quality and coverage measures (planned)

- **Coverage:** unique canonical GitHub projects with a reported query/corpus denominator; never pretend to know the entire population.
- **Recency:** p50/p95 metadata age and ingestion lag (UTC).
- **Traceability:** proportion of records with durable discovery edges and timestamped sources.
- **Duplication:** collisions detected before and after canonical ID reconciliation.
- **Validity:** fraction of records passing schema and invariant tests.
- **Usefulness:** search precision and task success evaluated on a held-out, human-reviewed set of natural-language requests.
- **Cost accuracy:** sampled verified cost claims segmented by API, hardware, hosting and license.
- **Safety/security:** no inference of safety based on stars; security findings require separate checks.

For each measurement define a denominator, sampling method, benchmark date and uncertainty interval before advertising a result.

## Explicit non-goals for v0.1

Not a complete scrape of GitHub, a semantic search engine, a hosted UI, an automated software installer, a security auditor, a guarantee of free execution, or an upstream-license compliance certification.

## First provenanced discovery snapshot (2026-10-12)

- Dataset: `data/discoveries/awesome-2026-10-12.jsonl`
- Origin: https://github.com/sindresorhus/awesome (`readme.md`)
- Origin content blob SHA: `0acaa99d5f45582ecf70f987213f59ae1855226f`
- Origin license: `CC0-1.0`, confirmed from upstream `license` file
- Extraction: `github_link_regex_v0.1`; canonical owner/repo matching, known GitHub navigation paths excluded, case-insensitive duplicate URLs merged.
- Output: **672 unique GitHub-path references**. All explicitly marked `target_verification: not_checked`.
- Semantics: a URL referenced in a source on that date; **not** proof the target repository exists today, and not proof of executability, license or cost.
- Reproducibility: `python3 scripts/discoveries.py validate`; to repeat extraction provide an independently retrieved upstream README, its blob SHA, review its license, and run `python3 scripts/discoveries.py extract --input path/to/readme.md --source-repo sindresorhus/awesome --source-sha <40-hex-blob> --source-license CC0-1.0 --date 2026-10-12 --output path/to/output.jsonl`.
- Registry flag `catalog_ingestion_enabled: false` still means **no scheduled upstream crawling is enabled**. This is a one-time provenance-preserving snapshot.

The discovery snapshot is not counted in the verified project inventory and must not be used as an exhaustive repository count.
