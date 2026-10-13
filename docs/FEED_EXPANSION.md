# RepoOrbit v0.13 · Four additional CC0 discovery feeds

**Observed 2026-10-13.** This is a source-rights and discovery-link audit, not a review of linked software capabilities.

## Rights review and immutable source evidence

We checked the official GitHub repository metadata for each added source and independently examined the source's `license` file. All four returned SPDX `CC0-1.0` and license text identifying **CC0 1.0 Universal**. We then read the original `readme.md` and extracted links with RepoOrbit's pre-existing, deterministic GitHub URL parser.

| Source repository | GitHub numeric ID | Pinned README blob SHA | Unique GitHub links |
|---|---:|---|---:|
| [sindresorhus/awesome-npm](https://github.com/sindresorhus/awesome-npm) | 49596056 | `497964a13119c80967ba63cc674f0b797606e7e3` | 64 |
| [sindresorhus/awesome-electron](https://github.com/sindresorhus/awesome-electron) | 34453060 | `a16961f2067a5950570ea8ca2b0ed48ce4029c65` | 145 |
| [sindresorhus/awesome-observables](https://github.com/sindresorhus/awesome-observables) | 57965762 | `b1ecef932b4a73f7f9c44a5d5dc0ab32a5847375` | 13 |
| [sindresorhus/awesome-tap](https://github.com/sindresorhus/awesome-tap) | 48281676 | `5d5ba058b8994af81288aa509be3fc0024add0e0` | 42 |

The observed LICENSE Git blob SHA for each source was `0e259d42c996742e9e3cba14c677129b2c1b6311`. Source license evidence allows catalog link metadata reuse for the reviewed directories; it **does not authorize us to copy code from linked projects or claim those projects share CC0**.

## Numerically reconciled coverage

- Prior approved corpus: **1,215 unique GitHub paths**, **1,199 source edges** from two rights-reviewed directories, **54 previously checked numeric GitHub IDs**.
- New source data: **264 additional GitHub link edges**. Among the added links, **247 canonical paths did not appear in the prior corpus**.
- New approved corpus: **1,462 unique owner/repo paths**, **1,463 source edges** across six reviewed directories, with **19 paths represented in more than one source directory**.
- Four new observed catalog GitHub IDs extend the 30 known seed IDs to **34**, for **58 independently ID-checked repositories** total. The other **1,404 paths are unverified source references**, not known-good software.
- Classification: **309 subject labels** (34 bounded editorials, 23 pinned original README self-descriptions, 252 lexical name hints), and **1,153 explicitly unclassified**. No newly inferred functionality, security certification, license compatibility or completely free execution.

Every catalog edge records the source ID, immutable upstream Git blob SHA, README line number, original URL, date and `target_verification=not_checked`. A normalized duplicate retains both original pointers instead of being counted as two projects. The original READMEs were **not mirrored** into this repository.

## Machine-first access and regeneration

The default entry is `agent.json`; offline clients can request `categories`, `owner_repos`, `search`, `resolve`, or `evidence_age` without loading the entire corpus or calling an LLM. Static readers can inspect `ai/owners/index.json` and one 64-record page or `ai/categories/index.json` and one topical shard. The approved source allowlist and immutable snapshot identities live in `data/feeds.json`.

Corpus acceptance requires deterministic validation of the six source snapshots, source-global deduplication, 34 seed numeric IDs, 24 separately checked references, 26 term shards, 15 topical files, owner navigation pages, machine status, and historical observation dates. A failed source or tampered blob prevents trust promotion.

**Limit:** additions are GitHub *link references*. Future runs of the read-only GitHub checkers must independently verify any referenced repository's numeric ID. No listed repository is newly certified as working or free from the directory membership alone.
