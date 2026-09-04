# Leonardo runtime / environment map

**Purpose:** which conda env / venv / container to use for which workstream on **CINECA Leonardo**, and the version facts that bite. Leonardo differs from Jupiter on every binary axis: **x86_64** (not aarch64), **A100-64GB** (not GH200), **CUDA 12.x / cu128 wheels** (not cu130), **SingularityPRO** (`/usr/bin/singularity`, **no `apptainer`, no podman**) — so Jupiter SIFs/wheels do NOT transfer. Access/preamble/paths/HF-upload live in `ops.md`; this is the runtime map.

Last verified: **2026-06-14**. Re-confirm with §3 if acting on this months later.

---

## 1. Decision table — which runtime for which workstream

| Workstream | Runtime | Stack |
|---|---|---|
| Orchestration, `hpc.launch`, eval listener, datagen, HF uploads, Supabase, agentic eval/datagen (Harbor + Daytona over proxychains) | **`otagent` conda** | torch 2.9.1+cu128, vLLM 0.16.0 (src), FA2 2.8.3 |
| **SkyRL RL** (gsm8k GRPO canary; SkyRL-native examples) | **MarinSkyRL uv venv in a singularity sandbox dir** | torch 2.8.0+cu128, vLLM 0.11.0, FA 2.8.3 |
| **SFT (Qwen3.5 9B/27B)** | **`sft-qwen35` conda** | torch 2.9.1+cu128, transformers 5.3+, deepspeed 0.18+ |
| **SERVE qwen3_5 / 3.6 models for agentic eval** | **`eval-qwen35` conda** | torch 2.11.0+cu128, transformers 5.12.1, vLLM 0.20.x (src, fork `penfever/working @ 76259c63a`) — §2f |
| Standard / pass@k downstream evals (Delphi #6279) | **`evalchemy-marin` conda** | lm-eval v0.4.12 |
| Compilers (for any from-source build) | **conda/mamba**, NOT system modules | gcc/gxx 14 + conda nvcc; `module load cuda/12.2` only for llama.cpp |

> Compute nodes have **no internet** → pre-download models on the login node; jobs use proxychains over an SSH SOCKS tunnel (`proxychains` provided by `otagent`).

---

## 2. The runtimes in detail

### 2a. `otagent` conda — the default (orchestration + eval + datagen + agentic)
- **Path:** `/leonardo_work/AIFAC_5C0_290/bfeuer00/miniforge3/envs/otagent/` (activate via the `ops.md` preamble).
- **Stack:** **torch 2.9.1+cu128**, **vLLM 0.16.0 built FROM SOURCE** against that torch (recipe + env scrubbing in `notes/leonardo.md` "Install"), **flash_attn 2.8.3+cu128torch2.9** (prebuilt x86 wheel from mjun0812 release **v0.9.0** — NOT the aarch64 wheel Jupiter uses).
- **Build gotchas (from-source vLLM):** `CUDA_HOME=$CONDA_PREFIX`, `CUDACXX/CMAKE_CUDA_COMPILER=$CONDA_PREFIX/bin/nvcc`, `LD_LIBRARY_PATH=$CONDA_PREFIX/lib:…`; `mamba install cmake ninja`; `VLLM_TARGET_DEVICE=cuda … uv pip install vllm==0.16.0 --no-build-isolation`. `-DCMAKE_CUDA_FLAGS=--allow-unsupported-compiler` if the host compiler is rejected.

### 2b. `sft-qwen35` conda — Qwen3.5 (9B/27B) SFT
- **Create:** `conda create -n sft-qwen35 python=3.12 && pip install uv`; `uv pip install --index-url https://download.pytorch.org/whl/cu128 "torch==2.9.1" …`; then in `sft/llamafactory`: `uv pip install "transformers>=5.3.0" "accelerate>=1.12" "deepspeed>=0.18" "datasets>=4.4" "peft>=0.18" "trl>=0.29" liger-kernel hf-kernels`.
- **Separate env required:** Qwen3.5's hybrid GatedDeltaNet+Attention arch needs **transformers ≥5.3**, which the default LLaMA-Factory/otagent stack (transformers 4.x) can't load. Use for any `sft/lf_configs/qwen3_5/*` run.
- **Leonardo-specific:** the launcher doesn't wire conda activation here — **hand-patch the sbatch** (conda activate + WORKDIR) per CLAUDE.md "SFT Launch on Leonardo". Cleanup = 8B path (root safetensors → skip consolidate; copy `preprocessor_config.json` from the base before upload). HF upload uses the `ops.md` sbatch-tunnel (login-node nohup fallback when cert expired).

### 2c. MarinSkyRL — uv venv inside a singularity SANDBOX (RL runtime)
Non-agentic SkyRL RL (gsm8k GRPO on Qwen2.5-1.5B-Instruct validated 2026-06-05, job 44478923 COMPLETED). **NO Harbor/Daytona/agentic yet** (proxyserver deferred).
- **Repo:** `marin-community/MarinSkyRL` `penfever/working` at `/leonardo_work/AIFAC_5C0_290/bfeuer00/code/MarinSkyRL`. Non-agentic recipe: `skyrl-train/examples/gsm8k/` via `python -m skyrl_train.entrypoints.main_base` (NOT main_tbench).
- **Image = writable singularity SANDBOX DIR, NOT a `.sif`:** `singularity build --sandbox $SCRATCH_FAST/marinskyrl_sandbox docker://anyscale/ray:2.51.1-slim-py312-cu128`. **`mksquashfs` OOM-kills on the Lustre login node + fatal `lustre.lov` xattr errors → `.sif` packaging deferred** (needs a non-login, xattr-clean build host). Exec via `singularity exec --nv`. Binary: `/usr/bin/singularity` (SingularityPRO 4.3.1).
- **Env = uv, not conda** (SkyRL-native): venv **`$SCRATCH_FAST/marin_venv`** (distinct from the sandbox image dir), built via `uv 0.9.4` + `uv sync --extra vllm` against the committed `uv.lock` → **torch 2.8.0+cu128, vLLM 0.11.0, flash-attn 2.8.3**. conda can't satisfy the pinned cu128/flashinfer/torch/vllm/flash-attn graph. MarinSkyRL is **`pip install -e`'d (editable)** into this venv.
- **⚠️ STALE EDITABLE-INSTALL TRAP — regenerate after any structural package change.** MarinSkyRL is editable-installed in `marin_venv`, so setuptools wrote a **meta-path finder** (`marin_venv/lib/python*/site-packages/__editable___skyrl_train_*_finder.py`). When a `git pull` **ADDS a `skyrl_train` subpackage** after the `pip install -e` ran, the install goes STALE: on a Ray actor the new subpackage resolves as an empty **"unknown location"** namespace → `ImportError: cannot import name <X> from 'skyrl_train.<new>' (unknown location)`. Manifests on remote-node FSDP workers at multi-node scale (driver cwd rescues it); a clean reinstall clears it. (`PYTHONPATH=$MARIN` does NOT fix it — meta-path precedes sys.path for the claimed namespace.)
  - **DETERMINISTIC pre-launch GATE (before spending N nodes):** from a NON-repo cwd inside the sandbox+venv: `python -c "from skyrl_train.dataset import PromptDataset; print('OK')"` must succeed (replicates the actor import context). ⚠️ Do NOT grep the finder file for the subpackage name — this finder style FS-walks children and never lists them literally (grep returns 0 even when healthy); the import repro is the ONLY reliable gate. If it fails `unknown location` → regenerate.
  - **FIX = regenerate the editable install** (env maintenance on committed code — like rebuilding a SIF, not a divergence change). Form matters (both `-m uv` and `-m pip` FAIL — this venv has neither as a module; `uv` is the standalone container binary). In the sandbox:
    ```
    singularity exec --nv -B /leonardo_work,/leonardo_scratch $SF/marinskyrl_sandbox bash -lc \
      "cd $MARIN/skyrl-train && uv pip install --python $SF/marin_venv/bin/python -e . --no-deps"
    ```
    Installs against **`$MARIN/skyrl-train`** (the package root where the finder lives), NOT `$MARIN`; offline (`--no-deps`; re-enumerates the finder).
  - **STANDING RULE:** after any MarinSkyRL pull that adds/moves/renames a `skyrl_train` subpackage, regenerate the editable install + run the import repro. Part of cluster-sync, same as `git pull`.
- **Gotchas:** Triton JIT needs a C compiler the ray base image lacks → bind host miniforge **gcc 14.3.0** onto PATH + set `CC`/`CXX` inside the container; `RAY_USAGE_STATS_ENABLED=0`. **`HOME`/`trainer.export_path` default to `${HOME}`** = read-only `/leonardo` inside the container → point `HOME` at writable scratch tmp, but **`trainer.export_path`/checkpoints MUST go to `$WORK` (`$CHECKPOINTS_DIR`), NOT `$SCRATCH_FAST`** — scratch is 1 TB/over-quota and a ckpt write fails `OSError [Errno 122] Disk quota exceeded` (ops.md "WRITE-PATH MANDATE"). Scratch = ephemeral caches only.
- **Configs:** `hpc/skyrl_standard/leonardo/{run_gsm8k_canary.sh, sbatch_gsm8k_canary.sh, note.txt}` (commit `44afed58`). sbatch = `--account=AIFAC_5C0_290 --partition=boost_usr_prod`, 1 node `--gres=gpu:a100:4` (debug QOS `boost_qos_dbg` ≤30min). Prestage on LOGIN node (compute has no internet): model → `$WORK/data/hub`, gsm8k parquet → `$WORK/data/gsm8k`. `WANDB_MODE=offline`.

### 2d. `skyrl_megatron_vllm0202rc0_r3_sandbox` + `pytorch_2509_sbx` — cu13 cross-cluster twin (BUILT, PARKED)
The x86/A100 analogue of Jupiter's `skyrl_megatron_vllm0202rc0_r3.sif`: SkyRL editable (`penfever/SkyRL @ 2ab513a6`) + Megatron-core 0.14.0 + TE + flash-attn + **vLLM fork `penfever/working @ 5d7319dd1`** (0.20.2rc0 + native R3 routed-experts capture + the DCP GQA-LSE fp32 fix). Built as **writable singularity sandbox dirs** at `$WORK/containers/skyrl_megatron_vllm0202rc0_r3_sandbox/` and `$WORK/containers/pytorch_2509_sbx/` (NGC `nvcr.io/nvidia/pytorch:25.09-py3`, 19 G) — NOT `.sif` (mksquashfs OOM/xattr blocker on Lustre login). **PARKED**: no live RL uses them; recipe committed under `.agents/ops/leonardo/sif_build/recipes/{README_vllm0202rc0_r3_leonardo.md, build_vllm0202rc0_r3_leonardo.sbatch}` so they're rebuildable. Retire only if the cross-cluster-twin effort is abandoned.
- **CUDA-13 via FORWARD COMPATIBILITY — GATE PASSED (2026-06-16).** Leonardo A100 nodes load NVIDIA kernel driver **`535.274.02`** (native CUDA ≤12.2); `singularity --nv` binds that host `libcuda` (a container can't replace the kernel driver). CUDA **Forward Compatibility** (`cuda-compat-13` package, bundled in NGC cu13 images at `/usr/local/cuda/compat`) ships a newer userspace `libcuda.so` that lets a cu13 toolkit run on an older **datacenter** driver — A100 qualifies. The NGC image wires the compat libs via its own ldconfig (`compat/lib` → `lib.real`), so no manual `LD_LIBRARY_PATH` reorder needed under `--nv`; if a future image doesn't, set `SINGULARITYENV_LD_LIBRARY_PATH=/usr/local/cuda-13.0/compat/lib.real`. **Verified:** a real CUDA-13 fp32 matmul ran on an A100 (host driver 535.274.02) — `torch 2.9.0a0+…nv25.09`, `torch.version.cuda 13.0`, cap `(8,0)`, `/proc/self/maps` confirms `libcuda.so.580.82.07` from `/usr/local/cuda-13.0/compat/lib.real`. **The 535 branch is within cu13's forward-compat floor** on the A100.
- **Matched with Jupiter (both paths):** vLLM fork commit `5d7319dd1`, R3 native capture, DCP fp32 fix, model archs (Gemma4/Qwen3Moe/Qwen3Next), SkyRL/Megatron/TE stack, `TORCH_CUDA_ARCH_LIST=8.0` (A100, vs 9.0 GH200), GDN/FlashQLA overlay **omitted** (deferred; vanilla GDN still runs).
- **Build recipe (two-phase sbatch):** A = SkyRL+Megatron+flash-attn; B = vLLM-from-source against in-base torch 2.8 via `use_existing_torch.py`, arch 8.0, offline wheelhouses. **Build sandbox on WORK, not SCRATCH_FAST.** Runtime env: `VLLM_ATTENTION_BACKEND=FLASH_ATTN`, `VLLM_USE_FLASHINFER_SAMPLER=0`, `LIBRARY_PATH=/.singularity.d/libs` for tp>1.

### 2e. `evalchemy-marin` conda — standard / pass@k downstream evals (Delphi #6279)
- **The ONE canonical evalchemy clone:** `/leonardo_work/AIFAC_5C0_290/bfeuer00/code/evalchemy-marin` — remote `origin = github.com/marin-community/evalchemy.git`, branch `main`. The **`evalchemy-marin` conda env** is the editable install against it (lm-eval v0.4.12). All recent Delphi #6279 pass@k + standard `SCORES.md` rows used this env+clone; the live `evalchemy_eval.sbatch` `cd`s here.
- **Use for:** MATH500 / gsm8k / AIME24 (`eval/evalchemy/*.sbatch`) + native pass@k (`eval.eval --num_samples N --pass_at_k …`; unbiased estimator in `eval/passk.py`).
- **Do NOT re-create** `code/evalchemy` or `code/evalchemy-resume-test` — both deleted as redundant (2026-06-18/22); `evalchemy-marin` is the only clone.

### 2f. `eval-qwen35` conda — SERVE qwen3_5 / qwen3.6 models for agentic eval
- **Path:** `/leonardo_work/AIFAC_5C0_290/bfeuer00/miniforge3/envs/eval-qwen35/`.
- **Purpose:** the ONLY env that can **vLLM-serve** `model_type: qwen3_5` / `qwen3_5_moe` models (`allenai/tmax-9b`, `allenai/tmax-27b`, `Qwen/Qwen3.5-35B-A3B`, `Qwen/Qwen3.6-35B-A3B`) for **agentic eval** via the unified eval listener. (`otagent` has vanilla vLLM 0.16.0 — no qwen3_5 impl — + transformers 4.x, can't parse the config; `sft-qwen35` is training-only, no vLLM-serve.)
- **Stack:** **torch 2.11.0+cu128** (+ triton 3.6.0, torchvision 0.26.0), **transformers 5.12.1** (≥5.3 required so the hybrid GatedDeltaNet+Attention config parses), **vLLM 0.20.x built FROM SOURCE from our FORK** `mlfoundations/vllm` branch `penfever/working` @ **`76259c63a`** (contains `vllm/model_executor/models/qwen3_5.py` + `Qwen3_5ForConditionalGeneration` / `Qwen3_5MoeForConditionalGeneration` in the registry; reports `0.1.dev16611+g76259c63a`). Fork clone: `/leonardo_work/AIFAC_5C0_290/bfeuer00/code/vllm-fork` (detached @ `76259c63a`; editable-installed). ⚠ **torch is 2.11.0, NOT otagent's 2.9.1** — the fork's `_C_stable_libtorch` extension uses the torch-2.10 stable-ABI macro `TORCH_BOX`, absent in torch 2.9.1 → 2.9.1 can't compile this fork. ⚠ **NO standalone `flash_attn`** — mjun0812 has no x86/cp312/torch2.11/cu128 wheel; vLLM serving uses its OWN bundled `vllm_flash_attn` (`_vllm_fa2_C`/`_vllm_fa3_C`), so the standalone is unnecessary.
- **⚠ LOAD-BEARING RUNTIME FLAGS (set in any serve sbatch — without them the serve crashes):**
  - `export LD_LIBRARY_PATH=$CONDA_PREFIX/lib:$LD_LIBRARY_PATH` — bundled `_vllm_fa*_C.abi3.so` need `CXXABI_1.3.15` (conda gcc-14); host `/lib64/libstdc++.so.6` only has `CXXABI_1.3.11`.
  - `export VLLM_USE_FLASHINFER_SAMPLER=0` — else flashinfer JIT-link fails `ld: cannot find -lcuda` (flashinfer looks in `$CONDA_PREFIX/lib64/stubs`, which conda cuda-toolkit doesn't create).
  - `export LIBRARY_PATH=$CONDA_PREFIX/targets/x86_64-linux/lib/stubs:$LIBRARY_PATH` — exposes the `libcuda` stub for any other runtime JIT link.
  - `export VLLM_ATTENTION_BACKEND=FLASH_ATTN`.
  - **Text-only checkpoints of a VL arch (e.g. `allenai/tmax-9b`):** `config.json` declares `vision_config` + `image_token_id` but ships **no `preprocessor_config.json`** → vLLM's multimodal path fails. Pass **`limit_mm_per_prompt={"image":0,"video":0}`** (LLM kwarg) / `--limit-mm-per-prompt image=0,video=0` (serve) to skip it (or copy a `preprocessor_config.json` from the base Qwen3.5-9B).
- **⚠ ROUTING GOTCHA — per-model env override requires the baseline config.** The per-model `conda_env: eval-qwen35` (+ TP/DP/trust_remote_code) lives in `eval/configs/baseline_model_configs_minimal.yaml` and is loaded by the listener ONLY when given that file. **FIX (committed 2026-06-25):** `eval/clusters/leonardo.yaml` now carries a top-level `baseline_model_configs:` default and the listener resolves `--baseline-model-configs` as **CLI > cluster-config > None** (+ logs which source it used, WARNs loudly when neither set). So a Leonardo listener picks up per-model overrides even if the operator forgets the CLI flag. Always prefer the canonical `eval-agentic-launch` invocation (passes the flag explicitly). Without it the serve silently falls back to **otagent** (vanilla vLLM 0.16 / transformers 4.x, TP=1, no trust_remote_code) → `ValidationError: model type qwen3_5_moe not recognized`.
- **Build gotchas (additional to §2a):** compute node has **NO internet** → from-source recipe is SPLIT and ALL deps pre-staged:
  - **CUDA toolkit:** `mamba install -c nvidia -c conda-forge cuda-toolkit=12.8 gxx_linux-64=14 gcc_linux-64=14` (conda nvcc 12.8). ⚠ This installs CUDA headers ONLY under `$CONDA_PREFIX/targets/x86_64-linux/include/` (NOT symlinked into `$CONDA_PREFIX/include/`) → torch's `Caffe2Config.cmake` fails `Could NOT find CUDA (missing: CUDA_INCLUDE_DIRS)`. FIX: symlink every entry from `targets/x86_64-linux/include/` into `$CONDA_PREFIX/include/` so `cuda_runtime.h` resolves top-level.
  - **(1) LOGIN node (internet):** `python use_existing_torch.py` (strips the fork's `torch==2.11.0` pin so it builds against the in-env torch — keep in-env torch AT 2.11.0), then `uv pip install -r requirements/common.txt -r requirements/cuda.txt` (pulls transformers 5.12.1, flashinfer, xgrammar, etc.).
  - **(1b) Pre-clone the 6 CMake-FetchContent deps** into `$WORK/vllm_build_deps/` (with `git submodule update --init --recursive`): cutlass (v4.4.2), vllm-flash-attn (bce29425), triton (v3.6.0, sparse-checkout `python/triton_kernels`), deepgemm (891d57b4), flashmla (a6ec2ba7), qutlass (830d2c45). vLLM git-clones these at configure time → offline every clone fails `Could not connect to github`. (deepgemm/flashmla/qutlass are Hopper-only and skip their compile on arch 8.0, but `FetchContent_MakeAvailable` still clones → must stage too.)
  - **(2) GPU compute node, OFFLINE compile (~5.5 h wall, 342 targets, arch 8.0):** export the 6 SRC_DIR overrides — `VLLM_CUTLASS_SRC_DIR`, `VLLM_FLASH_ATTN_SRC_DIR`, `TRITON_KERNELS_SRC_DIR` (→ `.../triton/python/triton_kernels/triton_kernels`), `DEEPGEMM_SRC_DIR`, `FLASH_MLA_SRC_DIR`, `QUTLASS_SRC_DIR` — plus `CUDA_HOME=$CONDA_PREFIX`, `TORCH_CUDA_ARCH_LIST=8.0`, `UV_OFFLINE=1`, then `VLLM_TARGET_DEVICE=cuda uv pip install -e . --no-build-isolation --no-deps --offline`. Use ABSOLUTE `$CONDA_PREFIX/bin/{python,uv,ninja,nvcc}` paths (conda-activate-on-PATH flaky in sbatch). ≥6 h walltime (cutlass GEMM kernels front-load slowly). Build artifacts: sbatch `$WORK/build_vllm_eq35_v3.sbatch`, deps `$WORK/vllm_build_deps/`, log `$WORK/vllm_build_eq35_v3_<jid>.log`.
- **Gates (✅ 2026-06-23/25):** (1) `AutoConfig.from_pretrained('allenai/tmax-9b').model_type == 'qwen3_5'`; (2) both `Qwen3_5ForConditionalGeneration` + `Qwen3_5MoeForConditionalGeneration` in `ModelRegistry.get_supported_archs()`; (3) `'qwen3_5_moe' in transformers.models.auto.configuration_auto.CONFIG_MAPPING` → True; (4) TP=4 serve of tmax-9b → coherent generation (job 47715931). Env serves both dense `qwen3_5` and MoE `qwen3_5_moe`; no transformers upgrade or vLLM rebuild needed for the MoE arch.

## 3. VERIFY before you trust

```bash
# otagent
/leonardo_work/AIFAC_5C0_290/bfeuer00/miniforge3/envs/otagent/bin/python -c "import torch,vllm; print('otagent', torch.__version__, vllm.__version__)"   # → 2.9.1+cu128 / 0.16.0
# sft-qwen35
/leonardo_work/AIFAC_5C0_290/bfeuer00/miniforge3/envs/sft-qwen35/bin/python -c "import torch,transformers; print('sft', torch.__version__, transformers.__version__)"  # → 2.9.1+cu128 / 5.3+
# eval-qwen35 (run on a GPU node WITH the §2f runtime flags)
/leonardo_work/AIFAC_5C0_290/bfeuer00/miniforge3/envs/eval-qwen35/bin/python -c "import torch,transformers,vllm; print('eval-qwen35', torch.__version__, transformers.__version__, vllm.__version__)"  # → 2.11.0+cu128 / 5.12.1 / 0.1.dev16611+g76259c63a
/leonardo_work/AIFAC_5C0_290/bfeuer00/miniforge3/envs/eval-qwen35/bin/python -c "from transformers import AutoConfig; print(AutoConfig.from_pretrained('allenai/tmax-9b').model_type)"  # → qwen3_5
/leonardo_work/AIFAC_5C0_290/bfeuer00/miniforge3/envs/eval-qwen35/bin/python -c "from vllm.model_executor.models.registry import ModelRegistry; print('Qwen3_5ForConditionalGeneration' in ModelRegistry.get_supported_archs())"  # → True
# SkyRL sandbox venv
singularity exec --nv $SCRATCH_FAST/marinskyrl_sandbox python -c "import torch,vllm; print('skyrl', torch.__version__, vllm.__version__)"   # → 2.8.0+cu128 / 0.11.0
# SkyRL editable-install freshness (§2c stale-finder trap) — from a NON-repo cwd (matches a Ray actor):
cd /tmp && singularity exec --nv -B /leonardo_work,/leonardo_scratch $SCRATCH_FAST/marinskyrl_sandbox $SCRATCH_FAST/marin_venv/bin/python -c "from skyrl_train.dataset import PromptDataset; print('editable OK', PromptDataset)"   # MUST print OK; if ImportError 'unknown location' → regenerate (§2c FIX). NOT `-m uv`/`-m pip` — not modules here; uv = standalone container binary.
```

---

## 4. Hardware / filesystems (the constraints that shape the above)

- **Booster nodes:** 32-core Ice Lake (x86_64) @ 2.6GHz, **4× A100-64GB**, 512 GB RAM, 3456 nodes. CUDA 12.2/12.3/12.6 modules; gcc 12.2 system / conda gcc 14.
- **Filesystems:** HOME `/leonardo/home/userexternal/bfeuer00` (50 GB, NFS, persistent) — too small for envs; **WORK** `/leonardo_work/AIFAC_5C0_290` (~1.465 PB shared GPFS, persistent — code/envs/HF-cache/experiments live here); **SCRATCH/fast** `/leonardo_scratch/fast/AIFAC_5C0_290` (1 TB shared Lustre, **auto-purged**, fastest — vLLM/Triton/FlashInfer caches + job tmp; often OVER quota, may need project cleanup). Env vars in `hpc/dotenv/leonardo.env`: `HF_HOME`/`HF_HUB_CACHE=$WORK/data/hub`, `VLLM_CONFIG_ROOT`/`TRITON_CACHE_DIR`/`FLASHINFER_WORKSPACE_BASE=$SCRATCH_FAST/vllm_cache`.
- **Account:** `AIFAC_5C0_290` (the expired `EUHPC_E03_068` / `CMPNS_E03_068` are dead — do NOT use). Partition `boost_usr_prod`, max wall 24h (`--time 23:59:00`), debug QOS `boost_qos_dbg` ≤30min. Budget: `saldo -b`; storage: `cinQuota`/`cindata`.

---

## 5. Canonical env set — anything else is cruft (inventory reconciled 2026-06-21)

These are ALL the runtimes we intentionally keep. If you find an env/sandbox/clone NOT on this list, it's a candidate to retire (audit before assuming).

- **conda (`$WORK/miniforge3/envs/`):** `otagent` (default), `sft-qwen35` (Qwen3.5 SFT), `eval-qwen35` (SERVE qwen3_5/3.6 — §2f), `evalchemy-marin` (Delphi #6279 evals), `ajudge` (LLM-judge tool, rarely used).
- **RL runtime (`$SF`):** `marinskyrl_sandbox` (singularity sandbox) + `marin_venv` (uv venv, editable MarinSkyRL) — torch 2.8/vLLM 0.11. **What live multi-node RL uses** (not the cu13 twin).
- **cu13 cross-cluster twin (`$WORK/containers/`):** `skyrl_megatron_vllm0202rc0_r3_sandbox` (22G) + `pytorch_2509_sbx` (19G) — both built, **PARKED** (rebuildable from `sif_build/recipes/`). Keep while the cross-cluster-twin option is open.
- **code clones (`$WORK/code/`):** `OpenThoughts-Agent`, `MarinSkyRL`, `harbor`, `evalchemy-marin`, `ajudge`, `vllm-fork` (`mlfoundations/vllm` fork @ `76259c63a` — source for `eval-qwen35`'s from-source vLLM, editable-installed into that env; §2f).
- **RETIRED (do NOT re-create):** deprecated `evalchemy` 0.4.9.1 conda env, conda `pkgs` cache, stale `$SF` dirs (`ray_tmp`/`canary_home`/`apptainer_cache`), one-off forward-compat/build artifacts, `code/abb` (700M, unidentified), `code/evalchemy`, `code/evalchemy-resume-test`, `code/SkyRL`.
