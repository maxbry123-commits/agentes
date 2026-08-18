# FORENSIC CODE AUDIT v1.2
**Fecha:** 2026-08-18  
**Regla maestra:** NO CONTEXT → NO PROGRAMMING · NO EVIDENCE → NO PASS · GAP → FIX → RE-AUDIT · 4 PASSES CLEAN → CLOSED

## CORE 14 (siempre)
01 REQUIREMENT · 02 SCOPE/DIFF · 03 IMPLEMENTATION · 04 ARCHITECTURE · 05 DEPENDENCY · 06 CONTRACT · 07 REAL WIRING · 08 BEHAVIOR/EDGE · 09 TEST EFFECTIVENESS · 10 REGRESSION/IMPACT · 11 ERROR PATHS · 12 CODE QUALITY · 13 REPOSITORY TRUTH · 14 EVIDENCE+VERDICT

## FC cierre
| ID | Regla |
|----|-------|
| FC-01 | Architecture ↔ project documentation |
| FC-02 | Full connectivity / wiring |
| FC-03 | Gap → Fix → Re-Audit loop |
| FC-04 | Requirement → Code → Test → Evidence |
| FC-05 | Change impact analysis |
| FC-06 | Real behavioral verification |
| FC-07 | Final independent re-audit |
| FC-08 | DOCUMENT CONTEXT VERIFICATION |
| FC-09 | DOCUMENT ↔ CODE CROSS-VERIFICATION |
| FC-10 | FUNCTIONAL WIRING (declared→…→output consumed→behavior) |
| FC-11 | EVIDENCE-BACKED VERDICT (CLAIM ≠ PROOF) |
| FC-12 | FOUR-PASS AUDIT (Structure/Connectivity/Behavior/Forensic) |
| FC-13 | ANTI-OVERENGINEERING (minimal audit ≠ minimal quality) |

## REGLA 1 — Conectividad funcional
DECLARED → REGISTERED → RESOLVED → INVOKED → EXECUTED → OUTPUT CONSUMED → BEHAVIOR VERIFIED  
broken_connections=0 · unresolved_dependencies=0 · unexplained_orphans=0 · unverified_paths=0

## REGLA 2 — Ningún PASS por afirmación
CLAIM ≠ PROOF · PASS = VERIFICATION + EVIDENCE

## NORMA 4 PASADAS
1 STRUCTURE — docs/arch/repo/files/deps/boundaries/contracts  
2 CONNECTIVITY — req→component→registration→resolution→invocation→execution→consumer  
3 BEHAVIOR — expected↔actual (normal/edge/error/regression/tests efectivos)  
4 FORENSIC CLOSURE — findings→fixes→re-audit→evidence→verdict (gaps residuales, scope, claims)

## CONTEXTO DOCUMENTAL
PROJECT DOCS → CONTEXT INDEX → REQUIREMENTS → ARCHITECTURE → CONTRACTS → IMPLEMENTATION → AUDIT  
¿Suficiente contexto? NO → BLOCK / REQUEST CONTEXT (no inventar)

## CROSS-VERIFY DOC ↔ CODE
DOC_ONLY · CODE_ONLY · DOC_CODE_MISMATCH · CODE_TEST_MISMATCH · TEST_EVIDENCE_MISMATCH = gaps

## CONDITIONAL (solo si aplica)
Security · DB/Migration · Perf · Concurrency · External API · AI/Agent · Production · New dependency · Persistence · Distributed · Multi-repo

## NO bloquear tarea normal
SBOM/licencias universales · compliance genérico · DR/RTO · SLO universal · chaos · shadow traffic · break-glass · rotation drills · on-call · cost universal · model drift · attestation por edit · offline pack · API freeze · multi-tenant/PII si no aplica

## Anti-sobreingeniería
MINIMAL AUDIT ≠ MINIMAL QUALITY  
Quitar controles no aplicables ≠ quitar verificaciones requeridas  
Nunca degradar arquitectura/seguridad/conectividad/funcionalidad

