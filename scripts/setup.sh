#!/bin/bash
# setup.sh — Instalación completa del Orquestador Universal v1.0
# Uso: bash setup.sh

set -e
set -u

ORCH_HOME="${ORCH_HOME:-$(pwd)/orchestrator-universal}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

echo "============================================================"
echo "  Orquestador Universal v1.0 — Setup"
echo "============================================================"
echo ""
echo "Directorio de instalación: $ORCH_HOME"
echo "Python: $PYTHON_BIN"
echo ""

# 1. Verificar Python
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    echo "ERROR: $PYTHON_BIN no encontrado. Instala Python 3.11+ primero."
    exit 1
fi

PY_VERSION=$($PYTHON_BIN --version 2>&1 | awk '{print $2}')
echo "  Python detectado: $PY_VERSION"

# 2. Verificar Docker (opcional pero recomendado)
HAS_DOCKER=0
if command -v docker >/dev/null 2>&1; then
    HAS_DOCKER=1
    echo "  Docker: $(docker --version)"
else
    echo "  Docker: NO detectado (los sandboxes no funcionarán sin docker)"
    echo "          Instálalo con: curl -fsSL https://get.docker.com | sh"
fi

# 3. Crear venv
echo ""
echo "[1/5] Creando entorno virtual..."
if [ ! -d "$ORCH_HOME/venv" ]; then
    cd "$ORCH_HOME"
    $PYTHON_BIN -m venv venv
    echo "  venv creado en $ORCH_HOME/venv"
else
    echo "  venv ya existe, saltando"
fi

# 4. Instalar dependencias
echo ""
echo "[2/5] Instalando dependencias Python..."
cd "$ORCH_HOME"
source venv/bin/activate
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
echo "  Dependencias instaladas"

# 5. Correr tests
echo ""
echo "[3/5] Corriendo tests (sin docker)..."
SKIP_DOCKER_TESTS=1 python -m pytest tests/test_mvp.py -v --tb=short 2>&1 | tail -10

# 6. Build de imágenes Docker (si docker está disponible)
if [ $HAS_DOCKER -eq 1 ]; then
    echo ""
    echo "[4/5] Construyendo imágenes Docker de los sandboxes..."
    docker build -f dockerfiles/claude_code.dockerfile -t claude-code-sandbox:latest .
    docker build -f dockerfiles/mimo_code.dockerfile   -t mimo-code-sandbox:latest   .
    docker build -f dockerfiles/opencode.dockerfile    -t opencode-sandbox:latest    .
    echo "  Imágenes construidas: claude-code-sandbox, mimo-code-sandbox, opencode-sandbox"

    echo ""
    echo "[5/5] Smoke test con docker (requiere docker-compose)..."
    if command -v docker-compose >/dev/null 2>&1 || docker compose version >/dev/null 2>&1; then
        docker compose up -d
        sleep 3
        docker compose ps
        echo ""
        echo "  Corriendo demo contra los sandboxes..."
        python main.py --demo --consensus fast
        echo ""
        echo "  Apagando sandboxes..."
        docker compose down
    else
        echo "  docker-compose no detectado, saltando smoke test"
    fi
else
    echo ""
    echo "[4/5] Saltando build de imágenes (sin docker)"
    echo "[5/5] Saltando smoke test (sin docker)"
fi

echo ""
echo "============================================================"
echo "  Setup completo"
echo "============================================================"
echo ""
echo "Para usar:"
echo "  cd $ORCH_HOME"
echo "  source venv/bin/activate"
echo "  python main.py --demo"
echo "  python main.py --template mi_template.json"
echo ""
echo "Para deploy real con sandboxes:"
echo "  docker compose up -d"
echo "  python main.py --demo"
echo "  docker compose down"
