FROM python:3.11-slim

LABEL maintainer="Mavis <max@orchestrator.local>"
LABEL description="Sandbox aislado para Claude Code agent"
LABEL orchestrator.role="claude_code"
LABEL orchestrator.loop="L4_execute"

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC
ENV PYTHONUNBUFFERED=1
ENV PATH="/root/.local/bin:${PATH}"

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip

# Claude Code CLI (placeholder — ajusta con el binario real de tu setup)
# Si usas claude-code-sdk:
# RUN pip install claude-code-sdk
# Si usas CLI nativo, copia el binario en build:
# COPY claude /usr/local/bin/claude
# RUN chmod +x /usr/local/bin/claude

# Si aún no tienes el binario real, instala un shim que se puede reemplazar luego
RUN cat > /usr/local/bin/claude <<'SHIM'
#!/bin/sh
# Claude Code shim — reemplazar con binario real en producción
# Acepta: --print --cwd <path> --prompt <text>
PROMPT=""
CWD="."
while [ $# -gt 0 ]; do
    case "$1" in
        --print) shift ;;
        --cwd) CWD="$2"; shift 2 ;;
        --prompt) PROMPT="$2"; shift 2 ;;
        *) shift ;;
    esac
done
echo "--- a/file.py"
echo "+++ b/file.py"
echo "@@ -1,1 +1,1 @@"
echo "-# old"
echo "+# new: $PROMPT"
SHIM
RUN chmod +x /usr/local/bin/claude

WORKDIR /work
RUN git init -q . 2>/dev/null || true

# El contenedor se mantiene vivo para que el orquestador le inyecte comandos
CMD ["sleep", "infinity"]
