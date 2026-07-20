#!/usr/bin/env bash
# install.sh — test-runner
set -euo pipefail
SKILL_ID="test-runner"
SKILL_DIR="${OPENCLAW_SKILLS_DIR:-$HOME/.openclaw/skills}/$SKILL_ID"
[ -d "$SKILL_DIR" ] && { echo "[install] $SKILL_ID ya instalado"; exit 0; }
mkdir -p "$SKILL_DIR"
cp -r "$(dirname "$0")/." "$SKILL_DIR/"
chmod +x "$SKILL_DIR/run.py" 2>/dev/null || true
echo "[install] $SKILL_ID -> $SKILL_DIR"
