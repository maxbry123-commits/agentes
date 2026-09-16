# TRAZABILIDAD DEL PROYECTO — Wordflow LOOP Yaiwes

Contrato: `tel.workflow/v3`  
Modo: `FAIL_CLOSED_LOOP`  
Cola: `1x1`  
Fecha de consolidación X-Ray: `2026-09-06`  
Regla: **presencia de archivo ≠ integración**. Cierre exige ruta + SHA/blob/diff + prueba/log + URL/evidencia.

## 1. Objetivo final
`documentos/proyectos → requisitos trazables → tareas de programación → código reutilizado/generado → Ficha/contrato → adapter/plugin → registry → ejecución real → verification/repair → auditoría multiagente → STATE/CHECKPOINT/evidence → salida E2E verificable`.

El LOOP es el motor persistente; no es el objetivo final.

## 2. Auditoría forense X-Ray — 5 pasadas contra el chat

### Pasada 1 — objetivos, plan y continuidad
- Se conservaron exactamente `O01–O11`.
- Se confirmó `T01–T30` como lote operativo vigente.
- GAP documental corregido: **T30 no termina automáticamente el proyecto**. Si quedan GAPs/objetivos abiertos, T30 debe producir el siguiente lote de 30 tareas (`T31–T60`, luego otro lote si hace falta) exclusivamente desde trabajo real pendiente, y continuar LOOP hasta cierre E2E.

### Pasada 2 — contrato LOOP literal del Director
Se fija la cadena operacional completa, no solo su resumen:
1. leer INPUT_BLOCK literal y no reinterpretar;
2. GOALS 12/12 entrada;
3. fijar 2 prioridades;
4. planificar;
5. cola 1×1;
6. ejecutar un delta autorizado;
7. verificar/refutar y analizar;
8. si falla: LOOP, no falso cierre;
9. auditor de instrucciones ×3;
10. si GAP: no stop/no falso escalado, investigar mínimo 10 vías y hasta 20 soluciones distintas;
11. auditor de soluciones y selección de StrategyDelta materialmente distinto;
12. investigación secundaria en comunidad de desarrolladores/code cuando fuentes oficiales no basten;
13. Council/Ask Consil 12 pasos;
14. 12 pasos de investigación intensiva cuando exista GAP complejo;
15. 6 cuestionamientos de causa: qué falló, por qué, qué evidencia falta, qué dependencia bloquea, qué delta ya falló, qué alternativa cambia materialmente;
16. ejecutar solución permitida y volver a verify/refute;
17. verificar cumplimiento del INPUT y del LOOP antes de continuar;
18. 3 refutaciones: INPUT_BLOCK, tarea/objetivos, cumplimiento LOOP;
19. verificación cruzada global;
20. checklist/CODA;
21. `verify_final`; si NO PASS, reinyección LOOP.

Política FLAG: un bloqueo `🚩` no recibe PASS. Se persiste el GAP y solo se continúa otra tarea segura si no viola dependencias; la tarea bloqueada permanece abierta.

### Pasada 3 — watchdog, salida y persistencia
- LOOP1 global: actualizar lista de tareas en **cada salida/corrida**.
- LOOP2 por tarea: aplicar la cadena anterior a cada nodo.
- Watchdog/sentinela/supervisor/guardián debe informar exactamente: avance %, nodo actual, cerradas, en curso, pendientes, GAP/flags, evidencia, cambios, siguiente acción 1×1 y mini resumen/estado.
- Estados de salida permitidos: `VERIFIED_CLOSED | CLOSED_UNVERIFIED | INCONCLUSIVE | ACTIVE_LOOP`.
- Persistencia por cambio real: reconciliar según alcance `BITACORA + STATE.json + CHECKPOINT.json + PLAN + RECOVERY + README arquitectura/HANDOFF`.

### Pasada 4 — fuentes, adquisición y arquitectura
Orden de búsqueda antes de programar:
1. chat/historial y documentos canónicos;
2. componentes locales Wordflow/YAIWES;
3. todo `maxbry123-commits/agentes`;
4. `maxbry123-commits/Agentes-motores-Wordflow-YAIWES`;
5. `router-universal-router-inteligente-`;
6. `osquestador-auditor`;
7. repos oficiales/docs GitHub;
8. comunidad solo como señal secundaria.

