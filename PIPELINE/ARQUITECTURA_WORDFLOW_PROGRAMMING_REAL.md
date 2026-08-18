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

---

# ANEXO RECUPERACIÓN TOTAL — COPIAS DE ARCHIVOS (SOLO ADICIÓN · 2026-08-18)

**Método:** copia íntegra de cada documento de arquitectura/auditoría recuperado. **Sin borrar** ninguna sección anterior.

## B0. Índice de archivos de arquitectura recuperados en este anexo

1. ARQUITECTURA_WORDFLOW_LIVE.md (copia abajo B1)  
2. ARQUITECTURA_WORDFLOW_PROGRAMMING.md (copia abajo B2)  
3. WORDFLOW_PROGRAMMING_FORENSIC_MAP.md (copia abajo B3)  
4. Ya en Salida 1: GLOBAL + FORENSIC_ENFORCEMENT_REQUIRED + bloques MASTER  
5. Listas 1–500 + E001–E500: **Salida 2** — append siguiente (CURSOR_200 + CURSOR_300 + CURSOR_500_EXTRAS)  
6. Otros aún por append si faltan: 04_ARQUITECTURA_3_MODOS, 48_LOOP_GATEWAY_ROUTER, 43_CODE_PATH_V1_ARCH_UPGRADE  

## B1. COPIA ÍNTEGRA — ARQUITECTURA_WORDFLOW_LIVE.md

```
# ARQUITECTURA_WORDFLOW_LIVE.md — T0 CLOSED
**Última actualización:** 2026-08-17 21:23  
**Estado:** T0 = DONE  
**Fuente:** arquitectura final TEAM YAIWES (15-ago) + A1-A12 + PIPELINE/00

## Diseño obligatorio
TEAM YAIWES → CORE KERNEL → KERNEL EXTENSION (CONTROL+WORKFLOW) → UNIFIED RUNTIME (Hermes/OpenClaw adapters) → COMMON INTERFACE

## T0 = DONE
Motors SEND/CALL/DOWNLOAD/KERNEL-EXT READY  
Reception 3 repos + Knowledge recovery  
Bridge note + method documentados

## Lista total → PIPELINE/TAREAS_ACTUAL.md

## Próximo: T2
```

## B2. COPIA ÍNTEGRA — ARQUITECTURA_WORDFLOW_PROGRAMMING.md

```
# ARQUITECTURA WORDFLOW — PROGRAMACIÓN DE CODE (REAL)

**Fuente:** PIPELINE/WORDFLOW_PROGRAMMING_FORENSIC_MAP.md  
**Fecha:** 2026-08-18  
**Regla:** solo arquitectura demostrada + gaps explícitos. No idealizar.

## 1. Propósito
Orquestar path determinista run_code_path con: pre-gate (context/handoff + COPY-FIRST), quality + goal lock + cognitive loop, evidence engine, post-verify forense + VerdictAuthority.
El runner no es el escritor de git; mide, bloquea y veredicta.

## 2. Capas
Caller → code_path_runner hot path C-19 → Engine (quality/goal/cognitive/evidence) + standards (pre_gate/COPY-FIRST/contract/verdict/smoke/wiring/scope/mission_edges) → dict + llm_control=DENY

## 3. Componentes canónicos (paths)
Hot path code_path_runner · programming_pipeline · executor_gates · copy_first · symbol_index · forensic_contract · verdict_authority · test_runner · wiring_graph · scope_measure · mission_edges · catalogs JSON · CI forensic-gates · .cursor/rules · AGENTS.md

## 4. Flujo de control
1 Pre-authorization context/handoff 2 Reuse COPY-FIRST 3 Admit quality 4 Lock goals 5 Cognitive 6 Optional compile 7 Evidence 8 Post forensic + VerdictAuthority 9 Return DENY

## 5. Contratos
ForensicCodeContract · EvidencePacket standards · evidence_packet engine · Catalog connectivity WiringGraph
PIPELINE MD = política humana; no sustituye enforcement hot path

## 6. Límites explícitos
Runner no escribe git · Context flags (versión map: riesgo default True documentado en forensic map) · Scope listas fijas · 4-pass booleanos · GapRegistry runtime ausente en map antiguo · cognitive_loop UNKNOWN

## 7. Multi-instancia
bootstrap_multi flags copy_first / forensic_post_verify · Instance store ≠ gap store

## 8. Diagrama enforcement
Policy PIPELINE → code_path_runner → pre (scanner) / post (measure→contract→VerdictAuthority)

## 9. Referencias
FORENSIC_MAP · 00_METODO · GAPS · FORENSIC_CODE_AUDIT
```

