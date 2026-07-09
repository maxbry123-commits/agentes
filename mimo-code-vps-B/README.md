# mimo-code-vps-B

**Grupo**: B · **Tipo**: verifier
**Binario**: `mimo`
**Modelo**: cerebras-verifier (gpt-oss-120b)
**Router**: http://127.0.0.1:4000/v1 (LiteLLM)

## Función
Verifica y corrige código. Cerebras gpt-oss-120b (razonamiento medio).

## Comandos directos
```bash
# Coder (escribe)
mimo -p "tarea aqui" --model cerebras-verifier (gpt-oss-120b) --allowedTools "Read,Write,Bash" --cwd /opt/nct/repos/agentes/mimo-code-vps-B/workspace

# Verifier (audita)
mimo -p "audita X. Lista 3 puntos OK/BUG. No modifiques." --model cerebras-verifier (gpt-oss-120b) --allowedTools "Read"
```

## Memoria
SQLite en `/opt/nct/memory/mimo-code-vps-B/state.db` (permisos 600).

## Skills
Consulta `/opt/nct/skills/vault/approved/` (Skill Router).

## Estado
```json
{
  "id": "mimo-code-vps-B",
  "rol": "verifier",
  "modelo": "cerebras-verifier",
  "backend": "Cerebras via LiteLLM 127.0.0.1:4000",
  "endpoint": "http://127.0.0.1:4000/v1",
  "memoria_db": "/opt/nct/memory/mimo-code-B/state.db",
  "workspace": "/opt/nct/repos/agentes/mimo-code-B/workspace",
  "sandbox": "/opt/nct/repos/agentes/mimo-code-B/sandbox",
  "skills_source": "/opt/nct/skills/vault/approved",
  "created": "2026-07-09T09:28:00Z",
  "status": "ready",
  "grupo": "B",
  "modelo_router": "cerebras-verifier",
  "modelo_real_cerebras": "gpt-oss-120b",
  "router_endpoint": "http://127.0.0.1:4000/v1",
  "openclaw_endpoint": "http://127.0.0.1:18789/v1",
  "version": "1.1.0",
  "last_heartbeat": null,
  "memory_db": "/opt/nct/memory/mimo-code-vps-B/state.db"
}
```
