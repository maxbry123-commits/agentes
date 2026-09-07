# ➡️📂 README arquitectura Wordflow LOOP Yaiwes

Contrato: `tel.workflow/v3`  
Modo: `FAIL_CLOSED_LOOP`  
Arquitectura: modular, determinista por defecto, no monolítica.  
Estado: `ACTIVE_LOOP / PLAN30_T16_FICHA_CONTRACTS`  
Progreso verificado: `15/30 = 50%`.

## 1. Fuentes de verdad / orden de lectura
1. `HANDOFF.md`.
2. Este README arquitectura actual.
3. README histórico `➡️📂 readme wordflow loop Yaiwes.md` — ledger literal/recuperación.
4. `Crazy Wall Orquestador/TRAZABILIDAD-PROYECTO-WORDFLOW-YAIWES.md` — X-Ray source→SHA→destino→evidencia + 5 pasadas chat.
5. `STATE.json`.
6. `CHECKPOINT.json`.
7. `RECOVERY-PATCH.md`.
8. `BITACORA-CRAZY-WALL.md`.
9. `PLAN-LOOP-30-TAREAS.md`.
10. evidencia exacta del nodo activo.

Divergencia entre anclas = `GAP`; reconciliar antes de mutar.

## 2. Objetivo final
`documentos/proyectos YAIWES → requisitos trazables → tareas de programación → reutilización/generación de código → Ficha/contrato → adapter/plugin → registry → agente/engine → ejecución → verification/repair → auditoría → STATE/CHECKPOINT/evidence → E2E verificable`.

El LOOP es el motor persistente que mantiene el trabajo hasta cierre real.

## 3. LOOP1 global + LOOP2 por tarea
### LOOP1 global
En cada salida/corrida actualizar: objetivos, tareas cerradas/en curso/pendientes, GAP/flags, evidencia, cambios y siguiente nodo 1×1.

### LOOP2 por tarea — cadena operacional
1. INPUT_BLOCK literal, sin reinterpretar.
2. GOALS 12/12 entrada.
3. 2 prioridades.
4. plan.
5. cola 1×1.
6. delta autorizado.
7. verify/refute + análisis.
8. fallo → LOOP, no falso cierre.
9. auditor instrucciones ×3.
10. GAP → investigar mínimo 10 vías y hasta 20 soluciones.
11. seleccionar StrategyDelta materialmente distinto.
12. comunidad/code como señal secundaria si fuentes oficiales no bastan.
13. Council/Ask Consil 12 pasos.
14. 12 pasos de investigación intensiva en GAP complejo.
15. 6 cuestionamientos de causa.
16. ejecutar solución permitida.
17. verificar cumplimiento INPUT + LOOP.
18. 3 refutaciones: INPUT, tarea/objetivos, LOOP.
19. cross-check global.
20. checklist/CODA.
21. `verify_final`; si falla, reinyección LOOP.

Política FLAG: bloqueo `🚩` permanece abierto; solo continuar otra tarea segura si no viola dependencias.

Prioridad de implementación: `REUSE > COPY/MOVE > PATCH QUIRÚRGICO > ADAPTER > GENERATE`.

## 4. Watchdog / Sentinela / Supervisor / Guardián
Salida obligatoria de 10 líneas:
1. avance % verificado;
2. nodo actual;
3. # cerradas;
4. # en curso;
5. # pendientes;
6. # GAP/flags;
7. evidencia nueva;
8. cambios desde corrida anterior;
9. siguiente acción 1×1;
10. mini resumen Director + `VERIFIED_CLOSED | CLOSED_UNVERIFIED | INCONCLUSIVE | ACTIVE_LOOP`.

No inflar porcentaje. Presencia ≠ integración.

## 5. Arquitectura por capas
### A — Input / documentos / Mission + GoalLock
`INPUT literal → schema → MissionContract → GoalLock → provenance`.

### B — DSL / DAG / contratos
`requisito → DSL → DAG → deps → Ficha/contrato → success/failure criteria`.

### C — Sheriff / gobierno
`contract → Sheriff → Validator → guards → policy → delta autorizado`.

### D — Kernel determinista
`event loop → scheduler → runtime → registry/router → state`; kernel/control `0% LLM`.

### E — Execution orchestration
`cola1×1/DAG-ready → execution manifest → capability select → dispatcher → checkpoint/recovery`.

### F — Enchufe universal
`Ficha v2 → adapter/plugin → Capability Registry → loader → health → evidence`.

