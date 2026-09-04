# TACC Vista Access

**SSH**: `ssh TACCVista` (alias in `~/.ssh/config`). Direct: `ssh penfever@login2.vista.tacc.utexas.edu`.
User `penfever`, account `CCR24067`. Login requires password (in 1Password) + TOTP (authenticator app).

**Cluster**: TACC Vista — **Grace Hopper GH200 96GB**, **aarch64** (ARM64), SLURM.
Vista user docs: <https://docs.tacc.utexas.edu/hpc/vista/>.
Common pitfalls: [TACC Vista Google Doc](https://docs.google.com/document/d/1URcWe8mLQF8HMNre7vZwgk6TiRNxFxVBwK_HCcRXQdM/edit).

**Pre-launch preamble** (run before launching any job):
```bash
source $SCRATCH/OpenThoughts-Agent/hpc/dotenv/tacc.env && \
source $SCRATCH/keys.env && \
cd $SCRATCH/OpenThoughts-Agent && git pull && \
git submodule update --init --remote sft/llamafactory && \
cd $SCRATCH/harbor && git pull && \
cd $SCRATCH/OpenThoughts-Agent && \
source $SCRATCH/miniconda3/bin/activate otagent
```

**Key paths**:
- Code (`$DCFT`): `$SCRATCH/OpenThoughts-Agent` = `/scratch/10635/penfever/OpenThoughts-Agent`
- Harbor: `$SCRATCH/harbor` = `/scratch/10635/penfever/harbor`
- Conda: `$SCRATCH/miniconda3` = `/scratch/10635/penfever/miniconda3`
- Secrets (`$DC_AGENT_SECRET_ENV`): `$SCRATCH/keys.env` = `/scratch/10635/penfever/keys.env`
- HF cache (`$HF_HUB_CACHE`): `$SCRATCH/hub` = `/scratch/10635/penfever/hub`
- Checkpoints (`$CHECKPOINTS_DIR`): `$SCRATCH/checkpoints`
- Tokenized datasets: `$SCRATCH/tokenized_datasets`
- Evalchemy (standard / pass@k evals): `$SCRATCH/evalchemy` — conda env `evalchemy`
- DCFT shared (read-only): `/scratch/08002/gsmyrnis/dcft_shared/`
- Negin/Richard eval traces: `/scratch/08134/negin/dc-agent-shared/dc-agent/eval/tacc/jobs/`

> **⚠ Allocation**: `CCR24067` — **107,765 SUs** available, **expires 2025-12-31**. Monitor periodically
> (SUs are consumed per GPU-hour). Check balance: `bbalance`.
>
> **⚠ Use `gg` for builds/installs.** `uv` and other Rust tools OOM on the shared login node; use `srun -p gg`.

**Disk quotas** (as of 2026-06):
| Disk | Usage | Limit | Notes |
|---|---|---|---|
| `/scratch` | ~3,780 GB | unlimited (no quota) | 1,248,064 inodes — primary code/data/envs |
| `/home1` | 1.9 GB | 23.3 GB | login dotfiles only — do NOT write large data here |
| `/work` | 0 GB | 1,024 GB | project work — currently unused |

## Partitions & QOS

| Partition | QOS | MaxWall | MaxJobs (running) | MaxSubmit (total) | Use |
|---|---|---|---|---|---|
| `gh` | `qgh` | 48:00:00 | 20 | 40 | Grace Hopper production |
| `gg` | `qgg` | 48:00:00 | 20 | 40 | Grace Grace production |
| `gh-dev` | `qdevelopment` | **02:00:00** | **1** | **3** | Interactive dev (2h cap!) |
| — | `qnormal` | 48:00:00 | 20 | 40 | General |

> **Use `gg` or `gh` for production.** `gh-dev` is development-only with a **2-hour wall cap** and
> **1 running job** — requesting `>120 min` on `gh-dev` triggers `QOSMaxWallDurationPerJobLimit`
> even though the partition shows `MaxTime=UNLIMITED`.

> **⚠ PER-USER RUNNING-JOB CAP = 20 (production QOS `qgh`/`qgg`/`qnormal`).** Hitting it holds further jobs
> PENDING with reason **`QOSMaxJobsPerUserLimit`** — it is a job-COUNT cap, **not** a node cap, so it fires
> **even when compute nodes are free.** Consequence: a queue of 20+ one-node jobs (e.g. the flawed_summ eval
> fill) will **STARVE a big multi-node job** (e.g. a 16-node SFT) indefinitely, because the big job can't get
> a running-slot no matter how many nodes are idle. **BUDGET penfever's concurrent jobs accordingly** — leave
> headroom for other work. Standing rule (see the flawed_summ tracker): **cap the flawed_summ eval fill at ≤16
> concurrent on TACC**, filling the rest of the campaign target on Leonardo/Iris-TPU. (Observed 2026-07-08:
> 20 running penfever eval legs blocked a 16-node axolotl SFT with `QOSMaxJobsPerUserLimit`; freed it by
> cancelling eval legs below the cap.)

**Interactive session** (for debugging / manual runs):
```bash
idev -A CCR24067 -p gg -m 1400     # 23h20m on gg
idev -A CCR24067 -p gh-dev -m 120  # 2h on gh-dev (max allowed)
# or srun:
srun -p gh -N 1 -n 1 -t 12:00:00 --pty bash -l
```

**SLURM submit**: standard `sbatch`. Watch your jobs: `watch squeue -u penfever`.

## Environment setup

> **⚠ uv crashes on the login node** with a Rust memory allocation failure
> (`memory allocation of 1520 bytes failed`). All `uv pip install` / build-heavy
> operations MUST run on a **compute node** via `srun` (see Partitions & QOS).
> The login node is fine for `git pull`, `squeue`, and lightweight commands.
>
> **⚠ Eval-scale HF trace uploads ALSO OOM on the login node** (`realloc failed` /
> shared-memory OOM) — a manual eval-agentic-cleanup trace push (large parquet) can
> land the score but silently fail to upload the traces. Run the HF trace upload on a
> **compute node** (a quick `-p gh-dev` sbatch/srun) too, not the login node (observed
> 2026-07-02 on two swe `__X__` legs; re-ran the upload as job 801969 → uploaded + relinked).

### otagent env (primary — datagen / eval / RL / SFT)

**Current state** (verified live, as of 2026-06-26):
- Python 3.12.13
- torch 2.11.0+cu128, torchvision 0.26.0+cu128, torchaudio 2.11.0+cu128
- vllm **`0.1.dev16611+g76259c63a`** (pip metadata: `0.1.dev16611+g76259c63a.cu128`;
  `vllm.__version__` reports the bare form) — the fork-vLLM built from source (§"Building the
  vLLM wheel from source"); it **resolves `qwen3_5`** (the bare `0.16.0` pip wheel the env was
  created with was replaced — verified live in the 2026-06-25 tmax-9b serve log). A stale
  "vllm 0.16.0" here previously caused a mis-diagnosis that tmax couldn't serve on TACC.
- **transformers 5.12.1** + **huggingface-hub 1.21.0** (bumped 2026-06-26 from 4.57.3 / 0.36.2).
  This gives transformers NATIVE `qwen3_5` support and aligns the env with Leonardo's
  `eval-qwen35` (which runs the SAME fork-vLLM + transformers 5.12.1) — so tmax/qwen3_5 serving
  is now exact Leonardo parity. ⚠ It's a 4.x→5.x jump in the PRIMARY otagent env: eval/serving
  is proven fine (the fork-vLLM runs on 5.12.1 on Leonardo), but the OTHER otagent workflows
  (datagen / SFT-llamafactory / harbor) on this env should be re-smoke-tested before relying on
  them, and the bump likely cascaded other deps (re-verify the rest of this block live).
- harbor 0.8.0 (editable, `main` branch; migrate a stale clone: `git checkout main && git pull` on next touch)
- flashinfer-python 0.6.3
- **SFT extras**: deepspeed 0.18.0, liger-kernel 0.8.0, peft 0.19.1, trl 1.6.0,
  llamafactory 0.9.4.dev0 (editable), gradio 6.17.3, torchao 0.17.0
- **No flash_attn** — using SDPA attention instead (no prebuilt aarch64 wheel exists
  for torch 2.11+cu128; see flash_attn note below)

**Fresh setup** (run each `uv` step on a compute node — see `srun` recipe below):
```bash
# 1. Create env + harbor (on compute node)
conda create -y -n otagent python=3.12 && conda activate otagent
cd $SCRATCH/harbor && pip install uv && uv pip install -e .

# 2. OT-Agent datagen extras (on compute node)
cd $SCRATCH/OpenThoughts-Agent
git submodule update --init --remote sft/llamafactory
uv pip install -e ".[datagen]"

# 3. SFT extras (on compute node)
cd sft/llamafactory
git checkout penfever/working_branch   # has relaxed version ceilings (see below)
uv pip install -e ".[liger-kernel,deepspeed,hf-kernels]"

# 4. Env vars
source $SCRATCH/keys.env && source ./hpc/dotenv/tacc.env
```

**`srun` build wrapper** (use this pattern for any install):
```bash
# Write a script, then srun it on a compute node
ssh TACCVista 'cat > $SCRATCH/build.sh << '\''EOF'\''
#!/bin/bash
source $SCRATCH/miniconda3/etc/profile.d/conda.sh && conda activate otagent
cd $SCRATCH/OpenThoughts-Agent
# ... your uv pip install commands here ...
EOF
chmod +x $SCRATCH/build.sh'

ssh TACCVista "srun -p gg -N 1 -n 1 -t 01:00:00 --account=CCR24067 bash /scratch/10635/penfever/build.sh"
```

### LLaMA-Factory version ceilings (relaxed)

The upstream `requirements.txt` pins hard ceilings that downgrade core packages
(datasets<=4.4.1, safetensors<=0.5.3, pydantic<=2.11.9, gradio<=5.45.0).
Branch **`penfever/working_branch`** on `mlfoundations/llama-factory` removes
these ceilings so the SFT install does NOT clobber the datagen env:
- `datasets>=2.16.0` (was `<=4.4.1`)
- `safetensors` (was `<=0.5.3`)
- `pydantic` (was `<=2.11.9`)
- `gradio>=4.38.0` (was `<=5.45.0`)

Always `git checkout penfever/working_branch` in the submodule before installing.

### flash_attn on aarch64 — INSTALLED (2026-07-11, flash-attn 2.8.3)

**A matching prebuilt aarch64 wheel NOW EXISTS** (the old "no wheel" note below was true
on 2026-06-25 but is STALE — `mjun0812/flash-attention-prebuild-wheels` added a torch-2.11
aarch64 set). Installed into the **`sft-axolotl`** env (the env the axolotl SFT chain runs
in — NOT `otagent`; the axolotl backend uses `--conda_env sft-axolotl`):
- **Wheel**: `flash_attn-2.8.3+cu128torch2.11-cp312-cp312-linux_aarch64.whl`
  (release **v0.9.22**) — EXACT match to torch 2.11.0+cu128 / Python 3.12 / aarch64.
  Install (prebuilt → download-only, no nvcc): `pip install --no-deps <wheel-url>`
  (`--no-deps` so pip never touches torch; `einops` already present).
- **GPU-verified** on a GH200 (`-p gh-dev` job 822558): `flash_attn_2_cuda` loads clean
  (no undefined-symbol/ABI mismatch) and a real `flash_attn_func` bf16 forward runs.
- **Config switch**: `sft/axolotl_configs/qwen3_32b_ot_sft_10k.yaml` `attn_implementation:
  sdpa` → `flash_attention: true` (the translator routes this to `attn_implementation:
  flash_attention_2`; an explicit `attn_implementation` WINS, so the sdpa line was removed —
  `hpc/axolotl_config_utils.py` L211-221). Axolotl pydantic-validates it. Expected ~2× over
  the ~338 s/it SDPA throughput. `agent_logs/2026-07-11_tacc_flash_attn_aarch64_wheel.md`.
  - **⚠ Takes effect only on a FRESH `python -m hpc.launch` submission — NOT on an `afterany`
    chain-restart.** A source-config edit re-renders the per-run `configs/*_train_config.yaml`
    ONLY when `hpc.launch` runs (which increments the experiment dir `_N`→`_N+1` and renders).
    `--max_restarts` submits N `afterany`-dependent sbatch legs that ALL point at the SAME
    already-rendered sbatch/config — so once the head job's config is rendered, editing the
    source YAML and letting the chain restart does NOTHING (the legs keep the stale render).
    **Proof (2026-07-11):** the flash-attn source edit landed AFTER exp dir `_14` was rendered
    (03:27, `attn_implementation: sdpa`); the whole 822306→307→308→309 `afterany` chain silently
    kept running SDPA. Fix = a FRESH submission → new dir `_15` re-rendered `flash_attention_2`
    (job 823417 + chain). **Rule: any source-config change requires a fresh `hpc.launch`, never
    a chain restart, to take effect.** `agent_logs/2026-07-11_tacc_axolotl32b_freshrelaunch_flashattn.md`.
- flash-attn 2.8.3 was ALSO installed into `otagent` (harmless — otagent doesn't run axolotl;
  available if other otagent workflows want it).

### Checkpoint save: SHARDED (16-bit gather OFF) — CONSOLIDATE AT CLEANUP

The axolotl-32B run saves **DeepSpeed-SHARDED** checkpoints — `deepspeed_config:
sft/axolotl_configs/deepspeed/zero3_bf16_shardsave.json` sets `gather_16bit_weights_on_model_save:
false` (the consolidated-16bit save-gather deadlocked the 16-node Vista IB fabric at step-10 save —
CONFIRMED job 823417, exp `_15`; `agent_logs/2026-07-12_tacc_axolotl32b_nccl_save_gather_hang.md`).
Consequence: checkpoint-N dirs hold per-rank `global_stepN/*.pt` + `zero_to_fp32.py`, **NO
consolidated root safetensors even at end-of-training** → cleanup MUST take the sft-job-cleanup
**32B ZeRO-3 consolidate path** (`global_stepN/`+`zero_to_fp32.py` recognition → consolidate before
HF upload). `deepspeed:` in the source YAML is only the ON/OFF toggle — the honored path key is
`deepspeed_config:` (the translator ignores the `deepspeed:` value).

Superseded stale note (2026-06-25 — kept for provenance): "No prebuilt wheel for torch
2.11+cu128 on aarch64; v0.6.4 needs a torch 2.9.0 downgrade; decision = use SDPA."

### SFT on GH200 — HBM is marginal; 3 gotchas that look like config bugs but aren't
1. **HBM is right at the edge for 32B ZeRO-3 @ seq 32k on 96GB** — it fits ONLY with full CPU-offload
   (params+optimizer), and every MB counts. **⚠ NCCL env tuning costs HBM: raising `NCCL_BUFFSIZE`
   (4MB→32MB) tipped this config into a first-backward CUDA-OOM that masqueraded as a recurring
   "step ~155-190 reduce_scatter death wall"** (killed every leg; reverting `NCCL_BUFFSIZE` to default →
   trained clean past step 200, job 832899). **Rule: keep `NCCL_BUFFSIZE` at default on HBM-marginal SFT;
   when a backward OOMs, suspect a recent NCCL-env bump BEFORE the config.** (Alt for speed/headroom:
   32-node no-offload — 2× nodes, but ~2× faster steps + HBM slack.)
2. **Lustre breaks advisory FileLocks under N-way concurrency** (ENOLCK / ESTALE): any framework that
   `flock()`s on shared `$SCRATCH` *before* dist-init (axolotl loads datasets pre-dist-init; the HF
   `datasets` builder also locks) hangs/fails at 16-way. Fix = **pretokenize once** into a shared path +
   a **lock-free persistent-sentinel** (all ranks `load_from_disk`, no flock) — NOT node-local-everything
   (does N× redundant tokenize + can desync-deadlock at "Generating split").
3. **c10d rendezvous flakes on some GH200 nodes** (transient `DistNetworkError`/`RendezvousConnectionError`
   at bring-up — seen on c637/c638) → add the offenders to the sbatch `--exclude` / `node_exclusion_list`
   (`hpc/hpc.py`); the `afterany` chain auto-retries a transient. Distinguish from the OOM above: rendezvous
   dies in the first ~5 min pre-training; OOM dies ~2 min into the first backward.

### Building the vLLM wheel from source (otagent env, aarch64 + Hopper sm_90)

**Proven recipe (2026-06-25, job 787093, node i614-011, fork `mlfoundations/vllm` @ `76259c63a`).**

> **⚠ Builds MUST run in a CPU SLURM allocation, NEVER on the login node.** The vLLM CUDA
> compile is `nvcc` host-side work that does NOT need a GPU to BUILD — request a **Grace-Grace
> CPU node (`-p gg`)**, not a GPU node. The login node is shared/under load and `uv`/Rust tooling
> OOMs there.
>
> **`salloc` is BLOCKED on Vista** (`salloc job submission is not allowed`) — interactive sessions
> must use `idev` (2h cap on `gh-dev`, too short for the ~hour build). So the build is submitted as
> a **CPU-only `sbatch` batch job** that runs the whole clone → build → install → verify script.
> (An `idev -p gg -m 700` interactive session inside tmux is the alternative, but sbatch is the
> proven, persistent path.)

**Toolchain** — must match the otagent env's torch `cu128`: load **nvcc 12.8 + gcc 13.2** (NOT the
default `nvidia/24.7`, which only ships cuda/12.5; and `cuda/12.8` won't load until a real gcc is
loaded first):
```bash
module purge && module load gcc/13.2.0 cuda/12.8   # -> nvcc 12.8.93, gcc 13.2.0, $TACC_CUDA_DIR set
```

