# TU-Dresden ZIH Capella Access

**SSH**: `ssh TUDCapella` (alias in `~/.ssh/config` → `login2.capella.hpc.tu-dresden.de`).
User `befe330h`, group/acctcode `p_agents_finetuning`. ControlMaster multiplexing, **ControlPersist 8h**
— drive everything through the alias. Normally reaching ZIH needs **eduvpn** first (launch + activate
eduvpn, then ssh); when the ControlMaster socket is live no 2FA/VPN re-auth is needed.
Login nodes: `login[1-2].capella.hpc.tu-dresden.de` (also Barnard `login1.barnard...` for CPU work).
ZIH docs: <https://compendium.hpc.tu-dresden.de/>. Operating status:
<https://tu-dresden.de/zih/dienste/betriebsstatus>.

**Cluster**: ZIH **Capella** (MEGWARE): **NVIDIA H100-SXM5 94GB** (observed 95830 MiB), 4/node, 154 nodes; AMD EPYC 9334 (2×32-core, no multithreading); 768 GB RAM (12 heavy nodes: 1.5 TB); Rocky Linux 9.6, SLURM, **x86_64**.

> **⚠ Compute nodes have FULL DIRECT internet egress** (verified 2026-07-14 from a `capella` GPU node:
> `huggingface.co` 200, `app.daytona.io` 200). So — like TACC, unlike Leonardo — **NO proxychains / SSH
> tunnel / step-ca cert, NO `HF_HUB_OFFLINE`, NO login-node pre-download.** HF weights + Daytona API are
> reached directly from the job.

## Pre-launch preamble (run before launching any job)
```bash
ssh TUDCapella   # ControlMaster socket persists 8h
WS=/data/cat/ws/befe330h-otagent
module load CUDA/12.8.0
source $WS/miniconda3/etc/profile.d/conda.sh && conda activate otagent
cd $WS/OpenThoughts-Agent && git pull && git submodule update --init --remote sft/llamafactory
cd $WS/harbor && git pull
cd $WS/MarinSkyRL && git pull
source ~/secrets.env
source $WS/OpenThoughts-Agent/hpc/dotenv/zih_capella.env
cd $WS/OpenThoughts-Agent
```
> Only `git stash` for divergent tracked changes; cluster rule: edit locally → push → pull.

## Key paths (workspace = the `cat` Lustre FS)
- **Workspace root (`$SCRATCH`)**: `/data/cat/ws/befe330h-otagent`
  > **⚠ PATH CHANGED 2026-07.** The prior workspace was `/data/cat/ws/befe330h-befe330h-otagent`
  > (double `befe330h-`); the current `ws_allocate` naming produces `/data/cat/ws/befe330h-otagent`
  > (single). The old dotenv/notes path is dead. `zih_capella.env` was updated to the new path.
- Code (`$DCFT`/`$DC_AGENT`): `$SCRATCH/OpenThoughts-Agent` (`penfever/working`)
- Harbor: `$SCRATCH/harbor` (`main`; migrate a stale clone: `git checkout main && git pull` on next cluster touch)
- MarinSkyRL: `$SCRATCH/MarinSkyRL` (`penfever/working`)
- Conda (`$DCFT_CONDA`): `$SCRATCH/miniconda3` (env `otagent`)
- Secrets (`$DC_AGENT_SECRET_ENV`): `~/secrets.env` (in /home; 52-line local secrets synced over)
- HF cache (`$HF_HUB_CACHE`/`$HF_HOME`): `$SCRATCH/huggingface/hub`
- pip cache: `$SCRATCH/.cache/pip`; XDG cache: `$SCRATCH/.cache/xdg` (both set by the dotenv, OFF /home)
- Checkpoints (`$CHECKPOINTS_DIR`): `$SCRATCH/checkpoints`
- Data / slow workspace: `/data/horse/ws/befe330h-dcagent` (`horse` = slow; big/cold data only)

> **⚠ WRITE-PATH + QUOTA MANDATE.** `/home` = **50 GB/user** (permanent, NFS4) — SOURCE CODE + CONFIG
> ONLY. ALL large/persistent writes AND all caches (conda pkgs+envs, HF, pip, XDG, TMPDIR, checkpoints,
> eval jobs) go to the **workspace** (`$SCRATCH` on `cat`). The `zih_capella.env` dotenv +
> `miniconda3/.condarc` (pkgs_dirs/envs_dirs in the workspace) enforce this. If /home fills at 50 GB,
> conda/pip/HF all break. Project quota on `horse` ≈ 7.68 TB / 30,733 files (`p_agents_finetuning`).

