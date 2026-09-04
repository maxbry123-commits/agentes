# WORDFLOW PROGRAMMING FORENSIC MAP

**Repo:** maxbry123-commits/agentes  
**Alcance:** Wordflow de programación de code  
**Regla:** REAL / DOCUMENTED_NOT_VERIFIED / INFERRED / ABSENT / UNKNOWN  
**Fecha:** 2026-08-18  

Objetivo: especificación operacional del flujo REAL. No rediseño. No idealización.

---

## 1. Executive Architecture

### REALMENTE IMPLEMENTADO

| Componente | Path |
|------------|------|
| Hot path | `extensions/wordflow/engine/code_path_runner.py` (`run_code_path`) |
| Quality bar | `extensions/wordflow/engine/input_quality_bar.py` |
| Goal lock | `extensions/wordflow/engine/goal_lock.py` |
| Cognitive loop | `extensions/wordflow/engine/cognitive_loop.py` |
| Evidence (engine) | `extensions/wordflow/engine/evidence_packet.py` |
| Programming pipeline | `extensions/wordflow/engine/programming_pipeline.py` |
| Pre/Post gates | `extensions/wordflow/standards/executor_gates.py` |
| COPY-FIRST scanner | `extensions/wordflow/standards/copy_first.py` |
| AST symbols | `extensions/wordflow/standards/symbol_index.py` |
| Forensic contract | `extensions/wordflow/standards/forensic_contract.py` |
| VerdictAuthority | `extensions/wordflow/standards/verdict_authority.py` |
| Test smoke | `extensions/wordflow/standards/test_runner.py` |
| WiringGraph | `extensions/wordflow/standards/wiring_graph.py` |
| Scope/requirements | `extensions/wordflow/standards/scope_measure.py` |
| Mission edges | `extensions/wordflow/standards/mission_edges.py` |
| Adapt imports | `extensions/wordflow/standards/adapt_imports.py` |
| Policy snapshot | `extensions/wordflow/standards/policy_snapshot.py` |
| Plan artifact | `extensions/wordflow/standards/plan_artifact.py` |
| Catalogs | `extensions/wordflow/component_catalog.json`, `connect_catalog.json` |
| Bootstrap multi | `extensions/wordflow_kernel/bootstrap_multi.py` |
| CI | `.github/workflows/forensic-gates.yml` |
| Cursor rules | `.cursor/rules/wordflow-programming.mdc`, `AGENTS.md` |

### DOCUMENTADO (no runtime completo)

- `PIPELINE/FORENSIC_CODE_AUDIT.md`
- `PIPELINE/00_METODO_TRABAJO_Y_ARQUITECTURA.md`
- `PIPELINE/ADVANCED_ENGINEERING_STANDARD_V3.md`
- `PIPELINE/GAPS_PROGRAMMING_WORDFLOW.md`

### AUSENTE / NOT VERIFIED

- State machine global persistente OPEN→FIXED→VERIFIED→CLOSED
- GapRegistry runtime con gap_id lifecycle completo
- FourPassController que ejecute 4 pasadas independientes sobre todo el repo
- Auto-carga de documentos `reception/` dentro de `run_code_path`

---

## 2. Real Execution Flow

Flujo REAL de `run_code_path` (no el flujo ideal del brief):

```
raw_input
  → pre_gate (context/handoff + COPY-FIRST plan)
       si allow=False → return ok=False stage=programming_pre_gate
  → admit_or_reject (quality_bar)
       si !ok → return stage=quality_bar
  → lock_goals
       si !ok → return stage=goal_lock
  → run_cognitive_loop(plan_steps, goal_lock, task_class=CODE)
  → [opcional] compile_skill_to_code(skill)
  → build_evidence_packet + verify_evidence_packet
  → post_verify (si enforce_post_verify=True)
       measure: smoke, wiring, modules, scope, requirements, mission_edges
       ForensicCodeContract (campos según medición)
       EvidencePacket (standards)
       VerdictAuthority.decide
  → return {
       ok, mission_id, lock, cognitive, skill_compile,
       programming_pre_gate, programming_post_verify,
       evidence, evidence_ok, llm_control: "DENY"
     }
```

