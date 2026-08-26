# README PLAN YAIWES v1 — PLAN EJECUTABLE COMPLETO

**Repo:** `maxbry123-commits/agentes` · **rama:** `main`  
**Agente:** Yaiwes v1  
**GitHub = única verdad.** 1 tarea = 1 salida. PASS solo con evidencia. FAIL-CLOSED.

Este documento es **auto-contenido**. Cualquier agente (GPT / Grok / otro) debe ejecutarlo **solo con archivos de este repo**. No usar memoria de chat.

---

## 1. FUENTES CANÓNICAS (todas en el repo — leer antes de actuar)

| # | Archivo | Para qué |
|---|---------|----------|
| 1 | `agente-yaiwes/PLAN_100_ESTRUCTURA_DEFINITIVA.md` | Árbol raíz objetivo |
| 2 | `PIPELINE/PASO3_ORGANIZACION_CODIGO_REAL_YAIWES.md` | **Mapa completo origen→destino del Director** |
| 3 | `agente-yaiwes/ORIGIN_MAP.md` | Contrato filas (generado S3) |
| 4 | `agente-yaiwes/COPY_MANIFEST.json` | Manifest machine-readable (generado S3) |
| 5 | `despliegue/INSTRUCCIONES_GROK_OPCION_A.md` | Despliegue 1 |
| 6 | `PIPELINE/PLAN_YAIWES_AGENTE_WORDFLOW.md` | **Este plan** |

**Si falta la fuente 2 → FAIL-CLOSED. No inventar filas del mapa.**

---

## 2. REGLAS GLOBALES (sheriff)

```text
PROHIBIDO:
- Inventar código, filas de mapa, o destinos no listados en PASO3.
- Reescribir code_path_runner.py en main sin paridad de tests.
- Duplicar goal_lock / cognitive_loop / evidence_packet (regla lego).
- Marcar PASS sin checkpoint NUEVO + evidencia en GitHub.
- Saltar salidas o reordenar sin orden Director.

OBLIGATORIO:
- Leer PASO3 + ORIGIN_MAP + COPY_MANIFEST antes de S4+.
- Por cada salida: crear PIPELINE/checkpoints/SALIDA_SN_YYYY-MM-DD.md
- Acción física = según fila: MOVER_INTACTO | REF | LLENAR | CABLEAR | SPLIT
- Al MOVER: preferir COPY de blob + SOURCE en origen LEGACY; no borrar hot path operativo.
- Monolito main sigue operativo hasta S11/S12 con evidencia de tests.
```

### Regla lego

| Módulo | Vive UNA vez | code-programming-engine |
|--------|--------------|-------------------------|
| goal_lock.py | execution-orchestration/goal-lock | solo import/REF |
| cognitive_loop.py | execution-orchestration/mission-planning | solo import/REF |
| evidence_packet.py | observability/evidence-packet | solo import/REF |

### Checkpoint template (obligatorio cada salida)

```markdown
# CHECKPOINT SALIDA SN — YYYY-MM-DD
**Status:** PASS | FAIL
## Evidence
- paths tocados / commits
## Cross-check
- against: PASO3 / ORIGIN_MAP filas X–Y
## Sheriff
- NO_INVENTAR: PASS/FAIL
- NO_FAKE_PASS: PASS/FAIL
## Next
S(N+1)
```

---

## 3. TOTAL DE SALIDAS = 12

| Orden | ID | Nombre | Estado actual |
|-------|-----|--------|---------------|
| 1 | S1 | Estructura raíz PLAN_100 | **PASS** |
| 2 | S2 | DESPLIEGUE 1 | **PASS parcial** (base; runtime apply opcional) |
| 3 | S3 | ORIGIN_MAP + COPY_MANIFEST | **PASS** |
| 4 | S4 | Organizar wordflow top-level | **PENDIENTE** |
| 5 | S5 | Organizar engine C-19 | **PENDIENTE** |
| 6 | S6 | Organizar engine resto | **PENDIENTE** |
| 7 | S7 | Organizar standards/ | **PENDIENTE** |
| 8 | S8 | Organizar schemas/ | **PENDIENTE** |
| 9 | S9 | Organizar wordflow_kernel/ | **PENDIENTE** |
| 10 | S10 | Gaps: adapters, stubs, p01–p12 | **PENDIENTE** |
| 11 | S11 | Enganche LEGACY | **PENDIENTE** |
| 12 | S12 | Cierre 100% | **PENDIENTE** |

**Siguiente salida a ejecutar: S4**

