# COPY EXACT — commit faa6d95d597b87349ee1f8f1e5a45924b08859b7
# Origen: PIPELINE/ARQUITECTURA_WORDFLOW_PROGRAMMING_REAL.md (anexos A+B+C solamente)
# Método: copia determinista. No editar a mano.

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

## A3. Separación de planos
```
CONTROL PLANE (decide BLOCK/PASS)
        ↓
EXECUTION PLANE (cognitive path)
        ↓
EXTERNAL APPLY (git commits) — fuera del runner
        ↓
REPOSITORY TRUTH + RE-AUDIT
```

## A4. CORE-01..14 nombres
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

## A5. CONNECTIVITY_CHAIN
```
DECLARED → REGISTERED → RESOLVED → INVOKED → EXECUTED
→ OUTPUT_CONSUMED → BEHAVIOR_VERIFIED
```

## A6. ClosureCounters — todos 0 para PASS
```
gaps, blocking_gaps, broken_connections, unexplained_orphans,
unreachable_required_paths, unresolved_dependencies, unverified_paths,
unverified_requirements, unverified_claims, pending_fixes,
new_gaps_after_fix, unexpected_changes
```

## A7. RULES del enforcer
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

## A8. Cuatro pasadas — condiciones
| Pass | Condición en código actual |
|------|----------------------------|
| STRUCTURE | CORE 01,02,03,04,05,06,13 todos True |
| CONNECTIVITY | chain all True AND CORE-07 True |
| BEHAVIOR | CORE 08,09,10,11 todos True |
| FORENSIC_CLOSURE | counters.all_zero AND evidence_complete AND final_clean_reaudit AND NOT claim_used_as_pass AND CORE-14 |

## A9. evaluate — orden de decisión
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

## A10. API run_code_path — parámetros
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

## A11. GapRegistry
Campos: gap_id, task_id, mission_id, rule_id, severity, description, location, root_cause, required_fix, implemented_fix, verification, evidence, status, created_revision, fixed_revision, verified_revision, created_at  
Transiciones: OPEN→FIXED · FIXED→VERIFIED|OPEN · VERIFIED→CLOSED|OPEN · CLOSED→(ninguna)  
OPEN→CLOSED lanza ValueError. Loop: IMPLEMENT→AUDIT→CLASSIFY→FIX→RE-AUDIT→FINAL CLEAN→CLOSED

## A12. Catalog runtime C-* / K-* / A-* / R-*
C-CTX-01/02/03 · C-PLN-01/02 · C-CPY-01/02/03 · C-APL-01 · C-VRF-01/02/03 · C-WRD-01/02 · C-GAP-01  
K-MUL, K-TST, K-DEP, K-API, K-SEC, K-CON, K-SFX, K-DB, K-EXT, K-AI  
A-IMP, A-CYC, A-LOC · R-HEX, R-CPY  
ApplicabilityEngine · ChecklistSheriff · EvidenceVerifier · AGENT_CLAIM_IS_NOT_VERIFICATION

## A13. Trazabilidad documental
```
DOCUMENT → CONTEXT → REQUIREMENT → CODE → TEST → EVIDENCE → VERDICT
```
DOC_ONLY | CODE_ONLY | DOC_CODE_MISMATCH | CODE_TEST_MISMATCH | TEST_EVIDENCE_MISMATCH  
NO VERIFIED CONTEXT → NO PROGRAMMING / NO AUDIT

## A14. QualityDAG
FORMAT→LINT→TYPE→STATIC→UNIT→INTEGRATION→CONTRACT→SECURITY*→DEPS*→ARCH→BUILD→AUDIT  
required without handler = FAIL · required SKIP = FAIL · optional SKIP = ALLOW · SKIP ≠ PASS

## A15. Playbook operativo
1 ContextManifest 2 Applicability 3 COPY-FIRST 4 Plan+scope 5 Sheriff pre 6 Implement allowlist 7 Medir CORE 8 Connectivity 9 Counters 10 run_code_path 11 GapRegistry loop 12 Final reaudit 13 CLOSED  
CODE_EXISTS ≠ FEATURE_COMPLETE (CORE-03)

## A16. Qué es / qué no es el Wordflow de programming
Es: bloquea sin context/handoff · orquesta C-19 · CORE14 · 4 pasadas · 12 counters · prohíbe CLAIM→PASS, SKIP→PASS, OPEN→CLOSED, bypass REQUIRED · llm DENY · verdict BLOCK|FAIL|PASS  
No es: IDE · escritor autónomo del git tree · 500 gates uno-a-uno · auto-PASS del LLM

## A17. Fin Salida 1
Recuperado Global, Forensic REQUIRED, planos, CORE, connectivity, counters, RULES, 4-pass, evaluate, API, GapRegistry, catalog, trazabilidad, QualityDAG, playbook, definición.

---

## B1. COPIA — ARQUITECTURA_WORDFLOW_LIVE.md
TEAM YAIWES → CORE KERNEL → KERNEL EXTENSION → UNIFIED RUNTIME → COMMON INTERFACE · T0 DONE · Motors SEND/CALL/DOWNLOAD/KERNEL-EXT READY · Reception 3 repos · Próximo T2

## B2. COPIA — ARQUITECTURA_WORDFLOW_PROGRAMMING.md
Propósito run_code_path determinista · pre-gate COPY-FIRST · quality/goal/cognitive/evidence · post-verify VerdictAuthority · runner no escribe git · paths canónicos · límites explícitos · multi-instancia bootstrap_multi

## B3. COPIA — WORDFLOW_PROGRAMMING_FORENSIC_MAP.md
REAL: code_path_runner · quality_bar · goal_lock · cognitive · evidence · gates · copy_first · forensic_contract · verdict · catalogs · CI  
DOCUMENTADO: FORENSIC_CODE_AUDIT · 00_METODO · ADVANCED_ENGINEERING · GAPS  
AUSENTE histórico: SM global OPEN→CLOSED · FourPassController repo-wide · reception auto

## B4. Estado listas 500+
CURSOR_200 · CURSOR_300 · CURSOR_500_EXTRAS en PIPELINE/

---

## C1. FORENSIC_MAP gaps §3–20 (append)
Component Map · Connectivity Graph DECLARED…BEHAVIOR · State Machine · Context/Handoff · REQ traceability · Contracts/Rules/FourPass/Gaps · Deterministic vs LLM · Persistence · pipeline · matrix

## C2. PROGRAMMING paths canónicos
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

## C3. 04_ARQUITECTURA_3_MODOS — copia íntegra
NÚCLEO DETERMINISTA (Sheriff · Contratos · MYTHOS · Recovery · Witness · Fichas)
- **Función 1** Kernel OpenClaw (sustitución / poda)
- **Función 2** Capa de Control externa (zero-invasive)
- **Función 3** Extensión Kernel vía ABI (plug-in)

| Modo | ¿Modifica host? | Conexión | Uso |
|------|-----------------|----------|-----|
| F1 | Sí | Sustitución núcleo | OpenClaw→TEAM |
| F2 | No | Capa externa | Orquestadores existentes |
| F3 | No | ABI extensión | Plugins |

## C4. Cierre lote faa6 A+B+C
FORENSIC_MAP gaps · PROGRAMMING paths · 04_3_MODOS íntegro — copiados.

**Fuente commit:** faa6d95d597b87349ee1f8f1e5a45924b08859b7
