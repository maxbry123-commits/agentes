# PLAN LOOP — Wordflow LOOP Yaiwes

Contrato: `tel.workflow/v4` · modo `FAIL_CLOSED_EXECUTION_LOOP`.  
Raíz única autorizada: `maxbry123-commits/agentes/➡️📂 Wordflow LOOP Yaiwes/`.

## Histórico cerrado
El cierre local de 3 pasos se conserva como evidencia histórica y no se repite: fleet=18, Council12=12, fail-closed local, router prioridad/failover y persistencia fueron probados. `AUTH_PROVIDER_TEST_PENDING` continúa abierto para ejecución autenticada externa.

# Plan activo — CODE_GRAPH_ARCHITECTURE_PROGRAMMING_LOOP
Checkpoint: `WFLOOP-CODE-GRAPH-20260910-0005`  
Nodo actual: `CG03_CODE_GRAPH_ROOT_G001`.

## Cola determinista
1. `CG03_CODE_GRAPH_ROOT_G001`: cerrar G-001 con raíz anclada, contrato de nodos/aristas y serialización determinista reutilizando DAG/task graph existentes; no crear orquestador paralelo.
2. `CG03_INPUT_AUDIT_G002`: auditoría/Ask Council normalizada a schema determinista.
3. `CG04_REUSE_CODE_G005_G009`: investigación previa, REUSE>PATCH>ADAPT>GENERATE, ingesta code, seguridad y NO_VALUE_GAP.
4. `CG04_SAFETY_EXECUTION`: G-008/G-017/G-022/G-024 — seguridad, sandbox, reviewer, deploy y separación determinismo/LLM.
5. `CG05_FABLES_AND_MEMORY`: G-014/G-018/G-030 — memorias de 18 agentes, Fables único y Crazy Wall concurrency.
6. `CG06_ACQUISITION`: G-011/G-012 — motores canónicos, intake list y read-back.
7. `CG07_GRAPH_CONTEXT_VISUAL`: G-026/G-027/G-028/G-029 — UI/Graphiti/Graphology/planificación solo si no duplican capacidades existentes.
8. `CG08_HF_BRIDGE`: G-023 — inventario/bridge solo con acceso real y sin exposición de secretos.

## Cerrados verificados
- `G-003`: task graph determinista; evidence `wordflow_loop/evidence/G003_TASK_GRAPH_2026-09-10.json`.
- `G-004`: placement classifier A–G + `PLACEMENT_REVIEW_REQUIRED`; module blob `69698ad30ba1903e0780efcea1952a3737aeb23e`; tests blob `bf1c26f49edf668ee05584b2a357324af0fc4d8d`; evidence `wordflow_loop/evidence/G004_PLACEMENT_CLASSIFIER_2026-09-10.json`.
- `G-010`: Watchdog supervisor.
- `G-020`: 12 fuentes de comunidad/desarrollo.

## Paralelismo permitido
Fan-out solo entre tareas independientes y con ownership explícito. Dependencias bloqueantes del DAG no se saltan. Mantener `director_tasks` y `generated_tasks` separados; dedup/idempotency/backpressure obligatorios antes de aumentar concurrencia.

## Regla de cierre
Cada GAP requiere source/provenance + decisión + implementación cuando corresponda + test/simulación + read-back/commit + persistencia. Presencia de archivo no equivale a PASS.
