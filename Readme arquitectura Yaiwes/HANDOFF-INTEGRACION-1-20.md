# HANDOFF — TAREA 2 · INTEGRACIÓN YAIWES · CONTRATO CANÓNICO DE 3 PASOS

**Repositorio:** `maxbry123-commits/agentes`  
**Rama:** `main`  
**Estado:** `ACTIVE_LOOP`  
**Regla:** exactamente 3 pasos. No crear Paso 4 ni fases paralelas.  
**Actualización:** 2026-09-10

## 1. Objetivo

Integrar los componentes de YAIWES con un proceso corto, verificable y retomable por cualquier agente/modelo. Se elimina sobreingeniería no necesaria: cada componente debe recorrer únicamente **Analizar → Mover/Conectar → Test**.

## 2. Contrato DSL / DAG / Schema

```text
CONTRACT yaiwes.integration.v3
INPUT  = componente encontrado o pendiente
ROOT   = Core kernel Yaiwes/ | Agente Yaiwes principal/
TARGET = destino canónico dentro de Agente Yaiwes principal/

STEP_1 ANALYZE_CLASSIFY
  X_RAY(runtime, entrypoint, IO, dependencies, state, security, capability)
  CLASSIFY(A|B|C)
  OUTPUT = IntegrationDecision

STEP_2 MOVE_WIRE_PRUNE_CONNECT
  MOVE(source -> canonical_target, Motor4, hash/readback)
  WIRE(real_adapter + ficha_contract_v2 + WIRING + registry/port)
  PRUNE(minimal_safe_only)
  CONNECT(real capability)
  OUTPUT = WiredComponent
  TESTS = FORBIDDEN

STEP_3 TEST_REAL_1X1
  TEST(contract, import/build, real_behavior, mount, health, failure_path, evidence, readback)
  OUTPUT = PASS | GAP
  PASS requires physical evidence
```

DAG canónico:

```text
[INPUT / Core kernel Yaiwes] → [1 ANALYZE + A/B/C] → [2 MOVE + WIRE + PRUNE + CONNECT] → [3 TEST REAL] → [PASS]
                                                               ↑                         │
                                                               └──── GAP REPAIR ─────────┘
```

Un GAP vuelve al paso donde nació. No crea una fase nueva.

## 3. Opciones A / B / C

### A — SUBAGENT / CHILD
Usar solamente si el componente mantiene goal/lifecycle/tools/context o decisiones autónomas.

`YAIWES → AgentPort → policy/budget → sandbox/runtime → subagente → result → evidence`

### B — WORKFLOW / DAG / POOL
Usar cuando el valor real es scheduler, DAG, state-machine, queue, workers, durable execution, multi-step, pipeline o loop.

`TaskClassifier → WorkflowPort/ExecutionPort → motor → state/events → result → evidence`

### C — MODULAR CAPABILITY
Usar para schema, policy, storage, memory, routing, observability, research utility, sandbox helper, reasoning utility u otra capacidad concreta.

`Capability → Adapter → Ficha/Contract → Registry/Port → YAIWES → evidence`

La clasificación debe salir del X-Ray del componente; queda prohibido asignarla solo por una tabla hardcodeada.

## 4. Regla nueva de intake desde Core kernel Yaiwes

**Todo componente que llegue o aparezca en `Core kernel Yaiwes/` entra automáticamente en TAREA 2.**

Proceso:

```text
DISCOVER Core kernel Yaiwes/**
→ identificar componente real
→ comprobar si ya tiene destino canónico
→ si no está integrado: STEP_1
→ STEP_2 usando motor de mover archivos
→ STEP_3
→ actualizar evidencia/estado
```

No se deja un componente operativo duplicado entre `Core kernel Yaiwes/` y `Agente Yaiwes principal/`. Se permite conservar evidencia, manifests o snapshots cuando sean necesarios, pero el runtime owner debe tener un destino canónico.

## 5. Estado físico actual

### Paso 1 MOVE histórico de la tanda 1–20

`VERIFIED_CLOSED` por:

- Workflow `YAIWES Motor4 Final MOVE 20`.
- Run `34445710787` = `completed/success`.
- Job `102771861495` = `completed/success`.
- Motor4 blob SHA `9a21facfe11327cf60a2afca8f415ad52f0ecbe5`.
- Commit MOVE `a3cf705f58f95cce65d1c230cb00abcab39732b2`.
- `Read back all 20 from origin main` = success.

Esto demuestra el MOVE de esa tanda. No convierte automáticamente los 20 en integración funcional cerrada.

