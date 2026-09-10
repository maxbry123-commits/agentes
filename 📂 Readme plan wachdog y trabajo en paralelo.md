# 📂 README PLAN WATCHDOG Y TRABAJO EN PARALELO

**Estado:** `ACTIVE_DESIGN / IMPLEMENTATION_PENDING`  
**Fecha:** 2026-09-10  
**Repositorio:** `maxbry123-commits/agentes`

---

## 1. Objetivo

Construir un Watchdog programable dentro de YAIWES que pueda registrar, programar, ejecutar, supervisar, recuperar y cerrar tareas simples, largas, multi-paso, DAG, LOOP, research y planificación adaptativa, manteniendo memoria/estado durable y ejecución paralela controlada.

El sistema debe poder manejar cientos de Watchdogs pendientes sin convertir cada Watchdog en un proceso permanente. La entidad Watchdog es durable en datos; el cómputo se asigna solamente cuando existe trabajo pendiente o un evento due.

---

## 2. Principio de ownership

Cada responsabilidad debe tener un owner lógico y alternativas detrás de un puerto común.

```text
TIME AUTHORITY       → APScheduler
WORK CALENDAR        → Workalendar
SIMPLE WORKERS       → Celery (Taskiq alternativa)
EVENT PLANE          → Redis
DURABLE EXECUTION    → Hatchet (DBOS/Restate alternativas)
MULTI-STEP           → Dagu
SMALL LOOP           → PocketFlow
FUNCTIONAL DAG       → Apache Hamilton/redun
ADAPTIVE PLANNING    → YAIWES + smolagents subordinado
RESEARCH             → ResearchPort → DeerFlow | GPT-Researcher | MindSearch
DURABLE STATE        → PostgreSQL
SEMANTIC MEMORY      → pgvector
SANDBOX ISOLATION    → gVisor / Firecracker según riesgo
SANDBOX RUNTIME      → iii-sandbox tras X-Ray
ARTIFACT STORAGE     → RustFS por ArtifactPort S3-compatible
EXTERNAL B2          → adapter S3/Backblaze B2 opcional
```

No activar dos owners simultáneos para la misma responsabilidad sin una política explícita de routing/fallback.

---

## 3. Contratos a materializar

### WatchdogDefinition

Campos mínimos:

```text
watchdog_id
name
goal
mode: deterministic|adaptive
schedule
timezone
calendar_policy
priority
concurrency_group
max_concurrency
agent_selector
model_selector
tool_policy
workflow_selector
sandbox_profile
timeout
retry_policy
heartbeat_policy
checkpoint_policy
approval_policy
budget_policy
notification_policy
status
created_at
updated_at
```

### WatchdogRun

```text
run_id
watchdog_id
scheduled_for
started_at
finished_at
status
attempt
idempotency_key
lease_owner
lease_expires_at
selected_engine
selected_agent
selected_model
sandbox_id
checkpoint_id
result_ref
evidence_ref
error_class
next_action
```

### WatchdogStep

```text
step_id
run_id
parent_step_id
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
created_at
resume_token
integrity_hash
```

---

## 4. Flujo de creación

```text
USER/CHAT
→ Watchdog Creator
→ WatchdogDefinition JSON Schema
→ VALIDATOR
→ POLICY/SHERIFF
→ PERSIST PostgreSQL
→ REGISTER APScheduler
→ RETURN WATCHDOG_ID + NEXT_RUN
```

La UI no escribe directamente en el scheduler. La UI envía una definición al backend; el backend valida, persiste y después registra el schedule.

---

## 5. Flujo de ejecución

```text
APScheduler DUE
→ CREATE RUN
→ GENERATE IDEMPOTENCY KEY
→ ACQUIRE LEASE
→ APPLY CALENDAR POLICY
→ PRIORITY QUEUE
→ CLASSIFY
→ SELECT ENGINE
→ BUILD CONTEXT PACK
→ CREATE/RESUME SANDBOX
→ PRELINE/POLICY
→ EXECUTE
→ HEARTBEAT
→ CHECKPOINT
→ VERIFY
→ SAVE RESULT + EVIDENCE
→ RELEASE LEASE
→ RESCHEDULE / COMPLETE
```

---

## 6. Clasificador de tareas

### SIMPLE

Características: una función, job corto, retries simples, poca coordinación.

Ruta:

`QueuePort → Celery`

Fallback/alternativa permitida:

`QueuePort → Taskiq`

### DURABLE_LONG

Características: trabajo largo, necesidad de reanudación/retries durable, espera externa, actividad multi-minuto/hora.

Ruta primaria:

`DurableExecutionPort → Hatchet`

Alternativas:

`DBOS Python` o `Restate`, solamente bajo policy/benchmark y sin acoplar el workflow a su API nativa.

