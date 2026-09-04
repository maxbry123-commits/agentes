#!/bin/bash
#SBATCH --job-name=mega_densemixer
#SBATCH --partition=beta
#SBATCH --account=ny_chinmayh_datacomp
#SBATCH --qos=standard
#SBATCH --gres=gpu:b200:1
#SBATCH --cpus-per-task=32
#SBATCH --mem=200G
#SBATCH --time=02:00:00
#SBATCH --output=/mnt/home/bf996/logs/mega_densemixer_%j.out

# =============================================================================
# Empire AI Beta — add the DenseMixer package to the SFT (system-python) layer.
#   mega_final.sqsh  ->  + `densemixer==1.0.1` into /usr/bin/python  ->  mega_final_dm.sqsh
# WHY: axolotl's integrations/densemixer/DenseMixerPlugin hard-checks
#   importlib.util.find_spec("densemixer") at pre_model_load and raises
#   "DenseMixer is not installed" if absent — and it was NOT in mega_final
#   (verified live: ModuleNotFoundError). densemixer 1.0.1 is a pure-Python
#   py3-none-any wheel (deps torch>=2.0 + transformers>=4.51, both already in the
#   SFT env: torch 2.8.0a0 / transformers 5.12.1) -> install --no-deps so torch/
#   transformers are untouched (same ABI-safe pattern as torchao/deepspeed in Job A).
# Self-contained sbatch (survives ssh-socket drops). enroot create-from-.sqsh in
# node-local /tmp -> pip install inside --rw -> enroot export to ~/images/.
# =============================================================================
set -euxo pipefail

export USER="${USER:-bf996}"
export ENROOT_CACHE_PATH=/tmp/$USER/enroot-cache
export ENROOT_DATA_PATH=/tmp/$USER/enroot-data
export ENROOT_TEMP_PATH=/tmp/$USER/enroot-tmp
export ENROOT_RUNTIME_PATH=/tmp/$USER/enroot-run
mkdir -p "$ENROOT_CACHE_PATH" "$ENROOT_DATA_PATH" "$ENROOT_TEMP_PATH" "$ENROOT_RUNTIME_PATH"

BASE=/mnt/home/bf996/images/mega_final.sqsh
OUT=/mnt/home/bf996/images/mega_final_dm.sqsh
NAME="megaDM_${SLURM_JOB_ID}"

echo "=== [$(date)] enroot create $NAME from $BASE ==="
enroot create --name "$NAME" "$BASE"
ROOTFS="$ENROOT_DATA_PATH/$NAME"
ls -ld "$ROOTFS/root"

# stage the transformers-5.x DenseMixer port into the sandbox (overwrites the pip file).
# densemixer 1.0.1's qwen3_moe_custom.py assumes the transformers 4.x Qwen3MoE API and
# crashes on 5.12 (`'tuple' object has no attribute 'to'` at first forward, job 31645).
cp /mnt/home/bf996/scripts/densemixer_qwen3moe_tf5.py "$ROOTFS/root/densemixer_qwen3moe_tf5.py"

cat > "$ROOTFS/root/setup.sh" <<'SETUP'
set -euxo pipefail
export PATH=/usr/local/bin:/usr/local/cuda/bin:/usr/bin:/bin
hash -r
unset PYENV_ROOT PYENV_VERSION PYENV_SHELL || true
unset PIP_CONSTRAINT || true            # NGC base pins torch 2.8 via PIP_CONSTRAINT — clear it
export PIP_NO_CACHE_DIR=1
PY=/usr/bin/python

$PY --version
$PY -c "import torch, transformers; print('pre torch', torch.__version__, '| transformers', transformers.__version__)"

# pure-python, deps already satisfied -> --no-deps keeps torch/transformers pinned to the NGC build.
$PY -m pip install --no-deps --break-system-packages densemixer==1.0.1

# ---- overwrite the incompatible qwen3_moe custom forward with the transformers-5.x port ----
DST=$($PY -c "import densemixer.models.qwen3_moe_custom as m; print(m.__file__)")
echo "densemixer qwen3_moe_custom.py -> $DST"
cp /root/densemixer_qwen3moe_tf5.py "$DST"
grep -q "tf5-ported-densemixer" "$DST" || { echo "PORT MARKER MISSING"; exit 1; }

# ---- GATE: import path the plugin uses + the port is in place ----
$PY - <<'PYGATE'
import importlib.util as u
assert u.find_spec("densemixer") is not None, "densemixer spec still missing"
import densemixer, inspect
from densemixer.patching import apply_olmoe_patch, apply_qwen2_moe_patch, apply_qwen3_moe_patch  # noqa: F401
from densemixer.models.qwen3_moe_custom import CustomQwen3MoeSparseMoeBlock
src = inspect.getsource(CustomQwen3MoeSparseMoeBlock.forward)
assert "tf5-ported-densemixer" in src, "port not active"
import torch, transformers
print("GATE densemixer", getattr(densemixer, "__version__", "?"),
      "| torch", torch.__version__, "| transformers", transformers.__version__, "| PORT active")
PYGATE
echo "SETUP_DONE_OK"
SETUP

echo "=== [$(date)] enroot start --root --rw $NAME -> run setup.sh ==="
enroot start --root --rw "$NAME" bash -lc 'bash /root/setup.sh'

echo "=== [$(date)] enroot export -> $OUT ==="
rm -f "$OUT"
enroot export -o "$OUT" "$NAME"

echo "=== cleanup ==="
enroot remove -f "$NAME" || true
rm -rf "$ROOTFS" || true
ls -lh "$OUT"
echo "JOB_DENSEMIXER_COMPLETE [$(date)]"
