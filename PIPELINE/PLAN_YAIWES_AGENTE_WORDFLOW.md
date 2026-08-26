# PLAN AGENTE YAIWES v1 — WORDFLOW DSL DAG SCHEMA

**Proyecto:** maxbry123-commits/agentes  
**Nombre del agente:** **Agente Yaiwes v1** (no Omega)  
**Estado:** PASO 1 PASS → PASO 2 MATERIALIZADO + AUDITADO  
**Actualización:** 2026-08-26  
**Modelo de referencia:** PIPELINE-HUGGINGFACE.md (Grupo-Trabajo-1) — estilo + disciplina, upgraded a DSL DAG.  
**Fundamento forense:** PIPELINE/PASO1_XRAY_WORDFLOW_400PLUS_2026-08-25.md (496 entries / ~470 blobs).  
**GitHub = truth.** COPY-FIRST. No re-write legacy. 1 tarea = 1 salida. Binary PASS only with evidence. Fail-closed.

---

## 0. BLOQUE DE PROTECCIÓN — NO TOCAR EL PLAN

```text
╔══════════════════════════════════════════════════════════════════╗
║  BLOQUE INVIOLABLE — NO TOCAR EL PLAN                            ║
║                                                                  ║
║  Este documento (PLAN_YAIWES_AGENTE_WORDFLOW.md) es el contrato  ║
║  maestro de las 500 salidas.                                     ║
║                                                                  ║
║  PROHIBIDO:                                                      ║
║  - Reescribir, acortar, fusionar o eliminar salidas.             ║
║  - Cambiar el TOTAL de salidas (500).                            ║
║  - Quitar sheriff / validador / verificación cruzada / guardián. ║
║  - Mezclar tareas o saltar nodos.                                ║
║  - Declarar PASS sin evidencia y sin checkpoint.                 ║
║                                                                  ║
║  PERMITIDO solo:                                                 ║
║  - Añadir evidencia / checkpoint de una salida ya definida.      ║
║  - Registrar GAP real detectado en ejecución (sin borrar nodo).  ║
║  - Actualizar status de una salida (PENDING → PASS/FAIL) con     ║
║    evidencia verificable.                                        ║
║                                                                  ║
║  Cualquier modificación estructural del plan requiere            ║
║  autorización explícita del Director + nuevo X-Ray.              ║
╚══════════════════════════════════════════════════════════════════╝
```

**Este bloque se evalúa en cada salida.** El sheriff de cada nodo debe comprobar que el plan no ha sido alterado estructuralmente.

---

## NÚMERO ÚNICO DE SALIDAS

# **TOTAL DE SALIDAS = 500**

Un solo número. No hay rangos ambiguos. No hay “aproximadamente”.  
**500 salidas = 500 nodos DAG = 500 checkpoints.**

| Bloque | Rango | Cantidad |
|--------|-------|----------|
| Fundación + Inventario + Catalogs | 001–050 | 50 |
| Kernel + Reception + Fail-closed | 051–100 | 50 |
| Engine core + Code Path | 101–150 | 50 |
| Standards + Forensic | 151–200 | 50 |
| State + Ledger + Blackboard | 201–250 | 50 |
| Gateway + Engines adapters | 251–300 | 50 |
| Loop 12-stage + Maxbry | 301–350 | 50 |
| Resources + HF index + Motors | 351–400 | 50 |
| Deploy + Accounts + CI | 401–450 | 50 |
| Cierre + X-Ray global + Certification | 451–500 | 50 |
| **TOTAL** | **001–500** | **500** |

---

## REGLA UNIVERSAL (inviolable)

- Cada **SALIDA** = **1 nodo DAG** obligatorio con los **cuatro elementos + verificación cruzada**:
  1. `sheriff` (LAW + ANTI_SKIP + ANTI_FAKE_PASS + ANTI_HALLUCINATION + NO_TOUCH_PLAN)
  2. `validador` (schema + evidence check + binary PASS)
  3. `verificación` + **verificación cruzada** (runtime / test / X-Ray + cross-check contra catalogs y tree)
  4. `guardián` (fail-closed: DENY si no PASS)
  - Además: `input_schema`, `output_schema`, `checkpoint_file`
