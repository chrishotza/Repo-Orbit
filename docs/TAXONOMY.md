# RepoOrbit classification protocol — v0.10

RepoOrbit uses **14 topical domains in English and Spanish**, plus a fifteenth `unclassified` bucket. The labels are designed by us for **AI navigation**, not borrowed as proof of upstream capabilities.

## Four different evidence states

| Method | Marker | Meaning |
|---|---|---|
| Editorial seed subject | `e` | Human-chosen subject for one of 30 known seeds; not an execution test |
| Reviewed README description | `d` | Category selected from a specific upstream README line and Git blob SHA; not verified functionality |
| Repository-name keyword | `h` | Low-confidence suggestion based on whole words in a repository's *name*, not its owner |
| Ambiguous name | `a` | Equally specific terms indicate different domains; abstain rather than guess |
| Unknown topic | `u` | No matching subject evidence; leave unclassified |

**Audited classification snapshot, 2026-10-13:** 1,215 paths; 30 editorial subjects; 178 lexical hints; 13 ambiguous; 994 without matching words. At v0.10, 23 previously unclassified projects have reviewed README-backed subjects: **231 assigned subjects and 984 unclassified**. The earlier 30 editorial and 178 lexical labels are unchanged. These are *subject assignments*, not 208 working tools.

## Independent dimensions

Category (subject) is separate from `role` (catalog / project / reference), `v` (existence checked / unchecked link), and `format_hint` (known catalog/project or name-derived catalog-like/learning-like/software-like). A repository can be about security and still be only an unverified hyperlink.

Do not infer installations, cost, licenses, safety, production readiness, or model capability from category or archived status. A requested zero-cost filter requires separate evidence; a public GitHub path does not establish free operation.

## Agent contract

| Query | Primary route |
|---|---|
| List topics and exact bucket counts | MCP `categories({})` or `ai/categories/index.json` |
| Explain one repository classification | MCP `classify({"repo":"owner/repo"})` |
| Browse a topic without dumping the corpus | MCP `browse({"category":"ai-ml","limit":5})` |
| Browse without an MCP runtime | Fetch only `ai/categories/ai-ml.json` |
| See exact original catalog evidence | MCP `resolve({"repo":"owner/repo"})` |

`ai/categories/index.json` is **1,188 bytes** at the v0.8 baseline. There are 15 category-specific data shards plus the routing manifest. Each repository appears in one and only one category bucket; `unclassified` is a real bucket, not a hidden failure.

Static shard row: `[repository_slug, role(c/p/r), exists(0/1), basis(e/d/h/a/u)]`. These abbreviations are evidence hints rather than quality rankings. For `verified_only=true`, `browse` checks GitHub-path existence only, never software behavior.

## Review and integrity gates

- Manual editorial seed overrides remain restricted to 30 checked seeds. Other records need reviewed versioned README self-description evidence or must remain a lexical hint or unknown.
- Whole words and phrases only; equally specific competing subjects cause explicit abstention.
- Category pagination and output length are bounded for AI context efficiency.
- Adding source links cannot silently promote their functional, license or cost status.
- All 1,215 known repository paths are represented exactly once across subject shards.
- CI regenerates all 16 derived JSON files and rejects stale or mismatched copies.

**README evidence layer shipped:** 23 checked projects now have short upstream subject descriptions pinned to exact Git blob SHA and line. The separate read-only audit validates those historical blobs; see [README_EVIDENCE.md](README_EVIDENCE.md). Next: held-out English/Spanish topical relevance benchmarks and reviewed evidence for more projects.

## Source-context facet

An agent can request `classify({"repo":"axios/axios"})` and see `category=developer-tools` and an exact reviewed README pointer while keeping its Awesome Node.js catalog origin. This is an **evidenced catalog membership**, not proof of Node.js compatibility or technical function. To combine provenance with subjects, use `browse({"category":"unclassified","source":"github:sindresorhus/awesome-nodejs","limit":5})`. Only source IDs in the current rights-reviewed feed registry are accepted.

## v0.10 language entry and untrusted review staging

`route_topic({"q":"quiero animación"})` maps known EN/ES topic phrases to a controlled subject ID. It abstains if nothing matches or equally specific phrases point to multiple subjects. Its 32 curated probes are **alias contract regressions**, not held-out semantic accuracy. Read [TOPIC_ROUTING_EVAL.md](TOPIC_ROUTING_EVAL.md). The new `stage-readmes.yml` uses read-only GitHub metadata and README API endpoints to stage at most five compact excerpts at a time. The excerpts are untrusted suggestions with blob hashes; no automatic category, execution or cost labels. See [REVIEW_PIPELINE.md](REVIEW_PIPELINE.md).
