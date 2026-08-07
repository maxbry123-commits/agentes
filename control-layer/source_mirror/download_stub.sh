#!/usr/bin/env bash
# W10 · plantilla descarga determinista (no ejecuta sin SHA esperado)
# Uso: ./download_stub.sh <url> <ref> <expected_sha> <dest>
set -euo pipefail
URL="${1:?url}"
REF="${2:?ref}"
EXPECT="${3:?sha}"
DEST="${4:?dest}"
mkdir -p "$(dirname "$DEST")"
if [[ ! -d "$DEST/.git" ]]; then
  git clone --depth 1 --branch "$REF" "$URL" "$DEST" || git clone --depth 1 "$URL" "$DEST"
  git -C "$DEST" checkout "$EXPECT" 2>/dev/null || true
fi
ACTUAL="$(git -C "$DEST" rev-parse HEAD)"
echo "[source_mirror] $DEST @ $ACTUAL (expect prefix $EXPECT)"
