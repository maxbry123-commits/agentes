# PIPELINE 08b — APPLY → COMMIT → PUSH (100% code)

**Fecha:** 2026-08-19  
**Regla:** el agente no decide. Solo entrega dest + account_id + token_ref + files.

## Entrada del agente

```json
{
  "apply": true,
  "account_id": "github_b",
  "token_ref": "env:GITHUB_B_TOKEN",
  "dest": {"provider": "github", "owner": "CUENTA_B", "repo": "cualquier-repo", "branch": "main"},
  "files": [{"path": "pkg/a.py", "content": "..."}],
  "commit_message": "wordflow apply",
  "expected_head": null
}
```

HF: `"provider": "huggingface"` + `token_ref: "env:HF_TOKEN"`.

Prohibido: pegar `ghp_` / `hf_` en el payload. Solo `env:NOMBRE`.

## Qué hace Wordflow (fijo)

1. locate_phase  
2. phase_plan.json si `apply=true`  
3. `check_protected` → HOLD  
4. AccountResolver (cuenta B = cualquier repo si allow-list vacía)  
5. resolve token_ref  
6. Git Data API blob→tree→commit→ref (`force=false`)  
7. `evidence.json` sin secretos  

Real push: `GITHUB_DEPLOY_REAL=1` + env del token.  
Real HF: `HF_DEPLOY_REAL=1`.  
Sin eso: `DRY_RUN` (git_apply true, published false).

## Código

- `extensions/github_deploy/apply_push.py`
- ingest: `wordflow_kernel.reception.convert.ingest(..., dest=, account_id=, files=, token_ref=)`

**No C100.** Este archivo no es evidencia de tests corridos.