Checkpoints hechos:
- `PIPELINE/checkpoints/SALIDA_S1_2026-08-26.md`
- `PIPELINE/checkpoints/SALIDA_S2_2026-08-26.md`
- `PIPELINE/checkpoints/SALIDA_S3_2026-08-26.md`

---

## 4. INSTRUCCIONES POR SALIDA (ejecutables)

### S1 — Estructura raíz [HECHA]
- Leer `PLAN_100_ESTRUCTURA_DEFINITIVA.md`
- Crear bajo `agente-yaiwes/` todas las carpetas del árbol con PLACEHOLDER.md o SOURCE.md
- No inventar .py de implementación
- Evidence: tree `agente-yaiwes/` expandido (~278 paths)

### S2 — DESPLIEGUE 1 [HECHA base]
- Leer `despliegue/INSTRUCCIONES_GROK_OPCION_A.md`
- Artefactos: instance_pool.py, capability_registration.py, classifier_hook.py, usage_metering.py, deployment_01.yaml
- Actualizar `despliegue/auditoria/verification.yaml`
- **NO** reemplazar code_path_runner
- Pendiente opcional Director: ejecutar append idempotente de catalogs en runtime

### S3 — Contrato mapa [HECHA]
- Fuente: `PIPELINE/PASO3_ORGANIZACION_CODIGO_REAL_YAIWES.md`
- Entregables: `agente-yaiwes/ORIGIN_MAP.md` + `agente-yaiwes/COPY_MANIFEST.json`
- Si la fuente no está en repo → FAIL-CLOSED (no inventar)

### S4 — Organizar top-level wordflow [PENDIENTE]

**Precondición:** S3 PASS + leer ORIGIN_MAP sección top-level.

Para **cada** fila top-level de PASO3 / ORIGIN_MAP:

1. Localizar origen bajo `extensions/wordflow/`
2. Destino bajo `agente-yaiwes/<nodo>/`
3. Acción **MOVER_INTACTO** = copiar contenido (mismo SHA si posible) al destino; dejar SOURCE.md o marker LEGACY en origen; **no borrar** origen operativo
4. Documentar en checkpoint: lista origen→destino→commit

Filas (resumen — detalle completo en PASO3):

| Origen | Destino |
|--------|--------|
| component_catalog.json + connect_catalog.json | definition-registry/declared-dependency-catalog |
| ficha.v2.json / manifest.yaml | kernel-principal/extension-kernel/capability-registry |
| accounts/ | deploy-publish/multi-account-registry |
| codegen/dag.py | execution-orchestration/dag-executor |
| connectors/ | deploy-publish/push-injection |
| context/builder.py | execution-orchestration/dependency-injection-context |
| contracts/ | definition-registry/domain-specific-contracts |
| docs_templates/ | PIPELINE/ |
| motors/ | code-programming-engine/external-motor-bridge |
| motors/kernel_ext | puente CPE ↔ kernel |
| planner/ | execution-orchestration/mission-planning |
| policies/engine_attach | extension-kernel/abi-mount |
| policies/sentinel+sheriff | control-governance/sentinel + sheriff-bridge |
| reception/ | input-layer/reception |
| state/ | state-events-durability/run-state-store |
| store/main_12.yaml | definition-registry/workflow-definition |
| store/goals, council | mission-planning / council |

**PASS si:** cada fila tiene artefacto en destino + evidencia en checkpoint.  
**FAIL si:** se inventa destino o se apaga origen sin SOURCE.

### S5 — engine C-19 [PENDIENTE]

Leer PASO3 sección C-19.

| Origen | Destino | Acción |
|--------|---------|--------|
| engine/code_path_runner.py | code-programming-engine/code-path-execution | CABLEAR (no apagar main) |
| engine/programming_pipeline.py | engine-modules | MOVER_INTACTO |
| engine/programming_kwargs.py | engine-modules | MOVER_INTACTO |
| engine/input_quality_bar.py | engine-modules | MOVER_INTACTO |
| engine/skill_native_compiler.py | engine-modules | MOVER_INTACTO (gap stub) |
| engine/code_path_smoke.py | module-tests | MOVER_INTACTO |
| engine/main_loop.py | runner-host + programming-engine-binding | SPLIT |

**NO copiar** goal_lock / cognitive_loop / evidence_packet a CPE.

### S6 — engine resto [PENDIENTE]

Leer PASO3 sección “engine resto”. Agrupar por prefijo → destino. Misma regla MOVER_INTACTO + no apagar origen. Incluir: resource-governance, control-governance, agent-fleet, deploy-publish, adapter-layer (ports/), FAKE engine marcado.

