# claude-code-B

**Rol**: verifier
**Backend**: Cerebras via LiteLLM (127.0.0.1:4000)
**Modelo**: cerebras-verifier

## Función
Verifica y corrige código. Usa cerebras/gpt-oss-120b (razonamiento medio).

## Identidad en el sistema
- ID: claude-code-B
- Memoria: claude-code-B/memory/
- Workspace: claude-code-B/workspace/
- Sandbox: claude-code-B/sandbox/

## Skills que puede usar
Solo las aprobadas por Skill Judge en /opt/nct/skills/vault/approved/

## Comandos (desde el VPS)
```

claude -p "revisar" --model cerebras-verifier --allowedTools "Read" --cwd /opt/nct/repos/agentes/claude-code-B/workspace


```
