# Provenance, reuse and claim integrity

RepoOrbit aims to make public software easier to discover **without appropriating other maintainers' work or making unsupported claims**.

## Default ingestion policy

- Store the repository URL, canonical identity and appropriately obtained public API metadata.
- Store a locator back to the catalog or project that introduced a reference.
- Do **not** copy README bodies, code, screenshots, compiled releases, database dumps, personal profiles or other expressive content by default.
- Treat catalog list contents as subject to their own published licenses, authorship, site rules and any applicable database rights. Review these **before** adding a content-extraction adapter.
- Record the source license **separately** from a linked project's license. A permissive list license does not make every linked project permissively licensed.
- Preserve credit and origin even when a license does not require attribution; provenance is useful for trust and updates.
- If terms or reuse rights are unclear, link rather than republish substantial content.

## Why public does not always mean free

| Question | Evidence needed |
|---|---|
| Is source visible? | Public repository access |
| May users copy/modify/redistribute? | Applicable project license, including scope and exceptions |
| Does it run locally? | Reproducible installation/execution evidence |
| Are hosted APIs required? | Actual configuration, dependencies and provider policies |
| Is there a free tier? | Provider terms and dated limit/credit information |
| Does a user need paid GPUs/hosting? | Workload-specific compute and resource estimate |
| Is it safe? | Separate security evaluation; never inferred from popularity |

If these are unverified, use \`unknown\`. The initial project corpus deliberately makes **zero verified-free or verified-working claims**.

## Upstream and API responsibilities

- Respect GitHub's API rate limits, authentication rules, backoff guidance and current terms.
- Fetch public repositories using official APIs where practical, not indiscriminate aggressive scraping.
- Do not embed or share API tokens; do not circumvent restrictions with multiple identities.
- No repackaging upstream data for spam, surveillance, or sale of user contact information.
- Follow robots and other applicable access restrictions for non-GitHub sources.
- Honor takedown/correction requests and investigate misattributed, sensitive or illegally shared material.

Useful primary references:
- https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api
- https://docs.github.com/en/rest/search/search
- https://docs.github.com/en/site-policy/github-terms/github-terms-of-service
- https://docs.github.com/en/rest/licenses/licenses
- https://creativecommons.org/public-domain/cc0/
- https://spdx.org/licenses/

## Truthful claims

A record must distinguish **observation**, **maintainer assertion**, **independent test**, and **inference**. Evidence should contain the source URL, retrieval timestamp, extraction method/version, and, where relevant, a content hash and test environment.

- Never invent GitHub stats, benchmark scores, compatibility, costs or safety.
- Display the verification date; freshness expires.
- Keep negative and failed checks, not just successful ones.
- Avoid ranking purely by stars. Ranking methods must be transparent and user-controllable.
- Ensure a description of an upstream product is original and factual, or reproduced only where rights permit.

## Licensing this repository

No \`LICENSE\` file is introduced in v0.1 because the repository owner has not chosen a license. Recommended review: an OSI-approved code license (often Apache-2.0 or MIT) **and**, if desired, a suitable dedication/license for *original* metadata compilations. A RepoOrbit license cannot relicense third-party material. Do not mark anyone else's work CC0 without authority.

This is a working engineering policy, not legal advice.

## Current permitted reuse example

For the first discovery snapshot, the upstream repository `sindresorhus/awesome` explicitly publishes a `CC0 1.0 Universal` license. We saved a *minimal index of repository URL references* (not README prose), together with the source repository identity, README line and blob SHA. The resulting 672 targets are **unverified**. Do not extend the same permission assumption to other sources without reviewing each source's terms and license independently.

## Second explicitly reviewed CC0 directory (2026-10-13)

The upstream `sindresorhus/awesome-nodejs` repository has a `license` file that explicitly declares CC0 1.0 Universal. RepoOrbit recorded only 527 GitHub path references from the README blob `329009f8d6a94007c3aa05a92b79317073b95001`, with their line numbers; none of the targets are assumed to exist, be free, or function. This permission review applies only to that directory's own material; linked repositories retain independent licenses.

The two reviewed feeds can be **monitored read-only** using `.github/workflows/refresh-feeds.yml`; staged output is not automatically promoted to the public index.