### S7 — standards/ [PENDIENTE]

Todo `extensions/wordflow/standards/*` → nodos `agente-yaiwes/control-governance/*` según tabla PASO3 (pre-post-gates, verdict-authority, forensic-core, closure-engine, quality-dag, sheriff-bridge, symbol-index-wiring-graph, …).

### S8 — schemas/ [PENDIENTE]

- 32 schemas → `definition-registry/schema-contracts`
- code_output + goal_lock → además REF en `code-programming-engine/schema-contracts-io` (no duplicar body)
- No inventar schemas stage; solo documentar gap → S10

### S9 — wordflow_kernel/ [PENDIENTE]

Leer PASO3 sección wordflow_kernel (mapa completo).

**Crítico:**
- gateway/intelligence.py + router_http.py → execution-engine-pool/adapter-layer
- openclaw_stub + hermes_stub + port → auxiliary-role-agents
- ui_gateway → EXCLUIDO (DOC-UI00)

Kernel size ref: ~109 paths / ~90–95 archivos / ~150–180 KB.

### S10 — Gaps [PENDIENTE]

Solo rellenar cuando haya diseño/evidencia real. Destinos ya fijados:

| Gap | Destino |
|-----|--------|
| Adapters reales (Claude Code, Codex, OpenHands, OpenCode, Aider, Cline) | adapter-layer |
| Body openclaw/hermes | auxiliary-role-agents |
| p01→p12 E2E wire | code-path-execution |
| Schemas stage C-19 | schema-contracts-io |
| SYMBOL_INDEX_PROGRAMMING.md | symbol-index-wiring-graph |
| test→asserts index | module-tests |
| Log CI real | trace-history |

Si no hay implementación real → documentar GAP en checkpoint, **no fake PASS**.

### S11 — LEGACY [PENDIENTE]

- Marker LEGACY en extensions/wordflow y wordflow_kernel
- Confirmar monolito code_path_runner sigue operativo
- Cutover solo si tests de paridad PASS

### S12 — Cierre [PENDIENTE]

Checklist:
- [ ] Árbol agente-yaiwes = PLAN_100
- [ ] Todas filas PASO3 ejecutadas o GAP explícito
- [ ] Lego respetada
- [ ] Monolito OK o cutover con evidencia
- [ ] Despliegue 1 auditado
- [ ] 12 checkpoints en PIPELINE/checkpoints/

---

## 5. DSL DAG (cada salida)

```text
INPUT:  precondiciones (salida anterior PASS) + fuentes canónicas
SHERIFF: reglas sección 2
VALIDADOR: evidencia en GitHub (paths, commits)
VERIFICACIÓN: tree + ORIGIN_MAP filas
VERIFICACIÓN CRUZADA: PASO3 vs lo escrito en destino
GUARDIÁN: FAIL-CLOSED si falta fuente o se inventa
OUTPUT: checkpoint NUEVO + cambios en main
```

---

## 6. CÓMO DEBE TRABAJAR EL SIGUIENTE AGENTE

1. Clonar / usar API sobre `maxbry123-commits/agentes` main
2. Leer este plan completo
3. Leer `PIPELINE/PASO3_ORGANIZACION_CODIGO_REAL_YAIWES.md`
4. Leer `agente-yaiwes/ORIGIN_MAP.md` + `COPY_MANIFEST.json`
5. Ejecutar **solo la siguiente salida pendiente** (hoy **S4**)
6. Crear checkpoint
7. No tocar el plan para “inventar” salidas
8. Si falta un archivo fuente listado en §1 → FAIL-CLOSED y reportar path faltante

---

## 7. ESTADO RESUMEN

| Pieza | Path | Estado |
|-------|------|--------|
| Plan ejecutable | PIPELINE/PLAN_YAIWES_AGENTE_WORDFLOW.md | **ACTUALIZADO** |
| Paso 3 Director | PIPELINE/PASO3_ORGANIZACION_CODIGO_REAL_YAIWES.md | **EN REPO** |
| ORIGIN_MAP | agente-yaiwes/ORIGIN_MAP.md | **PASS S3** |
| COPY_MANIFEST | agente-yaiwes/COPY_MANIFEST.json | **PASS S3** |
| Estructura raíz | agente-yaiwes/ | **PASS S1** |
| Despliegue 1 base | despliegue/ | **PASS parcial S2** |
| S4–S12 | — | **PENDIENTE** |

**TOTAL SALIDAS = 12**  
**SIGUIENTE = S4**
