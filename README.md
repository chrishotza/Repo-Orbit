<div align="center">

# 🪐 RepoOrbit

### A repository atlas made for AI agents

**Discover · Classify · Verify · Navigate**

*Un atlas de repositorios diseñado para agentes de IA, sin desperdiciar contexto.*

[![Corpus integrity](https://github.com/chrishotza/Repo-Orbit/actions/workflows/corpus.yml/badge.svg)](https://github.com/chrishotza/Repo-Orbit/actions/workflows/corpus.yml)
[![Python application](https://github.com/chrishotza/Repo-Orbit/actions/workflows/python-app.yml/badge.svg)](https://github.com/chrishotza/Repo-Orbit/actions/workflows/python-app.yml)

**[Agent contract](agent.json) · [AI instructions](AGENTS.md) · [Browse subjects](ai/categories/index.json) · [Evidence policy](docs/TAXONOMY.md) · [Current coverage](ai/status.json)**

</div>

---

## A catalog that knows what it *doesn't* know

Most repository lists tell you **where a link points**. RepoOrbit also tracks **who referenced it, what evidence exists, how it may be classified, and what remains unverified**. Its primary interface is machine-readable JSON and local MCP tools; this page is just an introduction.

| Indexed paths | GitHub IDs checked | Topical domains | Subjects assigned | Subjects unknown |
|:---:|:---:|:---:|:---:|:---:|
| **1,215** | **54** | **14** | **231** | **984** |

<sub>Snapshot: 2026-10-13. Of the 231 subject labels, 30 are editorial, 23 are supported by versioned README self-descriptions, and 178 remain lower-confidence filename hints. Counts are not claims of running/free software. The current machine-readable values are in [ai/status.json](ai/status.json).</sub>

## ⚡ Built for agents, not long prompts

| Agent wants to… | Compact interface |
|---|---|
| Find an app by a documented EN/ES task | `recommend({"q":"generar videos con IA", "limit":3})` |
| Route a subject request in Spanish or English | `route_topic({"q":"necesito ciberseguridad"})` |
| List available subject areas | `categories({})` |
| Browse a domain | `browse({"category":"ai-ml","limit":5})` |
| Ask why a repository has a subject label | `classify({"repo":"Comfy-Org/ComfyUI"})` |
| Search names and limited topic tags | `search({"q":"python","limit":3})` |
| Resolve exact evidence or numeric ID | `resolve({"repo":"id:589831718"})` |
| Inspect the age of a real GitHub observation | `evidence_age({"repo":"id:23088740"})` |
| Inspect coverage and uncertainty | `stats({})` |

**No hosted service, paid API, embedding model or LLM is needed for these offline queries.** A host can launch the bundled Python MCP stdio server or an agent can read only the small static index it needs. LLM response tokens are not literally zero: bounded JSON simply avoids putting the corpus into context.

### Read only what you need

| Machine-readable entry | Purpose |
|---|---|
| [`agent.json`](agent.json) | Versioned agent protocol and tool manifest |
| [`ai/categories/index.json`](ai/categories/index.json) | ~1.2 KB subject router; 14 areas + unclassified |
| [`ai/categories/ai-ml.json`](ai/categories/ai-ml.json) | One area, no other shards loaded |
| [`ai/index.json`](ai/index.json) | Alphabetic lexical index manifest |
| [`ai/intent.json`](ai/intent.json) | 8 curated bilingual task intents |
| [`ai/identities.json`](ai/identities.json) | 30 verified seed numeric IDs |
| [`ai/verified-targets.json`](ai/verified-targets.json) | 24 additional checked reference IDs |
| [`ai/status.json`](ai/status.json) | Tiny, reproducible coverage summary |
| [`ai/topic-route-eval.json`](ai/topic-route-eval.json) | 32 explicit EN/ES routing regression cases, *not* semantic accuracy |
| [`ai/evidence-dates.json`](ai/evidence-dates.json) | Historical numeric-ID and README evidence dates (not live project activity) |
| [`data/topic_evidence.jsonl`](data/topic_evidence.jsonl) | 23 original short subject statements, SHA and line pointers |


<details>
<summary><strong>Advanced agent filter: browse by verified source context</strong></summary>

An agent can pass `source: "github:sindresorhus/awesome-nodejs"` to `browse` while selecting any subject, including `unclassified`. That indicates a repository was **linked by that approved catalog**; it is not a verified Node.js-compatibility or execution claim. `classify` also exposes source IDs separately from topical hints.

</details>

## 🧭 Our classification system

RepoOrbit uses an original controlled vocabulary with 14 domains, such as **AI/ML**, **developer tools**, **security**, **cloud infrastructure**, **creative media**, **education**, **science** and **automation**. Every subject result includes the method used to derive it.

| Evidence tier | Source of label | Interpretation |
|---|---|---|
| **Editorial** (`e`) | 30 individually checked seed repositories | An editorial subject, not proof of functionality |
| **README-backed** (`d`) | 23 versioned upstream README lines | Auditable self-description, not an execution test |
| **Lexical hint** (`h`) | Whole words in a discovered repository's name | A suggestion, never a verified capability |
| **Ambiguous** (`a`) | Competing equally specific keywords | Remains unclassified |
| **Unknown** (`u`) | No defensible topical clue | Remains unclassified |

**We prefer abstaining over hallucinating.** A new read-only review queue stages source-anchored candidate excerpts and treats upstream README instructions as untrusted data. The 23 README-backed labels link to exact historical Git blobs and line numbers, not just names. [See audited evidence](docs/README_EVIDENCE.md). A GitHub link existing is not a benchmark, installation test, safety audit, license clearance or proof of free operation. [Read the classification methodology](docs/TAXONOMY.md).

## 🔎 Traceable from discovery to agent result

```mermaid
flowchart LR
    A[Approved CC0 catalogs] --> B[Source and line evidence]
    B --> C[Canonical repo paths]
    C --> D[Checked GitHub IDs]
    C --> E[Editorial subjects or lexical hints]
    D --> F[Compact static indexes]
    E --> F
    F --> G[Local MCP and AI readers]
```

Source links are preserved with their original Git blob SHA, catalog identifier and line number. GitHub numeric identities help detect renames without confusing a fork or reused slug with the same project. New sources are rights-reviewed; monitored updates are staged and proposed through **reviewable draft pull requests**, never silently merged.

## 🌱 Coverage, not hype

**1,199 catalog reference edges** come from two explicitly reviewed CC0-licensed discovery directories, and deduplicate into a corpus of 1,215 paths together with the seed references. Most discovered references are still unchecked against GitHub. Only 54 stable IDs have independent repository-existence observations. **Zero** repositories have been independently marked both functionally tested and free to run by RepoOrbit.

Daily, read-only rotating review jobs now inspect different **bounded** pages of pending GitHub references; no automatic approvals or free/functional claims. [Empirical coverage and evidence age](docs/COVERAGE_FRESHNESS.md).

Track engineering gates in [Roadmap](docs/ROADMAP.md), [Source provenance](docs/PROVENANCE.md), [ID verification](docs/TARGET_VERIFICATION.md), and [CI results](https://github.com/chrishotza/Repo-Orbit/actions).

## 🤖 Integration

An MCP-compatible agent host can use this entry in its own configuration (the host launches the server, not the end user):

```json
{"mcpServers":{"repoorbit":{"command":"python3","args":["-m","repoorbit.mcp"],"cwd":"/path/to/Repo-Orbit"}}}
```

Agent-only readers with no process execution can start at [`agent.json`](agent.json), then fetch [`ai/categories/index.json`](ai/categories/index.json) and **only their chosen category shard**. No terminal tutorial or full-corpus prompt is necessary.

---

<div align="center">

**Evidence before confidence. Small responses before giant prompts.**

[Agent navigation](AGENTS.md) · [Taxonomy](docs/TAXONOMY.md) · [Contribute](CONTRIBUTING.md)

<sub>RepoOrbit publishes original metadata and pointers, not mirrored third-party source code. Upstream repository licenses remain independent. RepoOrbit's own project-wide license has not yet been selected by its maintainer.</sub>

</div>