## ⚠ Lustre metadata ban (SHARED FS — admins flag violations)
**NEVER run `find`, `du`, `df`, `locate`, `ls -l`, `ls --color`, or `ls -R` on `/data/*`** (`cat`,
`horse`, `walrus`). These are metadata storms that degrade the FS for all users. Use instead:
- plain `ls <path>` / `ls -l <specific-file>` (a single named file is fine)
- `lfs df` (not `df`), `lfs quota -p <projid> /data/<fs>`
- `lfs find <root> [--maxdepth N] [--name '<glob>'] [--type f] [--mtime +30]` (not `find`)
This is the ZIH analog of Leonardo's GPFS no-find/du ban. Locate job logs via `scontrol show job <id> -o`
`StdOut=` + a depth-1 plain `ls`, never a recursive walk.

## Workspaces (ws_* tools)
```bash
ws_list                       # active workspaces (all FS)
ws_list -F cat -v             # cat FS, verbose (id, dir, remaining time, extensions, acctcode)
ws_list -R                    # sorted by remaining time
ws_find <name>                # resolve a workspace dir by name
ws_allocate -F cat -r 7 -m bf996@nyu.edu -n otagent -d 30    # 30-day cat workspace, reminder 7d, email
ws_extend  -F cat befe330h-otagent 30                        # extend (max 30d; 2 extensions total)
```
- **`cat`** = the faster workspace FS (use for the conda env + code + hot data). **`horse`** = slow
  ("slow as F" per the operator) — cold/bulk data only. **`walrus`** also exists.
- **30-day ttl, 2 extensions.** A workspace that expires is **PURGED** (the prior `cat/otagent` expired +
  everything on it — conda env, repos — was deleted; the 2026-07-14 rebuild re-created it). Watch
  `ws_list -F cat -v` remaining time; `ws_extend` before it lapses.
- **Cross-FS copy**: `dtcp -r <src> <dst>` (datatransfer copy), `dtmv` (move) — use the `dt*` wrappers for
  large `cat`↔`horse`↔`walrus` transfers, not plain `cp`/`rsync` on Lustre.

## Scheduler (SLURM)
- **Partition `capella`**: 154 nodes, `--gres=gpu:4` (UNTYPED) for a whole node (`sinfo` reports the gres
  as `gpu:h100:4(S:0-1)`, but the submit `cli_filter` requires the untyped form — see the ⚠ below), 773 GB+
  RAM/node, infinite `sinfo` timelimit but ZIH enforces a **7-day** job max.
  Slurm caps requestable CPUs at **56** (of 64). `capella-interactive` (c1/c2): 12h cap.
- **Whole node**: `--nodes=1 --gres=gpu:4 --cpus-per-task=56 --exclusive`.
- **1 GPU**: `--gres=gpu:1 --cpus-per-task=14` (14 cores/GPU is the natural ratio).
  > **⚠ Use `--gres=gpu:N` (untyped), NOT `--gres=gpu:h100:N`, in `#SBATCH` lines.** The Capella lua
  > `cli_filter` REJECTS the typed form at submit with *"This is a GPU cluster, only GPU jobs are
  > allowed."* (`sinfo` reports the gres as `gpu:h100:4`, but the submit filter wants the untyped
  > `gpu:N`). `srun --gres=gpu:1` and `sbatch --gres=gpu:1` both work; `gpu:h100:1` fails.
- **Memory**: default 300 MB/CPU (low!) — request explicitly (`--mem=<MB>` or `--mem-per-gpu=<MB>`);
  Slurm routes to the 752 GB standard or 1.5 TB heavy nodes by the memory ask.
- **Interactive** (srun blocks → launches an interactive job):
  ```bash
  srun --partition=capella --nodes=1 --ntasks=1 --cpus-per-task=56 --gres=gpu:4 --time=12:00:00 --exclusive --pty bash -l
  srun --partition=capella --nodes=1 --ntasks=1 --cpus-per-task=14 --gres=gpu:1 --time=12:00:00 --pty bash -l
  ```
- **Batch**: standard `sbatch <script>`; watch `squeue -u befe330h`. Best practice: short jobs (ZIH
  restricts long-running-job core share); use `afterany` chain jobs for long work.
- **Login-node 600 s CPU limit** — any process >600 s CPU on a login node is killed. No productive runs /
  heavy compiles on login. (I/O-bound `uv` installs ran fine detached during the rebuild; a from-source
  vLLM compile MUST go to a compute node.)

