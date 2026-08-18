# WORDFLOW DE PROGRAMACIÓN DE CODE — ESPECIFICACIÓN DETALLADA PARA AUDITORÍA

**Repo:** `maxbry123-commits/agentes`  
**Fecha:** 2026-08-18  
**Alcance:** solo el path de programming de code (control + execution plane)  
**Regla de lectura:** REAL implementado vs DOCUMENTADO vs AUSENTE  

Documentos relacionados:
- `PIPELINE/FORENSIC_ENFORCEMENT_REQUIRED.md`
- `PIPELINE/WORDFLOW_PROGRAMMING_COMO_FUNCIONA.md`
- `PIPELINE/ARQUITECTURA_WORDFLOW_GLOBAL.md`
- `PIPELINE/WORDFLOW_PROGRAMMING_FORENSIC_MAP.md`
- `PIPELINE/ENFORCEMENT_P0_REDESIGN.md`

---

## 1. Propósito del subsistema

El Wordflow de programming **no** es un editor de código autónomo que escribe el git tree por sí solo.

Es un **control plane fail-closed** que:

1. Exige contexto y handoff verificados antes de programar/auditar.
2. Orquesta el path C-19 (`run_code_path`).
3. Exige medidas deterministas CORE-01..14.
4. Ejecuta evaluación forense de 4 pasadas en orden.
5. Exige contadores de cierre en cero.
6. Prohíbe CLAIM→PASS y SKIP→PASS en gates REQUIRED.
7. Devuelve `llm_control: DENY` y `verdict` BLOCK/FAIL/PASS.

La escritura real de archivos en el historial del proyecto la hace típicamente el **agente externo vía GitHub API**; el runtime valida y puede bloquear el cierre.

---

## 2. Árbol de paths relevantes

### Execution plane
| Path | Rol |
|------|-----|
| `extensions/wordflow/engine/code_path_runner.py` | Hot path `run_code_path` |
| `extensions/wordflow/engine/input_quality_bar.py` | Admit/reject input |
| `extensions/wordflow/engine/goal_lock.py` | Lock de goals |
| `extensions/wordflow/engine/cognitive_loop.py` | Loop cognitivo (interior LLM = UNKNOWN) |
| `extensions/wordflow/engine/evidence_packet.py` | Evidence del engine |
| `extensions/wordflow/engine/skill_native_compiler.py` | Compile skill opcional |
| `extensions/wordflow/engine/programming_pipeline.py` | Pipeline pre/post helpers |

### Control plane (standards)
| Path | Rol |
|------|-----|
| `extensions/wordflow/standards/forensic_core.py` | **Enforcer** CORE14 + 4-pass + counters + evaluate |
| `extensions/wordflow/standards/forensic_contract.py` | Contrato dataclass legacy/complementario |
| `extensions/wordflow/standards/verdict_authority.py` | Verdict formal standards |
| `extensions/wordflow/standards/gap_registry.py` | Lifecycle gaps + new_gaps_after_fix |
| `extensions/wordflow/standards/closure_engine.py` | Árbitro CLOSED |
| `extensions/wordflow/standards/checklist_sheriff.py` | Sheriff checklist puntos |
| `extensions/wordflow/standards/programming_points_catalog.py` | Catálogo CORE/CONDITIONAL/… |
| `extensions/wordflow/standards/applicability_engine.py` | Tags → required points |
| `extensions/wordflow/standards/context_manifest.py` | Manifest + validator |
| `extensions/wordflow/standards/evidence_verifier.py` | claim ≠ evidence resoluble |
| `extensions/wordflow/standards/executor_gates.py` | Pre/post gates |
| `extensions/wordflow/standards/copy_first.py` | Scanner reuse |
| `extensions/wordflow/standards/symbol_index.py` | AST symbols |
| `extensions/wordflow/standards/wiring_graph.py` | Catalog graph |
| `extensions/wordflow/standards/test_runner.py` | Smoke tests |
| `extensions/wordflow/standards/quality_dag.py` | DAG calidad (librería) |
| `extensions/wordflow/standards/rule_engine.py` | Rule engine (librería) |

