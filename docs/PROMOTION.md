# RepoOrbit: reviewable feed promotion

**Agent-oriented operation.** Human shell commands are not the product interface. Automated GitHub Actions are maintenance infrastructure; assistants use `agent.json`, MCP tools, and compact JSON indexes.

## Two independent automations

**Daily, read-only:** `.github/workflows/refresh-feeds.yml` checks the current license and Git blob SHA for two explicitly approved CC0 catalogs. It writes a staging artifact. It cannot commit anything to `main`.

**Weekly or explicitly dispatched, draft PR only:** `.github/workflows/propose-feeds.yml` first checks whether a prior bot PR is awaiting review, re-fetches the allowlisted sources, validates staging, runs conservative promotion, regenerates machine indexes, tests everything, and proposes a **draft pull request** only when repository URLs were added or removed.

The PR bot cannot merge automatically. A repository administrator may need to enable Actions to create pull requests; if disabled, the run will report the permission error rather than silently changing `main`. PRs created with the default `GITHUB_TOKEN` may not trigger other workflows automatically, so the promotion job executes its own tests on the proposed content before pushing.

## Canonical source of truth

- `data/feeds.json`: the exact approved snapshot **per licensed source**, not the last GitHub fetch.
- `data/discoveries/*.jsonl`: immutable, committed source observations, including older snapshots. An older snapshot remains available for reproducibility but is **not** counted again by current search.
- `repoorbit.snapshots.approved_discoveries()`: the only snapshot paths consumed by `repoorbit.agent` and `repoorbit.build_status`.
- `ai/status.json`: compact current approved-snapshot counts, generated from tracked data.
- `ai/terms/[a-z].json`: deterministic current search indexes, generated after approval; never merged manually.

Approved history is preserved in Git; a new PR creates a new date-and-blob-named snapshot and atomically updates the active pointer. This prevents historical snapshots from silently inflating coverage.

## Rejection rules

A proposed update fails closed if:

- an upstream license is no longer the reviewed CC0 text, a Git blob digest differs, or an upstream API request fails;
- a source, staged path, blob digest, identity, observation date, line locator or license has unexpected structure;
- a snapshot becomes empty, contains duplicate canonical IDs, lacks deterministic ordering, or the reported delta does not match an independent baseline comparison;
- there are more than **200 new** links, more than **50 removed**, or removals exceed approximately **15%** of the pinned source's baseline (with a minimum five-link allowance);
- a bot PR is already pending review;
- machine index regeneration or the Python test suite fails.

These limits govern **automatic proposals**, not which projects are allowed into RepoOrbit. Larger legitimate source changes need separate inspection before their baselines are updated.

## What is and isn't verified

The ingestion process verifies a source's reuse license and retrieved file integrity, and preserves exact GitHub link references. It does **not** verify that every linked repository exists, has a permissive software license, works, is safe, or can run for free. `not_checked` must remain visible to agents.

The weekly workflow has been installed, but a successful automated *draft PR creation* must be observed separately from ordinary unit-test/CI success. No merge, hosted API, GitHub-wide coverage or functionality audit is implied.
