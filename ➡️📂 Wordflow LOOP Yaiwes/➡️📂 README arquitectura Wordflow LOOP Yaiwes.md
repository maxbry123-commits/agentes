# ➡️📂 README arquitectura Wordflow LOOP Yaiwes

Contrato operativo: `tel.workflow/v4`  
Modo: `FAIL_CLOSED_EXECUTION_LOOP`  
Arquitectura: modular, determinista por defecto, no monolítica.  
Estado actual: `ACTIVE_3STEP_AGENT_INTEGRATION`  
Nodo actual: `STEP3_AGENT_FLEET_VERIFY`  
Cola: `1×1`.

> Arquitectura detallada anterior preservada por blob `36141732a9f94b606657bc25fff8e6d0709dfe6a`. Esta reconciliación actualiza únicamente el parche de agentes de 3 pasos y conserva la trazabilidad histórica.

## 1. Objetivo final
`documentos/proyectos YAIWES → requisitos trazables → task contracts → código/agentes → Ficha/adapter/plugin → Capability Registry/binding → ejecución/repair → auditoría/tests → STATE/CHECKPOINT/evidence → E2E verificable`.

El Wordflow LOOP es el motor persistente que mantiene el trabajo hasta cierre real.

## 2. Método operativo
Guía canónica: `➡️📂 Wordflow LOOP Yaiwes/GUIA-MAESTRA-EJECUCION-LOOP-V4-WORDFLOW-YAIWES.md`.

Leyes: `estado real > memoria > inferencia`; `sin evidencia=GAP`; `archivo presente≠integrado`; `código escrito≠ejecutado`; `mock≠runtime real`; `NO_FORCE_GIT`; `NO_MONOLITO`; `NO_REHACER_TRABAJO_VERIFICADO`.

## 3. Arquitectura por capas
### A — Input/documentos
`INPUT literal → schema → Mission/GoalLock → provenance`.
### B — DSL/DAG/contratos
`requisito → DAG/deps → Task Contract/Ficha → criterios success/failure`.
### C — Sheriff/gobierno
`contract → Sheriff → Validator → guards → policy → delta autorizado`.
### D — Kernel determinista
`event loop → scheduler → runtime → registry/router → state`; kernel/control `0% LLM`.
### E — Execution orchestration
`cola 1×1/DAG-ready → manifest → capability select → dispatcher → checkpoint/recovery`.
### F — Enchufe Universal
`Ficha v2 → adapter/plugin → Capability Registry → loader/mount guard → binding → health/evidence`.
### G — Agentes/programación
`Task Contract → AgentFleetAdapter determinista → registry por slot/rol → transport env → agente → resultado normalizado → evidence`.
### H — Reasoning on demand
Primero algoritmo/código determinista; reasoning/model solo cuando no exista solución determinista suficiente.
### I — State/events/durability
`input_hash + node_id + checkpoint + attempt + strategy/delta → store → recovery/idempotencia`.
### J — Memory/storage/tools/models
Sistemas autorizados por contrato; modelos por `secret_ref`; health/budget/timeout/fallback.
### K — Evidence/audit
`fuente/URL/SHA → EvidencePacket → auditoría → tests → verify_final`.
### L — Output/E2E
`documento → tarea → code/agente → plugin/registry → ejecución → repair → audit → state/evidence → salida`.

Separación requerida: `contracts/ adapters/ plugins/ registry/ loader/ guards/ tests/`.

## 4. Fundación LOOP ya verificada — NO REHACER
- LOOP5: LangGraph, Temporal Python SDK, Prefect, Hatchet Python SDK, redun.
- MOVE: `26d0860ef23c3285ee60c63a5c9121fa45bb0ed1`.
- Wiring runtime Universal Plug: `da290e6200c9e82154ed917ce6bbc6194d423da3`.
- Trigger programación real: commit `ebac5c5b10d03d5e828e8fae266af88eb7b9b3d3`, run `34179064259`, `PASS_REAL`, 3/3, idempotencia PASS, fail-closed PASS.
- T16 Ficha v2: run `34075371938`, PASS 4/4.

