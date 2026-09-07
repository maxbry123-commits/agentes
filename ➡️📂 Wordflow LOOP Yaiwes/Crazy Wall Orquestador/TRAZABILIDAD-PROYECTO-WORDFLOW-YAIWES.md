# TRAZABILIDAD DEL PROYECTO — Wordflow LOOP Yaiwes

Contrato: `tel.workflow/v3`  
Modo: `FAIL_CLOSED_LOOP`  
Cola: `1x1`  
Fecha de consolidación: `2026-09-06`  
Regla: **presencia de archivo ≠ integración**. Un cierre exige ruta + SHA/blob/diff + prueba/log + URL/evidencia.

## 1. Objetivo final

`documentos/proyectos → requisitos trazables → tareas de programación → código reutilizado/generado → Ficha/contrato → adapter/plugin → registry → ejecución real → verificación/repair → auditoría multiagente → STATE/CHECKPOINT/evidence → salida E2E verificable`.

## 2. Objetivos operativos O01–O11

1. **O01** — LOOP/watchdog + checkpoint + STATE + Crazy Wall + recovery.
2. **O02** — investigar código fuente necesario en repos autorizados y OSS.
3. **O03** — copiar/reusar código faltante por SHA sin reescribir lógica innecesariamente.
4. **O04** — Ficha/contrato → adapter/plugin → registry → health → evidence.
5. **O05** — verificación documental de 5 pasadas y registro de GAPs.
6. **O06** — contratos de tareas de agentes con ID/objetivo/contexto/rutas/deps/LOC/tests/evidence.
7. **O07** — integrar/espejar agentes de programación y auditoría.
8. **O08** — Hugging Face / 3 procesadores con health y prueba real.
9. **O09** — Graphiti/Grapify/SQL/HF storage mediante contratos/adapters separados.
10. **O10** — APIs/modelos solo por `secret_ref`, budget, timeout, fallback y health.
11. **O11** — tests unitarios/integración/E2E, recovery/idempotencia, auditoría y cierre.

Estado actual: O01–O03 `VERIFIED_CLOSED`; O04 `IN_PROGRESS_T16`; O05–O11 `PENDING`.

## 3. Plan completo T01→T30

