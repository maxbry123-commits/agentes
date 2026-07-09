# mimo-code-vps-C

**Grupo**: C · **Tipo**: coder
**Binario**: `mimo`
**Modelo**: cerebras-coder
**Router**: http://127.0.0.1:4000/v1 (LiteLLM)

## Funcion
Backup coder (gemma-4-31b). Activado por el router cuando A esta ocupado.

## Comandos
```bash
mimo -p "tarea" --model cerebras-coder --allowedTools "Read,Write,Bash" --cwd /opt/nct/repos/agentes/mimo-code-vps-C/workspace
mimo -p "audita" --model cerebras-coder --allowedTools "Read"
```