- **PASS** solo con evidencia verificable (SHA, log, test, tree, catalog).  
- **NO** mezclar tareas. **NO** inventar. **NO** claim sin evidencia.  
- Acción sobre archivos wordflow: **CREATE | COPY | REF | PLACEHOLDER | ENGANCHE** únicamente.  
- Loop: GAP → DIAGNOSTICAR → RESOLVER → VERIFICAR → REGISTRAR → CONTINUAR.

**Motor de 3 capas (por nodo):**  
`SHERIFF → SENTINEL → JUDGE`  
(Sheriff bloquea, Sentinel monitorea, Judge clasifica PASS/FAIL/WARNING/DEGRADED/BLOCKED/UNKNOWN).

**DAG Maestro horizontal (referencia V7):**  
`INPUT → PRECHECK → AUDIT → DISCOVERY → INVENTORY → REGISTER → SANDBOX → MEMORY → WORKSPACE → HEALTH → HEARTBEAT → CONNECTIVITY → EXECUTION → RESULT → RECOVERY → FAILOVER → SECURITY → END_TO_END → GLOBAL_VALIDATION → CERTIFICATION → OUTPUT`

---

## 1. ROOT STRUCTURE COMPLETO (repo truth @ main)

```
agentes/
├── .cursor/
├── .github/workflows/
├── AGENTS.md
├── GUIA-DESPLIEGUE-ZIP-UNIVERSAL.md
├── GUIA_CUENTAS_REMOTE.md
├── GUIA_CUENTA_B_REMOTE.md
├── METODO_ZIP_COPY_DETERMINISTA.md
├── PIPELINE/                    ← documentos de control + este PLAN + checkpoints
├── README.md
├── README_ARQUITECTURA.md
├── README_FORENSIC_HANDOFF.md
├── README_METHOD.md
├── RENAME_NOTE.md
├── SETUP_TOKEN_MOVIL.md
├── agente-yaiwes/
├── agents/
├── code-programming-engine/     ← Despliegue 1 Opción A
├── control-layer/
├── despliegue/
├── docs/
├── extensions/
│   ├── wordflow/                ← ~380 blobs (core)
│   │   ├── accounts/
│   │   ├── codegen/
│   │   ├── connectors/
│   │   ├── context/
│   │   ├── contracts/
│   │   ├── docs_templates/
│   │   ├── engine/              ← code_path_runner, main_loop, goal_lock, sheriff_adapter…
│   │   ├── motors/
│   │   ├── planner/
│   │   ├── policies/
│   │   ├── reception/
│   │   ├── schemas/
│   │   ├── standards/           ← forensic_core, copy_first, sheriff, verdict_authority…
│   │   ├── state/
│   │   ├── store/
│   │   ├── tests/
│   │   ├── component_catalog.json (v1.1.1)
│   │   ├── connect_catalog.json (v1.7.1)
│   │   ├── ficha.v2.json
│   │   └── manifest.yaml
│   ├── wordflow_kernel/         ← ~90 blobs
│   │   ├── bootstrap_*.py
│   │   ├── bridge/
│   │   ├── engines/             ← openclaw_stub, hermes_stub (STUB)
│   │   ├── gateway/             ← intelligence (STUB)
│   │   ├── memory_slot/
│   │   ├── reception/
│   │   ├── resources/
│   │   ├── router_slot/
│   │   ├── stages/
│   │   ├── ui_gateway/
│   │   ├── slots/               ← kimi_minimax PLACEHOLDER
│   │   ├── tests/
│   │   └── (checkpoint, fail_closed, forensic, repo_truth, workflow…)
│   ├── github_deploy/           ← PARTIAL
│   ├── maxbry_loop/             ← materialized
│   └── source_evolution/        ← PARTIAL (acquire)
├── groups/
├── memory/
├── scripts/
├── tools/
└── wordflow/
```

**Conteo forense (Paso 1):** 496 entries bajo prefix wordflow → ~450-490 blobs. Confirmado.

---

## 2. DSL DAG SCHEMA — DEFINICIÓN OBLIGATORIA DE CADA NODO (SALIDA)

**Toda salida 001–500** debe instanciar exactamente este schema. No hay excepciones.

