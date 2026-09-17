# PLAN LOOP — Wordflow LOOP Yaiwes

Contrato: `tel.workflow/v4` · modo `FAIL_CLOSED_EXECUTION_LOOP`.  
Raíz única autorizada: `maxbry123-commits/agentes/➡️📂 Wordflow LOOP Yaiwes/`.

## Histórico cerrado
El cierre local de 3 pasos se conserva como evidencia histórica y no se repite: fleet=18, Council12=12, fail-closed local, router prioridad/failover y persistencia fueron probados. `AUTH_PROVIDER_TEST_PENDING` continúa abierto para ejecución autenticada externa.

# Plan activo — CODE_GRAPH_ARCHITECTURE_PROGRAMMING_LOOP
Checkpoint canónico: `WFLOOP-CODE-GRAPH-20260911-0010`  
Nodo actual: `CG18_FABLES_CANONICAL_BINDING_G018`.

## Cola determinista actualizada
1. `G-018`: verificar source proof + Ficha/contract + registro/test del Enchufe Universal Fables.
2. `G-006`: reabrir únicamente cuando G-018 quede verificado; política de creación de code nuevo posterior al gate G-005.
3. `G-007/G-008/G-009`: ingesta de code existente, seguridad/neutralización y `NO_VALUE_GAP`.
4. `G-017/G-022/G-024`: deployment real, sandbox enforceable, reviewer y separación determinismo/LLM.
5. `G-014/G-030`: memorias 18 agentes y Crazy Wall concurrency.
6. `G-011/G-012`: motores canónicos, intake de componentes/listas, hash/read-back.
7. `G-026/G-027/G-028/G-029`: UI/Graphiti/Graphology/planificación solo ante GAP concreto y sin duplicar DAGEngine.
8. `G-023`: HF bridge solo con acceso real y sin exponer secretos.

## Cerrados verificados
- `G-001`: CODE GRAPH workspace determinista.
- `G-002`: auditoría de archivo + Council normalizado sin autoridad ejecutiva.
- `G-003`: task graph determinista; `director_tasks` y `generated_tasks` separados.
- `G-004`: placement classifier A–G + `PLACEMENT_REVIEW_REQUIRED`.
- `G-005`: reuse selector `runtime/src/core/reuse_selector.py` blob `bc7f4805fc7f13e6de0341b84c533d4b7fb6b044`; catálogo `reuse_catalog_g005.json` blob `2367f7ed8c7e1ece1d724f15f6494d5ff56543f8`; evidence `G005_REUSE_SELECTOR_2026-09-11.json`.
- `G-010`: Watchdog supervisor.
- `G-013`: reconciliador de fuentes `yaiwes.truth_reconciliation/v1`; `PASS_8_OF_8` read-back + `PASS_7_OF_7` simulación equivalente; evidence `G013_CANONICAL_RECONCILIATION_2026-09-11.json`.
- `G-020`: 12 fuentes de comunidad/desarrollo.

## Política G-005 vigente
`REUSE > PATCH > ADAPT > GENERATE`. Máximo 10 candidatos por decisión; source/licencia/mantenimiento/compatibilidad/riesgo/footprint obligatorios. Candidato externo requiere `ADAPT`, nunca ejecución directa. Para `dag`, `DAGEngine` local es REUSE por defecto; NetworkX no reemplaza scheduler sin GAP demostrado. Graphiti/Graphology siguen en investigación y no están integrados.

## G-013 cerrado
El parser histórico acepta un único marcador explícito `Checkpoint canónico:` y rechaza marcadores canónicos conflictivos. Las ocho fuentes requeridas convergieron en `0010`. `repo_pytest_execution=NOT_CLAIMED`; el cierre es local/reproducible, no PASS externo.

## Paralelismo permitido
Fan-out solo entre tareas independientes y con ownership explícito. Dependencias bloqueantes del DAG no se saltan. Mantener `director_tasks` y `generated_tasks` separados; dedup/idempotency/backpressure obligatorios antes de aumentar concurrencia.

