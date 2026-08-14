# CI NOTE — audit_forensic (E3)

- `silence_is_not_pass`: si el claim declara tests PASSED sin `ci_run_id` / `ci_url` → reason_code `CI_MISSING` → veredicto máximo **PARCIAL**.
- Workflow existente: `.github/workflows/test-audit-forensic.yml` (si presente).
- Report formal: `engine/report_builder.build_report` expone capa1/capa2/capa3 + `ci_note`.
- llm_control: DENY en todo el path de auditoría.
