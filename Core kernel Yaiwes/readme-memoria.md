# readme-memoria — Watchdog YAIWES

## Propósito
La memoria del Watchdog conserva estado operativo verificable para que una tarea programada sobreviva cierres de chat, fallos de workers y reemplazos de sandbox. No persiste chain-of-thought privado; persiste contratos, entradas, decisiones explícitas, artefactos, evidencia, checkpoints y deltas de estado.

## Capas
`WORKING MEMORY → tarea actual/context pack`

`PERSISTENT MEMORY → conocimiento y estado durable`

`EPISODIC LOG → historial de ejecuciones y decisiones explícitas`

`VERSION GRAPH → branches + checkpoints + artefactos`

`RECOVERY → localizar → rollback/repair/fork → resume`

## Contrato Memory Orchestrator
El Workflow puede solicitar objetos estructurados: `GET_CONTEXT`, `GET_MEMORY`, `GET_EVIDENCE`, `GET_ARTIFACTS`, `GET_STATE`, `GET_HISTORY`, `GET_RELEVANT_RELATIONS`, `AUDIT_MEMORY`, `SAVE_STATE`, `SAVE_ARTIFACT`, `SAVE_CONSOLIDATION`, `CREATE_CHECKPOINT`.

El Memory Orchestrator recupera, rerankea, audita, ensambla y valida contexto; no decide el objetivo global, no modifica instrucciones del usuario, no convierte hipótesis en hechos y no autoriza operaciones peligrosas.

## Persistencia
- **PostgreSQL:** Watchdog, schedule, run, workflow, current_step, checkpoints, idempotency keys, outbox y estado durable.
- **pgvector:** memoria semántica y recuperación por relevancia.
- **Redis:** eventos, consumer groups, locks/leases, cola rápida y heartbeats; no reemplaza la verdad durable.
- **S3 compatible / Backblaze B2:** snapshots, artefactos grandes y workspaces.

## Sandbox y recovery
Cada ejecución recibe un workspace aislado. El sandbox mantiene `heartbeat`; si queda stale, el sistema crea/reasigna un sandbox, carga el último estado durable, remonta el workspace/snapshot, retoma locks con TTL y reanuda desde el último step verificable.

`FAIL ≠ RESET`

`FAIL → LOCALIZE → CHECKPOINT → ROLLBACK → REPAIR/FORK → RESUME`

## Sandbox Fork
Desde un `MASTER CHECKPOINT` pueden abrirse ramas aisladas con la misma policy, task contract, input references y validation schema, pero diferente modelo/estrategia/contexto local. Judge/Sheriff comparan evidencia y promueven una rama a `CANONICAL STATE`; las demás quedan como alternativas o evidencia de fallo.

## Flujo con el Watchdog
`SCHEDULE → WATCHDOG RUN → MEMORY REQUEST → CONTEXT PACK → SANDBOX → AGENT/MODEL → STATE DELTA → AUDIT → CONSOLIDATE → MEMORY UPDATE → CHECKPOINT → NEXT STEP / COMPLETE`

## Paralelismo
El sistema puede fan-out cientos de trabajos pendientes, pero controla concurrencia mediante priority queues, pools especializados, batching, deduplicación, backpressure e idempotencia. Cientos de tareas programadas no significan cientos de procesos sin límite.

## Regla canónica
El modelo piensa y propone; el runtime controla; la memoria recuerda; el sandbox aísla; Sheriff/Judge verifican; el Watchdog programa, despierta, supervisa y reanuda.
