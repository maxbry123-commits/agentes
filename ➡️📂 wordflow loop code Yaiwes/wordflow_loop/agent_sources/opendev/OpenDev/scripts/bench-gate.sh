#!/usr/bin/env bash
# bench-gate.sh — Run cargo bench and compare against baseline.
# If any benchmark regresses by >10%, exit non-zero.
#
# Usage:
#   ./scripts/bench-gate.sh              # compare against baseline
#   ./scripts/bench-gate.sh --update     # update baseline with current results

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BASELINE_FILE="$ROOT_DIR/benches/baseline.json"
RESULTS_FILE=$(mktemp /tmp/bench-results-XXXXXX.json)
REGRESSION_THRESHOLD=10  # percent

cleanup() {
    rm -f "$RESULTS_FILE"
}
trap cleanup EXIT

# ── Run benchmarks and capture output ──────────────────────────────────────
echo "Running cargo bench..."
BENCH_OUTPUT=$(cd "$ROOT_DIR" && cargo bench --workspace 2>&1) || {
    echo "ERROR: cargo bench failed"
    echo "$BENCH_OUTPUT"
    exit 1
}

# ── Parse criterion output into JSON ───────────────────────────────────────
# Criterion outputs lines like:
#   test_name           time:   [1.234 µs 1.300 µs 1.400 µs]
# We extract the middle (estimate) value and normalize to nanoseconds.

parse_benchmarks() {
    local output="$1"
    echo "{"
    local first=true
    while IFS= read -r line; do
        # Match criterion-style output: "bench_name  time:   [low est high]"
        if [[ "$line" =~ ^([a-zA-Z0-9_/]+)[[:space:]]+time:[[:space:]]+\[([0-9.]+)[[:space:]]+(ns|µs|us|ms|s)[[:space:]]+([0-9.]+)[[:space:]]+(ns|µs|us|ms|s)[[:space:]]+([0-9.]+)[[:space:]]+(ns|µs|us|ms|s)\] ]]; then
            name="${BASH_REMATCH[1]}"
            est_val="${BASH_REMATCH[4]}"
            est_unit="${BASH_REMATCH[5]}"

            # Normalize to nanoseconds
            case "$est_unit" in
                ns)  ns_val="$est_val" ;;
                µs|us) ns_val=$(echo "$est_val * 1000" | bc -l) ;;
                ms)  ns_val=$(echo "$est_val * 1000000" | bc -l) ;;
                s)   ns_val=$(echo "$est_val * 1000000000" | bc -l) ;;
                *)   ns_val="$est_val" ;;
            esac

            if [ "$first" = true ]; then
                first=false
            else
                echo ","
            fi
            printf '  "%s": %.2f' "$name" "$ns_val"
        fi
    done <<< "$output"
    echo ""
    echo "}"
}

parse_benchmarks "$BENCH_OUTPUT" > "$RESULTS_FILE"

# Count parsed benchmarks
BENCH_COUNT=$(python3 -c "import json; d=json.load(open('$RESULTS_FILE')); print(len(d))" 2>/dev/null || echo "0")

if [ "$BENCH_COUNT" = "0" ]; then
    echo "WARNING: No benchmarks parsed from cargo bench output."
    echo "This may be expected if no criterion benchmarks are defined."
    # If updating baseline, write empty baseline
    if [ "${1:-}" = "--update" ]; then
        echo "{}" > "$BASELINE_FILE"
        echo "Baseline updated (empty) at $BASELINE_FILE"
    fi
    exit 0
fi

echo "Parsed $BENCH_COUNT benchmark(s)."

# ── Update mode ────────────────────────────────────────────────────────────
if [ "${1:-}" = "--update" ]; then
    cp "$RESULTS_FILE" "$BASELINE_FILE"
    echo "Baseline updated at $BASELINE_FILE with $BENCH_COUNT benchmark(s)."
    exit 0
fi

# ── Compare against baseline ──────────────────────────────────────────────
if [ ! -f "$BASELINE_FILE" ]; then
    echo "No baseline found at $BASELINE_FILE"
    echo "Run with --update to create one: ./scripts/bench-gate.sh --update"
    exit 1
fi

echo "Comparing against baseline..."

# Use python3 for JSON comparison (available on macOS and most CI)
REGRESSION_FOUND=$(python3 -c "
import json, sys

with open('$BASELINE_FILE') as f:
    baseline = json.load(f)
with open('$RESULTS_FILE') as f:
    current = json.load(f)

threshold = $REGRESSION_THRESHOLD
regressions = []
improvements = []

for name, cur_ns in current.items():
    if name not in baseline:
        print(f'  NEW: {name} = {cur_ns:.2f} ns')
        continue
    base_ns = baseline[name]
    if base_ns == 0:
        continue
    pct_change = ((cur_ns - base_ns) / base_ns) * 100

    if pct_change > threshold:
        regressions.append((name, base_ns, cur_ns, pct_change))
        print(f'  REGRESSION: {name}: {base_ns:.2f} -> {cur_ns:.2f} ns (+{pct_change:.1f}%)')
    elif pct_change < -threshold:
        improvements.append((name, base_ns, cur_ns, pct_change))
        print(f'  IMPROVED: {name}: {base_ns:.2f} -> {cur_ns:.2f} ns ({pct_change:.1f}%)')
    else:
        print(f'  OK: {name}: {base_ns:.2f} -> {cur_ns:.2f} ns ({pct_change:+.1f}%)')

if regressions:
    print(f'\nFAILED: {len(regressions)} benchmark(s) regressed by >{threshold}%')
    sys.exit(1)
else:
    print(f'\nPASSED: No regressions above {threshold}% threshold')
    if improvements:
        print(f'  ({len(improvements)} benchmark(s) improved)')
    sys.exit(0)
" 2>&1) || {
    echo "$REGRESSION_FOUND"
    exit 1
}

echo "$REGRESSION_FOUND"
