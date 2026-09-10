# 📂 README ARQUITECTURA YAIWES — INTEGRACIÓN + WATCHDOG

**Repositorio:** `maxbry123-commits/agentes`  
**Rama:** `main`  
**Estado del documento:** `ACTIVE / RECOVERY-CANONICAL-COMPANION`  
**Fecha de actualización:** 2026-09-10  
**Fuente de verdad:** `estado físico del repositorio > evidencia de ejecución > STATE/bitácora > documentación > inferencia`.

Este archivo no sustituye silenciosamente `Readme arquitectura Yaiwes/README.md`; lo complementa con la fotografía operativa detallada de integración de componentes y el diseño del Watchdog programable. Cuando exista discrepancia, debe prevalecer el read-back físico del repositorio y el `STATE.json` actualizado.

---

## 1. Objetivo arquitectónico

YAIWES debe separar cinco responsabilidades que no pueden mezclarse en un único monolito:

1. **Control determinista:** contratos, DSL, DAG, scheduler, colas, estado, idempotencia, policy, recovery y evidencia.
2. **Ejecución:** workers, durable execution, multi-step workflows, sandboxes y pools paralelos.
3. **Razonamiento bajo demanda:** planificación adaptativa, research, selección de estrategia y replan solamente cuando una regla determinista no es suficiente.
4. **Memoria/estado:** fuente durable, memoria semántica, eventos, checkpoints y artefactos.
5. **Interfaz:** chat YAIWES + editor/monitor de Watchdogs, sin convertir la UI en fuente de verdad del runtime.

Principio rector:

```text
EL MODELO PIENSA CUANDO ES NECESARIO
EL RUNTIME CONTROLA
EL SCHEDULER DESPIERTA
LA COLA PRIORIZA
EL WORKFLOW ORGANIZA
EL SANDBOX AÍSLA
LA MEMORIA RECUERDA
EL SHERIFF/JUDGE VERIFICA
EL WATCHDOG SUPERVISA
YAIWES CONSERVA EL OBJETIVO GLOBAL
```

---

## 2. Arquitectura del Watchdog programable

```text
CHAT / UI YAIWES
        ↓
WATCHDOG DEFINITION + REGISTRY
        ↓
CONTRACT / SCHEMA / POLICY
        ↓
CALENDAR + TIME AUTHORITY
        ↓
SCHEDULER
        ↓
DUE EVENT
        ↓
QUEUE + PRIORITY + BACKPRESSURE + IDEMPOTENCY
        ↓
TASK CLASSIFIER
   ├── SIMPLE JOB
   ├── DURABLE JOB
   ├── MULTI-STEP DAG
   ├── SMALL LOOP
   ├── RESEARCH
   └── ADAPTIVE PLAN
        ↓
RUNTIME / WORKER / WORKFLOW ENGINE
        ↓
SANDBOX / ISOLATION
        ↓
AGENT + MODEL + TOOLS
        ↓
STATE + MEMORY + EVENT LOG
        ↓
CHECKPOINT + ARTIFACT
        ↓
VERIFY / SHERIFF / EVIDENCE
        ↓
COMPLETE | RETRY | ROLLBACK | REPLAN | RESCHEDULE
```

El Watchdog no es un cron con un prompt. Es una entidad durable que debe conocer su objetivo, contrato, siguiente ejecución, prioridad, estado, historial, heartbeat, checkpoint, política de retry, permisos, recursos, agente/modelo permitido y criterio de cierre.

---

## 3. Inventario físico backend comprobado

Raíz física examinada:

`Core kernel Yaiwes/Backend watchdog workflow adaptativo/`

### 3.1 Scheduling y calendario

- `time-scheduling/apscheduler/` — **PRESENTE**. Autoridad de programación temporal, intervalos, fechas, cron y timezone.
- `time-scheduling/rocketry/` — **PRESENTE**. Alternativa/segundo motor de scheduling; no debe competir con APScheduler sin un selector explícito.
- `work-calendar/workalendar/` — **PRESENTE**. Calendarios laborales, festivos, días hábiles y ventanas de ejecución.

### 3.2 Cola y dispatch

- `queue-execution/taskiq/` — **PRESENTE**. Cola/worker async disponible como capacidad adicional.
- `Agente Yaiwes principal/execution-engine-pool/parallel-dispatch/celery/` — **PRESENTE FUERA DE LA RAÍZ WATCHDOG**. Se debe consumir por referencia/adapter desde el Watchdog; no duplicar el árbol de Celery.

