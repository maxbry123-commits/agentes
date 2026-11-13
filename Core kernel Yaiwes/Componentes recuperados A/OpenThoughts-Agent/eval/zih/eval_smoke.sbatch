#!/bin/bash
#SBATCH -p capella
#SBATCH --time=00:55:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=14
#SBATCH --gres=gpu:1
#SBATCH --mem=120G
#SBATCH --output=%x_%j.out
#SBATCH --job-name=zih_eval_smoke
# ==============================================================================
# ZIH Capella eval SMOKE — self-contained cluster bring-up validation.
#
# Validates the cluster end-to-end WITHOUT any registry side-effects (NO Supabase
# DB registration, NO HF upload — deliberately, this is an infra smoke):
#   1. SLURM admits on `capella`, 1x H100 via --gres=gpu:1 (the untyped form — the
#      Capella cli_filter REJECTS the typed --gres=gpu:h100:N at submit)
#   2. otagent conda env activates
#   3. vLLM loads a small model on the H100 (Qwen/Qwen3-1.7B, TP=1)
#   4. a direct /v1/chat/completions produces output  <-- PASS GATE
#   5. (end-to-end) a 1-task terminal_bench_2 harbor terminus-2 + Daytona agentic
#      run advances (best-effort; compute nodes have direct Daytona egress)
#
# Run:  sbatch eval/zih/eval_smoke.sbatch
# ==============================================================================
set -uo pipefail

MODEL="${SMOKE_MODEL:-Qwen/Qwen3-1.7B}"
WS=/data/cat/ws/befe330h-otagent
DCFT="$WS/OpenThoughts-Agent"

echo "=============================================="
echo "ZIH Capella eval smoke"
echo "Model: $MODEL"
echo "Node:  $(hostname)"
echo "=============================================="

# --- Environment ---
module load CUDA/12.8.0 2>/dev/null || true
set +u   # dotenv / conda hooks reference unset vars
source "$WS/miniconda3/etc/profile.d/conda.sh"
conda activate otagent
source ~/secrets.env
source "$DCFT/hpc/dotenv/zih_capella.env"
set -u
export LD_LIBRARY_PATH="${CONDA_PREFIX}/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export HF_HUB_OFFLINE=0            # Capella compute nodes have direct egress
export TRITON_CACHE_DIR="/tmp/triton_${USER}_${SLURM_JOB_ID}"
cd "$DCFT"
export PYTHONPATH="$WS/harbor/src:$DCFT:${PYTHONPATH:-}"
PYTHON_BIN="$(which python)"

echo "[versions]"
$PYTHON_BIN -c "import torch,vllm,transformers,harbor; print('torch',torch.__version__,'| vllm',vllm.__version__,'| transformers',transformers.__version__,'| harbor',harbor.__version__)"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader

# --- Start vLLM (TP=1) via the shared builder ---
export EVAL_VLLM_TENSOR_PARALLEL_SIZE=1
export EVAL_VLLM_MAX_MODEL_LEN=16384
RUN_DIR="$WS/eval_jobs/zih_smoke_${SLURM_JOB_ID}"
mkdir -p "$RUN_DIR"
source "$DCFT/eval/build_vllm_cmd.sh"
build_vllm_cmd "$PYTHON_BIN" "$MODEL" "0.90"
echo "Starting vLLM ..."
"${VLLM_CMD[@]}" > "$RUN_DIR/vllm.log" 2>&1 &
VLLM_PID=$!
cleanup() { kill "$VLLM_PID" 2>/dev/null || true; }
trap cleanup EXIT

# --- Health check (30-min window: a COLD vLLM start on Capella = first-ever
#     `import vllm` CUDA init (~7 min) + HF model download + weight load; 10 min
#     was too short and the trap killed vLLM mid-init — job 3739411) ---
HEALTH="http://127.0.0.1:8000/v1/models"
READY=0
for i in $(seq 1 60); do
    if $PYTHON_BIN -c "import urllib.request,sys; urllib.request.urlopen('$HEALTH',timeout=8); sys.exit(0)" 2>/dev/null; then
        echo "vLLM ready (attempt $i)"; READY=1; break
    fi
    sleep 30
