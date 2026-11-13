#!/bin/bash
# ==============================================================================
# EmpireAI Beta — Unified Eval Harbor, IN-CONTAINER body.
#
# Runs INSIDE the Pyxis/Enroot `mega_v2_rl.sqsh` container (see eval_harbor.sbatch,
# which srun-launches this). The container's RL venv (/opt/envs/rl) carries the
# sm_100 vLLM fork + harbor[daytona]@22d75039 (incl. agents/installed/opencode.py)
# + flash-attn 2.8.3 + ray. This script is the Beta analog of the Vista body in
# eval/tacc/eval_harbor.sbatch (harbor + vLLM + pinggy tunnel + upload), adapted:
#   - PYTHON_BIN = /opt/envs/rl/bin/python  (the RL venv, NOT /usr/bin/python3)
#   - PATH sanitized to drop the host ~/.pyenv leak that --container-mount-home adds
#   - node-local /tmp caches (triton/inductor/flashinfer/torch) — dodges the VAST-NFS
#     ESTALE race the multi-node SFT hit (job 31689) + keeps MoE-kernel JIT off NFS
#   - DIRECT pinggy tunnel, NO proxychains (Beta compute nodes have full egress —
#     verified: app/api.daytona.io + pro.pinggy.io:443 reachable from a compute node)
#   - EVAL_SKIP_DB / EVAL_SKIP_UPLOAD guards for cheap smoke tests
#
# Consumes (exported by eval_harbor.sbatch, forwarded via srun --container-env):
#   MODEL REPO_ID BENCHMARK_ID RUN_TAG MASTER_ADDR SLURM_JOB_ID
#   DCFT (mounted repo root) EVAL_JOBS_DIR HF_HOME
#   EVAL_CONFIG_YAML EVAL_N_CONCURRENT EVAL_GPU_MEMORY_UTIL EVAL_TIMEOUT_MULTIPLIER
#   EVAL_PINGGY_URL EVAL_PINGGY_TOKEN EVAL_VLLM_* EVAL_AGENT_KWARGS EVAL_AGENT_PARSER
#   EVAL_DB_JOB_ID EVAL_SKIP_DB EVAL_SKIP_UPLOAD EVAL_OVERRIDE_MEMORY_MB
#   (secrets sourced from $SECRETS_ENV inside: HF_TOKEN, DAYTONA_*, SUPABASE_*, PINGGY_*)
# ==============================================================================
set -eo pipefail
ulimit -c 0
ulimit -n 65536 2>/dev/null || true

# --- Sanitize PATH so the container toolchain wins; drop host ~/.pyenv leak -----
# --container-mount-home mounts the host HOME (x86 pyenv shims) onto the aarch64
# container -> "Exec format error" if a shim shadows python. Force the container's
# own bins first (same remedy as ~/scripts/dm_incontainer.sh).
export PATH=/opt/envs/rl/bin:/usr/local/bin:/usr/local/cuda/bin:/usr/bin:/bin
hash -r
unset PYENV_ROOT PYENV_VERSION PYENV_SHELL PIP_CONSTRAINT 2>/dev/null || true

PYTHON_BIN=/opt/envs/rl/bin/python
SERVE_PYTHON_BIN="$PYTHON_BIN"
HARBOR_BIN=/opt/envs/rl/bin/harbor

TIMESTAMP=$(date +'%Y%m%d_%H%M%S')

# --- Positional config (already exported by the sbatch) ---
MODEL="${MODEL:?MODEL unset}"
REPO_ID="${REPO_ID:?REPO_ID unset}"
BENCHMARK_ID="${BENCHMARK_ID:-}"
RUN_TAG="${RUN_TAG:?RUN_TAG unset}"

N_CONCURRENT="${EVAL_N_CONCURRENT:-8}"
GPU_MEMORY_UTIL="${EVAL_GPU_MEMORY_UTIL:-0.90}"
DAYTONA_ERROR_THRESHOLD="${EVAL_DAYTONA_THRESHOLD:-999999}"
CONFIG_YAML="${EVAL_CONFIG_YAML:-eval_opencode_ctx32k.yaml}"
AGENT_KWARGS="${EVAL_AGENT_KWARGS:-}"
AGENT_PARSER="${EVAL_AGENT_PARSER:-}"
DB_JOB_ID="${EVAL_DB_JOB_ID:-}"
SKIP_DB="${EVAL_SKIP_DB:-0}"
SKIP_UPLOAD="${EVAL_SKIP_UPLOAD:-0}"