**CLOSED de misión global:** DOCUMENTED_NOT_VERIFIED (no hay un único motor que persista CLOSED).

---

## 3. Component Map

| Nombre | Path | Entradas | Salidas | Bloquea | Determinista | LLM |
|--------|------|----------|---------|---------|--------------|-----|
| run_code_path | code_path_runner.py | raw_input, flags | dict resultado | sí (stages) | sí (orquestación) | no (DENY) |
| pre_gate | code_path_runner + pipeline | context/handoff, symbol | allow/copy plan | sí si !context/handoff | sí | no |
| ExistingCodeScanner | copy_first.py | stem/symbol, roots | CopyFirstResult | bloquea GENERATE en plan | sí | no |
| admit_or_reject | input_quality_bar.py | raw_input | ok/detail | sí | sí* | UNKNOWN interior |
| lock_goals | goal_lock.py | text/raw | ok/lock | sí | sí* | UNKNOWN interior |
| run_cognitive_loop | cognitive_loop.py | topic, steps, lock | dict cognitive | no hard | UNKNOWN | UNKNOWN |
| post_verify | code_path_runner + standards | mission_id, evidence_ok | verdict dict | ok=false si FAIL | sí | no |
| VerdictAuthority | verdict_authority.py | contract, EvidencePacket | PASS/FAIL | sí formal | sí | no |

\*API determinista vista; cuerpo interno no auditado completo → UNKNOWN detalle.

**Callers verificados parcialmente:** `bootstrap_v1._run_code_path`, `code_path_smoke`. Otros callers: UNKNOWN.

---

## 4. Connectivity Graph

| Etapa | Estado |
|-------|--------|
| DECLARED | REAL (módulos + catalogs) |
| REGISTERED | PARTIAL (catalog; no registry universal verificado) |
| RESOLVED | PARTIAL (imports + paths catalog) |
| INVOKED | PARTIAL (solo path que llama pre/post/CI) |
| EXECUTED | PARTIAL (C-19 path) |
| OUTPUT PRODUCED | REAL (dict + evidence) |
| OUTPUT CONSUMED | UNKNOWN (quién usa el dict fuera del caller) |
| BEHAVIOR VERIFIED | PARTIAL (smoke + mission_edges default) |

**IMPORTABLE ≠ FUNCTIONALLY CONNECTED.**  
Muchos `standards/*` solo se ejecutan si `run_code_path`/CI los invocan.

Detecciones:

- broken connections: no inventadas; medir con WiringGraph + callers reales
- orphan components: standards no invocados fuera de code_path/CI = riesgo de aislamiento funcional
- never-invoked: helpers COPY/ADAPT no auto-llamados por runner

---

## 5. State Machine

### REAL (local al run)

- pre allow/deny
- stages: quality_bar | goal_lock | programming_pre_gate
- post verdict PASS/FAIL
- contract fields en memoria

### DOCUMENTADO no verificado como runtime

- OPEN → FIXED → VERIFIED → CLOSED
- forbidden OPEN→CLOSED con GapRegistry persistente

### Transiciones

| Transición | ¿Impedida en código del path? |
|------------|-------------------------------|
| sin context → execute | sí solo si flags False (default True) |
| sin post_verify → ok True | posible si `enforce_post_verify=False` |
| OPEN→CLOSED global | NOT VERIFIED |

---

## 6. Context / Document Handoff

| Mecanismo | Estado |
|-----------|--------|
| Flags `context_verified`, `handoff_verified` | REAL (default **True**) |
| BLOCK si False | REAL en validator/pre_gate |
| Auto discovery `reception/` | ABSENT en run_code_path |
| Versión/obsolescencia docs | ABSENT |
| Multi-repo reception MD | REAL como documentación; no wire al runner |