### MULTI_STEP

Características: dependencias, varios pasos, retries por paso, ramas y orden explícito.

Ruta:

`WorkflowPort → Dagu`

### SMALL_LOOP

Características: secuencia compacta con condición/repetición local.

Ruta:

`WorkflowPort → PocketFlow`

### DAG/CASCADE

Características: funciones dependientes, pipeline reproducible, cascada de transformaciones.

Ruta:

`WorkflowPort → Apache Hamilton | redun`

### RESEARCH

Ruta:

`ResearchPort → policy selector → DeerFlow | GPT-Researcher | MindSearch`

### ADAPTIVE

Ruta:

```text
GOAL
→ YAIWES planner
→ optional smolagents capability
→ research if needed
→ PRELINE
→ policy/budget
→ deterministic action dispatch
→ observe
→ verify
→ replan only if required
```

---

## 7. Planificación determinista y adaptativa

### Determinista

El usuario define pasos o un contrato estricto.

```text
INPUT
→ DSL
→ DAG
→ SCHEMA
→ VALIDATE
→ SCHEDULE
→ EXECUTE
→ VERIFY
```

No existe libertad del modelo para modificar el orden fuera de las condiciones declaradas.

### Adaptativa

El usuario define un objetivo y restricciones.

```text
GOAL
→ STATE/MEMORY/EVIDENCE
→ PLAN
→ RESEARCH
→ REFUTE
→ PRELINE
→ EXECUTE
→ OBSERVE
→ VERIFY
→ REPLAN?
```

El replan debe conservar `goal_lock`, presupuesto, permisos, seguridad y criterio de cierre.

---

## 8. Arquitectura de paralelismo

### Regla

`500 Watchdogs registrados` puede significar `10 workers activos`, no 500 procesos.

### Cola

Cada job entra con:

```text
priority
watchdog_id
run_id
project_id
resource_class
agent/model requirement
estimated_cost
deadline
concurrency_group
idempotency_key
```

### Pools

Separar al menos:

- CPU/light jobs;
- network/API jobs;
- coding/sandbox jobs;
- research jobs;
- long-running durable jobs;
- high-risk isolated jobs.

### Backpressure

Cuando la cola supera límites:

1. no crear procesos ilimitados;
2. mantener job durable en PostgreSQL/queue;
3. aplicar priority/deadline;
4. limitar fan-out;
5. retrasar low-priority;
6. escalar pool si la infraestructura lo permite;
7. conservar métricas `queue_depth`, `oldest_wait`, `active_workers`.

### Fan-out/Fan-in

```text
PARENT RUN
→ SPLIT N INDEPENDENT UNITS
→ ENQUEUE WITH SAME GROUP
→ EXECUTE UNDER CONCURRENCY LIMIT
→ COLLECT RESULTS
→ VERIFY EACH
→ CONSOLIDATE
→ CONTINUE PARENT
```

### Sharding

Sharding recomendado por `project_id`, `workspace_id` o `watchdog_id` para evitar que una tarea monopolice toda la capacidad.

---

## 9. Idempotencia y leases

Todo run programado debe tener una clave reproducible:

`watchdog_id + scheduled_for + schedule_version`.

Antes de ejecutar:

1. consultar si la clave ya está completada;
2. adquirir lease;
3. registrar owner y expiry;
4. renovar mediante heartbeat;
5. si el worker muere, permitir recuperación cuando expire el lease;
6. nunca ejecutar dos veces una acción no idempotente sin policy explícita.

---

## 10. Heartbeat

El heartbeat debe diferenciar:

- worker vivo;
- run vivo;
- sandbox vivo;
- conexión de motor durable viva.

La ausencia de heartbeat no significa automáticamente `FAIL`; primero comprobar lease, estado remoto y checkpoint.

---

## 11. Recovery

Estados mínimos:

```text
PENDING
QUEUED
LEASED
RUNNING
WAITING
PAUSED
RETRYING
RECOVERING
COMPLETED
FAILED
CANCELLED
```

Recovery:

```text
DETECT STALE/FAIL
→ FREEZE EVIDENCE
→ CLASSIFY FAILURE
→ CHECK IDEMPOTENCY
→ CHECK CHECKPOINT
→ RETRY SAME ENGINE?
   ├─ YES → RESUME
   └─ NO  → STRATEGY DELTA / FALLBACK ENGINE
→ VERIFY
→ CONTINUE
```

No hacer reset completo si existe checkpoint válido.

---

## 12. Memoria y estado

### PostgreSQL

Guardar definiciones, schedules, runs, steps, leases, idempotency, policy versions, checkpoint metadata y estado final.

### Redis

Usar para transporte/eventos/locks/leases/heartbeats y datos efímeros de coordinación. No utilizarlo como única fuente durable.

