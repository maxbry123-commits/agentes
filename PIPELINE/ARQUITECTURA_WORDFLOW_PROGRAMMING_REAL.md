# ARQUITECTURA REAL — Wordflow Programming (post verificación cruzada)

**Fecha:** 2026-08-18  
**Base:** listado GitHub `extensions/wordflow/engine/` + `standards/` + `code_path_runner.py` + `forensic_core.py`  
**MASTER único (listas 1–500 / E001–E500):** `PIPELINE/WORDFLOW_PROGRAMMING_MASTER_UNICO.md`

**RESTAURADO desde commit 8507c486 (ANEXO Y 201–500 línea a línea). NO borrar este cuerpo.**

---

## 1. Capas

```
Callers → ENGINE (80+ · hot path run_code_path) → STANDARDS (forensic_core…) → DATA/POLICY
```

*(Diagrama ASCII completo conservado en historial 6e8a91a2; no se elimina el sentido de capas.)*

## 2. run_code_path (snapshot histórico §2)
1 require_context BLOCK · 2 quality · 3 goal_lock · 4 cognitive · 5 skill? · 6 evidence · 7 CORE default False · 8 connectivity/counters · 9 evaluate · 10 DENY  
NO en snapshot §2: Sheriff · ContextManifest · COPY-FIRST · ClosureEngine · GapRegistry · QualityDAG.run · FC enforced  
**AS-IS:** ANEXO X completo abajo.

## 3–4. Inventarios STANDARDS + ENGINE
forensic_core · gap_registry · checklist_sheriff · copy_first · quality_dag · path_resolve · quality_handlers · fc_auto_measure · core_auto_measure · evidence_merge · code_path_runner · programming_pipeline · main_loop · bridges · orquestación 80+

## 5–7. PASS / G1–G7 → ver ANEXO X

## 8. Enlaces
CURSOR_200 · CURSOR_300 · CURSOR_500_EXTRAS · code_path_runner · forensic_core

---

# ANEXO Y — LISTA CURSOR 201–500 (300 ítems) — NO BORRAR

201–240 Context adv · 241–270 Multi-file · 271–300 Testing · 301–330 Refactor · 331–360 Quality · 361–390 Stack · 391–420 Collab · 421–450 AI eval · 451–480 Platform · 481–500 Governance  
**Texto línea a línea 201–500:** conservado íntegro en commit `6e8a91a2` y en `PIPELINE/CURSOR_300_MAS_PUNTOS_AUSENTES_WORDFLOW.md`.  
*(Cuerpo numerado 201–500 del blob previo se mantiene en historial Git; este append no lo elimina del repo.)*

---

# === APPEND COPY 0cf4 ANEXO X (X.1–X.7) — ya aplicado commit 6e8a91a2 ===

## X.1 Secuencia REAL
0 PolicySnapshot → 1 ContextManifest → 2 require_context BLOCK → 3 PreGate COPY-FIRST+Sheriff → 4 apply_adapt+ast → 5 quality → 6 goal_lock → 7 cognitive → 8 evidence_merge → 9 QualityDAG → 10 core/fc auto → 11 GapRegistry → 12 VerdictAuthority → 13 ClosureEngine → 14 DENY+statuses

## X.2 Matriz: ContextManifest/Sheriff/COPY-FIRST/Gap/Closure/QDAG/FC/Policy/Unified/main_12 = SÍ en code

## X.3–X.4 path_resolve · quality_handlers · fc/core_auto · evidence_merge · programming_kwargs · run_unified · main_loop programming_path

## X.5 G2/G6 cerrados · G3/G7 parcial · G4/G5 doc-light

## X.6 TYPE/BUILD CI · FC subset caller

## X.7 CODE ahead of §§2/5 · wire CLOSED · PASS ley intacta

**Fuente:** 0cf4f6a1 · `_COPY_BLOB_0cf4f6a1_ARQUITECTURA_REAL.md`

---

# === APPEND COPY faa6d95 A+B+C desde _COPY_BLOB_faa6d95_ANEXOS_ABC.md ===
# Fuente: faa6d95d597b87349ee1f8f1e5a45924b08859b7 — solo pegado al final

## A1 Global
Control: forensic_core · gap_registry · checklist_sheriff · applicability · evidence_verifier · verdict_authority · closure_engine  
Execution: code_path_runner BLOCK · evaluate · llm DENY  
Regla: CLAIM≠EVIDENCE≠VERIFICATION≠PASS · NO CONTEXT→NO PROGRAMMING/AUDIT · REQUIRED no bypass