### Datos / policy
| Path | Rol |
|------|-----|
| `extensions/wordflow/component_catalog.json` | Componentes declarados |
| `extensions/wordflow/connect_catalog.json` | Conexiones declaradas |
| `.github/workflows/forensic-gates.yml` | CI smoke |
| `.cursor/rules/wordflow-programming.mdc` | Rules agente IDE |
| `AGENTS.md` | Autoridad docs para agentes |

---

## 3. API de entrada: `run_code_path`

```text
run_code_path(
  raw_input: str,
  plan_steps: list[str] | None = None,
  skill: dict | None = None,
  mission_id: str = "",
  context_verified: bool = False,
  handoff_verified: bool = False,
  core_measures: dict[str, bool] | None = None,
  connectivity: dict[str, bool] | None = None,
  counters: dict[str, int] | None = None,
  evidence_complete: bool = False,
  final_clean_reaudit_passed: bool = False,
  quality_dag_ok: bool = False,
) -> dict
```

### Semántica fail-closed

| Condición | Resultado |
|-----------|-----------|
| `context_verified=False` o `handoff_verified=False` | **BLOCK** inmediato, no sigue programming |
| CORE id ausente en `core_measures` | se trata como **False** → fallará CORE |
| Contador > 0 | FAIL en cierre |
| 4 passes incompletas o fallidas | FAIL |
| `evidence_complete=False` o `final_clean_reaudit_passed=False` | FAIL |
| `quality_dag_ok=False` | FAIL |

**No hay** parámetro `allow_skip_post_verify` / bypass de REQUIRED en esta versión del runner.

---

## 4. Secuencia de ejecución real

```
1. ForensicProgrammingEnforcer.require_context
      ↓ BLOCK si falta
2. admit_or_reject (quality_bar)
      ↓ FAIL stage quality_bar
3. lock_goals
      ↓ FAIL stage goal_lock
4. run_cognitive_loop
5. optional compile_skill_to_code
6. build_evidence_packet + verify_evidence_packet (engine)
7. Construir ForensicEnforcementState:
      - CoreCheckResult × 14 desde core_measures (default False)
      - connectivity chain flags (default False)
      - ClosureCounters desde counters
      - evidence_complete ∧ evidence_ok
      - final_clean_reaudit_passed
      - quality_dag_ok
8. enforcer.evaluate(state)
9. return dict(ok, verdict, forensic, evidence, llm_control=DENY, ...)
```

---

## 5. CORE 01–14 (contrato ejecutable)

Definidos en `forensic_core.CORE_IDS` y evaluados en `ForensicEnforcementState.core_results`.

| ID | Nombre | Significado de auditoría |
|----|--------|--------------------------|
| CORE-01 | REQUIREMENT CLOSURE | Requisitos de la tarea materializados/trazados |
| CORE-02 | SCOPE/DIFF CLOSURE | Diff ⊆ scope; unexpected_changes debe ser 0 |
| CORE-03 | IMPLEMENTATION CLOSURE | CODE_EXISTS ≠ FEATURE_COMPLETE; DONE = scope completo |
| CORE-04 | ARCHITECTURE/BOUNDARY | Fronteras/arquitectura respetadas |
| CORE-05 | DEPENDENCY CLOSURE | Deps resueltas; sin deps prohibidas sin justificación |
| CORE-06 | CONTRACT CLOSURE | Contratos versionados/validables |
| CORE-07 | REAL WIRING | Cadena DECLARED…BEHAVIOR_VERIFIED |
| CORE-08 | BEHAVIOR/EDGE | Comportamiento y bordes |
| CORE-09 | TEST EFFECTIVENESS | Test capaz de fallar si se rompe la lógica |
| CORE-10 | REGRESSION/IMPACT | Impacto consumers/deps/contratos/tests |
| CORE-11 | ERROR PATH CLOSURE | Paths de fallo aplicables manejados/testeados |
| CORE-12 | CODE QUALITY | Calidad (lint/type/static según stack) |
| CORE-13 | REPOSITORY TRUTH | Verdad de repo (paths/revisión) no percepción LLM |
| CORE-14 | EVIDENCE/VERDICT | Evidence completa + veredicto autorizado |

