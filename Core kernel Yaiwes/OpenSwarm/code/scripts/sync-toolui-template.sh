#!/usr/bin/env bash
# Vendors the tool-ui component system into the app template (ENG-203).
# frontend/src/toolui is the single source of truth; the copy under
# webapp_template is GENERATED — never hand-edit it, rerun this instead.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$ROOT/frontend/src/toolui"
DST="$ROOT/backend/apps/outputs/webapp_template/frontend/src/toolui"

rm -rf "$DST"
mkdir -p "$DST"
# node_modules never exists inside src/toolui, so a straight copy is fine.
cp -R "$SRC/" "$DST/"

cat > "$DST/GENERATED.md" <<'EOF'
This directory is a GENERATED copy of OpenSwarm's `frontend/src/toolui`
(vendored per app template so generated apps can use the tool-ui components).
Do not hand-edit; run `scripts/sync-toolui-template.sh` from the OpenSwarm
repo root to refresh it.
EOF

echo "Synced $(find "$DST" -type f | wc -l | tr -d ' ') files into the template."
