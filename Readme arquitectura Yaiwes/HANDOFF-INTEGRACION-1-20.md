# HANDOFF — Integración YAIWES componentes 1–20 + continuidad Watchdog

**Repositorio canónico:** `maxbry123-commits/agentes`  
**Estado:** `ACTIVE_LOOP`  
**Contrato:** exactamente 3 pasos. No abrir fases adicionales.  
**Actualización:** 2026-09-10.

## 1. Regla principal

`PASO 1 MOVE 1–20 → PASO 2 CABLEAR/PODAR 1×1 SIN TESTS → PASO 3 TESTS 1×1`

- Código upstream: conservar bytes/código originales durante el MOVE; no reescribirlos.
- Dentro de `agentes`: MOVE/deduplicación verificada, no una copia paralela sin justificación.
- Paso 1: sin cableado, sin poda, sin tests.
- Paso 2: X-Ray + decisión A/B/C + cableado + poda 1×1; prohibido ejecutar tests.
- Paso 3: tests 1×1 únicamente después de completar el Paso 2 correspondiente.
- Un GAP se repara dentro del mismo paso. No se inventa un Paso 4.
- La fuente de verdad es el estado físico de `main`, seguido por read-back/test/evidence; el chat y documentos no sustituyen la verificación física.

## 2. Estado físico actualizado

### Paso 1 — `VERIFIED_CLOSED`

El MOVE final fue ejecutado con el motor de movimientos por lotes y quedó publicado en `main`.

- Workflow final: `YAIWES Motor4 Final MOVE 20`.
- Archivo: `.github/workflows/yaiwes-motor4-move-20-final.yml`.
- Run: `34445710787` — `completed/success`.
- Job: `102771861495` — `completed/success`.
- `Execute MOVE 1-20`: `success`.
- `Publish physical MOVE to main`: `success`.
- `Read back all 20 from origin main`: `success`.
- Commit físico de MOVE observado en `main`: `a3cf705f58f95cce65d1c230cb00abcab39732b2` (`move(yaiwes): Motor4 batch MOVE components 1-20 to final destinations`).

Esto cierra **solamente el Paso 1**. No implica que los 20 componentes estén aún `VERIFIED_CLOSED` como integración completa; falta Paso 2 y Paso 3.

### Paso 2 — `PENDING / CURRENT_BOUNDARY`

Siguiente frontera operativa: X-Ray + clasificación A/B/C + adapter/Ficha/WIRING/registry + poda mínima segura, uno por uno y **sin tests**.

### Paso 3 — `PENDING`

Solo después del cableado/poda: test 1×1 con contract/import/build/mount/health/behavior/fail-closed/evidence/read-back.

## 3. Componentes y destinos finales

| # | Componente | Destino final |
|---:|---|---|
| 1 | APScheduler | `Agente Yaiwes principal/execution-orchestration/task-classifier-scheduler/` |
| 2 | AWS-Step-Functions-DS-SDK | `Agente Yaiwes principal/execution-orchestration/state-machine-executor/aws-step-functions-ds-sdk/` |
| 3 | Ajv | `Agente Yaiwes principal/definition-registry/schema-contracts/ajv/` |
| 4 | Apache-APISIX | `Agente Yaiwes principal/mesh-routing-collaboration/apisix-api-gateway/` |
| 5 | Apache-Airflow | `Agente Yaiwes principal/execution-orchestration/dag-executor/apache-airflow/` |
| 6 | Argo-Workflows | `Agente Yaiwes principal/execution-orchestration/dag-executor/argo-workflows/` |
| 7 | Azure-Durable-Functions | `Agente Yaiwes principal/execution-orchestration/state-machine-executor/azure-durable-functions/` |
| 8 | BAML | `Agente Yaiwes principal/definition-registry/domain-specific-contracts/baml/` |
| 9 | Burr | `Agente Yaiwes principal/execution-orchestration/state-machine-executor/burr/` |
| 10 | Caddy | `Agente Yaiwes principal/mesh-routing-collaboration/caddy-gateway/` |
| 11 | Camunda | `Agente Yaiwes principal/execution-orchestration/state-machine-executor/camunda/` |
| 12 | Cedar | `Agente Yaiwes principal/definition-registry/authorization-model/cedar/` |
| 13 | Celery | `Agente Yaiwes principal/execution-engine-pool/parallel-dispatch/celery/` |
| 14 | Cerberus | `Agente Yaiwes principal/definition-registry/schema-contracts/cerberus/` |
| 15 | Cerbos | `Agente Yaiwes principal/control-governance/policy-guardrails-permissions/cerbos/` |
| 16 | Chroma | `Agente Yaiwes principal/tools-models-memory-knowledge/memory-microservices/chroma/` |
| 17 | ClawHub | `Agente Yaiwes principal/kernel-principal/extension-kernel/capability-registry/clawhub/` |
| 18 | Cloudflare-Workers-SDK | `Agente Yaiwes principal/execution-engine-pool/adapter-layer/cloudflare-workers-sdk/` |
| 19 | Coconut | `Agente Yaiwes principal/kernel-principal/reasoning-kernel/decision-on-demand/coconut/` |
| 20 | CodeUltraFeedback | `Agente Yaiwes principal/code-programming-engine/standards-forensic/code-ultrafeedback/` |

