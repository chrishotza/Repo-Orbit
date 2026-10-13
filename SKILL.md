---
name: repoorbit
description: Evidence-linked, low-context GitHub repository discovery for AI agents, in English and Spanish.
---

Use `agent.json` and start with `categories`/`browse` for category requests rather than reading full README or discovery files. Call MCP `recommend` with a user task, then `resolve` for exact evidence if necessary. If no supported intent matches, use lexical `search` (default 5 results); do not fabricate semantic relevance. `stats` counts only indexed paths.

If no runtime is available, read `ai/intent.json` or at most the needed `ai/terms/{letter}.json` files. `cost=unknown` and `tested=false` are literal: upstream documentation does not establish zero price or a functioning installation. Request `strict_free=true` to reject all unverified free claims.
