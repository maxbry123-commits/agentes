# PLAN YAIWES AGENTE WORDFLOW — DSL DAG SCHEMA

**Proyecto:** maxbry123-commits/agentes  
**Estado:** PASO 1 PASS → PASO 2 EN EJECUCIÓN  
**Actualización:** 2026-08-26  
**Modelo de referencia:** PIPELINE-HUGGINGFACE.md (Grupo-Trabajo-1) — estilo + disciplina, upgraded a DSL DAG.  
**Fundamento forense:** PIPELINE/PASO1_XRAY_WORDFLOW_400PLUS_2026-08-25.md (496 entries / ~470 blobs).  
**GitHub = truth.** COPY-FIRST. No re-write legacy. 1 tarea = 1 salida. Binary PASS only with evidence. Fail-closed.

---

## REGLA UNIVERSAL (inviolable)

- Cada **SALIDA** = **1 nodo DAG** con:
  - `input_schema` (JSON Schema / contrato)
  - `output_schema` (JSON Schema / contrato)
  - `sheriff` (LAW + ANTI_SKIP + ANTI_FAKE_PASS + ANTI_HALLUCINATION)
  - `validador` (schema + evidence check)
  - `verificación` (runtime / test / X-Ray)
  - `guardián` (fail-closed: DENY si no PASS)
  - `checkpoint_file` (PIPELINE/checkpoints/SALIDA_NNN_YYYY-MM-DD.md)
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

## 2. DSL DAG SCHEMA — DEFINICIÓN DE NODO (SALIDA)

Cada SALIDA NNN se registra exactamente así:

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
  required: [status, evidence, checkpoint_sha]
  properties:
    status: {enum: [PASS, FAIL, WARNING, DEGRADED, BLOCKED, UNKNOWN]}
    evidence: {type: array, items: string}
    checkpoint_sha: string
    files_touched: array

sheriff:
  laws: [NO_SKIP, NO_ASSUME, NO_HALLUCINATION, NO_FAKE_PASS, NO_REWRITE_LEGACY]
  anti_skip: true
  fail_closed: true

validador:
  schema_check: true
  evidence_required: true
  binary_pass: true

verificación:
  - type: tree | test | catalog | runtime | xray
    command_or_ref: "..."

guardián:
  on_fail: DENY
  on_pass: ALLOW_NEXT

checkpoint_file: PIPELINE/checkpoints/SALIDA_NNN_YYYY-MM-DD.md

archivos_afectados:   # solo CREATE/COPY/REF/PLACEHOLDER/ENGANCHE
  - path: extensions/wordflow/...
    accion: CREATE | COPY | REF | PLACEHOLDER | ENGANCHE
    nota: "..."