## Regla de cierre
Cada GAP requiere source/provenance + decisión + implementación cuando corresponda + test/simulación + read-back/commit + persistencia. Presencia de archivo no equivale a PASS. `AUTH_PROVIDER_TEST_PENDING` permanece abierto hasta evidencia autenticada real.

# CIERRE ACTIVO — CLOSURE-2026-09-17

Estado: `ACTIVE / CL-002 IN_PROGRESS`. El histórico G-001..G-030 permanece cerrado y no se reabre por este plan.

## X-Ray forense fresh
- Raíz del proyecto: 16 componentes directos.
- `agent_sources`: 20 árboles de fuente + manifiesto; 18 pertenecen al fleet registrado y 2 son Meta auxiliares.
- Fleet: 18 agentes registrados; presencia de source **no** equivale a runtime PASS.
- Adapters observados: `browser_use_adapter.py`, `codebase_memory_mcp_adapter.py`.
- Core observado: 38 módulos directos en `runtime/src/core`.

## Mapa de integración
- **Control/orquestación:** Crazy Wall + TASK-NODES + STATE + CHECKPOINT + BITÁCORA + HANDOFF.
- **Core:** runtime/core + contracts + workflows + adapters + plugins + skills; reutilizar `event_bus.py`, `dag_engine.py`, `component_intake.py`, `reuse_selector.py`, `completion_gate.py` y gates existentes; prohibido crear bus paralelo.
- **Fleet existente (18):** conservar registro y roles; sólo ampliar tras pruebas de transporte/runtime.
- **Meta:** `meta_agent_cookbook` → skills/patrones; `meta_muse_code_sdk` → sesión/continuidad/approval/resume (CL-009).
- **MiniMax:** Mini-Agent/mcode → candidatos fleet; OpenRoom → UI/agent capability; mmx/Plugins/MCP/MCP-JS/Coding-Plan-MCP → infraestructura detrás de ports existentes (CL-010).
- **Kimi:** kimi-code → candidato fleet; kimi-cli → legacy/fallback; kimi-agent-sdk + kimi-agent-rs → SDK/transporte; Kimi-Researcher → research si supera NO_VALUE_GAP (CL-011).

## Cola de cierre autoritativa
1. **CL-001 PASS** — X-Ray de raíz, runtime, adapters, motores y Crazy Wall.
2. **CL-002 IN_PROGRESS** — descarga/extracción/publicación MiniMax/Kimi GitHub con provenance/hash/read-back.
3. **CL-003 PENDING** — adquisición NPM exacta de `@minimax-ai/code`/mcode.
4. **CL-004 PENDING** — kimi-code/kimi-cli con symlinks sin debilitar motores.
5. **CL-005 PENDING** — reconciliar destino/manifiestos; ningún entregado sin read-back en main.
6. **CL-006 PENDING** — X-Ray 1×1 y clasificación AGENT/SKILL/SDK/UI/PLUGIN/INFRA/REFERENCE + ADOPT/ADAPT/REJECT.
7. **CL-007 PENDING** — ampliar fleet sólo con agentes reales y contrato/roles/transporte demostrados.
8. **CL-008 PENDING** — ACP/stdio/transporte oficial para Mini-Agent/Kimi Code/mcode; eventos normalizados.
9. **CL-009 PENDING** — Meta Cookbook + Muse SDK integrados en skills/continuidad.
10. **CL-010 PENDING** — infraestructura MiniMax detrás del bus/ports existentes.
11. **CL-011 PENDING** — SDKs Kimi + Researcher; kimi-cli sólo si aporta valor.
12. **CL-012 PENDING** — probes runtime/health/fail-closed/sandbox/memory/read-back; reparar y repetir.
13. **CL-013 PENDING** — cross-check global, duplicados/orphans/rutas, 3 refutaciones y cierre 100% del scope.

## Gate final
`100% PASS en scope OR SOURCE_NOT_PUBLIC explícito`; TESTED evidence y read-back obligatorios. `AUTH_PROVIDER_TEST_PENDING` no se convierte en PASS sin ejecución autenticada real.
