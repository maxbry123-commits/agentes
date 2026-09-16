# README — Memoria de agentes Wordflow LOOP YAIWES

Contrato: `yaiwes.agent-memory/v1`
Estado: `ACTIVE_NON_AUTHORITATIVE_MEMORY`

## Propósito

Esta carpeta conserva contexto operativo recuperable para la flota de 18 agentes sin convertir memoria en fuente de verdad. El estado autoritativo continúa en Crazy Wall `STATE.json` / `CHECKPOINT.json`; identidad, roles y transporte continúan en `agent_fleet_registry.json`.

## Flota referenciada

| slot | agent_id | función base |
|---:|---|---|
| 1 | opencode | writer / executor / final_reviewer |
| 2 | openhands | review / repair / final_reviewer |
| 3 | claude_code | flow_review / wiring_review / auditor |
| 4 | mimo_code | flow_review / wiring_review / auditor |
| 5 | codex | auditor / debug / code_review |
| 6 | smolagents | auditor / council |
| 7 | hermes | auditor / worker |
| 8 | openclaw | auditor / coordinator / gateway |
| 9 | aider | editor / council |
| 10 | muse_glimmer | council / reviewer |
| 11 | kimi_k | council / reviewer |
| 12 | qwen_code | council / reviewer |
| 13 | cline | coder / auxiliary |
| 14 | goose | research / auxiliary |
| 15 | agent_zero | fallback_worker |
| 16 | opendev | fallback_coder |
| 17 | research_agent_lab | research |
| 18 | mirothinker | reasoning / reviewer |

La tabla es una vista humana. Si discrepa con el registry fresco, **gana el registry**.

## Registro mínimo por memoria

```json
{
  "schema": "yaiwes.agent-memory/v1",
  "agent_id": "...",
  "project_id": "...",
  "node_id": "...",
  "goal": "...",
  "command_id": "cmd-...",
  "observations": [],
  "decisions": [],
  "evidence_refs": [],
  "skills_used": [],
  "last_verified_sha": "...",
  "updated_at": "..."
}
```

## Recuperación

```text
READ STATE
→ READ CHECKPOINT
→ READ agent_fleet_registry
→ LOAD profile del agent_id
→ LOAD sólo memoria relevante al project_id/node_id
→ verificar last_verified_sha
→ descartar contexto stale/incompatible
→ continuar desde evidencia, no desde recuerdo libre
```

## Reglas fail-closed

1. Memoria no concede PASS, permisos ni claims.
2. `UNKNOWN` permanece UNKNOWN.
3. No persistir secretos ni valores de tokens.
4. No persistir chain-of-thought privada; guardar sólo resultados, decisiones, observaciones y evidencia verificable.
5. Un retry conserva el mismo `command_id` cuando representa la misma operación.
6. Un nuevo side effect requiere StructuredAction + Sheriff + executor autorizado.
7. Los skills usados deben quedar identificados por nombre/versión/origen cuando se integren.
8. Frontend sólo registra PASS si existe evidencia de runtime/browser/interacción y móvil/touch además de code/build.
9. La memoria debe poder reconstruirse a partir de STATE/CHECKPOINT/evidence; si no, queda marcada `STALE_MEMORY`.

## Estado de copia física vs runtime

La presencia de un agente en `wordflow_loop/agent_sources/` prueba fuente local/copied-readback cuando existe evidencia correspondiente; **no prueba que su runtime remoto/API/MCP esté ejecutándose**. Esos dos estados se conservan separados.