```

---

## 3. TOTALIZACIÓN DE SALIDAS (1 → 500)

| Rango | Fase | Objetivo | Nodos estimados |
|-------|------|----------|-----------------|
| 001-050 | Fundación + Inventario + Catalogs | Root, IDs, catalogs, schemas base, sheriff core | 50 |
| 051-100 | Kernel + Reception + Fail-closed | wordflow_kernel full, reception link, fail_closed, checkpoint store | 50 |
| 101-150 | Engine core + Code Path | code_path_runner, goal_lock, input_compiler, task_classifier, dual_compiler | 50 |
| 151-200 | Standards + Forensic | forensic_core, copy_first, quality_dag, verdict_authority, gap_registry | 50 |
| 201-250 | State + Ledger + Blackboard | ledger, blackboard, cognitive_registers, evidence_packet | 50 |
| 251-300 | Gateway + Engines adapters | IntelligenceGateway real (RouterHTTP), openclaw/hermes ports (no stub) | 50 |
| 301-350 | Loop 12-stage + Maxbry | main_loop, cognitive_loop, maxbry_loop wiring, 12 hooks | 50 |
| 351-400 | Resources + HF index + Motors | resource_catalog, hf_index, motors (call/download/send/kernel_ext) | 50 |
| 401-450 | Deploy + Accounts + CI | github_deploy real path, accounts resolver, CI workflows, smoke | 50 |
| 451-500 | Cierre + X-Ray global + Certification | End-to-end, residual gaps, C100 Director, final X-Ray, PASS total | 50 |
| **TOTAL** | | | **500** |

Cada nodo produce **1 checkpoint file**. Al final de cada bloque de 50 se ejecuta X-Ray parcial + consolidación.

---

## 4. SALIDAS 001–050 — FUNDACIÓN (detalle completo)

### SALIDA 001 — Root map + IDs forenses
- **tipo:** AUDIT + CREATE
- **input_schema:** {repo_sha, tree_recursive}
- **output_schema:** {root_map.md, ids: [WF.xx, WK.xx, FILE.xxx], status}
- **sheriff:** NO_ASSUME, evidence = API tree
- **validador:** count == 496 entries
- **verificación:** github___get_repository_tree recursive
- **guardián:** fail-closed si count fuera de 450-500
- **checkpoint:** PIPELINE/checkpoints/SALIDA_001_2026-08-26.md
- **archivos:** CREATE PIPELINE/ROOT_MAP_IDS.md (ya existe → REF + update aditivo)

### SALIDA 002 — component_catalog.json v1.1.1 freeze
- **tipo:** REF
- **input:** catalog_version 1.1.1
- **output:** status matrix locked
- **sheriff:** no modificar status sin evidencia
- **archivos:** REF extensions/wordflow/component_catalog.json

### SALIDA 003 — connect_catalog.json v1.7.1 freeze
- **tipo:** REF
- **input:** version 1.7.1 + task DESPLIEGUE-01
- **output:** legend + connections locked
- **archivos:** REF extensions/wordflow/connect_catalog.json

### SALIDA 004 — Checkpoint store schema
- **tipo:** CREATE (si falta) / REF
- **input:** schemas/checkpoint.schema.json
- **output:** engine/checkpoint_store.py + kernel/checkpoint.py validados
- **archivos:** REF extensions/wordflow/schemas/checkpoint.schema.json, REF engine/checkpoint_store.py, REF kernel/checkpoint.py

### SALIDA 005 — Fail-closed core
- **tipo:** REF + ENGANCHE
- **input:** kernel/fail_closed.py
- **output:** guardián binary PASS/FAIL
- **archivos:** REF extensions/wordflow_kernel/fail_closed.py, ENGANCHE a standards/verdict_authority.py

### SALIDA 006 — Sheriff core
- **tipo:** REF
- **archivos:** REF standards/sheriff.py, REF engine/sheriff_adapter.py, REF engine/control_sheriff_bridge.py, REF policies/sheriff.yaml

### SALIDA 007 — Verdict authority
- **tipo:** REF
- **archivos:** REF standards/verdict_authority.py

### SALIDA 008 — Copy-first enforcer
- **tipo:** REF
- **archivos:** REF standards/copy_first.py, REF METODO_ZIP_COPY_DETERMINISTA.md (root)

### SALIDA 009 — Forensic core
- **tipo:** REF
- **archivos:** REF standards/forensic_core.py, REF kernel/forensic.py, REF kernel/forensic_api.py

### SALIDA 010 — Repo truth
- **tipo:** REF
- **archivos:** REF kernel/repo_truth.py

### SALIDA 011–020 — Schemas base (batch)
Cada una = 1 schema JSON:
- input_contract, goal_lock, execution_manifest, evidence_node, resource_entry, task_class, workflow_dna, capability_passport, handoff_package, structured_questions
- **tipo:** REF
- **archivos:** REF extensions/wordflow/schemas/*.schema.json (uno por salida)

### SALIDA 021–030 — Engine core files (batch)
- code_path_runner, main_loop, orchestrator_v1, goal_lock, input_compiler, task_classifier, dual_compiler, validator, sentinel, recovery
- **tipo:** REF
- **archivos:** REF extensions/wordflow/engine/<file>.py

### SALIDA 031–040 — Kernel bootstrap + instance
- bootstrap_v1, bootstrap_multi, bootstrap_fake, instance, instance_store, workflow, handle_message, spawn, runtime, preflight
- **tipo:** REF
- **archivos:** REF extensions/wordflow_kernel/<file>.py

### SALIDA 041–045 — Reception links
- wordflow/reception/convert.py, kernel/reception/convert.py, git_apply, KNOWLEDGE_RECEPTION_LINKS, RECEPTION_TEMPLATE
- **tipo:** REF + ENGANCHE
- **archivos:** REF + ENGANCHE CONN.kernel_reception_link

### SALIDA 046–050 — Catalog frontiers + CI smoke
- frontiers loop/gateway/router/engines/acquire
- CI wordflow_smoke / test-wordflow-code-path
- **tipo:** REF + VALIDATE
- **archivos:** REF component_catalog frontiers, REF .github/workflows/*

**Bloque 001-050 → X-Ray parcial obligatorio antes de avanzar.**

---

## 5. ROADMAP 051–500 (resumen por bloque)

### 051-100 — Kernel + Reception + Fail-closed deep
- Completar todos los tests kernel (vf01-03, vg04, vh01-04, vk01-06, vl03-05, vr01-03)
- Memory_slot + router_slot contracts
- Stages 12-hook default_handlers
- UI gateway plugin
- Gap_tasks + crosscheck
- **Acción dominante:** REF + ENGANCHE + CREATE de checkpoints

### 101-150 — Engine + Code Path full
- Todos los engine/*.py restantes (resource_*, parallel_*, wave4/5, cognitive_*, expert_*, etc.)
- Ports memory_port / planning_port
- Engines/fake_engine
- Code path smoke + integration tests
- **COPY-FIRST** de cualquier pieza que se reutilice desde code-programming-engine

### 151-200 — Standards + Quality DAG
- Todos standards/*.py
- quality_handlers, rule_engine, gap_registry, gap_state_machine
- Checklist_sheriff, programming_points_catalog
- **Guardián** de quality_bar en cada code path

### 201-250 — State + Evidence
- Blackboard, ledger, cognitive_registers, evidence_packet, evidence_graph, evidence_bridge
- Bitacora, reasoning_ledger, write_evidence

### 251-300 — Gateway + Real engines (cerrar STUBS)
- **P0:** IntelligenceGateway RouterHTTP real (cerrar stub)
- openclaw_stub → EnginePort real adapter (PLACEHOLDER → ENGANCHE)
- hermes_stub → EnginePort real adapter
- loop.fusion_minimax_kimi: PLACEHOLDER → decidir CREATE o dejar fusion:false documentado
- **Sheriff:** WIRED_DENY permanece hasta evidencia de vendor path correcto

### 301-350 — Loop 12-stage + Maxbry
- main_12.yaml, cognitive_loop, maxbry_loop full wiring
- 12 hooks: acquire_12, analyze_12, reuse_12, etc.
- Council + expert_panel + expert_router

### 351-400 — Resources + HF + Motors
- resource_catalog, resource_broker, resource_gate, resource_runtime, resource_trace
- hf_index, hf_resolver
- motors call/download/send/kernel_ext
- ResourceContract + dataset/skill/space loaders (kernel)

### 401-450 — Deploy + Accounts + CI
- github_deploy real (no solo dry_run)
- accounts registry/require/resolver
- connectors/github_external
- CI full matrix + smoke
- Token_ref never in body (already WIRED)

### 451-500 — Cierre global + Certification
- Residual gaps de connect_catalog (WIRED_NO_PASS, STUB, PLACEHOLDER)
- End-to-end test suite
- C100 Director claim
- X-Ray final completo (re-run tree + catalogs + status matrix)
- Checkpoint consolidado de las 500 salidas
- **SALIDA 500 = CERTIFICATION** → solo PASS con evidencia total

---

## 6. ARCHIVOS WORDFLOW — ACCIÓN GLOBAL (resumen)

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
| Nuevo: PIPELINE/checkpoints/ | CREATE | 1 por salida |
| Nuevo: este PLAN | CREATE | |

**Prohibido:** reescribir archivos legacy materializados. Solo COPY de piezas externas (COPY-FIRST) o ENGANCHE.

---

## 7. CHECKPOINT DE PASO 2

| Campo | Valor |
|-------|-------|
| **ID** | PLAN-PASO2-2026-08-26 |
| **Status** | **EN CURSO** (documento maestro materializado) |
| **Evidence** | Este archivo + PASO1 XRay PASS + tree 496 + catalogs 1.1.1/1.7.1 |
| **Sheriff** | Binary — estructura + totalización 500 + schema de nodo definidos |
| **Next** | PASO 3 — crear root faltante + missing files con notas; luego DESPLIEGUE 1 de documentos adjuntos + chain execution |

**Archivo de checkpoint de Paso 2:** este documento.

---

## 8. NO-STOP

GAP → DIAGNOSTICAR → RESOLVER → VERIFICAR → REGISTRAR → CONTINUAR.  
Un GAP no detiene el LOOP.  
No inventar. No mezclar. No claim sin evidencia.  
1 tarea = 1 salida. Fail-closed.

**PASO 2 → DOCUMENTO MAESTRO MATERIALIZADO. LISTO PARA PASO 3 Y DESPLIEGUE 1.**
