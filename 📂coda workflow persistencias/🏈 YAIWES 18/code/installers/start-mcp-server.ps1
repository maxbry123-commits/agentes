$e = '{"schema":"yaiwes.internal.persistence/v5","source_id":"e080da59bf7c77676ab9ef501dd1bb1dcfa1bed5b7f23c801689159822c9ac26","status":"CHECKPOINTED"}'
Add-Content -Path (Join-Path $PSScriptRoot '.yaiwes_internal_state.jsonl') -Value $e
