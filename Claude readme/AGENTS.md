# AGENTS.md — maxbry123-commits/agentes

## Authority
- Work method: `PIPELINE/00_METODO_TRABAJO_Y_ARQUITECTURA.md`
- Forensic audit: `PIPELINE/FORENSIC_CODE_AUDIT.md`
- Engineering standard: `PIPELINE/ADVANCED_ENGINEERING_STANDARD_V3.md`
- Batch copy/move/deploy skill: `skills/wordflow-code-deploy-router/SKILL.md`

## Hard rules
- Handoff ≠ full traceability; missing context/handoff → BLOCK
- COPY-FIRST before GENERATE
- LLM cannot declare PASS; VerdictAuthority only
- GitHub is source of truth; no sandbox storage claims
- Any COPY, MOVE, MIRROR, cross-repo transfer, ZIP extraction-to-live-root, or GitHub Contents API file relocation MUST read `skills/wordflow-code-deploy-router/SKILL.md` and `skills/wordflow-code-deploy-router/references/BATCH-COPY-MOVE-SAFETY.md` before mutation.
- Never delete a source file for a move until the destination passes path/type/count/hash verification; for cross-repo moves, destination push must be verified first.

## Programming pipeline
`CONTEXT → COPY-FIRST → IMPLEMENT → WIRE → FORENSIC 4-PASS → VERDICT → CLOSED|FIX`

Code: `extensions/wordflow/engine/programming_pipeline.py`  
Gates: `extensions/wordflow/standards/executor_gates.py`
