# YAIWES Agent Profile Template

Schema: `yaiwes.agent-profile/v1`

Use this template only after reading fresh `STATE.json`, `CHECKPOINT.json`, `agent_fleet_registry.json` and relevant evidence.

## Identity

- agent_id: `<registry agent_id>`
- project_id: `<project>`
- node_id: `<Crazy Wall node>`
- roles: `<from fresh registry>`
- write_scope: `<isolated path>`
- base_sha: `<fresh main SHA>`
- completion_profile: `backend | frontend | general`

## Execution contract

`DISCOVER → READ → UNDERSTAND → PLAN → StructuredAction → Sheriff → Adapter → Sandbox/Executor → Observation → Test → Acceptance → Evidence`

## Skills contract

Select 3–5 **relevant, enabled, verified** skills using the canonical task-skill selector. If fewer than 3 relevant verified skills exist, emit a GAP; do not pad the selection with unrelated skills.

Record for every selected skill:
- name
- version/revision
- origin
- local path
- digest/readback evidence

## Recovery

Same side effect retry = same `command_id`. If recovery exhausts retries, block only that node and continue another independent READY node when safe. If no safe independent node exists, remain `WAIT_BLOCKED`; never fabricate PASS.

## Completion

Backend: code + execution/tests + output/evidence.

Frontend: code + build + real runtime + browser + interaction + DOM/console or visual evidence + mobile/touch.

## Prohibitions

- no secrets in profile or memory
- no raw model output treated as executable command
- no force push
- no write outside assigned scope
- no presence==integration assumption
- no UNKNOWN==PASS
- no private chain-of-thought persistence
