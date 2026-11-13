#!/bin/bash
# Delphi 54-run SFT re-submit driver (Leonardo). Runs on login node.
# Per cell: hpc.launch (auto-submits) -> capture jobid+sbatch+config -> scancel ->
#   schema-strip train_config + fix $DCFT// in sbatch -> resubmit patched sbatch with
#   rolling afterany dependency window (<=WINDOW concurrent).
set -o pipefail
source /leonardo_work/AIFAC_5C0_290/bfeuer00/miniforge3/etc/profile.d/conda.sh
conda activate otagent
cd /leonardo_work/AIFAC_5C0_290/bfeuer00/code/OpenThoughts-Agent
source hpc/dotenv/leonardo.env && source ~/secrets.env

PREPBASE=/leonardo_work/AIFAC_5C0_290/bfeuer00/experiments/delphi-prepared-tok
EXPROOT=/leonardo_work/AIFAC_5C0_290/bfeuer00/code/OpenThoughts-Agent/experiments
MAP=$PREPBASE/launch_54_map.tsv          # jobid <tab> base <tab> recipe <tab> hub_model_id
LOG=$PREPBASE/launch_54.log
WINDOW=6                                  # rolling concurrency window
SKIP_VALIDATED_CELL="${SKIP_VALIDATED_CELL:-0}"   # 1 = skip 9e19-p33m67 x magpie

DCFT_PATH=/leonardo_work/AIFAC_5C0_290/bfeuer00/code/OpenThoughts-Agent

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

# recipe -> instruction-dataset-name (registered) and hub-id suffix
declare -A INSTR=( [magpie]=magpie [wc386k]=wildchat_386k )

echo "DRIVER START $(date)" | tee "$LOG"
: > "$MAP"
SUBMITTED=()   # ordered list of submitted jobids (for rolling window)