Antes de programar exigir `repo + ruta + URL + commit/blob SHA + comportamiento + destino + decisión REUSE/COPY/PATCH/ADAPTER`.

Si falta OSS: investigar hasta 10 pasadas y usar únicamente el skill autorizado de descarga/extracción:
https://github.com/maxbry123-commits/agentes/tree/c789e5fe635e220230ffc759d86dc3bbb8e261d4/skills/skills%20Github%20acci%C3%B3n

Reglas: no LFS, no reactivar workflows viejos, validar destino, luego `verify_final`.

### Pasada 5 — anti-alucinación, agentes y requisitos omitidos
Checks obligatorios antes de avanzar:
- ¿inventé algo?
- ¿seguí el INPUT literal?
- ¿revisé documentos/fuentes de verdad?
- ¿sigo el plan/objetivo?
- ¿verifiqué/refuté lo realizado?
- si se perdió rumbo: reconstruir contexto desde HANDOFF + README + STATE + CHECKPOINT + RECOVERY + BITACORA y retomar último checkpoint válido.

Roles fijados:
- OpenCode: escritor/ejecutor principal.
- OpenHands: reviewer/repair.
- Claude Code + Mimo Code: review de flujo/ejecución/wiring.
- Auditores: Claude Code, Mimo Code, Codex, Smolange, Hermes, OpenClaw.
- Council adicional: Aider, Muse/Glimmer Code, Kimi K Code CLI.
- 12.º Council candidato: **Qwen Code CLI**, solo si existe evidencia real/autorizada.
- Embudo final: OpenHands + OpenCode.

GAPs de arquitectura detectados por cross-check con README histórico:
- **105 capacidades/algoritmos deterministas** son parte del diseño aprobado y deben ser auditados/registrados/cableados antes de cierre global si aún no existe evidencia de registry/runtime. No se consideran integrados por mera existencia.
- **OpenMythos / capa de persistencia** existe como requisito/estructura histórica; su integración real debe auditarse antes del cierre global.
- PluginBus dinámico no se considera seguro/integrado hasta aislamiento/guardas + prueba.

## 3. Objetivos operativos O01–O11
1. **O01** LOOP/watchdog + checkpoint + STATE + Crazy Wall + recovery.
2. **O02** investigar código fuente necesario en repos autorizados y OSS.
3. **O03** copiar/reusar código faltante por SHA.
4. **O04** Ficha/contrato → adapter/plugin → registry → health → evidence.
5. **O05** verificación documental 5 pasadas y GAP ledger.
6. **O06** contratos de tareas de agentes.
7. **O07** integrar/espejar agentes de programación/auditoría.
8. **O08** HF/3 procesadores con health y prueba real.
9. **O09** Graphiti/Grapify/SQL/HF storage por contratos/adapters.
10. **O10** APIs/modelos por `secret_ref`, budget, timeout, fallback, health.
11. **O11** tests unit/integration/E2E, recovery/idempotencia, auditoría/cierre.

Estado: O01–O03 `VERIFIED_CLOSED`; O04 `IN_PROGRESS_T16`; O05–O11 `PENDING`.

