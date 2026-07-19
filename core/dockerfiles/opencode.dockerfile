FROM python:3.11-slim

LABEL maintainer="Mavis <max@orchestrator.local>"
LABEL description="Sandbox aislado para OpenCode agent (fallback/consensus)"
LABEL orchestrator.role="opencode"
LABEL orchestrator.loops="L2_consensus_plan,L3_assign_sandboxes"

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

# OpenCode CLI (shim — reemplazar con binario real)
RUN cat > /usr/local/bin/opencode <<'SHIM'
#!/bin/sh
# OpenCode shim — reemplazar con binario real en producción
PROMPT=""
while [ $# -gt 0 ]; do
    case "$1" in
        run) shift ;;
        *) PROMPT="$1"; shift ;;
    esac
done
echo "OpenCode processing: $PROMPT"
echo "--- a/file.py"
echo "+++ b/file.py"
echo "@@ -1,1 +1,1 @@"
echo "-# old"
echo "+# opencode-output"
SHIM
RUN chmod +x /usr/local/bin/opencode

WORKDIR /work
RUN git init -q . 2>/dev/null || true

CMD ["sleep", "infinity"]
