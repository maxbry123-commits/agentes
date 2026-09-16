# AUDITORÍA ORQUESTADOR — CHAT 100x — 2026-09-16

Estado: `PLANNING_ONLY / NO_NODE_CLAIMED`

Repo: `maxbry123-commits/agentes`  
Branch: `main`  
Base SHA: `6d35c08bf350890442606cb0582bf277271251bb`  
Autoridad: `➡️📂 Wordflow LOOP Yaiwes/Crazy Wall Orquestador/SWARM-COLLAB-QUEUE-2026-09-16.json`

Regla: preservar `CODE_GRAPH_CLOSED_VERIFIED_30_OF_30`; no reabrir nodos históricos sin evidencia nueva.

## Objetivo

Convertir Wordflow en el único control-plane determinista de una colmena de workers intercambiables, con una sola autoridad de DAG/FSM/PASS y recuperación durable.

## Estado fresco

- `STATE.json` declara raíz autorizada `➡️📂 Wordflow LOOP Yaiwes/`.
- `WF-HF-01` está ocupado por `ORCHESTRATOR_SOL`.
- `WF-COPY-02`, `WF-PROFILES-03`, `WF-INTAKE-04`, `WF-AUTOLOOP-05` y `WF-RECOVERY-06` están `FREE`.
- Esta auditoría no reclama ningún nodo.
- `kernel.py` aplica `completion_gate` solo si existe `completion_contract`.
- `Kernel._idempotency_cache` sigue en memoria.
- `CheckpointManager._checkpoints` sigue en memoria.
- Existen `runtime/src/agent/agent_router.py` y `AgentFleetAdapter` como dos superficies de routing.

## Candidatos GAP / mejoras

### AUD-001 — Reconciliar raíz/copia
Existe trabajo histórico también bajo `Wordflow Loops code Yaiwes/`, mientras STATE/Swarm usan `➡️📂 Wordflow LOOP Yaiwes/` como raíz autorizada.

Plan: inventariar ambas raíces por path/tree SHA; clasificar `canonical|mirror|staging|obsolete`; establecer una sola raíz de escritura sin borrar automáticamente.

Gate: `ONE_CANONICAL_WRITE_ROOT_VERIFIED`.

### AUD-002 — Completion contract obligatorio
`completion_gate.py` es fail-closed al existir contrato, pero los nodos legacy sin `completion_contract` conservan cierre anterior.

Plan: nuevas misiones swarm requieren goal + acceptance + evidence + oracle antes de `VERIFIED_CLOSED`.

Gate: `NO_COMPLETION_CONTRACT = NO_VERIFIED_CLOSE`.

### AUD-003 — Idempotencia durable
`Kernel._idempotency_cache` es memoria de proceso.

Plan: persistir `idempotency_key + canonical_input_hash + result_hash + receipt`; misma key/mismo payload => replay; misma key/payload distinto => FAIL_CLOSED; restaurar índice tras restart.

Gate: `CRASH_RESTART_NO_DOUBLE_EXECUTION`.

### AUD-004 — Checkpoint durable
`CheckpointManager._checkpoints` es memoria de proceso.

Plan: backend durable SQLite/Postgres o runtime externo; hash + schema/version + mission/input/contract hashes; prueba real de proceso nuevo y resume.

Gate: `NEW_PROCESS_RESUME_FROM_VERIFIED_CHECKPOINT`.

### AUD-005 — Router único
`agent_router.py` mantiene 4 agentes y fallback implícito; `AgentFleetAdapter` usa registry completo y falla cerrado por id/rol.

Plan: auditar imports reales; consolidar en una sola autoridad de routing; deprecar el router redundante solo con regresión verde.

Gate: `ONE_ROUTER_ONE_DECISION_PATH`.

### AUD-006 — Worker/abeja espejo
Diseño objetivo: `1 Wordflow control-plane + 1 artefacto worker inmutable + N réplicas`.