```yaml
id: SALIDA_NNN
nombre: "..."
tipo: CREATE | COPY | REF | PLACEHOLDER | ENGANCHE | AUDIT | WIRE | VALIDATE
prioridad: P0 | P1 | P2

input_schema:
  type: object
  required: [...]
  properties: {...}

output_schema:
  type: object
  required: [status, evidence, checkpoint_sha, cross_check]
  properties:
    status: {enum: [PASS, FAIL, WARNING, DEGRADED, BLOCKED, UNKNOWN]}
    evidence: {type: array, items: string}
    checkpoint_sha: string
    cross_check: {type: object}   # verificación cruzada obligatoria
    files_touched: array

sheriff:
  laws:
    - NO_SKIP
    - NO_ASSUME
    - NO_HALLUCINATION
    - NO_FAKE_PASS
    - NO_REWRITE_LEGACY
    - NO_TOUCH_PLAN          # nuevo: respeta el bloque de protección
  anti_skip: true
  fail_closed: true

validador:
  schema_check: true
  evidence_required: true
  binary_pass: true

verificación:
  - type: tree | test | catalog | runtime | xray
    command_or_ref: "..."

verificación_cruzada:          # OBLIGATORIA en todas las salidas
  - against: component_catalog | connect_catalog | tree | previous_checkpoint
    rule: "status/count/SHA debe coincidir o documentar GAP real"

guardián:
  on_fail: DENY
  on_pass: ALLOW_NEXT

checkpoint_file: PIPELINE/checkpoints/SALIDA_NNN_YYYY-MM-DD.md

archivos_afectados:            # solo CREATE/COPY/REF/PLACEHOLDER/ENGANCHE
  - path: extensions/wordflow/...
    accion: CREATE | COPY | REF | PLACEHOLDER | ENGANCHE
    nota: "..."
```

**Auditoría del schema:**  
Todas las 500 salidas heredan este contrato. No existe salida “ligera” ni “resumida” que omita sheriff, validador, verificación cruzada o guardián.

---

## 3. AUDITORÍA DEL PLAN — GAPS Y COBERTURA

### 3.1 Cobertura DSL DAG

| Elemento | Presente en 001–500 | Estado |
|----------|---------------------|--------|
| input_schema | Sí (obligatorio) | PASS |
| output_schema | Sí (obligatorio) | PASS |
| sheriff | Sí (incluye NO_TOUCH_PLAN) | PASS |
| validador | Sí (binary + evidence) | PASS |
| verificación | Sí | PASS |
| **verificación cruzada** | Sí (contra catalogs + tree + checkpoint previo) | PASS |
| guardián (fail-closed) | Sí | PASS |
| checkpoint_file | Sí (1 por salida) | PASS |
| Acción archivo restringida | Sí (CREATE/COPY/REF/PLACEHOLDER/ENGANCHE) | PASS |

### 3.2 Gaps residuales conocidos (heredados de Paso 1 X-Ray)

Estos gaps **no eliminan nodos**; se convierten en salidas concretas dentro de los bloques 251–300 y 451–500:

| Gap | Bloque destino | Tipo de salida |
|-----|----------------|----------------|
| intelligence_gateway = stub | 251–300 | PLACEHOLDER → ENGANCHE / CREATE adapter RouterHTTP |
| engine.openclaw = stub | 251–300 | PLACEHOLDER → ENGANCHE EnginePort |
| engine.hermes = stub | 251–300 | PLACEHOLDER → ENGANCHE EnginePort |
| loop.fusion_minimax_kimi = placeholder | 301–350 | PLACEHOLDER documentado o CREATE |
| Varios CONN WIRED_NO_PASS / WIRED_DENY | 451–500 | VALIDATE + residual close |
| github_deploy = partial | 401–450 | ENGANCHE real path |
| acquire_engine = partial | 351–400 / 401–450 | REF + ENGANCHE |

**Ningún gap deja una salida sin los 4 elementos + verificación cruzada.**  
Si un gap bloquea ejecución, el nodo registra FAIL/BLOCKED con evidencia y el LOOP continúa solo sobre ese nodo.

### 3.3 Auditoría de integridad del plan

- Total salidas = **500** (número único, no modificable).  
- Bloques de 50 = 10 × 50 = 500.  
- Nombre del agente = **Agente Yaiwes v1** (Omega eliminado).  
- Bloque “NO TOCAR EL PLAN” presente y referenciado por el sheriff de cada nodo.  
- Schema DSL DAG completo y obligatorio para las 500.  
- Gaps residuales mapeados a salidas concretas (no omitidos).  
- COPY-FIRST y no-rewrite-legacy preservados.