**Importante para auditores:** el enforcer **no inventa** que un CORE pasó. Si el caller no envía `core_measures["CORE-0X"]=True` con base real, el default es **False** → FAIL. Eso es `required_without_handler = FAIL`.

---

## 6. Cuatro pasadas obligatorias

`all_four_passes_required = true`  
Orden en `run_four_passes`:

| Pass | Nombre | Criterio simplificado en código actual |
|------|--------|----------------------------------------|
| 1 | STRUCTURE | Cores 01–06 y 13 en pass |
| 2 | CONNECTIVITY | Cadena connectivity completa + CORE-07 |
| 3 | BEHAVIOR | Cores 08–11 |
| 4 | FORENSIC_CLOSURE | counters all zero + evidence + final_reaudit + CORE-14 + no claim_as_pass |

Si pass N falla, los siguientes se marcan fallidos por bloqueo (no se “aprueba el cierre” en cascada).

---

## 7. Cadena de conectividad (contrato duro)

```
DECLARED → REGISTERED → RESOLVED → INVOKED → EXECUTED
→ OUTPUT_CONSUMED → BEHAVIOR_VERIFIED
```

Cada eslabón es un bool en `state.connectivity`. Default False si el caller no mide.

---

## 8. Contadores de cierre (todos deben ser 0)

```
gaps
blocking_gaps
broken_connections
unexplained_orphans
unreachable_required_paths
unresolved_dependencies
unverified_paths
unverified_requirements
unverified_claims
pending_fixes
new_gaps_after_fix
unexpected_changes
```

`new_gaps_after_fix` soporta el loop FIX → RE-AUDIT → detectar nuevos gaps.

---

## 9. Reglas inequívocas

| Regla | Valor |
|-------|--------|
| CLAIM ≠ EVIDENCE | sí |
| EVIDENCE ≠ VERIFICATION | sí |
| VERIFICATION + EVIDENCE para PASS | sí |
| required_without_handler | FAIL |
| required_skip | FAIL |
| optional_skip | ALLOW |
| skip == pass | **false** |
| OPEN → CLOSED | **prohibido** |
| no_dev_bypass_required | **true** |
| NO VERIFIED CONTEXT → NO PROGRAMMING/AUDIT | **true** |

---

## 10. GapRegistry (contrato de gap)

Campos: `gap_id`, `task_id`, `mission_id`, `rule_id`, `severity`, `description`, `location`, `root_cause`, `required_fix`, `implemented_fix`, `verification`, `evidence`, `status`, `created_revision`, `fixed_revision`, `verified_revision`, `created_at`.

Transiciones: OPEN→FIXED→VERIFIED→CLOSED (y retrocesos controlados a OPEN). Nunca OPEN→CLOSED.

`note_new_gap_after_fix` incrementa `new_gaps_after_fix`.

---

## 11. Catálogo de puntos (500) vs runtime

| Capa | Qué es |
|------|--------|
| Listas PIPELINE 200/300/500 | Dataset de referencia / inventario Cursor-class |
| `programming_points_catalog.py` | Subset con metadatos CORE/CONDITIONAL/ADVISORY/REFERENCE |
| `ApplicabilityEngine` | Elige required según tags; agente no downgrade |
| `ChecklistSheriff` | Exige claims + evidence verificable |

**No** se implementan 500 gates independientes.

---

## 12. ContextManifest

Campos: mission_id, task_id, project_docs, architecture_docs, task_spec, relevant_files, contracts, tests, repository_revision, handoff_ref.

`ContextValidator` falla si faltan mission/task/spec/handoff.

