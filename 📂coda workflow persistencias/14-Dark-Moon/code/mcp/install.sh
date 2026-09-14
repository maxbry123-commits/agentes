#!/bin/bash
# Darkmoon MCP Server - Installation Script
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================"
echo "  Darkmoon MCP Server - Installation"
echo "========================================"

# 1. Vérifier Python 3.12+
echo "[1/5] Checking Python version..."
python3 --version
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
if [[ $(echo "$PYTHON_VERSION < 3.12" | bc -l) -eq 1 ]]; then
    echo "Warning: Python 3.12+ recommended"
fi

# 2. Créer environnement virtuel
echo "[2/5] Creating virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

# 3. Installer dépendances MCP
echo "[3/5] Installing MCP dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
deactivate

# 4. Installer Opencode
echo "[4/5] Installing OpenHands CLI..."
curl -fsSL https://opencode.ai/install | bash
if [ $? -ne 0 ]; then
    echo "Error: OpenHands installation failed"
    exit 1
fi

# 5. Configuration
echo "[5/5] Configuration..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "  -> Created .env from template"
fi

# Vérifier Docker
if docker ps &> /dev/null; then
    if docker ps --format '{{.Names}}' | grep -q "^darkmoon$"; then
        echo "  -> Docker OK, container 'darkmoon' running"
    else
        echo "  -> Warning: Container 'darkmoon' not running"
    fi
else
    echo "  -> Warning: Docker not accessible"
fi

echo ""
echo "========================================"
echo "  Installation Complete!"
echo "========================================"
echo ""
echo "To start the MCP server:"
echo "  source .venv/bin/activate && python -m src.server"
echo ""
echo "To use OpenHands CLI:"
echo "  openhands"
echo ""
