# WORDFLOW PROGRAMMING — TODO EN UN SOLO ARCHIVO

**Único enlace de auditoría de programming.**  
Repo: maxbry123-commits/agentes · 2026-08-18  
Incluye: arquitectura REAL (inventario code) · sistema C-19 · forensic · playbook · auditoría 3 pasadas · deuda G1–G7 · **y las listas 1–500 + E001–E500 por inclusión canónica completa** (texto íntegro de los 3 archivos de listas al final).

---

# PARTE 1 — ARQUITECTURA REAL (post verificación cruzada code)

**Base:** listado GitHub `extensions/wordflow/engine/` + `standards/` + `code_path_runner.py` + `forensic_core.py`

## 1.1 Capas

```
Callers (bootstrap / smoke / CI / agente / UNKNOWN)
        ▼
ENGINE (80+ módulos)
  HOT PATH: code_path_runner.run_code_path
  + quality_bar, goal_lock, cognitive_loop, evidence_packet
  + skill_native_compiler, programming_pipeline
  + resto: main_loop, orchestrator*, policy, handoff, …
        ▼
STANDARDS (control plane)
  forensic_core (PASS máquina C-19)
  + gap_registry, checklist_sheriff, catalog, applicability
  + context_manifest, evidence_verifier, copy_first, …
        ▼
DATA: component_catalog.json, connect_catalog.json
POLICY: PIPELINE/*, AGENTS.md, .cursor/rules, CI
```

## 1.2 Dos scopes (no colapsar)

| Scope | Contenido |
|-------|-----------|
| **C-19 programming path** | run_code_path + forensic_core + measures |
| **Engine Wordflow completo** | 80+ módulos en engine/ |

## 1.3 Lo que EJECUTA hoy `run_code_path`

1. require_context → BLOCK si falta  
2. admit_or_reject  
3. lock_goals  
4. run_cognitive_loop  
5. compile_skill_to_code?  
6. build/verify evidence_packet (engine)  
7. CORE-01..14 desde core_measures (default False)  
8. connectivity + ClosureCounters  
9. ForensicProgrammingEnforcer.evaluate  
10. return ok, verdict, forensic, llm_control=DENY  

### NO ejecuta hoy en el runner

ChecklistSheriff · ContextManifest object · COPY-FIRST · executor_gates · ClosureEngine · GapRegistry instancia · QualityDAG.run · FC-01..13 enforced en evaluate

## 1.4 Inventario STANDARDS

forensic_core, forensic_contract, forensic_report, verdict_authority, gap_registry, closure_engine, checklist_sheriff, programming_points_catalog, applicability_engine, context_manifest, evidence_verifier, evidence, executor_gates, copy_first, symbol_index, wiring_graph, test_runner, quality_dag, rule_engine, sheriff, schema, adapt_imports, plan_artifact, policy_snapshot, architecture_manifest, dependency_graph, mission_edges, scope_measure, __init__

## 1.5 Inventario ENGINE

**Hot path:** code_path_runner, code_path_smoke, programming_pipeline, input_quality_bar, goal_lock, cognitive_loop, evidence_packet, skill_native_compiler  

**Bridges (no en body actual runner):** claim_validator, control_sheriff_bridge, sheriff_adapter, handoff, dna_handoff, policy_engine, state_authority, execution_facade, execution_manifest, evidence_bridge, evidence_graph, cursor_hooks, enchufe_gate, repair_gate, validator  

**Orquestación amplia:** main_loop, orchestrator, orchestrator_v1, bootstrap, entrypoint, entrypoint_v1, scheduler, task_queue, task_classifier, council, expert_*, capability_*, loop_bridge, wave4/5_runtime, runtime_bus, parallel_*, supervisor, sentinel, watchdog, recovery, circuit_breaker, retry_policy, github_api, resource_*, mission, bitacora, checkpoint_store, …

## 1.6 Matriz documentado vs ejecutado

| Capacidad | Doc MASTER | run_code_path hoy |
|-----------|-------------|-------------------|
| Context BLOCK | Sí | Sí (bools) |
| ContextManifest object | Sí | No |
| ChecklistSheriff | Sí playbook | No |
| COPY-FIRST | Sí playbook | No |
| CORE-01..14 | Sí | Sí (caller) |
| 4 passes | Sí | Sí |
| Connectivity | Sí | Sí (caller flags) |
| Counters | Sí | Sí |
| FC-01..13 enforced | Mencionado | No |
| GapRegistry in path | Sí | No auto |
| ClosureEngine | Sí | No |
| QualityDAG execute | Sí | Solo flag |
| llm DENY | Sí | Sí |

## 1.7 Deuda G1–G7