---

## 7. Requirement Traceability

| Eslabón | Estado |
|---------|--------|
| DOC → REQUIREMENT | ABSENT en runtime programming |
| REQUIREMENT → CODE | PARTIAL (listas fijas en scope_measure post_verify) |
| CODE → TEST | PARTIAL (smoke) |
| TEST → EVIDENCE | PARTIAL (packets) |

Detectores DOC_ONLY / CODE_ONLY / DOC_CODE_MISMATCH / CODE_TEST_MISMATCH / TEST_EVIDENCE_MISMATCH: **ABSENT** como sistema automático completo.

---

## 8. Contracts

| Contrato | Path | Enforcement |
|----------|------|-------------|
| ForensicCodeContract | standards/forensic_contract.py | si post_verify corre |
| EvidencePacket (standards) | standards/evidence.py | VerdictAuthority require_evidence |
| evidence_packet (engine) | engine/evidence_packet.py | verify en path |
| component/connect catalog | JSON | leídos por scanner/WiringGraph |
| FORENSIC MD / Standard V3 | PIPELINE | DOCUMENTED_NOT_VERIFIED como enforcement |
| QualityDAG / RuleEngine / Sheriff | standards | librería; no orquestan solas C-19 |

**CONTRACT DEFINITION ≠ siempre CONTRACT ENFORCEMENT en hot path.**

---

## 9. Rule Enforcement

| Regla | ¿Código? | ¿Bloquea? |
|-------|----------|-----------|
| COPY-FIRST | sí scanner | plan bloquea GENERATE; no reescribe solo |
| LLM ≠ PASS | VerdictAuthority + DENY | PASS formal no es LLM |
| SKIP ≠ PASS | contract + CI | sí en CI assert |
| 4-pass global | documentado | no loop 4-pass completo en runner |
| Gap loop FIX→RE-AUDIT | documentado | no máquina completa |
| Fail-closed CI | workflow | parcial (imports/smoke) |

---

## 10. Four-Pass Audit

- **DOCUMENTADO:** STRUCTURE / CONNECTIVITY / BEHAVIOR / FORENSIC_CLOSURE en MD.
- **EN C-19:** `AuditPasses` booleanos derivados de mediciones (smoke, wiring, modules, scope, edges).
- **No hay** cuatro runners forenses independientes sobre todo el árbol.

Estado: PARTIAL.

---

## 11. Gap Lifecycle

| Elemento | Estado |
|----------|--------|
| Campos gap_id…status en MD | DOCUMENTADO |
| GapRegistry runtime | ABSENT / NOT VERIFIED |
| Counters en ForensicCodeContract | REAL (memoria del post_verify) |
| GAPS_*.md | documentación humana |

Quién crea/clasifica/corrige/verifica gaps en runtime unificado: **NOT VERIFIED**.

---

## 12. AI / Agent Authority

- `llm_control: "DENY"` en return de `run_code_path` → REAL.
- VerdictAuthority no es LLM → REAL.
- Contenido LLM de `cognitive_loop` → UNKNOWN.
- `.cursor/rules` / `AGENTS.md` → reglas de agente IDE; no enforcement del kernel.

---

## 13. Deterministic vs LLM

| Etapa | Clase |
|-------|--------|
| pre_gate, scanner, AST, wiring, smoke, contract, verdict | DETERMINISTIC |
| quality_bar, goal_lock, skill compile | DETERMINISTIC API; interior UNKNOWN |
| cognitive_loop | UNKNOWN (posible HYBRID) |

---

## 14. Persistence / Memory

| Dato | Dónde | Estado |
|------|-------|--------|
| Instance state | wordflow_kernel instance_store | RELATED multi-instance |
| Copy sidecar | `*.copy_evidence.json` | REAL si se usa copy_file_deterministic |
| PlanArtifact / PolicySnapshot | módulos save() | REAL capacidad; no auto en cada run |
| Audit history append-only | — | NOT VERIFIED |
| Gap DB | — | ABSENT |