## 4. Plan vigente T01→T30
| Tarea | Objetivo | Trabajo | Estado |
|---|---|---|---|
| T01 | O02 | Reconciliar anclas/objetivo/roles | VERIFIED_CLOSED |
| T02 | O02 | Consolidar inventario candidato | VERIFIED_CLOSED |
| T03 | O02 | Verificar runner 1×1 | VERIFIED_CLOSED |
| T04 | O02 | Verificar pause/resume | VERIFIED_CLOSED |
| T05 | O02 | Verificar identidad/reinyección | VERIFIED_CLOSED |
| T06 | O02 | Verificar input_hash/node/attempt/checkpoint | VERIFIED_CLOSED |
| T07 | O02 | Verificar StrategyDelta/failure-memory | VERIFIED_CLOSED |
| T08 | O02 | Mapear candidatos a destino | VERIFIED_CLOSED |
| T09 | O02 | Provenance/compatibilidad/imports | VERIFIED_CLOSED |
| T10 | O03 | Integrar cola 1×1 | VERIFIED_CLOSED |
| T11 | O03 | Integrar pause/resume | VERIFIED_CLOSED |
| T12 | O03 | Integrar identidad/checkpoint | VERIFIED_CLOSED |
| T13 | O03 | Integrar input_hash/node_state | VERIFIED_CLOSED |
| T14 | O03 | Integrar StrategyDelta guard | VERIFIED_CLOSED |
| T15 | O03 | Patches quirúrgicos + tests | VERIFIED_CLOSED |
| T16 | O04 | Ficha Contract v2 de 4 capacidades | EN_CURSO |
| T17 | O04 | Cablear adapters/plugins a registry | PENDIENTE |
| T18 | O04 | Health/evidence/fail-closed | PENDIENTE |
| T19 | O05 | 5 pasadas docs↔arquitectura↔code↔contracts↔tests | PENDIENTE |
| T20 | O06 | Contratos de tareas de agentes | PENDIENTE |
| T21 | O07 | Cablear OpenCode | PENDIENTE |
| T22 | O07 | Cablear OpenHands | PENDIENTE |
| T23 | O07 | Cablear Claude Code + Mimo Code | PENDIENTE |
| T24 | O07 | Auditores + Council12 + embudo | PENDIENTE |
| T25 | O08 | HF/3 procesadores | PENDIENTE |
| T26 | O09 | Graphiti/Grapify/SQL/HF storage | PENDIENTE |
| T27 | O10 | APIs/modelos por secret_ref | PENDIENTE |
| T28 | O11 | Tests unit/integration/E2E | PENDIENTE |
| T29 | O11 | estabilidad ×10 + recovery/idempotencia | PENDIENTE |
| T30 | O11 | auditoría final + verify_final + decidir cierre o crear siguiente lote30 | PENDIENTE |

Regla post-T30: si cualquier O01–O11, GAP arquitectónico o E2E sigue abierto, generar siguiente lote de 30 tareas desde evidencia real pendiente; no reiniciar numeración ni borrar historial.

Plan canónico:
https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20Wordflow%20LOOP%20Yaiwes/Crazy%20Wall%20Orquestador/PLAN-LOOP-30-TAREAS.md

## 5. Componentes SELECTED / implementados
### C01 Serial dispatch 1×1
- Fuente: `maxbry123-commits/Agentes-motores-Wordflow-YAIWES/Loop Engineer/Loop-Engineer/loop/runner.py`
- Blob: `daa32a5d6dfeb0d21a975b8a5b8384d68a8aa08e`
- URL: https://github.com/maxbry123-commits/Agentes-motores-Wordflow-YAIWES/blob/main/Loop%20Engineer/Loop-Engineer/loop/runner.py
- Destino: `Agente Yaiwes principal/execution-orchestration/deterministic-execution/serial_dispatch.py`
- Blob destino: `77017b70239cedcce26f1df4a076272572f0927b`
- Estado: `VERIFIED_CLOSED`.

### C02 Pause/resume event-sourced
- Fuente: `.../loop/runcontrol.py`
- Blob: `2c6aff845c97b600d4b3851b5ee9a6e0ee23defb`
- URL: https://github.com/maxbry123-commits/Agentes-motores-Wordflow-YAIWES/blob/main/Loop%20Engineer/Loop-Engineer/loop/runcontrol.py
- Destino: `Agente Yaiwes principal/state-events-durability/checkpoint-recovery/run_control_adapter.py`
- Blob destino: `aa4f62571044d873e3969bc7f747bfc83e3047a6`
- Estado: `VERIFIED_CLOSED`.

