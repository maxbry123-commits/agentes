#!/usr/bin/env bash
set -euo pipefail

if [ -f .env ]; then
  set -a
  . ./.env
  set +a
fi

MODEL="${MODEL:-deepseek-v4-flash}"
# MODE="${MODE:-all}"
MODE="${MODE:-bayesian-full}"
BENCH="${BENCH:-core}"
GENERICAGENT_ROOT="${GENERICAGENT_ROOT:-../GenericAgent}"
PYTHON_BIN="${PYTHON_BIN:-$GENERICAGENT_ROOT/.venv/bin/python}"

CMD=(
  "$PYTHON_BIN"
  experiments/run_benchmarks.py
  --genericagent-root "$GENERICAGENT_ROOT"
  --model "$MODEL"
  --mode "$MODE"
  --bench "$BENCH"
)
if [ -n "${OUT_ROOT:-}" ]; then
  CMD+=(--out-root "$OUT_ROOT")
fi
CMD+=("$@")

"${CMD[@]}"
