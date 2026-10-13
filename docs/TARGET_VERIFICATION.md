# Checked discovery references — RepoOrbit v0.7

On 2026-10-13, RepoOrbit individually checked **24 GitHub catalog references** through the official GitHub repository metadata API, obtaining stable numeric repository IDs, canonical slugs, default branches and archive flags.

Of 1,215 known repository slugs, **30 are checked seeds**, **24 are separately checked discovery references**, and **1,161 remain unchecked reference-only paths**. These 54 ID observations do not prove functioning, cost, safety or licensing.

The checked evidence is stored in \`data/verified_targets.jsonl\`, distinct from immutable original source-link snapshots. One checked project (\`bestiejs/benchmark.js\`) is archived. The original \`0pandadev/awesome-windows\` link points to official casing \`0PandaDEV/awesome-windows\`; both spellings have the same numeric ID and are **not counted twice**.

## Machine-first access

Agents use \`resolve({"repo":"id:23088740"})\` for the checked Axios reference, receiving its numeric ID and **original catalog provenance**. \`search\` remains bounded and lexical. \`ai/verified-targets.json\` is a compact [ID, original slug, official slug if different, archived flag] index. \`ai/status.json\` supplies the current verified/unchecked counts without reading all discovery edges. Regenerated \`ai/terms/[a-z].json\` shards mark independently existence-checked references as verified, while keeping their role as catalog references.

## Continued verification without arbitrary manual commands

\`repoorbit.check_targets\` selects a deterministic, sorted queue from approved catalog references, excluding previously checked seeds and targets. Its \`--after\` cursor supports non-overlapping batches. Each network run handles at most **25** GitHub repository endpoints and writes only under ignored staging paths. API errors and rate limiting fail closed; HTTP 404 is **unresolved**, never a confirmed deletion. Duplicate IDs or collisions with known identities block automatic approval.

The read-only \`.github/workflows/check-targets.yml\` workflow queries 3 pending references during a PR, or up to 25 on each daily/explicit run, uploading evidence as an artifact **without changing main**. Subsequent promotion requires review, new registered observations, regenerated indexes and green CI. Weekly checks may overlap until someone approves a batch and advances the queue or cursor.

## Verification boundaries

Repository existence does not establish working installation, license compliance, zero-cost use, maintainership quality, or security. A public/archived flag is merely observed metadata. The batch workflow itself requires a **real completed live run** before being described as end-to-end validated. Token efficiency means bounded data transfer, not zero-token LLM operation.

## v0.11 calendar rotation

The daily checker now uses `--cycle-date` with a UTC date to select an incrementing page of 25 pending slugs; no repeated first-page-only checks. Each artifact records queue length and page index. [Coverage and empirical freshness methodology](COVERAGE_FRESHNESS.md). The 47-page sweep for the current pending queue is a theoretical number of attempts and assumes a stable queue and successful runs.
