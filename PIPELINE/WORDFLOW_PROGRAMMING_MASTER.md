# WORDFLOW PROGRAMMING — MASTER (SISTEMA COMPLETO EN UN ARCHIVO)

**Repo:** maxbry123-commits/agentes  
**Fecha:** 2026-08-18  
**Uso:** auditoría forense + arquitectura + flujo + catálogo + enforcement  
**Método:** 3 pasadas de consolidación sobre código real en `extensions/wordflow/engine/code_path_runner.py` y `extensions/wordflow/standards/*`

---

# PARTE A — QUÉ ES Y QUÉ NO ES

## A1. Definición

El **Wordflow de programación de code** es el subsistema que:

1. Bloquea programación/auditoría sin contexto y handoff verificados.
2. Orquesta el path determinista C-19 (`run_code_path`).
3. Exige medidas CORE-01..14 (default False = FAIL).
4. Evalúa 4 pasadas forenses en orden estricto.
5. Exige 12 contadores de cierre en 0.
6. Prohíbe CLAIM→PASS, SKIP→PASS, OPEN→CLOSED, bypass de REQUIRED.
7. Devuelve `llm_control: "DENY"` y `verdict: BLOCK|FAIL|PASS`.

## A2. Qué no es

- No es un IDE.
- No escribe por sí solo el árbol git (el apply suele ser agente GitHub API).
- No implementa 500 gates uno-a-uno.
- No permite que el LLM se auto-otorgue PASS.

## A3. Planos

