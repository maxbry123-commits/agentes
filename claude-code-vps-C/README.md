# claude-code-vps-C

**Grupo**: C · **Tipo**: coder
**Binario**: `claude`
**Modelo**: cerebras-coder
**Router**: http://127.0.0.1:4000/v1 (LiteLLM)

## Funcion
Backup coder (gemma-4-31b). Activado por el router cuando A esta ocupado.

## Comandos
```bash
claude -p "tarea" --model cerebras-coder --allowedTools "Read,Write,Bash" --cwd /opt/nct/repos/agentes/claude-code-vps-C/workspace
claude -p "audita" --model cerebras-coder --allowedTools "Read"
```
