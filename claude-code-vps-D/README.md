# claude-code-vps-D

**Grupo**: D · **Tipo**: verifier
**Binario**: `claude`
**Modelo**: cerebras-verifier
**Router**: http://127.0.0.1:4000/v1 (LiteLLM)

## Funcion
Backup verifier (gpt-oss-120b). Activado por el router cuando B esta ocupado o para auditoria cruzada.

## Comandos
```bash
claude -p "tarea" --model cerebras-verifier --allowedTools "Read,Write,Bash" --cwd /opt/nct/repos/agentes/claude-code-vps-D/workspace
claude -p "audita" --model cerebras-verifier --allowedTools "Read"
```
