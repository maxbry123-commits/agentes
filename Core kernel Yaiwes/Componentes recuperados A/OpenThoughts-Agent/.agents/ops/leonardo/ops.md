## CINECA Leonardo Access

**SSH**: ControlMaster multiplexing + step-ca cert:
```bash
ssh Leonardo    # complete 2FA once; socket persists 8h
```
> **Host keys ROTATE (benign — NOT an anomaly).** Round-robin login nodes rotate host keys, so a fresh connection (esp. `-o ControlPath=none` / `-o ControlMaster=no`) can hit `REMOTE HOST IDENTIFICATION HAS CHANGED` / a `known_hosts` mismatch. Use the standard `ssh Leonardo` (ControlMaster socket). Do NOT flag it as a failure or block on a `known_hosts` refresh.

**Cluster facts**: A100 64GB GPUs, 4/node, 3456 nodes, SLURM scheduler. User `bfeuer00`, account `AIFAC_5C0_290` (**valid to 2026-08-02, ~71% budget used as of 2026-07-08**), partition `boost_usr_prod`. Max wall 24h (`--time 23:59:00`; `boost_usr_prod` has a 1-day limit). **No internet on compute nodes** (use the SOCKS5 proxy / SSH tunnel). Compilers come from conda (GCC 15.2, CUDA 13.2) — do NOT `module load gcc cuda` (too old). Leonardo is in use; cron covers Jupiter + Leonardo.

> **⚠ MAINTENANCE-vs-account gotcha (2026-07-08).** During a CINECA maintenance reservation the `boost_usr_prod` partition is drained and **`sbatch` fails with `Batch job submission failed: Invalid account or account/partition combination specified`** — even a trivial 1-min test job, and identically with or without an explicit QOS. **This is the MAINTENANCE signature, NOT an account revocation or budget exhaustion** (AIFAC_5C0_290 is valid + funded — see above). Do NOT chase a "restore the account with CINECA" red herring: check for a scheduled maintenance window and **retry after it clears** (typical window ~1 day). E.g. 2026-07-08: all 8 flawed_summ re-fires failed this way → Leonardo was in a 1-day maintenance, not an account problem; retried the next day.

## Pre-launch preamble
```bash
source /leonardo_work/AIFAC_5C0_290/bfeuer00/miniforge3/etc/profile.d/conda.sh && \
conda activate otagent && \
cd /leonardo_work/AIFAC_5C0_290/bfeuer00/code/OpenThoughts-Agent && GIT_TERMINAL_PROMPT=0 git pull && \
cd /leonardo_work/AIFAC_5C0_290/bfeuer00/code/harbor && GIT_TERMINAL_PROMPT=0 git pull && \
source hpc/dotenv/leonardo.env && source ~/secrets.env && \
cd /leonardo_work/AIFAC_5C0_290/bfeuer00/code/OpenThoughts-Agent
```

## Key paths
- Code: `/leonardo_work/AIFAC_5C0_290/bfeuer00/code/OpenThoughts-Agent`
- Harbor: `/leonardo_work/AIFAC_5C0_290/bfeuer00/code/harbor`
- MarinSkyRL: `/leonardo_work/AIFAC_5C0_290/bfeuer00/code/MarinSkyRL`
- evalchemy (standard / pass@k evals): `/leonardo_work/AIFAC_5C0_290/bfeuer00/code/evalchemy-marin` — **single canonical** clone (remote `origin` = `marin-community/evalchemy`, branch `main`; editable-installed in the `evalchemy-marin` conda env; see ENVIRONMENT_MAP §2e).
- Data/HF cache: `/leonardo_work/AIFAC_5C0_290/bfeuer00/data/hub`
- Experiments/`$CHECKPOINTS_DIR`: `/leonardo_work/AIFAC_5C0_290/bfeuer00/experiments`

> **⚠ WRITE-PATH MANDATE (quota-bind — obey in every launcher/sbatch/subagent).** Two filesystems, two purposes:
> - **`$WORK` (`/leonardo_work/AIFAC_5C0_290/bfeuer00`, ~1.4 PB GPFS, persistent)** — ALL persistent/large writes: RL/SFT checkpoints, `trainer.export_path`, HF cache (`$WORK/data/hub`), envs, experiment outputs. The dotenv sets `CHECKPOINTS_DIR=$WORK/experiments` — use it; never hardcode a checkpoint/export path onto scratch.
> - **`$SCRATCH_FAST` (`/leonardo_scratch/fast/AIFAC_5C0_290/bfeuer00`, 1 TB Lustre, auto-purged)** — ONLY ephemeral caches/tmp (`VLLM_CONFIG_ROOT`/`TRITON_CACHE_DIR`/`FLASHINFER_WORKSPACE_BASE`). 1 TB, shared, chronically OVER quota — a checkpoint/export here fails with `OSError: [Errno 122] Disk quota exceeded` (NOT an OOM).
> - **Any launch subagent MUST verify its sbatch's checkpoint/export paths resolve to `$WORK`/`$CHECKPOINTS_DIR`, not `$SF`/`$SCRATCH_FAST`, BEFORE submitting.**

