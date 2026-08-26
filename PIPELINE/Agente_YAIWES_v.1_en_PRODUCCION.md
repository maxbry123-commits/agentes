# Agente YAIWES v.1 en PRODUCCIÓN

**Repo:** maxbry123-commits/agentes · **rama:** main  
**Fecha de consolidación:** 2026-08-26  
**GitHub = truth** · FAIL-CLOSED · REUSE > PATCH > ADAPT > GENERATE

Este documento es la **foto de producción** del sistema: arquitectura actual, wordflow real, verificación cruzada con código fuente, gaps, Refactoria y cómo crecer.

---

## 0. Resumen ejecutivo

| Dimensión | Estado |
|-----------|--------|
| Estructura raíz PLAN_100 | Materializada (S1 PASS) |
| Despliegue 1 materialización | PASS (S2); remote apply NO |
| Mapa origen→destino | PASO3 + ORIGIN_MAP + COPY_MANIFEST (S3 PASS) |
| Organización código S4–S9 | PASS documental/materialización según checkpoints |
| Gaps técnicos S10 | **7 OPEN** (correcto FAIL-CLOSED) |
| Hot path programming | `extensions/wordflow/engine/code_path_runner.py` **INTACTO** |
| Kernel | `extensions/wordflow_kernel/` ~109 paths / ~90–95 files / ~150–180 KB |
| Nivel producción SaaS | Estructura + gobierno listos; motores reales y pipeline modular **pendientes** |

**Avance orientativo:** estructura/organización ~75–80%; capacidad operativa real (adapters, p01–p12, bodies) ~10–20% de esa capa → **total mixto ~55–65%** del objetivo SaaS avanzado.

---

## 1. Arquitectura actual (vista de producción)

```text
                    ┌─────────────────────────┐
                    │   Director / Chat A     │
                    │  PLAN + PASO3 + UOOS    │
                    └───────────┬─────────────┘
                                │
         ┌──────────────────────┼──────────────────────┐
         ▼                      ▼                      ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│ input-layer     │   │ definition-     │   │ control-        │
│ reception       │   │ registry        │   │ governance      │
│                 │   │ catalogs/schemas│   │ sheriff/forensic│
└────────┬────────┘   └────────┬────────┘   └────────┬────────┘
         │                     │                     │
         └─────────────────────┼─────────────────────┘
                               ▼
              ┌────────────────────────────────┐
              │ multi-workflow-engine          │
              │ runner-host · bindings         │
              └────────────────┬───────────────┘
                               ▼
              ┌────────────────────────────────┐
              │ execution-orchestration        │
              │ DAG · mission-planning         │
              │ goal-lock (LEGO única)         │
              └────────────────┬───────────────┘
                 ┌─────────────┼─────────────┐
                 ▼             ▼             ▼
┌────────────────────┐ ┌──────────────┐ ┌────────────────────────┐
│ code-programming-  │ │ execution-   │ │ agent-fleet /          │
│ engine             │ │ engine-pool  │ │ state / observability  │
│ C-19 hot path REF  │ │ adapter-layer│ │                        │
│ → wordflow engine  │ │ aux agents   │ │                        │
└─────────┬──────────┘ └──────┬───────┘ └────────────────────────┘
          │                   │
          │                   ▼
          │         intelligence_gateway (stub)
          │         Mock + RouterHTTP hoy
          │         → adapters reales = G6 OPEN
          ▼
┌──────────────────────────────────────────┐
│ LEGACY OPERATIVO (no apagar)             │
│ extensions/wordflow/engine/              │
│   code_path_runner.py  ← HOT PATH        │
│ extensions/wordflow_kernel/              │
│   gateway · engines stubs · stages       │
└──────────────────────────────────────────┘
```

### Principios congelados
1. **code-programming-engine** fuera del kernel (raíz propia).
2. **Monolito C-19** sigue siendo la fuente operativa hasta paridad de tests.
3. **LEGO:** goal_lock, cognitive_loop, evidence_packet — una sola autoridad.
4. **Enchufe:** intelligence_gateway ya es el punto; no crear otro.
5. **Crecimiento:** OSS → extraer capacidades faltantes → ficha v2 + bus → catalog → router.

