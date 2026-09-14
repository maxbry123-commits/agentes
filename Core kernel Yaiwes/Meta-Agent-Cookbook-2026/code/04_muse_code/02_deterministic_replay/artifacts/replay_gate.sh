#!/usr/bin/env bash
# replay_gate.sh: merge-blocking golden-trace replay gate.
#
# Replays every committed golden trace with `muse trace inspect` and fails when
# any recorded session no longer projects to its frozen expectation. Wire it
# into CI as a required check: a projection diff exits non-zero and blocks the
# merge.
#
# Usage: replay_gate.sh <fixture-dir>
set -euo pipefail

FIXTURE_DIR="${1:-golden-traces}"
fail=0
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

shopt -s nullglob
fixtures=("$FIXTURE_DIR"/*.json)
if [ "${#fixtures[@]}" -eq 0 ]; then
  echo "FAIL  no JSON fixtures found in $FIXTURE_DIR"
  exit 1
fi

for fixture in "${fixtures[@]}"; do
  name="$(basename "$fixture" .json)"
  if muse trace inspect --fixture "$fixture" --format json \
      >"$tmp/report.json" 2>"$tmp/inspect.err"; then
    inspect_status=0
  else
    inspect_status=$?
  fi

  if ! jq -e . "$tmp/report.json" >/dev/null 2>&1; then
    echo "FAIL  $name: inspect failed with exit $inspect_status"
    sed 's/^/        /' "$tmp/inspect.err"
    fail=1
    continue
  fi

  # A fixture that fails to load (bad schema, malformed JSON) is a hard failure.
  status="$(jq -r '.load_status' "$tmp/report.json")"
  if [ "$status" != "loaded" ]; then
    echo "FAIL  $name: fixture did not load (load_status=$status)"
    jq -r '.errors[] | "        " + .message' "$tmp/report.json"
    fail=1
    continue
  fi

  if [ "$inspect_status" -ne 0 ]; then
    echo "FAIL  $name: inspect failed with exit $inspect_status"
    sed 's/^/        /' "$tmp/inspect.err"
    fail=1
    continue
  fi

  # Zero diffs is the pass signal. Any diff means recorded behavior drifted.
  diffs="$(jq '.diffs | length' "$tmp/report.json")"
  if [ "$diffs" -eq 0 ]; then
    echo "PASS  $name"
  else
    echo "FAIL  $name: $diffs projection diff(s)"
    jq -r '.diffs[]
      | "        " + .path + ": expected " + (.expected|tostring)
        + ", actual " + (.actual|tostring)' "$tmp/report.json"
    fail=1
  fi
done

exit "$fail"
