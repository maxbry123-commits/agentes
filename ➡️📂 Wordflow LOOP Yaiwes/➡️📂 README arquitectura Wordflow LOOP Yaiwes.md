# ➡️📂 README arquitectura Wordflow LOOP Yaiwes

Contrato operativo: `tel.workflow/v4`  
Modo: `FAIL_CLOSED_EXECUTION_LOOP`  
Arquitectura: modular, determinista por defecto, no monolítica.  
Estado actual: `ACTIVE_3STEP_AGENT_INTEGRATION`  
Nodo actual: `STEP1_AGENT_INDEX`  
Cola: `1×1`.

> Arquitectura detallada anterior preservada por blob `ee34fe643320b7ba8da5c8e26e79c3b417e8b750`. Esta reconciliación compacta el estado operativo actual sin borrar la trazabilidad histórica del repositorio.

## 1. Objetivo final
`documentos/proyectos YAIWES → requisitos trazables → task contracts → código/agentes → Ficha/adapter/plugin → Capability Registry/binding → ejecución/repair → auditoría/tests → STATE/CHECKPOINT/evidence → E2E verificable`.

El Wordflow LOOP es el motor persistente que mantiene el trabajo hasta cierre real.

## 2. Método operativo
Guía canónica:
`➡️📂 Wordflow LOOP Yaiwes/GUIA-MAESTRA-EJECUCION-LOOP-V4-WORDFLOW-YAIWES.md`.

Leyes:
- estado real > memoria/chat > inferencia;
- sin evidencia = GAP;
- archivo presente ≠ integrado;
- código escrito ≠ ejecutado;
- mock ≠ runtime real;
- `NO_FORCE_GIT`;
- `NO_MONOLITO`;
- `NO_REHACER_TRABAJO_VERIFICADO`.

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
`Task Contract → engine binding → agente ejecutor/revisor/auditor → resultado normalizado → evidence`.

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
### LOOP5
- LangGraph
- Temporal Python SDK
- Prefect
- Hatchet Python SDK
- redun

### Evidencia física
- MOVE a estructura final: commit `26d0860ef23c3285ee60c63a5c9121fa45bb0ed1`.
- Wiring runtime mediante Enchufe Universal: commit `da290e6200c9e82154ed917ce6bbc6194d423da3`.
- Evidencia de trigger real: `Agente Yaiwes principal/kernel-principal/extension-kernel/capability-registry/wordflow-loop-evidence/STEP3_PROGRAMMING_TRIGGER.json`.
- Commit evidencia: `ebac5c5b10d03d5e828e8fae266af88eb7b9b3d3`.
- Run: `34179064259`.
- Resultado: `PASS_REAL`, `registry_active=11`, `engine_binding=yaiwes.loop.loop_engineer`, `sum/normalize/classify=3/3 completed`, idempotencia PASS, fail-closed invalid profile PASS.
- T16 Ficha Contract v2: run `34075371938`, `YAIWES_T16_CANONICAL_VERIFY=PASS 4/4`.

## 5. PARCHE ACTIVO DEL DIRECTOR — EXACTAMENTE 3 PASOS

### PASO 1 — Índice de agentes
Origen: `maxbry123-commits/Agentes-motores-Wordflow-YAIWES`.

Acciones autorizadas:
- ubicar agentes/componentes existentes;
- no revisar su código;
- crear `➡️📂 readme indice agentes.md` en `main`;
- registrar nombre y función/rol general.

**Sin cableado. Sin tests.**

### PASO 2 — Lista adicional + cableado 1×1
- Mostrar al Director otros agentes del repo que puedan aportar al Wordflow LOOP.
- Seleccionar únicamente los necesarios.
- Cablear 1×1 por el Enchufe Universal existente:
  `Task Contract/Ficha → adapter/plugin → registry/binding → health descriptor`.
- No crear un bus paralelo.
- No ejecutar tests.
- Tras cada cableado relevante actualizar: arquitectura + STATE + CHECKPOINT + PLAN + RECOVERY + BITÁCORA + HANDOFF.
- Entregar enlaces visibles de archivos y bindings.