### C03/C04 Resume identity + input_hash/node/attempt/checkpoint
- Fuente patrón: `dta-au/elspeth` commit `720d441336434d227c2a00caaac100db48a07d5c`.
- `identity.py` blob `98b791e350e3a2829fb2c2977cc0fbc25beb4321` — https://github.com/dta-au/elspeth/blob/720d441336434d227c2a00caaac100db48a07d5c/src/elspeth/contracts/identity.py
- `audit.py` blob `c89a5d9d2354ae549845aeab9a90cc3ab14f853e` — https://github.com/dta-au/elspeth/blob/720d441336434d227c2a00caaac100db48a07d5c/src/elspeth/contracts/audit.py
- Destino: `Agente Yaiwes principal/state-events-durability/checkpoint-recovery/resume_identity.py`
- Blob destino: `dc440bd180194d6cef2bf1b38b1ef1b85138ef0b`
- Estado: `VERIFIED_CLOSED`.

### C05 StrategyDelta / no retry idéntico
- Fuente patrón: `Alex-v-p/indexer-core` commit `efcfcb20f09117504b00f682ada1bfff2b04b649`.
- Ruta: `packages/rag_core/retrieval/retry/rules.py`
- Blob: `7704a6bd73d8b073df88651bbaf232f1f3dbfd6b`
- URL: https://github.com/Alex-v-p/indexer-core/blob/efcfcb20f09117504b00f682ada1bfff2b04b649/packages/rag_core/retrieval/retry/rules.py
- Destino: `Agente Yaiwes principal/control-governance/strategy_delta_guard.py`
- Blob destino: `46efd22bd7b5ac3c22cc5ca084788d46b4b5b16b`
- Estado: `VERIFIED_CLOSED`.

### Test T10–T15
- `Agente Yaiwes principal/tests/test_plan30_loop_runtime.py`
- Blob `e1b1e3a4e4ca79e5dee00d5676a6038c6426bc31`
- Commit `3b7f0cec153ef03656f76dcd693c17fe061f7a78`
- Resultado registrado: `5 passed in 0.06s`.
- Evidence blob `f8a5db43fb0cc9e1712620c75b579229c7bad14a`.

## 6. Ficha Contract v2 — T16
Validador canónico:
- Path `skills/research-download-chain/assets/plugin-bus/ficha_contract_v2.py`
- Commit `37bef3a8a8f6dadca067638b8ea0c32995fc1d63`
- Blob `b27f14b4d64f77bccf53a893c49b6f20bd58e745`
- URL https://github.com/maxbry123-commits/agentes/blob/37bef3a8a8f6dadca067638b8ea0c32995fc1d63/skills/research-download-chain/assets/plugin-bus/ficha_contract_v2.py

Fichas:
- serial_dispatch `bc885059ed0a97f73aad02572853d1b0a4f8117d`
- run_control `7fdb64b7a21fe51c278dcc907b09eb800f2a2770`
- resume_identity `4ce82a32faa939177dd22603f097402e9b9e6ed9`
- strategy_delta `44aeb5cb48db6d42499bc940e47e912942d7fd40`
- provenance schema `5c3aa0b42fb9737baeb1f151a933fa83cc72c27d`
- provenance registry `5274c96b79a4862d4081be18b80c1c0b09d9607a`

Estado: `EN_CURSO`; falta ejecución exacta 4/4 + stdout/veredicto + path cross-check.

## 7. REFERENCE / dependency context — Loop Engineer
No se consideran integrados por presencia:
- `runtime.py` `6c3af6b9b40d1061cc34647cffd4f47bfb6ac477`
- `reducer.py` `4860716a67238f9c9436ce5ca4a667731f3286d1`
- `verifier.py` `2ae7afab38dd724527278a1a2f7ad1259504961e`
- `plan.py` `b6f96302042cb1651c6fb6f8f990963d50c13b99`
- `events.py` `91a8cc9018d58eca739e5a28be2a6a78e3af4458`
- `evidence.py` `b56f61da7e10ce8458d1258f5893b175e49cd643`
- `fsm.py` `0e757ea505cd19ceb569a6bb480b4cb9f8878327`
- `completion.py` `62fcca7a160a62728d415575b835c6c7d3d8f9b9`
- `chain.py` `97a044066566c54409f77b9304a4b66161efe76c`
- `contract.py` `d17350025b5263db8ec0eeffba02e00febc87df8`
- `emit.py` `cbadda36592b158862e3401e66de1a71a8d7fc87`