submit_cell () {
  local base="$1" recipe="$2"
  local prep="$PREPBASE/$base-prepared-tok"
  local instr="${INSTR[$recipe]}"
  local hub="laion/${base}-${recipe}_lr1e5-sft"     # dots sanitized by launcher

  if [ ! -f "$prep/model.safetensors" ] && [ ! -f "$prep/model.safetensors.index.json" ]; then
    echo "SKIP-NOPREP $base $recipe (prepared dir missing)" | tee -a "$LOG"
    echo -e "NOPREP\t$base\t$recipe\t$hub" >> "$MAP"
    return
  fi
  if [ "$SKIP_VALIDATED_CELL" = "1" ] && [ "$base" = "delphi-9e19-p33m67-k0p20-lr83-a002" ] && [ "$recipe" = "magpie" ]; then
    echo "SKIP-VALIDATED $base $recipe (job 45662136 already done)" | tee -a "$LOG"
    echo -e "VALIDATED-45662136\t$base\t$recipe\t$hub" >> "$MAP"
    return
  fi

  echo "===== LAUNCH $base $recipe -> $hub  $(date)" | tee -a "$LOG"
  local out
  out=$(DISABLE_VERSION_CHECK=1 python -m hpc.launch \
    --train_config_path sft/lf_configs/delphi/4k_sft.yaml \
    --model_path "$prep" \
    --dataset_dir sft/delphi \
    --dataset "${instr},delphi_warmup" \
    --mix_strategy interleave_under --interleave_probs 0.9,0.1 \
    --num_nodes 4 --gpus_per_node 4 --time_limit 23:59:00 --internet_node \
    --push_to_hub false --learning_rate 1.0e-5 \
    --hub_model_id "$hub" 2>&1)
  echo "$out" | tail -4 | sed 's/^/    /' | tee -a "$LOG"

  # jobid from "Writing logs to <logs_dir>/<job_name>_<jobid>.out"
  local jid logline
  logline=$(echo "$out" | grep -oE "Writing logs to .*/[^/]+_[0-9]+\.out" | tail -1)
  jid=$(echo "$logline" | grep -oE "_[0-9]+\.out" | grep -oE "[0-9]+")
  local sbatchpath
  sbatchpath=$(echo "$out" | grep -oE "Wrote SFT sbatch script to .*_sft\.sbatch" | sed -E 's#Wrote SFT sbatch script to ##' | grep -v "\.bak" | tail -1)
  # fallback: derive job_name from logline
  if [ -z "$sbatchpath" ]; then
    local jobname
    jobname=$(echo "$logline" | sed -E 's#.*/([^/]+)_[0-9]+\.out#\1#')
    sbatchpath=$(ls -t "$EXPROOT"/*/sbatch/${jobname}_sft.sbatch 2>/dev/null | head -1)
  fi

  if [ -z "$jid" ] || [ -z "$sbatchpath" ] || [ ! -f "$sbatchpath" ]; then
    echo "FAIL-CAPTURE $base $recipe jid=$jid sbatch=$sbatchpath" | tee -a "$LOG"
    echo -e "FAIL-CAPTURE\t$base\t$recipe\t$hub" >> "$MAP"
    return
  fi

  # scancel the auto-submitted (unpatched) job
  scancel "$jid" 2>/dev/null
  echo "    scancelled auto-submit $jid" | tee -a "$LOG"

  # locate the train_config yaml (same exp dir as sbatch)
  local expdir cfgdir cfg
  expdir=$(dirname "$(dirname "$sbatchpath")")
  cfgdir="$expdir/configs"
  cfg=$(ls "$cfgdir"/*_train_config.yaml 2>/dev/null | grep -v "\.bak" | tail -1)

  # --- §9.4 schema-strip on train_config ---
  if [ -n "$cfg" ] && [ -f "$cfg" ]; then
    cp "$cfg" "$cfg.bak"
    sed -i -E '/^assistant_tag:/d; /^content_tag:/d; /^formatting:/d; /^messages:/d; /^role_tag:/d; /^user_tag:/d' "$cfg"
    if grep -qE '^overwrite_cache:' "$cfg"; then
      sed -i -E 's/^overwrite_cache:.*/overwrite_cache: true/' "$cfg"
    else
      echo 'overwrite_cache: true' >> "$cfg"
    fi
  else
    echo "WARN-NOCFG $base $recipe (no train_config; submitting unpatched)" | tee -a "$LOG"
  fi

  # --- §5 sbatch patch: fix $DCFT// doubling ---
  cp "$sbatchpath" "$sbatchpath.bak"
  sed -i "s|\$DCFT//leonardo_work/AIFAC_5C0_290/bfeuer00/code/OpenThoughts-Agent|$DCFT_PATH|g" "$sbatchpath"

  # --- rolling dependency: depend on the job WINDOW positions back ---
  local dep=""
  local n=${#SUBMITTED[@]}
  if [ "$n" -ge "$WINDOW" ]; then
    local depjob="${SUBMITTED[$((n-WINDOW))]}"
    dep="--dependency=afterany:$depjob"
  fi

  # resubmit patched sbatch
  local sub newjid
  sub=$(sbatch $dep "$sbatchpath" 2>&1)
  newjid=$(echo "$sub" | grep -oE "[0-9]+" | tail -1)
  if [ -z "$newjid" ]; then
    echo "FAIL-RESUBMIT $base $recipe: $sub" | tee -a "$LOG"
    echo -e "FAIL-RESUBMIT\t$base\t$recipe\t$hub" >> "$MAP"
    return
  fi
  SUBMITTED+=("$newjid")
  echo "    RESUBMITTED $newjid  dep='$dep'" | tee -a "$LOG"
  echo -e "$newjid\t$base\t$recipe\t$hub" >> "$MAP"
}

for base in "${BASES[@]}"; do
  for recipe in magpie wc386k; do
    submit_cell "$base" "$recipe"
  done
done

echo "DRIVER DONE $(date) — submitted ${#SUBMITTED[@]} jobs" | tee -a "$LOG"
echo "MAP at $MAP"
