# Stable GitHub repository identities — RepoOrbit v0.6

## Why numeric IDs matter

GitHub's \`owner/repository\` URL is an address, not a permanent identity.
A repository can be renamed or transferred. A completely different repository
may later reuse the old address. Forks have their **own** numeric IDs.

RepoOrbit therefore records **both** the immutable numeric GitHub repository ID
and the user-facing slug, and never merges projects solely because their slugs,
README text, or repository contents look alike.

## Current evidence and limits

On **2026-10-13**, 30 existing RepoOrbit seed repositories were checked
individually using GitHub repository metadata:

- 22 catalog seeds.
- 8 software project seeds.
- 30 distinct numeric GitHub repository IDs.
- Three additional inverse lookups, by numeric ID only, returned the expected
  repositories: \`589831718\` (ComfyUI), \`21737465\` (Awesome) and
  \`896335270\` (awesome-mcp-servers).

The observations live in \`data/identities.jsonl\`, with an observation date,
default branch, current slug, numeric ID, and archival flag.
\`ai/identities.json\` is a compact 1.4 KB derivative for remote AI readers.
It covers **only the 30 checked seeds**, not the 1,185 other references.
A repository metadata check does not establish that a model/app runs, is safe,
or is free.

## Agent-facing exact lookup

\`resolve({"repo":"id:589831718"})\` finds the corresponding existing
project seed. The same tool still accepts \`Comfy-Org/ComfyUI\` or its GitHub URL.
For a checked seed, the result includes \`github_id\` and
\`identity_observed_on\`. All functional/cost caveats remain intact.

Agents that cannot execute MCP can read \`ai/identities.json\`; the file
contains sorted triples \`[numeric_id, observed_slug, role]\` with
\`c\` for catalog and \`p\` for project. An agent does **not** need to read
a full README or the entire discovery corpus to identify a checked seed.

## Read-only drift watch

The \`repoorbit.identity_watch\` module performs a bounded review of the 30
recorded seed slugs, using GitHub's documented repository metadata endpoint.
It compares the **returned numeric ID** to the pinned numeric ID. Only the
same numeric identity can be classified as a rename or transfer:

- **Same ID, same slug:** unchanged.
- **Same ID, new name:** renamed.
- **Same ID, different owner:** transferred.
- **Old slug now returns another numeric ID:** possible slug reuse;
  fail closed and request manual review.
- **404 or inaccessible:** unresolved; never assert deletion.
- **Different numeric ID and similar contents:** different repository,
  potentially a fork; do not auto-merge.

The weekly \`identity-watch.yml\` workflow has read-only GitHub permissions
and uploads a short audit artifact under the ignored snapshots directory.
It **never** silently rewrites the approved identity table or links.

## Promotion and historical data

The separate CC0 catalog promotion pipeline remains source-rights-gated and
review-only. Numeric identities are not yet available for every catalog
reference. Until a reference is checked against GitHub, it must remain
\`v=not_checked\`, even if a neighboring catalog link refers to a known project.

**Next stage:** verify referenced targets in small, rate-limited batches;
stage alias transitions with timestamped evidence; build a reviewable
canonical-ID promotion mechanism; verify at least one real rename/transfer
event before claiming end-to-end rename handling in production.

No hosted API or full GitHub crawl is claimed.