done
if [ "$READY" -ne 1 ]; then
    echo "FAIL: vLLM did not become ready"; tail -60 "$RUN_DIR/vllm.log"; exit 1
fi

# --- GATE: direct chat completion produces output ---
echo "=== direct generation gate ==="
GEN=$($PYTHON_BIN - "$MODEL" <<'PY'
import json, sys, urllib.request
model = sys.argv[1]
req = urllib.request.Request(
    "http://127.0.0.1:8000/v1/chat/completions",
    data=json.dumps({"model": model,
                     "messages":[{"role":"user","content":"Reply with exactly: SMOKE_OK"}],
                     "max_tokens":32, "temperature":0}).encode(),
    headers={"Content-Type":"application/json"})
out = json.load(urllib.request.urlopen(req, timeout=120))
txt = out["choices"][0]["message"]["content"]
print("COMPLETION:", repr(txt))
PY
)
echo "$GEN"
if echo "$GEN" | grep -q "COMPLETION:"; then
    echo "GATE PASS: vLLM produced a completion on the H100."
else
    echo "GATE FAIL: no completion"; exit 1
fi

# --- End-to-end: 1-task terminal_bench_2 harbor terminus-2 + Daytona (best-effort) ---
echo "=== agentic end-to-end (1 task, best-effort) ==="
set +e
DS_ROOT="$WS/data/datasets/terminal_bench_2"
if [ ! -d "$DS_ROOT" ] || [ "$(ls -d "$DS_ROOT"/*/instruction.md 2>/dev/null | wc -l)" -eq 0 ]; then
    $PYTHON_BIN "$DCFT/eval/snapshot_download.py" DCAgent2/terminal_bench_2 --local-dir "$DS_ROOT" 2>&1 | tail -3
fi
# subset to ONE task dir
SMOKE_DS="$RUN_DIR/dataset_1task"
mkdir -p "$SMOKE_DS"
FIRST_TASK=$(ls -d "$DS_ROOT"/*/instruction.md 2>/dev/null | head -1 | xargs -r dirname)
if [ -n "$FIRST_TASK" ]; then
    ln -sfn "$FIRST_TASK" "$SMOKE_DS/$(basename "$FIRST_TASK")"
    MI='{"max_input_tokens":16384,"max_output_tokens":8192,"input_cost_per_token":0,"output_cost_per_token":0}'
    DAYTONA_API_KEY="${DAYTONA_DATA_API_KEY:-$DAYTONA_API_KEY}" \
    harbor jobs start \
        -p "$SMOKE_DS" \
        --n-concurrent 1 \
        --agent terminus-2 \
        --model "hosted_vllm/$MODEL" \
        --env daytona \
        --agent-kwarg "api_base=http://127.0.0.1:8000/v1" \
        --agent-kwarg "key=fake_key" \
        --agent-kwarg "model_info=$MI" \
        --n-attempts 1 \
        --job-name "zih_smoke_${SLURM_JOB_ID}" \
        --jobs-dir "$WS/eval_jobs" \
        --config "$DCFT/hpc/harbor_yaml/eval/configs/dcagent_eval_config_no_override.yaml" \
        --environment-kwarg auto_snapshot=true
    HRC=$?
    echo "harbor exit: $HRC"
    TRIALS=$(ls -d "$WS/eval_jobs/zih_smoke_${SLURM_JOB_ID}"/*__*/ 2>/dev/null | wc -l)
    echo "trial dirs produced: $TRIALS"
else
    echo "SKIP agentic: dataset not available"
fi
set -e

echo "=============================================="
echo "ZIH smoke finished. PASS GATE = direct generation above."
echo "=============================================="
