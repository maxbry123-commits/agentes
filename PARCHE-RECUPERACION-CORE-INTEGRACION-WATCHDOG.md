# PARCHE DE RECUPERACIÓN — CORE INTEGRACIÓN + WATCHDOG YAIWES

**Repositorio:** `maxbry123-commits/agentes`  
**Rama canónica:** `main`  
**Fecha:** 2026-09-10  
**Propósito:** permitir recuperar el trabajo completo de integración 1–20 y construcción del Watchdog en una nueva sesión sin depender del historial del chat.

---

## 1. Regla de recuperación

En caso de pérdida de contexto, leer en este orden:

```text
1. ESTE PARCHE
2. Readme arquitectura Yaiwes/HANDOFF-INTEGRACION-1-20.md
3. 📂 Readme Handoff core integracion y wachdog.md
4. 📂 Bitácora stated JSON Craxy wall.json
5. Core kernel Yaiwes/Crack wall bitácora stated JSON/STATE.json
6. 📂 Readme arquitectura Yaiwes.md
7. 📂 Readme plan wachdog y trabajo en paralelo.md
8. PLAN-WATCHDOG-PROGRAMMING-V2.json
9. READ-BACK FÍSICO DEL REPO
```

Si un documento contradice el estado físico de `main`, prevalece el estado físico y se corrige el documento. No inferir un cierre por nombres de carpetas, comentarios o logs parciales.

---

## 2. Estado exacto de integración 1–20

Contrato obligatorio:

```text
PASO 1 MOVE 1–20
→ PASO 2 WIRE + PRUNE 1×1 SIN TESTS
→ PASO 3 TEST 1×1
→ CIERRE
```

### Paso 1 — CERRADO FÍSICAMENTE

Evidencia fresca:

- Workflow: `YAIWES Motor4 Final MOVE 20`.
- Archivo: `.github/workflows/yaiwes-motor4-move-20-final.yml`.
- Run `34445710787`: `completed / success`.
- Job `102771861495`: `completed / success`.
- Step `Verify Motor4 immutable SHA`: success.
- Step `Execute MOVE 1-20`: success.
- Step `Publish physical MOVE to main`: success.
- Step `Read back all 20 from origin main`: success.
- Commit de movimiento final localizado en `main`: `a3cf705f58f95cce65d1c230cb00abcab39732b2`.

**Interpretación correcta:** el MOVE de los 20 quedó físicamente publicado y leído de vuelta desde `main`. Esto no significa que 20/20 tengan todavía cableado + pruebas cerradas.

### Paso 2 — FRONTERA ACTUAL

Estado: `PENDING / CURRENT_BOUNDARY`.

Por componente:

```text
X-RAY
→ GAP REAL
→ A/B/C
→ PORT/ADAPTER
→ FICHA CONTRACT V2
→ WIRING
→ REGISTRY
→ PODA MÍNIMA SEGURA
→ EVIDENCIA
```

No ejecutar tests en este paso.

### Paso 3 — PENDIENTE

Por componente:

```text
contract validation
→ import/build
→ mount/registry
→ behavior
→ health/heartbeat
→ failure path
→ evidence
→ read-back
→ PASS | GAP
```

No crear un Paso 4. Reparar el GAP en el paso actual y repetir.

---

## 3. Las tres opciones de integración A/B/C

### A — SUBAGENT / CHILD

Usar cuando el componente mantiene agencia: goal/lifecycle/tools/memory/context/decisión propia.

Integración:

`YAIWES → AgentPort → policy/budget → sandbox/runtime aislado → subagente → resultado normalizado → evidence`.

Justificación: un agente autónomo no debe convertirse en lógica interna del microkernel determinista.

### B — WORKFLOW / DAG / POOL

Usar cuando la capacidad central es scheduling, DAG, state-machine, queue, workers, durable execution, multi-step o loop.

Integración:

`TaskClassifier → WorkflowPort/ExecutionPort → motor → state/events → result normalizer → evidence`.

Justificación: el motor ejecuta la coordinación local, mientras YAIWES conserva autoridad de policy, objetivo y cierre.

### C — MODULAR CAPABILITY

Usar cuando se necesita una capacidad aislada: schema, auth, policy, storage, memory, routing, observability, research utility, sandbox helper, etc.

Integración:

`Capability → Adapter → Ficha/Contract → Registry → UniversalPluginBus/Port → YAIWES → evidence`.

Justificación: minimiza acoplamiento y evita incorporar repositorios completos cuando solo se necesita una función.

---

## 4. Backend Watchdog — inventario físico recuperado

Raíz:

`Core kernel Yaiwes/Backend watchdog workflow adaptativo/`

### Componentes base presentes

