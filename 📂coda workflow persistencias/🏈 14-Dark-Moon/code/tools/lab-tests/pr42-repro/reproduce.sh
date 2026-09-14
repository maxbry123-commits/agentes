#!/usr/bin/env bash
set -euo pipefail
echo '{"schema":"yaiwes.internal.persistence/v1","source":"tools/lab-tests/pr42-repro/reproduce.sh","status":"CHECKPOINTED"}' >> "$(dirname "$0")/.yaiwes_internal_state.jsonl"