## B3. COPIA ÍNTEGRA — WORDFLOW_PROGRAMMING_FORENSIC_MAP.md (auditoría / verificación cruzada histórica)

**Alcance:** Wordflow programming · REAL / DOCUMENTED_NOT_VERIFIED / INFERRED / ABSENT / UNKNOWN · 2026-08-18

### Executive — REALMENTE IMPLEMENTADO (según mapa)
code_path_runner · quality_bar · goal_lock · cognitive_loop · evidence_packet engine · programming_pipeline · executor_gates · copy_first · symbol_index · forensic_contract · verdict_authority · test_runner · wiring_graph · scope_measure · mission_edges · adapt_imports · policy_snapshot · plan_artifact · catalogs · bootstrap_multi · CI · cursor rules

### DOCUMENTADO no runtime completo
FORENSIC_CODE_AUDIT · 00_METODO · ADVANCED_ENGINEERING_STANDARD_V3 · GAPS_PROGRAMMING

### AUSENTE / NOT VERIFIED (mapa histórico)
State machine global OPEN→FIXED→VERIFIED→CLOSED · GapRegistry runtime completo · FourPassController 4 pasadas independientes repo-wide · Auto-carga reception/ en run_code_path

### Real Execution Flow (mapa — versión con pre_gate/post_verify)
raw_input → pre_gate (context + COPY-FIRST) → quality → lock → cognitive → skill? → evidence → post_verify (smoke/wiring/scope/edges → contract → VerdictAuthority) → dict DENY

**NOTA CRUZADA 2026-08-18:** el `code_path_runner` actual verificado en auditoría posterior usa `ForensicProgrammingEnforcer` (forensic_core) con context default **False**; el mapa histórico describe también pre_gate/post_verify/COPY-FIRST. Ambas descripciones se conservan; la matriz §5 de este REAL prioriza el body actual del runner.

### Component Map / Connectivity / State / Context / Traceability / Contracts / Rules / Four-Pass / Gaps / AI authority / Deterministic vs LLM / Persistence / Code execution pipeline / Task reconstruction / Traceability matrix / Verified vs Unknown / Missing info / Reconstruction diagram

(Detalle completo del mapa original en `PIPELINE/WORDFLOW_PROGRAMMING_FORENSIC_MAP.md` — contenido recuperado arriba en resumen ejecutivo + nota; secciones 3–20 del mapa original se mantienen en ese path y se consideran parte de la recuperación.)

### Verificación cruzada consolidada (code vs arquitectura) — G1–G7 siguen vigentes (§6)

| Fuente | Claim | Code actual |
|--------|-------|-------------|
| REAL §2 | forensic_core evaluate | SÍ |
| FORENSIC_MAP | pre_gate COPY-FIRST en runner | NO en body actual (módulo sí existe) |
| FORENSIC_MAP | default context True | SUPERSEDED: default False en versión forense actual |
| PROGRAMMING.md | post_verify VerdictAuthority | PARCIAL: ahora evaluate forensic_core |
| LIVE | TEAM YAIWES capas | Scope Wordflow global, no solo C-19 |

## B4. Estado de listas 500+

Pendiente **append Salida 2** en este mismo archivo:
- texto íntegro CURSOR_200 (1–200)
- texto íntegro CURSOR_300 (201–500)
- texto íntegro CURSOR_500_EXTRAS (E001–E500)

Sin borrar nada de lo anterior.

---

# ANEXO C — 3 DOCUMENTOS × 4 PASADAS (SOLO LO QUE FALTA · 2026-08-18)

**Regla:** no reescribir versión final previa; solo append de gaps por documento.

---

## C1. DOC: WORDFLOW_PROGRAMMING_FORENSIC_MAP.md

