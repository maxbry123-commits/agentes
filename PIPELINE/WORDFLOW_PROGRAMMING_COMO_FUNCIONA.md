# Cómo funciona el Wordflow de programación (ENFORCEMENT 100%)

## Entrada crítica
`run_code_path(..., context_verified=True, handoff_verified=True, core_measures={...}, connectivity={...}, counters={...}, evidence_complete=True, final_clean_reaudit_passed=True, quality_dag_ok=True)`

Sin context/handoff verificados → **BLOCK** (no ejecución de programming path).

Sin medidas CORE explícitas → cada CORE default **False** → **FAIL** (required_without_handler).

## Motor
`ForensicProgrammingEnforcer.evaluate`:
1. require_context
2. CORE-01..14 todos pass
3. 4 passes en orden (STRUCTURE→CONNECTIVITY→BEHAVIOR→FORENSIC_CLOSURE); fail corta la cadena de éxito
4. counters todos 0 incluyendo new_gaps_after_fix y unexpected_changes
5. evidence_complete + final_clean_reaudit
6. quality_dag_ok (skip≠pass)
7. claim_used_as_pass prohibido

## Conectividad requerida
DECLARED→REGISTERED→RESOLVED→INVOKED→EXECUTED→OUTPUT_CONSUMED→BEHAVIOR_VERIFIED

## Gaps
GapRegistry: gap_id, severity, description, location, root_cause, required_fix, implemented_fix, verification, evidence, status, revisions. OPEN→FIXED→VERIFIED→CLOSED only.

## No existe
Flag de desarrollo que desactive un gate REQUIRED.

Ver: `PIPELINE/FORENSIC_ENFORCEMENT_REQUIRED.md`