## 4. Paso 2 detallado — X-Ray + A/B/C + wire/prune

El X-Ray no es un cuarto paso: vive dentro del Paso 2 y determina cómo se conecta cada componente.

Por cada componente registrar:

`SOURCE/DESTINATION → runtime real → entrypoint → inputs/outputs → dependencias → estado/persistencia → seguridad → scheduler/DAG/queue/loop → LLM vs determinista → duplicados → GAP YAIWES → A/B/C → KEEP/PRUNE → PORT/ADAPTER → FICHA → WIRING → REGISTRY → EVIDENCE`.

Si una propiedad no se puede demostrar: `GAP / NO_DETERMINABLE`.

### Opción A — Subagente/hijo

Aplicar si conserva objetivo, lifecycle, herramientas, contexto/memoria y decisiones autónomas. Integración:

`YAIWES → AgentPort/Contract → Policy/Budget → Sandbox/Runtime aislado → Subagente → Result normalizado → Evidence`.

No incrustar un agente autónomo completo como lógica del microkernel.

### Opción B — Workflow/DAG/pool

Aplicar si su valor es scheduler, DAG, state-machine, cola, workers, durable execution, multi-step, pipeline o loop. Integración:

`TaskClassifier → WorkflowPort/ExecutionPort → motor → state/events → ResultNormalizer → Evidence`.

El motor ejecuta; YAIWES mantiene policy y objetivo global.

### Opción C — Capacidad modular

Aplicar si aporta una capacidad concreta: schema, authorization, policy, storage, memory, routing, observability, research utility, sandbox helper o reasoning utility. Integración:

`Capability → Adapter → Ficha/Contract → Registry → UniversalPluginBus/Port → YAIWES → Evidence`.

## 5. Paso 3 detallado — test 1×1

Gate mínimo:

`DESTINATION → CONTRACT/FICHA VALID → ADAPTER IMPORT/BUILD → WIRING → REGISTRY/MOUNT → HEALTH → BEHAVIOR → FAILURE PATH/FAIL-CLOSED → HEARTBEAT/EVIDENCE → READ-BACK → PASS|GAP`.

Un PASS sin evidencia física no cierra el componente.

## 6. Continuidad Watchdog programable

El backend Watchdog ya tiene físicamente las familias principales bajo `Core kernel Yaiwes/Backend watchdog workflow adaptativo/`: APScheduler, Rocketry, Workalendar, Taskiq, Redis, Hatchet, DBOS Python, Restate, Dagu, PocketFlow, Apache Hamilton, redun, smolagents, DeerFlow, GPT-Researcher, MindSearch, PostgreSQL, pgvector, gVisor, Firecracker, iii-sandbox y RustFS. Celery está físicamente en `Agente Yaiwes principal/execution-engine-pool/parallel-dispatch/celery/` y debe consumirse por referencia/adapter, no duplicarse.

El GAP backend principal ya no es descargar otro orquestador grande. Son los contratos/ports: `WatchdogDefinition`, `WatchdogRun`, `WatchdogStep`, `Checkpoint`, `EventEnvelope`, `SchedulerPort`, `QueuePort`, `DurableExecutionPort`, `WorkflowPort`, `ResearchPort`, `PlanningPort`, `SandboxPort`, `StatePort`, `SemanticMemoryPort`, `ArtifactPort`, idempotency/leases/heartbeat/retry/timeout/recovery y health/evidence. RustFS cubre un proveedor S3-compatible; un binding específico de Backblaze B2 permanece `NOT_DEMONSTRATED` hasta materializar el adapter/configuración correspondiente.

Frontend: `assistant-ui` y `Dockview` están demostrados como `EXTRACTED/COMPLETE`; `xyflow` está inventariado como `ZIP_ONLY/COMPLETE` y requiere extracción/read-back antes de integrarlo. Los módulos no demostrados en el índice revisado son FullCalendar, TanStack Table, react-jsonschema-form, xterm.js, Monaco Editor, Apache ECharts, dnd-kit y, opcionalmente, Frappe Gantt.

## 7. Workflow objetivo del Watchdog

