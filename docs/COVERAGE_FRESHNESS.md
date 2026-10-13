# Daily coverage and empirical evidence freshness · RepoOrbit v0.11

RepoOrbit distinguishes **having a link**, **observing a GitHub numeric ID**, **reading an author's description**, **testing software**, and **confirming free operation**. None of these automatically implies any other.

## Fixed the repeated-first-page bug

Before v0.11, scheduled identity checks and README candidate staging always examined the *first* pending links. This generated repeated evidence but failed to systematically extend the breadth of discovery.

A standard-library-only calendar planner now divides the **sorted, unique, approved pending queue** into contiguous, bounded pages and selects one using the UTC day offset from 2026-10-13:

- Daily ID metadata check: at most **25 links**, staging only.
- Daily README review candidate collection: at most **5 links**, staging only; each candidate may involve two official GitHub REST calls.
- Manual and PR runs continue to use a first-page sample unless an explicit date is supplied.
- Every staged report includes the queue size, page size, page index, total pages and next page. No manual shell step is needed by an agent.
- Both workflows have `contents: read` permission. Neither automatically commits or merges newly observed records.

For today's baseline queue of **1,161 unverified links**, a stable queue has **47 identity pages** and **233 README pages**. If all daily runs succeed and the queue remains unchanged, those respective intervals attempt every pending link at least once. This is an **ideal coverage estimate**, not measured successful completion or a promise that every repository resolves. Missing runs, changed queues, rate limits and duplicate/redirect collisions can delay or repeat checks; unresolved cases remain explicitly uncertain.

A synthetic test constructs 250,000 distinct string slugs and validates that a single 25-item page is returned without losing scope information. It does **not** add fake repos to the corpus and is not a benchmark of GitHub throughput.

## Evidence age, not repo health

The new `evidence_age` MCP tool accepts an exact path, GitHub URL or a checked `id:<number>` and returns:

- `identity_status=not_individually_checked`: merely an approved catalog reference, with **no fabricated timestamp**;
- `recent_observation`: last recorded ID metadata observation was at most 30 UTC days ago;
- `aging_observation`: last recorded observation was 31–90 days ago;
- `stale_observation`: last recorded observation was over 90 days ago;
- `future_dated_evidence_invalid`: local query date precedes the pinned source date, never silently treated as fresh.

Checked results include their observed numeric ID, original observation date, current UTC age and observed archived flag. A documentary topic can include its separate README observation date and pinned SHA.

**Stale metadata does not mean dead, unsafe or malfunctioning software.** Conversely, a recent GitHub API response does not mean software works, is maintained, licensed for any particular use, or free end to end.

## Zero-runtime-network AI access

`ai/evidence-dates.json` is a small, deterministic **historical observation histogram**, not a live clock: 54 checked numeric IDs and 23 independently reviewed self-descriptions in the baseline, all observed 2026-10-13. The runtime `evidence_age` tool computes age from the UTC clock without making network requests.

Agents requesting tiny subject/identity results can continue using `ai/categories/index.json`, per-category shards, `ai/identities.json`, `ai/verified-targets.json`, `resolve` and `classify`.

## What remains

The monitoring workflows **stage** newly checked data as short-lived GitHub Actions artifacts; they do not automatically promote it into the approved corpus. Stable priority queues, error retries, historical evidence re-check cadence, proof-backed change proposals, large-scale topic facets and held-out multilingual search-quality measurements remain future work.

Daily monitoring is a bounded bootstrap, not a claim of fast full-GitHub coverage. To scale toward 100,000+ links, use partitioned source manifests, explicit rate budgets, persisted checkpoints, source-diff processing and repeatable retrieval benchmarks before expanding API calls.