### pgvector

Guardar embeddings/referencias semánticas, no reemplazar los records transaccionales.

### Artifact storage

RustFS expone el puerto S3-compatible para artefactos y snapshots. Si se usa Backblaze B2, añadir provider adapter al mismo `ArtifactPort`, sin cambiar a los consumidores.

---

## 13. Sandbox y trabajo en paralelo

Cada ejecución de código debe recibir un `sandbox_profile`:

```text
LOW_RISK        → runtime aislado estándar
MEDIUM_RISK     → gVisor
HIGH_RISK       → Firecracker/microVM
SPECIAL_RUNTIME → iii-sandbox después de validación
```

El sandbox debe recibir únicamente el context pack y recursos autorizados. No montar todo el repositorio ni secretos globales por defecto.

---

## 14. Backend a integrar

### Presentes y seleccionados

- APScheduler — time authority.
- Workalendar — calendar policy.
- Celery — simple workers desde el execution pool existente.
- Redis — event plane.
- Hatchet — durable owner candidato.
- Dagu — multi-step owner candidato.
- PostgreSQL — durable state.
- pgvector — semantic memory.
- gVisor — sandbox isolation.
- RustFS — S3-compatible artifacts.

### Presentes como alternativas/capacidades

- Rocketry.
- Taskiq.
- DBOS Python.
- Restate.
- PocketFlow.
- Apache Hamilton.
- redun.
- smolagents.
- DeerFlow.
- GPT-Researcher.
- MindSearch.
- Firecracker.
- iii-sandbox.

### Backend faltante

No se requiere descargar otro gran motor para iniciar. Se debe construir/cablear la capa de ports/adapters/contracts. Si el proveedor final será Backblaze B2, falta materializar el adapter/configuración B2 sobre S3.

---

## 15. Frontend del Watchdog

### Ya disponible

- assistant-ui — chat/streaming/composer.
- Dockview — workspace/panel docking.
- xyflow — artefacto disponible pero debe extraerse y validarse antes de usarlo como código real.

### A incorporar/verificar

- FullCalendar — calendar/schedule view.
- TanStack Table — queue/runs/evidence.
- RJSF — WatchdogDefinition form.
- xterm.js — logs/sandbox terminal.
- Monaco Editor — DSL/config/policy editor.
- ECharts — observability metrics.
- dnd-kit — drag/drop de pasos/tareas.
- Frappe Gantt — timeline opcional.

### Integración UI

```text
assistant-ui → shell conversacional
Dockview → panel manager
FullCalendar → schedule panel
xyflow → workflow panel
RJSF → definition editor
TanStack Table → runs/queue panel
xterm.js → logs panel
Monaco → advanced config panel
ECharts → metrics panel
```

La UI consume APIs/event streams del backend; no accede directamente a PostgreSQL, Redis o motores internos.

---

## 16. Gates de construcción

### Gate 1 — Contratos

No conectar motores hasta fijar `WatchdogDefinition`, `Run`, `Step`, `Checkpoint`, `EventEnvelope`, `Evidence`.

### Gate 2 — Ports

Crear puertos para scheduler, queue, durable, workflow, research, planning, state, memory, sandbox, artifacts.

### Gate 3 — Adapters

Conectar un owner por puerto y comprobar que la API nativa no fuga al resto del sistema.

### Gate 4 — Persistencia

Persistir definición/run/checkpoint/idempotency antes de activar scheduling real.

### Gate 5 — E2E mínimo

```text
create watchdog
→ persist
→ schedule
→ due
→ queue
→ execute simple no-op/test task
→ heartbeat
→ verify
→ complete
→ next_run
```

### Gate 6 — Durable/multi-step

Probar recovery y multi-step solamente después del E2E mínimo.

### Gate 7 — Adaptive/research

Agregar planificación adaptativa/research después de que el carril determinista sea estable.

### Gate 8 — UI

Conectar UI cuando backend contract/API/event stream estén definidos. UI no debe retrasar ni gobernar el kernel.

---

## 17. Criterio de finalización del Watchdog

No se considera completo hasta que existan pruebas reales para:

1. create/update/delete/disable WatchdogDefinition;
2. persistencia después de restart;
3. timezone y calendar policy;
4. ejecución exactly-once lógica mediante idempotency;
5. retry;
6. timeout;
7. heartbeat/lease recovery;
8. checkpoint/resume;
9. parallel queue + backpressure;
10. simple job;
11. durable job;
12. multi-step job;
13. small loop;
14. research job;
15. adaptive replan;
16. sandbox isolation;
17. artifacts;
18. memory/state recovery;
19. UI live status/event stream;
20. read-back de evidencia y cierre fail-closed.
