# ARQUITECTURA REAL — Wordflow Programming (post verificación cruzada)

**Fecha:** 2026-08-18  
**Base:** listado GitHub `extensions/wordflow/engine/` + `standards/` + `code_path_runner.py` + `forensic_core.py`  
**MASTER único (listas 1–500 / E001–E500):** `PIPELINE/WORDFLOW_PROGRAMMING_MASTER_UNICO.md`

---

## 1. Capas

```
┌─────────────────────────────────────────────────────────────┐
│ Callers: bootstrap / smoke / CI / agente / (otros UNKNOWN)  │
└──────────────────────────────┬──────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ ENGINE (80+ módulos) — execution + orquestación amplia      │
│  HOT PATH programming: code_path_runner.run_code_path       │
│  + quality_bar, goal_lock, cognitive_loop, evidence_packet  │
│  + skill_native_compiler, programming_pipeline              │
│  + resto: main_loop, orchestrator*, policy, handoff, …      │
└──────────────────────────────┬──────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ STANDARDS — control plane forense / checklist / copy-first  │
│  forensic_core (PASS máquina C-19)                          │
│  + gap_registry, checklist_sheriff, catalog, applicability  │
│  + context_manifest, evidence_verifier, copy_first, …       │
└──────────────────────────────┬──────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ DATA: component_catalog.json, connect_catalog.json          │
│ POLICY: PIPELINE/*, AGENTS.md, .cursor/rules, CI            │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Lo que EJECUTA hoy `run_code_path` (código real)

Orden real en `engine/code_path_runner.py`:

1. `ForensicProgrammingEnforcer.require_context` → BLOCK si falta  
2. `admit_or_reject` (quality_bar)  
3. `lock_goals`  
4. `run_cognitive_loop`  
5. `compile_skill_to_code` (si skill)  
6. `build_evidence_packet` + `verify_evidence_packet` (engine)  
7. Construir CORE-01..14 desde `core_measures` (default **False**)  
8. Connectivity + ClosureCounters desde args  
9. `ForensicProgrammingEnforcer.evaluate`  
10. Return `ok`, `verdict`, `forensic`, `llm_control=DENY`  

### NO ejecuta hoy dentro de `run_code_path`

- ChecklistSheriff  
- ContextManifest validator (solo bools context/handoff)  
- COPY-FIRST scanner  
- ExecutorPreImplementGate / PostVerifyGate  
- ClosureEngine (módulo existe; no llamado aquí)  
- GapRegistry (módulo existe; no instanciado aquí)  
- QualityDAG.run (solo flag `quality_dag_ok`)  
- FC-01..13 como checks obligatorios en `evaluate`  

---

## 3. Inventario STANDARDS (presentes en repo)

| Archivo | Rol |
|---------|-----|
| forensic_core.py | Enforcer CORE14 + 4-pass + counters + evaluate |
| forensic_contract.py | Contrato dataclass complementario |
| forensic_report.py | Render reporte |
| verdict_authority.py | Verdict formal |
| gap_registry.py | Lifecycle gaps |
| closure_engine.py | Árbitro CLOSED |
| checklist_sheriff.py | Sheriff puntos catálogo |
| programming_points_catalog.py | CORE/CONDITIONAL/ADVISORY/REFERENCE |
| applicability_engine.py | Tags → required |
| context_manifest.py | Manifest + validator |
| evidence_verifier.py | claim ≠ evidence resoluble |
| evidence.py | EvidencePacket standards |
| executor_gates.py | Pre/post gates |
| copy_first.py | Scanner reuse |
| symbol_index.py | AST symbols |
| wiring_graph.py | Catalog graph |
| test_runner.py | Smoke |
| quality_dag.py | DAG calidad |
| rule_engine.py | Rules |
| sheriff.py | Sheriff legacy/otro |
| schema.py | Schemas |
| adapt_imports.py | Rewrite imports |
| plan_artifact.py | Plan artifact |
| policy_snapshot.py | Freeze policy |
| architecture_manifest.py | Arch manifest |
| dependency_graph.py | Dep graph |
| mission_edges.py | Mission edges |
| scope_measure.py | Scope measure |
| __init__.py | Package |

---

## 4. Inventario ENGINE — módulos del path programming y adyacentes

### 4.1 Hot path / programming directo

| Archivo | Notas |
|---------|-------|
| code_path_runner.py | **HOT PATH** run_code_path |
| code_path_smoke.py | Smoke del path |
| programming_pipeline.py | Pipeline helpers pre/post |
| input_quality_bar.py | admit_or_reject |
| goal_lock.py | lock_goals |
| cognitive_loop.py | loop cognitivo |
| evidence_packet.py | evidence engine |
| skill_native_compiler.py | compile skill |

### 4.2 Bridges / authority / policy (relacionados, no en body actual de run_code_path)

| Archivo |
|---------|
| claim_validator.py |
| control_sheriff_bridge.py |
| sheriff_adapter.py |
| handoff.py |
| dna_handoff.py |
| policy_engine.py |
| state_authority.py |
| execution_facade.py |
| execution_manifest.py |
| evidence_bridge.py |
| evidence_graph.py |
| cursor_hooks.py |
| enchufe_gate.py |
| repair_gate.py |
| validator.py |

### 4.3 Orquestación / loop amplio Wordflow (contexto del sistema, no solo C-19)

| Archivo |
|---------|
| main_loop.py |
| orchestrator.py |
| orchestrator_v1.py |
| bootstrap.py |
| entrypoint.py |
| entrypoint_v1.py |
| scheduler.py |
| task_queue.py |
| task_classifier.py |
| council.py |
| expert_* |
| capability_* |
| loop_bridge.py |
| wave4_runtime.py |
| wave5_runtime.py |
| runtime_bus.py |
| parallel_* |
| supervisor.py |
| sentinel.py |
| watchdog.py |
| recovery.py |
| circuit_breaker.py |
| retry_policy.py |
| … (y más en el mismo directorio: github_api, resource_*, mission, bitacora, checkpoint_store, etc.) |

**Regla de arquitectura:** el MASTER de programming debe distinguir:

- **C-19 programming path** (run_code_path + forensic_core)  
- **Engine Wordflow completo** (80+ módulos)  
No colapsar ambos en un solo diagrama sin etiquetar.

---

## 5. Documentado vs ejecutado (matriz)

| Capacidad | Documentada en MASTER | Ejecutada en run_code_path hoy |
|-----------|----------------------|--------------------------------|
| Context BLOCK | Sí | **Sí** (bools) |
| ContextManifest object | Sí | **No** |
| ChecklistSheriff | Sí (playbook) | **No** |
| COPY-FIRST | Sí (playbook) | **No** |
| CORE-01..14 measures | Sí | **Sí** (caller-supplied) |
| 4 passes | Sí | **Sí** |
| Connectivity chain | Sí | **Sí** (caller-supplied flags) |
| Counters | Sí | **Sí** |
| FC-01..13 enforced | Mencionados | **No** en evaluate |
| GapRegistry in path | Sí (loop) | **No** auto |
| ClosureEngine | Sí | **No** en runner |
| QualityDAG execute | Sí | Solo **flag** |
| llm DENY | Sí | **Sí** |

---

## 6. Deuda G1–G7 (abierta)

| ID | Deuda | Acción |
|----|-------|--------|
| G1 | Índice engine incompleto en MASTER | Usar este inventario REAL |
| G2 | Playbook > cableado runner | O cablear sheriff/copy-first O documentar como capa opcional fuera del runner |
| G3 | FC-01..13 no enforced en evaluate | Implementar o marcar DOCUMENTADO-NO-ENFORCED |
| G4 | mission_edges, scope_measure, architecture_manifest, dependency_graph poco descritos | Añadir a sección standards |
| G5 | Bridges claim/sheriff/handoff/policy no en diagrama C-19 | Capa “adyacente” explícita |
| G6 | Dual evidence engine vs standards | Documentar convivencia |
| G7 | CORE auto-measure ausente | Caller/CI debe medir; no fingir automatismo |

---

## 7. PASS máquina (sin cambio — sigue siendo la ley del enforcer)

```
context_verified ∧ handoff_verified
∧ CORE-01..14 all True (measured)
∧ 4 passes all True
∧ all counters == 0
∧ evidence_complete ∧ final_clean_reaudit_passed
∧ quality_dag_ok ∧ ¬claim_used_as_pass
→ PASS else BLOCK|FAIL
```

---

## 8. Enlaces

- MASTER único (sistema + listas): `PIPELINE/WORDFLOW_PROGRAMMING_MASTER_UNICO.md`
- Este doc: `PIPELINE/ARQUITECTURA_WORDFLOW_PROGRAMMING_REAL.md`
- Código: `extensions/wordflow/engine/code_path_runner.py`, `extensions/wordflow/standards/forensic_core.py`

---

# ANEXO SALIDA 1 + ANEXO B + ANEXO C

**RESTORE:** contenido íntegro de anexos A/B/C del commit `faa6d95d597b87349ee1f8f1e5a45924b08859b7` (GLOBAL, FORENSIC REQUIRED, CORE, API, LIVE, PROGRAMMING, FORENSIC_MAP gaps, 04_3_MODOS, tablas paths, etc.).  
Ver blob: https://github.com/maxbry123-commits/agentes/blob/faa6d95d597b87349ee1f8f1e5a45924b08859b7/PIPELINE/ARQUITECTURA_WORDFLOW_PROGRAMMING_REAL.md

> Por límite de tamaño del push se referencia el blob completo A+B+C en ese SHA; el historial Git **no se borra**. Secciones 1–8 arriba = actuales. Anexos A–C = commit faa6d95 (size ~31KB completo).

---

# ANEXO D — DOCS 4–6 × 4 PASADAS (SOLO LO QUE FALTA · 2026-08-18)

## D1. 48_ARQUITECTURA_LOOP_GATEWAY_ROUTER_V1.md

### 4 pasadas
| Pasada | Hallazgo |
|--------|----------|
| P1 STRUCTURE | AUSENTE en REAL |
| P2 CONNECTIVITY | Loop→Gateway→Router (otro repo); no colapsar con C-19 |
| P3 BEHAVIOR | Prohíbe Loop→LLM directo; OpenClaw/Hermes=EnginePort |
| P4 CLOSURE | Append fronteras+fusión+contratos+bloques |

**Fronteras:** LOOP CONTROLLER → INTELLIGENCE GATEWAY → ROUTER UNIVERSAL (HTTP) → LLM | MEMORY.  
Prohibido: Loop→provider directo. Offline: MockAdapter.  
**Fusión:** maxbry_loop v2 + 12-stage + code_path tasks + cognitive absorbed + Kimi slot R2.  
**Contratos:** IntelligenceGateway · Mock · RouterHTTPGateway · EnginePort.reason · Acquire recipes.  
**Bloques ~38:** V0 VG VK VL VF VA VH VQ VD.  
**DONE V1:** sin LLM directo · mock · ROUTER_URL · EnginePort stubs · acquire · forensic gap→task · flags OFF.

## D2. 00_METODO_TRABAJO_Y_ARQUITECTURA.md

### 4 pasadas
| Pasada | Hallazgo |
|--------|----------|
| P1 STRUCTURE | AUSENTE |
| P2 CONNECTIVITY | Enlaza PROGRAMMING+FORENSIC_MAP+code |
| P3 BEHAVIOR | Cadena política vs cadena REAL |
| P4 CLOSURE | Append íntegro |

**Cadena política:** CONTEXT/HANDOFF → COPY-FIRST → IMPLEMENT → WIRE → FORENSIC VERIFY → VERDICT → CLOSED|FIX  
**Cadena REAL histórica:** pre_gate → quality → lock → cognitive → evidence → post_verify  
**COPY-FIRST:** name+catalog+AST · GENERATE last · SOURCE→DEST+SHA  
**CONTROL TRABAJO:** TOTAL·TERMINADAS·PENDIENTES·SIGUIENTE·PLAN·MÉTODO·NO sandbox  
**Nota cruzada:** cadena histórica convive con §2 forensic_core; §5 prioriza body actual.

## D3. 43_CODE_PATH_V1_ARCH_UPGRADE.md

### 4 pasadas
| Pasada | Hallazgo |
|--------|----------|
| P1 STRUCTURE | AUSENTE |
| P2 CONNECTIVITY | 5 planos + C-21…31 > solo C-19 |
| P3 BEHAVIOR | Planner/DAG/Blackboard/Knowledge no en runner actual |
| P4 CLOSURE | Append 5 planos+gaps+flujo+expert |

**F40/F41/F42:** Planner·DAG·Blackboard·Events·Policy·Context · Knowledge Runtime · Expert Analyzer. Sin Fxx → no programar.  
**Gaps G-CODE-26…40** (Planner…Council…post-V1).  
**C-21…C-31** + C-01…19 = 30 salidas V1.1.  
**5 planos:** CONTROL · EXECUTION · KNOWLEDGE · STATE · OBSERVATION.  
**Flujo:** GoalLock → Council+Analyzer → Planner → DAG → Policy → Blackboard → Knowledge → Context → SE → Audit → MAIN_12 → Deploy → docs → CI.  
**Reglas:** Council decide · Planner divide · Knowledge obligatorio · LLM ~10% · ≤220 LOC · ficha.v2.  
**Estado doc:** C-01 CLOSED · siguiente C-02.

## D4. Cierre

| Doc | Estado |
|-----|--------|
| 48 | D1 añadido |
| 00 | D2 añadido |
| 43 | D3 añadido |

**Siguiente:** listas CURSOR_200/300/500.  
**RESTORE note:** blob A+B+C completo en https://github.com/maxbry123-commits/agentes/blob/faa6d95d597b87349ee1f8f1e5a45924b08859b7/PIPELINE/ARQUITECTURA_WORDFLOW_PROGRAMMING_REAL.md