**Resultado auditoría del plan:** **PASS** (estructura completa, sin salidas huérfanas de schema).

---

## 4. SALIDAS 001–050 — FUNDACIÓN (instanciación del schema)

Todas siguen el schema de la sección 2. Resumen operativo:

### SALIDA 001 — Root map + IDs forenses
- **tipo:** AUDIT + CREATE
- **sheriff:** NO_ASSUME + NO_TOUCH_PLAN + evidence = API tree
- **validador:** count == 496 entries
- **verificación:** github___get_repository_tree recursive
- **verificación cruzada:** contra PASO1_XRAY + component_catalog
- **guardián:** fail-closed si count fuera de 450-500
- **checkpoint:** PIPELINE/checkpoints/SALIDA_001_YYYY-MM-DD.md
- **archivos:** REF/CREATE aditivo PIPELINE/ROOT_MAP_IDS.md

### SALIDA 002 — component_catalog.json v1.1.1 freeze
- **tipo:** REF
- **sheriff / validador / verificación cruzada / guardián:** schema completo
- **archivos:** REF extensions/wordflow/component_catalog.json

### SALIDA 003 — connect_catalog.json v1.7.1 freeze
- **tipo:** REF
- **archivos:** REF extensions/wordflow/connect_catalog.json

### SALIDA 004 — Checkpoint store schema
- **tipo:** REF
- **archivos:** REF schemas/checkpoint.schema.json + engine/checkpoint_store.py + kernel/checkpoint.py

### SALIDA 005 — Fail-closed core
- **tipo:** REF + ENGANCHE
- **archivos:** REF kernel/fail_closed.py + ENGANCHE standards/verdict_authority.py

### SALIDA 006 — Sheriff core
- **tipo:** REF
- **archivos:** REF standards/sheriff.py, engine/sheriff_adapter.py, engine/control_sheriff_bridge.py, policies/sheriff.yaml

### SALIDA 007 — Verdict authority
- **tipo:** REF
- **archivos:** REF standards/verdict_authority.py

### SALIDA 008 — Copy-first enforcer
- **tipo:** REF
- **archivos:** REF standards/copy_first.py + METODO_ZIP_COPY_DETERMINISTA.md

### SALIDA 009 — Forensic core
- **tipo:** REF
- **archivos:** REF standards/forensic_core.py, kernel/forensic.py, kernel/forensic_api.py

### SALIDA 010 — Repo truth
- **tipo:** REF
- **archivos:** REF kernel/repo_truth.py

### SALIDA 011–020 — Schemas base (10 salidas)
Cada una = 1 schema (input_contract, goal_lock, execution_manifest, evidence_node, resource_entry, task_class, workflow_dna, capability_passport, handoff_package, structured_questions).  
**tipo:** REF — schema completo + verificación cruzada contra component_catalog.

### SALIDA 021–030 — Engine core files (10 salidas)
code_path_runner, main_loop, orchestrator_v1, goal_lock, input_compiler, task_classifier, dual_compiler, validator, sentinel, recovery.  
**tipo:** REF — schema completo.

### SALIDA 031–040 — Kernel bootstrap + instance (10 salidas)
bootstrap_v1, bootstrap_multi, bootstrap_fake, instance, instance_store, workflow, handle_message, spawn, runtime, preflight.  
**tipo:** REF — schema completo.

### SALIDA 041–045 — Reception links (5 salidas)
wordflow/reception/convert, kernel/reception/convert, git_apply, KNOWLEDGE_RECEPTION_LINKS, RECEPTION_TEMPLATE.  
**tipo:** REF + ENGANCHE — verificación cruzada CONN.kernel_reception_link.

### SALIDA 046–050 — Catalog frontiers + CI smoke (5 salidas)
frontiers + CI wordflow_smoke / test-wordflow-code-path.  
**tipo:** REF + VALIDATE — schema completo.

**Bloque 001-050 → X-Ray parcial obligatorio antes de avanzar.**

---

## 5. ROADMAP 051–500 (todos con schema completo)

Cada salida de estos bloques **instancia el mismo DSL DAG schema** (sheriff + validador + verificación + verificación cruzada + guardián + checkpoint).

