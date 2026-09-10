# 📂 TAREA 3 — PLAN WATCHDOG · PARALELISMO + SANDBOX + MEMORIA

**Estado:** `ACTIVE_DESIGN / IMPLEMENTATION_PENDING`  
**Fecha:** 2026-09-10  
**Repositorio:** `maxbry123-commits/agentes`  
**Regla:** 3 pasos de trabajo. Las capacidades internas no crean fases nuevas.

## 1. Objetivo

Construir el Watchdog programable de YAIWES con el mínimo sistema que permita:

- programar tareas;
- ejecutarlas en paralelo bajo límites;
- mantener estado y memoria persistentes;
- aislar ejecución en sandbox;
- recuperar trabajos después de fallo;
- demostrar el resultado con evidence/read-back.

No se acepta una cifra `100x` como requisito ni como hecho hasta medirla en benchmark real. Los documentos MAX/Mavis aportan patrones y código de referencia, pero la aceptación del Watchdog se basa en comportamiento medido y tests.

## 2. Contrato único de 3 pasos

```text
CONTRACT yaiwes.watchdog.minimax.v1

STEP_1 ANALYZE_AND_DEFINE
  definir Job/Watchdog schema
  definir DSL + DAG
  elegir owner por capacidad
  elegir puertos/adapters mínimos
  OUTPUT = ContractPack

STEP_2 WIRE_AND_RUN
  conectar scheduler + queue + workers
  conectar state + memory + artifacts
  conectar sandbox + durable/workflow engines
  conectar parallel runtime
  ejecutar por contracts
  OUTPUT = RunnableWatchdog
  TESTS = FORBIDDEN como gate de cierre

STEP_3 TEST_AND_CLOSE
  test simple + parallel + recovery + sandbox + memory
  evidence + readback
  OUTPUT = PASS | GAP
```

DAG:

```text
[1 SCHEMA/DSL/OWNERS] → [2 WIRE RUNTIME] → [3 TEST E2E] → [PASS]
          ↑                    ↑                │
          └──────────── GAP REPAIR ────────────┘
```

## 3. MINIMAX — núcleo mínimo que maximiza capacidad

Solo estos bloques son obligatorios para la primera versión:

1. **JobContract / WatchdogDefinition** — contrato uniforme `validate → execute → checkpoint → resume → cleanup`.
2. **Registry + Factory/Capability resolver** — resolver capacidades sin `if` gigantes ni creación directa acoplada.
3. **SchedulerPort** — APScheduler como time authority; Workalendar como política de calendario.
4. **QueuePort + Priority Queue** — Celery primary o Taskiq alternativa; prioridad y límites de concurrencia.
5. **Persistent Worker Pools** — separar I/O, CPU, coding/sandbox, research y durable jobs solo cuando el recurso lo justifique.
6. **Parallel Runtime** — fan-out/fan-in, batching, async pipeline, backpressure y dedup.
7. **State/Memory/Artifacts** — PostgreSQL + pgvector + Redis event/lease plane + RustFS/S3-compatible.
8. **SandboxPort** — gVisor por defecto para aislamiento reforzado; Firecracker solo para perfil high-risk; iii-sandbox queda candidato hasta X-Ray.
9. **Recovery** — idempotency key, lease, heartbeat, checkpoint, retry/timeout y DLQ cuando sea necesaria.
10. **Evidence/Health** — cada cierre produce estado verificable y read-back.

Todo lo demás es opcional hasta demostrar un GAP.

## 4. Componentes físicos ya presentes

### Owners/candidatos principales

```text
TIME              → APScheduler
CALENDAR          → Workalendar
SIMPLE QUEUE      → Celery | Taskiq
EVENT/LEASE       → Redis
DURABLE           → Hatchet | DBOS Python | Restate
MULTI-STEP        → Dagu
SMALL LOOP        → PocketFlow
DAG               → Apache Hamilton | redun
RESEARCH          → DeerFlow | GPT-Researcher | MindSearch
ADAPTIVE PLAN     → YAIWES + optional smolagents
STATE             → PostgreSQL
SEMANTIC MEMORY   → pgvector
SANDBOX           → gVisor | Firecracker | iii-sandbox candidate
ARTIFACTS         → RustFS / S3-compatible
```

Regla de ownership: un owner activo por responsabilidad; alternativas detrás del mismo port.

## 5. Schemas mínimos

### WatchdogDefinition

```text
watchdog_id
name
goal
mode
schedule
timezone
priority
concurrency_group
max_concurrency
capability
sandbox_profile
timeout
retry_policy
checkpoint_policy
status
created_at
updated_at
```