### G — Code programming engine / agentes
`task contract → engine binding → OpenCode execute → OpenHands review/repair → Claude/Mimo wiring review → auditors/council`.

### H — Reasoning on demand
`determinista? → algoritmo/capability code; si insuficiente → reasoning/model por contrato`.

### I — State/events/durability
`input_hash + node_id + checkpoint + attempt + strategy/delta → store → recovery/idempotencia`.

### J — Memory/storage/tools/models
`Graphiti/Grapify/SQL/HF storage + APIs secret_ref + budget/timeout/fallback`.

### K — Research/evidence/audit
`fuente→URL/SHA → EvidencePacket → tests → refutaciones → cross-check → verify_final`.

### L — Output/E2E
`documento→tarea→code→plugin→registry→ejecución→repair→audit→state/evidence→salida`.

Separación obligatoria: `contracts/ adapters/ plugins/ registry/ loader/ guards/ tests/`.

## 6. Diseño aprobado adicional que no puede perderse
- Catálogo de **105 capacidades/algoritmos deterministas**: capacidades Python reales, no prompts. Antes del cierre global se debe demostrar su inventario/registry/runtime o registrar GAP explícito.
- Ruta conceptual candidata histórica: `reasoning_kernel/decision_on_demand/reasoning_modules/`.
- `ejecucion.kind: code` para capacidades deterministas; `ejecucion.kind: llm` solo cuando no exista solución determinista suficiente.
- `SKILL-CLASIFICAR-UBICAR-RECICLAR-CODE`: clasificar → ubicar → localizar/reutilizar → validar procedencia/licencia/contrato → Ficha → plugin → test → evidence.
- Capa/estructura **OpenMythos/persistencia** debe ser auditada para determinar si está realmente integrada antes del cierre global.
- PluginBus dinámico no se declara seguro/integrado hasta aislamiento/guardas/tests.

## 7. Objetivos O01–O11
| Objetivo | Definición | Estado |
|---|---|---|
| O01 | LOOP/watchdog + checkpoint/STATE/Crazy Wall/recovery | VERIFIED_CLOSED |
| O02 | investigación de código fuente | VERIFIED_CLOSED |
| O03 | copy/reuse por SHA | VERIFIED_CLOSED |
| O04 | Ficha→adapter/plugin→registry→health→evidence | IN_PROGRESS_T16 |
| O05 | verificación documental 5 pasadas | PENDING |
| O06 | task contracts agentes | PENDING |
| O07 | integrar agentes/council | PENDING |
| O08 | HF/3 procesadores | PENDING |
| O09 | Graphiti/Grapify/SQL/HF storage | PENDING |
| O10 | APIs/modelos secret_ref | PENDING |
| O11 | tests/auditoría/E2E | PENDING |

## 8. Plan T01→T30
T01–T15 `VERIFIED_CLOSED`; T16 `EN_CURSO`; T17–T30 `PENDIENTE`.

T16: Ficha Contract v2 4 capacidades.  
T17: adapters/plugins→registry.  
T18: health/evidence/fail-closed.  
T19: 5 pasadas docs↔arquitectura↔code↔contracts↔tests.  
T20: task contracts agentes.  
T21: OpenCode.  
T22: OpenHands.  
T23: Claude Code + Mimo Code.  
T24: auditores + Council12 + embudo.  
T25: HF/3 procesadores.  
T26: Graphiti/Grapify/SQL/HF storage.  
T27: APIs/modelos secret_ref.  
T28: tests unit/integration/E2E.  
T29: estabilidad ×10 + recovery/idempotencia/no duplicate effects.  
T30: auditoría final + verify_final + **cerrar proyecto solo si no queda GAP; de lo contrario generar siguiente lote de 30**.

Regla de continuidad: al terminar T30, si cualquier objetivo/GAP/E2E permanece abierto, crear `T31–T60` desde evidencia real pendiente; después repetir lotes de 30 hasta `VERIFIED_CLOSED` global. No borrar historial ni reiniciar numeración.