## Correct upstream per codebase (SoT = Mac clones under `/Users/benjaminfeuer/Documents/`; branch = `penfever/working` except harbor)
- **OpenThoughts-Agent** → `origin` = `open-thoughts/OpenThoughts-Agent` (`penfever/working`).
- **harbor** → `marin` = `marin-community/harbor`, branch `main` (`penfever/working` RETIRED — worktree→PR→main; migrate a stale cluster clone: `git checkout main && git pull` on next touch).
- **MarinSkyRL** → `marin-community/MarinSkyRL` `penfever/working` (see `.agents/projects/marinskyrl/marinskyrl.md`).
- Sync discipline: commit on Mac → push → `git pull` on the cluster (Leonardo can't push). SFT runs also need `git submodule update --init --remote sft/llamafactory`.

## Conda envs
- **`otagent`** — dense Qwen3 / Llama-3-tokenizer (default)
- **`sft-qwen35`** — Qwen3.5 hybrid arch ONLY
- **`evalchemy-marin`** — evalchemy standard evals

## SIF / runtime — vLLM 0.20.2rc0 cross-cluster twin
Leonardo analogue of Jupiter's prod `skyrl_megatron_vllm0202rc0_r3.sif` (vLLM fork `penfever/working @ 5d7319dd1`: 0.20.2rc0 + R3 capture + DCP GQA-LSE fp32 fix). Built as a **writable singularity sandbox dir** on `$WORK` (NOT a `.sif` — `mksquashfs` OOMs / `lustre.lov` xattr errors on the Lustre login node). Full runtime detail + recipe paths: `ENVIRONMENT_MAP.md` §2d.
- **cu13/torch-2.9 path taken** (NGC `pytorch:25.09-py3`, arch 8.0, via `cuda-compat-13` forward-compat on the A100's 535.274.02 host driver — forward-compat verified: a cu13 fp32 matmul ran; `/proc/self/maps` confirmed the bundled `cuda-compat-13` `libcuda.so.580.82.07` loaded). Sandbox at `$WORK/containers/pytorch_2509_sbx` (19 G).
- **Run convention:** `SINGULARITYENV_LD_LIBRARY_PATH=/usr/local/cuda-13.0/compat/lib.real singularity exec --nv …`
- **Build:** `singularity build --sandbox` with `TMPDIR`/`SINGULARITY_TMPDIR` forced onto GPFS WORK (default `TMPDIR=/scratch_local` is Lustre → xattr storm). Recipes: `sif_build/recipes/{README_vllm0202rc0_r3_leonardo_cu13.md, build_vllm0202rc0_r3_leonardo_cu13.sbatch}`; the torch-2.8 / NGC-25.06 / CUDA-12.9.1 recipe is retained as the documented fallback.

## HF Upload — use the sbatch-tunnel, NEVER the login node
Leonardo login nodes SIGKILL any long-running user process after ~100s (process-agnostic — `nohup`, `tmux`, `systemd-run` all die ~100s, regardless of `hf` vs legacy `huggingface-cli`). The login node DOES have direct internet; the killer is the problem, not the network. **The reliable path is an sbatch job on a compute node with an SSH tunnel back to the login node.** Compute nodes have no direct internet, but `eval/leonardo/start_proxy_tunnel.sh` opens a SOCKS5 forward (compute→login05) and prints a `proxychains4 -q -f <config>` prefix wrapping any HF-bound command.

### Pre-flight (from your local Mac) — refresh the ~12h intra-cluster cert
```bash
step ssh certificate 'bfeuer00' --provisioner cineca-hpc \
  ~/.ssh/leonardo_daytona --no-password --insecure
ssh-keygen -R login.leonardo.cineca.it && \
rsync -avz -e 'ssh -i ~/.ssh/leonardo_daytona -o IdentitiesOnly=yes -o StrictHostKeyChecking=no' \
  ~/.ssh/leonardo_daytona ~/.ssh/leonardo_daytona.pub ~/.ssh/leonardo_daytona-cert.pub \
  bfeuer00@login.leonardo.cineca.it:~/.ssh/
```
Verify: `ssh-keygen -L -f ~/.ssh/leonardo_daytona-cert.pub | grep Valid`. Key on Leonardo: `/leonardo/home/userexternal/bfeuer00/.ssh/leonardo_daytona`. (The `leonardo_daytona` step-ca cert is for the Daytona/SOCKS proxy; the intra-cluster `ssh Leonardo` key is a separate credential. The auth-required HedgeDoc setup-instructions URL is in `.agents/secret.md` — untracked.)
**Cert expired?** The SOCKS tunnel gets `Permission denied (publickey)` and the `upload_*.sbatch` job dies in ~19s — when a Leonardo upload sbatch fails fast on a publickey error, suspect the expired cert first and refresh via the pre-flight above (needs interactive CINECA SSO 2FA in a browser; can't be done headless). Do NOT fall back to a detached login-node upload — it dies at ~100s and leaves a partial. Refresh the cert and use the sbatch job.

### sbatch template for HF upload
```bash
cat > /leonardo_work/AIFAC_5C0_290/bfeuer00/upload_<job_name>.sbatch <<'EOF'
#!/bin/bash
#SBATCH --job-name=hf_upload_<short>
#SBATCH --output=<workdir>/upload_logs/upload_sbatch.log
#SBATCH --time=00:30:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --partition=boost_usr_prod
#SBATCH --account=AIFAC_5C0_290
#SBATCH --gres=gpu:1
#SBATCH --qos=boost_qos_dbg

set -e
source /leonardo_work/AIFAC_5C0_290/bfeuer00/miniforge3/etc/profile.d/conda.sh
conda activate otagent
source ~/secrets.env

WD=<workdir>
DCFT=/leonardo_work/AIFAC_5C0_290/bfeuer00/code/OpenThoughts-Agent

unset LD_PRELOAD
export PATH="/leonardo_work/AIFAC_5C0_290/bfeuer00/proxychains/bin:${PATH}"
CMD_PREFIX=$(bash "$DCFT/eval/leonardo/start_proxy_tunnel.sh")

cd $WD/final_repo   # or $CHECKPOINTS_DIR/<job_name> for 8B path
$CMD_PREFIX /leonardo_work/AIFAC_5C0_290/bfeuer00/miniforge3/envs/otagent/bin/hf upload \
    <hub_model_id> . . \
    --repo-type=model
EOF
cd /leonardo_work/AIFAC_5C0_290/bfeuer00
sbatch upload_<job_name>.sbatch
```
Then `squeue -j <jobid>` and `tail -f <workdir>/upload_logs/upload_sbatch.log`.

### Sizing
- 131GB consolidated 32B → ~4 min wall through the tunnel.
- 30 min wall fits `boost_qos_dbg` (debug QOS); longer jobs need a different QOS.
- `hf upload` is sequential (no `--num-workers`); use `hf upload`, NOT `upload-large-folder` (deprecation stub AND deadlocks against HF Hub LFS rate limits).
- Resume is automatic — `.cache/huggingface/` persists state; if requeued, `hf upload` picks up where it left off.

## Agentic Harbor eval (terminus-2) — feasible on compute via the SOCKS5 proxy
Agentic terminus-2 eval runs end-to-end on Leonardo **compute** nodes (no native internet) through `eval/leonardo/start_proxy_tunnel.sh` (SOCKS5 compute→login05 + proxychains4). Verified 2026-06-20 (job 47436018, Qwen3-1.7B × tb2 subset → Supabase `sandbox_jobs` row `d9eef9e5-525b-476a-b4bd-f8937bf1588b` `Finished`, 9 trials, 0 errors, traces on HF, benchmark auto-registered).
- For terminus-2 the LLM call is made by the **orchestrator on the compute node** to the locally-served vLLM (`api_base=http://$MASTER_ADDR:8000`); the Daytona sandbox only runs shell commands and never reaches the model. So the only outbound traffic is orchestrator→Daytona-API + →HF, both carried by the proxy — **no pinggy / served-model tunnel needed.** (Agentic RL, with its heavier cross-node/Daytona coupling, is NOT feasible on Leonardo; eval is.)
- **Single cross-cluster entrypoint:** `eval/unified_eval_listener.py --cluster-config eval/clusters/<cluster>.yaml` (each cluster-config carries its own `sbatch_script` + log-dir; the Leonardo config points `sbatch_script` at `eval/leonardo/eval_harbor.sbatch`). Launch in tmux on Leonardo, after the preamble:
```bash
python eval/unified_eval_listener.py --cluster-config eval/clusters/leonardo.yaml --preset <tb2|swebench|v2|...> \
  --require-priority-list --priority-file <list> --pre-download --once --verbose
```
- **Load-bearing gotcha:** `eval/leonardo/eval_harbor.sbatch` MUST pass `--jobs-dir "$EVAL_JOBS_DIR"` to harbor — without it harbor writes trials to the wrong dir and Supabase auto-register silently no-ops. Eval auto-registration to Supabase is BY DESIGN (the `enable_db_registration:false` guardrail applies to RL/SFT *training* YAMLs, not evals). Depends on the `~/.ssh/leonardo_daytona` step-ca cert being fresh (~12h; refresh per the pre-flight above).

## ptrace LOCKED DOWN cluster-wide (`ptrace_scope=2`) — software profilers/debuggers FAIL (CVE-2026-46333)
Since 2026-05-15, CINECA raised `kernel.yama.ptrace_scope` from `0` → **`2`** (admin-only ptrace). Cluster-wide kernel setting (broader than the SIF-only ptrace block on Jupiter — `ops/jupiter/ops.md` §Debugging tooling). **Any ptrace/software-sampling tool fails** — `py-spy dump`/`py-spy record`, `gdb -p`, software-sampling profilers. Do NOT burn time on them against a wedged Leonardo process.
- Use **hardware-based sampling** (`perf`-backed), not software (ptrace). Check whether a tool's collection method is configurable to hw before running.
- **Intel VTune** (`vtune -collect <analysis_type>`) — verify hw-sampling support per analysis with `vtune -help collect <analysis_type>`:
  - **NOT affected (work as-is):** `performance-snapshot`, `uarch-exploration`, `hpc-performance`, `io`, `system-overview`.
  - **Affected (need the hw-sampling knob):** `hotspots`, `threading`.
    - `vtune -collect hotspots  -r vtune_hotspots  -knob sampling-mode=hw`
    - `vtune -collect threading -r vtune_threading -knob sampling-and-waits=hw`
  - ⚠ **`memory-consumption` has NO hw-sampling mode → unusable under `ptrace_scope=2`.**
- For wedged RL/inference: ptrace is out — rely on NCCL trace + per-rank `opCount` alignment + last-log-line-per-rank + `/proc/<pid>/{stack,environ}` (readable without ptrace). faulthandler/`SIGUSR1`-stack-dump is in-process (no ptrace) and still works if instrumented at launch.

## Sweep / gather particulars (for the `monitor-cron-sweep` skill)
Leonardo-specific triage rules the cron sweep applies each pass. The skill's cross-cluster rules (liveness check, passthrough exceptions, false-drain validation) are general; these are the Leonardo layer.

- **GPFS `find`/`du` ban.** Stat-walks stall the SSH session for minutes. Locate logs via `scontrol show job <id> -o` `StdOut=`/`%Z` + depth-1 `ls`, never `find`/`du` on the GPFS scratch tree.
- **Eval log-path trap.** If the `scontrol` `StdOut=` path doesn't exist, read `data_<jobid>.out` in the job's `%Z` workdir before judging liveness (a path mismatch, not a death).
- **Standard-eval results JSON without `Mean:` lines is the expected shape**, not a broken run.
- **Leonardo's binding constraint is disk QUOTA, not inodes** — ckpts/exports → `$WORK`, never the chronically-over-quota `$SCRATCH_FAST` (see WRITE-PATH MANDATE above).
- **HF upload via the sbatch-tunnel** (login node SIGKILLs ~100s) + the fresh `~/.ssh/leonardo_daytona` step-ca cert (~12h) — full mechanics in the **HF Upload** section above.
- **Campaign-driver (sweep tracking).** The 4 `rl_dlp` Delphi standard-GRPO cells + the **SummarizationTimeoutError-deflated re-eval campaign (a1-`<benchmark>` models)**. For flawed_summ specifically: drive off `experiments/active/flawed_summ_evals/POLICY.md` (the canonical directive) + `STATE.md` (the per-row worklist) each sweep — the gate, resume-until-registered, one-benchmark-at-a-time, snapshot-vs-sandbox reclaim + HARD caps, cluster priority, and in-flight target ALL live there; look them up, never hardcode.

---

# SFT (Leonardo particulars for the `sft-launch` skill)

Cluster-agnostic flow + backend/Delphi decisions: **`.agents/skills/sft-launch`**. This section is the Leonardo-specific procedural layer. The cluster facts above (A100-64GB, 4/node, no-internet-on-compute, login-node killer, 24h max wall, conda envs, WRITE-PATH MANDATE) drive almost every SFT quirk. Read **dsfs** (multi-node) + **canary blockers** before launching anything large — they are the two ways a run silently wastes a 24h slot. Authoritative launch template: `experiments/active/delphi/rl-scaling-laws-6279/SFT_LEONARDO_INSTRUCTIONS.md`.

## SFT preamble (adds SFT submodule sync to the general preamble)
```bash
ssh Leonardo   # step-ca cert; complete 2FA once, socket persists ~8h
source /leonardo_work/AIFAC_5C0_290/bfeuer00/miniforge3/etc/profile.d/conda.sh && \
conda activate otagent && \   # or sft-qwen35 for Qwen3.5 hybrid
cd /leonardo_work/AIFAC_5C0_290/bfeuer00/code/OpenThoughts-Agent && GIT_TERMINAL_PROMPT=0 git pull && \
git submodule update --init --remote sft/llamafactory && \
git submodule update --init sft/axolotl && \   # pinned; no --remote; only for --sft_backend axolotl
source hpc/dotenv/leonardo.env && source ~/secrets.env
```

## Launch template
```bash
DISABLE_VERSION_CHECK=1 python -m hpc.launch --job_type sft \
  --train_config_path sft/lf_configs/<family>/<cfg>.yaml \
  --time_limit 23:59:00 --num_nodes 4 --gpus_per_node 4 \
  --model_path <hf_base_model> \
  --dataset_dir <registry, e.g. sft/delphi> --dataset <instr>[,<warmup>] \
  [--mix_strategy interleave_under --interleave_probs 0.9,0.1] \
  --hub_model_id <hub_model_id> --internet_node --max_restarts 2
```
- Vary only `--model_path`/`--hub_model_id`/`--dataset` for a controlled set — configs bake template/cutoff/epochs/LR.
- **`--dry_run` the first cell** (confirm model, template, epochs, LR, role tags, `push_to_hub`).
- Multi-node SFT uses **`accelerate` (not torchrun)** — `training_launcher="accelerate"` in `hpc.py` (torchrun's c10d rendezvous fails on Leonardo inter-node TCP). `--num_nodes 4 --gpus_per_node 4` = 16 A100-64GB; ZeRO-3 handles ≤~9.7B full-FT.

## No-internet-on-compute handling (compute can't reach HF Hub)
1. **Pre-download model + datasets on the login node first** (detached tmux, retry): `export HF_HUB_ENABLE_HF_TRANSFER=1; hf download <base_model> --repo-type model; hf download <dataset_repo> --repo-type dataset` (monitor by `$HF_HUB_CACHE` size growth).
2. **`--internet_node`** — skips the launcher's own pre-download (`_materialize_dataset_and_model` does a `snapshot_download` on a *registry name* → 404 → looks like a stall). Everything is already cached by step 1.
3. **Offline dataset LOADING:** repoint each dataset in the registry `dataset_info.json` from `hf_hub_url` to a local `file_name` parquet dir (LF `load_from=file`), and strip the ~6 global schema-tag keys the launcher injects (they `KeyError` on heterogeneous mixes — let LF use the per-dataset registry tags).
4. **`push_to_hub: false`** in the config (repo-create at train start hits the unreachable hub → `OfflineModeIsEnabled` crash). Model saves to local disk; upload post-run via the sbatch-tunnel.

## ⚠️ Multi-node dataset prep — the `data_shared_file_system` cache race (the REAL "24h timeout")
A tiny model (e.g. 447M) multi-node SFT that idles to the 24h wall with `TIMEOUT`, never checkpointing, LOOKS like "24h tokenizing" but ISN'T (tokenizing the 555k/428k mixes takes ~65s with `preprocessing_num_workers: 16`). Real cause: with default `data_shared_file_system: false`, LF's `main_process_first(local=…)` barrier is **per-node**, so each node's local-rank-0 runs `datasets.map` simultaneously against the same shared GPFS cache → race → `FileNotFoundError` on a parquet shard → collective hangs → NCCL watchdog SIGABRTs at 600s → the step never releases → idle to the wall. Intermittent (timing-dependent). **Fix: `data_shared_file_system: true`** (global barrier; same tokens/loss — infra only) via a per-run config copy (e.g. `sft/lf_configs/delphi/4k_sft_dsfs.yaml`). Safe mid-grid. `--pretokenize`/`--pretokenize_bprod` is an OPTIONAL optimization, NOT this fix — reach for it only after confirming tokenization is actually the bottleneck (it usually isn't). Diagnose order: dsfs → schema-key `KeyError` → pretokenize.

## MANDATORY sbatch post-patch (the launcher does NOT do this for Leonardo SFT)
After `hpc.launch` generates the sbatch, BEFORE `sbatch`-ing, patch it. The newer launcher template no longer emits literal `WORKDIR="$PWD"`/`export DCFT="$WORKDIR"` lines (it resolves WORKDIR at runtime from `$DCFT`/`$DCFT_PRIVATE` via a dotenv loop; on the compute node neither is set → falls through to `$HOME` → `triton_cache.sh` "No such file" → `set -e` exit 1 in ~22s). **Inject literal `export DCFT=<code path>` and `export DCFT_PRIVATE=<code path>` immediately before the `conda activate` line** in the generated sbatch (also add the conda activation — `otagent`, NOT `sft-qwen35`, for dense Qwen3). Then `grep` the spooled script (`scontrol write batch_script <jobid> -`) to confirm both exports + `conda activate otagent`, no `$DCFT//leonardo_work` doubling. **A fast (~20s) ExitCode-1 is almost always a missing/incorrect post-patch.** Slurm snapshots the script at submit — re-submit after editing.

## 24h wall + `--max_restarts` resume
- `--max_restarts N` submits an N-deep `afterany` chain (auto-resume from latest ckpt; `save_total_limit: 1` keeps it).
- **MUTUALLY EXCLUSIVE with `--overwrite_output_dir`** (hard-errors: overwrite wipes the ckpt dir each restart). For a clean re-run, `rm -rf` the output dir first.
- Resume only helps if the job *checkpoints* — a job that TIMEOUTs in tokenization (dsfs) never saves → re-tokenizes forever. Fix dsfs first.
- **Levanter checkpoint / resume / allocator gotchas** (ghost-staging-checkpoint poison, resume-only BFC-fragmentation OOM → `cuda_async`, save-cadence-vs-MTTF) are Levanter-CODEBASE behavior → **`.agents/projects/levanter/levanter.md` §"Checkpoint & resume gotchas"**, not here. (They surfaced on `delphi_1e22` on Leonardo, but the fix is the same on any cluster Levanter runs on.)
- **sacct lies if the sbatch swallows srun's exit code.** A tail like `echo "…EXIT=$?"` makes the `.batch` step exit 0 (the echo's own success), so `sacct` reports a dead resume as `COMPLETED 0:0` even though the `.0` step is `FAILED 1:0` — naive polling reads "done" on a dead job. Fix: `srun …; rc=$?; echo …; exit $rc` (then `afterany`→`afterok` becomes usable to stop a chain on genuine failure).

## Canary-discovered blockers — apply to EVERY cell
(From `SFT_LEONARDO_INSTRUCTIONS.md §9.`)
1. HF pre-download stalls → pre-stage in detached tmux w/ retry.
2. `upath` missing in `otagent` → `pip install universal_pathlib`.
3. Launcher can't resolve REGISTERED names for pre-download → `--internet_node`.
4. Offline dataset loading → local `file_name` parquet + strip global schema tags.
5. `push_to_hub: true` crashes at repo-create offline → `false`, upload post-run.
6. **Template × tokenizer mismatch** (top silent ruin) — Llama-3-family (Delphi) → `delphi`/llama3 template, NEVER `qwen3`; `--dry_run` + eyeball the first rendered example of an instruction turn AND a `<think>` warmup example.

## Cleanup (recognition → skill §6; UPLOAD mechanics → the HF Upload section above)
- Recognition: `ls $CHECKPOINTS_DIR/<job>/ | grep -E 'safetensors|global_step'` — root `model-*.safetensors` → 8B path (also Qwen3.5-9B); `global_stepN/`+`zero_to_fp32.py` → 32B path (consolidate first via `--job_type consolidate` → upload from `final_repo/`).
- **Upload via the sbatch-tunnel (never a >100s login-node process); `hf upload`, never `upload-large-folder`** — full mechanics + cert refresh in the **HF Upload** section above.
- DB register via `manual_db_push.py` (skip for HF-only series like Delphi #6279, `enable_db_registration: false`).
- `rm -rf` exp + (32B) workdir only after upload+register succeed.
