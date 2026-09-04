# ZIH Capella runtime / environment map

**Purpose:** which conda env to use for which workstream on **TU-Dresden ZIH Capella**, and the version
facts that bite. Capella is the closest twin to **TACC Vista** on the axes that matter for eval/datagen:
**bare-metal conda (NO Singularity/Apptainer), full direct compute-node internet egress, SLURM.** The big
divergences from Vista are all in our favor: **x86_64** (not aarch64 — so PREBUILT wheels work: vanilla
vLLM, flash-attn, torch cu128, no from-source vLLM build needed for standard models), **4× H100-94GB per
node** (not 1× GH200 96GB), and **GPUs ARE a SLURM gres** — but the submit filter requires the UNTYPED
`--gres=gpu:N` (the typed `gpu:h100:N` is rejected; see ops.md §Scheduler ⚠), unlike Vista's whole-node
trick. Access/preamble/paths/filesystem-rules live in `ops.md`; this is the runtime map.

Last verified: **2026-07-14** (fresh workspace rebuild — the prior `cat/otagent` workspace expired + was
purged; conda env + repos rebuilt from scratch). Re-confirm with §3 if acting on this months later.

---

## 0. TL;DR — the discriminators

> - **otagent conda** = the default runtime for EVERYTHING — orchestration, eval, datagen, agentic eval,
>   serving standard Qwen3/Llama models. Built with **PREBUILT x86_64 wheels** (torch cu128 + vanilla
>   `vllm[flashinfer]` 0.11.2–0.16.0 + transformers 4.57.3) via `uv pip install -e ".[datagen]"` — **NO
>   from-source vLLM build** (Capella is x86_64/H100, so the wheels Just Work; contrast TACC aarch64 which
>   must build vLLM from source).
> - Compute nodes have **full direct internet egress** (verified: `huggingface.co` 200, `app.daytona.io`
>   200 from a `capella` compute node) — NO proxychains / SSH-SOCKS5 / step-ca cert, NO `HF_HUB_OFFLINE`,
>   NO pre-download. Same simplification as TACC, opposite of Leonardo.
> - **GPUs ARE a SLURM gres** — use the UNTYPED `--gres=gpu:N` (whole node = `--gres=gpu:4`); the typed
>   `--gres=gpu:h100:N` is REJECTED by Capella's cli_filter at submit (verified 2026-07-14; see ops.md §Scheduler ⚠).
> - **NO containers.** Capella has no Singularity/Apptainer — everything is bare-metal conda.
> - **fork-vLLM for qwen3_5/3.6 serving is NOT YET built here.** If/when Capella needs to serve
>   `qwen3_5`/`qwen3_5_moe` (tmax, Qwen3.5/3.6) for agentic eval, follow the Leonardo `eval-qwen35` §2f
>   recipe (x86_64, so Leonardo's from-source path transfers almost verbatim — same fork commit, cu128).
>   Not needed for standard-model evals.

---

## 1. Decision table — which runtime for which workstream

| Workstream | Runtime | Stack |
|---|---|---|
| Orchestration, `hpc.launch`, eval listener, datagen, HF uploads, Supabase | **`otagent` conda** | torch 2.9–2.10+cu128, vanilla vLLM 0.11–0.16, transformers 4.57.3 |
| Agentic eval / datagen (Harbor + Daytona, direct egress) | **`otagent` conda** | same |
| Serving standard Qwen3 / Llama models | **`otagent` conda** | same (vanilla vLLM) |
| **Serving qwen3_5 / qwen3_5_moe** (tmax, Qwen3.5/3.6) | **(not built yet)** | build a separate `eval-qwen35` per Leonardo ENVIRONMENT_MAP §2f (x86_64 recipe transfers) |
| SFT (Qwen3 / Llama) | **`otagent` conda** (+ LLaMA-Factory editable) | + `.[sft]` extras (deepspeed / liger / flash-attn cu128 wheel) |
| RL (MarinSkyRL / SkyRL GRPO) | **`otagent` conda** (or a dedicated RL venv) | MarinSkyRL editable; see `ops.md` §RL |

---

## 2. The runtimes in detail

### 2a. `otagent` conda — orchestration + eval + datagen + agentic + standard serving (the default)
- **Path:** `/data/cat/ws/befe330h-otagent/miniconda3/envs/otagent/` (activate via the `ops.md` preamble).
- **Build (fresh, 2026-07-14):** miniconda in the workspace (`$DCFT_CONDA=$SCRATCH/miniconda3`, pkgs +
  envs dirs pinned into the workspace via `.condarc`, channel = `conda-forge`), then:
  ```bash
  conda create -y -p $SCRATCH/miniconda3/envs/otagent python=3.12 && conda activate otagent
  pip install uv
  cd $SCRATCH/harbor && uv pip install -e .            # editable, main (migrate a stale clone: git checkout main && git pull)
  cd $SCRATCH/OpenThoughts-Agent && uv pip install -e ".[datagen]"
  ```
  `.[datagen]` pulls **prebuilt** `vllm[flashinfer]>=0.11.2,<=0.16.0` + `torch>=2.9.0,<=2.10.0` (cu128) +
  `transformers==4.57.3` + `ray` — all x86_64 wheels, no compile. Add `.[sft]` / `.[cloud]` only if that
  workstream is needed (the zih.md legacy notes did `.[datagen,cloud,sft]` + a torch cu128 force-reinstall
  + a flash-attn cu128 wheel for RL/SFT — do that ONLY when SFT/RL is the target, not for an eval smoke).
- **Stack (verified live 2026-07-14):** **torch 2.9.1+cu128, vLLM 0.16.0 (vanilla, flashinfer),
  transformers 4.57.3, harbor (editable, `main`)** + nvidia-cu12 12.8 libs, xgrammar 0.1.29,
  ray. This is byte-for-byte the SAME core stack as Leonardo's `otagent` (torch 2.9.1+cu128 / vLLM 0.16.0)
  — the x86_64 prebuilt wheels transfer directly.
- **Use for:** everything — `hpc.launch`, the unified eval listener, datagen, uploads, agentic eval
  (Harbor + Daytona over direct egress), and serving standard (non-qwen3_5) models.

### 2b. Serving qwen3_5 / qwen3_5_moe — NOT BUILT (follow Leonardo §2f if needed)
Vanilla vLLM 0.11–0.16 in `otagent` does **not** resolve `qwen3_5` / `qwen3_5_moe` archs. To serve
tmax / Qwen3.5 / Qwen3.6 for agentic eval, build a dedicated `eval-qwen35` env exactly as Leonardo does
(`.agents/ops/leonardo/ENVIRONMENT_MAP.md` §2f): torch 2.11.0+cu128 + transformers 5.12.1 + the
`mlfoundations/vllm` fork @ `76259c63a` built from source. Capella is **x86_64 like Leonardo**, so that
recipe transfers directly (use the CUDA/12.8.0 module or conda cuda-toolkit=12.8, `TORCH_CUDA_ARCH_LIST=9.0`
for Hopper H100). Not required for the current standard-model eval work.

### 2c. RL — MarinSkyRL editable
MarinSkyRL (`penfever/working`) is cloned at `$SCRATCH/MarinSkyRL`. The zih.md legacy notes reference an
`envs/rl/bin/activate` venv path AND `conda activate otagent` — reconcile to the **current standard**: RL
runs in the `otagent` conda env with MarinSkyRL editable-installed (mirrors TACC, which runs SkyRL in
`otagent`). If a run needs the pinned SkyRL torch/vLLM/flash-attn graph that conda can't satisfy, build a
uv venv per the Leonardo `marin_venv` pattern (`.agents/ops/leonardo/ENVIRONMENT_MAP.md` §2c). RL was NOT
exercised in the 2026-07-14 rebuild — verify before relying on it.

---

## 3. VERIFY before you trust

```bash
WS=/data/cat/ws/befe330h-otagent
# otagent (the default — torch/vllm/transformers)
$WS/miniconda3/envs/otagent/bin/python -c "import torch,vllm,transformers; print('otagent', torch.__version__, vllm.__version__, transformers.__version__)"
# harbor editable + branch
$WS/miniconda3/envs/otagent/bin/python -c "import harbor; print('harbor', harbor.__version__)"
cd $WS/harbor && git rev-parse --abbrev-ref HEAD   # -> main (migrate a stale clone: git checkout main && git pull)
# GPU visible (from an srun/sbatch on capella, NOT the login node)
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader   # -> NVIDIA H100, 95830 MiB (x4)
```

---

## 4. Hardware / filesystems (the constraints that shape the above)

- **Capella nodes (partition `capella`, 154 nodes):** 2× AMD EPYC 9334 (32-core, **multithreading OFF** →
  64 cores, but Slurm caps requestable at **56**), **4× NVIDIA H100-SXM5 94GB** (observed 95830 MiB) unified
  in one node, **768 GB RAM** (752 GB usable; **12 "heavy" nodes have 1.5 TB**), 800 GB local NVMe at
  `/tmp`, Rocky Linux 9.6. GPUs ARE a SLURM gres (`gpu:h100:4(S:0-1)`). `capella-interactive` = 2 nodes
  (c1/c2), 12h cap.
- **GPU memory:** H100-94GB HBM2e; supports MIG fractions (not used by us).
- **Filesystems:** **/home** `/home/befe330h` (**50 GB/user**, NFS4, permanent — SOURCE CODE / CONFIG
  ONLY, never large data/envs/caches); **/projects** `/projects/p_agents_finetuning` (13 TB shared, NFS,
  permanent); **Lustre workspaces** on `cat` (faster), `horse` (slow — "slow as F"), `walrus` — 30-day ttl,
  2 extensions. Project quota on `horse` ≈ 7.68 TB / 30,733 files. Our workspace:
  `/data/cat/ws/befe330h-otagent` (holds miniconda3, repos, HF cache, checkpoints, eval jobs).
- **⚠ LUSTRE METADATA BAN** (degrades a SHARED FS + flagged by admins): **NEVER run `find`, `du`, `df`,
  `locate`, `ls -l`, `ls --color`, `ls -R` on `/data/*`.** Use plain `ls <path>` / `ls <file>`, or `lfs`
  (`lfs df`, `lfs find <root> [--maxdepth N --name ...]`, `lfs quota`). The ZIH analog of Leonardo's GPFS
  no-find/du ban.
- **⚠ /home = 50 GB HARD.** Alias EVERY space-eater into the workspace: conda pkgs+envs (`.condarc`
  `pkgs_dirs`/`envs_dirs`), `HF_HOME`/`HF_HUB_CACHE`, `PIP_CACHE_DIR`, `XDG_CACHE_HOME`, `TMPDIR` — the
  `zih_capella.env` dotenv does this. If /home fills, conda/pip/HF all break.
- **Login nodes:** `login[1-2].capella.hpc.tu-dresden.de`, **600 s CPU-time limit** per process — no
  productive runs / long builds on login; use `srun`/`sbatch` on `capella`. (Env builds via `uv` ran fine
  detached on login in the 2026-07-14 rebuild — they're I/O-bound, not CPU-heavy — but a from-source vLLM
  compile MUST go to a compute node.)
- **Internet:** compute nodes have **FULL direct egress** (verified: `huggingface.co` 200,
  `app.daytona.io` 200 from a `capella` GPU node) — NO proxy / SOCKS / cert, NO `HF_HUB_OFFLINE`.
- **Account/scheduler:** group/acctcode `p_agents_finetuning`; partition `capella` (infinite timelimit in
  `sinfo`, but ZIH docs enforce a **7-day** job max); `capella-interactive` (12h). No SU/budget balance
  tool documented here (use `show_resources`).

---

## 5. Canonical env set — anything else is cruft

**conda (`$SCRATCH/miniconda3/envs/`):** `otagent` (default — orch/eval/datagen/agentic/SFT/RL + standard
serving). No `eval-qwen35` / `evalchemy` / `vllm_sandboxes` yet — add only when that workstream lands
(mirror Leonardo/TACC). **No containers** (bare-metal conda).

**code clones (`$SCRATCH/`):** `OpenThoughts-Agent` (`penfever/working`, editable `.[datagen]`),
`harbor` (`main`, editable; migrate a stale clone on next touch), `MarinSkyRL` (`penfever/working`). (The `~/OpenThoughts-Agent`
and `~/harbor` clones in /home are STALE leftovers — the canonical clones live in the workspace.)

---

## 6. Key differences from TACC Vista & Leonardo (quick reference)

| Axis | ZIH Capella | TACC Vista | Leonardo |
|---|---|---|---|
| **Arch** | x86_64 | aarch64 (ARM64) | x86_64 |
| **GPU** | 4× H100-94GB / node | 1× GH200 96GB / node | 4× A100-64GB / node |
| **GPUs as gres** | YES (`--gres gpu:h100:N`) | NO (whole-node trick) | YES (`--gres gpu:N`) |
| **Container** | None (bare-metal conda) | None (bare-metal conda) | SingularityPRO |
| **Internet (compute)** | Direct egress (no proxy) | Direct egress (no proxy) | NO (proxychains + tunnel) |
| **vLLM (standard models)** | vanilla PREBUILT wheel | from-source (aarch64) | from-source |
| **qwen3_5 serving** | not built (use §2f recipe) | `otagent` fork-vLLM | `eval-qwen35` (separate) |
| **flash_attn** | prebuilt cu128 x86 wheel available | NO (SDPA) | prebuilt cu128 x86 wheel |
| **Scheduler** | SLURM `capella` (7-day) | SLURM `gh`/`gg` (48h) | SLURM `boost_usr_prod` (24h) |
| **FS metadata ban** | Lustre (no find/du on `/data/*`) | — | GPFS (no find/du) |
| **/home** | 50 GB (code only) | 23.3 GB (dotfiles) | 50 GB (too small for envs) |