| Componente | Rol | Estado físico | Ruta / estrategia |
|---|---|---|---|
| APScheduler | TIME_AUTHORITY | PRESENT | `time-scheduling/apscheduler/`; owner detrás de `SchedulerPort` |
| Workalendar | WORK_CALENDAR | PRESENT | `work-calendar/workalendar/`; `CalendarPolicy` |
| Celery | SIMPLE_JOB_WORKERS | PRESENT | `Agente Yaiwes principal/execution-engine-pool/parallel-dispatch/celery/`; usar por referencia/adapter |
| Redis | EVENT_TRANSPORT | PRESENT | `event-plane/redis/`; streams/leases/heartbeat, no source of truth única |
| Hatchet | DURABLE_LONG_JOB | PRESENT | `durable-execution/hatchet/`; primary detrás de `DurableExecutionPort` |
| Dagu | MULTI_STEP_JOB | PRESENT | `workflow-multistep/dagu/`; primary detrás de `WorkflowPort` |
| PostgreSQL | DURABLE_SOURCE_OF_TRUTH | PRESENT | `persistent-state/postgresql/`; definitions/runs/steps/checkpoints/idempotency |
| pgvector | SEMANTIC_MEMORY | PRESENT | `persistent-memory/pgvector/`; semantic retrieval |
| gVisor | SANDBOX_ISOLATION | PRESENT | `sandbox-isolation/gvisor/`; sandbox profile |
| RustFS | S3_COMPATIBLE_ARTIFACTS | PRESENT | `artifact-storage/rustfs/`; `ArtifactPort` |

### Componentes adicionales presentes

- Rocketry — scheduler alternativo.
- Taskiq — queue/worker alternativo.
- DBOS Python — durable execution alternativo.
- Restate — durable execution alternativo.
- PocketFlow — small loop.
- Apache Hamilton — functional DAG/cascade.
- redun — DAG/workflow alternativo.
- smolagents — adaptive planning capability subordinada.
- DeerFlow — research provider.
- GPT-Researcher — research provider.
- MindSearch — research provider.
- Firecracker — sandbox high isolation.
- iii-sandbox — sandbox runtime candidate.

### GAP backend real

No hace falta descargar otro gran orquestador para iniciar. Faltan interfaces e integración:

`WatchdogDefinition`, `WatchdogRun`, `WatchdogStep`, `Checkpoint`, `EventEnvelope`, `SchedulerPort`, `QueuePort`, `DurableExecutionPort`, `WorkflowPort`, `ResearchPort`, `PlanningPort`, `SandboxPort`, `StatePort`, `SemanticMemoryPort`, `ArtifactPort`, idempotency, leases, heartbeat, retry, timeout, recovery, health y evidence.

Backblaze B2: no está demostrado un binding específico dentro de la raíz. RustFS ya cubre object storage S3-compatible; si B2 se selecciona, crear un provider adapter al mismo `ArtifactPort`.

---

## 5. Frontend Watchdog — estado y GAP

Repositorio: `maxbry123-commits/frontend`.

Índice revisado: `📂 Indice fromtend componentes.md`.

### Demostrado

- `assistant-ui` — `EXTRACTED / COMPLETE`; shell/chat/streaming/composer.
- `Dockview` — `EXTRACTED / COMPLETE`; workspace de paneles acoplables.
- `xyflow` — `ZIP_ONLY / COMPLETE`; el artefacto existe, pero se debe extraer y hacer read-back como código navegable antes de integrarlo.

### No demostrado en el índice revisado

- FullCalendar — calendar/schedule panel.
- TanStack Table — queue/runs/evidence.
- react-jsonschema-form — formulario declarativo `WatchdogDefinition`.
- xterm.js — logs/terminal de sandbox.
- Monaco Editor — DSL/policy/config editor.
- Apache ECharts — métricas/health/queue depth.
- dnd-kit — drag/drop de steps/tareas.
- Frappe Gantt — timeline opcional para jobs largos.

No sustituir UI YAIWES con otro chat completo. Se integran módulos/paneles.

---

## 6. Workflow Watchdog a construir

```text
USER / CHAT
→ WATCHDOG CREATOR
→ WatchdogDefinition
→ SCHEMA VALIDATION
→ POLICY / SHERIFF
→ PostgreSQL
→ APScheduler + Workalendar
→ DUE EVENT
→ WatchdogRun + IDEMPOTENCY KEY
→ PRIORITY QUEUE
→ TASK CLASSIFIER
→ SELECT ENGINE
→ ACQUIRE LEASE
→ SANDBOX
→ LOAD STATE / MEMORY / EVIDENCE
→ PRELINE / POLICY
→ EXECUTE
→ HEARTBEAT
→ CHECKPOINT
→ VERIFY
→ SAVE RESULT / EVIDENCE / ARTIFACT
→ COMPLETE | RETRY | ROLLBACK | REPLAN
→ NEXT RUN
```

Routing:

```text
SIMPLE       → Celery primary | Taskiq alternative
DURABLE LONG → Hatchet primary | DBOS/Restate alternatives
MULTI-STEP   → Dagu
SMALL LOOP   → PocketFlow
DAG/CASCADE  → Apache Hamilton/redun
RESEARCH     → ResearchPort → DeerFlow/GPT-Researcher/MindSearch
ADAPTIVE     → YAIWES + PlanningPort + optional smolagents + PRELINE/policy
STATE        → PostgreSQL
MEMORY       → pgvector
EVENTS       → Redis
SANDBOX      → gVisor/Firecracker profiles
ARTIFACTS    → RustFS/S3; optional B2 adapter
```

---