### WatchdogRun

```text
run_id
watchdog_id
scheduled_for
status
attempt
idempotency_key
lease_owner
lease_expires_at
worker_id
sandbox_id
checkpoint_id
result_ref
evidence_ref
error_class
started_at
finished_at
```

### WatchdogStep

```text
step_id
run_id
dependencies
state
input_ref
output_ref
attempt
heartbeat_at
checkpoint_ref
evidence_ref
```

### Checkpoint

```text
checkpoint_id
run_id
step_id
state_version
artifact_snapshot
memory_snapshot_ref
resume_token
integrity_hash
created_at
```

### EventEnvelope

```text
event_id
event_type
watchdog_id
run_id
step_id
created_at
payload_ref
idempotency_key
trace_id
```

## 6. Job ABI mínimo

Referencia obligatoria para no convertir cada componente en un mini-sistema operativo:

```python
from abc import ABC, abstractmethod

class Job(ABC):
    @abstractmethod
    def validate(self): ...

    @abstractmethod
    def execute(self): ...

    @abstractmethod
    def checkpoint(self): ...

    @abstractmethod
    def resume(self): ...

    @abstractmethod
    def cleanup(self): ...
```

El Registry resuelve la implementación por capacidad. El Scheduler no conoce internals del plugin/job.

## 7. Runtime paralelo mínimo

Las funciones tomadas como referencia del documento Mavis Parallel se incorporan como capacidades, no como servicios separados obligatorios:

```text
PersistentPool
PriorityTaskQueue
SmartCache
SmartBatcher
StreamingResult
AsyncPipeline
DedupExecutor
```

Aplicación:

```text
I/O independent tasks → async/fan-out
CPU-bound             → process workers
external API           → batching cuando API lo soporta
large output           → streaming + backpressure
repeated request       → dedup/cache
mixed workloads        → priority queue + bounded pools
```

No multiplicar factores teóricos para declarar rendimiento. Medir `throughput`, `p95/p99`, `queue_depth`, `oldest_wait`, `failure_rate`, `memory_peak` y costo por job.

## 8. Estado, memoria y artefactos

### PostgreSQL

Fuente durable de verdad para:

- definitions;
- runs/steps;
- state machine;
- leases/idempotency metadata;
- checkpoints;
- final state;
- audit/evidence references.

### pgvector

Memoria semántica y retrieval. No sustituye las tablas transaccionales.

### Redis

Eventos, queue support, cache, locks/leases/heartbeat y coordinación efímera. No es fuente durable única.

### RustFS / S3

Snapshots, outputs, adjuntos y artefactos grandes. Backblaze B2 se conecta únicamente como provider S3-compatible si se selecciona.

### Capas de recuperación

```text
STATE      → PostgreSQL
MEMORY     → PostgreSQL + pgvector
ARTIFACTS  → RustFS/S3
FAST COORD → Redis
```

## 9. Sandbox

```text
LOW_RISK        → sandbox runtime estándar aislado
MEDIUM_RISK     → gVisor
HIGH_RISK       → Firecracker
SPECIAL_RUNTIME → iii-sandbox solo después de X-Ray/test
```

Todo sandbox recibe solo:

- `job/run id`;
- input autorizado;
- capability/tool policy;
- workspace asignado;
- límites CPU/RAM/time;
- secrets mínimos por lease;
- checkpoint/artifact refs necesarios.

No montar repositorios completos ni secretos globales por defecto.

## 10. Recovery

```text
FAIL/STALE
→ freeze evidence
→ check lease + heartbeat
→ read checkpoint
→ check idempotency
→ retry if safe
→ resume same worker/engine OR route fallback through same Port
→ verify
→ persist result
```

Estados mínimos:

```text
PENDING → QUEUED → LEASED → RUNNING → COMPLETED
                         ├→ WAITING
                         ├→ RETRYING
                         ├→ RECOVERING
                         ├→ FAILED
                         └→ CANCELLED
```

## 11. Patrones aceptados de los dos documentos adjuntos

Se incorporan como biblioteca técnica:

- fan-out/fan-in;
- batching;
- sharding solo cuando exista presión medida;
- priority queues;
- persistent worker pools;
- async pipelines;
- backpressure;
- deduplication;
- idempotency keys;
- checkpoints/resume;
- DLQ;
- outbox cuando se necesite consistencia DB→evento;
- cache LRU/mmap donde exista relectura real;
- streaming de outputs grandes;
- sandbox isolation;
- durable state;
- semantic memory;
- artifact snapshots.