| Tarea | Objetivo | Trabajo | Estado | Evidencia / cierre requerido |
|---|---|---|---|---|
| T01 | O02 | Reconciliar HANDOFF + README Wordflow + README arquitectura + STATE + CHECKPOINT + RECOVERY + Crazy Wall contra objetivo/roles | VERIFIED_CLOSED | anclas + SHA + cross-check |
| T02 | O02 | Consolidar inventario de código candidato | VERIFIED_CLOSED | `CODE-CANDIDATE-MANIFEST-PLAN30.md` blob `304176f00cafb0c3f1ff8ba12f7fb955e9dcbd83` |
| T03 | O02 | Verificar `runner.py` para cola 1×1 | VERIFIED_CLOSED | blob `daa32a5d6dfeb0d21a975b8a5b8384d68a8aa08e` |
| T04 | O02 | Verificar `runcontrol.py` pause/resume | VERIFIED_CLOSED | blob `2c6aff845c97b600d4b3851b5ee9a6e0ee23defb` |
| T05 | O02 | Verificar identidad/reinyección/checkpoint provenance | VERIFIED_CLOSED | Elspeth commit `720d441336434d227c2a00caaac100db48a07d5c` |
| T06 | O02 | Verificar `input_hash + node_id + attempt + checkpoint` | VERIFIED_CLOSED | Elspeth identity/audit/node-state evidence |
| T07 | O02 | Verificar memoria de estrategias fallidas / delta distinto | VERIFIED_CLOSED | `indexer-core` commit `efcfcb20f09117504b00f682ada1bfff2b04b649` |
| T08 | O02 | Mapear candidatos a capas físicas YAIWES | VERIFIED_CLOSED | source→dest manifest |
| T09 | O02 | Provenance/compatibilidad/imports/dependencias/decisión REUSE/COPY/PATCH/ADAPTER | VERIFIED_CLOSED | manifest blob `304176f...` |
| T10 | O03 | Integrar cola 1×1 | VERIFIED_CLOSED | `serial_dispatch.py` blob `77017b70239cedcce26f1df4a076272572f0927b` |
| T11 | O03 | Integrar pause/resume | VERIFIED_CLOSED | `run_control_adapter.py` blob `aa4f62571044d873e3969bc7f747bfc83e3047a6` |
| T12 | O03 | Integrar identidad/checkpoint | VERIFIED_CLOSED | `resume_identity.py` blob `dc440bd180194d6cef2bf1b38b1ef1b85138ef0b` |
| T13 | O03 | Integrar `input_hash/node_state` | VERIFIED_CLOSED | mismo módulo T12 + test |
| T14 | O03 | Integrar StrategyDelta/no retry idéntico | VERIFIED_CLOSED | `strategy_delta_guard.py` blob `46efd22bd7b5ac3c22cc5ca084788d46b4b5b16b` |
| T15 | O03 | Patches quirúrgicos + prueba del lote | VERIFIED_CLOSED | test blob `e1b1e3a4e4ca79e5dee00d5676a6038c6426bc31`; commit `3b7f0cec153ef03656f76dcd693c17fe061f7a78`; `5 passed in 0.06s` |
| T16 | O04 | Crear/ajustar Ficha Contract v2 de 4 capacidades | EN_CURSO | 4 Fichas materializadas; falta ejecutar validador canónico exacto 4/4 + stdout/cross-check |
| T17 | O04 | Cablear adapters/plugins a Universal Plugin/Capability Registry | PENDIENTE | registry entry + adapter test |
| T18 | O04 | Añadir health/evidence hooks + fail-closed | PENDIENTE | health/evidence tests |
| T19 | O05 | 5 pasadas docs↔arquitectura↔código↔contratos↔tests | PENDIENTE | informe + GAP ledger |
| T20 | O06 | Contratos de tareas para agentes | PENDIENTE | task contracts verificables |
| T21 | O07 | Localizar/cablear OpenCode escritor/ejecutor | PENDIENTE | source/binding/health/test |
| T22 | O07 | Localizar/cablear OpenHands revisor/repair | PENDIENTE | source/binding/health/test |
| T23 | O07 | Cablear Claude Code + Mimo Code para flow/execution/wiring review | PENDIENTE | bindings + health + review test |
| T24 | O07 | Auditores Claude/Mimo/Codex/Smolange/Hermes/OpenClaw + Council12 + embudo OpenHands/OpenCode | PENDIENTE | registry + consensus contract + test |
| T25 | O08 | HF/3 procesadores autorizados | PENDIENTE | `secret_ref` + health + run evidence |
| T26 | O09 | Graphiti/Grapify/SQL/HF storage | PENDIENTE | health + CRUD/integration test |
| T27 | O10 | APIs/modelos por `secret_ref` | PENDIENTE | no secret leak + health/budget/timeout/fallback |
| T28 | O11 | Tests unitarios/integración/E2E | PENDIENTE | logs + artifacts + pipeline documento→code→plugin→verify |
| T29 | O11 | Repetición hasta 10× de checks reales inestables + recovery/idempotencia/no duplicate effects | PENDIENTE | `stable_across_runs` + recovery evidence |
| T30 | O11 | Auditoría final + Council + 3 refutaciones + cross-check + `verify_final` | PENDIENTE | `VERIFIED_CLOSED` o GAP/INCONCLUSIVE con evidencia |

Plan canónico:  
https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20Wordflow%20LOOP%20Yaiwes/Crazy%20Wall%20Orquestador/PLAN-LOOP-30-TAREAS.md

## 4. Componentes seleccionados e implementados — trazabilidad completa

### C01 — Serial dispatch / cola determinista 1×1
- Repo origen: `maxbry123-commits/Agentes-motores-Wordflow-YAIWES`
- Ruta origen: `Loop Engineer/Loop-Engineer/loop/runner.py`
- Blob origen: `daa32a5d6dfeb0d21a975b8a5b8384d68a8aa08e`
- URL: https://github.com/maxbry123-commits/Agentes-motores-Wordflow-YAIWES/blob/main/Loop%20Engineer/Loop-Engineer/loop/runner.py
- Función usada: `select_next_task()` + semántica `dispatch_once()` de máximo un dispatch durable.
- Destino: `Agente Yaiwes principal/execution-orchestration/deterministic-execution/serial_dispatch.py`
- Blob destino: `77017b70239cedcce26f1df4a076272572f0927b`
- Tareas: T03/T10/T15.
- Estado: `VERIFIED_CLOSED`.

