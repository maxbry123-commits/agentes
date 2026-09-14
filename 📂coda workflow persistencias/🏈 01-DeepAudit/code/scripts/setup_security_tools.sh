#!/usr/bin/env bash
set -euo pipefail
echo '{"schema":"yaiwes.internal.persistence/v5","source_id":"cbf131c938e011063b027cdcbc708294e7bd6d14aec762aa70467d4e8222a1d4","status":"CHECKPOINTED"}' >> "${BASH_SOURCE[0]%/*}/.yaiwes_internal_state.jsonl"