## 8. REFERENCE/PATTERN — Elspeth adicional
Commit `720d441336434d227c2a00caaac100db48a07d5c`:
- `transform.py` blob `89f79150c0c0f31ab25f3d40d41908f48557d343`
- `node_states.py` blob `6333f7d0e708006fb69e564d828fd4571203b3c7`
- `test_resume_offset_propagation.py` blob `84be0a07639bc24612eb3ab2f44bb5c138474874`
- `test_recorder_node_states.py` blob `0f29b7fe3d0d8211e29268b45741afbc3e8f5ab4`
Decisión: patrones/auditoría, no copiar framework completo.

## 9. REJECTED_AS_PRIMARY / REFERENCE_ONLY — Supreme-Agent
Commit `aae277a05c5f20526443933c14fe93e1e200913f`:
- `src/core/models.py` blob `567939c73a6056a795fa24e21791914928862e1c`
- `src/core/post_execution/feedback.py` blob `0060950ff9317c27e9b68857ea07f5023b25c25d`
- `src/core/planner.py` blob `2eb1fbf4e4d61467fa5abdbfe2028f83c4b210be`
- `tests/test_post_execution.py` blob `c74808c43015b59f6b664056fc853ecd0bd5e567`
Motivo: memoria de estrategias útil, pero no garantiza por sí sola `delta_hash` materialmente distinto antes del retry.

## 10. GAPs/global backlog detectado por X-Ray que T30 debe resolver o trasladar al siguiente lote
1. T16 validador Ficha v2 exacto 4/4.
2. T17 registry/adapters/plugins real.
3. T18 health/evidence/fail-closed real.
4. T19 verificación documental 5 pasadas.
5. T20 task contracts agentes.
6. T21–T24 fleet/council bindings + health/tests.
7. T25 HF/3 processors real.
8. T26 storage Graphiti/Grapify/SQL/HF real.
9. T27 APIs/modelos secret_ref/health/budget/timeout/fallback.
10. T28 E2E documento→code→plugin→verify.
11. T29 stability/recovery/idempotencia/no duplicate effects.
12. T30 auditoría final.
13. Auditoría de las **105 capacidades deterministas** y prueba de registry/runtime antes de cierre global.
14. Auditoría/cableado real de **OpenMythos/capa persistencia** si sigue siendo requisito activo.
15. Verificar PluginBus/ejecución dinámica con aislamiento/guards/tests.
16. Confirmar Council12 completo; Qwen Code CLI solo pasa de candidato a miembro con evidencia.
17. Si cualquier punto queda abierto: crear siguiente lote de 30 y continuar LOOP.

## 11. Arquitectura destino
`documentos/inputs → contracts/schema/DSL/DAG → Sheriff/Validator → kernel determinista → execution-orchestration → Ficha/adapter/plugin → Capability Registry → engine/agente → state-events-durability → evidence/audit → verify_final`.

Capas físicas:
- `code-programming-engine/`
- `kernel-principal/`
- `execution-orchestration/`
- `control-governance/`
- `state-events-durability/`
- `execution-engine-pool/`
- `reasoning-kernel/`
- `research-evidence/`
- `tools-models-memory-knowledge/`
- `tests/`

No monolito: separar `contracts/adapters/plugins/registry/loader/guards/tests`.

## 12. Cierre global
Solo `VERIFIED_CLOSED` cuando exista evidencia E2E:
`documento → requisito → task contract → engine/agente → código → repair → Ficha/plugin/registry → ejecución real → auditoría → test independiente → STATE/CHECKPOINT/evidence → output`.

Estado actual: `15/30 VERIFIED_CLOSED = 50%`; T16 `EN_CURSO`; T17–T30 `PENDIENTE`; estado global `ACTIVE_LOOP`.