---

## 2. Árbol agente-yaiwes (nodos de producción)

Fuente: `PLAN_100_ESTRUCTURA_DEFINITIVA.md`. Estados: REAL materializado parcialmente vía S4–S9; ESQ = PLACEHOLDER; REF = SOURCE a LEGACY.

| Nodo raíz | Rol | Fuente code real típica |
|-----------|-----|-------------------------|
| code-programming-engine | Motor de programación | wordflow/engine, standards, schemas |
| kernel-principal | ABI, capabilities, resources, bus | wordflow_kernel bootstrap/registry/resources |
| input-layer | Reception / entradas | wordflow/reception, kernel reception |
| definition-registry | Catalogs, contracts, schemas | component/connect catalogs, schemas/ |
| control-governance | Sheriff, forensic, gates, symbol index | standards/* |
| multi-workflow-engine | Instancias + runner-host | instance_store, main_loop split |
| execution-orchestration | DAG, planning, goal-lock | planner, context, bridges |
| execution-engine-pool | Adapters + aux agents | gateway, engines stubs, ports |
| deploy-publish | Accounts, push | accounts/, connectors |
| state-events-durability | Checkpoints, ledger | state/, checkpoint |
| observability | Trace, evidence | trace.py, evidence_* |
| extensions/* | REF a LEGACY | extensions/wordflow* |

Detalle de subnodos: ver PLAN_100 (árbol completo en repo).

---

## 3. Wordflow — mapa forense del código fuente

### 3.1 extensions/wordflow (LEGACY operativo)

| Área | Paths clave | Destino YAIWES | Estado prod |
|------|-------------|----------------|-------------|
| Catalogs | component_catalog.json, connect_catalog.json | definition-registry/declared-dependency-catalog | REAL + S2 append (code_programming_engine, pool, CONNs) |
| Engine C-19 | code_path_runner.py | code-path-execution (CABLEAR, no apagar) | **HOT PATH** |
| Engine modules | programming_pipeline, kwargs, input_quality_bar, skill_native_compiler | engine-modules | Copiados/organizados S5 |
| Smoke | code_path_smoke.py | module-tests | Organizado |
| main_loop | main_loop.py | runner-host + programming-engine-binding | SPLIT pendiente de wiring |
| Standards | forensic_*, verdict_*, executor_gates, symbol_index, copy_first, quality_dag, … | control-governance/* | Organizado S7 |
| Schemas | ~30–32 JSON | definition-registry/schema-contracts; REF schema-contracts-io | S8 |
| Motors | call/download/send/kernel_ext | external-motor-bridge | S4 |
| Policies | sentinel, sheriff, engine_attach | control-governance / abi-mount | S4 |
| State/store | blackboard, ledger, main_12.yaml | state-events / workflow-definition | S4 |
| Accounts/connectors | accounts/, connectors/ | deploy-publish | S4 |

### 3.2 extensions/wordflow_kernel

| Área | Paths | Destino | Estado |
|------|-------|---------|--------|
| Core | workflow.py, runtime.py, spawn.py | kernel-principal | Organizado S9 |
| Gateway | intelligence.py, router_http.py | adapter-layer | **Stub** Mock/RouterHTTP — G6 |
| Engines | openclaw_stub, hermes_stub, port.py | auxiliary-role-agents | **Stubs** — G7 |
| Fail-closed / LLM | fail_closed.py, llm_control.py | llm-control-deny | S9 |
| Forensic | forensic.py, forensic_api.py, gap_tasks, crosscheck, models | forensic-core | S9 + deps |
| Memory | memory.py, memory_slot/ | memory-microservices | S9 |
| Reception | convert.py, git_apply.py | input-layer / push-injection | S9 |
| Resources | registry, loaders, factory | resource-broker-gate | S9 |
| Stages/bridge | stages/*, bridge/* | kernel / orchestration | S9 |
| Tests | tests/test_*.py (~25) | viajan con módulos | REAL |
| ui_gateway | * | EXCLUIDO DOC-UI00 | No copiado |

### 3.3 LEGO (no duplicar)

| Módulo | Vive en |
|--------|--------|
| goal_lock.py | execution-orchestration/goal-lock |
| cognitive_loop.py | execution-orchestration/mission-planning |
| evidence_packet.py | observability/evidence-packet |

El hot path **importa** estos; no se copian al CPE como segunda verdad.

### 3.4 Despliegue

| Artefacto | Rol |
|-----------|-----|
| despliegue/programming_instance.py, instance_pool.py, capability_registration.py, classifier_hook.py, usage_metering.py | Opción A materializada |
| manifests/deployment_01.yaml | pending_after_push / PENDING |
| auditoria/verification.yaml | S2 materialization PASS; remote NOT_CLAIMED |
| INSTRUCCIONES_GROK_OPCION_A.md | Contrato S2 |

---

## 4. Verificación cruzada arquitectura ↔ código (X-Ray)

| Claim arquitectura | Evidencia en main | Veredicto |
|--------------------|-------------------|-----------|
| Árbol PLAN_100 bajo agente-yaiwes | S1 + tree expandido | PASS estructura |
| Despliegue 1 catalogs | component_catalog + connect_catalog entries | PASS materialización |
| ORIGIN_MAP = PASO3 | Archivos en repo | PASS |
| COPY_MANIFEST exhaustivo | Resumen parcial vs ORIGIN_MAP | PASS parcial |
| code_path_runner hot path | Presente en extensions/wordflow/engine/ | PASS intacto |
| intelligence_gateway adapters reales | Solo Mock/RouterHTTP | **GAP G6** |
| openclaw/hermes reales | *_stub.py + EnginePort | **GAP G7** |
| p01–p12 en main | No hay archivos p01_*…p12_* (solo mención PASO3) | **GAP G5** |
| SYMBOL_INDEX_PROGRAMMING.md | symbol_index.py sí; export MD no | **GAP G1** |
| Schemas por stage | schemas globales sí; por stage no | **GAP G2** |
| test→assert index | tests sí; índice no | **GAP G3** |
| CI log en observability | workflows sí; artifact en trace-history no | **GAP G4** |
| Remote deploy aplicado | validation PENDING | NO CLAIMED |

---

## 5. Gaps G1–G7 (producción)

| ID | Requiere code | Cerrable ya | Función de negocio |
|----|---------------|-------------|--------------------|
| G1 | Script export | Sí | Inventario símbolos reproducible |
| G2 | Schemas desde runner | Parcial | Contratos I/O por stage |
| G3 | Script índice tests | Sí | Trazabilidad test↔claim |
| G4 | Operación CI | Sí (run) | Evidencia de corrida |
| G5 | Fuente modular | No sin source | Pipeline programable por stages |
| G6 | OSS/SDK + adapter | No sin source | Motores reales en el pool |
| G7 | OSS acquire | No sin source | Agentes Nivel 3 reales |

**Regla:** OPEN no se cierra por declaración. Refactoria obligatoria al implementar.

---

## 6. Sistema Refactoria (producción)

```text
1) Copia exacta → despliegue/refactoria/<ID>/source/ + Refactoria/<ID>/source/
2) Nueva versión → Refactoria/<ID>/new/  (LOOP vs source)
3) Verificación cruzada ×3 (diff APIs, tests, checklist)
4) Integrar a path canónico PASO3 solo si 3× PASS
5) No borrar source/ en el mismo task; original LEGACY hasta orden Director
```

Anotado también en `PIPELINE/PLAN_YAIWES_AGENTE_WORDFLOW.md`.

---

## 7. Flujo de ejecución actual (runtime real)

```text
Request / mission
  → reception / input-layer
  → catalogs + policy gates (control-governance)
  → multi-workflow / orchestration (goal_lock, planning)
  → code path: code_path_runner (C-19)  [ÚNICO hot path hoy]
  → LLM/tools: IntelligenceGateway (Mock o RouterHTTP)
  → engines: OpenClaw/Hermes STUB via EnginePort (si policy)
  → evidence / forensic / sheriff
  → state checkpoint / ledger
```

Lo que **no** ocurre aún en producción real: dispatch multi-engine con adapters Claude/Codex/OpenHands; orquestación p01→p12 sin monolito; bodies OpenClaw/Hermes no stub.

---

## 8. Salidas S1–S12 (ledger)

| ID | Nombre | Status |
|----|--------|--------|
| S1 | Raíz PLAN_100 | PASS |
| S2 | Despliegue 1 | PASS materialización |
| S3 | ORIGIN_MAP + COPY_MANIFEST | PASS |
| S4 | wordflow top-level | PASS |
| S5 | engine C-19 org | PASS |
| S6 | engine resto | PASS |
| S7 | standards | PASS |
| S8 | schemas | PASS |
| S9 | wordflow_kernel | PASS |
| S10 | Gaps | PASS documental; 7 OPEN |
| S11 | LEGACY | PASS |
| S12 | Cierre proceso | PASS proceso |

Checkpoints: `PIPELINE/checkpoints/SALIDA_S*_2026-08-26.md`

---

## 9. Fase 2 — crecimiento por capacidades OSS

```text
Source open source de otro agente
  → ACQUIRE
  → ANALYZE (qué capacidad falta aquí)
  → REUSE / PATCH / ADAPT (no clonar agente entero)
  → Ficha v2 + Enchufe universal (bus)
  → Catalog + capability matching
  → Router elige motor/workflow
  → Más workflows/loops = más definiciones en registry, mismo runtime
```

Chat A: ubica destino PASO3. Chat B: implementa ≤2000 LOC con Refactoria. Director: aprueba y sube.

---

## 10. Enchufe universal + ficha v2 (próxima capa)

| Componente | Uso en producción |
|------------|-------------------|
| ficha_contract_v2 (36 invariantes) | Contrato de todo módulo enchufable |
| UniversalPluginBus | enchufar / desenchufar / upgrade + CostGovernor + evidence |
| Destino | execution-engine-pool/adapter-layer + definition-registry |
| Compatibilidad | v1.5 normaliza a v2.0 con defaults |

Materialización: COPY de adjuntos a paths canónicos vía Refactoria cuando el Director abra el lote.

---

## 11. Checklist producción (honestidad)

- [x] Estructura y mapa en GitHub
- [x] Despliegue 1 materializado (no remoto)
- [x] Hot path preservado
- [x] Gaps registrados sin fake PASS
- [x] Refactoria documentada
- [ ] G1–G3 cerrados con artifacts
- [ ] G4 log CI real
- [ ] G5 pipeline modular E2E
- [ ] G6/G7 motores y bodies reales
- [ ] Remote deploy con readback

---

## 12. Referencias canónicas

| Doc | Path |
|-----|------|
| Plan ejecutable | PIPELINE/PLAN_YAIWES_AGENTE_WORDFLOW.md |
| Estructura | agente-yaiwes/PLAN_100_ESTRUCTURA_DEFINITIVA.md |
| Mapa Director | PIPELINE/PASO3_ORGANIZACION_CODIGO_REAL_YAIWES.md |
| ORIGIN_MAP | agente-yaiwes/ORIGIN_MAP.md |
| COPY_MANIFEST | agente-yaiwes/COPY_MANIFEST.json |
| Este documento | PIPELINE/Agente_YAIWES_v.1_en_PRODUCCION.md |

---

**FIN — Agente YAIWES v.1 en PRODUCCIÓN**  
Arquitectura = árbol + LEGACY operativo + gobierno.  
Producción SaaS completa = cerrar G1–G7 con evidencia y Refactoria, sin apagar el monolito hasta paridad.
