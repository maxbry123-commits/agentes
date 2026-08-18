# AGENTS.md — maxbry123-commits/agentes

## Authority
- Work method: `PIPELINE/00_METODO_TRABAJO_Y_ARQUITECTURA.md`
- Forensic audit: `PIPELINE/FORENSIC_CODE_AUDIT.md`
- Engineering standard: `PIPELINE/ADVANCED_ENGINEERING_STANDARD_V3.md`

## Hard rules
- Handoff ≠ full traceability; missing context/handoff → BLOCK
- COPY-FIRST before GENERATE
- LLM cannot declare PASS; VerdictAuthority only
- GitHub is source of truth; no sandbox storage claims

## Programming pipeline
`CONTEXT → COPY-FIRST → IMPLEMENT → WIRE → FORENSIC 4-PASS → VERDICT → CLOSED|FIX`

Code: `extensions/wordflow/engine/programming_pipeline.py`  
Gates: `extensions/wordflow/standards/executor_gates.py`
