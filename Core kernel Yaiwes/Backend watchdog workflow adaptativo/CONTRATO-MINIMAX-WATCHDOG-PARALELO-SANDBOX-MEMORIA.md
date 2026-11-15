# CONTRATO MINIMAX — WATCHDOG · PARALELISMO · SANDBOX · MEMORIA

**Schema:** `yaiwes.watchdog.minimax-contract/v1`  
**Fecha:** 2026-09-10  
**Estado:** `ACTIVE / IMPLEMENTATION_PENDING`  
**Objetivo:** contrato corto y retomable para construir el Watchdog sin sobreingeniería.

## 1. Regla principal

Solo existen tres pasos:

```text
1 ANALYZE_AND_DEFINE
2 WIRE_AND_RUN
3 TEST_AND_CLOSE
```

No crear fases 4, 5, 6 ni convertir cada capacidad en un proyecto independiente.

## 2. DSL

```yaml
contract: yaiwes.watchdog.minimax.v1
source_of_truth:
  - physical_repo_state
  - runtime_test_evidence
  - readback

steps:
  - id: 1
    name: ANALYZE_AND_DEFINE
    requires:
      - WatchdogDefinition
      - WatchdogRun
      - WatchdogStep
      - Checkpoint
      - EventEnvelope
      - JobABI
      - ports
    output: ContractPack

  - id: 2
    name: WIRE_AND_RUN
    requires:
      - scheduler
      - queue
      - worker_pool
      - state
      - memory
      - artifacts
      - sandbox
      - recovery
      - parallel_runtime
    tests_forbidden_as_close_gate: true
    output: RunnableWatchdog

  - id: 3
    name: TEST_AND_CLOSE
    requires:
      - behavior
      - failure_path
      - recovery
      - parallel_bounds
      - memory_readback
      - sandbox_isolation
      - evidence
      - readback
    output: PASS_OR_GAP

gap_policy: repair_in_current_step
no_step_4: true
```

## 3. DAG

```text
[Definition/DSL]
      │
      ▼
[STEP 1: Schema + Ports + Owners]
      │
      ▼
[STEP 2: Wire Runtime]
      │
      ├── Scheduler/Calendar
      ├── Priority Queue
      ├── Bounded Worker Pools
      ├── Batch/Dedup/Backpressure
      ├── PostgreSQL/Redis/pgvector
      ├── Artifact Storage
      ├── Sandbox
      └── Checkpoint/Recovery
      │
      ▼
[STEP 3: E2E Tests]
      │
      ├── PASS → CLOSED
      └── GAP  → repair owning step → repeat
```

## 4. Owners

```text
TIME             = APScheduler
CALENDAR         = Workalendar
QUEUE            = Celery primary | Taskiq alternative
EVENTS/LEASES    = Redis
DURABLE          = Hatchet primary | DBOS/Restate alternatives
MULTI_STEP       = Dagu
SMALL_LOOP       = PocketFlow
FUNCTIONAL_DAG   = Apache Hamilton | redun
STATE            = PostgreSQL
SEMANTIC_MEMORY  = pgvector
ARTIFACTS        = RustFS/S3-compatible
SANDBOX_MEDIUM   = gVisor
SANDBOX_HIGH     = Firecracker
SANDBOX_SPECIAL  = iii-sandbox after validation
RESEARCH         = DeerFlow | GPT-Researcher | MindSearch through ResearchPort
ADAPTIVE_PLAN    = YAIWES; smolagents optional behind PlanningPort
```

Una responsabilidad = un owner activo. Alternativas solo detrás del mismo Port.

## 5. Job ABI

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

Registry mínimo:

```python
JOB_REGISTRY = {}

def register_job(name, cls):
    JOB_REGISTRY[name] = cls
```

Regla: los consumidores piden una **capability**, no una clase concreta del proveedor.

## 6. Parallel Runtime

Capacidades admitidas:

```text
Persistent Worker Pool
Priority Task Queue
Smart Batching
Async Pipeline
Fan-out/Fan-in
Backpressure
Deduplication
Cache cuando existe relectura real
Streaming para outputs grandes
```

Contrato de job paralelo:

```yaml
job:
  id: string
  capability: string
  priority: integer
  resource_class: io|cpu|sandbox|research|durable
  concurrency_group: string
  max_concurrency: integer
  timeout_s: number
  idempotency_key: string
  checkpoint_policy: string
  sandbox_profile: string
```