### PASO 3 — Test final
Solo cuando el Paso 2 esté materialmente terminado:
- lanzar workflow/trigger real del Wordflow LOOP;
- comprobar bindings, ejecución, fail-closed y evidencia;
- cerrar con run/job/status/conclusion/SHA/log/evidence.

**No existe Paso 4 dentro de este parche.**

## 6. Agentes objetivo del Director
1. OpenCode — writer/executor.
2. OpenHands — review/repair.
3. Claude Code — flow/execution/wiring review + auditoría.
4. MiMo Code — flow/execution/wiring review + auditoría.
5. Codex / Codex CLI — implementación/debugging/auditoría.
6. Cline — agente de programación; clasificar por inventario en Paso 1.
7. Kimi K Code CLI — programación/revisión/Council.
8. Hermes — worker auxiliar + auditor.
9. OpenClaw — coordinador/worker auxiliar + auditor.
10. Aider — edición/programación repo + Council.
11. Muse / Glimmer Code — programación/revisión alternativa + Council.
12. Smolagents / Smolange — auditor/revisión adicional.
13. Qwen Code CLI / GLM Code — programación/contraste sujeto a presencia real.
14. Goose — investigador/auxiliar; clasificar por inventario en Paso 1.

`nombre/carpeta presente ≠ binding integrado`.

## 7. Hugging Face
Estado comunicado por el Director: `EN CURSO` fuera de este parche.

Regla: no tocar ni probar HF hasta que el Director indique que está listo.

## 8. PLAN30 histórico y mapeo del parche
La evidencia histórica conserva T01–T16 `VERIFIED_CLOSED`. El snapshot PLAN30 anterior mantenía T17 activo y T18–T30 pendientes. La evidencia posterior del MOVE/wiring/trigger runtime no debe rehacerse.

Para el bloque actual:
- Paso 1 prepara inventario para O06/O07.
- Paso 2 ejecuta el binding de agentes de O06/O07/T20–T24 que resulten necesarios.
- Paso 3 cubre el test/verify del bloque actual y alimenta O11/T28–T30.
- T25/HF espera señal del Director.
- T26/T27 no se ejecutan dentro de este parche salvo nueva instrucción literal.

## 9. Prohibiciones actuales
`NO_STEP_4`  
`NO_NEW_OSS_RESEARCH`  
`NO_REDOWNLOAD_LOOP5`  
`NO_CODE_REVIEW_STEP1`  
`NO_TEST_STEP1_STEP2`  
`NO_PARALLEL_ARCHITECTURE`  
`NO_FORCE_GIT`  
`NO_FALSE_PASS`.

## 10. Fuentes de verdad / recovery
Orden:
1. `HANDOFF.md`.
2. guía v4.
3. este README arquitectura.
4. `Crazy Wall Orquestador/STATE.json`.
5. `CHECKPOINT.json`.
6. `PLAN-LOOP-30-TAREAS.md`.
7. `RECOVERY-PATCH.md`.
8. `BITACORA-CRAZY-WALL.md`.
9. HEAD real / evidencia exacta del paso activo.

Divergencia = GAP; nunca degradar evidencia posterior por un snapshot antiguo.

## 11. Siguiente acción exacta
`STEP1_AGENT_INDEX`: revisar únicamente el inventario/nombres del repo `Agentes-motores-Wordflow-YAIWES` y crear `➡️📂 readme indice agentes.md`; no inspeccionar código y no ejecutar tests.

## 12. Enlaces canónicos
- HANDOFF: https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20Wordflow%20LOOP%20Yaiwes/HANDOFF.md
- STATE: https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20Wordflow%20LOOP%20Yaiwes/Crazy%20Wall%20Orquestador/STATE.json
- CHECKPOINT: https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20Wordflow%20LOOP%20Yaiwes/Crazy%20Wall%20Orquestador/CHECKPOINT.json
- PLAN: https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20Wordflow%20LOOP%20Yaiwes/Crazy%20Wall%20Orquestador/PLAN-LOOP-30-TAREAS.md
- RECOVERY: https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20Wordflow%20LOOP%20Yaiwes/Crazy%20Wall%20Orquestador/RECOVERY-PATCH.md
- BITÁCORA: https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20Wordflow%20LOOP%20Yaiwes/Crazy%20Wall%20Orquestador/BITACORA-CRAZY-WALL.md
