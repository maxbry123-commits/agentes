<!--
name: 'Tool Description: Skill'
description: Load a skill explicitly referenced by the user into the conversation
version: 2.1.0
-->

Load a skill's instructions into the current conversation context. Skills are predefined workflows that the user explicitly requests by name (e.g., "commit", "/review-pr", "deploy").

## When to use this tool

ONLY use `Skill` when the user explicitly mentions a skill by name in their prompt — either as a slash command (e.g., "/commit") or by name (e.g., "run the commit skill"). This tool loads predefined workflow instructions — it does NOT perform general tasks.

## CRITICAL: Do NOT use this tool for general tasks

This tool ONLY loads predefined markdown skill files. It cannot explore code, summarize, plan, or perform any general work. If the user did not explicitly mention a skill name, do NOT use this tool.

- "summarize the codebase" → use `Agent` with `agent_type: "explore"`, NOT `Skill`
- "how does auth work?" → use `Agent` with `agent_type: "explore"`, NOT `Skill`
- "design a caching layer" → use `Agent` with `agent_type: "planner"`, NOT `Skill`
- Any general task → use the appropriate tool or subagent, NEVER `Skill`

## Usage notes

- Skills only need to be loaded ONCE per conversation — after loading, the skill content remains available in context. Do not re-invoke a skill that is already loaded
- When a skill tag (from a previous invocation) is already present in the conversation, follow its instructions directly instead of invoking again
- BLOCKING REQUIREMENT: When a user references a skill or slash command (e.g., /commit, /review-pr), invoke the relevant skill BEFORE generating any other response about the task
- Call without skill_name to list all available skills
- Do not use this tool for built-in CLI commands (/help, /clear, etc.) — those are handled directly by the CLI
- After a skill is loaded, it may contain checklists or workflows. Follow the skill's instructions exactly as specified
