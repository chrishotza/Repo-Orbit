---
name: repoorbit
description: Find GitHub repository references with minimal AI-context usage and traceable evidence.
---

Read \`agent.json\`, not whole README files. Prefer the local stdio MCP tools \`search\` (limit 5), \`resolve\`, \`stats\`. When MCP is unavailable but file fetching works, read \`ai/index.json\` and only the needed \`ai/terms/{letter}.json\`.

\`exists\` means repository-path check only, not functional verification. \`not_checked\` is just a catalog reference. Cost/safety/execution are unknown unless separately evidenced. Never claim full GitHub coverage; do not copy upstream contents.