### C02 — Pause/resume event-sourced
- Repo origen: `maxbry123-commits/Agentes-motores-Wordflow-YAIWES`
- Ruta: `Loop Engineer/Loop-Engineer/loop/runcontrol.py`
- Blob: `2c6aff845c97b600d4b3851b5ee9a6e0ee23defb`
- URL: https://github.com/maxbry123-commits/Agentes-motores-Wordflow-YAIWES/blob/main/Loop%20Engineer/Loop-Engineer/loop/runcontrol.py
- Destino: `Agente Yaiwes principal/state-events-durability/checkpoint-recovery/run_control_adapter.py`
- Blob destino: `aa4f62571044d873e3969bc7f747bfc83e3047a6`
- Tareas: T04/T11/T15.
- Estado: `VERIFIED_CLOSED`.

### C03/C04 — identidad de reinyección + input_hash/node/attempt/checkpoint
- Repo patrón: `dta-au/elspeth`
- Commit fijado: `720d441336434d227c2a00caaac100db48a07d5c`
- `src/elspeth/contracts/identity.py` blob `98b791e350e3a2829fb2c2977cc0fbc25beb4321`
- URL: https://github.com/dta-au/elspeth/blob/720d441336434d227c2a00caaac100db48a07d5c/src/elspeth/contracts/identity.py
- `src/elspeth/contracts/audit.py` blob `c89a5d9d2354ae549845aeab9a90cc3ab14f853e`
- URL: https://github.com/dta-au/elspeth/blob/720d441336434d227c2a00caaac100db48a07d5c/src/elspeth/contracts/audit.py
- Destino adaptado: `Agente Yaiwes principal/state-events-durability/checkpoint-recovery/resume_identity.py`
- Blob destino: `dc440bd180194d6cef2bf1b38b1ef1b85138ef0b`
- Tareas: T05/T06/T12/T13/T15.
- Estado: `VERIFIED_CLOSED`.

### C05 — StrategyDelta / no repetir estrategia o delta fallido
- Repo patrón: `Alex-v-p/indexer-core`
- Commit: `efcfcb20f09117504b00f682ada1bfff2b04b649`
- Ruta: `packages/rag_core/retrieval/retry/rules.py`
- Blob: `7704a6bd73d8b073df88651bbaf232f1f3dbfd6b`
- URL: https://github.com/Alex-v-p/indexer-core/blob/efcfcb20f09117504b00f682ada1bfff2b04b649/packages/rag_core/retrieval/retry/rules.py
- Destino: `Agente Yaiwes principal/control-governance/strategy_delta_guard.py`
- Blob destino: `46efd22bd7b5ac3c22cc5ca084788d46b4b5b16b`
- Tareas: T07/T14/T15.
- Estado: `VERIFIED_CLOSED`.

### Test integrado T10–T15
- Ruta: `Agente Yaiwes principal/tests/test_plan30_loop_runtime.py`
- Blob: `e1b1e3a4e4ca79e5dee00d5676a6038c6426bc31`
- Commit: `3b7f0cec153ef03656f76dcd693c17fe061f7a78`
- Resultado registrado: `5 passed in 0.06s`.
- Evidence: `Crazy Wall Orquestador/EVIDENCE-PLAN30-T10-T15.md` blob `f8a5db43fb0cc9e1712620c75b579229c7bad14a`.

## 5. Ficha Contract v2 — T16

Fuente canónica:
- `skills/research-download-chain/assets/plugin-bus/ficha_contract_v2.py`
- Commit `37bef3a8a8f6dadca067638b8ea0c32995fc1d63`
- Blob `b27f14b4d64f77bccf53a893c49b6f20bd58e745`
- URL: https://github.com/maxbry123-commits/agentes/blob/37bef3a8a8f6dadca067638b8ea0c32995fc1d63/skills/research-download-chain/assets/plugin-bus/ficha_contract_v2.py