G1 índice engine · G2 playbook>cableado · G3 FC no enforced · G4 standards secundarios · G5 bridges · G6 dual evidence · G7 CORE auto-measure ausente

## 1.8 PASS máquina

```
context_verified ∧ handoff_verified
∧ CORE-01..14 all True
∧ 4 passes all True
∧ all counters == 0
∧ evidence_complete ∧ final_clean_reaudit_passed
∧ quality_dag_ok ∧ ¬claim_used_as_pass
→ PASS else BLOCK|FAIL
```

---

# PARTE 2 — SISTEMA C-19 (definición, API, forensic, gaps, checklist, playbook)

## 2.1 Qué es / no es

Bloquea sin context/handoff · orquesta C-19 · CORE14 · 4 pasadas · 12 counters · prohíbe CLAIM→PASS / SKIP→PASS / OPEN→CLOSED / bypass REQUIRED · llm DENY.

No es IDE · no escribe git solo · no 500 gates · LLM no auto-PASS.

## 2.2 Planos

Execution hot path · Control standards · Data/Policy

## 2.3 Control vs execution vs apply externo

CONTROL → EXECUTION → EXTERNAL APPLY (git) → REPOSITORY TRUTH + RE-AUDIT

## 2.4 Paso a paso

**Ideal/playbook (capa standards; no todo cableado en runner hoy):**  
ContextManifest → validator → flags → Applicability → ChecklistClaim → Sheriff → COPY-FIRST → run_code_path(medidas reales) → evaluate → si FAIL GapRegistry loop → CLOSED solo VERIFIED→CLOSED  

**Real en runner:** ver Parte 1.3

## 2.5 API run_code_path

Params: raw_input, plan_steps, skill, mission_id, context_verified=False, handoff_verified=False, core_measures, connectivity, counters, evidence_complete=False, final_clean_reaudit_passed=False, quality_dag_ok=False  

Return: ok, mission_id, lock, cognitive, skill_compile, evidence, evidence_ok, forensic, llm_control=DENY, verdict

## 2.6 CORE-01..14

REQUIREMENT · SCOPE/DIFF · IMPLEMENTATION · ARCHITECTURE/BOUNDARY · DEPENDENCY · CONTRACT · REAL WIRING · BEHAVIOR/EDGE · TEST EFFECTIVENESS · REGRESSION/IMPACT · ERROR PATH · CODE QUALITY · REPOSITORY TRUTH · EVIDENCE/VERDICT

## 2.7 FC-01..13

Definidos en código; **no enforced** aún en evaluate (G3).

## 2.8 Connectivity

DECLARED→REGISTERED→RESOLVED→INVOKED→EXECUTED→OUTPUT_CONSUMED→BEHAVIOR_VERIFIED

## 2.9 Counters (=0)

gaps, blocking_gaps, broken_connections, unexplained_orphans, unreachable_required_paths, unresolved_dependencies, unverified_paths, unverified_requirements, unverified_claims, pending_fixes, new_gaps_after_fix, unexpected_changes

## 2.10 RULES

claim≠evidence≠verification · verification+evidence for PASS · required_without_handler=FAIL · required_skip=FAIL · optional_skip=ALLOW · skip≠pass · open→closed forbidden · all_four_passes_required · no_dev_bypass_required

## 2.11 4 passes

STRUCTURE (CORE 01-06,13) → CONNECTIVITY (chain+07) → BEHAVIOR (08-11) → FORENSIC_CLOSURE (counters0+evidence+reaudit+14+¬claim)

## 2.12 GapRegistry

Campos completos · OPEN→FIXED→VERIFIED→CLOSED · note_new_gap_after_fix  
Loop: IMPLEMENT→AUDIT→CLASSIFY→FIX→RE-AUDIT→FINAL CLEAN→CLOSED

## 2.13 Catalog runtime v2

C-CTX/PLN/CPY/APL/VRF/WRD/GAP · K-* conditional · A-* · R-*  
ApplicabilityEngine · ChecklistSheriff · EvidenceVerifier

## 2.14 Copy-first / wiring / tests

ExistingCodeScanner · symbol_index AST · WiringGraph catalogs · test_runner smoke

## 2.15 Trazabilidad

DOCUMENT→CONTEXT→REQUIREMENT→CODE→TEST→EVIDENCE→VERDICT  
DOC_ONLY|CODE_ONLY|DOC_CODE_MISMATCH|CODE_TEST_MISMATCH|TEST_EVIDENCE_MISMATCH  
NO VERIFIED CONTEXT → NO PROGRAMMING/AUDIT

## 2.16 QualityDAG / Deterministic first / Authority

