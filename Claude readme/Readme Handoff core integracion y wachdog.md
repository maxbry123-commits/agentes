# 📂 README HANDOFF CORE INTEGRACIÓN Y WATCHDOG

**Repositorio:** `maxbry123-commits/agentes`  
**Rama:** `main`  
**Estado:** `ACTIVE_HANDOFF`  
**Fecha:** 2026-09-10  
**Regla:** continuar desde evidencia física; no reiniciar trabajo ya demostrado.

---

## 1. Propósito del Handoff

Este Handoff concentra en un solo documento la continuidad de dos líneas de trabajo que deben permanecer relacionadas pero no confundirse:

1. **Integración de los 20 componentes YAIWES**, bajo el contrato exacto de tres pasos.
2. **Construcción del Watchdog programable**, usando los componentes backend y frontend ya presentes o aún faltantes.

El Watchdog no debe invalidar el contrato de integración 1–20. Las decisiones A/B/C forman parte del análisis de cómo vive cada componente; no añaden fases al contrato operativo de tres pasos.

---

## 2. Orden de fuente de verdad

```text
1. ESTADO FÍSICO REAL EN main
2. HASH / TREE / READ-BACK / TEST / HEALTH
3. STATE Y CRAZY WALL ACTUALIZADOS
4. HANDOFF Y README
5. HISTÓRICO
6. INFERENCIA
```

No aceptar un `VERIFIED_CLOSED` histórico si el destino físico actual no lo demuestra.

---

# BLOQUE A — INTEGRACIÓN DE COMPONENTES YAIWES

## 3. Contrato exacto de tres pasos

```text
PASO 1 — MOVE FÍSICO
        ↓
PASO 2 — WIRE + PRUNE 1×1 SIN TESTS
        ↓
PASO 3 — TEST 1×1
        ↓
VERIFIED_CLOSED
```

No existe Paso 4. Si aparece un GAP, se resuelve dentro del paso donde apareció.

---

## 4. PASO 1 — MOVE físico

### Objetivo

Mover el árbol original de cada componente desde su ubicación actual al destino canónico YAIWES, preservando bytes y estructura útil.

### Reglas

- MOVE dentro del mismo repositorio; no crear una segunda copia arbitraria.
- No reescribir código upstream.
- No cablear.
- No podar.
- No ejecutar tests.
- No considerar completo un MOVE ocurrido solo en un runner.
- Publicar commit/push a `main`.
- Hacer read-back desde `origin/main`.
- Verificar que el destino contiene archivos y que el origen quedó vacío/eliminado o deduplicado con hashes equivalentes.

### Flujo

```text
DISCOVER SOURCE
→ BUILD MANIFEST
→ HASH
→ CREATE DESTINATION
→ MOVE IN BATCHES
→ VERIFY FILE HASH
→ REMOVE/DEDUP SOURCE
→ COMMIT
→ REBASE/RESOLVE MAIN
→ PUSH
→ FRESH READ-BACK
```

### Cierre

`20/20 destinos físicos verificados desde main`.

---

## 5. PASO 2 — Wire + prune 1×1 sin tests

### Objetivo

Convertir cada árbol ya movido en una capacidad consumible por YAIWES sin romper upstream ni crear acoplamientos directos.

### Secuencia por componente

```text
X-RAY DEL DESTINO
→ IDENTIFICAR FUNCIÓN REAL
→ IDENTIFICAR GAP YAIWES
→ DECIDIR A/B/C
→ DEFINIR PORT/CONTRACT
→ ADAPTER
→ FICHA CONTRACT V2
→ WIRING
→ REGISTRY
→ PODA MÍNIMA SEGURA
→ EVIDENCIA DE CABLEADO
```

### Poda permitida

- CI upstream que no participa en runtime YAIWES.
- archivos de development environment no necesarios.
- duplicados demostrados.
- demos/examples que no sean dependencia del runtime.

### Poda prohibida

- runtime.
- licenses/NOTICE.
- schemas necesarios.
- configuración requerida.
- assets/runtime dependencies.
- código cuya no-utilización no haya sido demostrada.

### Regla crítica

**No ejecutar tests en Paso 2.**

---

## 6. PASO 3 — Test 1×1

Cada componente se prueba después de que Paso 2 esté terminado para la cola correspondiente.

### Gate mínimo

```text
DESTINATION EXISTS
→ CONTRACT/FICHA VALID
→ ADAPTER IMPORT/BUILD
→ WIRING RESOLVES
→ REGISTRY/MOUNT
→ HEALTH
→ BEHAVIOR
→ FAILURE PATH / FAIL-CLOSED
→ HEARTBEAT/EVIDENCE
→ READ-BACK
→ PASS | GAP
```

Si falla, registrar GAP, reparar, repetir el test del mismo componente y continuar solamente cuando el criterio esté cumplido.

---

# BLOQUE B — ANÁLISIS X-RAY Y OPCIONES A/B/C

