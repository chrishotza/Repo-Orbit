# RepoOrbit AI protocol v0.2

## What to read, in order

1. **AGENTS.md** (short instructions, no corpus).
2. **agent.json** (machine contract and entrypoints).
3. Invoke the four MCP tools as needed. Only request additional evidence for a specific result.
4. If no executable tools exist, fetch **ai/index.json** and the *one* matching \`ai/terms/{letter}.json\` static shard. Do not read the discovery JSONL snapshots just to search by a word.

No step assumes a chat assistant can read a local terminal. An MCP host handles process startup. A web-only AI can navigate the static JSON files without human commands or authentication.

## MCP stdio

MCP protocol version: \`2025-06-18\`. Standard JSON-RPC 2.0 over newline-delimited stdio messages. Python 3.10+ standard library only. The server does **not** call GitHub or any external service during queries.

Available tools:

- `recommend(q, limit=5, strict_free=false)`: bilingual (EN/ES) curated task matching with upstream README fingerprints. This is **not** independently executed or priced. Setting `strict_free=true` returns no projects until genuine free-execution evidence is available.

- \`search(q, limit=5, offset=0, role=null)\`: deterministic lexical search (max 20 records/request), stable ordering. \`n\` is the number of in-corpus matches; \`more\` signals pagination.
- \`resolve(repo)\`: exact lookup by \`owner/repo\` or \`https://github.com/owner/repo\`. Returns any recorded upstream source pointers and checked/unchecked status.
- \`stats()\`: compact internal inventory only.

Example compact tool result for \`search("mcp", 1)\` (illustrative shape, not a claim about a specific result):

\`\`\`json
{"q":"mcp","n":2,"offset":0,"items":[{"r":"owner/repo","role":"reference","v":"not_checked"}],"more":true,"semantics":"lexical_not_functionally_verified"}
\`\`\`

This example illustrates fields only. An actual tool call returns actual record names and actual in-corpus match counts.

### Trust semantics

- \`r\`: an owner/repository slug, not a claim that the software is functional.
- \`role\`: \`catalog\` = discovery source; \`project\` = individually checked seed; \`reference\` = external catalog URL found in a document.
- \`v: exists\`: GitHub path was checked on the recorded seed date. Not a present-day availability guarantee.
- \`v: not_checked\`: the link was extracted but has **not** been checked against GitHub.
- \`cost: unknown\`: not independently verified free.
- \`working: not_run\`: no reproducible installation or execution test.
- \`source\`: \`s\` source ID, \`line\` upstream line and \`sha\` upstream file blob; kept so agents can cite/verify the precise discovery location.

Queries are simple lexical ranking on repository slugs and verified seed topic labels. The search is **not** semantic, retrieval augmented generation, a guaranteed capability match, a license audit, or a full GitHub index. For user queries whose intent is missing from names/tags, return the limitation instead of fabricating relevance.

### Compact response design

- Default five hits; caller controls the cap up to 20.
- No README bodies, commit histories, license text or dependency trees are sent to the agent.
- The local index is loaded once per process and cached. Reusing an MCP session avoids reparsing data.
- No paid LLM or embedding endpoint is required.
- Actual token count depends on the receiving model's tokenizer, host serialization, and selected results. **Zero tokens are impossible when an LLM has to read a response.** Reducing payload bytes is the measurable objective.

## Bilingual intent route (v0.3)

Read `ai/intent.json` only if the agent host cannot call MCP. This compact static manifest holds 8 reviewed task IDs, English/Spanish aliases and canonical candidate slugs. Alias matching normalizes accents, lowercases, and matches whole phrases (not arbitrary substrings). The evidence registry `data/intent_map.json` links each candidate to an upstream README, its checked blob SHA, the observation date and a short original summary. `ev=readme@<prefix>` in tool results is a short fingerprint, not proof of execution.

**Failure behavior matters**: if no explicit alias matches, `recommend` returns zero candidates; it does not pretend to know every possible task. If a query asks for free usage, it returns relevant documented candidates with `cost=unknown` and a warning. In strict mode it returns none. Neither mode claims licensing approval or reproducible results.

For a query such as `Quiero generar videos con IA gratis`, the task router identifies `generate-video` and may suggest `Comfy-Org/ComfyUI` with `cost_not_verified` (not a guarantee that a requested video generation setup will run at zero cost). A model should still ask for specifics only when the task cannot be met using the documented limitations.

## Static indexed discovery without local execution

If an agent cannot launch MCP but can fetch files, read \`ai/index.json\` first.

Choose \`ai/terms/{first_letter}.json\` for each significant lowercase ASCII word in the query. For example \`mcp\` maps to \`ai/terms/m.json\`. Each file is self-contained:

\`\`\`json
{"v":1,"r":[["owner/repo","u",0]],"t":{"example":[0]}}
\`\`\`

The example is a shape demonstration, not real corpus data.

\`r\` is a local, zero-based row table: \`[repository_slug, role, verification]\`; roles \`c\`/ \`p\`/ \`u\` mean catalog / project / unverified reference; verification \`1\` means path existence checked when seeded, \`0\` means unchecked link. The map \`t\` contains lowercased lexical terms to integer offsets into \`r\`. For multiword queries, intersect **repository slugs**, not per-shard numeric offsets (offsets are local). Stopwords are documented in \`ai/index.json\`. Numeric-leading words, paraphrases, and semantic associations require the MCP route.

### Source and update policy

Intent aliases are deterministically built into `ai/intent.json` from the reviewed task registry; a separate CI check detects stale manifests. Index shards are deterministically built from \`data/sources.json\`, \`data/repositories.jsonl\`, and \`data/discoveries/*.jsonl\`. The CI suite rejects stale shard contents after corpus changes. The source lists remain the authoritative evidence; static indexes are derived and may be rebuilt, never hand-edited.

## Performance measurement plan

For each representative test query, record the complete incoming + outgoing MCP payload size in bytes and, where available, model-token count. Compare against a baseline that injects the full 672-reference JSONL. Benchmark single-hit, 5-hit, 20-hit, multiword, missing-result and typo cases separately. Report model, tokenizer, date, cache state and corpus version. Never generalize a one-query byte saving to all tokenizers or queries.

## First measured payload comparison (2026-10-12 corpus snapshot)

These are **UTF-8 file sizes**, not model token counts or end-to-end network measurements:

| Fetched data | Bytes | Reduction versus full discovery snapshot |
|---|---:|---:|
| Entire 672-link discovery JSONL | 299,786 | baseline |
| One static index shard for letter \`v\` | 1,758 | 99.41% fewer bytes |
| One static index shard for letter \`m\` | 5,868 | 98.04% fewer bytes |

The one-time orientation files \`AGENTS.md\` and \`agent.json\` together are 2,348 bytes, and the static routing manifest \`ai/index.json\` is another 1,300 bytes. A model with a cached agent contract does not have to reread them for every query. Results and metadata checks are still necessary; smaller transfer size is not proof of search relevance, execution, or lower cost for every LLM host.

Verification performed: all 26 published static shards were checked against a fresh deterministic regeneration of their seed/source/discovery inputs with zero mismatches. The MCP and Python test suite is included in CI; this measurement alone is **not** an assertion that a remote CI run succeeded.

## Future evolution

Semantic aliases, curated capability evidence and incremental catalog ingestion can be added as **additional evidence-bearing layers**, never silently to the lexical field. Any hosted HTTP/MCP endpoint would require deployment and security review; **no hosted endpoint is claimed in v0.2**.

## Multi-source index growth

The search corpus now contains 1,215 unique GitHub slugs drawn from 1,199 discovery edges plus 30 individually checked catalog/project seeds. The 26 lexical shards were rebuilt from both CC0 snapshots. A separate rights-gated scheduled workflow stages upstream changes but does not publish unreviewed data to search or silently mark references as functional software. The 299,786-byte comparison above is **historical measurement of the first 672-link snapshot**, not the combined two-source corpus size.

## Stable ID exact resolution (v0.6)

The existing `resolve` MCP tool also accepts `id:<positive_integer>`, such as `id:589831718` for the individually checked ComfyUI seed. The result preserves the seed record and separately adds the numeric ID and identity observation date. This is a metadata verification, **not** a working-software, cost, or security test. A remote-only agent can look up any of 30 verified seed IDs in the 1.4 KB `ai/identities.json` table. All unchecked references still lack numeric identity verification. Renames/transfers are recognized **only** after the same numeric ID is re-observed by GitHub; slug reuse under a different ID fails closed. See [IDENTITIES.md](IDENTITIES.md).

## v0.7 checked catalog references

The separate `ai/verified-targets.json` file contains 24 checked discovery references and is deliberately distinct from 30 seed ID entries in `ai/identities.json`. `resolve({"repo":"id:23088740"})` retrieves a previously unchecked catalog reference that now has independent GitHub-ID evidence; it keeps its `role=reference` and its original source pointers. `v=exists` means existence metadata only, not an executable or free result. The 26 lexical shards contain updated existence flags with no increase in repository count. See [TARGET_VERIFICATION.md](TARGET_VERIFICATION.md).

## v0.12 owner-route precision and global source deduplication

`owner_repos({"owner":"sindresorhus","limit":5})` lists only approved paths for that owner, not everything live on GitHub. Remote-only clients use `ai/owners/index.json` (622 bytes), then `ai/owners/{initial}/index.json` and select a bounded page by first/last slug ranges. Current corpus: 29 buckets, 35 pages, each <=64 paths and <=16 KiB. Cross-feed duplicates retain each source/hash/line in a staged global delta. See [INCREMENTAL_SCALE.md](INCREMENTAL_SCALE.md).