### Primeros cinco

APScheduler, AWS-Step-Functions-DS-SDK, Ajv, Apache-APISIX y Apache-Airflow conservan adapters/WIRING/fichas reales y evidencia histórica de montaje UniversalPluginBus. En el contrato nuevo se **preservan** y en Paso 3 se revalida comportamiento real; no se sustituyen por wrappers genéricos.

### Componentes 6–20

Argo-Workflows, Azure-Durable-Functions, BAML, Burr, Caddy, Camunda, Cedar, Celery, Cerberus, Cerbos, Chroma, ClawHub, Cloudflare-Workers-SDK, Coconut y CodeUltraFeedback requieren completar/revalidar Paso 1 funcional y Paso 2 real antes de Paso 3.

## 6. Destinos canónicos de la tanda 1–20

| # | Componente | Destino |
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

## 7. Corrección obligatoria de los workflows antes de continuar

Los archivos actuales `.github/workflows/yaiwes-step2-wire-prune-1-20.yml` y `.github/workflows/yaiwes-step3-test-1-20.yml` **no son gate canónico todavía**.

Motivos:

- Paso 2 usa clasificación A/B/C hardcodeada en lugar de X-Ray real.
- Para componentes no cableados crea un `source_probe()` genérico que solo prueba presencia de carpeta.
- La ficha genérica no demuestra IO/capacidad real.
- La poda por nombre `.github/.circleci/.devcontainer` no está precedida por X-Ray 1×1.
- Paso 3 puede dar PASS al wrapper/PluginBus sin probar comportamiento upstream real.
- El trigger de Paso 2 escucha el workflow antiguo `YAIWES STEP 1 - MOVE 1-20`, no el Motor4 final que cerró la tanda.

**Regla:** corregir esos workflows dentro de Paso 2/3; no añadir fases.

## 8. Test mínimo real de Paso 3

Por componente:

```text
contract valid
→ adapter imports/builds
→ adapter llama capacidad real o boundary real
→ caso positivo
→ caso inválido/failure path
→ registry/mount
→ health/heartbeat si aplica
→ evidence
→ readback desde main/runtime
→ PASS | GAP
```

`source_probe()` por sí solo nunca es prueba funcional.

## 9. Nota de relevo para Grok / GPT-5.6 Sol / Astra

```text
HANDOFF_LOCK = YAIWES-INTEGRATION-3-STEPS
DO_NOT_RESTART = true
DO_NOT_ADD_PHASES = true
CURRENT_GOAL = completar integración funcional con 3 pasos

1. Leer este archivo literal.
2. Verificar main antes de aceptar estados históricos.
3. Incorporar cualquier componente nuevo encontrado en Core kernel Yaiwes/.
4. Ejecutar STEP_1 ANALYZE_CLASSIFY con evidencia; A/B/C no hardcodeado.
5. STEP_2 usa Motor4 para MOVE cuando haga falta y después adapter/ficha/wiring/registry reales; SIN TESTS.
6. STEP_3 prueba comportamiento real 1×1; no aceptar source_probe como PASS.
7. Reparar GAP dentro del paso actual.
8. No reemplazar los adapters reales de los primeros cinco por wrappers genéricos.
9. Actualizar STATE/evidence solo después de read-back físico.
```

## 10. Tareas pendientes — lista corta

1. Corregir Paso 2 para hacer X-Ray real, intake de `Core kernel Yaiwes/`, MOVE con Motor4 y wiring funcional específico.
2. Completar adapters/ports/fichas/WIRING reales para los pendientes sin destruir los cinco ya integrados.
3. Corregir Paso 3 para behavior/failure/evidence real y ejecutar 1×1 hasta 20/20 + cualquier nuevo componente incorporado.

## 11. Enlaces

- Este plan TAREA 2: https://github.com/maxbry123-commits/agentes/blob/main/Readme%20arquitectura%20Yaiwes/HANDOFF-INTEGRACION-1-20.md
- Motor4: https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82motores%20de%20descarga%20extracci%C3%B3n%20copiado%20movimiento%20archivos%20agentes/%E2%9E%A1%EF%B8%8F%F0%9F%93%82motor%20de%20moves%20archivos/motor_4_move_batches.py
- Run MOVE 20: https://github.com/maxbry123-commits/agentes/actions/runs/34445710787
- Plan Watchdog TAREA 3: https://github.com/maxbry123-commits/agentes/blob/main/%F0%9F%93%82%20Readme%20plan%20wachdog%20y%20trabajo%20en%20paralelo.md
