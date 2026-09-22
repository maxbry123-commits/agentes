# ➡️ 📂 shema skills agente

Purpose: canonical Agent Skills schema + YAIWES executable contracts + source acquisition queue for Seals Team YAIWES.

Files:
- `agent-skills-official-frontmatter.schema.json` - official Agent Skills frontmatter rules.
- `yaiwes-agent-skill-contract.schema.json` - deterministic YAIWES extension used by Seals.
- `scrapling.schema.json` - Scrapling capability contract.
- `scrapegraph-ai.schema.json` - optional LLM-assisted graph scraping contract.
- `agent-reach.schema.json` - read-only multi-platform research contract.
- `DOWNLOAD-EXTRACT-QUEUE.json` - exact Motor 2 queue pinned to commits.
- `TRACEABILITY.md` - source evidence.

Architecture:
`Agent Skill -> validate official metadata -> YAIWES contract -> Sheriff/Policy -> adapter/tool -> ToolResult -> evidence`

Rule:
These components are NOT subagents inside Seals. They are capabilities/tools exposed through schemas and adapters. The source repos are materialized outside `seals_core`.

Materialization status:
`PENDING` until canonical Motor 2 is actually executed and returns `VERIFIED_CLOSED` for all 4 queue items.