## Module system (Lmod)
```bash
module load CUDA/12.8.0      # our target (matches cu128 torch wheels); also 12.1.1/12.6.0/13.0.0(D)
module avail CUDA            # cuDNN/9.10.1.4-CUDA-12.8.0, cuSPARSELt, cuTENSOR also present
module load GCC/13.2.0       # or 13.3.0 — for any from-source build (Hopper sm_90)
```

## Codebase + conda-env + dotenv layout (the standard pattern, mirrors TACC/Leonardo)
- **Repos** (all in the workspace): `OpenThoughts-Agent` (`penfever/working`), `harbor` (`main`; migrate a stale clone on next touch), `MarinSkyRL` (`penfever/working`).
  Sync discipline: commit on the Mac (`/Users/benjaminfeuer/Documents/...`) → push → `git pull` on the
  cluster (the Python repos are editable installs — live after pull). NO divergent/untracked changes on
  the cluster. SFT also needs `git submodule update --init --remote sft/llamafactory`.
- **Conda env `otagent`** = the single default runtime (orch / eval / datagen / agentic / SFT / RL +
  standard serving). Built with prebuilt x86_64 wheels — see `ENVIRONMENT_MAP.md` §2a. The zih.md legacy
  `envs/rl/bin/activate` vs `conda activate otagent` ambiguity resolves to **`conda activate otagent`**
  (matches TACC/Leonardo; RL runs in `otagent` unless a pinned SkyRL graph forces a uv venv).
- **dotenv** `hpc/dotenv/zih_capella.env` — sets `$SCRATCH` (workspace root), `$DCFT`/`$DC_AGENT`,
  `$DCFT_CONDA`, `$DCFT_ACTIVATE_ENV`, HF/pip/XDG caches into the workspace, `$DC_AGENT_SECRET_ENV=~/secrets.env`,
  WANDB, `$CHECKPOINTS_DIR`, `$SKYRL_HOME`. **Sourced after `~/secrets.env`** in the preamble.

## Secrets
`~/secrets.env` (in /home) is the 52-line local secrets env (`/Users/benjaminfeuer/Documents/secrets.env`)
synced over via `rsync -av /Users/benjaminfeuer/Documents/secrets.env TUDCapella:~/secrets.env`. Carries
`HF_TOKEN`, `WANDB_API_KEY`, `DAYTONA_API_KEY`/`DAYTONA_DATA_API_KEY`/`DAYTONA_RL_API_KEY`, `SUPABASE_URL`/
`SUPABASE_ANON_KEY`/`SUPABASE_SERVICE_ROLE_KEY`, `OPENAI_API_KEY`, `LAION_*`, `COREWEAVE_TOKEN`,
`PINGGY_API_KEY`, etc. Referenced by name from skills; never print values.

## Eval on Capella
Capella mirrors the **TACC** eval path (direct egress, single `otagent` env serving vLLM on the compute
node, orchestrator → localhost:8000, Daytona sandbox for terminal commands — no served-model tunnel
needed). A full `eval/clusters/zih.yaml` + `eval/zih/eval_harbor.sbatch` (adapt from `eval/clusters/tacc.yaml`
+ `eval/tacc/eval_harbor.sbatch`, but with `gpu_gres: true` + the UNTYPED `--gres=gpu:N` (Capella
gres-tracks GPUs, but its cli_filter rejects the typed `gpu:h100:N` — see §Scheduler ⚠),
`slurm_partition: capella`, `arch: x86_64`) is the production path — **not yet committed**
(the 2026-07-14 bring-up ran a lightweight self-contained smoke instead; see `eval/zih/eval_smoke.sbatch`).
For the standard/math eval path, add an `evalchemy` clone + env per Leonardo (`evalchemy-marin`).

## Gotchas
- **Workspace expiry = data loss.** `ws_extend` before the 30-day ttl lapses, or lose the env + repos.
- **New workspace naming** (`befe330h-otagent`, not the old double `befe330h-befe330h-otagent`) — update
  any hardcoded path.
- **`ws_list` needs `/usr/bin/ws_list`** on PATH (works in a plain SSH shell); it returns EMPTY (exit 0)
  when you have no active workspaces — that's "none", not an error.
- **conda 26.x needs an explicit channel** — the workspace `.condarc` sets `channels: [conda-forge]`
  (a bare `conda create` otherwise fails `NoChannelsConfiguredError`).
- **`pkill -f` over SSH can exit 255** (kills a proc the multiplexed session references) even when it
  worked — verify with a follow-up `pgrep`, don't trust the exit code.
- **`hfco_resolve` (xet CDN `cas-bridge.xethub.hf.co`) returns 403 to a bare GET** — that's reachable +
  path/auth-gated, NOT an egress failure.