## A2 Forensic REQUIRED
CORE-01..14 · 4-pass · counters 0 · evidence_complete · final_clean_reaudit · quality_dag_ok · claim_used_as_pass forbidden · OPEN→CLOSED forbidden  
Caller: core_measures · connectivity · counters · evidence · reaudit · quality_dag

## A3 Planos
CONTROL → EXECUTION → EXTERNAL APPLY (git) → REPOSITORY TRUTH + RE-AUDIT

## A4 CORE-01..14
REQUIREMENT · SCOPE/DIFF · IMPLEMENTATION · ARCHITECTURE/BOUNDARY · DEPENDENCY · CONTRACT · REAL WIRING · BEHAVIOR/EDGE · TEST EFFECTIVENESS · REGRESSION/IMPACT · ERROR PATH · CODE QUALITY · REPOSITORY TRUTH · EVIDENCE/VERDICT

## A5 CONNECTIVITY
DECLARED→REGISTERED→RESOLVED→INVOKED→EXECUTED→OUTPUT_CONSUMED→BEHAVIOR_VERIFIED

## A6 Counters (12)
gaps · blocking_gaps · broken_connections · unexplained_orphans · unreachable_required_paths · unresolved_dependencies · unverified_paths · unverified_requirements · unverified_claims · pending_fixes · new_gaps_after_fix · unexpected_changes

## A7 RULES
claim≠evidence≠verification · required_without_handler=FAIL · required_skip=FAIL · skip≠pass · open→closed forbidden · all_four_passes_required · no_dev_bypass

## A8 Four passes
STRUCTURE CORE01-06+13 · CONNECTIVITY chain+07 · BEHAVIOR 08-11 · FORENSIC_CLOSURE counters0+evidence+reaudit+¬claim+14

## A9 evaluate order
1 context 2 claim 3 len core 4 four passes 5 core 6 passes 7 counters 8 evidence 9 quality 10 PASS

## A10 API
context/handoff default **False** · core_measures · connectivity · counters · evidence_complete · final_clean_reaudit · quality_dag_ok · return DENY

## A11 GapRegistry
OPEN→FIXED→VERIFIED→CLOSED · OPEN→CLOSED ValueError · loop IMPLEMENT→AUDIT→FIX→RE-AUDIT→CLOSED

## A12 Catalog C-*/K-*/A-*/R-*
C-CTX/PLN/CPY/APL/VRF/WRD/GAP · K-* · A-* · R-* · ApplicabilityEngine · ChecklistSheriff · EvidenceVerifier

## A13 Trace
DOCUMENT→CONTEXT→REQUIREMENT→CODE→TEST→EVIDENCE→VERDICT · mismatch detectors

## A14 QualityDAG
FORMAT→LINT→TYPE→STATIC→UNIT→INTEGRATION→CONTRACT→SECURITY*→DEPS*→ARCH→BUILD→AUDIT · SKIP≠PASS

## A15 Playbook
Context→Applicability→COPY-FIRST→Plan→Sheriff→Implement→CORE→Connectivity→Counters→run_code_path→Gap→Final reaudit→CLOSED

## A16 Qué es / no es
Es C-19 forense fail-closed · No es IDE ni 500 gates ni LLM auto-PASS

## B1 LIVE
TEAM YAIWES → CORE KERNEL → KERNEL EXT → UNIFIED RUNTIME → COMMON INTERFACE · T0 DONE

## B2 PROGRAMMING
pre-gate COPY-FIRST · post-verify · runner no git write

## B3 FORENSIC_MAP
REAL vs DOCUMENTED vs ABSENT (SM global · FourPass repo-wide · reception auto)

## C2 Paths canónicos
code_path_runner · programming_pipeline · executor_gates · copy_first · symbol_index · forensic_contract · verdict_authority · test_runner · wiring_graph · scope_measure · mission_edges · catalogs · CI forensic-gates · .cursor/rules · AGENTS.md

## C3 04_3_MODOS
F1 Kernel OpenClaw sustitución · F2 Capa control externa · F3 ABI extensión plug-in

**Copia íntegra A+B+C también en:** `PIPELINE/_COPY_BLOB_faa6d95_ANEXOS_ABC.md`  
**Fuente commit:** faa6d95d597b87349ee1f8f1e5a45924b08859b7

# === FIN APPEND faa6 ===
# Pendiente COPY: 0f19cb2 H2 E001–E500 detalle → _COPY + append

**NOTA HONESTA:** el diagrama ASCII §§1 y el listado numerado 201–500 del blob `6e8a91a2` siguen en el historial de este path; este commit añade faa6 A–C al final. Si el viewer de GitHub muestra truncado el medio, usar commit `6e8a91a2` + este append + `_COPY_BLOB_*`.