**Nota de auditoría:** tener ContextManifest **no** sustituye por sí solo `context_verified=True`; el caller debe demostrar verificación real antes de poner el flag.

---

## 13. QualityDAG / RuleEngine / Sheriff legacy

Existen como librerías bajo `standards/`. El enforcer exige `quality_dag_ok=True` medido por el caller (skip≠pass). Integración automática completa de todos los nodos FORMAT…AUDIT en el hot path: **parcial / a verificar en callers CI**.

---

## 14. Salida de `run_code_path`

```text
ok: bool
mission_id, lock, cognitive, skill_compile
evidence, evidence_ok
forensic: { verdict, reason, passes?, counters?, rules?, connectivity? }
llm_control: "DENY"
verdict: BLOCK | FAIL | PASS
```

---

## 15. Diagrama de cierre

```
CONTEXT+HANDOFF verified?
    │ no → BLOCK
    ▼
quality_bar → goal_lock → cognitive → evidence_engine
    ▼
CORE-01..14 measured?
    │ missing/false → FAIL
    ▼
PASS1 STRUCTURE → PASS2 CONNECTIVITY → PASS3 BEHAVIOR → PASS4 FORENSIC
    │ any fail → FAIL
    ▼
counters all 0?
    │ no → FAIL
    ▼
evidence_complete ∧ final_clean_reaudit ∧ quality_dag_ok?
    │ no → FAIL
    ▼
PASS / ok=True
```

Loop de gaps (operativo con GapRegistry):

```
IMPLEMENT → AUDIT → CLASSIFY → FIX → RE-AUDIT
→ (new_gaps_after_fix?) → FIX… → FINAL CLEAN RE-AUDIT → CLOSED
```

---

## 16. Qué debe comprobar un auditor humano o CI

1. ¿El caller pasa context/handoff solo cuando hay prueba?  
2. ¿Las medidas CORE vienen de WiringGraph/tests/diff y no del LLM?  
3. ¿Connectivity refleja DECLARED…BEHAVIOR_VERIFIED real?  
4. ¿Counters reflejan gaps reales post-fix?  
5. ¿Se puede obtener PASS con core_measures vacíos? → **No debe ser posible**.  
6. ¿Existe bypass REQUIRED? → **No en runner actual**.  
7. ¿cognitive_loop usa LLM? → **UNKNOWN** (inspeccionar archivo).  
8. ¿Quién consume el dict de salida? → inventario de callers.  

---

## 17. Limitaciones explícitas (honestas)

| Tema | Estado |
|------|--------|
| Auto-medición de cada CORE | Caller/CI debe aportar measures |
| DOC↔CODE mismatch detectors automáticos completos | Parcial / no sistema único |
| ImpactAnalyzer callers AST | No cerrado como motor único |
| Mutation testing real CORE-09 | Política + medida externa; no motor mutación global |
| Four runners de proceso independientes | Un enforcer con 4 fases ordenadas |
| Apply git dentro del runner | No (by design) |

---

## 18. Checklist de auditoría rápida del código

- [ ] Leer `forensic_core.py` (RULES, evaluate, run_four_passes)  
- [ ] Leer `code_path_runner.py` (BLOCK context, defaults measures False)  
- [ ] Leer `gap_registry.py` (campos + transitions)  
- [ ] Confirmar ausencia de `allow_skip` REQUIRED  
- [ ] Revisar CI `forensic-gates.yml`  
- [ ] Trazar callers de `run_code_path`  
- [ ] Verificar que PASS de demo use measures reales no hardcode alegre  

---

## 19. PASS oficial (definición de máquina)

```
PASS only if:
  context_verified
  AND handoff_verified
  AND all CORE-01..14 pass
  AND all 4 passes pass
  AND all closure counters == 0
  AND evidence_complete
  AND final_clean_reaudit_passed
  AND quality_dag_ok
  AND not claim_used_as_pass
else:
  FAIL or BLOCK
```

---

**Fin de la especificación de auditoría del Wordflow de programming de code.**