## 7. Trabajo en paralelo

Regla: `N Watchdogs registrados != N procesos activos`.

Controles obligatorios:

- priority queue;
- concurrency groups;
- persistent worker pools;
- batching;
- sharding;
- fan-out/fan-in;
- backpressure;
- dedup;
- idempotency keys;
- leases;
- DLQ;
- queue-depth autoscaling;
- per-agent/model/provider limits;
- sandbox/workspace isolation;
- checkpoint/resume.

---

## 8. Recovery operativo del Watchdog

```text
FAIL != RESET

FAIL
→ LOCALIZE
→ FREEZE EVIDENCE
→ CHECK LEASE / HEARTBEAT
→ CHECKPOINT
→ CHECK IDEMPOTENCY
→ RETRY IF SAFE
→ STRATEGY DELTA / FALLBACK IF REQUIRED
→ ROLLBACK OR FORK IF REQUIRED
→ VERIFY
→ RESUME
```

PostgreSQL conserva estado durable; Redis eventos/leases; pgvector memoria semántica; RustFS/S3 snapshots/artefactos; sandbox conserva el workspace según perfil/runtime.

---

## 9. Commits de actualización de este parche de trabajo

| Cambio | Commit |
|---|---|
| Crear `📂 Readme arquitectura Yaiwes.md` | `3b58e808f17bb4d763422cc3af1d5e861bad4edf` |
| Crear `📂 Readme Handoff core integracion y wachdog.md` | `af0b1dc1af2c79921d204edde93ab5d2f07d1112` |
| Crear `📂 Readme plan wachdog y trabajo en paralelo.md` | `6000509c3632bd8b20ba51356ff4cc3dafa3e411` |
| Crear `📂 Bitácora stated JSON Craxy wall.json` | `72762056a4972048764805db4cae19571658fba7` |
| Actualizar Handoff canónico 1–20 | `e3bd4561f9ca57468abf99526a3dea7ff64f64e4` |
| Sincronizar `STATE.json` | `95bae10968b4021c601aa13916ef8adf3adcb41f` |
| Sincronizar plan Watchdog machine-readable | `61807cabc947d0ee79b2084bab9614925ed0e114` |

---

## 10. Enlaces directos

- Repo agentes: https://github.com/maxbry123-commits/agentes
- Arquitectura canónica histórica: https://github.com/maxbry123-commits/agentes/blob/main/Readme%20arquitectura%20Yaiwes/README.md
- Arquitectura detallada integración + Watchdog: https://github.com/maxbry123-commits/agentes/blob/main/%F0%9F%93%82%20Readme%20arquitectura%20Yaiwes.md
- Handoff canónico 1–20: https://github.com/maxbry123-commits/agentes/blob/main/Readme%20arquitectura%20Yaiwes/HANDOFF-INTEGRACION-1-20.md
- Handoff core integración + Watchdog: https://github.com/maxbry123-commits/agentes/blob/main/%F0%9F%93%82%20Readme%20Handoff%20core%20integracion%20y%20wachdog.md
- Plan Watchdog + paralelo: https://github.com/maxbry123-commits/agentes/blob/main/%F0%9F%93%82%20Readme%20plan%20wachdog%20y%20trabajo%20en%20paralelo.md
- Crazy Wall nuevo: https://github.com/maxbry123-commits/agentes/blob/main/%F0%9F%93%82%20Bit%C3%A1cora%20stated%20JSON%20Craxy%20wall.json
- STATE: https://github.com/maxbry123-commits/agentes/blob/main/Core%20kernel%20Yaiwes/Crack%20wall%20bit%C3%A1cora%20stated%20JSON/STATE.json
- Plan Watchdog machine-readable: https://github.com/maxbry123-commits/agentes/blob/main/Core%20kernel%20Yaiwes/Crack%20wall%20bit%C3%A1cora%20stated%20JSON/PLAN-WATCHDOG-PROGRAMMING-V2.json
- Backend Watchdog: https://github.com/maxbry123-commits/agentes/tree/main/Core%20kernel%20Yaiwes/Backend%20watchdog%20workflow%20adaptativo
- Motor4 run final: https://github.com/maxbry123-commits/agentes/actions/runs/34445710787
- Motor4 MOVE commit: https://github.com/maxbry123-commits/agentes/commit/a3cf705f58f95cce65d1c230cb00abcab39732b2
- Frontend repo: https://github.com/maxbry123-commits/frontend
- Frontend component index: https://github.com/maxbry123-commits/frontend/blob/main/%F0%9F%93%82%20Indice%20fromtend%20componentes.md
- Este parche: https://github.com/maxbry123-commits/agentes/blob/main/PARCHE-RECUPERACION-CORE-INTEGRACION-WATCHDOG.md

---

## 11. Primer punto de reanudación

No repetir el MOVE 1–20: está cerrado por run + publish + read-back.

Reanudar en:

`STEP_2_WIRE_PRUNE_1X1_NO_TESTS`.

En paralelo documental se puede preparar el contrato Watchdog, pero no promover el Watchdog a runtime canónico hasta cerrar el contrato de integración 1–20 según el bloqueo registrado en el plan.
