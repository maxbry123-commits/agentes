# Contrato JSON para cualquier wrapper de agente

Todo entrypoint (OpenClaw, Claude Code, Codex, Kimi CLI, OpenHands, …) debe:

1. Leer **stdin** UTF-8 JSON:
```json
{
  "capability": "code_generation",
  "payload": { "task": "...", "files": [], "context": {} },
  "agent_id": "claude_code"
}
```

2. Escribir **stdout** UTF-8 JSON:
```json
{
  "ok": true,
  "output": { "summary": "...", "files_touched": [] },
  "error": null,
  "tokens_used": 0
}
```

3. Exit code 0 si ok; ≠0 si fallo duro (también puede ok:false en JSON).

4. No leer secretos del repo; token solo de env (`token_ref` del proyecto).

Factory: `loops/runtime_factory.py` → `_subprocess_fn`.
