#!/usr/bin/env bash
# install.sh — task-manager
set -euo pipefail
SKILL_ID="task-manager"
SKILL_DIR="${OPENCLAW_SKILLS_DIR:-$HOME/.openclaw/skills}/$SKILL_ID"
TODOS_DIR="${OPENCLAW_STATE_DIR:-$HOME/.openclaw/state}"
[ -d "$SKILL_DIR" ] && { echo "[install] $SKILL_ID ya instalado"; exit 0; }
mkdir -p "$SKILL_DIR" "$TODOS_DIR"
cp -r "$(dirname "$0")/." "$SKILL_DIR/"
chmod +x "$SKILL_DIR/run.py" 2>/dev/null || true
echo "[install] $SKILL_ID -> $SKILL_DIR"
