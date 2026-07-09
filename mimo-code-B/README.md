# mimo-code-B

**Rol**: verifier
**Backend**: Cerebras via LiteLLM (127.0.0.1:4000)
**Modelo**: cerebras-verifier

## Función
Verifica y corrige código. Usa cerebras/gpt-oss-120b (razonamiento medio).

## Identidad en el sistema
- ID: mimo-code-B
- Memoria: mimo-code-B/memory/
- Workspace: mimo-code-B/workspace/
- Sandbox: mimo-code-B/sandbox/

## Skills que puede usar
Solo las aprobadas por Skill Judge en /opt/nct/skills/vault/approved/

## Comandos (desde el VPS)
```



mimo run "revisar" --model cerebras-verifier --workspace /opt/nct/repos/agentes/mimo-code-B/workspace
```