### 3.3 Transporte de eventos

- `event-plane/redis/` — **PRESENTE**. Streams, consumer groups, locks/leases, heartbeat y transporte de eventos. Redis no es la memoria canónica del sistema.

### 3.4 Durable execution

- `durable-execution/hatchet/` — **PRESENTE**. Motor candidato principal para ejecuciones largas/durables.
- `durable-execution/dbos-python/` — **PRESENTE**. Alternativa durable que deberá mantenerse detrás del mismo contrato de puerto.
- `durable-execution/restate/` — **PRESENTE**. Alternativa durable/event-driven; no se activa simultáneamente como owner sin decisión de routing.

### 3.5 Multi-step, DAG, cascada y LOOP

- `workflow-multistep/dagu/` — **PRESENTE**. Motor principal candidato para tareas de varios pasos y DAG operativo.
- `workflow-loop/pocketflow/` — **PRESENTE**. Motor ligero para pequeños loops/flows.
- `dag-cascade/apache-hamilton/` — **PRESENTE**. DAG funcional basado en dependencias; útil para composición/cascada determinista.
- `dag-cascade/redun/` — **PRESENTE**. Alternativa de workflow funcional con memoización/ejecución reproducible.

### 3.6 Planificación adaptativa e investigación

- `adaptive-planning/smolagents/` — **PRESENTE**. Capacidad de agentic planning que debe estar subordinada a policy/preline; nunca controla el scheduler ni la fuente de verdad.
- `research-engine/deerflow/` — **PRESENTE**.
- `research-engine/gpt-researcher/` — **PRESENTE**.
- `research-engine/mindsearch/` — **PRESENTE**.

Los tres motores de research deben exponerse por un único `ResearchPort`; la selección se hace por costo, capacidades, latencia, permisos y política. No se permite que cada workflow acople directamente un motor diferente.

### 3.7 Estado, memoria y artefactos

- `persistent-state/postgresql/` — **PRESENTE**. Fuente durable de verdad para definiciones, runs, steps, checkpoints, locks e idempotency.
- `persistent-memory/pgvector/` — **PRESENTE**. Memoria semántica sobre PostgreSQL; no sustituye el ledger estructurado.
- `artifact-storage/rustfs/` — **PRESENTE**. Object storage S3-compatible local/self-hosted candidato.
- **Backblaze B2 binding específico:** **NO DEMOSTRADO EN LA RAÍZ**. No se debe inventar que RustFS es Backblaze B2; RustFS puede cubrir el puerto S3-compatible y B2 puede añadirse como proveedor externo mediante adapter S3.

### 3.8 Sandbox

- `sandbox-isolation/gvisor/` — **PRESENTE**. Aislamiento de cargas.
- `sandbox-isolation/firecracker/` — **PRESENTE**. MicroVM/aislamiento fuerte como opción de mayor aislamiento.
- `sandbox-runtime/iii-sandbox/` — **PRESENTE**. Runtime adicional que deberá pasar X-Ray antes de ser owner de ejecución.

---

## 4. Qué falta realmente en backend para construir el Watchdog

No falta descargar otro orquestador grande para empezar. La raíz ya contiene las piezas principales y alternativas. Los GAP reales son de **integración**, no de acumulación de repositorios:

1. `WatchdogDefinition` y `WatchdogRun` como contratos canónicos.
2. `SchedulerPort` que normalice APScheduler/Rocketry y elija un owner.
3. `QueuePort` que normalice Celery/Taskiq y aplique prioridad/backpressure.
4. `DurableExecutionPort` para Hatchet/DBOS/Restate.
5. `WorkflowPort` para Dagu/PocketFlow/Hamilton/redun.
6. `ResearchPort` para DeerFlow/GPT-Researcher/MindSearch.
7. `PlanningPort` para planificación adaptativa controlada.
8. `SandboxPort` para gVisor/Firecracker/iii-sandbox.
9. `StatePort` sobre PostgreSQL + `SemanticMemoryPort` sobre pgvector.
10. `ArtifactPort` S3-compatible usando RustFS y adapter opcional a Backblaze B2.
11. Event envelope común sobre Redis.
12. Idempotency key, lease, heartbeat, retry, timeout, checkpoint y recovery comunes a todos los motores.
13. Universal Plugin Bus/registry para montar cada capacidad sin imports cruzados directos.
14. Evidencia y health/read-back obligatorios antes de promover cualquier owner.