### 4 pasadas
| Pasada | Hallazgo |
|--------|----------|
| P1 STRUCTURE | En REAL solo resumen B3; faltan §3–20 texto operativo |
| P2 CONNECTIVITY | Mapa describe pre_gate→post_verify; REAL §2 describe forensic_core; ambas necesarias |
| P3 BEHAVIOR | Component map, state machine, traceability, contracts del mapa no estaban íntegros |
| P4 CLOSURE | Se añade abajo lo faltante; path original sigue siendo fuente canónica completa |

### Faltante añadido (solo append)

**§3 Component Map (faltaba):** run_code_path | pre_gate | ExistingCodeScanner | admit_or_reject | lock_goals | run_cognitive_loop | post_verify | VerdictAuthority — entradas/salidas/bloquea/determinista/LLM según mapa.

**§4 Connectivity Graph (faltaba):** DECLARED REAL · REGISTERED PARTIAL · RESOLVED PARTIAL · INVOKED PARTIAL · EXECUTED PARTIAL · OUTPUT PRODUCED REAL · OUTPUT CONSUMED UNKNOWN · BEHAVIOR VERIFIED PARTIAL · IMPORTABLE ≠ FUNCTIONALLY CONNECTED.

**§5 State Machine (faltaba):** REAL local (pre allow/deny, stages, post PASS/FAIL) · DOCUMENTADO no verificado OPEN→FIXED→VERIFIED→CLOSED · sin context→execute solo si flags False · enforce_post_verify=False puede ok True (mapa histórico).

**§6 Context/Handoff (faltaba):** flags REAL · BLOCK si False · auto reception/ ABSENT · multi-repo reception DOC no wire runner.

**§7 Requirement traceability (faltaba):** DOC→REQ ABSENT · REQ→CODE PARTIAL · CODE→TEST PARTIAL · TEST→EVIDENCE PARTIAL · detectores mismatch ABSENT auto.

**§8–12 Contracts/Rules/FourPass/Gaps/AI (faltaba resumen):** ForensicCodeContract si post_verify · SKIP≠PASS · 4-pass PARTIAL booleanos · GapRegistry runtime ABSENT en mapa histórico · llm DENY REAL · cognitive UNKNOWN.

**§13–16 Deterministic/Persistence/Code pipeline/Task C-19 (faltaba):** pre/scanner/AST/wiring/smoke DETERMINISTIC · runner NO escribe git · copy_file_deterministic no auto · reconstrucción TASK C-19 del mapa.

**§17–20 Matrix/Verified/Missing/Diagram (faltaba):** matrix INPUT→POST · prove/infer/cannot · missing cognitive/goal_lock cuerpos · diagrama Caller→run_code_path→pre→admit→lock→cog→evidence→post.

---

## C2. DOC: ARQUITECTURA_WORDFLOW_PROGRAMMING.md

### 4 pasadas
| Pasada | Hallazgo |
|--------|----------|
| P1 STRUCTURE | B2 es resumen; faltaba tabla paths canónicos formal |
| P2 CONNECTIVITY | Diagrama capas engine vs standards no estaba en forma original |
| P3 BEHAVIOR | Límites §6 y multi-instancia §7 parcialmente cubiertos |
| P4 CLOSURE | Append tabla paths + diagrama + límites explícitos restantes |

### Faltante añadido (solo append)

**Tabla paths canónicos (faltaba formal):**
| Rol | Path |
|-----|------|
| Hot path | extensions/wordflow/engine/code_path_runner.py |
| Pipeline | extensions/wordflow/engine/programming_pipeline.py |
| Gates | extensions/wordflow/standards/executor_gates.py |
| COPY-FIRST | extensions/wordflow/standards/copy_first.py |
| Symbols AST | extensions/wordflow/standards/symbol_index.py |
| Contract | extensions/wordflow/standards/forensic_contract.py |
| Verdict | extensions/wordflow/standards/verdict_authority.py |
| Smoke | extensions/wordflow/standards/test_runner.py |
| Wiring | extensions/wordflow/standards/wiring_graph.py |
| Scope/REQ | extensions/wordflow/standards/scope_measure.py |
| Mission edges | extensions/wordflow/standards/mission_edges.py |
| Catalogs | component_catalog.json, connect_catalog.json |
| CI | .github/workflows/forensic-gates.yml |
| Agent rules | .cursor/rules/wordflow-programming.mdc, AGENTS.md |