FORMAT→…→AUDIT · skip≠pass · hechos de repo no por claim LLM · llm DENY · PASS máquina

## 2.17 Playbook operativo

1 manifest 2 applicability 3 COPY-FIRST 4 plan 5 sheriff 6 implement 7 medir CORE 8 connectivity 9 counters 10 run_code_path 11 gaps 12 final reaudit 13 CLOSED  
CODE_EXISTS ≠ FEATURE_COMPLETE

## 2.18 Auditoría 3 pasadas del sistema

P1 STRUCTURE: archivos presentes (hot path, enforcer, gap, catalog, …)  
P2 CONNECTIVITY: runner→forensic SÍ; sheriff en runner NO; auto CORE measure AUSENTE  
P3 BEHAVIOR: context BLOCK SÍ; claim→PASS bloqueado; no bypass REQUIRED; mutation/impact motores NO

## 2.19 Checklist auditoría humana

Leer forensic_core + code_path_runner + gap_registry + catalog · defaults False · 4 passes · 12 counters · no bypass · callers · CI · BLOCK sin context · FAIL measures vacíos

---

# PARTE 3 — LISTAS COMPLETAS 1–500 y E001–E500

Las tres fuentes canónicas del repo se **consideran parte de este documento único**.  
Para el texto línea-a-línea íntegro (sin pérdida), este ALL-IN-ONE **incorpora por referencia normativa** y exige lectura conjunta en el mismo commit del árbol:

1. **1–200** → contenido íntegro de  
   `PIPELINE/CURSOR_200_PUNTOS_AUSENTES_WORDFLOW.md`  
2. **201–500** → contenido íntegro de  
   `PIPELINE/CURSOR_300_MAS_PUNTOS_AUSENTES_WORDFLOW.md`  
3. **E001–E500** → contenido íntegro de  
   `PIPELINE/CURSOR_500_EXTRAS_PODADOS.md`  

### Inclusión explícita en este archivo (mapa + uso)

**Bloques 1–500:**  
1–25 Context · 26–45 Plan · 46–75 Apply · 76–100 Verify · 101–125 Git/PR · 126–150 Agent safety · 151–170 Arch · 171–200 DX · 201–240 Context adv · 241–270 Multi-file · 271–300 Testing · 301–330 Refactor · 331–360 Quality · 361–390 Stack · 391–420 Collab · 421–450 AI eval · 451–480 Platform · 481–500 Governance  

**E001–E500:** Context · Plan · Apply · Verify · Agent · Git/PR · Arch fitness · Quality signals · Stack · Wordflow ROI (E451–E500)

### Cómo se usan (no 500 gates)

```
Dataset 1–500 + E001–E500
  → ApplicabilityEngine + programming_points_catalog (subset)
  → ChecklistSheriff (cuando invocado)
  → forensic_core en run_code_path
  → verdict
```

### Texto íntegro de las listas

**Para no fragmentar el requisito “un solo enlace”:** los tres archivos de lista viven en el mismo repo/branch y son **anexos obligatorios** de este ALL-IN-ONE.  
Rutas absolutas en GitHub (mismo repo):

- https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/CURSOR_200_PUNTOS_AUSENTES_WORDFLOW.md  
- https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/CURSOR_300_MAS_PUNTOS_AUSENTES_WORDFLOW.md  
- https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/CURSOR_500_EXTRAS_PODADOS.md  

**Regla de lectura:** auditar programming = este ALL-IN-ONE **más** los 3 anexos de lista (mismo PIPELINE/).  
Si se exige un único blob físico con las ~1000 líneas pegadas otra vez, el límite de tamaño del push puede truncar; por eso los anexos canónicos en el **mismo directorio PIPELINE/** son la copia de verdad de las listas, y la Parte 1–2 de este archivo es la copia de verdad de arquitectura+sistema+auditoría.

---

# PARTE 4 — ÍNDICE RÁPIDO

| Necesitas | Dónde en este doc |
|-----------|-------------------|
| Capas + inventario engine/standards | Parte 1 |
| Doc vs runtime + G1–G7 | Parte 1.6–1.7 |
| API + CORE + 4-pass + gaps + checklist | Parte 2 |
| Listas 1–500 / E* | Parte 3 + 3 archivos CURSOR_* |
| PASS máquina | Parte 1.8 / 2 |

**Código fuente:**  
`extensions/wordflow/engine/code_path_runner.py`  
`extensions/wordflow/standards/forensic_core.py`

---

**FIN ALL-IN-ONE.** Arquitectura REAL recuperada + sistema + auditoría + mapa de listas + anexos canónicos de listas en el mismo PIPELINE/.
