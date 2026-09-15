# README — Perfiles de agentes Wordflow LOOP YAIWES

Contrato: `yaiwes.agent-profile/v1`
Estado: `ACTIVE_NON_AUTHORITATIVE_PROFILE_INDEX`

## Autoridad

Los perfiles orientan cómo trabaja cada agente, pero **no son fuente de verdad**. Ante discrepancia gana, en este orden:

`Crazy Wall STATE/CHECKPOINT → agent_fleet_registry.json → evidencia fresca → profile → memoria`.

No guardar secretos, tokens ni chain-of-thought. Un perfil nunca concede PASS, permisos, claim o ejecución.

## Contrato común

Todo agente del LOOP hereda estas reglas:

1. READ FRESH antes de actuar.
2. DISCOVER → READ → UNDERSTAND → PLAN → STRUCTURED ACTION; nunca write blind.
3. Side effects: `StructuredAction → Sheriff/Policy → Adapter → Sandbox/Executor → Observation`.
4. Retry de la misma operación conserva `command_id`.
5. Usar entre 3 y 5 skills **relevantes y verificadas** cuando exista cobertura suficiente; si hay menos de 3, registrar GAP en vez de rellenar con skills irrelevantes.
6. Backend PASS requiere tests/ejecución/evidencia real.
7. Frontend PASS requiere code + build + runtime + browser + interaction + DOM/console o evidencia visual + mobile/touch.
8. `UNKNOWN != PASS`; presencia de código != integración runtime.
9. Trabajo paralelo requiere write scope aislado.
10. STATE/CHECKPOINT/evidence deben permitir reconstruir el trabajo sin depender de memoria libre del agente.

## Flota 18/18

| slot | agent_id | rol base | perfil específico |
|---:|---|---|---|
| 1 | opencode | writer / executor / final_reviewer | contrato común + registry |
| 2 | openhands | review / repair / final_reviewer | contrato común + registry |
| 3 | claude_code | flow_review / wiring_review / auditor | `CLAUDE.md` |
| 4 | mimo_code | flow_review / wiring_review / auditor | contrato común + registry |
| 5 | codex | auditor / debug / code_review | contrato común + registry |
| 6 | smolagents | auditor / council | contrato común + registry |
| 7 | hermes | auditor / worker | contrato común + registry |
| 8 | openclaw | auditor / coordinator / gateway | contrato común + registry |
| 9 | aider | editor / council | contrato común + registry |
| 10 | muse_glimmer | council / reviewer | contrato común + Muse/Glimmer gates |
| 11 | kimi_k | council / reviewer | contrato común + registry |
| 12 | qwen_code | council / reviewer | contrato común + registry |
| 13 | cline | coder / auxiliary | contrato común + registry |
| 14 | goose | research / auxiliary | contrato común + registry |
| 15 | agent_zero | fallback_worker | contrato común + registry |
| 16 | opendev | fallback_coder | contrato común + registry |
| 17 | research_agent_lab | research | contrato común + registry |
| 18 | mirothinker | reasoning / reviewer | contrato común + registry |

La tabla es una vista humana sincronizada con `workspace/memory/agents/➡️📂 readme memoria agentes.md`. Si el registry cambia, debe regenerarse/reconciliarse antes de usarla para routing.

## Perfil mínimo por ejecución

```json
{
  "schema": "yaiwes.agent-profile/v1",
  "agent_id": "...",
  "project_id": "...",
  "node_id": "...",
  "roles": [],
  "allowed_tools": [],
  "selected_skills": [],
  "write_scope": "...",
  "base_sha": "...",
  "completion_profile": "backend|frontend|general",
  "command_id": "cmd-...",
  "evidence_required": true
}
```

## Relación con memoria

El perfil define **cómo debe actuar** el agente. `workspace/memory/agents/` conserva únicamente contexto recuperable de lo que ocurrió. Ninguno sustituye STATE/CHECKPOINT.
