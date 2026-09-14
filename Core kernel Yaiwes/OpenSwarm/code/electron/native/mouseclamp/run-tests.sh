#!/bin/bash
# Compile + run the clamp_decision property test (plain clang, no electron deps).
set -euo pipefail
if ! command -v clang >/dev/null 2>&1; then
  echo "clang not found; skipping clamp_decision property test"; exit 0
fi
HERE="$(cd "$(dirname "$0")" && pwd)"
BIN="$(mktemp -t clamp_decision_test)"
trap 'rm -f "$BIN"' EXIT
clang -O2 -Wall -Wextra -Werror -o "$BIN" "$HERE/clamp_decision_test.c"
"$BIN"
