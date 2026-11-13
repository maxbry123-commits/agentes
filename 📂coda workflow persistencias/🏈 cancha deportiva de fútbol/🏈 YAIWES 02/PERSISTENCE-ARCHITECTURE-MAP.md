# 02 — CyberStrikeAI → CODA persistence link

## Provenance

- Canonical source: `AIPentest/CyberStrikeAI`
- Source commit: `ac101d8476d700f7766107894727a9f8234d1867`
- Verified source/extracted tree SHA-256: `bf55ae3fb9879cb1106461b870648fc216b2612f1103622e10550620e078565b`
- Files verified by download/extract motor: 1048

## Retained architecture

The copied project separates agent logic, orchestration prompts, application/runtime modules and observability. The useful persistence patterns are its bounded agent loop, orchestrator/supervisor split, trace handling, planning and rollback/cleanup concepts.

## Surgical transformation

The transformed working tree repurposes the public orchestrator to the benign lifecycle:

`LOAD_STATE → VALIDATE_TASK → PLAN → SAVE_CHECKPOINT → EXECUTE_SAFE_TASK_ADAPTER → VERIFY → SAVE_RESULT → HANDOFF_READY`

Four role files that represented external/offensive actions were neutralized or repurposed for task-state responsibilities: external inventory became local task inventory; lateral movement became state handoff; evasion became policy checking; exfiltration became result/checkpoint preparation.

The original Go `internal/agent` implementation imports HTTP/network, MCP and C2 infrastructure. CODA does not execute that path. `code/coda_persistence/link.py` is a stdlib-only persistence runtime and explicitly reports network, subprocess, C2 and offensive MCP tools as disabled.

## Tests

GitHub Actions run `34810553492`, job `103870881676`: **PASS**. Four tests for this link passed, covering safe handoff, idempotent resume, fail-closed rejection of an offensive task category, and checkpoint path containment.

Next link: `03-LuaN1aoAgent`.