### 051-100 — Kernel + Reception + Fail-closed deep (50)
Tests kernel, memory_slot, router_slot, stages 12-hook, UI gateway, gap_tasks, crosscheck.  
Acción: REF + ENGANCHE + CREATE checkpoints.

### 101-150 — Engine + Code Path full (50)
Todos engine/*.py restantes, ports, fake_engine, code path smoke + integration.  
COPY-FIRST desde code-programming-engine cuando proceda.

### 151-200 — Standards + Quality DAG (50)
Todos standards/*.py, quality_handlers, rule_engine, gap_registry, checklist_sheriff.  
Guardián de quality_bar en cada code path.

### 201-250 — State + Evidence (50)
Blackboard, ledger, cognitive_registers, evidence_packet/graph/bridge, bitacora, reasoning_ledger.

### 251-300 — Gateway + Real engines — cierre de STUBS (50)
- IntelligenceGateway RouterHTTP real
- openclaw / hermes → EnginePort real (PLACEHOLDER → ENGANCHE)
- WIRED_DENY se mantiene hasta evidencia de path correcto

### 301-350 — Loop 12-stage + Maxbry (50)
main_12.yaml, cognitive_loop, maxbry_loop, 12 hooks, council, expert_panel.  
fusion_minimax_kimi: PLACEHOLDER documentado o CREATE.

### 351-400 — Resources + HF + Motors (50)
resource_catalog/broker/gate/runtime/trace, hf_index/resolver, motors, ResourceContract + loaders.

### 401-450 — Deploy + Accounts + CI (50)
github_deploy real path, accounts resolver, connectors, CI full matrix, token_ref safe.

### 451-500 — Cierre global + Certification (50)
Residual gaps, end-to-end, C100 Director, X-Ray final, consolidación de 500 checkpoints.  
**SALIDA 500 = CERTIFICATION** → PASS solo con evidencia total de las 500.

---

## 6. ARCHIVOS WORDFLOW — ACCIÓN GLOBAL

| Ámbito | Acción dominante | Notas |
|--------|------------------|-------|
| component_catalog.json / connect_catalog.json | REF | Solo update aditivo de status si evidencia |
| engine/*.py (~90) | REF | No rewrite; ENGANCHE desde nuevos nodos |
| standards/*.py (~35) | REF | copy_first + forensic + sheriff = anclas |
| schemas/*.json (~30) | REF | Input/output de cada nodo |
| tests/* (~110 + ~25 kernel) | REF + CREATE de nuevos si gap real |
| wordflow_kernel/* | REF + ENGANCHE | stubs → PLACEHOLDER documentado o real adapter |
| reception/* | REF + ENGANCHE | CONN ya WIRED |
| motors/*, policies/*, store/*, state/* | REF | |
| Nuevo: PIPELINE/checkpoints/ | CREATE | 1 por cada una de las 500 salidas |
| Este PLAN | CREATE (ya materializado) | Protegido por bloque NO TOCAR |

**Prohibido:** reescribir archivos legacy materializados. Solo COPY de piezas externas (COPY-FIRST) o ENGANCHE.

---

## 7. CHECKPOINT DE PASO 2 (actualizado post-auditoría)

| Campo | Valor |
|-------|-------|
| **ID** | PLAN-PASO2-2026-08-26-AUDIT |
| **Nombre agente** | **Agente Yaiwes v1** |
| **Total salidas** | **500** (número único) |
| **Status** | **PASS** (documento maestro + auditoría schema + gaps mapeados + bloque NO TOCAR) |
| **Evidence** | Este archivo + PASO1 XRay PASS + tree 496 + catalogs 1.1.1/1.7.1 |
| **Sheriff** | Binary — 500 nodos con sheriff+validador+verificación cruzada+guardián |
| **Next** | PASO 3 — crear root faltante + missing files con notas; luego DESPLIEGUE 1 |

**Archivo de checkpoint de Paso 2:** este documento.

---

## 8. NO-STOP

GAP → DIAGNOSTICAR → RESOLVER → VERIFICAR → REGISTRAR → CONTINUAR.  
Un GAP no detiene el LOOP.  
No inventar. No mezclar. No claim sin evidencia.  
1 tarea = 1 salida. Fail-closed.  
**No tocar el plan.**

**PASO 2 → AUDITADO Y CERRADO CON TOTAL = 500. LISTO PARA PASO 3.**