Métricas obligatorias antes de afirmar mejoras de rendimiento:

```text
throughput
p95_latency
p99_latency
queue_depth
oldest_wait
failure_rate
retry_rate
memory_peak
cost_per_job
```

No se acepta `100x` por multiplicación teórica de factores.

## 7. State + Memory

### Estado durable

PostgreSQL es source of truth para Definition/Run/Step/checkpoints/idempotency/final state.

### Memoria

PostgreSQL + pgvector almacena memoria estructurada y referencias semánticas. No sustituye state transaccional.

### Coordinación rápida

Redis gestiona eventos, locks, leases, heartbeat, dedup/cache efímero. No es el único ledger durable.

### Artifacts

RustFS/S3-compatible conserva snapshots, outputs y archivos grandes. B2 es provider opcional detrás de ArtifactPort.

## 8. Sandbox

```yaml
profiles:
  low:
    isolation: standard
  medium:
    isolation: gvisor
  high:
    isolation: firecracker
  special:
    isolation: iii-sandbox
    gate: validation_required
```

Todo sandbox debe recibir recursos mínimos autorizados y límites de CPU/RAM/time. Secretos globales y montaje completo del repositorio están prohibidos por defecto.

## 9. Recovery

```text
DETECT FAIL/STALE
→ freeze evidence
→ verify lease/heartbeat
→ load checkpoint
→ verify idempotency
→ retry/resume if safe
→ fallback behind same Port if required
→ verify behavior
→ persist/readback
```

No resetear un workflow completo si existe checkpoint válido.

## 10. Fuentes técnicas incorporadas 1×1

Los siguientes documentos adjuntos forman parte del contrato como **fuentes de diseño y código de referencia**:

1. `fuentes/📌MAX-SYSTEM-100X-FINAL-1.md`
2. `fuentes/📌MAVIS-PARALLEL-100X.md`

Regla de interpretación:

- conservar su código y patrones como material de referencia;
- no convertir cifras de throughput/costo/RTO en garantías sin benchmark propio;
- no activar multi-region, time-wheel propio, CDC complejo, predictive autoscaling o nuevas infraestructuras hasta que un GAP medido las requiera;
- preferir el Job ABI, ports y owners ya seleccionados.

## 11. Test de cierre

```text
Definition create/read/update/disable
→ restart/readback state
→ schedule/timezone
→ enqueue priority
→ bounded parallel execution
→ dedup/idempotency
→ timeout/retry
→ heartbeat + lease recovery
→ checkpoint/resume
→ memory write/read
→ artifact write/readback
→ sandbox isolation
→ failure path
→ final evidence
```

Si cualquiera falla: `GAP`, reparar en el paso responsable y repetir.

## 12. Handoff para Grok / GPT-5.6 Sol / Astra

```text
READ_THIS_FIRST = true
CONTRACT = yaiwes.watchdog.minimax.v1
STEPS = 3
NO_NEW_PHASES = true
NO_UNMEASURED_100X_CLAIMS = true

NEXT_ACTIONS:
1. Materialize schemas + JobABI + Ports.
2. Wire minimum owners and parallel runtime.
3. Run E2E tests and close only with evidence/readback.

DEPENDENCY:
- TAREA 2 must continue integrating components arriving in Core kernel Yaiwes/ into canonical Agente Yaiwes principal/ destinations.

DO_NOT:
- create provider-specific coupling in consumers
- replace real adapters with source_probe placeholders
- add infrastructure without a demonstrated GAP
- claim PASS from folder existence
```

## 13. Enlaces canónicos

- Contrato: https://github.com/maxbry123-commits/agentes/blob/main/Core%20kernel%20Yaiwes/Backend%20watchdog%20workflow%20adaptativo/CONTRATO-MINIMAX-WATCHDOG-PARALELO-SANDBOX-MEMORIA.md
- Plan TAREA 3: https://github.com/maxbry123-commits/agentes/blob/main/%F0%9F%93%82%20Readme%20plan%20wachdog%20y%20trabajo%20en%20paralelo.md
- Plan TAREA 2: https://github.com/maxbry123-commits/agentes/blob/main/Readme%20arquitectura%20Yaiwes/HANDOFF-INTEGRACION-1-20.md
