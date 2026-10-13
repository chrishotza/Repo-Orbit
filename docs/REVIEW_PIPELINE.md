# README review pipeline: untrusted evidence, never instructions

RepoOrbit does not bulk-copy repositories or take behavioral instructions from their READMEs. The collector is a **read-only review queue** for approved-source links with no prior verified GitHub ID. It does not decide topics, costs, security or whether a project works.

## Source and method

The `repoorbit.stage_readmes` module draws from the same approved CC0 discovery links as `check_targets.pending()`. It excludes all 30 checked seeds and 24 approved checked references at this stage. Its GitHub API calls are strictly bounded:

1. GET repository metadata to obtain the GitHub numeric ID and canonical slug; resolve 404 as unknown, never deletion.
2. GET the repository README through the official REST endpoint; validate the reported Git blob digest by hashing the actual bytes.
3. Inspect no more than 150 lines, without mirroring the full README. Skip fenced code, HTML comments, obvious assistant-targeted commands, sponsor blocks and excessive markup. Produce at most three short candidate strings of 170 characters each with line numbers, SHA and exact approved source-catalog IDs.
4. Write only to ignored `data/snapshots/readme_review/report.json`, tagged `unreviewed_staging_only`.

A batch contains at most five targets. Duplicate slugs, repeated numeric GitHub IDs, identity collisions, oversized responses, unsafe paths, Git SHA mismatches and API errors fail closed. A missing README is unresolved rather than silently accepted.

**Important:** the prompt-injection word filter is a precaution, not a security boundary. External text remains untrusted even when it passes the filter. An agent must never execute or obey any command embedded in a README. No line from this staging process is ever automatically promoted to `data/topic_evidence.jsonl`.

## Workflow contract

`.github/workflows/stage-readmes.yml` has `contents: read` permission, executes a two-target sample on PRs and at most five candidates on its weekly schedule, and uploads an artifact for inspection. It cannot push commits or merge pull requests.

The deterministic pending queue supports an `after` cursor, but currently no persisted weekly cursor or automatic reviewed promotion exists. Repeated scheduled runs can revisit the same targets; a later iteration must persist state safely before claiming continuous coverage.

The source README may contain adversarial LLM instructions. One previously reviewed repository is deliberately **not** promoted as a documentary topic in this batch because it contains such text. This is a decision about trusting evidence, not about suppressing links from the raw index.

## Promotion gate

Future promotion requires independent review of the candidate's original README, the exact Git SHA and source line; rights checks, stable numeric ID resolution, a reviewed controlled topic, tests, regenerated deterministic indices and a normal reviewed PR. Repository existence, topical self-description, functionality, security and cost are **separate dimensions**.

The read-only collector's actual operation must be confirmed from a completed Actions artifact before describing it as live-validated.
