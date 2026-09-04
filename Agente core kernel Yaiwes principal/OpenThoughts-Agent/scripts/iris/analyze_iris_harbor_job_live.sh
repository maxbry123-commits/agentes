#!/usr/bin/env bash
# Refresh and report one active Iris Harbor datagen/eval job using its shared bundle.
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "usage: analyze_iris_harbor_job_live.sh /<user>/<job> [watch_iris_harbor.py options]" >&2
  exit 64
fi

JOB_ID="$1"
shift
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
exec /Users/benjaminfeuer/miniconda3/envs/otagent/bin/python \
  "$REPO_ROOT/scripts/iris/watch_iris_harbor.py" --job "$JOB_ID" "$@"
