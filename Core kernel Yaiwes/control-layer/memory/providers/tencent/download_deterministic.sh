#!/usr/bin/env bash
# Descarga determinista TencentDB-Agent-Memory @ v2.0.0 / 0aff21a
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
DEST="${ROOT}/sources/tencent/TencentDB-Agent-Memory"
URL="https://github.com/TencentCloud/TencentDB-Agent-Memory.git"
TAG="v2.0.0"
EXPECT_SHA="0aff21a2d9f2b8a0354aaa80a2e586aab4054562"

mkdir -p "$(dirname "$DEST")"
if [[ -d "$DEST/.git" ]]; then
  echo "[tencent] already present: $DEST"
else
  git clone --depth 1 --branch "$TAG" "$URL" "$DEST"
fi
ACTUAL="$(git -C "$DEST" rev-parse HEAD)"
if [[ "$ACTUAL" != "$EXPECT_SHA" ]]; then
  echo "[tencent] SHA mismatch: got $ACTUAL want $EXPECT_SHA" >&2
  exit 1
fi
echo "[tencent] OK $TAG @ $ACTUAL -> $DEST"
