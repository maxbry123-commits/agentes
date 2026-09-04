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
| `extensions/wordflow/engine/programming_pipeline.py` | Pipeline pre/post + run_unified |
| `extensions/wordflow/engine/main_loop.py` | main_12 + programming_path |
| `extensions/wordflow/engine/programming_kwargs.py` | kwargs attested / minimal |

### Control plane (standards)
| Path | Rol |
|------|-----|
| `extensions/wordflow/standards/forensic_core.py` | **Enforcer** CORE14 + 4-pass + counters + evaluate |
| `extensions/wordflow/standards/forensic_contract.py` | Contrato dataclass |
| `extensions/wordflow/standards/verdict_authority.py` | Verdict formal |
| `extensions/wordflow/standards/gap_registry.py` | Lifecycle gaps |
| `extensions/wordflow/standards/closure_engine.py` | Árbitro CLOSED |
| `extensions/wordflow/standards/checklist_sheriff.py` | Sheriff checklist |
| `extensions/wordflow/standards/programming_points_catalog.py` | Catálogo puntos |
| `extensions/wordflow/standards/applicability_engine.py` | Tags → required |
| `extensions/wordflow/standards/context_manifest.py` | Manifest + validator |
| `extensions/wordflow/standards/evidence_verifier.py` | claim ≠ evidence |
| `extensions/wordflow/standards/executor_gates.py` | Pre/post gates |
| `extensions/wordflow/standards/copy_first.py` | Scanner reuse + stem index |
| `extensions/wordflow/standards/path_resolve.py` | Resolve paths |
| `extensions/wordflow/standards/symbol_index.py` | AST symbols |
| `extensions/wordflow/standards/wiring_graph.py` | Catalog graph |
| `extensions/wordflow/standards/test_runner.py` | Smoke tests |
| `extensions/wordflow/standards/quality_dag.py` | DAG calidad |
| `extensions/wordflow/standards/quality_handlers.py` | Handlers + UNIT/ARCH smoke |
| `extensions/wordflow/standards/fc_auto_measure.py` | FC auto |
| `extensions/wordflow/standards/core_auto_measure.py` | CORE auto |
| `extensions/wordflow/standards/policy_snapshot.py` | Policy freeze |
| `extensions/wordflow/standards/evidence_merge.py` | Dual evidence |
| `extensions/wordflow/standards/rule_engine.py` | Rule engine |

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
  ... PreGate / FC / adapt / profile / scan_paths ...
) -> dict
```

### Semántica fail-closed

| Condición | Resultado |
|-----------|-----------|
| `context_verified=False` o `handoff_verified=False` | **BLOCK** |
| CORE id ausente | **False** → FAIL CORE |
| Contador > 0 | FAIL cierre |
| 4 passes fallidas | FAIL |
| evidence/final_reaudit/quality_dag_ok False | FAIL |

**No hay** bypass de REQUIRED.

---

## 4. Secuencia de ejecución (legacy resumen)

```
require_context → quality_bar → goal_lock → cognitive → evidence
→ CORE measures → 4 passes → counters → PASS/FAIL
```

Ver **§20** para secuencia REAL completa post-FA.

---

## 5. CORE 01–14

| ID | Nombre |
|----|--------|
| CORE-01 | REQUIREMENT CLOSURE |
| CORE-02 | SCOPE/DIFF CLOSURE |
| CORE-03 | IMPLEMENTATION CLOSURE |
| CORE-04 | ARCHITECTURE/BOUNDARY |
| CORE-05 | DEPENDENCY CLOSURE |
| CORE-06 | CONTRACT CLOSURE |
| CORE-07 | REAL WIRING |
| CORE-08 | BEHAVIOR/EDGE |
| CORE-09 | TEST EFFECTIVENESS |
| CORE-10 | REGRESSION/IMPACT |
| CORE-11 | ERROR PATH CLOSURE |
| CORE-12 | CODE QUALITY |
| CORE-13 | REPOSITORY TRUTH |
| CORE-14 | EVIDENCE/VERDICT |

Enforcer no inventa PASS; default False.

---

## 6. Cuatro pasadas

1 STRUCTURE (01–06,13) → 2 CONNECTIVITY (+CORE-07) → 3 BEHAVIOR (08–11) → 4 FORENSIC_CLOSURE

---

## 7. Cadena connectivity

DECLARED → REGISTERED → RESOLVED → INVOKED → EXECUTED → OUTPUT_CONSUMED → BEHAVIOR_VERIFIED

---

## 8. Contadores de cierre (todos 0)

gaps, blocking_gaps, broken_connections, unexplained_orphans, unreachable_required_paths, unresolved_dependencies, unverified_paths, unverified_requirements, unverified_claims, pending_fixes, new_gaps_after_fix, unexpected_changes

---

## 9. Reglas

CLAIM≠EVIDENCE≠VERIFICATION≠PASS · required_without_handler=FAIL · skip≠pass · OPEN→CLOSED prohibido · no context → BLOCK

---

## 10. GapRegistry

OPEN→FIXED→VERIFIED→CLOSED · nunca OPEN→CLOSED · new_gaps_after_fix

---

## 11. Catálogo 500 vs runtime

Dataset referencia + ApplicabilityEngine + ChecklistSheriff · no 500 gates sueltos

---

## 12. ContextManifest

mission/task/spec/handoff required · flag context_verified es del caller

---

## 13. QualityDAG

Hot path con quality_handlers · UNIT/ARCH/AUDIT vía smoke FA-01 · TYPE/INTEGRATION/BUILD aún CI flag

---

## 14. Salida run_code_path

ok, verdict, forensic, policy, wire_trace (stage_ms, quality_bar), llm_control=DENY, c/s/t/u_status

---

## 15. Diagrama de cierre

CONTEXT+HANDOFF → quality → goals → CORE14 → 4 passes → counters0 → evidence+reaudit+quality → PASS

---

## 16. Checklist auditor

Leer forensic_core, runner, gap_registry · sin allow_skip · CI · callers · measures no LLM

---

## 17. Limitaciones

CORE auto parcial · mutation CORE-09 externa · git apply fuera del runner

---

## 18. Checklist rápida

forensic_core · code_path_runner · gap_registry · forensic-gates.yml · callers · PASS attested

---

## 19. PASS oficial (máquina)

```
PASS only if:
  context_verified AND handoff_verified
  AND all CORE-01..14 pass
  AND all 4 passes pass
  AND all closure counters == 0
  AND evidence_complete AND final_clean_reaudit_passed
  AND quality_dag_ok AND not claim_used_as_pass
else: FAIL or BLOCK
```

---

## 20. Secuencia REAL hot path (FA-04)

```
0. PolicySnapshot.freeze
1. ContextManifest (opt) → context/handoff
2. VerdictAuthority.require_context → BLOCK
3. PreGate COPY-FIRST+Sheriff (una vez U7)
4. apply_adapt + post_adapt ast
5. admit_or_reject (thresholds wire_trace)
6. lock_goals
7. cognitive + skill
8. evidence + merge
9. QualityDAG (smoke UNIT/ARCH FA-01)
10. core_auto + fc_auto (FA-02)
11. VerdictAuthority.decide
12. ClosureEngine
13. return DENY + statuses
```

---

## 21. FA-01..04 cierre

| ID | Fix |
|----|-----|
| FA-01 | quality_handlers UNIT/ARCH/AUDIT + test_runner smoke |
| FA-02 | fc_auto +FC-04/06/08 |
| FA-03 | test_main12_programming load yaml + programming_path |
| FA-04 | §20 secuencia real |

**Fin especificación auditoría Wordflow programming code.**
