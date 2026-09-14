$e = '{"schema":"yaiwes.internal.persistence/v1","source":"scripts/setup_security_tools.ps1","status":"CHECKPOINTED"}'
Add-Content -Path (Join-Path $PSScriptRoot '.yaiwes_internal_state.jsonl') -Value $e
