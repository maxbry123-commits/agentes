# TRAZABILIDAD - AGENT SKILLS + WEB CAPABILITIES PARA SEALS

## Agent Skills standard
Official standard: https://agentskills.io/specification
Anthropic reference repo: https://github.com/anthropics/skills
Pinned commit: 34040c9c568585f6929bedeaad110ad08f079624
spec/agent-skills-spec.md blob: 772512097afe01955bd635c46b71cd351ce42e9a
template/SKILL.md blob: 50a4f9b104357d96361e257adb70454604cd15c0

Verified official constraints used by the schema:
- skill directory requires SKILL.md;
- SKILL.md = YAML frontmatter + Markdown body;
- required frontmatter: name + description;
- optional: license, compatibility, metadata, allowed-tools;
- scripts/, references/, assets/ are optional conventions;
- progressive disclosure is part of the standard;
- official validation reference: skills-ref.

## Scrapling
Repo: https://github.com/D4Vinci/Scrapling
Commit: 2b160ee18bfee79bb0115e2d9e9c746c8d9bf4c9
Official Agent Skill: agent-skill/Scrapling-Skill/SKILL.md
Blob: d3545fdc5503fbce3d4a9779378541e7ed6c0e5e
Key verified behavior: static/browser/stealth extraction, official Agent Skill, AI-targeted sanitization guidance.

## ScrapeGraphAI
Repo: https://github.com/ScrapeGraphAI/Scrapegraph-ai
Official site: https://scrapegraphai.com/
Commit: c75c8084fae2d4f5ba01a8c218bc1168b67e3569
SmartScraperGraph file blob: b29d038aed801d1056cc6daf184a03b6a9eace0a
SearchGraph file blob: 2458c1d8bc7e445cddd71859b54367de64a80133
Verified behavior: graph-based fetch/parse/reason/generate pipeline and search->iterate->merge pipeline.

## Agent Reach
Repo: https://github.com/Panniantong/Agent-Reach
Commit: a19a171fa980a0785849596492e0af4db800c82f
Agent Skill: agent_reach/skill/SKILL_en.md
Blob: 4d7466d9cda598716a697f2a63774d399d2b1333
English README blob: b15b3ce6a807af6980202c09a00b6d197f0a6ded
Verified behavior: health-check-first multi-backend research routing; read-only use is the Seals integration target.

## MATERIALIZATION

Use ONLY the canonical Motor 2:
`➡️📂motores de descarga extracción copiado movimiento archivos agentes/📂Motor descarga de componentes y extracción de zip/motor_2_queue_download_extract.py`

Queue:
`DOWNLOAD-EXTRACT-QUEUE.json`

Expected destination after execution:
`➡️ 📂 shema skills agente/sources/<slug>/code/`

Current status: SCHEMAS_READY / SOURCE_MATERIALIZATION_PENDING.
Do not mark downloaded until Motor 2 returns VERIFIED_CLOSED and read-back proves source_commit + extracted_tree.
