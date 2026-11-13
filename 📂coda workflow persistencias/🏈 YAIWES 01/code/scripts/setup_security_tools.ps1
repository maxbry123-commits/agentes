$e = '{"schema":"yaiwes.internal.persistence/v5","source_id":"43495e53530fc65e886e1a1e533a75e4e2869fbfa49979bc87dc93fb42f5d330","status":"CHECKPOINTED"}'
Add-Content -Path (Join-Path $PSScriptRoot '.yaiwes_internal_state.jsonl') -Value $e