Fichas materializadas:
1. `execution-orchestration/deterministic-execution/ficha.serial_dispatch.v2.json` blob `bc885059ed0a97f73aad02572853d1b0a4f8117d`.
2. `state-events-durability/checkpoint-recovery/ficha.run_control.v2.json` blob `7fdb64b7a21fe51c278dcc907b09eb800f2a2770`.
3. `state-events-durability/checkpoint-recovery/ficha.resume_identity.v2.json` blob `4ce82a32faa939177dd22603f097402e9b9e6ed9`.
4. `control-governance/ficha.strategy_delta.v2.json` blob `44aeb5cb48db6d42499bc940e47e912942d7fd40`.
5. Provenance schema blob `5c3aa0b42fb9737baeb1f151a933fa83cc72c27d`.
6. Provenance registry blob `5274c96b79a4862d4081be18b80c1c0b09d9607a`.

Estado: `T16_IN_PROGRESS`; read-back 4/4 existe, pero **no se cierra** hasta ejecutar el validador canónico exacto y registrar stdout/veredicto/cross-check.

## 6. Dependencias fuente de Loop Engineer investigadas — NO copiadas ciegamente

Estas piezas explican el contexto de `runner.py/runcontrol.py`; quedaron investigadas para compatibilidad y provenance. No se consideran integradas salvo C01/C02.

- `loop/runtime.py` blob `6c3af6b9b40d1061cc34647cffd4f47bfb6ac477` — https://github.com/maxbry123-commits/Agentes-motores-Wordflow-YAIWES/blob/main/Loop%20Engineer/Loop-Engineer/loop/runtime.py
- `loop/reducer.py` blob `4860716a67238f9c9436ce5ca4a667731f3286d1` — https://github.com/maxbry123-commits/Agentes-motores-Wordflow-YAIWES/blob/main/Loop%20Engineer/Loop-Engineer/loop/reducer.py
- `loop/verifier.py` blob `2ae7afab38dd724527278a1a2f7ad1259504961e` — https://github.com/maxbry123-commits/Agentes-motores-Wordflow-YAIWES/blob/main/Loop%20Engineer/Loop-Engineer/loop/verifier.py
- `loop/plan.py` blob `b6f96302042cb1651c6fb6f8f990963d50c13b99` — https://github.com/maxbry123-commits/Agentes-motores-Wordflow-YAIWES/blob/main/Loop%20Engineer/Loop-Engineer/loop/plan.py
- `loop/events.py` blob `91a8cc9018d58eca739e5a28be2a6a78e3af4458` — https://github.com/maxbry123-commits/Agentes-motores-Wordflow-YAIWES/blob/main/Loop%20Engineer/Loop-Engineer/loop/events.py
- `loop/evidence.py` blob `b56f61da7e10ce8458d1258f5893b175e49cd643` — https://github.com/maxbry123-commits/Agentes-motores-Wordflow-YAIWES/blob/main/Loop%20Engineer/Loop-Engineer/loop/evidence.py
- `loop/fsm.py` blob `0e757ea505cd19ceb569a6bb480b4cb9f8878327` — https://github.com/maxbry123-commits/Agentes-motores-Wordflow-YAIWES/blob/main/Loop%20Engineer/Loop-Engineer/loop/fsm.py
- `loop/completion.py` blob `62fcca7a160a62728d415575b835c6c7d3d8f9b9` — https://github.com/maxbry123-commits/Agentes-motores-Wordflow-YAIWES/blob/main/Loop%20Engineer/Loop-Engineer/loop/completion.py
- `loop/chain.py` blob `97a044066566c54409f77b9304a4b66161efe76c` — https://github.com/maxbry123-commits/Agentes-motores-Wordflow-YAIWES/blob/main/Loop%20Engineer/Loop-Engineer/loop/chain.py
- `loop/contract.py` blob `d17350025b5263db8ec0eeffba02e00febc87df8` — https://github.com/maxbry123-commits/Agentes-motores-Wordflow-YAIWES/blob/main/Loop%20Engineer/Loop-Engineer/loop/contract.py
- `loop/emit.py` blob `cbadda36592b158862e3401e66de1a71a8d7fc87` — https://github.com/maxbry123-commits/Agentes-motores-Wordflow-YAIWES/blob/main/Loop%20Engineer/Loop-Engineer/loop/emit.py

