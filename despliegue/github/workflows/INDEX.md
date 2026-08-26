# Índice de workflows GitHub (punteros — no ejecutable aquí)

GitHub solo ejecuta archivos bajo `.github/workflows/`.

| Workflow en .github/workflows | Uso aproximado |
|-------------------------------|----------------|
| [test-wordflow-code-path.yml](../../../.github/workflows/test-wordflow-code-path.yml) | tests path C-19 / wordflow |
| [test-wordflow.yml](../../../.github/workflows/test-wordflow.yml) | tests wordflow |
| [wordflow-full-verification.yml](../../../.github/workflows/wordflow-full-verification.yml) | verificación full |
| [wordflow_smoke.yml](../../../.github/workflows/wordflow_smoke.yml) | smoke |
| [forensic-gates.yml](../../../.github/workflows/forensic-gates.yml) | puertas forenses |
| [test-audit-forensic.yml](../../../.github/workflows/test-audit-forensic.yml) | audit forensic |
| [test-control-layer.yml](../../../.github/workflows/test-control-layer.yml) | control-layer |
| [test-github-publisher.yml](../../../.github/workflows/test-github-publisher.yml) | github publisher |
| [test-project-bootstrap.yml](../../../.github/workflows/test-project-bootstrap.yml) | project bootstrap |
| [test-source-evolution.yml](../../../.github/workflows/test-source-evolution.yml) | source evolution |
| [deterministic-build.yml](../../../.github/workflows/deterministic-build.yml) | build determinista |
| [validate-external-github.yml](../../../.github/workflows/validate-external-github.yml) | validación externa |
| [check-external-token-secret.yml](../../../.github/workflows/check-external-token-secret.yml) | token secret check |
| [acquire-codex.yml](../../../.github/workflows/acquire-codex.yml) | acquire codex |
| [acquire-codex-v21.yml](../../../.github/workflows/acquire-codex-v21.yml) | acquire codex v21 |
| [acquire-hermes.yml](../../../.github/workflows/acquire-hermes.yml) | acquire hermes |
| [acquire-openclaw.yml](../../../.github/workflows/acquire-openclaw.yml) | acquire openclaw |
| [a5-codex.yml](../../../.github/workflows/a5-codex.yml) | a5 codex |
| [a5-codex-meta.yml](../../../.github/workflows/a5-codex-meta.yml) | a5 codex meta |
| [a5-codex-finalize.yml](../../../.github/workflows/a5-codex-finalize.yml) | a5 finalize |
| [codex-meta.yml](../../../.github/workflows/codex-meta.yml) | codex meta |
| [create-cuenta-b-repo.yml](../../../.github/workflows/create-cuenta-b-repo.yml) | cuenta B |
| [phase1_restore_arquitectura_real.yml](../../../.github/workflows/phase1_restore_arquitectura_real.yml) | restore arquitectura |
| [purge-agents-root.yml](../../../.github/workflows/purge-agents-root.yml) | purge agents root |
| [purge-agents.yml](../../../.github/workflows/purge-agents.yml) | purge agents |
| [purge-openclaw-only.yml](../../../.github/workflows/purge-openclaw-only.yml) | purge openclaw |

Cuando se añada un `deploy_c0.yml` / `validate_c0.yml` / `recovery_c0.yml` operativo, debe crearse en **`.github/workflows/`** y registrarse aquí como puntero. La lógica declarativa y evidencia van en `despliegue/manifests`, `schemas`, `validators`, `auditoria`.
