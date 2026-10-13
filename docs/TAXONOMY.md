# RepoOrbit classification protocol — v0.8

RepoOrbit uses **14 topical domains in English and Spanish**, plus a fifteenth `unclassified` bucket. The labels are designed by us for **AI navigation**, not borrowed as proof of upstream capabilities.

## Four different evidence states

| Method | Marker | Meaning |
|---|---|---|
| Editorial seed subject | `e` | Human-chosen subject for one of 30 known seed repositories; not a working-software test |
| Repository-name keyword | `h` | Low-confidence suggestion based on whole words in a repository's *name*, not its owner |
| Ambiguous name | `a` | Equally specific terms indicate different domains; abstain rather than guess |
| Unknown topic | `u` | No matching subject evidence; leave unclassified |

**Audited classification snapshot, 2026-10-13:** 1,215 paths; 30 editorial subjects; 178 lexical hints; 13 ambiguous; 994 without matching words. Thus **208 assigned subjects and 1,007 unclassified**. These are *subject assignments*, not 208 working tools.

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

Static shard row: `[repository_slug, role(c/p/r), exists(0/1), basis(e/h/a/u)]`. These abbreviations are evidence hints rather than quality rankings. For `verified_only=true`, `browse` checks GitHub-path existence only, never software behavior.

## Review and integrity gates

- Manual seed overrides are restricted to the 30 checked catalog/project seeds. Every other record must be a lexical hint or unknown.
- Whole words and phrases only; equally specific competing subjects cause explicit abstention.
- Category pagination and output length are bounded for AI context efficiency.
- Adding source links cannot silently promote their functional, license or cost status.
- All 1,215 known repository paths are represented exactly once across subject shards.
- CI regenerates all 16 derived JSON files and rejects stale or mismatched copies.

**Next evidence layer:** independent README-based claims with exact source blob SHA, observation date, reviewer notes, and held-out Spanish/English relevance benchmarks. Keep that evidence independent from lexical guesses.