Cada réplica: `worker_id`, capabilities, provider/config, isolated workspace, mismo code SHA/digest.

Gate: `N_REPLICAS_SAME_CODE_DIGEST_DIFFERENT_WORKER_ID`.

### AUD-007 — Claim + lease + heartbeat + reclaim
Flujo: `READY -> CLAIMED -> ACKED -> RUNNING`; lease con owner/expiry; heartbeat; pérdida => reclaim; idempotency check antes de reejecutar.

Gate: `WORKER_CRASH_RECLAIM_WITHOUT_DOUBLE_EFFECT`.

### AUD-008 — Cola durable / runtime externo
Investigar por PoC: Temporal, Dapr Workflow/Agents, Hatchet, DBOS, Restate; Ray Core solo para compute/actors.

Criterios: durability/replay, worker queues, heartbeat, retry/timeout, idempotency, Python, licencia, complejidad, adapter fino sin duplicar DAG Wordflow.

Gate: `RUNTIME_SELECTED_BY_REPRODUCIBLE_POC`.

### AUD-009 — Seals como worker, no segundo orquestador
Interfaz objetivo: `NodeInput -> ExecutionResult + ToolReceipt + Evidence`.

Wordflow conserva DAG/FSM/queue/retry global/state/oracle.

Gate: `NO_DUPLICATE_ORCHESTRATOR`.

### AUD-010 — Oracle independiente
Worker nunca autoriza PASS. Wordflow verifica test/build/runtime/hash/schema/API/postcondition.

Gate: `NO_REAL_ORACLE = NO_VERIFIED_CLOSED`.

### AUD-011 — Ledger/evidence de colmena
Registrar por dispatch/mutación: mission_id, node_id, command_id, worker_id, idempotency_key, base_sha, before/after SHA256, tool_receipt, test_receipt, prev_hash/hash.

Gate: `TRACE_REPLAYABLE_AND_TAMPER_EVIDENT`.

### AUD-012 — Escalado 3 -> 5 -> 10 -> 50
3 workers primero; luego crash/reclaim con 5; concurrency/backpressure con 10; 50 solo con invariantes verdes.

Gate final: `50_WORKERS_NO_COLLISION_NO_DOUBLE_WRITE_NO_FAKE_PASS`.

## Mapeo a cola actual

- `WF-RECOVERY-06`: relacionado con AUD-003/AUD-004/AUD-007; no reclamar aquí.
- `WF-AUTOLOOP-05`: contratos/run artifacts; relacionado con AUD-002/AUD-011.
- `WF-PROFILES-03`: perfiles/memoria; puede alimentar identidad/capabilities.
- `WF-HF-01`: ocupado; no tocar.

## Plan 100x

P0: reconciliar raíz; completion contract obligatorio en nuevos nodos; idempotency/checkpoint durable.  
P1: contrato BeeWorker; lease/heartbeat/reclaim; router único; PoC 3 workers.  
P2: benchmark reproducible Temporal vs Dapr vs Hatchet vs DBOS/Restate y adapter fino.  
P3: convertir Seals a worker; OpenCode/OpenHands/Codex como perfiles separados; reviewer independiente.  
P4: chaos test y escalar 5 -> 10 -> 50.

## Invariantes

- 1 control-plane autoritativo.
- 1 nodo = 1 owner activo.
- 1 path = 1 writer activo.
- no mutation sin authorization/lease.
- no replay sin idempotency check.
- no `VERIFIED_CLOSED` sin oracle real.
- persistencia fallida => FAIL_CLOSED.
- runtime externo no reemplaza policy/oracle de Wordflow.

## Siguiente acción

READ FRESH de la cola antes de reclamar. Para esta línea la prioridad sugerida es `WF-RECOVERY-06`, por ser el punto más cercano a durability/retry/resume/reclaim; reclamarlo solo si continúa `FREE` y con base SHA fresco.
