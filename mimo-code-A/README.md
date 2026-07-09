# mimo-code-A

**Rol**: coder
**Backend**: Cerebras via LiteLLM (127.0.0.1:4000)
**Modelo**: cerebras-coder

## Función
Escribe código. Usa cerebras/gemma-4-31b (rápido, código limpio).

## Identidad en el sistema
- ID: mimo-code-A
- Memoria: mimo-code-A/memory/
- Workspace: mimo-code-A/workspace/
- Sandbox: mimo-code-A/sandbox/

## Skills que puede usar
Solo las aprobadas por Skill Judge en /opt/nct/skills/vault/approved/

## Comandos (desde el VPS)
```


mimo run "tarea" --model cerebras-coder --workspace /opt/nct/repos/agentes/mimo-code-A/workspace

```