Quedan **fuera del MVP** hasta GAP/benchmark: multi-region active-active, predictive autoscaling, time-wheel propio, CDC complejo, DNS failover propio, varios schedulers activos y nuevas bases de datos redundantes.

Fuentes 1×1 incorporadas al plan:

- `Core kernel Yaiwes/Backend watchdog workflow adaptativo/fuentes/📌MAX-SYSTEM-100X-FINAL-1.md`
- `Core kernel Yaiwes/Backend watchdog workflow adaptativo/fuentes/📌MAVIS-PARALLEL-100X.md`

## 12. Flujo operativo

```text
USER/CHAT
→ WatchdogDefinition
→ schema + policy/sheriff
→ PostgreSQL
→ APScheduler + Workalendar
→ DUE
→ WatchdogRun + idempotency key
→ priority queue
→ capability/task classifier
→ bounded worker pool
→ acquire lease
→ sandbox
→ load state/memory/artifacts
→ execute
→ heartbeat/checkpoint
→ verify
→ evidence/artifact
→ complete | retry | recover
→ next run
```

## 13. Paralelismo controlado

`N Watchdogs registrados != N procesos activos`.

Cada job usa al menos:

```text
priority
resource_class
concurrency_group
max_concurrency
idempotency_key
timeout
```

Fan-out solo en unidades independientes. Fan-in espera únicamente los resultados requeridos por el DAG. La cola debe ejercer backpressure en lugar de crear procesos ilimitados.

## 14. Tareas pendientes reales

1. Materializar los 5 schemas: Definition, Run, Step, Checkpoint, EventEnvelope.
2. Materializar Ports mínimos: Scheduler, Queue, Durable, Workflow, State, Memory, Sandbox, Artifact; Research/Planning solo si los carriles los usan.
3. Implementar Job ABI + Registry/Factory/Capability resolver.
4. Conectar APScheduler/Workalendar, Celery/Taskiq, PostgreSQL/Redis/pgvector/RustFS y un sandbox profile.
5. Integrar PersistentPool + PriorityQueue + batching/dedup/backpressure/streaming donde aplique.
6. Integrar Hatchet/Dagu detrás de ports después del E2E simple.
7. Testear simple → parallel → recovery → memory → sandbox → durable/multi-step.
8. Conectar UI/event stream después de estabilizar el backend contract.

## 15. Criterio de cierre

Paso 3 debe demostrar como mínimo:

```text
create definition
persist/restart/readback
schedule/timezone
priority/concurrency
simple job
parallel bounded jobs
idempotency
retry + timeout
lease/heartbeat recovery
checkpoint/resume
memory write/read
artifact snapshot/readback
sandbox isolation
failure path
final evidence
```

Research/adaptive/multi-step se prueban cuando se habilitan como capability; no bloquean el MVP si no forman parte del primer carril activado.

## 16. Nota de relevo para Grok / GPT-5.6 Sol / Astra

```text
HANDOFF_LOCK = YAIWES-WATCHDOG-MINIMAX-3-STEPS
READ_FIRST = this file + CONTRATO-MINIMAX-WATCHDOG-PARALELO-SANDBOX-MEMORIA.md
DO_NOT_ADD_PHASES = true
DO_NOT_CLAIM_100X_WITHOUT_BENCHMARK = true

CURRENT_STATE:
- backend OSS components are physically present
- integration/contracts are pending
- Task 2 component integration must close real behavior gates
- Watchdog runtime must remain behind ports

NEXT:
1. STEP_1 schemas/DSL/ports
2. STEP_2 wire minimal owners + parallel runtime + state/memory/sandbox
3. STEP_3 E2E evidence/readback

Do not replace a port with a provider-specific API in consumers.
Do not add infrastructure unless a measured GAP requires it.
```

## 17. Enlaces

- Plan TAREA 3: https://github.com/maxbry123-commits/agentes/blob/main/%F0%9F%93%82%20Readme%20plan%20wachdog%20y%20trabajo%20en%20paralelo.md
- Contrato MINIMAX: https://github.com/maxbry123-commits/agentes/blob/main/Core%20kernel%20Yaiwes/Backend%20watchdog%20workflow%20adaptativo/CONTRATO-MINIMAX-WATCHDOG-PARALELO-SANDBOX-MEMORIA.md
- Plan TAREA 2: https://github.com/maxbry123-commits/agentes/blob/main/Readme%20arquitectura%20Yaiwes/HANDOFF-INTEGRACION-1-20.md