## FORENSIC_CODE_CONTRACT v1.2
```yaml
FORENSIC_CODE_CONTRACT:
  version: "1.2"
  core: # all REQUIRED
    requirements: REQUIRED
    scope_diff: REQUIRED
    implementation: REQUIRED
    architecture: REQUIRED
    dependencies: REQUIRED
    contracts: REQUIRED
    connectivity: REQUIRED
    behavior: REQUIRED
    tests: REQUIRED
    regression_impact: REQUIRED
    error_paths: REQUIRED
    code_quality: REQUIRED
    repository_truth: REQUIRED
    evidence: REQUIRED
  context:
    required_before_implementation: true
    required_before_audit: true
    missing_context: BLOCK
    cross_verify_documents: true
  connectivity:
    declared: REQUIRED
    registered: REQUIRED
    resolved: REQUIRED
    invoked: REQUIRED
    executed: REQUIRED
    output_consumed: REQUIRED
    behavior_verified: REQUIRED
  audit:
    passes_required: 4
    pass_1: STRUCTURE
    pass_2: CONNECTIVITY
    pass_3: BEHAVIOR
    pass_4: FORENSIC_CLOSURE
    all_passes_required: true
  loop:
    sequence: [IMPLEMENT, AUDIT, CLASSIFY_GAPS, FIX, RE_AUDIT]
    if_gap_found: FIX_AND_REAUDIT
    require_clean_reaudit: true
    unlimited_iterations: true
    states: [OPEN, FIXED, VERIFIED, CLOSED]
    forbidden_transition: [OPEN_TO_CLOSED]
  engineering:
    avoid_overengineering: true
    preserve_architecture: true
    preserve_quality_standard: true
    remove_non_applicable_checks: true
    never_remove_required_verification: true
  closure:
    blocking_gaps: 0
    broken_connections: 0
    unexplained_orphans: 0
    unresolved_dependencies: 0
    unverified_requirements: 0
    unverified_claims: 0
    pending_fixes: 0
    new_gaps_after_fix: 0
    unexpected_changes: 0
  evidence:
    required: true
    claim_is_not_proof: true
    every_critical_pass_requires_evidence: true
    evidence_must_reference: [repository, path, test, commit_or_revision]
  verdict:
    PASS_ONLY_IF:
      - context_verified
      - all_required_checks_pass
      - all_four_audit_passes_complete
      - blocking_gaps == 0
      - broken_connections == 0
      - unexplained_orphans == 0
      - unresolved_dependencies == 0
      - unverified_requirements == 0
      - unverified_claims == 0
      - pending_fixes == 0
      - new_gaps_after_fix == 0
      - unexpected_changes == 0
      - evidence_complete
      - final_clean_reaudit_passed
```

## Salida mínima obligatoria
```
FORENSIC CODE AUDIT
━━━━━━━━━━━━━━━━━━
PASS 1 — STRUCTURE          [✓/✗]
PASS 2 — CONNECTIVITY       [✓/✗]
PASS 3 — BEHAVIOR           [✓/✗]
PASS 4 — FORENSIC CLOSURE   [✓/✗]

ARCHITECTURE ↔ DOCS              [✓/✗]
CONNECTIVITY                     [✓/✗]
REQ → CODE → TEST → EVIDENCE     [✓/✗]
DEPENDENCIES / CONTRACTS         [✓/✗]
BEHAVIOR / ERROR PATHS           [✓/✗]
IMPACT / REGRESSION              [✓/✗]
EVIDENCE                         [✓/✗]

GAPS: 0 | BROKEN: 0 | ORPHANS: 0 | PENDING: 0 | UNVERIFIED: 0
RESULT: PASS / FAIL
```

**Nota:** 0 gaps = 0 bloqueantes aplicables del contrato, no “cero mejoras posibles en el universo”.
