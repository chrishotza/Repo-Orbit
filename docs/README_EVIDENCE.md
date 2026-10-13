# RepoOrbit v0.9: README-backed subject evidence

The subject system now has **four distinct provenance tiers**: editorial seed subjects (`e`), **12 manually reviewed upstream README topics (`d`)**, filename-only lexical guesses (`h`), and abstentions (`a` or `u`). Every verified subject remains only a topical statement, **not** a software execution or pricing check.

## Reviewed corpus evidence, 2026-10-13

| Repo | Documentary subject | README line |
|---|---|---|
| [Mongoose](https://github.com/Automattic/mongoose) | data-storage | 3 |
| [Actionhero](https://github.com/actionhero/actionhero) | web-apps | 37 |
| [Acorn](https://github.com/acornjs/acorn) | developer-tools | 7 |
| [ApostropheCMS](https://github.com/apostrophecms/apostrophe) | web-apps | 34 |
| [Agenda](https://github.com/agenda/agenda) | automation | 8 |
| [Axios](https://github.com/axios/axios) | developer-tools | 472 |
| [Babel](https://github.com/babel/babel) | developer-tools | 8 |
| [AVA](https://github.com/avajs/ava) | developer-tools | 7 |
| [Bee-Queue](https://github.com/bee-queue/bee-queue) | automation | 5 |
| [Ajv](https://github.com/ajv-validator/ajv) | developer-tools | 5 |
| [Nano ID](https://github.com/ai/nanoid) | developer-tools | 8 |
| [Amplication](https://github.com/amplication/amplication) | cloud-devops | 11 |

Each entry in [`data/topic_evidence.jsonl`](../data/topic_evidence.jsonl) binds a **checked numeric GitHub ID**, source repository path, manually selected controlled topic, exact source-file path, immutable 40-character **Git blob SHA**, line number, short source-line text fingerprint, observation date and a short original description. The record explicitly states `execution_test=not_run` and `cost=unknown`. We do **not** bulk mirror third-party READMEs or overwrite independent project licensing.

## Query protocol for agents

- `classify({"repo":"axios/axios"})` now yields `category=developer-tools`, `basis=readme_topic_evidence`, and `readme_evidence` with a historical blob URL, blob SHA, exact line, current branch README link, date and short explanation.
- `browse({"category":"automation","limit":5})` returns bounded records whose `basis` can be `readme_topic_evidence`; callers can `classify` one result to fetch full evidence on demand.
- Remote-only agents may read `ai/categories/index.json` and one category shard. Static method code `d` means README evidence. The source registry is separate from the tiny read indexes.

The combined corpus still contains **1,215 unique paths**. Exactly **220 have subject assignments**: 30 editorial, 12 README-backed and 178 filename suggestions. The other **995 remain unclassified**; these are not claimed to be unsuitable projects.

## Audit method

`repoorbit.audit_topics` reads only the recorded original Git blob, through the documented GitHub REST endpoint `/repos/{owner}/{repo}/git/blobs/{sha}`. It checks the API SHA, independently recomputes the Git blob digest, enforces size limits, decodes UTF-8 and verifies that the short anchor appears on the recorded exact line. No branch-head README is assumed to be immutable; the current-branch link is for convenience, while the Git blob SHA establishes the pinned evidence.

A read-only GitHub Actions job verifies three blobs on PRs and **all 12** on its weekly schedule. Reports are archived as artifacts, not silently committed or promoted. The test suite independently rejects hash and line mismatches. An actual successful workflow run is the gate for claiming that external verification worked end to end.

## Boundaries and next step

A GitHub README is an author's own description, not proof of performance, model capability, no-cost operation, software safety or license approval. We also have not measured classifier recall or precision on held-out real tasks. Next: expand evidence review to more unchecked-topic repos and benchmark topical search in English and Spanish, tracking disagreements and false classifications instead of optimizing only coverage.
