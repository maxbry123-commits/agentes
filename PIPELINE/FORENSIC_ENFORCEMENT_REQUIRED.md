# FORENSIC PROGRAMMING ENFORCEMENT — REQUIRED (100%)

## Runtime
- `extensions/wordflow/standards/forensic_core.py` — CORE-01..14, 4-pass, counters, evaluate()
- `extensions/wordflow/engine/code_path_runner.py` — context BLOCK; measures explícitas; sin bypass REQUIRED
- `extensions/wordflow/standards/gap_registry.py` — campos completos + new_gaps_after_fix

## Rules
- NO VERIFIED CONTEXT → NO PROGRAMMING / NO AUDIT
- CLAIM ≠ EVIDENCE ≠ VERIFICATION ≠ PASS
- required_without_handler = FAIL
- required_skip = FAIL
- skip != pass
- OPEN → CLOSED forbidden
- all_four_passes_required = true
- no_dev_bypass_required = true

## PASS only if
context_verified AND handoff_verified AND CORE14 AND 4 passes AND counters all 0 AND evidence_complete AND final_clean_reaudit AND quality_dag_ok

## Caller must supply
- core_measures[CORE-01..14] = bool measured (default False)
- connectivity chain flags
- counters dict
- evidence_complete, final_clean_reaudit_passed, quality_dag_ok
