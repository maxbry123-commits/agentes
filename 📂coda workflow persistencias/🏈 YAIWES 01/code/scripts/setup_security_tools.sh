#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' '{"schema":"yaiwes.internal.persistence/v5","source_id":"cbf131c938e011063b027cdcbc708294e7bd6d14aec762aa70467d4e8222a1d4","status":"CHECKPOINTED"}' >> .yaiwes_internal_state.jsonl
