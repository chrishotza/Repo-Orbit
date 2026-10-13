# RepoOrbit AI protocol v0.2

## What to read, in order

1. **AGENTS.md** (short instructions, no corpus).
2. **agent.json** (machine contract and entrypoints).
3. Invoke the three MCP tools as needed. Only request additional evidence for a specific result.
4. If no executable tools exist, fetch **ai/index.json** and the *one* matching \`ai/terms/{letter}.json\` static shard. Do not read the 672-reference JSONL just to search by a word.

No step assumes a chat assistant can read a local terminal. An MCP host handles process startup. A web-only AI can navigate the static JSON files without human commands or authentication.

## MCP stdio

MCP protocol version: \`2025-06-18\`. Standard JSON-RPC 2.0 over newline-delimited stdio messages. Python 3.10+ standard library only. The server does **not** call GitHub or any external service during queries.

Available tools:

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

## Static indexed discovery without local execution

If an agent cannot launch MCP but can fetch files, read \`ai/index.json\` first.

Choose \`ai/terms/{first_letter}.json\` for each significant lowercase ASCII word in the query. For example \`mcp\` maps to \`ai/terms/m.json\`. Each file is self-contained:

\`\`\`json
{"v":1,"r":[["owner/repo","u",0]],"t":{"example":[0]}}
\`\`\`

The example is a shape demonstration, not real corpus data.

\`r\` is a local, zero-based row table: \`[repository_slug, role, verification]\`; roles \`c\`/ \`p\`/ \`u\` mean catalog / project / unverified reference; verification \`1\` means path existence checked when seeded, \`0\` means unchecked link. The map \`t\` contains lowercased lexical terms to integer offsets into \`r\`. For multiword queries, intersect **repository slugs**, not per-shard numeric offsets (offsets are local). Stopwords are documented in \`ai/index.json\`. Numeric-leading words, paraphrases, and semantic associations require the MCP route.

### Source and update policy

Index shards are deterministically built from \`data/sources.json\`, \`data/repositories.jsonl\`, and \`data/discoveries/*.jsonl\`. The CI suite rejects stale shard contents after corpus changes. The source lists remain the authoritative evidence; static indexes are derived and may be rebuilt, never hand-edited.

## Performance measurement plan

For each representative test query, record the complete incoming + outgoing MCP payload size in bytes and, where available, model-token count. Compare against a baseline that injects the full 672-reference JSONL. Benchmark single-hit, 5-hit, 20-hit, multiword, missing-result and typo cases separately. Report model, tokenizer, date, cache state and corpus version. Never generalize a one-query byte saving to all tokenizers or queries.

## Future evolution

Semantic aliases, curated capability evidence and incremental catalog ingestion can be added as **additional evidence-bearing layers**, never silently to the lexical field. Any hosted HTTP/MCP endpoint would require deployment and security review; **no hosted endpoint is claimed in v0.2**.
