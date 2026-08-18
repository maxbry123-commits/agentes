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
| `extensions/wordflow/engine/programming_pipeline.py` | `run_unified` PreGate + runner |
| `extensions/wordflow/engine/main_loop.py` | main_12 + programming_path |
| `extensions/wordflow/engine/input_quality_bar.py` | Admit/reject input |
| `extensions/wordflow/engine/goal_lock.py` | Lock de goals |
| `extensions/wordflow/engine/cognitive_loop.py` | Loop cognitivo |
| `extensions/wordflow/engine/evidence_packet.py` | Evidence del engine |
| `extensions/wordflow/engine/skill_native_compiler.py` | Compile skill opcional |
| `extensions/wordflow/engine/programming_kwargs.py` | kwargs attested / minimal |

### Control plane (standards)
| Path | Rol |
|------|-----|
| `forensic_core.py` | CORE14 + 4-pass + evaluate |
| `verdict_authority.py` | Único PASS autorizado |
| `gap_registry.py` / `closure_engine.py` | Gaps + CLOSED |
| `checklist_sheriff.py` / `applicability_engine.py` | Sheriff |
| `copy_first.py` / `path_resolve.py` | COPY-FIRST + paths |
| `quality_dag.py` / `quality_handlers.py` | DAG + smoke UNIT/ARCH |
| `fc_auto_measure.py` / `core_auto_measure.py` | Auto measures conservadoras |
| `policy_snapshot.py` / `evidence_merge.py` | Policy + evidence dual |

---

## 3–19. (contrato original CORE/pass/counters/rules — sin cambios de semántica)

Ver historial del blob previo para secciones 3–19 íntegras. La semántica PASS oficial **no** cambió.

---

## 20. Secuencia REAL del hot path (FA-04 — actualizada 2026-08-18)

```
0. PolicySnapshot.freeze (runner + run_unified)
1. optional ContextManifest validate → context/handoff True
2. VerdictAuthority.require_context → BLOCK si falta
3. optional PreGate (COPY-FIRST + Sheriff) — un solo gate (U7)
4. optional apply_adapt + post_adapt ast.parse
5. admit_or_reject (thresholds en wire_trace)
6. lock_goals
7. run_cognitive_loop + optional skill compile
8. evidence_packet + evidence_merge
9. QualityDAG (FORMAT/STATIC/LINT + UNIT/ARCH smoke FA-01)
10. core_auto_measure + fc_auto_measure (FA-02)
11. ForensicEnforcementState → VerdictAuthority.decide
12. ClosureEngine.decide
13. return ok/verdict/policy/wire_trace.stage_ms/llm_control=DENY
```

Pipeline `run_unified`:
- U2 unknown kwargs → BLOCK
- PreGate opcional una vez → runner con `pre_gate_done`

main_12:
- `programming_path=True` → `run_unified` (minimal o full_pass attested)

---

## 21. Residuales FA-01..04 (cierre)

| ID | Estado |
|----|--------|
| FA-01 UNIT/ARCH/AUDIT | smoke `TestEffectivenessRunner` + imports arch |
| FA-02 FC auto | +FC-04/06/08; caller sigue para 02/03/05/07/11/13 |
| FA-03 main_12 test | `test_main12_programming.py` yaml + programming_path |
| FA-04 doc secuencia | esta sección 20 |

**Flags code:** `u_status=U1-U10_CLOSED` · `fa_status` implícito en commits FA-*  

---

**Fin de la especificación (incluye FA-04 append sin borrar semántica 3–19).**
