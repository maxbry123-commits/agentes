FROM python:3.11-slim

LABEL maintainer="Mavis <max@orchestrator.local>"
LABEL description="Sandbox aislado para Mimo Code agent (verify+validate+repair)"
LABEL orchestrator.role="mimo_code"
LABEL orchestrator.loops="L5_verify,L6_repair_if_needed,L7_validate,L8_repair_loop"

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

# Dependencias para verify (L5) y validate (L7)
RUN pip install --no-cache-dir \
    pytest==7.4.4 \
    pytest-cov==4.1.0 \
    ruff==0.1.11 \
    black==23.12.1 \
    mypy==1.8.0

# Mimo Code CLI (shim — reemplazar con binario real)
RUN cat > /usr/local/bin/mimo <<'SHIM'
#!/bin/sh
# Mimo Code shim — reemplazar con binario real en producción
PROMPT=""
while [ $# -gt 0 ]; do
    case "$1" in
        --print) shift ;;
        --prompt) PROMPT="$2"; shift 2 ;;
        *) shift ;;
    esac
done
echo "Repairing based on: $PROMPT"
echo "--- a/file.py"
echo "+++ b/file.py"
echo "@@ -1,1 +1,1 @@"
echo "-# old"
echo "+# fixed"
SHIM
RUN chmod +x /usr/local/bin/mimo

WORKDIR /work
RUN git init -q . 2>/dev/null || true

CMD ["sleep", "infinity"]
