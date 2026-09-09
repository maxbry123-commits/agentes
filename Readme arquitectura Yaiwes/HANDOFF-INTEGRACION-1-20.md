# HANDOFF — Integración YAIWES componentes 1–20

**Repositorio canónico:** `maxbry123-commits/agentes`  
**Estado:** `ACTIVE_LOOP`  
**Contrato:** exactamente 3 pasos. No abrir fases adicionales.

## Regla principal

`PASO 1 MOVE 1–20 → PASO 2 CABLEAR/PODAR 1×1 SIN TESTS → PASO 3 TESTS 1×1`

- Código upstream: mover/conservar bytes de código originales; no reescribirlos durante el MOVE.
- Dentro de `agentes`: MOVE, no COPY.
- Paso 1: sin cableado, sin poda, sin tests.
- Paso 2: cableado + poda 1×1; prohibido ejecutar tests.
- Paso 3: tests 1×1 únicamente cuando 1 y 2 estén completos para los 20.
- Si un componente falla dentro de un paso, resolver el GAP dentro del mismo paso y continuar; no abrir otra fase.
- Actualizar `Readme arquitectura Yaiwes/README.md` con el avance físico de cada paso.

## Componentes y destinos finales

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

## Paso 1 — MOVE

**Workflow:** `YAIWES STEP 1 - MOVE 1-20`  
**Archivo:** `.github/workflows/yaiwes-step1-move-1-20.yml`  
**Run activo optimizado:** `34299244917`  
**Job:** `102302447840`  
**Regla:** mover árboles originales a destino final y registrar en README arquitectura. Sin poda/cableado/tests.

## Paso 2 — Cableado y poda

**Workflow:** `YAIWES STEP 2 - WIRE PRUNE 1-20 NO TESTS`  
**Archivo:** `.github/workflows/yaiwes-step2-wire-prune-1-20.yml`  
Se dispara automáticamente cuando Paso 1 termina `success`.  
Cola estricta `1 → 20`; conserva runtime, añade/adopta adapter + Ficha v2 + WIRING y hace poda mínima segura.  
**Prohibido testear en Paso 2.**

## Paso 3 — Tests

**Workflow:** `YAIWES STEP 3 - TEST 1-20`  
**Archivo:** `.github/workflows/yaiwes-step3-test-1-20.yml`  
Se dispara automáticamente cuando Paso 2 termina `success`.  
Cola estricta `1 → 20`; prueba adapter/Ficha/WIRING, import real del adapter y montaje mediante `UniversalPluginBus`, health/evidence, y publica reporte en README arquitectura.

## Enlaces canónicos

- Repositorio: https://github.com/maxbry123-commits/agentes
- Arquitectura YAIWES: https://github.com/maxbry123-commits/agentes/blob/main/Readme%20arquitectura%20Yaiwes/README.md
- Este HANDOFF: https://github.com/maxbry123-commits/agentes/blob/main/Readme%20arquitectura%20Yaiwes/HANDOFF-INTEGRACION-1-20.md
- Crazy Wall / STATE: https://github.com/maxbry123-commits/agentes/blob/main/Core%20kernel%20Yaiwes/Crack%20wall%20bit%C3%A1cora%20stated%20JSON/STATE.json
- Método de integración: https://github.com/maxbry123-commits/agentes/blob/main/Core%20kernel%20Yaiwes/Readme%20de%20integraci%C3%B3n%20de%20componentes%20arquitectura%20Yaiwes/README.md
- Memoria Watchdog: https://github.com/maxbry123-commits/agentes/blob/main/Core%20kernel%20Yaiwes/readme-memoria.md
- Plan Watchdog programación: https://github.com/maxbry123-commits/agentes/blob/main/Core%20kernel%20Yaiwes/Crack%20wall%20bit%C3%A1cora%20stated%20JSON/PLAN-WATCHDOG-PROGRAMMING-V2.json
- Workflow Paso 1: https://github.com/maxbry123-commits/agentes/blob/main/.github/workflows/yaiwes-step1-move-1-20.yml
- Run Paso 1 activo: https://github.com/maxbry123-commits/agentes/actions/runs/34299244917
- Job Paso 1 activo: https://github.com/maxbry123-commits/agentes/actions/runs/34299244917/job/102302447840
- Workflow Paso 2: https://github.com/maxbry123-commits/agentes/blob/main/.github/workflows/yaiwes-step2-wire-prune-1-20.yml
- Workflow Paso 3: https://github.com/maxbry123-commits/agentes/blob/main/.github/workflows/yaiwes-step3-test-1-20.yml

## Cómo continuar la tarea

1. Leer este HANDOFF.
2. Leer `Readme arquitectura Yaiwes/README.md`.
3. Leer `STATE.json`.
4. Continuar en el paso físico actual sin reiniciar trabajo cerrado.
5. Si falla un componente, resolver dentro del mismo paso y seguir la cola.
6. No iniciar ninguna tarea externa hasta cerrar `Paso 1 → Paso 2 → Paso 3`.

## Handoff operativo

En cualquier chat/sesión nueva: leer primero este archivo, después README arquitectura y STATE. Continuar exactamente desde el paso y componente físico no completado; no reiniciar ni reinterpretar el plan.
