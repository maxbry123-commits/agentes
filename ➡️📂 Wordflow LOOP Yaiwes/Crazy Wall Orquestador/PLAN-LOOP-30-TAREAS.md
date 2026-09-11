# PLAN LOOP — Wordflow LOOP Yaiwes

Contrato: `tel.workflow/v4` · modo `FAIL_CLOSED_EXECUTION_LOOP`.  
Raíz única autorizada: `maxbry123-commits/agentes/➡️📂 Wordflow LOOP Yaiwes/`.

## Histórico cerrado
El cierre local de 3 pasos se conserva como evidencia histórica y no se repite: fleet=18, Council12=12, fail-closed local, router prioridad/failover y persistencia fueron probados. `AUTH_PROVIDER_TEST_PENDING` continúa abierto para ejecución autenticada externa.

# Plan activo — CODE_GRAPH_ARCHITECTURE_PROGRAMMING_LOOP
Checkpoint canónico: `WFLOOP-CODE-GRAPH-20260911-0010`  
Nodo actual: `CG13_SOURCE_TRUTH_RECONCILIATION_G013`.

## Cola determinista actualizada
1. `G-013`: reconciliar las fuentes de verdad requeridas, ejecutar read-back y cerrar solo si STATE/CHECKPOINT/README/BITACORA/GAPS/HANDOFF/PLAN/RECOVERY convergen en el mismo checkpoint.
2. `G-018`: verificar source proof + Ficha/contract + registro/test del Enchufe Universal Fables.
3. `G-006`: reabrir únicamente cuando G-018 quede verificado; política de creación de code nuevo posterior al gate G-005.
4. `G-007/G-008/G-009`: ingesta de code existente, seguridad/neutralización y `NO_VALUE_GAP`.
5. `G-017/G-022/G-024`: deployment real, sandbox enforceable, reviewer y separación determinismo/LLM.
6. `G-014/G-030`: memorias 18 agentes y Crazy Wall concurrency.
7. `G-011/G-012`: motores canónicos, intake de componentes/listas, hash/read-back.
8. `G-026/G-027/G-028/G-029`: UI/Graphiti/Graphology/planificación solo ante GAP concreto y sin duplicar DAGEngine.
9. `G-023`: HF bridge solo con acceso real y sin exponer secretos.

## Cerrados verificados
- `G-001`: CODE GRAPH workspace determinista.
- `G-002`: auditoría de archivo + Council normalizado sin autoridad ejecutiva.
- `G-003`: task graph determinista; `director_tasks` y `generated_tasks` separados.
- `G-004`: placement classifier A–G + `PLACEMENT_REVIEW_REQUIRED`.
- `G-005`: reuse selector `runtime/src/core/reuse_selector.py` blob `bc7f4805fc7f13e6de0341b84c533d4b7fb6b044`; catálogo `reuse_catalog_g005.json` blob `2367f7ed8c7e1ece1d724f15f6494d5ff56543f8`; evidence `G005_REUSE_SELECTOR_2026-09-11.json`.
- `G-010`: Watchdog supervisor.
- `G-020`: 12 fuentes de comunidad/desarrollo.

## Política G-005 vigente
`REUSE > PATCH > ADAPT > GENERATE`. Máximo 10 candidatos por decisión; source/licencia/mantenimiento/compatibilidad/riesgo/footprint obligatorios. Candidato externo requiere `ADAPT`, nunca ejecución directa. Para `dag`, `DAGEngine` local es REUSE por defecto; NetworkX no reemplaza scheduler sin GAP demostrado. Graphiti/Graphology siguen en investigación y no están integrados.

## Estado G-013
`runtime/src/core/source_truth_reconciler.py` fue corregido para aceptar un marcador explícito `Checkpoint canónico:` en documentos con historial de múltiples checkpoints y mantener fail-closed ante marcadores canónicos conflictivos. Tests ampliados para historial/conflicto. Cierre todavía pendiente de reconciliación y read-back de las 8 fuentes requeridas.

## Paralelismo permitido
Fan-out solo entre tareas independientes y con ownership explícito. Dependencias bloqueantes del DAG no se saltan. Mantener `director_tasks` y `generated_tasks` separados; dedup/idempotency/backpressure obligatorios antes de aumentar concurrencia.

## Regla de cierre
Cada GAP requiere source/provenance + decisión + implementación cuando corresponda + test/simulación + read-back/commit + persistencia. Presencia de archivo no equivale a PASS. `AUTH_PROVIDER_TEST_PENDING` permanece abierto hasta evidencia autenticada real.
