#!/bin/sh

# Script to run the GitHub API scripts with correct paths
SCRIPT_DIR=$(dirname "$0")
cd "$SCRIPT_DIR"

echo "=== GitHub API Test ==="
python3 test_github_api.py

echo ""
echo "=== GitHub Repository and Issues Collector ==="
python3 swebench_get_repo.py
