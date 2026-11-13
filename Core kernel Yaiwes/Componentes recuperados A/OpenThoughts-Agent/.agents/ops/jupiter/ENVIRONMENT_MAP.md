# Jupiter runtime / environment map

Jupiter has **6 runtimes**, two vLLM lines (0.16-era/0.20.2rc0), and two torch lines (2.9/2.11). `vllm.__version__` is unreliable; use **`torch.__version__`** (§0) and verify with §4.

Last verified: **2026-06-13** (versions probed live).

---

## 0. TL;DR — the discriminator

> - **torch 2.9.0+cu130 → OLD stack → vLLM 0.16-era** (RL venv, `*_r3baked.sif`)
> - **torch 2.11.0+cu130 → NEW stack → vLLM 0.20.2rc0** (otagent conda, `*vllm0202rc0_r3*.sif`)
>
> DCP (`decode_context_parallel_size`/`get_dcp_group`), torch-native CP (`context_parallel`), and anything needing torch≥2.10 ONLY exist in the **NEW stack**. If a parity/feature test "fails" on a torch-2.9 runtime, you tested the wrong vLLM.

---

## 1. Decision table — which runtime for which workstream

| Workstream | Runtime | vLLM / torch |
|---|---|---|
| **Local** Harbor/SkyRL code, launching, uploads, eval/datagen orchestration, count tooling, Supabase | **`otagent` conda (local Mac AND Jupiter)** | local: no GPU / Jupiter otagent: vLLM `0.1.dev…041cfa68e`, **torch 2.11** |
| **Standard dense RL** (8B/32B FSDP2: a3, seqnorm/TIS/shaped/symclip/lrboost/loopshape) | **RL venv** `$WORKDIR/envs/rl` | vLLM `dev` (**0.16-era**), **torch 2.9** |
| **MoE / Megatron RL** (Qwen3-Coder-30B-A3B; prod 80B Qwen3-Next-80B-A3B R3+TIS) | **SIF `skyrl_megatron_vllm_r3baked.sif`** | vLLM **0.16.0**, **torch 2.9** (NGC) |
| **NEW torch2.11 / vLLM-0.20.2rc0 work** (FSDP2-CP, DCP, Mixtral multi-node, anything needing torch≥2.10) | **SIF `skyrl_megatron_vllm0202rc0_r3.sif`** | vLLM **0.20.2rc0**, **torch 2.11** |
| Datagen / eval (Harbor + Daytona, no training) | **`otagent` conda** | torch 2.11 |
| **SFT (Qwen3.5 — 9B/27B)** | **`sft-qwen35` conda** (§2f) | **transformers 5.3.0 / torch 2.9.1+cu130** |
| Axolotl SFT (Sera/CoderForge) | `sera-axolotl` conda | torch 2.9.1+cu130 |
| Curator datagen | `curator` conda | — |

> **The launcher chooses venv vs SIF for RL.** `hpc/sbatch_rl/universal_rl.sbatch` resolves `RL_ENV_DIR="${RL_ENV_DIR:-$WORKDIR/envs/rl}"` and a container var (`RL_CONTAINER` / `RL_CONTAINER_OVERLAYS`). Dense FSDP2 → venv; Megatron/MoE/80B → SIF. **To know which a job used, read its rendered sbatch** (`experiments/<job>/sbatch/*.sbatch`) for `apptainer exec … <sif>` vs the venv python — don't assume.

---

## 2. The runtimes in detail