```text
CHAT/UI
→ WATCHDOG DEFINITION
→ SCHEMA/POLICY
→ PostgreSQL
→ APScheduler + Workalendar
→ DUE EVENT
→ RUN + IDEMPOTENCY KEY
→ PRIORITY QUEUE
→ TASK CLASSIFIER
→ SELECT ENGINE
→ LEASE
→ SANDBOX
→ LOAD STATE/MEMORY
→ PRELINE/POLICY
→ EXECUTE + HEARTBEAT
→ CHECKPOINT
→ VERIFY/EVIDENCE
→ COMPLETE | RETRY | ROLLBACK | REPLAN
→ NEXT RUN
```

Routing previsto:

- SIMPLE → Celery; Taskiq como alternativa detrás de `QueuePort`.
- DURABLE LONG → Hatchet; DBOS/Restate como alternativas detrás de `DurableExecutionPort`.
- MULTI-STEP → Dagu.
- SMALL LOOP → PocketFlow.
- DAG/CASCADE → Apache Hamilton/redun.
- RESEARCH → `ResearchPort` → DeerFlow | GPT-Researcher | MindSearch.
- ADAPTIVE → YAIWES + planning subordinado + PRELINE/policy.
- STATE → PostgreSQL; semantic memory → pgvector; events → Redis.
- SANDBOX → gVisor/Firecracker según perfil de riesgo.
- ARTIFACTS → RustFS/S3-compatible; B2 mediante adapter si se selecciona.

## 8. Trabajo en paralelo

`500 Watchdogs registrados ≠ 500 procesos simultáneos`.

Usar priority queues, pools persistentes, batching, sharding, fan-out/fan-in, backpressure, dedup, idempotency, leases, DLQ, queue-depth scaling, límites por agente/modelo/proveedor y aislamiento por sandbox/workspace.

## 9. Enlaces canónicos

- Repositorio: https://github.com/maxbry123-commits/agentes
- Arquitectura histórica: https://github.com/maxbry123-commits/agentes/blob/main/Readme%20arquitectura%20Yaiwes/README.md
- Arquitectura integración + Watchdog detallada: https://github.com/maxbry123-commits/agentes/blob/main/%F0%9F%93%82%20Readme%20arquitectura%20Yaiwes.md
- Este HANDOFF: https://github.com/maxbry123-commits/agentes/blob/main/Readme%20arquitectura%20Yaiwes/HANDOFF-INTEGRACION-1-20.md
- Handoff core + integración + Watchdog: https://github.com/maxbry123-commits/agentes/blob/main/%F0%9F%93%82%20Readme%20Handoff%20core%20integracion%20y%20wachdog.md
- Plan Watchdog/paralelo: https://github.com/maxbry123-commits/agentes/blob/main/%F0%9F%93%82%20Readme%20plan%20wachdog%20y%20trabajo%20en%20paralelo.md
- Crazy Wall detallado: https://github.com/maxbry123-commits/agentes/blob/main/%F0%9F%93%82%20Bit%C3%A1cora%20stated%20JSON%20Craxy%20wall.json
- STATE: https://github.com/maxbry123-commits/agentes/blob/main/Core%20kernel%20Yaiwes/Crack%20wall%20bit%C3%A1cora%20stated%20JSON/STATE.json
- Plan machine-readable Watchdog: https://github.com/maxbry123-commits/agentes/blob/main/Core%20kernel%20Yaiwes/Crack%20wall%20bit%C3%A1cora%20stated%20JSON/PLAN-WATCHDOG-PROGRAMMING-V2.json
- Backend Watchdog: https://github.com/maxbry123-commits/agentes/tree/main/Core%20kernel%20Yaiwes/Backend%20watchdog%20workflow%20adaptativo
- Run Motor4 MOVE 20: https://github.com/maxbry123-commits/agentes/actions/runs/34445710787
- Commit MOVE 20: https://github.com/maxbry123-commits/agentes/commit/a3cf705f58f95cce65d1c230cb00abcab39732b2
- Recovery patch: https://github.com/maxbry123-commits/agentes/blob/main/PARCHE-RECUPERACION-CORE-INTEGRACION-WATCHDOG.md

## 10. Cómo continuar en una sesión nueva

1. Leer `PARCHE-RECUPERACION-CORE-INTEGRACION-WATCHDOG.md`.
2. Leer este Handoff.
3. Leer `📂 Bitácora stated JSON Craxy wall.json` y `STATE.json`.
4. Verificar físicamente el boundary actual.
5. No repetir Paso 1: su run final y read-back están cerrados.
6. Continuar desde Paso 2 sin tests; después ejecutar Paso 3.
7. Construir/cablear el Watchdog sobre los componentes ya presentes, evitando descargar motores redundantes.