DCFT="${DCFT:?DCFT (mounted repo root) unset}"
EVAL_JOBS_DIR="${EVAL_JOBS_DIR:?EVAL_JOBS_DIR unset}"

SAFE_MODEL=$(echo "$MODEL" | tr '/:' '_')
if [[ "$REPO_ID" == /* ]]; then SAFE_REPO=$(basename "$REPO_ID"); else SAFE_REPO=$(echo "$REPO_ID" | tr '/:' '_'); fi

echo "=============================================="
echo "EmpireAI Beta Eval Harbor (B200 sm_100 aarch64, containerized)"
echo "=============================================="
echo "Node: $(hostname)   Container python: $($PYTHON_BIN --version 2>&1)"
echo "Model: $MODEL | Dataset: $REPO_ID | Config: $CONFIG_YAML"
echo "N concurrent: $N_CONCURRENT | GPU mem util: $GPU_MEMORY_UTIL"
echo "SKIP_DB=$SKIP_DB SKIP_UPLOAD=$SKIP_UPLOAD"
echo "=============================================="

# --- Secrets (HF / Daytona / Supabase / Pinggy) -------------------------------
SECRETS_ENV="${SECRETS_ENV:-/mnt/home/bf996/secrets.env}"
if [ -f "$SECRETS_ENV" ]; then set -a; source "$SECRETS_ENV"; set +a; echo "Sourced secrets: $SECRETS_ENV"; else echo "WARN: secrets not found: $SECRETS_ENV"; fi

# --- Node-local caches (avoid VAST-NFS ESTALE; keep MoE-kernel JIT off NFS) ----
CACHE=/tmp/${USER:-bf996}/evalcache_${SLURM_JOB_ID:-nojob}
mkdir -p "$CACHE"/{triton,inductor,flashinfer,torch,torchinductor,xdg,tmp,vllm}
export TRITON_CACHE_DIR="$CACHE/triton" TRITON_HOME="$CACHE/triton"
export TORCHINDUCTOR_CACHE_DIR="$CACHE/torchinductor"
export TORCH_EXTENSIONS_DIR="$CACHE/torch" TORCH_HOME="$CACHE/torch"
export FLASHINFER_WORKSPACE_BASE="$CACHE/flashinfer"
export XDG_CACHE_HOME="$CACHE/xdg" TMPDIR="$CACHE/tmp"
export VLLM_CACHE_ROOT="$CACHE/vllm" VLLM_CONFIG_ROOT="$CACHE/vllm"
export MAX_JOBS="${MAX_JOBS:-8}"            # bound flashinfer JIT nvcc parallelism
export HF_HUB_OFFLINE=0                     # Beta compute nodes have direct egress
export HF_HOME="${HF_HOME:-/mnt/home/bf996/hf_cache}"
export HF_HUB_CACHE="${HF_HUB_CACHE:-$HF_HOME/hub}"
export HYDRA_FULL_ERROR=1
export TOKENIZERS_PARALLELISM=false
# aiohttp Path.home() thread-unsafety segfault guard (see TACC/Leonardo rationale)
export NETRC="$CACHE/.netrc_eval_placeholder"; touch "$NETRC" 2>/dev/null || true

# --- Daytona settings + strict DATA org for the installed (opencode) agent -----
export DAYTONA_MAX_RETRIES=5 DAYTONA_RETRY_DELAY=30 DAYTONA_BACKOFF_FACTOR=2 DAYTONA_TIMEOUT=1800
export AIOHTTP_CLIENT_TIMEOUT=900 AIOHTTP_CONNECTOR_TIMEOUT=900 AIOHTTP_SOCK_CONNECT_TIMEOUT=300 AIOHTTP_TOTAL_TIMEOUT=1800

# --- PYTHONPATH: mounted repo (for build_vllm_cmd deps, uploader, config resolve)
unset PYTHONPATH
export PYTHONPATH="${DCFT}"
echo "PYTHONPATH: $PYTHONPATH"

# --- Resolve harbor config path (mirrors TACC resolution order) ---------------
if [[ "$CONFIG_YAML" == /* ]]; then HARBOR_CONFIG="$CONFIG_YAML"
elif [ -f "$DCFT/hpc/harbor_yaml/eval/configs/$CONFIG_YAML" ]; then HARBOR_CONFIG="$DCFT/hpc/harbor_yaml/eval/configs/$CONFIG_YAML"
elif [ -f "$DCFT/eval/empireai/$CONFIG_YAML" ]; then HARBOR_CONFIG="$DCFT/eval/empireai/$CONFIG_YAML"
else echo "ERROR: harbor config not found: $CONFIG_YAML"; exit 1; fi
echo "Resolved harbor config: $HARBOR_CONFIG"

# --- Detect installed-agent (opencode) vs host-agent (terminus-2) -------------
CFG_AGENT_NAME=$($PYTHON_BIN -c "
import yaml
with open('$HARBOR_CONFIG') as f: cfg = yaml.safe_load(f)
agents = cfg.get('agents', [])
print(agents[0].get('name','terminus-2') if agents else 'terminus-2')" 2>/dev/null || echo "terminus-2")
case "$CFG_AGENT_NAME" in
    terminus|terminus-1|terminus-2|terminus-kira|oracle|nop) IS_INSTALLED_AGENT=false ;;
    *) IS_INSTALLED_AGENT=true ;;
esac
echo "Harbor config agent: $CFG_AGENT_NAME (installed_agent=$IS_INSTALLED_AGENT)"

# --- Daytona key selection: STRICT DATA org (org2) for installed agents --------
DAYTONA_KEY_ORG1="${DAYTONA_API_KEY:?DAYTONA_API_KEY unset — source secrets}"
DAYTONA_KEY_ORG2="${DAYTONA_DATA_API_KEY:?DAYTONA_DATA_API_KEY unset — source secrets}"
if [ "$IS_INSTALLED_AGENT" = true ]; then
    export DAYTONA_API_KEY="$DAYTONA_KEY_ORG2"
    echo "Selected Daytona org: org2/DATA (strict, installed-agent) (${DAYTONA_API_KEY:0:10}...)"
elif (( RANDOM % 4 == 0 )); then
    export DAYTONA_API_KEY="$DAYTONA_KEY_ORG1"; echo "Selected Daytona org: org1"
else
    export DAYTONA_API_KEY="$DAYTONA_KEY_ORG2"; echo "Selected Daytona org: org2"
fi

# ==============================================================================
# Cleanup trap
# ==============================================================================
cleanup() {
    echo "Cleaning up..."
    [ -n "${VLLM_PID:-}" ] && kill "$VLLM_PID" 2>/dev/null || true
    if [ -n "${PINGGY_PID:-}" ]; then kill "$PINGGY_PID" 2>/dev/null || true; pkill -P "$PINGGY_PID" 2>/dev/null || true; fi
    echo "Cleanup done."
}
trap cleanup EXIT

# ==============================================================================
# Run directory
# ==============================================================================
RUN_DIR="${EVAL_JOBS_DIR}/${RUN_TAG}"
mkdir -p "$RUN_DIR"
echo "Run tag: $RUN_TAG | Run dir: $RUN_DIR"

# ==============================================================================
# vLLM serve (TP from per-model config; default TP=1 — fits 1 B200 ~189GB)
# ==============================================================================
export EVAL_VLLM_TENSOR_PARALLEL_SIZE="${EVAL_VLLM_TENSOR_PARALLEL_SIZE:-1}"
export VLLM_PORT="${VLLM_PORT:-8000}"

# --- Container dependency fix: vLLM api_server ⇄ prometheus middleware ------------
# mega_B_rl.sbatch STEP 5 swapped the fork vLLM wheel in with `--no-deps`, so the RL
# venv kept skyrl's OLDER `prometheus-fastapi-instrumentator` (<7.0) — its route-name
# resolver does a bare `route.path`, which crashes on EVERY request under the fork's
# newer FastAPI ("'_IncludedRouter' object has no attribute 'path'" → 500 on
# /v1/models → the serve never passes its health check; smoke 32390 died here at
# ~28 min). v7.0.0 handles routes without `.path`. Ensure it at runtime (egress OK).
# ⚠ BAND-AID — the DURABLE fix is to bake `prometheus-fastapi-instrumentator>=7.0.0`
# into the next mega container rebuild (mega_B_rl.sbatch: install the fork vLLM WITH
# its deps, or add the explicit pin) so the eval doesn't runtime-pip every launch.
if ! $PYTHON_BIN -c "import importlib.metadata as m,sys; from packaging.version import Version; sys.exit(0 if Version(m.version('prometheus-fastapi-instrumentator'))>=Version('7.0.0') else 1)" 2>/dev/null; then
    echo "[dep-fix] upgrading prometheus-fastapi-instrumentator>=7.0.0 (vLLM api_server compat)"
    $PYTHON_BIN -m pip install -q --no-cache-dir -U 'prometheus-fastapi-instrumentator>=7.0.0' 2>&1 | tail -3 || echo "[dep-fix] WARN: pip upgrade failed — serve may 500 on every request"
fi

# --- Clamp gpu_memory_utilization to ACTUAL free memory (Beta gres-node reality) --
# Beta's fractional `--gres=gpu:b200:N` does NOT isolate GPU MEMORY: a co-tenant
# process on the same physical GPU counts against free memory, so a fixed
# 0.9-of-TOTAL request can exceed what's free and the vLLM engine aborts at startup
# ("Free memory ... less than desired GPU memory utilization" — smoke 32247, node
# had ~44 GiB already used). Read free/total for GPU 0 and cap the util so the
# request fits (free - margin); a clean GPU keeps ~0.90, a contended one steps down.
_margin_mib="${EVAL_GPU_MEM_MARGIN_MIB:-8192}"
read -r _gpu_total _gpu_free <<< "$(nvidia-smi --query-gpu=memory.total,memory.free --format=csv,noheader,nounits 2>/dev/null | head -1 | tr ',' ' ')"
if [ -n "${_gpu_total:-}" ] && [ -n "${_gpu_free:-}" ] && [ "${_gpu_total:-0}" -gt 0 ] 2>/dev/null; then
    _safe_util=$($PYTHON_BIN -c "t=$_gpu_total; f=$_gpu_free; m=$_margin_mib; print(f'{max(0.10, min(float('$GPU_MEMORY_UTIL'), (f-m)/t)):.2f}')" 2>/dev/null || echo "$GPU_MEMORY_UTIL")
    echo "[gpu-mem] GPU0 total=${_gpu_total}MiB free=${_gpu_free}MiB requested_util=$GPU_MEMORY_UTIL -> capped_util=$_safe_util"
    GPU_MEMORY_UTIL="$_safe_util"
fi

echo "Starting vLLM server for model: $MODEL"
source "$DCFT/eval/build_vllm_cmd.sh"
build_vllm_cmd "$SERVE_PYTHON_BIN" "$MODEL" "$GPU_MEMORY_UTIL"

MI_MAX_MODEL_LEN="${EVAL_VLLM_MAX_MODEL_LEN:-32768}"
MI_MAX_OUTPUT="${EVAL_MAX_OUTPUT_TOKENS:-16384}"
[ "$MI_MAX_OUTPUT" -ge "$MI_MAX_MODEL_LEN" ] 2>/dev/null && MI_MAX_OUTPUT=$(( MI_MAX_MODEL_LEN / 2 ))
MODEL_INFO_JSON="{\"max_input_tokens\":${MI_MAX_MODEL_LEN},\"max_output_tokens\":${MI_MAX_OUTPUT},\"input_cost_per_token\":0,\"output_cost_per_token\":0}"

"${VLLM_CMD[@]}" > "$RUN_DIR/vllm.log" 2>&1 &
VLLM_PID=$!

MASTER_ADDR="${MASTER_ADDR:-$(hostname)}"
VLLM_HEALTH_URL="http://${MASTER_ADDR}:${VLLM_PORT}/v1/models"
echo "Health check URL: $VLLM_HEALTH_URL"
MAX_RETRIES=40; RETRY_INTERVAL=30
_ready=false
for i in $(seq 1 $MAX_RETRIES); do
    if ! kill -0 "$VLLM_PID" 2>/dev/null; then echo "ERROR: vLLM process died during startup"; tail -80 "$RUN_DIR/vllm.log" || true; exit 1; fi
    if $PYTHON_BIN -c "import urllib.request,sys
try: urllib.request.urlopen('$VLLM_HEALTH_URL', timeout=10); sys.exit(0)
except Exception: sys.exit(1)" 2>/dev/null; then echo "vLLM server is ready (attempt $i)"; _ready=true; break; fi
    echo "Waiting for vLLM ($i/$MAX_RETRIES)..."; sleep $RETRY_INTERVAL
done
if [ "$_ready" = false ]; then echo "ERROR: vLLM failed to start"; tail -80 "$RUN_DIR/vllm.log" || true; exit 1; fi

# ==============================================================================
# Dataset (direct HF egress, or a local task path)
# ==============================================================================
if [[ "$REPO_ID" == /* ]]; then
    DATASET_PATH="$REPO_ID"
    [ -d "$DATASET_PATH" ] || { echo "ERROR: local dataset path missing: $DATASET_PATH"; exit 1; }
    TASK_COUNT=$(ls -d "$DATASET_PATH"/*/instruction.md 2>/dev/null | wc -l)
    echo "Local dataset: $DATASET_PATH ($TASK_COUNT tasks)"
else
    DATASET_LOCAL_DIR="${HF_HOME}/data/datasets/${SAFE_REPO}"
    TASK_COUNT=$(ls -d "$DATASET_LOCAL_DIR"/*/instruction.md 2>/dev/null | wc -l || echo 0)
    if [ "${TASK_COUNT:-0}" -gt 0 ]; then
        DATASET_PATH="$DATASET_LOCAL_DIR"; echo "Pre-downloaded dataset: $DATASET_PATH ($TASK_COUNT tasks)"
    else
        echo "Downloading dataset: $REPO_ID"
        DL_LOG=$(mktemp "$CACHE/tmp/dl_XXXXXX.log")
        $PYTHON_BIN "$DCFT/eval/snapshot_download.py" "$REPO_ID" --local-dir "$DATASET_LOCAL_DIR" > "$DL_LOG" 2>&1
        DL_EXIT=$?; cat "$DL_LOG"
        DATASET_PATH=$(grep DATASET_PATH "$DL_LOG" | tail -n1 | cut -d'=' -f2); rm -f "$DL_LOG"
        [ $DL_EXIT -ne 0 ] || [ -z "${DATASET_PATH:-}" ] && { echo "ERROR: dataset download failed ($DL_EXIT)"; exit 1; }
    fi
fi
echo "Using dataset path: $DATASET_PATH"

# ==============================================================================
# DB: Started (optional — skipped for smokes / when SKIP_DB=1)
# ==============================================================================
export MODEL REPO_ID RUN_TAG SLURM_JOB_ID
BENCHMARK_NAME="${BENCHMARK_NAME:-$SAFE_REPO}"; export BENCHMARK_NAME
if [ "$SKIP_DB" != "1" ]; then
    HARBOR_VERSION=$($PYTHON_BIN -c "import harbor;print(harbor.__version__)" 2>/dev/null || echo unknown); export HARBOR_VERSION
    $PYTHON_BIN - <<'PY' || echo "WARN: DB create step failed (continuing)"
import os, sys
try:
    from database.unified_db.utils import create_job_entry_started
    r = create_job_entry_started(
        model_hf_name=os.environ["MODEL"], benchmark_hf_name=os.environ["REPO_ID"],
        job_name=os.environ["RUN_TAG"], username=os.environ.get("USER","bf996"),
        slurm_job_id=os.environ["SLURM_JOB_ID"], harbor_package_version=os.environ.get("HARBOR_VERSION","unknown"),
        agent_name="opencode", config={"agent":"opencode","env":"daytona"}, n_trials=128, n_rep_eval=3)
    print(f"DB job: {r.get('job',{}).get('id')}" if r.get("success") else f"WARN DB create: {r.get('error')}")
except Exception as e:
    print(f"WARN: DB create unavailable ({e})", file=sys.stderr)
PY
else
    echo "SKIP_DB=1 — not creating a DB job entry (smoke mode)"
fi

# ==============================================================================
# Extra harbor args (timeout multiplier, memory override, agent kwargs)
# ==============================================================================
set +e
EXTRA_HARBOR_ARGS=""
# EVAL_N_TASKS caps the number of tasks (harbor -l/--n-tasks) — used for cheap smokes.
[ -n "${EVAL_N_TASKS:-}" ] && EXTRA_HARBOR_ARGS="$EXTRA_HARBOR_ARGS --n-tasks $EVAL_N_TASKS"
[ -n "${EVAL_TIMEOUT_MULTIPLIER:-}" ] && EXTRA_HARBOR_ARGS="$EXTRA_HARBOR_ARGS --timeout-multiplier $EVAL_TIMEOUT_MULTIPLIER"
[ -n "${EVAL_OVERRIDE_MEMORY_MB:-}" ] && EXTRA_HARBOR_ARGS="$EXTRA_HARBOR_ARGS --override-memory-mb $EVAL_OVERRIDE_MEMORY_MB"
[ -n "${EVAL_AUTO_SNAPSHOT:-}" ] && EXTRA_HARBOR_ARGS="$EXTRA_HARBOR_ARGS --environment-kwarg auto_snapshot=$EVAL_AUTO_SNAPSHOT"
if [ -n "$AGENT_KWARGS" ]; then
    while IFS= read -r _kw; do [ -z "$_kw" ] && continue; EXTRA_HARBOR_ARGS="$EXTRA_HARBOR_ARGS --agent-kwarg $_kw"; done <<< "$AGENT_KWARGS"
fi
[ -n "$AGENT_PARSER" ] && EXTRA_HARBOR_ARGS="$EXTRA_HARBOR_ARGS --agent-kwarg parser=$AGENT_PARSER"
echo "[DEBUG] EXTRA_HARBOR_ARGS=$EXTRA_HARBOR_ARGS"

# ==============================================================================
# Installed-agent (opencode) ingress: pinggy tunnel + model routing (DIRECT, no proxychains)
# opencode runs its CLI INSIDE the Daytona sandbox and calls the served model over a
# PUBLIC pinggy URL. Beta compute nodes have direct egress (verified pro.pinggy.io:443
# OPEN) but no public INGRESS, so expose localhost:8000 via a reverse SSH tunnel.
# ==============================================================================
if [ "$IS_INSTALLED_AGENT" = true ]; then
    if [ -z "${EVAL_PINGGY_URL:-}" ] || [ -z "${EVAL_PINGGY_TOKEN:-}" ]; then
        echo "[pinggy] FATAL: installed agent '$CFG_AGENT_NAME' needs a public tunnel but EVAL_PINGGY_URL/TOKEN unset."; exit 1
    fi
    echo "[pinggy] Starting SSH tunnel to ${EVAL_PINGGY_URL} (vLLM port ${VLLM_PORT})..."
    PINGGY_LOG="$RUN_DIR/pinggy_${SLURM_JOB_ID}.log"
    bash -c "while true; do ssh -p 443 \
        -R0:localhost:${VLLM_PORT} \
        -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
        -o ServerAliveInterval=30 -o ExitOnForwardFailure=yes \
        ${EVAL_PINGGY_TOKEN}@pro.pinggy.io; sleep 10; done" > "$PINGGY_LOG" 2>&1 &
    PINGGY_PID=$!
    echo "[pinggy] PID $PINGGY_PID (log: $PINGGY_LOG)"
    for _pg in $(seq 1 5); do sleep 1; kill -0 "$PINGGY_PID" 2>/dev/null || { echo "[pinggy] ERROR: tunnel died at startup"; cat "$PINGGY_LOG"; exit 1; }; done
    TUNNEL_URL="https://${EVAL_PINGGY_URL}"
    _verified=false
    for _vt in $(seq 1 18); do
        if curl -sk --connect-timeout 5 "${TUNNEL_URL}/v1/models" 2>/dev/null | grep -q "object"; then
            echo "[pinggy] Connectivity verified: $TUNNEL_URL (attempt $_vt)"; _verified=true; break; fi
        sleep 5
    done
    if [ "$_verified" = false ]; then echo "[pinggy] FATAL: public tunnel not reachable after 90s."; tail -20 "$PINGGY_LOG"; exit 1; fi
    export OPENAI_BASE_URL="${TUNNEL_URL}/v1"
    export OPENCODE_DUMMY_KEY="${OPENCODE_DUMMY_KEY:-capability-url-no-auth-header}"
    export OPENAI_API_KEY="${OPENAI_API_KEY:-$OPENCODE_DUMMY_KEY}"
    echo "[opencode] routing: model=vllm/$MODEL OPENAI_BASE_URL=$OPENAI_BASE_URL"
fi

# ==============================================================================
# Run Harbor eval (installed-agent opencode branch, or terminus-2 host branch)
# ==============================================================================
if [ "$IS_INSTALLED_AGENT" = true ]; then
    echo "Starting new job (installed agent: $CFG_AGENT_NAME)"
    RUNTIME_HARBOR_CONFIG="$CACHE/tmp/harbor_opencode_${SLURM_JOB_ID}.yaml"
    $PYTHON_BIN - "$HARBOR_CONFIG" "$RUNTIME_HARBOR_CONFIG" "vllm/$MODEL" <<'PY'
import sys, yaml
src, dst, model = sys.argv[1], sys.argv[2], sys.argv[3]
with open(src) as f: cfg = yaml.safe_load(f)
if not cfg.get("agents"): raise SystemExit(f"FATAL: no agents[] in {src}")
cfg["agents"][0]["model_name"] = model
with open(dst, "w") as f: yaml.dump(cfg, f, default_flow_style=False)
print(f"injected model_name={model} into {dst}")
PY
    "$HARBOR_BIN" jobs start \
        -p "$DATASET_PATH" \
        --n-concurrent "$N_CONCURRENT" \
        --env "daytona" \
        --n-attempts "${EVAL_N_ATTEMPTS:-3}" \
        --job-name "$RUN_TAG" \
        --jobs-dir "$EVAL_JOBS_DIR" \
        --config "$RUNTIME_HARBOR_CONFIG" \
        $EXTRA_HARBOR_ARGS
else
    echo "Starting new job (host agent: terminus-2)"
    "$HARBOR_BIN" jobs start \
        -p "$DATASET_PATH" \
        --n-concurrent "$N_CONCURRENT" \
        --agent terminus-2 \
        --model "hosted_vllm/$MODEL" \
        --env "daytona" \
        --agent-kwarg "api_base=http://${MASTER_ADDR}:${VLLM_PORT}/v1" \
        --agent-kwarg "key=fake_key" \
        --agent-kwarg "model_info=$MODEL_INFO_JSON" \
        --n-attempts "${EVAL_N_ATTEMPTS:-3}" \
        --job-name "$RUN_TAG" \
        --jobs-dir "$EVAL_JOBS_DIR" \
        --config "$HARBOR_CONFIG" \
        $EXTRA_HARBOR_ARGS
fi
SB_EXIT=$?
set -e

TRIAL_COUNT=$(find "$RUN_DIR" -maxdepth 1 -type d -name '*__*' 2>/dev/null | wc -l)
echo "Found $TRIAL_COUNT trial dirs in $RUN_DIR"
{ echo "MODEL=$MODEL"; echo "REPO_ID=$REPO_ID"; echo "TIMESTAMP=$TIMESTAMP"; echo "SLURM_JOB_ID=$SLURM_JOB_ID"; echo "N_CONCURRENT=$N_CONCURRENT"; } > "$RUN_DIR/meta.env"

# --- Score summary (reward), for smoke visibility ---
if [ -f "$RUN_DIR/result.json" ]; then
    $PYTHON_BIN -c "
import json
d=json.load(open('$RUN_DIR/result.json'))
st=d.get('stats',{})
print('[result] stats keys:', list(st.keys()))
ev=st.get('evals',{})
for k,v in ev.items():
    print('[result] eval', k, 'reward_mean=', v.get('reward_mean'), 'n=', v.get('n'), 'exceptions=', list((v.get('exception_stats') or {}).keys()))
" 2>&1 || echo "[result] parse failed"
else
    echo "[result] no result.json produced"
fi

if [ ${SB_EXIT:-0} -ne 0 ]; then echo "Harbor eval exited non-zero: ${SB_EXIT}. Skipping upload."; exit ${SB_EXIT}; fi

# ==============================================================================
# Upload (HF traces + optional DB). Skipped for smokes / when SKIP_UPLOAD=1.
# The RL-venv may lack supabase-py (an OT-Agent dep, not a harbor/skyrl one); the
# uploader degrades to a WARN in that case rather than aborting the job.
# ==============================================================================
if [ "$SKIP_UPLOAD" = "1" ]; then echo "SKIP_UPLOAD=1 — not uploading (smoke mode). Artifacts in $RUN_DIR"; exit 0; fi

export UPLOAD_DIR="$RUN_DIR" RUN_DIR UPLOAD_USERNAME="${UPLOAD_USERNAME:-$USER}" UPLOAD_MODE="${UPLOAD_MODE:-skip_on_error}" RUN_TAG
UPLOAD_LOG="$RUN_DIR/upload.log"
echo "Uploading results from: $RUN_DIR" | tee -a "$UPLOAD_LOG"
$PYTHON_BIN - <<'PY' 2>&1 | tee -a "$UPLOAD_LOG"
import os, re, hashlib, sys
try:
    from database.unified_db.utils import upload_eval_results
except Exception as e:
    print(f"WARN: uploader unavailable in this env ({e}); skipping upload. Artifacts remain on disk.", file=sys.stderr)
    raise SystemExit(0)
def sanitize_hf_repo_id(repo_id, max_length=96):
    def collapse(s):
        prev=None
        while s!=prev: prev=s; s=s.replace("--","-").replace("..",".")
        return s
    org,name=repo_id.split("/",1) if "/" in repo_id else (None,repo_id)
    name=re.sub(r"[^A-Za-z0-9._-]","-",name); name=collapse(name).strip("-.")
    if not name: name="repo"
    limit=max_length-(len(org)+1 if org else 0)
    if len(name)>limit:
        d=hashlib.sha1(name.encode()).hexdigest()[:8]; keep=max(1,limit-len(d)); base=name[:keep].rstrip("-.") or "r"; name=collapse(f"{base}{d}").strip("-.")
    name=collapse(name).strip("-.")
    if name[0] in "-.": name="r"+name[1:]
    if name[-1] in "-.": name=name[:-1]+"0"
    return f"{org}/{name}" if org else name
run_dir=os.environ["RUN_DIR"]; run_tag=os.environ["RUN_TAG"]
username=os.environ.get("UPLOAD_USERNAME", os.environ.get("USER","bf996"))
hf_repo_id=sanitize_hf_repo_id(f"DCAgent2/{run_tag}")
dataset_hf=os.environ.get("REPO_ID",""); benchmark_name=os.environ.get("BENCHMARK_NAME","") or (dataset_hf.split("/")[-1] if "/" in dataset_hf else dataset_hf)
print(f"[uploader] upload_eval_results(path={run_dir!r}, hf_repo_id={hf_repo_id!r})")
upload_eval_results(os.environ.get("UPLOAD_DIR",run_dir), username=username, error_mode=os.environ.get("UPLOAD_MODE","skip_on_error"),
    hf_token=os.environ["HF_TOKEN"], hf_repo_id=hf_repo_id, register_benchmark=True,
    benchmark_name=benchmark_name, benchmark_version_hash=hashlib.sha256(benchmark_name.encode()).hexdigest())
print("[uploader] done.")
PY
echo "=============================================="
echo "Eval finished (SB_EXIT=$SB_EXIT). Artifacts: $RUN_DIR"
echo "=============================================="
