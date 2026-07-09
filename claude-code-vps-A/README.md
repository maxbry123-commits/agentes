# claude-code-vps-A

**Grupo**: A · **Tipo**: coder
**Binario**: `claude`
**Modelo**: cerebras-coder (gemma-4-31b)
**Router**: http://127.0.0.1:4000/v1 (LiteLLM)

## Función
Escribe código. Cerebras gemma-4-31b (rápido, código limpio).

## Comandos directos
```bash
# Coder (escribe)
claude -p "tarea aqui" --model cerebras-coder (gemma-4-31b) --allowedTools "Read,Write,Bash" --cwd /opt/nct/repos/agentes/claude-code-vps-A/workspace

# Verifier (audita)
claude -p "audita X. Lista 3 puntos OK/BUG. No modifiques." --model cerebras-coder (gemma-4-31b) --allowedTools "Read"
```

## Memoria
SQLite en `/opt/nct/memory/claude-code-vps-A/state.db` (permisos 600).

## Skills
Consulta `/opt/nct/skills/vault/approved/` (Skill Router).

## Estado
```json
{
  "id": "claude-code-vps-A",
  "rol": "coder",
  "modelo": "cerebras-coder",
  "backend": "Cerebras via LiteLLM 127.0.0.1:4000",
  "endpoint": "http://127.0.0.1:4000/v1",
  "memoria_db": "/opt/nct/memory/claude-code-A/state.db",
  "workspace": "/opt/nct/repos/agentes/claude-code-A/workspace",
  "sandbox": "/opt/nct/repos/agentes/claude-code-A/sandbox",
  "skills_source": "/opt/nct/skills/vault/approved",
  "created": "2026-07-09T09:28:00Z",
  "status": "ready",
  "grupo": "A",
  "modelo_router": "cerebras-coder",
  "modelo_real_cerebras": "gemma-4-31b",
  "router_endpoint": "http://127.0.0.1:4000/v1",
  "openclaw_endpoint": "http://127.0.0.1:18789/v1",
  "version": "1.1.0",
  "last_heartbeat": null,
  "memory_db": "/opt/nct/memory/claude-code-vps-A/state.db"
}
```