---

## 15. Code Execution Pipeline (cambio real de repo)

`run_code_path` **no** escribe el árbol git por sí solo.

Escritura de archivos en el trabajo reciente del agente = **GitHub API externa**, no el runner.

Helpers REALES pero no auto-invocados por el runner:

- `copy_file_deterministic`
- `adapt_file` / `rewrite_imports`

Riesgos:

- scope measure con listas fijas (no git diff)
- `enforce_post_verify=False` salta verdict

---

## 16. Real Task Reconstruction (C-19)

```
TASK: run_code_path(raw_input)
DOCS: no auto-load
CONTEXT: flags default True
REQUIREMENTS: measure hardcode post
PLAN: plan_steps default
CODE WRITE: no (runner)
TEST: smoke + mission_edges default
AUDIT: post_verify medido
GAPS: counters only
FIX/RE-AUDIT: no automático
EVIDENCE: engine + standards packets
CLOSED: solo verdict local PASS/FAIL
```

---

## 17. Master Traceability Matrix

| STEP | COMPONENT | INPUT | OUTPUT | BLOCKING |
|------|-----------|-------|--------|----------|
| INPUT | run_code_path | raw_input | — | — |
| PRE | pre_gate | flags, symbol | allow, copy plan | sí si !context/handoff |
| QUALITY | admit_or_reject | raw | ok | sí |
| LOCK | lock_goals | text | lock | sí |
| COG | run_cognitive_loop | steps, lock | cognitive | no hard |
| EVIDENCE | build/verify | paths/tests | evidence_ok | no hard |
| POST | VerdictAuthority | contract+packet | PASS/FAIL | ok acoplado a verdict |

---

## 18. Verified vs Inferred vs Unknown

### WHAT I CAN PROVE

- Cadena de `run_code_path` y paths standards citados.
- `llm_control: DENY`.
- Pre/post gates en ese archivo.
- CI import/smoke.
- Catalogs usados por WiringGraph/scanner.

### WHAT I CAN INFER

- cognitive_loop es etapa intermedia de plan/ejecución ligera.
- standards son librería de enforcement usada sobre todo desde code_path/CI.

### WHAT I CANNOT DETERMINE

- Todos los callers de producción.
- Si cognitive_loop usa LLM.
- Persistencia real de gaps/audit history.
- Consumidores del dict de salida.
- Enforcement global OPEN→CLOSED.

---

## 19. Missing Information Required

1. Cuerpo completo: `cognitive_loop.py`, `goal_lock.py`, `input_quality_bar.py`, `engine/evidence_packet.py`
2. `bootstrap_v1.py` alrededor de `_run_code_path`
3. Tests code_path bajo el repo
4. Workers/queues que encolen code_path
5. Relación `maxbry_loop` ↔ programming pipeline

---

## 20. Exact Reconstruction Diagram

```
Caller
 └─ run_code_path
     ├─ pre_gate → ProgrammingPipeline.pre_implement
     │    ├─ ForensicContractValidator.block_if_no_context
     │    └─ ExistingCodeScanner.plan (name | catalog | AST)
     ├─ admit_or_reject
     ├─ lock_goals
     ├─ run_cognitive_loop
     ├─ [compile_skill_to_code]
     ├─ build_evidence_packet / verify_evidence_packet
     └─ post_verify
          ├─ smoke / WiringGraph / scope / requirements / mission_edges
          ├─ ForensicCodeContract (measured)
          ├─ EvidencePacket
          └─ VerdictAuthority.decide
 ← dict(ok, pre, post, evidence, llm_control=DENY)
```

---

**Fin del mapa.** Funcionamiento REAL demostrado del Wordflow de programación de code, no la arquitectura ideal del PIPELINE forense completo.
