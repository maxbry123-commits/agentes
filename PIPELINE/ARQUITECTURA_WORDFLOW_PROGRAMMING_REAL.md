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

# ANEXO SALIDA 1 — RECUPERACIÓN ARQUITECTURA ANTERIOR (SOLO ADICIÓN · 2026-08-18)

**Método:** copiar desde documentos anteriores de arquitectura/enforcement/sistema. **No se borró ninguna palabra** de las secciones 1–8 anteriores.

## A1. Arquitectura Wordflow Global (recuperado de ARQUITECTURA_WORDFLOW_GLOBAL.md)

### Control plane (fail-closed)
`standards/forensic_core.py` → CORE14 + 4-pass + counters + PASS rules  
`standards/gap_registry.py` → lifecycle gaps  
`standards/checklist_sheriff.py` + applicability + evidence_verifier  
`standards/verdict_authority.py` / closure_engine  

### Execution plane
`engine/code_path_runner.py` — BLOCK sin context; forensic evaluate obligatorio; llm DENY  

### Data
catalogs JSON · PIPELINE policy docs · CI forensic-gates  

### Regla de oro
CLAIM ≠ EVIDENCE ≠ VERIFICATION ≠ PASS  
NO VERIFIED CONTEXT → NO PROGRAMMING / NO AUDIT  
REQUIRED no se bypasea  

## A2. Forensic Programming Enforcement REQUIRED (recuperado de FORENSIC_ENFORCEMENT_REQUIRED.md)

### Runtime
- `extensions/wordflow/standards/forensic_core.py` — CORE-01..14, 4-pass, counters, evaluate()
- `extensions/wordflow/engine/code_path_runner.py` — context BLOCK; measures explícitas; sin bypass REQUIRED
- `extensions/wordflow/standards/gap_registry.py` — campos completos + new_gaps_after_fix

### Rules
- NO VERIFIED CONTEXT → NO PROGRAMMING / NO AUDIT
- CLAIM ≠ EVIDENCE ≠ VERIFICATION ≠ PASS
- required_without_handler = FAIL
- required_skip = FAIL
- skip != pass
- OPEN → CLOSED forbidden
- all_four_passes_required = true
- no_dev_bypass_required = true

### PASS only if
context_verified AND handoff_verified AND CORE14 AND 4 passes AND counters all 0 AND evidence_complete AND final_clean_reaudit AND quality_dag_ok

### Caller must supply
- core_measures[CORE-01..14] = bool measured (default False)
- connectivity chain flags
- counters dict
- evidence_complete, final_clean_reaudit_passed, quality_dag_ok

## A3. Separación de planos (recuperado de MASTER / sistema)

```
CONTROL PLANE (decide BLOCK/PASS)
        ↓
EXECUTION PLANE (cognitive path)
        ↓
EXTERNAL APPLY (git commits) — fuera del runner
        ↓
REPOSITORY TRUTH + RE-AUDIT
```

## A4. CORE-01..14 nombres (recuperado de forensic_core / MASTER)

```
CORE-01 REQUIREMENT CLOSURE
CORE-02 SCOPE/DIFF CLOSURE
CORE-03 IMPLEMENTATION CLOSURE
CORE-04 ARCHITECTURE/BOUNDARY
CORE-05 DEPENDENCY CLOSURE
CORE-06 CONTRACT CLOSURE
CORE-07 REAL WIRING
CORE-08 BEHAVIOR/EDGE
CORE-09 TEST EFFECTIVENESS
CORE-10 REGRESSION/IMPACT
CORE-11 ERROR PATH CLOSURE
CORE-12 CODE QUALITY
CORE-13 REPOSITORY TRUTH
CORE-14 EVIDENCE/VERDICT
```

FC-01 … FC-13 (lista en código; resultados en state.fc_results).

## A5. CONNECTIVITY_CHAIN (recuperado)

```
DECLARED → REGISTERED → RESOLVED → INVOKED → EXECUTED
→ OUTPUT_CONSUMED → BEHAVIOR_VERIFIED
```

## A6. ClosureCounters — todos 0 para PASS (recuperado)

```
gaps, blocking_gaps, broken_connections, unexplained_orphans,
unreachable_required_paths, unresolved_dependencies, unverified_paths,
unverified_requirements, unverified_claims, pending_fixes,
new_gaps_after_fix, unexpected_changes
```

## A7. RULES del enforcer (recuperado)

```
claim_is_not_evidence: true
evidence_is_not_verification: true
verification_plus_evidence_for_pass: true
required_without_handler: FAIL
required_skip: FAIL
optional_skip: ALLOW
skip_equals_pass: false
open_to_closed_forbidden: true
all_four_passes_required: true
no_dev_bypass_required: true
```

## A8. Cuatro pasadas — condiciones (recuperado)

| Pass | Condición en código actual |
|------|----------------------------|
| STRUCTURE | CORE 01,02,03,04,05,06,13 todos True |
| CONNECTIVITY | chain all True AND CORE-07 True |
| BEHAVIOR | CORE 08,09,10,11 todos True |
| FORENSIC_CLOSURE | counters.all_zero AND evidence_complete AND final_clean_reaudit AND NOT claim_used_as_pass AND CORE-14 |

