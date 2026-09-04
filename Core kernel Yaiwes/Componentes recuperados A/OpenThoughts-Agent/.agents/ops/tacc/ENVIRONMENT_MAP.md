# TACC Vista runtime / environment map

TACC Vista conda runtime map. Its aarch64 GH200 96GB single-GPU nodes, CUDA 12.8/cu128 `sm_90` wheels, and bare-metal-only environment differ from Leonardo; Leonardo SIFs/wheels do not transfer. Access/preamble/paths/HF upload/eval launch: `ops.md`.

Last verified: **2026-06-27** (from `ops.md` + the fork-vLLM build + the tmax-9b serve canary). Re-confirm with §3 if acting on this months later.

---

## 0. TL;DR — the discriminators

> - **otagent conda** = the default runtime for EVERYTHING — orchestration, eval, datagen, agentic eval, AND serving qwen3_5/3.6 models — **torch 2.11.0+cu128, vLLM 0.1.dev16611+g76259c63a (fork built from source), transformers 5.12.1, NO standalone flash_attn** (SDPA only — no aarch64 wheel exists for torch 2.11+cu128).
> - Unlike Leonardo (where otagent has vanilla vLLM 0.16 + transformers 4.x, and a separate `eval-qwen35` env is needed for qwen3_5 serving), **TACC's otagent was built from scratch with the fork-vLLM + transformers 5.12.1** — so it resolves `qwen3_5` / `qwen3_5_moe` natively without a separate env.
> - **vllm_sandboxes conda** = standalone vLLM testing (vanilla, not the fork).
> - **evalchemy conda** = standard / pass@k downstream evals (Delphi scaling-laws math suite).
> - Compute nodes have **full direct internet egress** — NO proxychains / SSH-SOCKS5 / step-ca cert needed (the big simplification vs Leonardo).
> - **GPUs are NOT a SLURM gres** → request whole NODES; **1 GH200 per node** → everything is **TP=1**.

---

## 1. Decision table — which runtime for which workstream

| Workstream | Runtime | Stack |
|---|---|---|
| Orchestration, `hpc.launch`, eval listener, datagen, HF uploads, Supabase | **`otagent` conda** | torch 2.11.0+cu128, fork-vLLM (src), transformers 5.12.1 |
| Agentic eval / datagen (Harbor + Daytona, direct egress) | **`otagent` conda** | same |
| **Serving qwen3_5 / qwen3_5_moe** (tmax-9b/27b, Qwen3.5/3.6-35B-A3B) | **`otagent` conda** | same (fork-vLLM resolves these archs natively) |
| SFT (Qwen3 / Qwen3.5) | **`otagent` conda** (+ LLaMA-Factory editable) | same + deepspeed 0.18, liger-kernel, peft, trl |
| Standalone vLLM testing | **`vllm_sandboxes` conda** | vanilla vLLM + gcc 15.1 |
| Standard / pass@k evals (MATH-500, gsm8k, AIME24) | **`evalchemy` conda** | lm-eval v0.4.x |
| RL (SkyRL) | **`otagent` conda** (SkyRL `arm` branch) | see `ops.md` SkyRL TACC setup |

---

## 2. The runtimes in detail