## 9. Componentes integrados y provenance
1. Serial dispatch: `runner.py` blob `daa32a5d6dfeb0d21a975b8a5b8384d68a8aa08e` → `serial_dispatch.py` blob `77017b70239cedcce26f1df4a076272572f0927b`.
2. Pause/resume: `runcontrol.py` blob `2c6aff845c97b600d4b3851b5ee9a6e0ee23defb` → `run_control_adapter.py` blob `aa4f62571044d873e3969bc7f747bfc83e3047a6`.
3. Resume identity/input hash: Elspeth commit `720d441336434d227c2a00caaac100db48a07d5c` → `resume_identity.py` blob `dc440bd180194d6cef2bf1b38b1ef1b85138ef0b`.
4. StrategyDelta: indexer-core commit `efcfcb20f09117504b00f682ada1bfff2b04b649` → `strategy_delta_guard.py` blob `46efd22bd7b5ac3c22cc5ca084788d46b4b5b16b`.
5. Test T10–T15: `test_plan30_loop_runtime.py` blob `e1b1e3a4e4ca79e5dee00d5676a6038c6426bc31`; resultado `5 passed in 0.06s`.

Trazabilidad forense completa SELECTED/REFERENCE/REJECTED:
https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20Wordflow%20LOOP%20Yaiwes/Crazy%20Wall%20Orquestador/TRAZABILIDAD-PROYECTO-WORDFLOW-YAIWES.md

## 10. T16 — Ficha Contract v2
Validador canónico:
https://github.com/maxbry123-commits/agentes/blob/37bef3a8a8f6dadca067638b8ea0c32995fc1d63/skills/research-download-chain/assets/plugin-bus/ficha_contract_v2.py

Commit `37bef3a8a8f6dadca067638b8ea0c32995fc1d63`; blob `b27f14b4d64f77bccf53a893c49b6f20bd58e745`.

Fichas:
- serial_dispatch `bc885059ed0a97f73aad02572853d1b0a4f8117d`
- run_control `7fdb64b7a21fe51c278dcc907b09eb800f2a2770`
- resume_identity `4ce82a32faa939177dd22603f097402e9b9e6ed9`
- strategy_delta `44aeb5cb48db6d42499bc940e47e912942d7fd40`

GAP: falta ejecución exacta del validador 4/4 + stdout/veredicto + path cross-check; T17 bloqueado hasta cierre.

## 11. Agentes / Council
- OpenCode: writer/executor.
- OpenHands: review/repair.
- Claude Code + Mimo Code: flow/execution/wiring review.
- Auditores: Claude Code, Mimo Code, Codex, Smolange, Hermes, OpenClaw.
- Council adicional: Aider, Muse/Glimmer Code, Kimi K Code CLI.
- 12.º candidato: **Qwen Code CLI**, pendiente evidencia/autorización real.
- Embudo: OpenHands + OpenCode.

Presencia de agente ≠ binding/integración.

## 12. Fuentes / adquisición OSS
Orden: chat/historial → componentes locales → repo `agentes` → `Agentes-motores-Wordflow-YAIWES` → router-universal → osquestador-auditor → repo/docs oficiales → comunidad secundaria.

Antes de programar: `repo+ruta+URL+commit/blob SHA+comportamiento+destino+decisión`.

Skill autorizado:
https://github.com/maxbry123-commits/agentes/tree/c789e5fe635e220230ffc759d86dc3bbb8e261d4/skills/skills%20Github%20acci%C3%B3n

No LFS; no reactivar workflows viejos; validar destino; `verify_final`.
Plugins externos autorizados por este proyecto: GitHub y Hugging Face únicamente, salvo autorización literal posterior.

## 13. Anti-alucinación / refutación
Antes de avanzar responder con evidencia:
1. ¿inventé algo?
2. ¿seguí INPUT literal?
3. ¿revisé fuentes de verdad?
4. ¿sigo plan/objetivo?
5. ¿verify/refute de lo realizado pasó?

Si se pierde rumbo: reconstruir contexto desde `HANDOFF + README + STATE + CHECKPOINT + RECOVERY + BITACORA` y retomar último checkpoint válido.

## 14. Persistencia
Cada cambio real reconcilia según alcance:
`BITACORA + STATE + CHECKPOINT + PLAN + RECOVERY + README/HANDOFF`.

Registro mínimo:
`node_id + input_hash + checkpoint_id + attempt_id + strategy_id + delta_hash + cause + source_url + source_sha + destination + test/log + outcome`.

## 15. Cierre global
Solo `VERIFIED_CLOSED` cuando exista:
`documento → requisito → task contract → engine/agente → código → repair → Ficha/plugin/registry → ejecución real → auditoría → test independiente → STATE/CHECKPOINT/evidence → output`.

Si falta evidencia: `GAP/INCONCLUSIVE`, nunca falso PASS.