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

# RESTORE + ANEXO A + G + H — COPIA EXACTA blob 0f19cb2

**Método:** copy determinista del blob `0f19cb2ed0fdea7f727b73b1cbe8149bf1bfc764` (sha archivo `ef3357bbf96aca65321121b46f63a0be14cbf0f5`).

## A1 Global
Control plane: forensic_core · gap_registry · checklist_sheriff · applicability · evidence_verifier · verdict_authority · closure_engine  
Execution: code_path_runner BLOCK sin context; evaluate; llm DENY  
Regla: CLAIM ≠ EVIDENCE ≠ VERIFICATION ≠ PASS · NO CONTEXT → NO PROGRAMMING/AUDIT · REQUIRED no bypass

## A2 Forensic REQUIRED
CORE-01..14 · 4-pass · counters all 0 · evidence_complete · final_clean_reaudit · quality_dag_ok · claim_used_as_pass forbidden · OPEN→CLOSED forbidden

## A3–A16
Planos CONTROL→EXECUTION→EXTERNAL APPLY→RE-AUDIT  
CORE-01…CORE-14  
CONNECTIVITY DECLARED→…→BEHAVIOR_VERIFIED  
Counters: gaps, blocking_gaps, broken_connections, unexplained_orphans, unreachable_required_paths, unresolved_dependencies, unverified_paths, unverified_requirements, unverified_claims, pending_fixes, new_gaps_after_fix, unexpected_changes  
API context/handoff default False  
GapRegistry OPEN→FIXED→VERIFIED→CLOSED  
QualityDAG FORMAT→…→AUDIT · SKIP≠PASS  
Playbook Context→Applicability→COPY-FIRST→Plan→Sheriff→Implement→CORE→Connectivity→Counters→run_code_path→Gap loop→Final reaudit→CLOSED

## B1 LIVE / B2 PROGRAMMING / B3 FORENSIC_MAP / C1–C3 04_3_MODOS
(texto en anexos posteriores I si amplía; resumen operativo en 0f19cb2)

## G 48+00+43+CURSOR_200
G1 Loop→Gateway→Router · G2 método cadenas · G3 5 planos C-21…31 · G4 puntos 1–200

## H1 CURSOR_300 (201–500)
I–R bloques: context adv · multi-file · testing · refactor · quality · stack · collab · AI eval · platform · governance

## H2 CURSOR_500 E001–E500
E001–E050 Context · E051–E100 Plan · E101–E150 Apply · E151–E200 Verify · E201–E250 Agent · E251–E300 Git/PR · E301–E350 Arch · E351–E400 Quality · E401–E450 Stack · E451–E500 Wordflow ROI (E451 context default False … E500 frontmatter test)

## H3 GLOBAL / H4 FORENSIC_ENFORCEMENT
Control/Execution plane · PASS rules · caller must supply core_measures+connectivity+counters+evidence+reaudit+quality_dag

**RESTORE OK — blob 0f19cb2 en main. Siguiente parte: append I (LIVE+04+FORENSIC_MAP+G detalle) sin tocar este cuerpo.**

---

# ANEXO X — VERIFICACIÓN CRUZADA CODE vs §§1–8 (2026-08-18) — SOLO APPEND

**Regla:** no se borró el cuerpo histórico §§1–8 ni anexos A–H. Este anexo **corrige el AS-IS** donde el code actual supera el texto de §2/§5.

## X.1 Secuencia REAL actual de `run_code_path` (code main)