## 7. X-Ray obligatorio antes de integrar

El X-Ray no es una fase nueva; es el análisis que permite ejecutar correctamente el Paso 2.

Para cada componente revisar:

1. árbol físico y archivos de runtime;
2. entrypoints;
3. imports/dependencias;
4. inputs/outputs;
5. contratos/schemas;
6. estado/persistencia;
7. scheduling/colas/workers;
8. DAG/FSM/loops;
9. memoria;
10. sandbox;
11. permisos/seguridad;
12. llamadas LLM;
13. rutas deterministas;
14. servicios externos;
15. puntos de extensión;
16. duplicados con YAIWES;
17. qué se puede conservar intacto;
18. qué necesita adapter;
19. qué puede podarse;
20. qué GAP real cubre.

Si una propiedad no puede demostrarse: `GAP / NO_DETERMINABLE`.

---

## 8. Opción A — Subagente / hijo

### Cuándo usar A

Cuando el componente conserva agencia propia:

- objetivo propio;
- lifecycle;
- toolset;
- memoria o contexto propio;
- planificación;
- delegación;
- capacidad de tomar decisiones;
- estado de ejecución independiente.

### Integración

```text
YAIWES
→ AgentPort / Contract
→ Policy + Budget + Permission
→ Isolated Runtime/Sandbox
→ SUBAGENT
→ Normalized Result
→ Evidence
→ YAIWES
```

Nunca meter un agente autónomo completo dentro del microkernel determinista.

---

## 9. Opción B — Workflow / DAG / pool

### Cuándo usar B

Cuando el valor principal es:

- scheduler;
- DAG;
- state-machine;
- durable execution;
- workers;
- queue;
- fan-out/fan-in;
- pipeline;
- multi-step;
- loop operacional.

### Integración

```text
YAIWES CONTRACT
→ TASK CLASSIFIER
→ WorkflowPort / ExecutionPort
→ ENGINE B
→ STATE/EVENTS
→ RESULT NORMALIZER
→ EVIDENCE
```

El motor ejecuta; no gobierna la política global.

---

## 10. Opción C — Capacidad modular

### Cuándo usar C

Cuando solo se requiere una capacidad concreta:

- schema validation;
- authorization;
- storage;
- policy;
- routing;
- memory;
- research utility;
- observability;
- sandbox helper;
- reasoning utility.

### Integración

```text
CAPABILITY
→ Adapter
→ Ficha/Contract
→ Capability Registry
→ Universal Plugin Bus / Port
→ YAIWES CALL
→ Normalized Output
→ Evidence
```

Objetivo general: coordinación y verificaciones deterministas; LLM solamente donde aporta valor no reducible a reglas.

---

## 11. Registro mínimo A/B/C

Por cada componente dejar:

```text
NAME
SOURCE
DESTINATION
PHYSICAL STATE
FUNCTION
INPUTS
OUTPUTS
STATE
DEPENDENCIES
YAIWES GAP
A/B/C
JUSTIFICATION
KEEP
PRUNE
ADAPTER/PORT
FICHA
WIRING
REGISTRY
TEST
EVIDENCE
COMMIT/SHA
FINAL VERDICT
```

---

# BLOQUE C — WATCHDOG PROGRAMABLE

## 12. Backend físico ya disponible

Raíz:

`Core kernel Yaiwes/Backend watchdog workflow adaptativo/`

### Scheduling

- APScheduler — `time-scheduling/apscheduler/` — presente.
- Rocketry — `time-scheduling/rocketry/` — presente como alternativa.
- Workalendar — `work-calendar/workalendar/` — presente.

### Queue/workers

- Taskiq — `queue-execution/taskiq/` — presente.
- Celery — `Agente Yaiwes principal/execution-engine-pool/parallel-dispatch/celery/` — presente en árbol YAIWES; consumir por referencia, no duplicar.

### Events

- Redis — `event-plane/redis/` — presente.

### Durable execution

- Hatchet — presente.
- DBOS Python — presente.
- Restate — presente.

### Multi-step / LOOP / DAG

- Dagu — presente.
- PocketFlow — presente.
- Apache Hamilton — presente.
- redun — presente.

### Adaptive planning / research

- smolagents — presente.
- DeerFlow — presente.
- GPT-Researcher — presente.
- MindSearch — presente.

### State / memory

- PostgreSQL — presente.
- pgvector — presente.

### Sandbox

- gVisor — presente.
- Firecracker — presente.
- iii-sandbox — presente.

### Artifacts

- RustFS — presente como object storage S3-compatible.
- Backblaze B2 binding específico — pendiente/no demostrado.

---

## 13. Qué falta en backend

No falta otro gran motor OSS para iniciar. Faltan las capas de integración y ownership:

