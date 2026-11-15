#!/bin/bash
set -e  # Stoppt bei erstem Fehler

echo "=== Ruff Lint ==="
ruff check src/ tests/ --fix

echo "=== Ruff Format ==="
ruff format src/ tests/

echo "=== Tests ==="
pytest tests/ -x --tb=short -q --ignore=tests/test_channels/test_voice_ws_bridge.py 2>&1 | tee test_results.txt

echo "=== Fertig ==="