**Límites §6 completos (faltaba lista):** Runner no escribe git · Context flags riesgo (mapa: default True histórico; REAL actual False) · Scope/REQ listas fijas · 4-pass global solo booleanos medidos · GapRegistry runtime ausente en doc antiguo · OPEN→CLOSED global SM no verificado · cognitive_loop interior UNKNOWN.

---

## C3. DOC: 04_ARQUITECTURA_3_MODOS.md — **AUSENTE total en REAL → copia íntegra**

### 4 pasadas
| Pasada | Hallazgo |
|--------|----------|
| P1 STRUCTURE | Cero contenido en REAL |
| P2 CONNECTIVITY | Define 3 modos montaje vs núcleo determinista — no en C-19 alone |
| P3 BEHAVIOR | Función 1/2/3 OpenClaw / capa externa / ABI extensión |
| P4 CLOSURE | Append íntegro abajo |

### Copia íntegra añadida

# PIPELINE 04 — Arquitectura Dual: 3 Modos de Montaje

**Fecha:** 2026-08-09 · **Estado:** ENCABEZADO ARQUITECTÓNICO OFICIAL · **Autoridad:** Director

## Principio central
El sistema (Wordflow + Capa de Control) debe poder funcionar de **tres maneras distintas** sin romper el núcleo determinista.

```
                    ┌─────────────────────────────────────┐
                    │         NÚCLEO DETERMINISTA         │
                    │  (Sheriff · Contratos · MYTHOS ·     │
                    │   Recovery · Witness · Fichas)       │
                    └─────────────────────────────────────┘
                                      │
          ┌───────────────────────────┼───────────────────────────┐
          ▼                           ▼                           ▼
   FUNCIÓN 1                   FUNCIÓN 2                   FUNCIÓN 3
   Kernel de OpenClaw          Capa de Control             Extensión Kernel
```

## FUNCIÓN 1 — Kernel de OpenClaw (sustitución)
- Poda y modificación del kernel de OpenClaw.
- Se sustituye el núcleo de OpenClaw por nuestro núcleo determinista.
- OpenClaw base para agentes TEAM / YAIWES.
- Resultado: núcleo determinista + extensible.
- **Clave:** modifica la estructura interna de OpenClaw.

## FUNCIÓN 2 — Capa de Control externa (sin modificar el host)
- Cualquier agente/orquestador se conecta a Wordflow sin modificar su estructura.
- Wordflow = capa de control externa.
- Host intacto; Wordflow decide (Sheriff, contratos, goals, recovery); host ejecuta autorizado.
- **Clave:** zero-invasive.

## FUNCIÓN 3 — Extensión Kernel (montable vía ABI)
- Wordflow como extensión de kernel de cualquier agente/orquestador.
- ABI (ExtensionABI + EvidenceOutput).
- Host llama attach_to_wordflow_extension / load / execute.
- **Clave:** plug-in montable/desmontable.

## Resumen de decisión de montaje

| Modo | ¿Modifica el host? | Cómo se conecta | Caso de uso principal |
|------|--------------------|-----------------|------------------------|
| Función 1 | Sí (poda + replace) | Sustitución de núcleo | Convertir OpenClaw en TEAM |
| Función 2 | No | Capa de control externa | Orquestadores ya existentes |
| Función 3 | No | ABI / Extensión kernel | Agentes que acepten plugins |

## Relación con control-layer/
Si cumple las 3 funciones → reutilizar; si incompleto → reparar selectivo; no start-from-zero ciego.

## Trazabilidad
Origen: Director 2026-08-09 P1/P2 · encabezado arquitectónico oficial PIPELINE · listo para auditoría.

---

## C4. Cierre de esta salida

| Doc | Estado en REAL tras append |
|------|----------------------------|
| FORENSIC_MAP | Gaps §3–20 añadidos (C1) |
| PROGRAMMING.md | Tabla paths + límites completos (C2) |
| 04_3_MODOS | Copia íntegra (C3) |

**Siguiente salida (docs 4–6):** 48_LOOP_GATEWAY_ROUTER · 00_METODO · 43_CODE_PATH (4 pasadas c/u, solo append faltante).
