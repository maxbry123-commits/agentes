#!/usr/bin/env bash
# Cognithor Agent OS — Linux/macOS startup script
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "  COGNITHOR — Agent OS"
echo "  ===================="
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "  [FAIL] Python 3 not found. Install Python 3.12+."
    exit 1
fi
echo "  [OK] Python 3 found: $(python3 --version)"

# Check Ollama
if command -v ollama &>/dev/null; then
    echo "  [OK] Ollama available."
else
    echo "  [WARN] Ollama not found. Install from https://ollama.ai"
fi

# Check/install pysqlcipher3 (GDPR encryption at rest)
if python3 -c "import pysqlcipher3" 2>/dev/null; then
    echo "  [OK] pysqlcipher3 available."
else
    echo "  [INFO] Installing pysqlcipher3 for GDPR encryption..."
    # SQLCipher dev library required on Linux
    if command -v apt-get &>/dev/null; then
        echo "  [INFO] Installing libsqlcipher-dev (requires sudo)..."
        sudo apt-get install -y libsqlcipher-dev 2>/dev/null || true
    elif command -v brew &>/dev/null; then
        echo "  [INFO] Installing sqlcipher via Homebrew..."
        brew install sqlcipher 2>/dev/null || true
    fi
    pip install pysqlcipher3 2>/dev/null || {
        echo "  [WARN] pysqlcipher3 installation failed. Database encryption unavailable."
        echo "         On Ubuntu: sudo apt-get install libsqlcipher-dev && pip install pysqlcipher3"
        echo "         On macOS: brew install sqlcipher && pip install pysqlcipher3"
    }
fi

# Check SearXNG Docker container
if command -v docker &>/dev/null; then
    if docker ps -q -f "name=cognithor-searxng" 2>/dev/null | grep -q .; then
        echo "  [OK] SearXNG already running."
    else
        echo "  [INFO] Starting SearXNG..."
        docker start cognithor-searxng 2>/dev/null || echo "  [SKIP] SearXNG container not found."
    fi
else
    echo "  [SKIP] Docker not installed — SearXNG unavailable."
fi

echo ""
echo "  Starting Cognithor..."
echo ""

# Start the application
python3 -m jarvis "$@"