Por tanto, **backend OSS grande faltante: ninguno obligatorio para arrancar**. Falta el adapter/proveedor B2 si se exige específicamente Backblaze B2; para object storage S3-compatible ya existe RustFS.

---

## 5. Frontend Watchdog — inventario y faltantes

Fuente inspeccionada: repo `maxbry123-commits/frontend`, índice `📂 Indice fromtend componentes.md` y raíz `📂componentes open soure fromtend/`.

### 5.1 Ya disponible

- **assistant-ui — EXTRACTED / COMPLETE.** Base del chat/agent UI: mensajes, composer, streaming y estados de conversación.
- **Dockview — EXTRACTED / COMPLETE.** Layout de paneles acoplables, tabs y workspace tipo IDE; útil para Chat/Watchdog/Logs/Artifacts/Memory.
- **xyflow / React Flow — ZIP_ONLY / COMPLETE.** El artefacto llegó pero aún no está demostrado como árbol extraído en el índice; debe extraerse antes de integración real.

### 5.2 Componentes frontend que faltan demostrar/adquirir

Estos módulos no aparecen demostrados en el índice frontend revisado y se consideran `GAP / NOT_DEMONSTRATED` hasta read-back físico:

- **FullCalendar** — calendario/agenda visual, recurrencias y planificación temporal.
- **TanStack Table** — tabla virtualizable/ordenable para cola, runs, estados y evidencias.
- **react-jsonschema-form (RJSF)** — generar formularios de creación/edición de Watchdog desde JSON Schema.
- **xterm.js** — terminal/logs interactivos para ejecución y sandbox.
- **Monaco Editor** — edición avanzada de DSL/DAG/configuración/policies.
- **Apache ECharts** — métricas, throughput, latencia, errores, queue depth y timeline.
- **dnd-kit** — drag-and-drop accesible para reordenar tareas/steps y editor de flujos.
- **Frappe Gantt** — Gantt/timeline para trabajos largos y dependencias; opcional si FullCalendar + xyflow cubren la UX requerida.
- **tool-ui / equivalente de tool-call cards** — tarjetas de herramientas/approvals/evidence; debe elegirse solo si no se puede construir con assistant-ui + componentes propios.

Regla frontend: **no instalar otro chat completo**. La UI Watchdog se inserta como módulos dentro de UI YAIWES.

---

## 6. Mapa frontend objetivo

```text
UI YAIWES
├── Chat / assistant-ui
├── Workspace / Dockview
├── Watchdog Creator
│   └── JSON Schema Form
├── Calendar
│   └── FullCalendar
├── Workflow / DAG / LOOP Editor
│   └── xyflow + dnd-kit
├── Queue / Runs / Evidence
│   └── TanStack Table
├── Timeline / Long Jobs
│   └── Frappe Gantt (opcional)
├── Logs / Sandbox Console
│   └── xterm.js
├── DSL / Policy / Config Editor
│   └── Monaco Editor
├── Metrics / Health
│   └── ECharts
└── Approval / Tool / Evidence Cards
    └── assistant-ui extension o tool-ui seleccionado
```

---

## 7. Contrato de integración de componentes — tres pasos

La integración de los componentes YAIWES sigue exactamente tres pasos operativos. A/B/C es una decisión de arquitectura dentro de la integración; **no agrega fases nuevas**.

### PASO 1 — MOVE físico

```text
ORIGEN REAL
→ MANIFEST / HASH
→ MOVE POR LOTES
→ DESTINO FINAL
→ SOURCE REMOVED/DEDUP
→ COMMIT
→ PUSH
→ READ-BACK DESDE main
```

Reglas: no cablear, no podar, no testear, no reescribir upstream. El éxito requiere evidencia en `main`, no solamente dentro de un runner.

### PASO 2 — WIRE + PRUNE 1×1, sin tests

```text
DESTINO FÍSICO
→ X-RAY
→ DECISIÓN A/B/C
→ RESPONSABILIDAD ÚNICA
→ ADAPTER/PORT
→ FICHA/CONTRACT
→ WIRING/REGISTRY
→ PODA MÍNIMA SEGURA
→ EVIDENCIA DE CABLEADO
```

Poda permitida: CI de upstream, tooling de desarrollo no requerido y duplicados demostrados. Prohibido podar runtime, licencia, NOTICE, schemas, configuración necesaria o código requerido.

### PASO 3 — TEST 1×1

```text
CONTRACT VALIDATION
→ IMPORT/BUILD
→ MOUNT
→ HEALTH
→ BEHAVIOR
→ FAIL-CLOSED
→ HEARTBEAT/EVIDENCE
→ PASS | GAP
```