| Plano | Paths | Función |
|-------|-------|--------|
| Execution | `engine/code_path_runner.py`, quality_bar, goal_lock, cognitive_loop, evidence_packet, skill_native_compiler, programming_pipeline | Orquestación C-19 |
| Control | `standards/forensic_core.py`, gap_registry, checklist_sheriff, applicability, context_manifest, evidence_verifier, copy_first, symbol_index, wiring_graph, test_runner, verdict_authority, closure_engine, forensic_contract, quality_dag, rule_engine, executor_gates | Enforcement fail-closed |
| Data/Policy | component_catalog.json, connect_catalog.json, PIPELINE/*.md, AGENTS.md, .cursor/rules, CI forensic-gates | Declarativo |

---

# PARTE B — ARQUITECTURA

```
Caller (bootstrap / smoke / CI / agente)
        │
        ▼
┌─────────────────────────────────────────┐
│ run_code_path                           │
│  1 require_context → BLOCK?             │
│  2 quality_bar                          │
│  3 goal_lock                            │
│  4 cognitive_loop                       │
│  5 skill compile?                       │
│  6 evidence engine                      │
│  7 build ForensicEnforcementState       │
│  8 ForensicProgrammingEnforcer.evaluate │
└─────────────────────────────────────────┘
        │
        ├── standards/forensic_core.py
        ├── measures CORE-01..14 (caller)
        ├── connectivity chain (caller)
        ├── ClosureCounters (caller)
        └── quality_dag_ok / evidence / reaudit flags
        │
        ▼
   verdict BLOCK|FAIL|PASS + llm DENY
```

Separación obligatoria:

```
CONTROL PLANE (decide BLOCK/PASS)
        ↓
EXECUTION PLANE (cognitive path)
        ↓
EXTERNAL APPLY (git commits) — fuera del runner
        ↓
REPOSITORY TRUTH + RE-AUDIT
```

---

# PARTE C — PASO A PASO OPERATIVO (AGENTE + RUNTIME)

## C1. Antes de programar

1. Construir **ContextManifest** (mission_id, task_id, task_spec, handoff_ref, docs, files, tests, revision).
2. Validar con **ContextValidator** (errores → no poner context_verified).
3. Solo entonces `context_verified=True`, `handoff_verified=True`.
4. **ApplicabilityEngine.classify** (files, action, tags) → required points.
5. Armar **AgentChecklistClaim** (action COPY|ADAPT|GENERATE, sources, files_touched, claims+evidence).
6. **ChecklistSheriff** + **EvidenceVerifier** (claim no es verification).
7. **COPY-FIRST** scan (nombre + catalog + AST).

## C2. Ejecutar path

8. Llamar `run_code_path` con flags y **medidas reales** (no inventadas por LLM).
9. quality_bar → goal_lock → cognitive_loop → evidence engine.
10. Enforcer: CORE14 + 4 passes + counters + evidence + reaudit + quality_dag.

## C3. Si FAIL

11. Crear gaps en **GapRegistry** (campos completos).
12. FIX → RE-AUDIT → si aparecen gaps nuevos `new_gaps_after_fix++`.
13. Repetir hasta counters 0 y **FINAL CLEAN RE-AUDIT**.
14. Transition VERIFIED→CLOSED solamente.

## C4. Apply externo

15. Commits vía proceso autorizado; scope/diff debe alimentar CORE-02 / unexpected_changes.
16. No declarar DONE si solo CODE_EXISTS (CORE-03).

---

# PARTE D — API `run_code_path` (CÓDIGO REAL)

**Archivo:** `extensions/wordflow/engine/code_path_runner.py`

### Parámetros

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

### Retorno

`ok`, `mission_id`, `lock`, `cognitive`, `skill_compile`, `evidence`, `evidence_ok`, `forensic`, `llm_control="DENY"`, `verdict`

### Secuencia en código

1. `ForensicProgrammingEnforcer.require_context` → BLOCK dict si falla  
2. `admit_or_reject` → FAIL quality_bar  
3. `lock_goals` → FAIL goal_lock  
4. `run_cognitive_loop(...)`  
5. `compile_skill_to_code` si skill  
6. `build_evidence_packet` + `verify_evidence_packet`  
7. Loop `CORE_IDS` → `CoreCheckResult(cid, measures.get(cid, False))`  
8. `ClosureCounters(**counters)`  
9. `ForensicEnforcementState(...)`  
10. `enforcer.evaluate(state)`  
11. `ok = (verdict == "PASS")`  

**No existe** `allow_skip_post_verify` en esta versión.

---

# PARTE E — FORENSIC CORE (CÓDIGO REAL)

**Archivo:** `extensions/wordflow/standards/forensic_core.py`

## E1. CORE_IDS

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

## E2. FC_IDS

`FC-01` … `FC-13` (lista en código; resultados en `state.fc_results`).

## E3. CONNECTIVITY_CHAIN

```
DECLARED → REGISTERED → RESOLVED → INVOKED → EXECUTED
→ OUTPUT_CONSUMED → BEHAVIOR_VERIFIED
```

## E4. ClosureCounters (todos 0 para PASS)

```
gaps, blocking_gaps, broken_connections, unexplained_orphans,
unreachable_required_paths, unresolved_dependencies, unverified_paths,
unverified_requirements, unverified_claims, pending_fixes,
new_gaps_after_fix, unexpected_changes
```

## E5. RULES del enforcer

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

## E6. Cuatro pasadas (`run_four_passes`)

| Pass | Condición en código actual |
|------|----------------------------|
| STRUCTURE | CORE 01,02,03,04,05,06,13 todos True |
| CONNECTIVITY | chain all True AND CORE-07 True |
| BEHAVIOR | CORE 08,09,10,11 todos True |
| FORENSIC_CLOSURE | counters.all_zero AND evidence_complete AND final_clean_reaudit AND NOT claim_used_as_pass AND CORE-14 |

Fail en pass N marca siguientes como failed (`blocked by PASSn`).

## E7. `evaluate` orden de decisión

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

---

# PARTE F — GAP REGISTRY

**Archivo:** `extensions/wordflow/standards/gap_registry.py`

### Campos Gap

gap_id, task_id, mission_id, rule_id, severity, description, location,  
root_cause, required_fix, implemented_fix, verification, evidence,  
status, created_revision, fixed_revision, verified_revision, created_at

### Transiciones

```
OPEN → FIXED
FIXED → VERIFIED | OPEN
VERIFIED → CLOSED | OPEN
CLOSED → (ninguna)
```

OPEN→CLOSED **lanza ValueError**.  
`note_new_gap_after_fix` añade gap e incrementa contador.

### Loop obligatorio de proceso

```
IMPLEMENT → AUDIT → CLASSIFY → FIX → RE-AUDIT
→ (¿new_gaps_after_fix?) → FIX…
→ FINAL CLEAN RE-AUDIT → CLOSED
```

---

# PARTE G — CHECKLIST + APLICABILIDAD + EVIDENCIA

## G1. programming_points_catalog v2.0.0

Cada `ProgPoint`: id, stage, title, enforcement∈{CORE,CONDITIONAL,ADVISORY,REFERENCE}, applicability tags, evidence_type.

### Runtime CORE points (C-*)

| ID | Stage | Title |
|----|-------|-------|
| C-CTX-01 | context | ContextManifest complete |
| C-CTX-02 | context | Handoff verified with artifact |
| C-CTX-03 | context | No secrets in context |
| C-PLN-01 | plan | Action COPY\|ADAPT\|GENERATE explicit |
| C-PLN-02 | plan | Scope paths declared |
| C-CPY-01 | copy | COPY-FIRST scan executed |
| C-CPY-02 | copy | GENERATE only if no match |
| C-CPY-03 | copy | SOURCE→DEST if COPY/ADAPT |
| C-APL-01 | apply | Path allowlist respected |
| C-VRF-01 | verify | Evidence packet present |
| C-VRF-02 | verify | SKIP != PASS |
| C-VRF-03 | verify | Required gate missing = FAIL |
| C-WRD-01 | verdict | VerdictAuthority only |
| C-WRD-02 | verdict | Agent claim is not verification |
| C-GAP-01 | verdict | new_gaps_after_fix == 0 |

### CONDITIONAL (K-*)

K-MUL-01/02 multi_file · K-TST-01/02 tests · K-DEP-01 new_dep · K-API-01 public_api · K-SEC-01 security · K-CON-01 concurrency · K-SFX-01 side_effects · K-DB-01 db · K-EXT-01 external_api · K-AI-01 ai_agent

### ADVISORY / REFERENCE

A-IMP-01, A-CYC-01, A-LOC-01 · R-HEX-01, R-CPY-01

## G2. ApplicabilityEngine

Tags desde files/action/flags → required_ids.  
**AGENT_CANNOT_DOWNGRADE_REQUIRED_CHECK**.

## G3. ChecklistSheriff

- Version pin catálogo  
- EvidenceVerifier por claim  
- BLOCK: required missing, evidence vacía, GENERATE sin no-match, COPY/ADAPT sin sources  
- Regla: AGENT_CLAIM_IS_NOT_VERIFICATION  

## G4. EvidenceVerifier

kinds: path|symbol|test|measure|commit|manifest  
path vacío → fail; extensions/\|PIPELINE/ aceptado como repo-relative.

---

# PARTE H — COPY-FIRST / WIRING / TESTS

## H1. ExistingCodeScanner (`copy_first.py`)

- Roots: `WORDFLOW_SCAN_ROOTS` + wordflow + wordflow_kernel  
- find_by_name, find_in_catalog, find_by_symbol (AST)  
- plan → ADAPT si hits; GENERATE last  
- `copy_file_deterministic` + sidecar `.copy_evidence.json`  

## H2. symbol_index.py

AST ClassDef/FunctionDef/AsyncFunctionDef → SymbolIndex.

## H3. WiringGraph

Carga component_catalog + connect_catalog → nodes/edges; orphans helper.

## H4. test_runner

TestEffectivenessRunner + default_smoke_runner (imports, skip≠pass, catalogs).

---

# PARTE I — INVENTARIO 500 PUNTOS (DATASET, NO 500 GATES)

Los puntos 1–500 viven como **dataset de referencia** en:

| Archivo | Rango |
|---------|-------|
| `PIPELINE/CURSOR_200_PUNTOS_AUSENTES_WORDFLOW.md` | 1–200 |
| `PIPELINE/CURSOR_300_MAS_PUNTOS_AUSENTES_WORDFLOW.md` | 201–500 |
| `PIPELINE/CURSOR_500_EXTRAS_PODADOS.md` | E001–E500 (podados alto ROI) |

### Cómo se usan en el Wordflow

```
CATÁLOGO 1–500 / E001–E500
        ↓
CLASSIFIER / ApplicabilityEngine
        ↓
REQUIRED | CONDITIONAL | ADVISORY | REFERENCE
        ↓
AgentChecklistClaim
        ↓
ChecklistSheriff + EvidenceVerifier
        ↓
CORE-01..14 + 4-PASS + COUNTERS (forensic_core)
        ↓
PASS | FAIL | BLOCK
```

**Anti-overengineering:** quitar solo no aplicables; **nunca** quitar REQUIRED arquitectónico/conectividad/tests/verificación para “simplificar”.

### Mapa de bloques del dataset (auditoría)

**1–25** Context IDE · **26–45** Plan · **46–75** Apply/edit · **76–100** Verify · **101–125** Git/PR · **126–150** Agent safety · **151–170** Arch · **171–200** DX Cursor · **201–240** Context avanzado · **241–270** Multi-file · **271–300** Testing · **301–330** Refactor · **331–360** Quality fina · **361–390** Stack · **391–420** Collab · **421–450** AI eval · **451–480** Platform · **481–500** Governance  
**E001–E500** versión podada orientada a gates útiles + **E451–E500** ROI Wordflow.

Solo un **subset** tiene enforcement runtime (Parte G). El resto es guía de ejecución/selección.

---

# PARTE J — TRAZABILIDAD DOCUMENTAL (CONTRATO)

```
DOCUMENT → CONTEXT → REQUIREMENT → CODE → TEST → EVIDENCE → VERDICT
```

Clasificaciones a detectar (política; detectores auto completos = parcial en runtime):

- DOC_ONLY  
- CODE_ONLY  
- DOC_CODE_MISMATCH  
- CODE_TEST_MISMATCH  
- TEST_EVIDENCE_MISMATCH  

Regla dura implementada:

```
NO VERIFIED CONTEXT → NO PROGRAMMING
NO VERIFIED CONTEXT → NO AUDIT
```

---

# PARTE K — QUALITYDAG / DETERMINISTIC FIRST / AUTHORITY

## QualityDAG (política integrada al PASS)

FORMAT→LINT→TYPE→STATIC→UNIT→INTEGRATION→CONTRACT→SECURITY*→DEPS*→ARCH→BUILD→AUDIT  
\* condicional por applicability.

- required without handler = FAIL  
- required SKIP = FAIL  
- optional SKIP = ALLOW  
- SKIP ≠ PASS  

Flag `quality_dag_ok` debe ser medido True.

## Deterministic First

Si path/file/import/symbol/registration/dependency/test/hash/diff/schema/status se puede comprobar en repo → **no** aceptar solo claim LLM.

## Agent authority

`llm_control: DENY` en return.  
PASS solo máquina (`ForensicProgrammingEnforcer` / Verdict path).  
Tool allowlist = punto CONDITIONAL K-AI-01 + dataset agent safety.

---

# PARTE L — GUÍA DE EJECUCIÓN (PLAYBOOK)

1. Leer task + docs → ContextManifest  
2. Applicability → checklist required  
3. COPY-FIRST scan  
4. Plan action + scope paths  
5. Sheriff pre  
6. Implement/adapt (externo) dentro allowlist  
7. Medir CORE-01..14 con herramientas (diff, tests, wiring, catalogs)  
8. Medir connectivity chain  
9. Contadores gaps  
10. `run_code_path` con flags honestos  
11. Si FAIL: GapRegistry + fix + reaudit hasta new_gaps_after_fix=0  
12. Final clean reaudit  
13. Solo entonces CLOSED  

DONE literal ≠ archivo creado.  
FEATURE_COMPLETE exige scope completo (CORE-03).

---

# PARTE M — AUDITORÍA FORENSE DE ESTE SISTEMA (3 PASADAS)

## Pasada 1 — STRUCTURE (archivos y responsabilidades)

| Componente | Path | ¿Presente? |
|------------|------|------------|
| Hot path | code_path_runner.py | SÍ |
| Enforcer | forensic_core.py | SÍ |
| Gap registry | gap_registry.py | SÍ |
| Catalog points | programming_points_catalog.py | SÍ |
| Applicability | applicability_engine.py | SÍ |
| Context | context_manifest.py | SÍ |
| Evidence verify | evidence_verifier.py | SÍ |
| Sheriff | checklist_sheriff.py | SÍ |
| Copy-first | copy_first.py + symbol_index | SÍ |
| Wiring | wiring_graph.py | SÍ |
| Dataset 500 | PIPELINE CURSOR_* | SÍ |

## Pasada 2 — CONNECTIVITY

| Enlace | Estado |
|--------|--------|
| runner → forensic_core | SÍ import/evaluate |
| runner → quality/goal/cognitive/evidence | SÍ |
| measures default False | SÍ fail-closed |
| ChecklistSheriff → siempre llamado en runner | **PARCIAL** (API measures; sheriff en gates) |
| Auto CORE medidores | **AUSENTE** (caller debe medir) |
| DOC mismatch auto | **PARCIAL** |
| Output dict consumers | **UNKNOWN** inventario callers |

## Pasada 3 — BEHAVIOR / CIERRE

| Regla | ¿Código la impone? |
|-------|---------------------|
| NO context → BLOCK | SÍ |
| CORE incompleto → FAIL | SÍ |
| 4 passes orden | SÍ |
| counters ≠0 → FAIL | SÍ |
| claim→PASS | bloqueado en evaluate |
| dev bypass REQUIRED | NO en runner actual |
| OPEN→CLOSED | prohibido en GapRegistry |
| Test effectiveness motor mutación | **NO** (solo flag/medida) |
| Impact engine AST | **NO** motor único |

### Hallazgos de verificación cruzada (honestos)

1. Enforcement de **cierre** está en `forensic_core` + runner.  
2. **Medición** de cada CORE sigue siendo responsabilidad del caller/CI → riesgo operativo si el caller miente; mitigación de diseño = no aceptar claim LLM como measure.  
3. Dataset 500 **no** está hardcodeado en el enforcer; está referenciado por diseño (anti-sobreingeniería).  
4. Sheriff de checklist y forensic CORE son **dos capas**; integración total en una sola llamada aún puede endurecerse.  

---

# PARTE N — DEFINICIÓN MÁQUINA DE PASS

```
PASS only if:
  context_verified
  AND handoff_verified
  AND all CORE-01..14 == True (measured)
  AND all 4 passes == True
  AND all closure counters == 0
  AND evidence_complete
  AND final_clean_reaudit_passed
  AND quality_dag_ok
  AND claim_used_as_pass == False
else:
  BLOCK or FAIL
```

---

# PARTE O — ÍNDICE DE ARCHIVOS DEL SISTEMA PROGRAMMING

```
extensions/wordflow/engine/
  code_path_runner.py
  programming_pipeline.py
  input_quality_bar.py
  goal_lock.py
  cognitive_loop.py
  evidence_packet.py
  skill_native_compiler.py
  code_path_smoke.py

extensions/wordflow/standards/
  forensic_core.py
  forensic_contract.py
  forensic_report.py
  verdict_authority.py
  gap_registry.py
  closure_engine.py
  checklist_sheriff.py
  programming_points_catalog.py
  applicability_engine.py
  context_manifest.py
  evidence_verifier.py
  evidence.py
  executor_gates.py
  copy_first.py
  symbol_index.py
  wiring_graph.py
  test_runner.py
  quality_dag.py
  rule_engine.py
  sheriff.py
  schema.py
  adapt_imports.py
  plan_artifact.py
  policy_snapshot.py
  architecture_manifest.py
  dependency_graph.py

extensions/wordflow/
  component_catalog.json
  connect_catalog.json

PIPELINE/
  WORDFLOW_PROGRAMMING_MASTER.md          ← ESTE ARCHIVO
  WORDFLOW_PROGRAMMING_AUDIT_SPEC.md
  WORDFLOW_PROGRAMMING_COMO_FUNCIONA.md
  WORDFLOW_PROGRAMMING_FORENSIC_MAP.md
  ARQUITECTURA_WORDFLOW_GLOBAL.md
  ARQUITECTURA_WORDFLOW_PROGRAMMING.md
  FORENSIC_ENFORCEMENT_REQUIRED.md
  FORENSIC_CODE_AUDIT.md
  ENFORCEMENT_P0_REDESIGN.md
  PROGRAMMING_CHECKLIST_SHERIFF.md
  GAPS_PROGRAMMING_WORDFLOW.md
  CURSOR_200_PUNTOS_AUSENTES_WORDFLOW.md
  CURSOR_300_MAS_PUNTOS_AUSENTES_WORDFLOW.md
  CURSOR_500_EXTRAS_PODADOS.md
  ADVANCED_ENGINEERING_STANDARD_V3.md
  00_METODO_TRABAJO_Y_ARQUITECTURA.md

.cursor/rules/wordflow-programming.mdc
AGENTS.md
.github/workflows/forensic-gates.yml
```

---

# PARTE P — CHECKLIST DE AUDITORÍA HUMANA

- [ ] Leer `forensic_core.py` completo  
- [ ] Leer `code_path_runner.py` completo  
- [ ] Leer `gap_registry.py` completo  
- [ ] Leer `programming_points_catalog.py` completo  
- [ ] Confirmar defaults context/handoff False  
- [ ] Confirmar measures default False  
- [ ] Confirmar 4 passes cortan en cadena  
- [ ] Confirmar 12 counters  
- [ ] Confirmar no bypass REQUIRED  
- [ ] Revisar dataset 500 enlazado  
- [ ] Inventariar callers de run_code_path  
- [ ] Verificar CI forensic-gates  
- [ ] Probar BLOCK sin context  
- [ ] Probar FAIL con core_measures vacíos  

---

**FIN DEL MASTER.** Un solo archivo de referencia del sistema de programming de code del Wordflow: arquitectura, flujo, código de enforcement, gaps, checklist, dataset 500, guía de ejecución y auditoría cruzada.