Decisión: `REFERENCE/DEPENDENCY_CONTEXT`; YAIWES conserva su runtime/store/contratos propios y adapta solo semántica necesaria.

## 7. Elspeth — candidatos forenses adicionales

Commit fijado: `720d441336434d227c2a00caaac100db48a07d5c`.

- `src/elspeth/engine/executors/transform.py` blob `89f79150c0c0f31ab25f3d40d41908f48557d343` — auditoría de ejecución, node state, error routing y spans. URL: https://github.com/dta-au/elspeth/blob/720d441336434d227c2a00caaac100db48a07d5c/src/elspeth/engine/executors/transform.py
- `src/elspeth/core/landscape/execution/node_states.py` blob `6333f7d0e708006fb69e564d828fd4571203b3c7` — persistencia `node_id/attempt/input_hash/resume_checkpoint_id`. URL: https://github.com/dta-au/elspeth/blob/720d441336434d227c2a00caaac100db48a07d5c/src/elspeth/core/landscape/execution/node_states.py
- `tests/unit/engine/test_resume_offset_propagation.py` blob `84be0a07639bc24612eb3ab2f44bb5c138474874` — evidencia de resume/offset. URL: https://github.com/dta-au/elspeth/blob/720d441336434d227c2a00caaac100db48a07d5c/tests/unit/engine/test_resume_offset_propagation.py
- `tests/unit/core/landscape/repository_integration/test_recorder_node_states.py` blob `0f29b7fe3d0d8211e29268b45741afbc3e8f5ab4` — evidencia de node-state persistence. URL: https://github.com/dta-au/elspeth/blob/720d441336434d227c2a00caaac100db48a07d5c/tests/unit/core/landscape/repository_integration/test_recorder_node_states.py

Decisión: `REFERENCE/PATTERN`; no copiar el framework completo. C03/C04 adaptan solo identidad/provenance mínima.

## 8. Supreme-Agent — candidatos investigados y no seleccionados

Commit fijado: `aae277a05c5f20526443933c14fe93e1e200913f`.

- `src/core/models.py` blob `567939c73a6056a795fa24e21791914928862e1c` — `PlanStep.failed_strategies`. URL: https://github.com/corruptspower-maker/Supreme-Agent/blob/aae277a05c5f20526443933c14fe93e1e200913f/src/core/models.py
- `src/core/post_execution/feedback.py` blob `0060950ff9317c27e9b68857ea07f5023b25c25d` — cambia a alternativa si estrategia exacta ya fue intentada. URL: https://github.com/corruptspower-maker/Supreme-Agent/blob/aae277a05c5f20526443933c14fe93e1e200913f/src/core/post_execution/feedback.py
- `src/core/planner.py` blob `2eb1fbf4e4d61467fa5abdbfe2028f83c4b210be` — registra estrategias fallidas y busca herramienta alternativa. URL: https://github.com/corruptspower-maker/Supreme-Agent/blob/aae277a05c5f20526443933c14fe93e1e200913f/src/core/planner.py
- `tests/test_post_execution.py` blob `c74808c43015b59f6b664056fc853ecd0bd5e567` — tests del feedback post-ejecución. URL: https://github.com/corruptspower-maker/Supreme-Agent/blob/aae277a05c5f20526443933c14fe93e1e200913f/tests/test_post_execution.py

Decisión: `REJECTED_AS_PRIMARY / REFERENCE_ONLY`. Motivo: ofrece memoria de estrategias fallidas, pero el flujo por defecto todavía puede hacer un primer retry sin demostrar un `delta_hash` materialmente diferente. C05/indexer-core fue seleccionado como guard más estricto para la regla YAIWES.

## 9. Fuentes investigadas sin componente aplicable seleccionado en T16

