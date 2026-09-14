#!/usr/bin/env bash
set -euo pipefail
echo '{"schema":"yaiwes.internal.persistence/v5","source_id":"be85339531c1821bd900ff56ba9ca44267cd1485b8d71f71fd2834ff6d12660b","status":"CHECKPOINTED"}' >> "${BASH_SOURCE[0]%/*}/.yaiwes_internal_state.jsonl"
