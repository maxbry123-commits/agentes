#!/usr/bin/env bash
# subir_a_github.sh v2 — 0% LLM
# SOURCE: DESPLIEGUE-DETERMINISTA-UNIVERSAL-v2 PASO 4
# Uso: bash subir_a_github.sh OWNER [repos_listos]
set -euo pipefail
OWNER="${1:?owner required}"
ROOT="${2:-repos_listos}"

if ! command -v gh >/dev/null 2>&1; then
  echo "gh CLI required" >&2
  exit 1
fi

for d in "$ROOT"/*; do
  [ -d "$d" ] || continue
  name=$(basename "$d")
  echo "==> $OWNER/$name"
  (
    cd "$d"
    if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
      git init
      git add -A
      git commit -m "deploy: init" || true
    fi
    if gh repo view "$OWNER/$name" >/dev/null 2>&1; then
      git remote remove origin 2>/dev/null || true
      git remote add origin "https://github.com/$OWNER/$name.git"
      git push -u origin HEAD || git push -u origin HEAD:main
    else
      gh repo create "$OWNER/$name" --private --source=. --remote=origin --push
    fi
  )
done
echo "done"