**Build flags**: `TORCH_CUDA_ARCH_LIST="9.0"` (Hopper GH200), `CUDA_HOME=$TACC_CUDA_DIR`,
`VLLM_TARGET_DEVICE=cuda`, `MAX_JOBS=32`, `NVCC_THREADS=4`. Build with **`--no-build-isolation`** so it
uses the env's `torch==2.11.0` as the base; first `pip install` the build-system requires
(`setuptools<81 setuptools-scm packaging wheel ninja jinja2 cmake` — the env ships ninja but NOT
setuptools_scm). **Install these WITH deps (no `--no-deps`)** — they are pure-Python and don't touch
torch, and setuptools-scm 10.x needs its `vcs-versioning` helper (a `--no-deps` install of just
setuptools-scm fails the build with `ModuleNotFoundError: No module named 'vcs_versioning'`).
Wheel command: `python -m pip wheel . --no-build-isolation --no-deps -w dist/` (the `--no-deps` HERE,
on the vLLM wheel itself, is correct — it stops pip resolving vLLM's runtime deps).

The whole thing is captured in `$SCRATCH/build_vllm.sbatch` (clone → toolchain → build → install →
import-verify). Submit + watch:
```bash
sbatch $SCRATCH/build_vllm.sbatch          # -> job NNN on a gg node; log: $SCRATCH/vllm_build.NNN.log
squeue -u penfever ; tail -f $SCRATCH/vllm_build.NNN.log
```
Install (done by the script, or manually after): `pip install --no-deps --force-reinstall $SCRATCH/vllm/dist/vllm-*.whl`
then verify `python -c "import vllm; print(vllm.__version__, vllm.__file__)"`.

### vLLM standalone (vllm_sandboxes env)
```bash
source /scratch/10635/penfever/miniconda3/bin/activate vllm_sandboxes
module load gcc/15.1.0
export TRITON_CC=$(which gcc)
export LD_LIBRARY_PATH=/home1/apps/gcc/15.1.0/lib64:/scratch/10635/penfever/miniconda3/lib/python3.12/site-packages/torch/lib:$LD_LIBRARY_PATH
vllm serve meta-llama/Llama-3.1-8B-Instruct
```

### Evalchemy (standard evals)
```bash
cd $SCRATCH/evalchemy && conda activate evalchemy
```

### Source conda (generic)
```bash
source /scratch/10635/penfever/miniconda3/etc/profile.d/conda.sh
```

## aarch64 specifics

- Miniconda installer: `Miniconda3-latest-Linux-aarch64.sh` (NOT x86_64).
- System modules via Lmod: `module load gcc/15.1.0`, `module load cuda/12.6`, `module load nvidia/24.7`.
- Default loaded modules: `TACC`, `cmake/4.1.1`, `gcc/15.1.0`, `nvidia/24.7`, `openmpi/5.0.5`, `nvpl/24.5`, `ucx/1.18.1`.
- GH200 unified memory: GPU memory is used as filesystem cache and **cannot always be reclaimed** after
  an application exits → occasional hung nodes requiring reboot. Avoid relying on clean memory reclamation.
- **Native JIT / C-extension builds need a real gcc MODULE — the default nvc++/system compiler rejects the
  armv9 flags.** This bites any runtime-compiled op: Triton (`TRITON_CC`), and **`DeepSpeedCPUAdam` (the ZeRO
  offload optimizer).** Recipe: `module load gcc/13.2.0` (matches the cu128 torch toolchain; `gcc/15.1.0` also
  works) + `export CC=$(which gcc) CXX=$(which g++)` (+ `TRITON_CC=$(which gcc)`), prepend the module's
  `lib64` to `LD_LIBRARY_PATH`, and prebuild on a `-p gg` node (`DS_BUILD_CPU_ADAM=1`). **⚠ "cpu_adam /
  CPU-offload is unbuildable on aarch64" is FALSE** — it's a wrong-compiler artifact. Proof: LLaMA-Factory
  builds+runs `liger-kernel` + `deepspeed` (incl. `ds_z3_offload` CPU-offloaded Adam) on THIS aarch64 via
  `.[liger-kernel,deepspeed]` and fits Qwen3-32B@32k. So both the offload lever AND the liger fused-CE lever
  are available on Vista. (Context: the 32B axolotl OOM = liger-off + offload-off, not a capacity wall —
  `.agents/projects/axolotl/axolotl.md` gotcha #2 + §Qwen3-32B; `agent_logs/2026-07-09_sft_32b_axolotl_oom_config_gap.md`.)

## Syncing eval traces to local (via AWS S3)

TACC eval traces (especially from Negin/Richard's shared dir) can be synced to local through an AWS S3
bucket:

```bash
# TACC → S3 (from TACC login node)
aws s3 sync /scratch/08134/negin/dc-agent-shared/dc-agent/eval/tacc/jobs/to_upload/<run_dir> \
  s3://oumi-science-donotdelete/benjamin/<run_dir> --only-show-errors

# S3 → local Mac (from Mac)
aws s3 sync s3://oumi-science-donotdelete/benjamin/<run_dir> ../evaltraces/<run_dir> --only-show-errors
```

## Agentic eval on Vista (unified v6 listener)

TACC Vista is wired into the unified v6 eval listener (added 2026-06-25). Files:
`eval/clusters/tacc.yaml` (cluster config), `eval/tacc/eval_harbor.sbatch` (serve+Harbor+Daytona
driver), `eval/clusters/tacc_baseline_model_configs.yaml` (per-model serve overrides, all TP=1).

**The Vista-specific particulars (vs Leonardo):**

- **Daytona connectivity is DIRECT — NO proxy / SSH-SOCKS5 / step-ca cert.** Vista compute nodes have
  **full direct internet egress** (verified: `huggingface.co`, `app.daytona.io`, generic all return 200
  from a compute node). The terminus-2 LLM call is made by the harbor orchestrator ON the compute node to
  the LOCAL vLLM (`localhost:8000`) — the Daytona sandbox only runs terminal commands and never calls the
  model — so the only external dependency is compute-node → Daytona API, which works directly. The TACC
  sbatch has NO `proxied()` wrapper, NO `start_proxy_tunnel.sh`, NO model pre-download (compute node
  downloads from HF directly). This is the big simplification over Leonardo.
- **GPUs are NOT a SLURM gres** (`scontrol show node` → `Gres=(null)`) and **RealMemory is misreported as
  1 (MB)**. So `--gres gpu:N` and `--mem=<MB>` both FAIL. The listener handles this via the new
  `hardware.gpu_gres: false` flag in `tacc.yaml` → it requests whole NODES (`--nodes
  ceil(TP*DP / gpus_per_node)`) with NO `--gres` / `--mem` / `--cpus-per-task` (the node is allocated
  exclusively, CPUAlloc=72). **1 GH200 (96GB) per node** → a 32B serves at **TP=1** on one GPU (a
  multi-GPU TP would need a multi-node vLLM). The TACC baseline config pins the 32B family to TP=1.
- **Do NOT use `--pre-download` on the listener.** It runs HF snapshot_download on the shared login node,
  whose Rust-based HF transfer OOMs (`memory allocation of N bytes failed` → `Aborted (core dumped)`),
  killing the listener. Drop `--pre-download`; the sbatch downloads the model directly on the compute node
  (188GB RAM, direct egress).
- **The `gh` partition is heavily contended** (~100 pending jobs, est. start ~6h out as of 2026-06-25).
  For a quick infra-canary use **`-p gh-dev`** (2h wall cap, 1 running job, ~5 idle nodes) by overriding
  `--partition gh-dev --time 02:00:00` on the sbatch (keep `tacc.yaml` default = `gh` for production).
- **Secrets**: `$SCRATCH/keys.env` (= `DC_AGENT_SECRET_ENV`) must exist with `SUPABASE_URL` /
  `SUPABASE_ANON_KEY` (the listener's model-discovery query is FATAL without Supabase) + `HF_TOKEN` +
  `DAYTONA_API_KEY`. It is the local secrets env synced over (see `.agents/secret.md`). `HF_TOKEN`
  is also set in `~/.bashrc`. The Daytona org keys are also hardcoded in the sbatch (same bank as Leonardo).
- **Benign serve noise**: terminus-2 hits the vLLM `/tokenize` endpoint for token-counting, and the fork
  wheel's Qwen3 chat-template renderer raises `IndexError: list index out of range` there (`hf.py:682
  safe_apply_chat_template`). This is **NON-FATAL** — `/v1/chat/completions` generations succeed (real
  `<think>` responses, ~25s/gen), trials advance through multiple episodes, and the agent falls back from
  the failed tokenize. Do NOT treat the `/tokenize` errors as a launch failure. (Canary 2026-06-25 job
  787344: serve READY, Daytona `_DaytonaDirect` sandboxes up, 34 trials, 17 multi-episode, vLLM
  `Running: ~29 reqs` — fully progressing.)
- **⚠ Serving the `qwen3_5`/`qwen3_6` family (tmax-*, Qwen3.5/3.6) needs `limit_mm_per_prompt: 0` — text-only weights in a multimodal VL config.** These checkpoints declare a VL arch (e.g. `allenai/tmax-9b`: `architectures: ["Qwen3_5ForConditionalGeneration"]` + a `vision_config` + image/video token ids) but ship text-only weights and **no `preprocessor_config.json`**. The `otagent` env's **fork-vLLM (`0.1.dev16611+g76259c63a`, built from source — §"Building the vLLM wheel from source") resolves `Qwen3_5ForConditionalGeneration` CLEANLY** (verified from the crash log: `Resolved architecture: Qwen3_5ForConditionalGeneration`, NO `qwen3_vl` misdetect, NO "model type not recognized"). BUT because that arch is a *multimodal class*, vLLM eagerly builds a `MultiModalBudget` at init → `get_image_processor()` → loads `preprocessor_config.json` (absent) → **`OSError`, fatal, vLLM never healthy, 0 trials** (jobs `787630`/`787631`, FAILED ~50 min in, 2026-06-25; the non-VL Qwen3-32B canary `787589` serves fine). **FIX (cheap, CONFIRMED — NOT an env rebuild):** set **`limit_mm_per_prompt: '{"image":0,"video":0}'`** on the model's serve entry (its OWN YAML field, NEVER folded into `extra_args` — the JSON quotes get word-split) → vLLM skips the MultiModalBudget image path, exactly as the identical fork-vLLM serves tmax-9b on Leonardo. Applied 2026-06-26 to `tacc_baseline_model_configs.yaml` (added a tmax-9b entry — it had none → catch-all `.*` → same crash at 32k) + `_65k.yaml`. **(Correction:** the first-pass "needs a transformers-5.x `eval-qwen35` env" theory was WRONG — the crash log proved TACC's `otagent` fork-vLLM already resolves `qwen3_5`; the only delta vs Leonardo was the missing MM-disable flag; the transformers-4.57-vs-5.x angle is a red herring for this crash. Cf. `agent_logs/2026-06-26_tacc_tmax9b_vl_misdetect.md`.)
- **Launch (from `$SCRATCH/OpenThoughts-Agent`, `export PYTHONPATH="$PWD:$PYTHONPATH"`, secrets sourced):**
  ```bash
  python eval/unified_eval_listener.py --cluster-config eval/clusters/tacc.yaml \
    --baseline-model-configs eval/clusters/tacc_baseline_model_configs.yaml \
    --preset tb2 --require-priority-list --priority-file <list> \
    --config-yaml dcagent_eval_config_no_override.yaml --force-reeval --once --verbose
  ```
  (NOT `eval/configs/baseline_model_configs_minimal.yaml` — that pins Qwen3-32B to TP=2, which on Vista's
  1-GPU nodes would need multi-node vLLM. Use the TACC baseline config.)

## VS Code remote tunnel

```bash
~/apps/vscode-cli/code tunnel --name vista-idev --verbose
```

## Shared directory ownership

To preserve executability while locking out non-group members:
```bash
chmod -R u+rwX,g+rwX,o-rwx /path/to/dir
find /path/to/dir -type d -exec chmod g+s {} +
umask 007
setfacl -R -d -m g::rwx /path/to/dir
setfacl -R -d -m o::--- /path/to/dir
```

## Gotchas

- **`uv` crashes on the login node** (Rust memory allocation failure). Use `srun -p gg`
  to get a compute node for any `uv pip install` / build operation. See Environment setup.
- **`/home1/10635/penfever/.cache` is a symlink** to `$SCRATCH/.cache` (fixed 2026-06-25;
  was previously a broken symlink to `$SCRATCH/hf_cache/.cache`). If `uv` fails with
  `failed to create directory ... File exists`, check this symlink.
- **`gh-dev` has a 2-hour wall cap.** Use `gh`/`gg` for anything longer.
- **`idev -p gh-dev -m >120` fails** with `QOSMaxWallDurationPerJobLimit` regardless of partition's
  `MaxTime=UNLIMITED`.
- **GH200 memory is not always reclaimable.** A crashed job can leave a node unusable until reboot;
  if `srun`/`idev` lands on such a node, exit and request a fresh allocation.
- **SkyRL TACC setup**: <https://github.com/NovaSky-AI/SkyRL/blob/arm/skyrl-train/scripts/tacc_setup.sh>
  (the `arm` branch has TACC-specific setup).
- **SUs expire 2025-12-31.** Check `bbalance` periodically; request renewal if running low.