```
0. PolicySnapshot.freeze → policy en return
1. ContextManifest validate (si require_context_manifest)
2. VerdictAuthority.require_context → BLOCK
3. ExecutorPreImplementGate (si require_pre_gate | symbol+dest)
   → COPY-FIRST + ChecklistSheriff (si checklist)
4. apply_adapt + post_adapt ast.parse (si apply_adapt)
5. admit_or_reject (thresholds en wire_trace)
6. lock_goals
7. run_cognitive_loop + skill compile opt
8. evidence_packet + evidence_merge
9. QualityDAG.run + quality_handlers (FORMAT/STATIC/LINT/UNIT/ARCH smoke)
10. core_auto_measure + fc_auto_measure
11. GapRegistry (gaps de pre_gate/FC)
12. VerdictAuthority.decide(state) → forensic_core.evaluate
13. ClosureEngine.decide
14. return ok, verdict, policy, wire_trace.stage_ms, llm_control=DENY,
    c_status/s_status/t_status/u_status
```

## X.2 Matriz §5 ACTUALIZADA (code vs claim §5 viejo)

| Capacidad | §5 decía | Code main ahora |
|-----------|----------|-----------------|
| Context BLOCK | Sí | **Sí** |
| ContextManifest | No | **Sí** (opt require_context_manifest) |
| ChecklistSheriff | No | **Sí** (vía PreGate + checklist) |
| COPY-FIRST | No | **Sí** (PreGate + apply_adapt) |
| CORE-01..14 | Sí caller | **Sí** + core_auto_measure |
| 4 passes | Sí | **Sí** |
| Connectivity | Sí | **Sí** |
| Counters | Sí | **Sí** + gaps registry |
| FC-01..13 en evaluate | No | **Sí** si require_fc o fc_results; auto parcial FA-02 |
| GapRegistry | No | **Sí** instanciado en runner |
| ClosureEngine | No | **Sí** llamado en runner |
| QualityDAG execute | Solo flag | **Sí** run + handlers; TYPE/BUILD aún CI |
| VerdictAuthority | — | **Sí** decide() |
| PolicySnapshot | — | **Sí** |
| Unified pipeline | — | **Sí** run_unified |
| main_12 programming_path | — | **Sí** |
| full_pass attestation | — | **Sí** ci_attestation |
| llm DENY | Sí | **Sí** |

## X.3 Inventario STANDARDS faltante en §3 (append nombres)

| Archivo | Rol |
|---------|-----|
| path_resolve.py | Resolve paths WF/REPO |
| quality_handlers.py | DAG handlers + smoke UNIT/ARCH |
| fc_auto_measure.py | FC auto conservador |
| core_auto_measure.py | CORE auto conservador |
| evidence_merge.py | Dual evidence engine+standards |
| checklist_factory.py | dict → AgentChecklistClaim |
| adapt_imports.py | (ya en §3) |

## X.4 Inventario ENGINE faltante en §4.1

| Archivo | Notas |
|---------|-------|
| programming_kwargs.py | full_pass attested / minimal_block |
| programming_pipeline.py | **run_unified** (no solo helpers) |
| main_loop.py | programming_path / programming_full_pass |

## X.5 Deuda G1–G7 estado post-code

| ID | Estado |
|----|--------|
| G1 | Mitigado por este anexo + inventarios |
| G2 | **Cerrado en code** (Sheriff/COPY-FIRST cableados) |
| G3 | **Parcial cerrado** (evaluate FC + auto; resto caller) |
| G4 | Sigue doc-light en módulos mission_edges/scope_measure |
| G5 | Bridges siguen adyacentes; C-19 ya no solo bools |
| G6 | **Cerrado** evidence_merge |
| G7 | **Parcial** core_auto_measure existe; no finge 14×True |

## X.6 Gaps residuales honestos (no reabrir wire)

- TYPE / INTEGRATION / BUILD QualityDAG → CI `quality_dag_ok`
- FC-02/03/05/07/11/13 → caller/CI
- §2 texto histórico “NO ejecuta…” queda como **snapshot antiguo**; verdad operativa = **§X.1–X.2**

## X.7 Veredicto cruzado

```
CODE  ahead of ARCH §§2/5  →  ARCH actualizado por ANEXO X (append-only)
Wire gaps GC/GR/C/S/T/U/FA → CLOSED en code
PASS máquina §7           → sin cambio de ley
```

**Fin ANEXO X — verificación cruzada 2026-08-18.**