## 5. PARCHE DEL DIRECTOR — EXACTAMENTE 3 PASOS
### PASO 1 — Índice — VERIFIED_CLOSED
- Repo: `maxbry123-commits/Agentes-motores-Wordflow-YAIWES`.
- Archivo: `➡️📂 readme indice agentes.md`.
- Commit: `ba9596c5716f34926e23186330609d4238bd8ccd`.
- Solo nombres/rutas/metadata; sin tests.

### PASO 2 — Cableado 1×1 — WIRED_UNTESTED
Carril implementado: `Ficha v2 → AgentFleetAdapter → registry/binding → Universal Plug registry → health descriptor`.

Archivos:
- Adapter: `Agente Yaiwes principal/execution-engine-pool/agent-bindings/agent_fleet_adapter.py`, blob `3e88678073c895899ab05dac0dd1c0ecee3c817e`, commit `1567d025656466df2c816ee4f52f404cbaca2e5a`.
- Registry 18 agentes: `agent_fleet_registry.json`, commit `f2e99e193286043d8cd2ed5bd5310b5ea9b42c7c`.
- Ficha: `wordflow-loop-contracts/ficha.agent_fleet.v2.json`, commit `c21c632a09d27098157d39b80e0ebd29fd72dad1`.
- Health sin tests: `agent_fleet_health.json`, commit `ff4f60a69bad684acb60e2239ffe72c2f6b0e20d`.
- Registry Universal Plug: `wordflow_loop_plugin_registry.json`, commit `973a9ab800ea91ff0503efbd933428a693fdee50`.

El router es determinista: `agent_id` explícito tiene prioridad; si se selecciona por rol, usa el primer slot numérico que declara ese rol. Ningún LLM decide el routing del fleet.

### PASO 3 — Test final — IN_PROGRESS
Workflow: `.github/workflows/wordflow-agent-fleet-step3.yml`.
Trigger head: `79e0a5d29313ff5620b136cf19c1e71eab776505`.
Run: `34405553218`.

Test autorizado únicamente aquí: 18 IDs únicos, Council12, routing exacto por roles, health descriptors, fail-closed, registro único `yaiwes.runtime.agent_fleet`, y preservación del trigger de programación real 3/3.

## 6. Fleet cableado — 18
1. OpenCode — writer/executor/final reviewer.
2. OpenHands — review/repair/final reviewer.
3. Claude Code — flow/wiring review + auditor.
4. MiMo Code — flow/wiring review + auditor.
5. Codex — auditor/debug/code review.
6. SmolAgents — auditor/council.
7. Hermes — auditor/worker.
8. OpenClaw — auditor/coordinator/gateway.
9. Aider — editor/council.
10. Muse/Glimmer Code — council/reviewer.
11. Kimi K Code — council/reviewer.
12. Qwen Code — council/reviewer.
13. Cline — coder/auxiliary.
14. Goose — research/auxiliary.
15. Agent-Zero — fallback worker.
16. OpenDev — fallback coder.
17. Research Agent Lab — research.
18. MiroThinker — reasoning/reviewer.

Council12: Claude Code · OpenClaw · Hermes · Codex · Aider · OpenCode · OpenHands · MiMo Code · Muse/Glimmer · Kimi · SmolAgents · Qwen.

Adicionales seleccionados: Agent-Zero, OpenDev, Research Agent Lab y MiroThinker. No se agregaron más porque ya existe cobertura de consenso y estos cuatro cubren fallback worker, fallback coder, research y reasoning/review.

## 7. Fuentes físicas y GAPs
Fuente física localizada en motor repo para: OpenCode, OpenHands, Claude Code, MiMo, Codex, SmolAgents, OpenClaw, Aider, Kimi, Qwen y Cline.

