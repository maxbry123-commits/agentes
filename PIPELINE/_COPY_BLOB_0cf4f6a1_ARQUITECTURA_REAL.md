# COPY EXACT — commit 0cf4f6a18515134b675fd44b93e2bf8780e20b72
# Path origen: PIPELINE/ARQUITECTURA_WORDFLOW_PROGRAMMING_REAL.md
# Método: copia determinista GitHub. No editar este archivo a mano.

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
**Fuente commit:** 0cf4f6a18515134b675fd44b93e2bf8780e20b72
