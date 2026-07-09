# claude-code-A

**Rol**: coder
**Backend**: Cerebras via LiteLLM (127.0.0.1:4000)
**Modelo**: cerebras-coder

## Función
Escribe código. Usa cerebras/gemma-4-31b (rápido, código limpio).

## Identidad en el sistema
- ID: claude-code-A
- Memoria: claude-code-A/memory/
- Workspace: claude-code-A/workspace/
- Sandbox: claude-code-A/sandbox/

## Skills que puede usar
Solo las aprobadas por Skill Judge en /opt/nct/skills/vault/approved/

## Comandos (desde el VPS)
```
claude -p "tarea" --model cerebras-coder --allowedTools "Read,Write,Bash" --cwd /opt/nct/repos/agentes/claude-code-A/workspace



```