Ante GAP: localizar, reparar dentro del mismo paso, repetir y continuar. No crear Paso 4.

---

## 8. Opciones A/B/C

### A — Subagente / hijo

Se usa cuando el componente mantiene objetivo, lifecycle, herramientas, memoria o decisiones propias. Vive aislado y YAIWES lo invoca por contrato. No se incrusta como código de control del microkernel.

### B — Workflow / DAG / pool

Se usa cuando el valor principal es scheduling, state-machine, DAG, cola, workers, durable workflow, secuencia de pasos o paralelismo. Vive detrás de puertos de ejecución/orquestación y nunca decide por sí mismo la política global.

### C — Capacidad modular

Se usa cuando solo se necesita una capacidad concreta: validación, policy, storage, memoria, routing, observabilidad, research utility, sandbox helper, etc. Se conserva el runtime útil y se monta mediante adapter/contract/registry.

La decisión exige:

`FUNCIÓN REAL → GAP QUE CUBRE → A/B/C → DESTINO → QUÉ CONSERVAR → QUÉ PODAR → PORT/ADAPTER → EVIDENCIA`

---

## 9. Trabajo en paralelo del Watchdog

El sistema podrá mantener cientos de Watchdogs pendientes, pero nunca traducirá `N tareas = N procesos`. Debe existir control de concurrencia:

- priority queues;
- worker pools persistentes;
- batching;
- sharding por proyecto/tenant/key;
- fan-out/fan-in;
- backpressure;
- queue-depth autoscaling;
- deduplicación;
- idempotency;
- leases;
- dead-letter queue;
- checkpoint/resume;
- aislamiento por sandbox/worktree;
- límites por agente/modelo/proveedor.

Routing base:

```text
SIMPLE → Celery/Taskiq
DURABLE LONG → Hatchet (DBOS/Restate como alternativas detrás del port)
MULTI-STEP → Dagu
SMALL LOOP → PocketFlow
FUNCTIONAL DAG/CASCADE → Hamilton/redun
RESEARCH → ResearchPort → DeerFlow | GPT-Researcher | MindSearch
ADAPTIVE → YAIWES + smolagents/planificador subordinado + PRELINE + policy
```

---

## 10. Recovery

```text
FAIL ≠ RESET

FAIL
→ LOCALIZE
→ FREEZE EVIDENCE
→ CHECKPOINT
→ RETRY SI ES SEGURO
→ ROLLBACK/FORK SI PROCEDE
→ REPAIR
→ RESUME DESDE ÚLTIMO ESTADO VÁLIDO
```

PostgreSQL conserva estado durable; Redis transporta eventos/heartbeats; pgvector recupera memoria semántica; RustFS/S3 conserva artefactos; el sandbox conserva/recupera workspace mediante snapshot cuando el runtime lo soporte.

---

## 11. Criterio de cierre

Un componente o capacidad no se marca `VERIFIED_CLOSED` hasta demostrar:

- presencia física correcta;
- provenance/hash cuando aplique;
- contract/ficha;
- adapter/wiring;
- registry/mount;
- test relevante;
- health/heartbeat cuando corresponda;
- evidencia de ejecución;
- read-back desde la rama canónica;
- ausencia de duplicación destructiva.

Una carpeta sola no es integración. Un log del runner sin push no es integración. Una declaración en README no es integración.

---

## 12. Enlaces de continuidad

- Arquitectura canónica histórica: `Readme arquitectura Yaiwes/README.md`
- Handoff 1–20: `Readme arquitectura Yaiwes/HANDOFF-INTEGRACION-1-20.md`
- Handoff core + Watchdog detallado: `📂 Readme Handoff core integracion y wachdog.md`
- Plan Watchdog + paralelo: `📂 Readme plan wachdog y trabajo en paralelo.md`
- Crazy Wall operativo: `📂 Bitácora stated JSON Craxy wall.json`
- STATE canónico: `Core kernel Yaiwes/Crack wall bitácora stated JSON/STATE.json`
- Plan machine-readable Watchdog: `Core kernel Yaiwes/Crack wall bitácora stated JSON/PLAN-WATCHDOG-PROGRAMMING-V2.json`
- Backend Watchdog: `Core kernel Yaiwes/Backend watchdog workflow adaptativo/`
- Recovery patch: `PARCHE-RECUPERACION-CORE-INTEGRACION-WATCHDOG.md`
