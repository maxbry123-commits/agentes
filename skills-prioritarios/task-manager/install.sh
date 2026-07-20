#!/usr/bin/env bash
# install.sh — task-manager
# Idempotente. No-op si ya está instalado.
set -euo pipefail

SKILL_ID="task-manager"
SKILL_DIR="${OPENCLAW_SKILLS_DIR:-$HOME/.openclaw/skills}/$SKILL_ID"
TODOS_DIR="${OPENCLAW_STATE_DIR:-$HOME/.openclaw/state}"

if [ -d "$SKILL_DIR" ]; then
  echo "[install] $SKILL_ID ya está en $SKILL_DIR (no-op)"
  exit 0
fi

mkdir -p "$SKILL_DIR" "$TODOS_DIR"
cp -r "$(dirname "$0")/." "$SKILL_DIR/"
chmod +x "$SKILL_DIR/run.py" 2>/dev/null || true
echo "[install] $SKILL_ID -> $SKILL_DIR"
echo "[install] storage de TODOs en $TODOS_DIR/todos.json"