- WatchdogDefinition schema.
- WatchdogRun/Step/Checkpoint schema.
- SchedulerPort.
- QueuePort.
- WorkflowPort.
- DurableExecutionPort.
- ResearchPort.
- PlanningPort.
- SandboxPort.
- StatePort.
- SemanticMemoryPort.
- ArtifactPort.
- EventEnvelope.
- idempotency/lease/heartbeat.
- retry/timeout/recovery policy.
- provider adapter S3/Backblaze B2 si se usa B2.
- registry/mount/health/evidence comunes.

La prioridad es integrar lo que ya existe, no descargar otra colección de frameworks.

---

## 14. Frontend Watchdog

Repositorio fuente:

`maxbry123-commits/frontend`

### Disponible físicamente según índice frontend

- assistant-ui — `EXTRACTED / COMPLETE`.
- Dockview — `EXTRACTED / COMPLETE`.
- xyflow — `ZIP_ONLY / COMPLETE`; requiere extracción/read-back como árbol antes de integración.

### GAP frontend a cubrir

- FullCalendar — calendario y agenda.
- TanStack Table — queue/runs/evidence tables.
- react-jsonschema-form — formulario declarativo WatchdogDefinition.
- xterm.js — consola/logs.
- Monaco Editor — DSL/policy/config editor.
- Apache ECharts — health/metrics/latency/queue depth.
- dnd-kit — reorder/drag/drop de tareas/steps.
- Frappe Gantt — timeline opcional de jobs largos.
- tool-call/approval cards — elegir extensión sobre assistant-ui antes de añadir otro framework grande.

### Regla UI

No sustituir UI YAIWES. Cada componente se integra como módulo/panel reutilizable.

---

## 15. Workflow funcional objetivo del Watchdog

```text
USER/CHAT
→ CREATE/UPDATE WATCHDOG DEFINITION
→ VALIDATE SCHEMA
→ STORE DEFINITION
→ SCHEDULER REGISTER
→ WAIT
→ DUE EVENT
→ CREATE RUN + IDEMPOTENCY KEY
→ PRIORITY QUEUE
→ CLASSIFY TASK
→ SELECT ENGINE
→ ACQUIRE LEASE
→ SANDBOX
→ LOAD MEMORY/STATE
→ PRELINE/POLICY
→ EXECUTE
→ HEARTBEAT
→ CHECKPOINT
→ VERIFY
→ SAVE RESULT/EVIDENCE
→ COMPLETE/RETRY/ROLLBACK/REPLAN
→ COMPUTE NEXT RUN
```

---

## 16. Dos vías del Watchdog

### Vía determinista

```text
USER STRICT FLOW
→ DSL
→ DAG
→ SCHEMA
→ CONTRACT
→ VALIDATOR/SHERIFF
→ SCHEDULER
→ EXECUTION
→ VERIFY
```

La LLM no puede alterar arbitrariamente el grafo ni el contrato.

### Vía adaptativa

```text
GOAL
→ LOAD STATE/MEMORY/EVIDENCE
→ PLAN
→ RESEARCH IF NEEDED
→ REFUTE
→ PRELINE/POLICY
→ EXECUTE
→ OBSERVE
→ VERIFY
→ REPLAN? → LOOP
```

El plan puede variar; el objetivo, permisos, presupuesto y criterios de cierre siguen gobernados por YAIWES.

---

## 17. Trabajo en paralelo

Regla: `500 Watchdogs pendientes ≠ 500 procesos simultáneos`.

El control deberá aplicar:

- prioridad;
- límites de concurrencia;
- pools persistentes;
- fan-out/fan-in;
- batching;
- sharding;
- backpressure;
- dedup;
- idempotency;
- leases;
- DLQ;
- autoscaling por queue depth;
- aislamiento por proyecto;
- cuotas por modelo/agente/API.

---

## 18. Recovery

```text
FAIL
→ RECORD FAILURE + EVIDENCE
→ CHECK HEARTBEAT/LEASE
→ CHECKPOINT
→ RETRY IF IDEMPOTENT
→ ROLLBACK/FORK IF NEEDED
→ REPAIR/REPLAN
→ RESUME
```

Nunca borrar todo el progreso por un fallo local.

---

## 19. Archivos de continuidad

- `📂 Readme arquitectura Yaiwes.md`
- `📂 Readme Handoff core integracion y wachdog.md`
- `📂 Readme plan wachdog y trabajo en paralelo.md`
- `📂 Bitácora stated JSON Craxy wall.json`
- `Readme arquitectura Yaiwes/HANDOFF-INTEGRACION-1-20.md`
- `Readme arquitectura Yaiwes/README.md`
- `Core kernel Yaiwes/Crack wall bitácora stated JSON/STATE.json`
- `Core kernel Yaiwes/Crack wall bitácora stated JSON/PLAN-WATCHDOG-PROGRAMMING-V2.json`
- `PARCHE-RECUPERACION-CORE-INTEGRACION-WATCHDOG.md`

En una sesión nueva: leer Handoff → Crazy Wall → arquitectura → plan → evidencia física y continuar desde el primer GAP real.
