# Contributing to RepoOrbit

Thanks for helping make repository discovery more useful and more accurate.

## Add a discovery source

1. Confirm the GitHub repository actually exists; note the date.
2. Add an entry in \`data/sources.json\` with a unique lowercase \`github:owner/repo\` ID, canonical URL, source type, scope, and topics.
3. Set \`reuse_mode\` to \`links_and_metadata_only\` and \`catalog_ingestion_enabled\` to \`false\` until rights and adapters are reviewed.
4. Do not paste third-party README content into the registry. Add links and a short original description instead.
5. Run the offline validation and test suite.

## Add a project

1. Verify the repository path against GitHub.
2. Add exactly one JSON object per line in \`data/repositories.jsonl\`.
3. Use the complete record contract from \`schemas/repository.schema.json\`.
4. Include a genuine \`discovered_via\` value and \`last_verified_at\`. Never claim discovery through a catalog unless you actually found the reference there.
5. Use \`null\` for unobserved metadata, \`unknown\` for costs, and \`not_run\` until a functional test is actually executed.
6. Keep source catalogs and project seeds in their separate files. Report a repository serving both roles so it can be modeled explicitly in a future version.

## Validate

\`\`\`bash
python3 scripts/corpus.py validate
python3 scripts/corpus.py stats
python3 -m unittest discover -s tests -v
\`\`\`

## Review criteria

Changes must demonstrate real provenance, valid identity, non-duplication and no fabricated claims. Document license/usage restrictions for upstream content extraction. PRs that introduce scrapers must include conservative rate limits, terms review, fixture-based tests, and graceful failure.

Open an issue for corrections or removal requests, identifying the exact source record and supporting evidence. Maintainers should preserve a dated audit trail for corrections.
