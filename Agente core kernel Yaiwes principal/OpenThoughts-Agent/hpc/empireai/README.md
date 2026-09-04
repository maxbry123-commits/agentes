# Empire AI **Beta** (B200 NVL72) — containerized training bring-up

aarch64 (Grace) + Blackwell **B200 sm_100**, **Pyxis/Enroot mandatory**. This dir holds the
reusable container build defs + smoke templates for the three bring-up phases.
Read `.agents/ops/empireai/ops.md` first (access model, module gotcha, storage, hardware).

> ⚠️ **STATUS (2026-07-02): cluster execution is BLOCKED on SLURM account provisioning.**
> As of 2026-07-01 SU charging went live and `AccountingStorageEnforce = associations,limits,qos,safe`.
> User `bf996` has **NO account association** (empty `sacctmgr show assoc user=bf996`, empty `sshare`,
> not present in the accounting DB). Every `srun`/`sbatch` — even bare, even with an allowed account
> like `-A nyu` / `-A nyu_beta_test` / `-A ny_chinmayh_datacomp` — fails with
> `Invalid account or account/partition combination specified`. The `beta` partition *allows* those
> accounts, but the **user must be associated** with one, and bf996 is not.
> **ACTION REQUIRED (operator/admin, Flatiron support ticket):** add `bf996` to an account association
> on beta — candidates seen in `beta` AllowAccounts: `nyu_beta_test` (validation), `ny_chinmayh_datacomp`
> (DataComp / Chinmay Hegde, NYU — most likely relevant), or `nyu`. Until then, Phases 0/1/2 cannot run.
>
> The templates below are therefore **authored + arch-validated offline but NOT yet cluster-validated.**

## How to reach beta
- Ride the operator's ControlMaster socket, non-interactively, ALWAYS in a login shell:
  `ssh -o BatchMode=yes EmpireAI_Beta "bash -lc '<cmd>'"` (a plain ssh does NOT load modules →
  `sinfo`/`srun`/Pyxis come back empty). If the socket is dead, the operator must reconnect
  `ssh EmpireAI_Beta` in a real terminal (2FA).
- Confirmed live: `beta*` partition, 64/72 nodes idle, `Gres=gpu:b200:4`, SLURM 25.05.6,
  enroot at `/usr/bin/enroot` (compute nodes only — bare enroot on login FAILS).

## Storage (interim — real allocation still needed)
- HOME `/mnt/home/bf996` = 100 GB Vast quota (code/configs/one .sqsh, too small for models).
- `/ddn` = 11 PB Lustre; **no per-user/group dir yet** — only `/ddn/client_validation` (world-writable,
  scratch, may be wiped) and root-owned `/ddn/lustre`. **No `find`/`du` on Lustre.**
- `/tmp` = 11 TB node-local (ephemeral). Put the `.sqsh` image(s) in HOME or a self-made dir under
  `/ddn/client_validation`; checkpoints on `/tmp` or `/ddn/client_validation`.
- **File a support ticket for a real `/ddn/<group>/<user>` allocation before any large run.**

## Account / QoS (once associated)
- Pass `-A <account>` on every submit (now mandatory). QoS: `test` (≤4 GPU/6h sandbox),
  `interactive` (2h), `standard` (production ≤36 GPU/48h), `long` (backfill ≤7d), `priority` (2×/24h).
- Set `export EMPIREAI_ACCT=<account>` and the scripts pick it up.

## Files
| File | Phase | What |
|---|---|---|
| `phase0_smoke.sh` | 0 | Pyxis/Enroot + GPU-injection + Blackwell-torch validation (NGC pytorch 26.06-py3 arm64). |
| `enroot_import.sh` | all | Import a docker/NGC image → persistent `.sqsh` (run on a compute node via srun). |
| `Dockerfile.axolotl-aarch64` | 1 | Axolotl on NGC pytorch arm64 + CUDA≥12.8 base. |
| `sft_axolotl_smoke.sbatch` | 1 | Tiny SFT smoke (Qwen2.5-0.5B, few steps, checkpoint). |
| `Dockerfile.marin-aarch64` | 2 | Marin/Levanter `jax[cuda13]` (JAX 0.9.2, CUDA 13) for B200. |
| `marin_moe_smoke.sbatch` | 2 | Tiny initialized-MoE (grug/nano_moe) pretrain smoke. |

## Image choice (arch-validated offline)
- **NGC `nvcr.io/nvidia/pytorch:26.06-py3`** — confirmed multi-arch (`linux/amd64`, **`linux/arm64`**)
  via the nvcr registry manifest list; public (no NGC key needed). Latest tag as of 2026-07-02.
  CUDA ≥12.8 / recent torch → Blackwell sm_100 capable. (Fallbacks: `26.04-py3`, `25.12-py3` — also arm64.)

## Phase 2 (Marin MoE) — how the Marin team does it (from the marin GitHub, via mumwelt)
- **Framework = Levanter (JAX).** MoE support = the **"grug" MoE** backend (issue #929, Levanter PR #958;
  expert-parallel backends + DeepEP dispatch #5982). Launch = the marin experiment `launch.py`
  (`experiments/grug/moe/…`, `experiments/grug/nano_moe/launch.py`) via the Ray/executor, or directly
  `python -m levanter.main.train_lm --config <moe.yaml>`.
- **Normally run on TPU** (v4-8/v4-32/v5p via Ray/Iris — e.g. nano_moe baseline hidden=512, 16 experts
  top-2, Muon optimizer + aux-loss-free bias, issue #3466). A **GPU path exists** (CoreWeave H100, #5509).
- **Blackwell/B200 crux = JAX runtime:** Marin's `gpu` extra was `jax[cuda12]==0.9.2`; it was moved to
  **CUDA 13 / `jax[cuda13]` (JAX 0.9.2)** specifically to support B200 (issue **#5427** / PR **#5428**,
  earlier opt-in PR #5425). GPU jobs also need the **CUDA toolchain staged** (ptxas/nvlink; PR **#6637**)
  and **FA4 CuTe/THD** deps (PR **#6237**). Smoke guidance: PR **#5431** (CoreWeave GPU sharp edges +
  tiny JAX smoke + H100/GH200/B200 config mapping). Marin uses Ray+uv venvs / Docker (not Pyxis) —
  so the beta path is: bake `jax[cuda13]`+levanter into an aarch64 container and run `levanter.main.train_lm`.