Fail en pass N marca siguientes como failed (`blocked by PASSn`).

## A9. evaluate — orden de decisión (recuperado)

1. require_context → BLOCK  
2. claim_used_as_pass → FAIL  
3. len(core_results)<14 → FAIL required_without_handler  
4. run_four_passes  
5. core_all_pass?  
6. four_passes_ok?  
7. counters.all_zero?  
8. evidence_complete ∧ final_clean_reaudit?  
9. quality_dag_ok?  
10. PASS  

## A10. API run_code_path — parámetros (recuperado)

| Param | Default | Efecto |
|-------|---------|--------|
| raw_input | required | texto misión |
| plan_steps | analyze/compile/validate/promote | cognitive |
| skill | None | compile opcional |
| mission_id | "" | o lock_id |
| context_verified | **False** | False → BLOCK |
| handoff_verified | **False** | False → BLOCK |
| core_measures | None | cada CORE ausente = False |
| connectivity | None | eslabones ausentes = False |
| counters | None | enteros de cierre |
| evidence_complete | False | debe True para PASS |
| final_clean_reaudit_passed | False | debe True para PASS |
| quality_dag_ok | False | debe True para PASS |

Retorno: `ok`, `mission_id`, `lock`, `cognitive`, `skill_compile`, `evidence`, `evidence_ok`, `forensic`, `llm_control="DENY"`, `verdict`  
**No existe** `allow_skip_post_verify` en esta versión.

## A11. GapRegistry (recuperado)

Campos: gap_id, task_id, mission_id, rule_id, severity, description, location, root_cause, required_fix, implemented_fix, verification, evidence, status, created_revision, fixed_revision, verified_revision, created_at  

Transiciones:
```
OPEN → FIXED
FIXED → VERIFIED | OPEN
VERIFIED → CLOSED | OPEN
CLOSED → (ninguna)
```
OPEN→CLOSED lanza ValueError. `note_new_gap_after_fix` añade gap e incrementa contador.

Loop: IMPLEMENT → AUDIT → CLASSIFY → FIX → RE-AUDIT → (¿new_gaps_after_fix?) → FINAL CLEAN RE-AUDIT → CLOSED

## A12. Catalog runtime C-* / K-* / A-* / R-* (recuperado)

C-CTX-01/02/03 · C-PLN-01/02 · C-CPY-01/02/03 · C-APL-01 · C-VRF-01/02/03 · C-WRD-01/02 · C-GAP-01  
K-MUL, K-TST, K-DEP, K-API, K-SEC, K-CON, K-SFX, K-DB, K-EXT, K-AI  
A-IMP, A-CYC, A-LOC · R-HEX, R-CPY  
ApplicabilityEngine · AGENT_CANNOT_DOWNGRADE_REQUIRED_CHECK · ChecklistSheriff · EvidenceVerifier · AGENT_CLAIM_IS_NOT_VERIFICATION

## A13. Trazabilidad documental (recuperado)

```
DOCUMENT → CONTEXT → REQUIREMENT → CODE → TEST → EVIDENCE → VERDICT
```
DOC_ONLY | CODE_ONLY | DOC_CODE_MISMATCH | CODE_TEST_MISMATCH | TEST_EVIDENCE_MISMATCH  
NO VERIFIED CONTEXT → NO PROGRAMMING / NO AUDIT

## A14. QualityDAG (recuperado)

FORMAT→LINT→TYPE→STATIC→UNIT→INTEGRATION→CONTRACT→SECURITY*→DEPS*→ARCH→BUILD→AUDIT  
required without handler = FAIL · required SKIP = FAIL · optional SKIP = ALLOW · SKIP ≠ PASS

## A15. Playbook operativo (recuperado)

1 ContextManifest 2 Applicability 3 COPY-FIRST 4 Plan+scope 5 Sheriff pre 6 Implement allowlist 7 Medir CORE 8 Connectivity 9 Counters 10 run_code_path 11 GapRegistry loop 12 Final reaudit 13 CLOSED  
CODE_EXISTS ≠ FEATURE_COMPLETE (CORE-03)

## A16. Qué es / qué no es el Wordflow de programming (recuperado)

Es: bloquea sin context/handoff · orquesta C-19 · CORE14 · 4 pasadas · 12 counters · prohíbe CLAIM→PASS, SKIP→PASS, OPEN→CLOSED, bypass REQUIRED · llm DENY · verdict BLOCK|FAIL|PASS  

No es: IDE · escritor autónomo del git tree · 500 gates uno-a-uno · auto-PASS del LLM

## A17. Fin Salida 1

Recuperado y **añadido al final** de este mismo archivo (sin borrar secciones 1–8): Global, Forensic REQUIRED, planos, CORE, connectivity, counters, RULES, 4-pass, evaluate, API, GapRegistry, catalog runtime, trazabilidad, QualityDAG, playbook, definición.

**Siguiente:** Salida 2 — recuperar lista de componentes (1–500 / E*) y **solo añadir** al final de este archivo.
