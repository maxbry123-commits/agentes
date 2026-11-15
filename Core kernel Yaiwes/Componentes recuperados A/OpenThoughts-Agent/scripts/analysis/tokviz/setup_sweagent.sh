#!/usr/bin/env bash
# setup_sweagent.sh -- install SWE-agent from source into its OWN conda env.
#
# STRICT: swe-agent must NEVER be installed into otagent. This creates a
# standalone `sweagent` conda env (python 3.11) and installs SWE-agent there
# from source.
#
# Usage:
#   bash setup_sweagent.sh
#
# After this completes, the agentic half uses:
#   /Users/benjaminfeuer/miniconda3/envs/sweagent/bin/sweagent ...
set -euo pipefail

ENV_NAME="sweagent"
CLONE_DIR="${TOKVIZ_SWEAGENT_DIR:-$HOME/SWE-agent}"
CONDA_BASE="$(conda info --base 2>/dev/null || echo "$HOME/miniconda3")"
PY="$CONDA_BASE/envs/$ENV_NAME/bin/python"

echo "==> Creating conda env '$ENV_NAME' (python 3.11) if missing"
if ! conda env list | grep -qE "^\s*$ENV_NAME\s"; then
  conda create -y -n "$ENV_NAME" python=3.11
fi

echo "==> Cloning SWE-agent into $CLONE_DIR (if missing)"
if [ ! -d "$CLONE_DIR/.git" ]; then
  git clone https://github.com/SWE-agent/SWE-agent.git "$CLONE_DIR"
fi

echo "==> pip install -e SWE-agent into $ENV_NAME"
"$PY" -m pip install -e "$CLONE_DIR"

echo "==> Verifying install"
"$PY" -c "import sweagent; print('swe-agent', getattr(sweagent, '__version__', '?'))"

echo
echo "DONE. swe-agent installed in env '$ENV_NAME'."
echo "Docker is required by swe-agent's default execution backend."
if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
  echo "Docker: AVAILABLE and running."
else
  echo "Docker: NOT available/running -- the agentic run step will need Docker."
fi
