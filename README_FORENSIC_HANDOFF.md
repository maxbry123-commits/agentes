# Handoff / Context — Regla obligatoria

```yaml
HANDOFF_RULE:
  handoff_is_not_full_traceability: true
  required_before_programming:
    - project_context_documents
    - work_method_reference
    - verified_handoff
  if_missing: BLOCK
  agent_may_not:
    - start_programming
    - declare_valid_audit
```

Sin Context + método de trabajo + Handoff verificado → el agente no programa ni declara auditoría válida.

Ver: PIPELINE/FORENSIC_CODE_AUDIT.md · PIPELINE/00_METODO_TRABAJO_Y_ARQUITECTURA.md