### 2a. `otagent` conda — orchestration + eval + datagen + agentic + qwen3_5 serving (the default)
- **Path:** `/scratch/10635/penfever/miniconda3/envs/otagent/` (activate via the `ops.md` preamble: `source $SCRATCH/miniconda3/bin/activate otagent`).
- **Stack:** **torch 2.11.0+cu128** (+ torchvision 0.26.0, torchaudio 2.11.0, triton 3.6.0), **transformers 5.12.1** (bumped 2026-06-26 from 4.57.3 — gives native `qwen3_5` support + aligns with Leonardo's `eval-qwen35`), **vLLM `0.1.dev16611+g76259c63a`** (fork `mlfoundations/vllm` @ `76259c63a` built FROM SOURCE for aarch64 + sm_90 — resolves `Qwen3_5ForConditionalGeneration` + `Qwen3_5MoeForConditionalGeneration` in the registry), harbor 0.8.0 (editable, `main`), flashinfer-python 0.6.3.
- **SFT extras:** deepspeed 0.18.0, liger-kernel 0.8.0, peft 0.19.1, trl 1.6.0, llamafactory 0.9.4.dev0 (editable at `sft/llamafactory`), gradio 6.17.3, torchao 0.17.0.
- **NO standalone flash_attn** — no prebuilt aarch64 wheel exists for torch 2.11+cu128 (checked mjun0812 v0.9.39–0.9.41: no cu128/aarch64 combos). vLLM serving uses **SDPA** (PyTorch native scaled dot-product attention). The fork-vLLM auto-falls-back to SDPA when FA2 is unavailable.
- **Use for:** everything — `hpc.launch`, the unified eval listener (`eval/tacc/eval_harbor.sbatch`, TP=1, 1 node, 24h), datagen, uploads, SFT (via LLaMA-Factory editable), AND serving qwen3_5/qwen3_5_moe models for agentic eval (the fork-vLLM + transformers 5.12.1 handles this natively — no separate `eval-qwen35` env needed, unlike Leonardo).
- **⚠ transformers 4.x → 5.x jump in the PRIMARY env (2026-06-26):** eval/serving is proven fine (the fork-vLLM runs on 5.12.1 on Leonardo), but other otagent workflows (datagen, SFT-llamafactory, harbor) should be re-smoke-tested before relying on them — the bump likely cascaded other deps.
- **Build gotchas (from-source fork-vLLM on aarch64):**
  - **Builds MUST run on a compute node** — the login node is shared and `uv`/Rust tooling OOMs (`memory allocation of N bytes failed` → `Aborted`). Use `srun -p gg` for a CPU allocation (the nvcc compile is host-side, doesn't need a GPU).
  - **`salloc` is BLOCKED on Vista** — interactive sessions must use `idev` (2h cap on `gh-dev`, too short for the ~hour build). Submit the build as a **CPU-only `sbatch` batch job**.
  - **Toolchain:** `module purge && module load gcc/13.2.0 cuda/12.8` (NOT default `nvidia/24.7` which only ships cuda/12.5; `cuda/12.8` won't load until a real gcc is loaded first).
  - **Build flags:** `TORCH_CUDA_ARCH_LIST="9.0"` (Hopper GH200), `CUDA_HOME=$TACC_CUDA_DIR`, `VLLM_TARGET_DEVICE=cuda`, `MAX_JOBS=32`, `NVCC_THREADS=4`. Build with `--no-build-isolation` against the env's torch 2.11.0.
  - **Pre-install build deps:** `setuptools<81 setuptools-scm packaging wheel ninja jinja2 cmake` (env ships ninja but NOT setuptools_scm). Install these WITH deps (not `--no-deps`) — setuptools-scm 10.x needs its `vcs-versioning` helper.
  - Build recipe captured in `$SCRATCH/build_vllm.sbatch` (clone → toolchain → build → install → import-verify). Fork clone: built against `mlfoundations/vllm` @ `76259c63a` (the same commit Leonardo's `eval-qwen35` uses).

### 2b. `vllm_sandboxes` conda — standalone vLLM testing
- **Path:** `/scratch/10635/penfever/miniconda3/envs/vllm_sandboxes/`.
- **Stack:** vanilla vLLM (NOT the fork) + gcc 15.1.0.
- **Use for:** quick standalone `vllm serve` testing. NOT for agentic eval (the unified eval listener uses `otagent`).
- **Gotchas:** requires `module load gcc/15.1.0` + `TRITON_CC=$(which gcc)` + conda libstdc++ on `LD_LIBRARY_PATH`.

### 2c. `evalchemy` conda — standard / pass@k downstream evals
- **Path:** `/scratch/10635/penfever/miniconda3/envs/evalchemy/`.
- **Clone:** `$SCRATCH/evalchemy` (the canonical evalchemy clone).
- **Use for:** MATH-500 / gsm8k / AIME24 standard evals via lm-eval. Activated via `cd $SCRATCH/evalchemy && conda activate evalchemy`.

---

## 3. VERIFY before you trust

```bash
# otagent (the default — torch/vllm/transformers)
/scratch/10635/penfever/miniconda3/envs/otagent/bin/python -c "import torch,vllm,transformers; print('otagent', torch.__version__, vllm.__version__, transformers.__version__)"
# → 2.11.0+cu128 / 0.1.dev16611+g76259c63a / 5.12.1

# otagent qwen3_5 resolution (dense + MoE)
/scratch/10635/penfever/miniconda3/envs/otagent/bin/python -c "
from transformers import AutoConfig
from vllm.model_executor.models.registry import ModelRegistry
c = AutoConfig.from_pretrained('Qwen/Qwen3.5-35B-A3B')
print('model_type:', c.model_type)
print('qwen3_5_moe in transformers:', 'qwen3_5_moe' in __import__('transformers').models.auto.configuration_auto.CONFIG_MAPPING)
print('Qwen3_5MoeForConditionalGeneration in vLLM:', 'Qwen3_5MoeForConditionalGeneration' in ModelRegistry.get_supported_archs())
"
# → model_type: qwen3_5_moe / True / True

# vllm_sandboxes
/scratch/10635/penfever/miniconda3/envs/vllm_sandboxes/bin/python -c "import vllm; print(vllm.__version__)"
```

---

## 4. Hardware / filesystems (the constraints that shape the above)

- **GH200 nodes:** Grace Hopper superchip, **aarch64** (ARM64) @ 3.5GHz (Grace CPU 72-core, single socket), **1× GH200 96GB** unified memory, 480 GB RAM. GPU is NOT a SLURM gres — each node has exactly ONE whole-node-allocated 96GB GPU. Everything runs at **TP=1** (a multi-GPU TP would need multi-node vLLM, which is complex on Vista).
- **GPU memory:** GH200 unified memory is used as filesystem cache and **cannot always be reclaimed** after an application exits → occasional hung nodes requiring reboot. Avoid relying on clean memory reclamation.
- **Filesystems:** **SCRATCH** `/scratch/10635/penfever` (unlimited quota — code/envs/HF-cache/checkpoints/eval-jobs all live here); **HOME** `/home1/10635/penfever` (23.3 GB — login dotfiles only, do NOT write large data); **WORK** `/work/08663` (1,024 GB — project work, currently unused).
- **Account:** `CCR24067` — **107,765 SUs** (expires 2025-12-31; check `bbalance` periodically). Partitions: `gh`/`gg` (48h max, 20 running / 40 submit), `gh-dev` (2h cap, 1 running, 3 submit — dev only).
- **Internet:** compute nodes have **FULL direct egress** (verified: `huggingface.co`, `app.daytona.io` return 200) — NO proxy / SSH-SOCKS5 / step-ca cert needed. The TACC sbatch has NO `proxied()` wrapper, NO proxychains.

---

## 5. Canonical env set — anything else is cruft

**conda (`$SCRATCH/miniconda3/envs/`):** `otagent` (default — orch/eval/datagen/agentic/SFT/qwen3_5-serving, fork-vLLM @ 76259c63a + transformers 5.12.1), `vllm_sandboxes` (standalone vLLM testing), `evalchemy` (Delphi math evals).

**No containers.** Vista has no Singularity/Apptainer — everything is bare-metal conda. This is simpler than Leonardo (which has 3+ singularity sandboxes) but means the from-source vLLM build must succeed natively on aarch64.

**code clones (`$SCRATCH/`):** `OpenThoughts-Agent` (this repo), `harbor` (editable, `main` branch; migrate a stale clone on next touch), `evalchemy` (standard evals clone).

---

## 6. Serving qwen3_5 / qwen3_5_moe on TACC (tmax, Qwen3.5/3.6 family)

TACC's `otagent` env is the **only env needed** to serve these models — unlike Leonardo's split (`otagent` for standard models, `eval-qwen35` for qwen3_5). The fork-vLLM + transformers 5.12.1 are already in `otagent`.

### Serve flags for qwen3_5 / qwen3_5_moe models

These flags MUST be set in the serve sbatch / baseline config (without them the serve crashes):

1. **`limit_mm_per_prompt: '{"image":0,"video":0}'`** — these checkpoints declare a VL arch (`vision_config` + image/video token ids) but ship text-only weights. Without this flag, vLLM eagerly builds a `MultiModalBudget` at init → `get_image_processor()` → loads `preprocessor_config.json` (absent) → `OSError`, fatal, 0 trials. (Confirmed in jobs 787630/787631, 2026-06-25.)
2. **`trust_remote_code: true`** — needed for the qwen3_5 model class.
3. **`tensor_parallel_size: 1`** — Vista has 1 GPU/node. A 35B-A3B MoE (~34.4B total / ~69 GB bf16) fits the 96 GB GH200 at TP=1 with ~17 GB KV headroom at 32k context (the hybrid arch grows KV on only 10/40 layers, so 32k is cheap).
4. **`max_model_len: 32768`** — eval parity with all other clusters.
5. **`agent_kwargs: ['extra_body={"chat_template_kwargs":{"enable_thinking":true}}']`** — Qwen3.5/3.6 are hybrid thinking models; this enables the `<think>` block (thinking ON by default in the chat template, but explicit is safer).
6. **NO `VLLM_ATTENTION_BACKEND=FLASH_ATTN`** — TACC has no flash_attn. The fork-vLLM auto-falls-back to SDPA. (Unlike Leonardo's `eval-qwen35` which sets `VLLM_ATTENTION_BACKEND=FLASH_ATTN`.)

### Baseline config entries

The TACC baseline config (`eval/clusters/tacc_baseline_model_configs.yaml`) must carry per-model entries for qwen3_5 / qwen3_5_moe models with the flags above. Without an explicit entry, these models fall to the catch-all `.*` pattern (no MM-disable) → the multimodal crash.

---

## 7. Key differences from Leonardo (quick reference)

| Axis | TACC Vista | Leonardo |
|---|---|---|
| **Arch** | aarch64 (ARM64) | x86_64 |
| **GPU** | 1× GH200 96GB / node | 4× A100-64GB / node |
| **TP** | Always 1 (1 GPU/node) | 1–4 (4 GPUs/node) |
| **GPUs as gres** | NO (`Gres=(null)`) | YES (`--gres gpu:N`) |
| **Memory** | Whole-node alloc (no `--mem`) | `--mem` works |
| **Internet** | Direct egress (no proxy) | NO egress (proxychains + SSH tunnel) |
| **Container** | None (bare-metal conda) | SingularityPRO sandbox/`.sif` |
| **flash_attn** | NO (SDPA only) | YES (mjun0812 x86 wheel) |
| **qwen3_5 serving** | `otagent` env (fork-vLLM built-in) | `eval-qwen35` env (separate) |
| **RL** | `otagent` env (SkyRL arm branch) | MarinSkyRL uv venv in singularity sandbox |
| **Account** | `CCR24067` (107,765 SUs) | `AIFAC_5C0_290` |
| **Partition** | `gh` / `gg` (48h) | `boost_usr_prod` (24h) |
