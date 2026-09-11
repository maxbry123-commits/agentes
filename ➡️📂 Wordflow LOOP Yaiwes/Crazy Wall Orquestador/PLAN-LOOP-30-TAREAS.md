# PLAN LOOP — Wordflow LOOP Yaiwes

Contrato: `tel.workflow/v4` · modo `FAIL_CLOSED_EXECUTION_LOOP`.  
Raíz única autorizada: `maxbry123-commits/agentes/➡️📂 Wordflow LOOP Yaiwes/`.

## Histórico cerrado
El cierre local de 3 pasos se conserva como evidencia histórica y no se repite: fleet=18, Council12=12, fail-closed local, router prioridad/failover y persistencia fueron probados. `AUTH_PROVIDER_TEST_PENDING` continúa abierto para ejecución autenticada externa.

# Plan activo — CODE_GRAPH_ARCHITECTURE_PROGRAMMING_LOOP
Checkpoint: `WFLOOP-CODE-GRAPH-20260910-0002`  
Nodo actual: `CG01_REUSE_AUDIT`.

## Cola determinista
1. `CG01_REUSE_AUDIT`: localizar/revisar Chat A↔B, deployment, Fables, sandbox, memoria agente y motores dentro de la arquitectura existente.
2. `CG02_SOURCE_OF_TRUTH_RECONCILE`: reconciliar README/HANDOFF/STATE/CHECKPOINT/PLAN/RECOVERY/BITÁCORA y cerrar G-013 solo tras read-back.
3. `CG03_FOUNDATION_CONTRACTS`: G-001/G-002/G-003/G-004 — raíz CODE GRAPH, auditoría, task schema y placement rules.
4. `CG04_SAFETY_EXECUTION`: G-008/G-017/G-022/G-024 — seguridad, sandbox, reviewer, deploy y separación determinismo/LLM.
5. `CG05_FABLES_AND_MEMORY`: G-014/G-018/G-030 — memorias de 18 agentes, Fables único y Crazy Wall concurrency.
6. `CG06_ACQUISITION`: G-011/G-012 — motores canónicos, intake list y read-back.
7. `CG07_GRAPH_CONTEXT_VISUAL`: G-026/G-027/G-028/G-029 — UI/Graphiti/Graphology/planificación solo si no duplican capacidades existentes.
8. `CG08_HF_BRIDGE`: G-023 — inventario/bridge solo con acceso real y sin exposición de secretos.

## Paralelismo permitido
Fan-out solo entre tareas independientes y con ownership explícito. Dependencias bloqueantes del DAG no se saltan. Mantener `director_tasks` y `generated_tasks` separados; dedup/idempotency/backpressure obligatorios antes de aumentar concurrencia.

## GAP cerrados verificados
- G-010 — Watchdog supervisor.
- G-020 — 12 fuentes de comunidad/desarrollo.

Evidencia: `➡️📂 Wordflow LOOP Yaiwes/wordflow_loop/evidence/CODE_GRAPH_CYCLE_0002_2026-09-10.json`.

## Regla de cierre
Cada GAP requiere source/provenance + decisión + implementación cuando corresponda + test/simulación + read-back/commit + persistencia. Presencia de archivo no equivale a PASS.
