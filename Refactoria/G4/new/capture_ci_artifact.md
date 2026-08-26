# G4 — CI evidence runbook

No GitHub Actions execution artifact was claimed or fabricated in this task.

Deterministic capture command from repository root:

```bash
gh run list --workflow test-wordflow-code-path.yml --branch main --limit 1
gh run view <RUN_ID> --log > despliegue/refactoria/G4/new/ci-run-<RUN_ID>.log
```

If the workflow is not present or no run exists, status remains OPEN. The resulting log must be committed only after an actual Actions run and must include the run ID and commit SHA.
