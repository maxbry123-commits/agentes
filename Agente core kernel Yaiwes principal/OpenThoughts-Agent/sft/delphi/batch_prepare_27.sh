#!/bin/bash
set -o pipefail
source /leonardo_work/AIFAC_5C0_290/bfeuer00/miniforge3/etc/profile.d/conda.sh
conda activate otagent
cd /leonardo_work/AIFAC_5C0_290/bfeuer00/code/OpenThoughts-Agent
source hpc/dotenv/leonardo.env && source ~/secrets.env
OUTBASE=/leonardo_work/AIFAC_5C0_290/bfeuer00/experiments/delphi-prepared-tok
mkdir -p "$OUTBASE"
BASES=(
delphi-3e18-p33m67-k0p20-lr83-a003
delphi-3e18-p50m50-k0p20-lr83-a003
delphi-3e18-p67m33-k0p20-lr83-a003
delphi-9e18-p33m67-k0p20-lr83-a002
delphi-9e18-p50m50-k0p20-lr83-a002
delphi-9e18-p67m33-k0p20-lr83-a002
delphi-2e19-p33m67-k0p20-lr83-a002
delphi-2e19-p50m50-k0p20-lr83-a002
delphi-2e19-p67m33-k0p20-lr83-a002
delphi-3e19-p33m67-k0p20-lr83-a002
delphi-3e19-p50m50-k0p20-lr83-a002
delphi-3e19-p67m33-k0p20-lr83-a002
delphi-9e19-p33m67-k0p20-lr83-a002
delphi-9e19-p50m50-k0p20-lr83-a002
delphi-9e19-p67m33-k0p20-lr83-a002
delphi-2e20-p33m67-k0p20-lr83-a001
delphi-2e20-p50m50-k0p20-lr83-a001
delphi-2e20-p67m33-k0p20-lr83-a001
delphi-3e20-p33m67-k0p20-lr83-a001
delphi-3e20-p50m50-k0p20-lr83-a001
delphi-3e20-p67m33-k0p20-lr83-a001
delphi-1e21-p33m67-9p25b-lr0.67-9cf8da
delphi-1e21-p50m50-9p25b-lr0.83-f9edd2
delphi-1e21-p67m33-9p25b-lr0.67-ecbd27
delphi-1e22-p33m67-32p07b-lr0.67-54770ae7
delphi-1e22-p50m50-32p07b-lr0.5-ecfa99
delphi-1e22-p67m33-32p07b-lr0.33-4e8cc7a7
)
echo "START $(date) — ${#BASES[@]} bases"
for b in "${BASES[@]}"; do
  OUT="$OUTBASE/$b-prepared-tok"
  if [ -f "$OUT/model.safetensors" ] || [ -f "$OUT/model.safetensors.index.json" ]; then
    echo "SKIP  $b (already prepared)"; continue
  fi
  echo "===== PREP $b -> $OUT  $(date)"
  python sft/delphi/prepare_delphi_tokenizer.py --model "laion/$b" --output "$OUT" 2>&1 | tail -6
  rc=${PIPESTATUS[0]}
  if [ $rc -ne 0 ]; then echo "FAIL  $b rc=$rc"; else echo "OK    $b"; fi
done
echo "DONE $(date)"
