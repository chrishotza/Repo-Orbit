# RepoOrbit

**One search. Every repository.**

RepoOrbit is an open, evidence-first index for discovering GitHub projects and the catalogs that reference them. It aims to make finding useful software simple without confusing popularity with quality or source availability with free operation.

> **Project status: foundation / corpus v0.1.** This repository currently contains a manually verified seed set and a local command-line corpus synchronizer. It is not yet a comprehensive GitHub index, hosted search engine, or functional software testing service.

## What makes it different

- **Find things by purpose**, not just by repository name (planned).
- **Aggregate catalogs**, but preserve attribution and source-specific reuse policies.
- **One canonical project record** with all discovered references and no accidental duplicates.
- **Evidence over advertising**: a GitHub repository existing does not prove that its software runs, is safe, or costs nothing.
- **Explain costs honestly**: unknown is not free. APIs, hardware, hosting, models, and licenses are separate dimensions.
- **Zero mandatory paid services** for the core corpus maintenance scripts.

## Corpus quick start

Requires **Python 3.10+**, with no third-party Python packages.

```bash
python3 scripts/corpus.py validate
python3 scripts/corpus.py stats
python3 scripts/corpus.py sync --limit 5 --output data/snapshots/latest.jsonl
python3 -m unittest discover -s tests -v
```

The first two commands run offline. `sync` accesses the **GitHub REST API**; set `GITHUB_TOKEN` to increase available request limits. The synchronizer refreshes repository metadata only; it does **not** copy the contents of third-party catalogs or verify that their projects work.

## Layout

```text
data/
  sources.json               Verified catalog and discovery-source registry
  repositories.jsonl         Small, traceable starting set of project references
  snapshots/                Generated enrichment output (not committed)
schemas/
  source.schema.json         Source registry record contract
  repository.schema.json     Repository record contract
scripts/
  corpus.py                  Offline validation, stats, on-demand metadata sync
tests/
  test_corpus.py             Corpus invariants and normalization checks
docs/
  CORPUS.md                  Data model, pipeline, quality and coverage definitions
  PROVENANCE.md              Attribution, licensing and claims policy
  ROADMAP.md                 Measurable implementation milestones
CONTRIBUTING.md              Rules for adding/reviewing records
```

## Principles

1. **Never fabricate metrics or validation.** A missing measurement remains `null` or `unknown`.
2. **Preserve evidence.** Every seed reference has a source, verification date, and confidence state.
3. **Favor reproducible ingestion.** Canonical identities, validation, stable sorting, and auditable diffs.
4. **Respect creators.** Prefer links and API metadata; never bulk-mirror README text or code without checking rights and applicable platform terms.
5. **Prefer discoverability over gatekeeping.** Do not hide projects merely for low star counts; expose user-controlled filters.
6. **Keep search approachable.** End-user experience should eventually fit into one simple search field.

## Current limitations

The initial seed set is not an exhaustive census. `repository_exists` means only that the repository path was confirmed when seeded; it is **not** a test of installation, execution, security, maintainership, cost, or license compatibility. Catalog ingestion, semantic search, UI, and automated installation tests are later milestones.

See [corpus specification](docs/CORPUS.md), [provenance policy](docs/PROVENANCE.md), and [roadmap](docs/ROADMAP.md).

**Licensing:** Project code and original dataset licensing are pending a maintainer decision. Do not assume that publicly visible content from this or any upstream project is automatically licensed for redistribution.