### 2a. `otagent` conda — orchestration + local dev
- **Local Mac:** `/Users/benjaminfeuer/miniconda3/envs/otagent/bin/python` (symlinks don't work in the sandbox — use the full path).
- **Jupiter:** `/e/scratch/jureap59/feuer1/miniforge3/envs/otagent/` (torch 2.11.0+cu130; vLLM `0.1.dev…041cfa68e` build).
- **Use for:** Harbor/SkyRL code, `hpc.launch`, HF uploads, eval/datagen listeners, `count_snapshots_from_tasks.py`, Supabase, trace upload + `parse_skyrl_metrics.py` (needs `google.cloud.storage` + matplotlib — the RL venv lacks these).
- **Load (Jupiter, non-interactive):** `/e/scratch/jureap59/feuer1/miniforge3/envs/otagent/bin/python …` (`$DCFT_ACTIVATE_ENV` doesn't work over non-interactive ssh).
- **Local-dev gotcha:** Harbor's `__init__.py` fails without the package installed; to test modules in isolation locally, mock the package first: `import sys,types; m=types.ModuleType('harbor'); m.__path__=['/Users/benjaminfeuer/Documents/harbor/src/harbor']; m.__version__='0.0.0'; sys.modules['harbor']=m; sys.path.insert(0,'/Users/benjaminfeuer/Documents/harbor/src')`. System python + conda base lack loguru/pydantic — always use the otagent env.
- **`flash_attn` (FA2) INSTALLED (2026-06-14):** `2.8.3+cu130torch2.11` (prebuilt wheel `flash_attn-2.8.3+cu130torch2.11-cp312-cp312-manylinux_2_34_aarch64.whl`, from mjun0812/flash-attention-prebuild-wheels release **v0.9.22**). Installed `--no-deps` so torch/vLLM untouched; exact match to otagent's torch 2.11.0+cu130 / cp312 / aarch64 / glibc 2.34. `import flash_attn; import flash_attn_2_cuda; from flash_attn import flash_attn_func` all clean → `attn: fa2` SFT configs no longer fall back to eager.

### 2b. RL venv `$WORKDIR/envs/rl` — standard dense RL training
- **Path:** `/e/scratch/jureap59/feuer1/OpenThoughts-Agent/envs/rl` (resolved via `RL_ENV_DIR` in `hpc/sbatch_rl/universal_rl.sbatch`).
- **Versions:** vLLM `dev` (**0.16-era**), **torch 2.9.0+cu130**.
- **Use for:** the 8B/32B FSDP2 RL ablations (a3, seqnorm/TIS/shaped/symclip/lrboost/loopshape). Default RL rollout+train runtime — DCP/CP do NOT live here.
- **Load:** `$WORKDIR/envs/rl/bin/python …` (venv, NOT conda — `conda activate` is wrong; see memory `reference_jupiter_rl_venv_path`).

### 2c. `skyrl_megatron_vllm_r3baked.sif` — MoE + prod 80B RL (OLD stack)
- **Path:** `/e/scratch/jureap59/feuer1/containers/skyrl_megatron_vllm_r3baked.sif` (9.7 GB, 2026-06-08).
- **Versions:** vLLM **0.16.0**, **torch 2.9** (NGC base), transformers 5.10.1. **Overlays baked in** (`vllm_http_overlay` + `fla_tilelang_overlay`) — no `--overlay` needed (see memory `reference_80b_baked_sif_overlay_fix`).
- **Use for:** Qwen3-Coder-30B-A3B MoE RL, and the prod 80B Qwen3-Next-80B-A3B R3+TIS run (validated job 662928).
- **Load:** `apptainer exec --nv <sif> python …` (the `--nv` + baked `LD_LIBRARY_PATH`/`TRITON_LIBCUDA_PATH` are required or TransformerEngine import fails on `libcuda.so` — see `reference_skyrl_megatron_container`).
- **Predecessor SIFs `skyrl_megatron_vllm.sif` and `skyrl_megatron.sif` were DELETED 2026-06-13** — don't look for them; their active references were stale comments only.

### 2c-bis. Rebake lineage: `r3` → `r4` → `r5` (2026-08-01) ⭐ NEWEST is `r5`

Surgical sandbox rebakes off `r3`, each built alongside its predecessor; **all three still exist and
`r3`/`r4` are untouched.** Recipes: `sif_build/recipes/rebake_r4*.sh`, `rebake_r5.sh` (on Jupiter).

| SIF | size | adds |
|---|---|---|
| `…_r3.sif` | 11.59 GB | base (below) |
| `…_r4.sif` | 11.62 GB | py-spy 0.4.2, torchtitan a1fdd7e + tyro/typeguard/tomli, deep_ep 1.2.1+73b6ea4, nvshmem + `libnvshmem_host.so` symlink |
| **`…_r5.sif`** | **11.68 GB** | **flash-attn 2.6.3 → 2.8.3** (prebuilt wheel `flash_attn-2.8.3+cu130torch2.11-cp312-cp312-manylinux_2_34_aarch64.whl` from `mjun0812/flash-attention-prebuild-wheels` **v0.9.22**) |

Acceptance scripts are baked in at `/opt/r4_accept.py` and `/opt/r5_accept.py`.

**Three traps found during the r5 rebake:**

1. **`--pwd /` or every vLLM assertion is worthless.** `/e/scratch/jureap59/feuer1/vllm` is the rsynced
   vLLM *repo root* with no `__init__.py`. Apptainer keeps the host cwd and Python puts cwd first on
   `sys.path`, so a check run from the login home resolves `vllm` to an empty namespace package —
   `vllm.__file__ is None`, `vllm.__version__` raises `AttributeError`. **Always `apptainer exec --pwd /`.**
2. **`unpad_input` returns a 5-tuple on 2.8.3** (2.6.3 returned 4). Both SkyRL call sites
   (`model_wrapper.py:772`, `:1476`) already star the tail so no code change is needed, but the comment
   at `:772` still claims "the SIF ships flash_attn 2.6.3 → 4-tuple" and is now wrong.
3. **`r5` closes the door on Megatron + flash-attn.** `skyrl_train/utils/utils.py` guards
   `if flash_attn.__version__ > "2.7.4.post1": raise ValueError(...)`. That is a **string** compare, so
   `"2.8.3"` trips it. FSDP2 never calls `validate_megatron_cfg`, so production is unaffected — but any
   Megatron-backend run with `trainer.flash_attn: true` will fail on r5. Note the comparison is
   lexical and independently fragile: `"2.10.0" < "2.7.4.post1"` is *true*, so it will also wrongly
   admit a future 2.10.

**The titan PYTHONPATH shadow is still load-bearing on r5.** Verified as a delta against an r4 baseline
in the same three modes: `expert_parallel` fails under the overlay with no prefix, **identically on r4
and r5**. That is the §3a overlay shadow, not a regression. Do not retire
`sif_pydeps_titan_a1fdd7e`.

**OT-Agent follow-up:** PR #74 pins `FLASH_ATTN_WHEEL_RELEASE="v0.7.16"`, which has no torch-2.11
wheels — the URL its formula builds 404s for aarch64/torch-2.11, and `setup_rl_env.sh` then falls
through to a slow source build. Bump it to `v0.9.22`. The wheel *filename* the formula constructs is
byte-identical to what works; only the release tag is wrong.

### 2d. `skyrl_megatron_vllm0202rc0_r3.sif` — torch2.11 / vLLM 0.20.2rc0 base
- **Path:** `/e/scratch/jureap59/feuer1/containers/skyrl_megatron_vllm0202rc0_r3.sif` (11.6 GB, 2026-06-12). **Base of the r4/r5 rebake lineage; `r5` is the newest SIF.**
- **Versions (verified 2026-06-13):** vLLM **0.20.2rc0**, **torch 2.11.0+cu130**. `decode_context_parallel_size` field present; `get_dcp_group` imports. Source = `mlfoundations/vllm` `v0.20.2rc0-306-g3e3a1c45d` (local tree `/Users/benjaminfeuer/Documents/vllm`, branch `v2-migration`).
- **Use for:** FSDP2 torch-native **CP** (Stage 1+ pins torch≥2.10 here), vLLM **DCP**, Mixtral-8x7B multi-node. Any DCP/CP/torch≥2.10 test MUST use this — NOT the venv or r3baked SIF.
- **Load:** `apptainer exec --nv <sif> python …`. vLLM lives at `/opt/vllm_build/vllm/` (NOT `dist-packages/vllm`), which shadows R3 single-file binds — remove the binds when R3 is OFF. Multi-node here surfaces 3 torch-2.11 fixes the OLD SIF doesn't need (vLLM-bind-removal when R3 off, `NCCL_P2P_DISABLE=1`, `pg_options→backend_options` — see `reference_new_sif_torch211_multinode_fixes`).
- **GOTCHA — set `VLLM_USE_FLASHINFER_SAMPLER=0` for any direct `vllm.LLM`/engine call.** No `flashinfer` shipped; 0.20.2rc0 defaults the flag True and unconditionally imports `FlashInferBackend` → `ModuleNotFoundError: No module named 'flashinfer'` before its graceful fallback. The PyTorch/Triton sampler is irrelevant to greedy parity.
- **GOTCHA — multi-GPU (tp>1) spawned workers fail Triton linking** (`ld: cannot find -l:libcuda.so.1` on GH200/aarch64). Fix: `export LIBRARY_PATH=/.singularity.d/libs:${LIBRARY_PATH:-}`.
- **`VLLM_ATTENTION_BACKEND` is a dead env var on 0.20.2rc0** (logs "Unknown vLLM environment variable"); the engine auto-selects FlashAttention-3. Don't rely on it to pin a backend.

### 2e. CP-variant SIF chain — `skyrl_megatron_vllm0202rc0_r3_cp*.sif` (#232 FSDP2-CP) ⭐
Built off §2d (torch 2.11 / vLLM 0.20.2rc0) for the #232 FSDP2 context-parallel (ring-SDPA) + R3 work. Path prefix `/e/scratch/jureap59/feuer1/containers/`. Load like §2d (same flashinfer/libcuda/attention-backend gotchas apply).
- **`skyrl_megatron_vllm0202rc0_r3_cp_fixb3.sif`** (11.6 GB, 2026-06-19) — ⭐ **CANONICAL CP+R3 SIF.** `.vllm_commit = 4d167a4af` (`penfever/working` with merged **#237** rank-symmetric R3-capture fix baked in). **Use for ALL new CP and/or R3 runs** (#232 cp2 / cp2_r3 rungs point here).
- Non-CP R3 variants (`_r3_fixb.sif` / `_r3_v2migration.sif`) are NOT rebuilt with the #237 fix as of 2026-06-19 — separate rebake needed if a non-CP R3 run must carry it.
- **KNOWN CP BUG (SkyRL-side, 2026-06-19 — NOT the SIF):** Qwen3-**MoE** crashes in CP≥2 policy forward (`model_wrapper.py:668` passes a dict attention_mask MoE's `create_causal_mask` can't consume → `AttributeError: 'dict' has no attribute 'ndim'`). Dense-Qwen3 & CP1 unaffected. Fix is in the SkyRL host clone (`OpenThoughts-Agent/SkyRL/skyrl-train/skyrl_train/model_wrapper.py`) — editable install, no SIF rebuild. See `agent_logs/2026-06-19_cp2_forward_dict_ndim_bug.md`.

### 2f. `sft-qwen35` conda — Qwen3.5 SFT (and other SFT/datagen condas)
- **Path (Jupiter):** `/e/scratch/jureap59/feuer1/miniforge3/envs/sft-qwen35/`
- **Versions (Jupiter-verified 2026-06-13):** **torch 2.9.1+cu130, transformers 5.3.0** (deepspeed `zero3_bf16` for sharding).
- **Use for:** Qwen3.5 (9B/27B), which needs **transformers ≥ 5.3**; use for `sft/lf_configs/qwen3_5/*`.
- **Load:** `/e/scratch/jureap59/feuer1/miniforge3/envs/sft-qwen35/bin/python …` (full path over non-interactive ssh). `hpc.launch --train_config_path sft/lf_configs/qwen3_5/...` wires conda activation on Jupiter; on **Leonardo** hand-patch the sbatch (conda activate + WORKDIR) per CLAUDE.md "SFT Launch on Leonardo".
- **Launch + cleanup specifics:**
  - Harbor role/content tags: `--role_tag role --user_tag user --assistant_tag assistant --content_tag content` (or the thinking preprocessor finds 0 assistant messages → garbage).
  - Qwen3.5 writes **full safetensors at the checkpoint root on completion → SKIP the `consolidate` step** (memory `feedback_qwen35_9b_no_consolidate`); follow the **8B SFT cleanup checklist**.
  - Before HF upload, copy `preprocessor_config.json` from the base model into the checkpoint (LLaMA-Factory doesn't emit it; vLLM needs it).
  - HF-only / DB-register per the SFT checklist; uploads default PUBLIC to `laion/`.

**Other condas on Jupiter:**
- `sera-axolotl` — Sera/CoderForge axolotl SFT (torch 2.9.1+cu130; see CLAUDE.md "Axolotl SFT on Jupiter" for install recipe + mandatory env patches).
- `curator` — Curator sharded datagen (`run_curator_datagen_sharded.sbatch`, `--account=reformo`).

---

## 3. Overlay images (`containers/*.img`)

Overlays stack onto a SIF at `apptainer exec --overlay <img>` (or are baked in). On GPFS they can FUSE-mount-timeout on the Ray head — the prod 80B SIF bakes them in to avoid that.

| Overlay | Size | Provides | Status |
|---|---|---|---|
| `vllm_http_overlay.img` | 0.5 G | vLLM HTTP `routed_experts` serialization (R3 routing capture) | baked into both `*r3*.sif` |
| `fla_tilelang_overlay.img` | 4 G | tilelang 0.1.8 + FlashQLA fused GatedDeltaNet kernels (FSDP2-EP Stage 8) | baked into `*r3*.sif` |
| `skyrl_titan_overlay.img` | 4 G (2026-06-13) | torchtitan (CP **+EP** / MoE expert-parallel — CP Stage-6 TEST3) | overlay (stack when CP+EP) |

### 3a. `PYTHONPATH` pydeps prefixes — the no-rebuild injection mechanism ⭐

The RL config's `container.pydeps` is colon-separated and **prepended first** (`rl_launch_utils.py:202`),
so the first entry **shadows the SIF**. For a pure-python package this is the bake-equivalent: no image
rebuild, and — unlike an overlay — no GPFS-FUSE Ray-bootstrap timeout risk.

| Prefix | Contains | Why |
|---|---|---|
| `sif_pydeps` | daytona / hydra / harbor / tyro / etc. | shared base, used by every RL config |
| `sif_pydeps_longctx_titan022` | **torchtitan 0.2.2** only (+ dist-info) | shadows the SIF *up* for the longctx/CP configs |
| `sif_pydeps_titan_a1fdd7e` | **torchtitan 0.1.0 @ a1fdd7e** only (+ dist-info) | shadows the SIF *down*; see the version trap below |

**THE OVERLAY ALSO CARRIES TORCHTITAN — AND IT WINS OVER THE IMAGE (2026-08-01).** Baking the right
torchtitan into the SIF is **not sufficient** and does not let you retire the PYTHONPATH prefix.
`skyrl_titan_overlay.img` ships its own torchtitan at the *identical* path
(`/usr/local/lib/python3.12/dist-packages/torchtitan`) **without `expert_parallel`**, and an overlay
shadows the image. Proven by retiring the prefix on the r4 SIF: every MoE arm immediately reinstated
the B11 `ImportError` below, on an image that imports the symbol fine when run bare.

**Test with the overlay stacked or the test is worthless:**
```bash
apptainer exec --overlay $C/skyrl_titan_overlay.img:ro $C/<sif> env PYTHONPATH=$S/sif_pydeps \
  python -c "from torchtitan.distributed.expert_parallel import expert_parallel; print('OK')"
```
**And do not trust `importlib.metadata.version("torchtitan")`** — under the overlay it still reports the
*baked* version (0.1.0) while the imported module comes from the overlay. Version metadata and module
code disagree here. Only importing the symbol, under the real overlay stack, proves anything.

**TORCHTITAN VERSION TRAP (2026-07-31).** The SIF ships **torchtitan 0.2.2**. MarinSkyRL `main` pins
**a1fdd7e (0.1.0)** and does `from torchtitan.distributed.expert_parallel import expert_parallel` —
a symbol 0.2.2 **removed**. Without the shadow, every MoE arm dies ~10 min in, *after* weights load, at
`model_wrapper.py:639 → moe_swap → moe.py:57` with `ImportError: cannot import name 'expert_parallel'`.
The repo history crossed the pin twice (`cdacec77` aligned to 0.2.2, `4ba60a1f` reverted to a1fdd7e), so
**check which torchtitan the checked-out SkyRL wants before launching**, not which branch it is on.
Clearing `moe_grouped_gemm` is NOT a workaround — `fsdp_strategy.py:418` then rejects
`expert_model_parallel_size > 1`.
The image's build assert (`import ExpertParallel`) does **not** catch this: that class exists in both.

### 3b. DeepEP (`ep_comm_backend: "deepep"`) — NOT present; buildable, not yet built

`skyrl_train/distributed/deepep.py` needs `from deep_ep import Buffer` + `deep_ep.utils.{EventHandle,
EventOverlap}`. Its docstring claims a verified `deep_ep 1.2.1+73b6ea4` JSC aarch64/cu13 build —
**that build is not on this filesystem.** Verified absent 2026-07-31 from the SIF, all three overlays,
and every `sif_pydeps*` prefix.

What the container **does** have (so the gap is smaller than it looks):

| | status |
|---|---|
| nvcc | **present**, CUDA **13.0**, `--list-gpu-arch` includes `compute_90` (GH200) |
| torch | 2.11.0+**cu130** — matches the "cu13" build the docstring references |
| NVSHMEM **runtime** | **present** — `libnvshmem_host.so.3` + ibrc/libfabric/ucx transports under `/usr/local/cuda/targets/sbsa-linux/lib` |
| NVSHMEM **SDK** (headers, `libnvshmem_device.a`) | **ABSENT** — this is what blocks a build |
| `deep_ep` on PyPI | **no** — source-only, `github.com/deepseek-ai/DeepEP` |

The SDK is obtainable: **`nvidia-nvshmem-cu13` 3.7.2** has an aarch64 manylinux wheel carrying the
headers, `libnvshmem_device.a`, **and `libnvshmem_device_sm_90.bc`** (GH200's exact arch), with a
`libnvshmem_host.so.3` soname matching the container's runtime. DeepEP's `setup.py` explicitly supports
this route (`find_nvshmem_root()`, and a comment that the NVIDIA wheels ship only the versioned soname
so it links `-l:libnvshmem_host.so`).

**QUEUED for the next SIF rebuild** alongside `py-spy` — spec, pins and acceptance checks in
`sif_build/recipes/README_vllm0202rc0_r3_sif.md` §QUEUED. Gated on the in-flight MarinSkyRL fixes so
both land in one rebuild.

**Build attempted 2026-07-31. Failed at DeepEP HEAD (`dd758ca`) — and NOT on NVSHMEM.** The nvcc
diagnostics are a **torch C++ API mismatch**, i.e. DeepEP HEAD is written against a different torch than
this SIF's 2.11.0+cu130:

```
error: no matching function for call to 'empty(<brace-enclosed initializer list>, c10::TensorOptions)'
error: variable or field 'launch_engram_fetch_wait' declared void
error: expected primary-expression before '>' token
```

**So pin DeepEP, do not build HEAD.** `skyrl_train/distributed/deepep.py` names `1.2.1+73b6ea4`, and
`73b6ea4` ("support hidden-dim 3072", #458) *is* reachable on origin — it is simply not what a
`--depth 1` clone gives you (fetch with `--depth 200`).

**At `73b6ea4` the torch API errors are gone and the build reaches a new, further blocker:**
`fatal error: cuda/std/array: No such file or directory` — the **CCCL / libcu++ headers**, absent from
`/usr/local/cuda/include`. `nvidia-cuda-cccl-cu13` on PyPI is a **0.0.1 stub sdist**, not the real
headers, so the source for these is still unsettled. That is the single remaining blocker; NVSHMEM,
nvcc, arch and torch are all satisfied.

Work-in-progress at `/e/scratch/jureap59/feuer1/deepep_smoke/`: `DeepEP/` (checked out to `73b6ea4`),
`build.sh`, `build_full.log` (HEAD failure), `build_73b6ea4.log` (pinned attempt).
**Do not record DeepEP as unavailable-in-principle** — every prerequisite is present or one pip install
away, and the one observed failure is a version pin, not a missing dependency.

> **Two instrumentation traps this exposed, both self-inflicted — don't repeat them.**
> Piping the build through `| tail -40` discarded the nvcc diagnostics and kept only the Python
> traceback, which says nothing. And `grep -c "IMPORT OK"` on a `set -x` script returns **1** by
> matching the *echoed command line*, not the output — a false pass. Log builds in full, and never
> grep for a success string that also appears in the command that produces it.

### 3c. py-spy works from the HOST against in-container ranks ⭐

`py-spy` is **not** in the SIF and does not need to be. Apptainer shares the host PID namespace, so a
host-side install attaches straight through:

```bash
/e/scratch/jureap59/feuer1/miniforge3/envs/otagent/bin/py-spy dump --pid <pid>   # 0.4.1, already installed
srun --jobid=<J> --overlap -w <node> -N1 -n1 bash -c 'for P in $(pgrep -f "ray::FSDPPolicyWorkerBase"); do py-spy dump --pid $P; done'
```

`srun --overlap` without `-w` lands on an arbitrary node of the allocation and `--ntasks-per-node=1`
often launches on only one — **always pass `-w <node>`** and iterate, or you will sample one rank and
conclude the others are fine.

This is the only way to diagnose a hang here: **`nvidia-smi` utilization is worthless as a liveness
signal.** A NCCL collective busy-waits, so a fully deadlocked job reads **100 % on every GPU** while
every Python thread is idle. Confirmed 2026-07-31 on a wedged MoE run — 11 of 12 policy ranks parked in
`_token_dispatch (torchtitan/distributed/expert_parallel.py:192)` (the EP all-to-all) with one rank
diverged into `all_gather_into_tensor`, i.e. a rank-order divergence that can never complete. Four hours,
no error, SLURM still `RUNNING`, `--max_restarts` useless because nothing failed. See
`agent_logs/2026-07-31_escalation-tasktrove-shaped-arm-async-deadlock.md`.

**R3 routing-capture works on stock-0.16 (no SIF rebuild):** `vllm_http_overlay` serializes `routed_experts` over `/chat/completions`; the only blocker was `enable_return_routed_experts=False` (now true). For **Qwen3-Next**, the vLLM **Ray Compiled-DAG** backend deadlocks on the hybrid arch when capture is on → run with **mp executor backend** (`generator.inference_engine_mp_backend: true`, ran clean 12/12 rounds TP=4), plus the hybrid-kv-buffer fix + defensive clip (`gmr_fix`/`scheduler_fix`/`capturer_fix` single-file binds; SkyRL flag on branch `r3-mp-backend-qwen3next-20260608`). The FSDP2 router-replay hook EXISTS and ran a full GRPO backprop step on the 80B (do NOT repeat the "Megatron-only / no FSDP2 replay" claim).

---

## 4. VERIFY before you trust — copy-paste probes

**SIF:**
```bash
C=/e/scratch/jureap59/feuer1/containers
apptainer exec --nv $C/<sif>.sif python -c "import vllm,torch; print('vllm',vllm.__version__,'torch',torch.__version__); \
from vllm.engine.arg_utils import EngineArgs; print('DCP field', 'decode_context_parallel_size' in EngineArgs.__dataclass_fields__)"
```
**venv / conda:**
```bash
/e/scratch/jureap59/feuer1/OpenThoughts-Agent/envs/rl/bin/python -c "import vllm,torch; print(vllm.__version__, torch.__version__)"   # → dev 2.9.0  (OLD)
/e/scratch/jureap59/feuer1/miniforge3/envs/otagent/bin/python   -c "import torch; print(torch.__version__)"                          # → 2.11.0     (NEW)
```
**torchtitan — run this BEFORE any MoE launch (§3a trap):**
```bash
C=/e/scratch/jureap59/feuer1/containers; S=/e/scratch/jureap59/feuer1
# what the SIF ships vs what the checked-out SkyRL needs:
apptainer exec $C/skyrl_megatron_vllm0202rc0_r3.sif python -c "import torchtitan;print(torchtitan.__file__)"
grep -n "from torchtitan" $S/OpenThoughts-Agent/SkyRL/skyrl-train/skyrl_train/models/layers/moe.py
# resolve WITH the pydeps prefix the config will actually use:
apptainer exec --env PYTHONPATH=$S/sif_pydeps_titan_a1fdd7e:$S/sif_pydeps:$S/OpenThoughts-Agent/SkyRL/skyrl-train \
  $C/skyrl_megatron_vllm0202rc0_r3.sif python -c \
  "from torchtitan.distributed.expert_parallel import expert_parallel; \
   from skyrl_train.models.layers.moe_swap import swap_moe_blocks_to_grouped; print('MoE import chain OK')"
```
**DeepEP presence (§3b) — absence is cheap to confirm, don't assume either way:**
```bash
apptainer exec $C/skyrl_megatron_vllm0202rc0_r3.sif python -c "import importlib.util as u;print(u.find_spec('deep_ep'))"   # → None as of 2026-07-31
```
torch 2.9 ⇒ 0.16-era (no DCP/CP); torch 2.11 ⇒ 0.20.2rc0 (has DCP/CP). If a feature requiring torch≥2.10 "isn't there" or "fails parity," confirm you're on a torch-2.11 runtime before concluding it's a real defect — and pin the parity/feature smoke to the SIF that carries the feature (§2d/§2e).