`SOURCE_NOT_LOCATED_IN_REPO_ROOT_INDEX`: Hermes, Muse/Glimmer, Goose. Se permite conservar su slot lógico/transport fail-closed, pero **no** declarar integración física de source ni runtime ejecutado.

Transportes externos se configuran solo por variables de entorno (`command_env`/`http_env`); no hay secretos/endpoints hardcodeados.

## 8. Hugging Face
Estado comunicado por el Director: `EN_CURSO` fuera de este parche. No tocar ni probar HF hasta señal explícita.

## 9. PLAN30 histórico
T01–T16 permanecen históricamente `VERIFIED_CLOSED`. El parche actual materializa T20–T24 como contratos/bindings `WIRED_UNTESTED`; STEP3 aporta evidencia para T28–T30. No declarar cierre global mientras run STEP3 no pase y los GAPs externos requeridos permanezcan sin evidencia.

## 10. Prohibiciones actuales
`NO_STEP_4` · `NO_NEW_OSS_RESEARCH` · `NO_REDOWNLOAD_LOOP5` · `NO_TEST_STEP1_STEP2` · `NO_PARALLEL_ARCHITECTURE` · `NO_FORCE_GIT` · `NO_FALSE_PASS`.

## 11. Recovery / siguiente acción
`HANDOFF → STATE → CHECKPOINT → PLAN → RECOVERY → BITACORA → HEAD → run 34405553218`.

Siguiente delta: verificar run `34405553218`; si falla, reparar solo el fallo del test; si success, persistir `STEP3_AGENT_FLEET_VERIFY.json`, promover plugin fleet a `ACTIVE` y reconciliar documentos.

## 12. Enlaces
- Índice: https://github.com/maxbry123-commits/Agentes-motores-Wordflow-YAIWES/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20readme%20indice%20agentes.md
- Adapter: https://github.com/maxbry123-commits/agentes/blob/main/Agente%20Yaiwes%20principal/execution-engine-pool/agent-bindings/agent_fleet_adapter.py
- Registry: https://github.com/maxbry123-commits/agentes/blob/main/Agente%20Yaiwes%20principal/execution-engine-pool/agent-bindings/agent_fleet_registry.json
- Health: https://github.com/maxbry123-commits/agentes/blob/main/Agente%20Yaiwes%20principal/execution-engine-pool/agent-bindings/agent_fleet_health.json
- Ficha: https://github.com/maxbry123-commits/agentes/blob/main/Agente%20Yaiwes%20principal/kernel-principal/extension-kernel/capability-registry/wordflow-loop-contracts/ficha.agent_fleet.v2.json
- Universal Plug registry: https://github.com/maxbry123-commits/agentes/blob/main/Agente%20Yaiwes%20principal/kernel-principal/extension-kernel/capability-registry/wordflow_loop_plugin_registry.json
- STEP3 workflow: https://github.com/maxbry123-commits/agentes/blob/main/.github/workflows/wordflow-agent-fleet-step3.yml
- STEP3 run: https://github.com/maxbry123-commits/agentes/actions/runs/34405553218
- HANDOFF: https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20Wordflow%20LOOP%20Yaiwes/HANDOFF.md
- STATE: https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20Wordflow%20LOOP%20Yaiwes/Crazy%20Wall%20Orquestador/STATE.json
- CHECKPOINT: https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20Wordflow%20LOOP%20Yaiwes/Crazy%20Wall%20Orquestador/CHECKPOINT.json
- PLAN: https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20Wordflow%20LOOP%20Yaiwes/Crazy%20Wall%20Orquestador/PLAN-LOOP-30-TAREAS.md
- RECOVERY: https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20Wordflow%20LOOP%20Yaiwes/Crazy%20Wall%20Orquestador/RECOVERY-PATCH.md
- BITÁCORA: https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20Wordflow%20LOOP%20Yaiwes/Crazy%20Wall%20Orquestador/BITACORA-CRAZY-WALL.md