- `maxbry123-commits/Agentes-motores-Wordflow-YAIWES`: fuente principal de C01/C02; no aportó Ficha Contract v2 equivalente a la canónica del skill.
- `router-universal-router-inteligente-`: revisado durante GAP T16; sin Ficha v2 YAIWES aplicable seleccionada.
- `osquestador-auditor`: revisado durante GAP T16; sin Ficha v2 YAIWES aplicable seleccionada.
- Evidencia: `Crazy Wall Orquestador/EVIDENCE-PLAN30-T16-PARTIAL.md` blob `79c89aa3c9b3ccc4670b6be5de7e312c23cbbe6b`.

## 10. Arquitectura de destino

`documentos/inputs → contracts/schema/DSL/DAG → Sheriff/Validator → kernel/control determinista → execution-orchestration → Ficha/adapter/plugin → Capability Registry → engine/agent → state-events-durability → evidence/audit → verify_final`.

Capas físicas relevantes:
- `Agente Yaiwes principal/code-programming-engine/`
- `Agente Yaiwes principal/kernel-principal/`
- `Agente Yaiwes principal/execution-orchestration/`
- `Agente Yaiwes principal/control-governance/`
- `Agente Yaiwes principal/state-events-durability/`
- `Agente Yaiwes principal/execution-engine-pool/`
- `Agente Yaiwes principal/reasoning-kernel/`
- `Agente Yaiwes principal/research-evidence/`
- `Agente Yaiwes principal/tools-models-memory-knowledge/`
- `Agente Yaiwes principal/tests/`

Prohibido monolito: `contracts/`, `adapters/`, `plugins/`, `registry/`, `loader/`, `guards/`, `tests/` separados.

## 11. Agentes y roles pendientes O07

Council/arquitectura/auditoría objetivo: Claude Code CLI, OpenClaw, Hermes, Codex, Aider, OpenCode, OpenHands, Mimo Code, Muse/Glimmer Code, Kimi K Code CLI, Smolange y un 12.º agente solo si existe evidencia real/autorizada.

Roles fijados:
- OpenCode: escritor/ejecutor principal.
- OpenHands: reviewer + repair.
- Mimo Code + Claude Code: review de flujo/ejecución/wiring.
- Auditores independientes: Claude Code, Mimo Code, Codex, Smolange, Hermes, OpenClaw.
- Embudo final de auditorías: OpenHands + OpenCode.

Ningún agente se marca integrado por mera presencia en repositorio. T21–T24 exigen binding/adapter/registry/health/test/evidence.

## 12. Anclas canónicas

- README histórico/ledger: `➡️📂 Wordflow LOOP Yaiwes/➡️📂 readme wordflow loop Yaiwes.md`
- README arquitectura actual: `➡️📂 Wordflow LOOP Yaiwes/➡️📂 README arquitectura Wordflow LOOP Yaiwes.md`
- HANDOFF: `➡️📂 Wordflow LOOP Yaiwes/HANDOFF.md`
- STATE: `➡️📂 Wordflow LOOP Yaiwes/Crazy Wall Orquestador/STATE.json`
- CHECKPOINT: `➡️📂 Wordflow LOOP Yaiwes/Crazy Wall Orquestador/CHECKPOINT.json`
- RECOVERY: `➡️📂 Wordflow LOOP Yaiwes/Crazy Wall Orquestador/RECOVERY-PATCH.md`
- BITÁCORA: `➡️📂 Wordflow LOOP Yaiwes/Crazy Wall Orquestador/BITACORA-CRAZY-WALL.md`
- PLAN30: `➡️📂 Wordflow LOOP Yaiwes/Crazy Wall Orquestador/PLAN-LOOP-30-TAREAS.md`
- Este ledger de trazabilidad: `➡️📂 Wordflow LOOP Yaiwes/Crazy Wall Orquestador/TRAZABILIDAD-PROYECTO-WORDFLOW-YAIWES.md`

## 13. Estado de continuidad

- T01–T15: `VERIFIED_CLOSED`.
- T16: `EN_CURSO`.
- T17–T30: `PENDIENTE`.
- Progreso PLAN30 verificado: `50%`.
- Próximo delta 1×1: ejecutar `ficha_contract_v2.py` canónico contra las cuatro Fichas; si 4/4 PASS + path cross-check, cerrar T16 y abrir T17.
- Estado global: `ACTIVE_LOOP`.