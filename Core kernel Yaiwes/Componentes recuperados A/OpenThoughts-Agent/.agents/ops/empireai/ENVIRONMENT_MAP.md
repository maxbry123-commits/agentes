# EmpireAI Beta runtime / environment map

Canonical **`mega_final_dm.sqsh`** (`mega_final.sqsh` + `densemixer==1.0.1`; §1) carries isolated SFT/axolotl, RL, and JAX layers for EmpireAI Beta (GB200 NVL72, aarch64). Access, SLURM, and filesystem facts: `.agents/ops/empireai/ops.md`.

Last verified: **2026-07-17** (built + gate-probed live on the GB200).

---

## 0. TL;DR — the discriminator = which python

> - **`/usr/bin/python` (system)** → **SFT/axolotl** layer → torch **2.8.0a0+nv25.06 / CUDA 12.9** (the NGC base torch; Blackwell sm_100).
> - **`/opt/envs/rl/bin/python`** → **RL** layer → torch **2.11.0+cu128** (sm_100) + the from-source vLLM fork + flash-attn 2.8.3 + skyrl_train/torchtitan/ray/harbor.
> - **`/opt/envs/jax/bin/python`** → **JAX** layer → **jax[cuda13]==0.10.1** (sm_100) + marin-levanter.
>
> Layers are isolated: SFT uses base Python, RL/JAX non-inheriting uv venvs. `--container-mount-home` leaks host pyenv, so sanitize PATH first (§4).

---

## 1. Image lineage (all in `~/images` = `/mnt/home/bf996/images`, VAST)

| Image | Size | = prior + | Layer added |
|---|---|---|---|
| `pytorch-25.06-py3.sqsh` | 24.4 GB | — (NGC base) | `nvcr.io/nvidia/pytorch:25.06-py3` arm64/sbsa, torch 2.8.0a0+nv25.06, CUDA 12.9, Blackwell-optimized (sm_100). Anonymous enroot import (NO NGC key needed). |
| `mega_v1_sft.sqsh` | 24 GB | base | SFT/axolotl into the **base system python** |
| `mega_v2_rl.sqsh` | 58 GB | v1 | RL env `/opt/envs/rl` |
| `mega_final.sqsh` | 67 GB | v2 | JAX env `/opt/envs/jax` — the 3-layer base (SFT+RL+JAX); **superseded as the run image by `mega_final_dm`** |
| **`mega_final_dm.sqsh`** | **67 GB** | final | **+ `densemixer==1.0.1`** (`pip install --no-deps` into the base system python) for the DenseMixer axolotl SFT plugin — **THE current image; use this**. Built via job `31630` (gate green: `densemixer 1.0.1 | apply_qwen3_moe_patch import OK`). densemixer is INERT unless the `DenseMixerPlugin` is enabled in the axolotl config, so this is a strict superset — safe for RL/JAX runs too. |

- **Build recipe (per layer = one self-contained sbatch; scripts in `~/scripts/mega_{A,B,C}_*.sbatch`):** enroot `--rw` sandbox on node-local `/tmp` — `enroot create --name <sb> <prior.sqsh>` → `enroot start --root --rw <sb> bash -lc 'bash /root/setup.sh'` → `enroot export -o ~/images/<next>.sqsh <sb>`. **enroot = 4.0.1.** Set `ENROOT_{CACHE,DATA,TEMP,RUNTIME}_PATH=/tmp/$USER/enroot-*` before create. Sandbox unpack+build on `/tmp` (node-local `/`, ~1.6 TB free); export the `.sqsh` to HOME.
- Heavy builds are `sbatch`-detached and hold 1 B200 (`--gres=gpu:b200:1`, `qos=standard`) for CPU-bound install/compile; only `beta` GPU partition exists.

## 2. Container run invocation (Pyxis/Enroot)

```bash
srun --partition=beta --account=ny_chinmayh_datacomp --qos=<test|interactive|standard> \
     --gres=gpu:b200:N \
     --container-image=/mnt/home/bf996/images/mega_final_dm.sqsh --container-mount-home \
     bash -lc '<cmd>'
```
- **⚠ PATH-sanitize gotcha (load-bearing for EVERY container job):** `--container-mount-home` puts the host `~/.pyenv` shims on PATH → a bare `python` runs the HOST pyenv interpreter ("Exec format error"/wrong python). **Inside the container sanitize first:** `export PATH=/usr/local/bin:/usr/local/cuda/bin:/usr/bin:/bin; hash -r; unset PYENV_ROOT PYENV_VERSION PYENV_SHELL`. Container system python = `/usr/bin/python` (3.12.3).
- **⚠ NGC-baked `PIP_CONSTRAINT` gotcha:** the NGC base sets `PIP_CONSTRAINT` → `torch==2.8.0a0…` (pins torch to the base build). It silently blocks any `pip install/download` of a different torch (e.g. building a fresh venv). **Clear it** (`unset PIP_CONSTRAINT; export PIP_CONSTRAINT=`) before installing into a non-base venv.

---

## 3. The env layers in detail

### 3a. SFT / axolotl — the **base system python** (`/usr/bin/python`), NOT a venv
- **Versions:** torch **2.8.0a0+nv25.06 / cu12.9**, axolotl **0.17.0.dev0** (`marin-community/axolotl @ 8bd0a508`, branch `feuer/lockfree-prepared-sentinel`), transformers 5.12.1, torchao 0.17.0, deepspeed 0.18.9, triton 3.3.0 (via NGC `pytorch-triton`).
- **WHY system python, not a venv:** uv's resolver does NOT count a `--system-site-packages` venv's inherited packages as installed, so the exact-version torch override (`torch==2.8.0a0+…nv25.06`, a local version absent from any index) sent uv hunting an index → resolution abort. **Fix: install into the base env** (`uv pip install --python /usr/bin/python --break-system-packages --override /tmp/ovr.txt -e /opt/axolotl`) → uv SEES the NGC torch installed → the override merely RELAXES axolotl's declared `torch>=2.9.1` floor onto 2.8.0a0 (torch never re-fetched). Override set pins torch/torchvision/triton/numpy to the installed versions.
- **⚠ triton dist-name alias (load-bearing):** the NGC base ships triton as the distribution **`pytorch-triton` (3.3.0+git…nvinternal)** which PROVIDES the importable `triton` module — there is NO dist literally named `triton`. So axolotl's `triton>=3.4.0` (+liger's) made uv hunt PyPI for a `triton` dist → PyPI triton has NO aarch64 wheel → abort. **Fix:** register a metadata-only `triton-3.3.0.dist-info` ALIAS (Name: triton, Version = the module's 3.3.0) in the triton dist-packages dir → uv sees `triton` installed; the `triton==3.3.0` override then satisfies every triton req from the present module → nothing fetched, NGC pytorch-triton preserved. Metadata-only (no RECORD) so a stray uninstall can't delete real triton files.
- **aarch64 dep gotchas:** torchao via `--no-deps` (pyproject excludes it on aarch64 but `qat.py` imports it unconditionally); deepspeed via `--no-build-isolation` (builds vs the base torch). **aarch64 uses SDPA — flash-attn NOT required for axolotl SFT** (`flash_attention: false` in configs).

### 3b. RL — `/opt/envs/rl` (fresh non-inheriting uv venv)
- **Versions:** torch **2.11.0+cu128** (arch list `sm_80/sm_90/sm_100/sm_120`), vLLM fork `0.1.dev16611+g76259c63a` (= `mlfoundations/vllm @ 76259c63`, built from source), flash-attn **2.8.3** (`flash_attn_2_cuda` compiled for sm_100), skyrl_train, torchtitan (EP), ray **2.51.1**, harbor **0.8.1**, transformers **5.8.1**.
- **Recipe:** `uv sync --frozen --extra vllm --extra ep` from **skyrl-train's `uv.lock` @ MarinSkyRL `ded7a2f1`** (the cu128 lock; universal/aarch64 — carries aarch64 wheels for torch 2.11+cu128, stock vllm 0.20.2, ray, nccl-cu12, flashinfer-jit-cache, torchvision; megatron/TE are x86_64-marker-gated → skipped). Then **`--no-deps` swap** the two from-source wheels (vLLM fork + flash-attn 2.8.3, both `pip wheel` in a throwaway torch-2.11-cu128 venv with `use_existing_torch.py` + `sed cutlass-dsl[cu13]→cu128`), then `harbor[daytona]` from git @`22d75039`. This reproduces the canonical gpu-rl fsdp2 image (`MarinSkyRL docker/Dockerfile.gpu-rl`), adapted linux/amd64+`8.0;9.0` → **aarch64 + `TORCH_CUDA_ARCH_LIST=10.0`**.
- **⚠ cu128, NOT cu130:** canonical `penfever/working` uses torch 2.11.0+**cu130**, but the NGC 25.06 base's nvcc is **CUDA 12.9** — it compiles sm_100 for cu12.8 extensions but CANNOT build cu130 from source. cu128 is the only feasible from-source path on this base (and the torch-2.11-cu128 aarch64 wheel carries native sm_100 SASS — verified with `cuobjdump --list-elf libtorch_cuda.so`). The vLLM fork requires torch 2.11 (its `_C_stable_libtorch` extension uses the `TORCH_BOX` macro absent from 2.9/2.10) → this venv must NOT inherit the base torch 2.8.
- **Note:** the vLLM fork wheel was built for plain `10.0` (not `10.0a`) — sufficient for `import vllm`; some cutlass fp8/MoE kernels may want `10.0a` for full engine throughput (revisit if a served-engine kernel is missing).

### 3c. JAX / marin-levanter — `/opt/envs/jax` (fresh non-inheriting uv venv)
- **Versions:** **jax[cuda13]==0.10.1** (device `NVIDIA GB200`, `compute_capability 10.0`), marin-levanter **0.2.50.dev202607170746** (py3-none-any, `uv_build` — no Rust), jax-triton 0.3.1, triton 3.7.1, nvidia-cutlass-dsl 4.6.0.
- **cuda13 (not cu12):** matches levanter's `[gpu]` extra (`jax[cuda13]==0.10.1`, B200-aware) AND the Beta driver is CUDA-13 native (§5) — no forward-compat. jax[cuda13] brings its OWN cu13 nvidia libs → does NOT clash with the RL venv's cu128 torch (separate venv). Probe confirmed both cuda13 and cuda12 init on the GB200; cuda13 chosen.
- **⚠ `flash-attn-4[cu13]` is ABSENT** — levanter's `[gpu]` extra pins `flash-attn-4>=4.0.0b16` (beta) which has **no aarch64 pre-release wheel**. Installed best-effort/non-fatal → levanter falls back to XLA/cuDNN attention (jax-triton/cutlass/triton DID land). Revisit when an aarch64 FA4 wheel ships.

---

## 4. PATH / env preamble (copy for any in-container command)
```bash
export PATH=/usr/local/bin:/usr/local/cuda/bin:/usr/bin:/bin; hash -r
unset PYENV_ROOT PYENV_VERSION PYENV_SHELL || true
unset PIP_CONSTRAINT || true    # NGC base pins torch 2.8 via PIP_CONSTRAINT
# then: /usr/bin/python (SFT) | /opt/envs/rl/bin/python (RL) | /opt/envs/jax/bin/python (JAX)
```

## 5. Hardware / driver
- **GB200** (Grace-Blackwell, NVL72 SuperPOD), **cc 10.0 (sm_100)**, **~189 GB HBM**/GPU. 72 DGX × 4 B200 = 288; 144 aarch64 Grace cores + ~1.5 TB RAM per node.
- **Driver `580.126.16` / CUDA `13.0` native** (so cu13 jax runs without forward-compat; cu128 torch runs fine under it too).
- `--gres=gpu:b200:N` (GPUs ARE SLURM gres). `--segment {1,2,4,8,16}` controls multi-node NVLink placement locality — **`--segment=2` validated for a 2-node job**.
- Native Blackwell kernels CONFIRMED both stacks: torch cu128 arch list has `sm_100`; jax cuda13 device `compute_capability 10.0` + bf16 matmul.

## 6. Multi-node launch (axolotl SFT, validated Stage-3 pattern)
torchrun static rendezvous under Pyxis (SFT layer = system python):
```bash
# batch shell: head node for rendezvous (full path — Bright module gotcha)
SCONTROL=$(command -v scontrol || echo /cm/local/apps/slurm/current/bin/scontrol)
nodes=($($SCONTROL show hostnames "$SLURM_JOB_NODELIST")); export MASTER_ADDR="${nodes[0]}" MASTER_PORT=29500
srun --nodes=2 --ntasks-per-node=1 --gres=gpu:b200:4 \
     --container-image=/mnt/home/bf996/images/mega_final_dm.sqsh --container-mount-home \
     bash -lc '<sanitize PATH>; export NCCL_DEBUG=INFO; \
       export NCCL_SOCKET_IFNAME=bond0 GLOO_SOCKET_IFNAME=bond0 NCCL_SOCKET_FAMILY=AF_INET; \
       /usr/bin/python -m torch.distributed.run --nnodes=2 --nproc_per_node=4 \
         --node_rank=$SLURM_PROCID --master_addr=$MASTER_ADDR --master_port=$MASTER_PORT \
         -m axolotl.cli.train <cfg.yaml>'
```
- **⚠ NCCL bootstrap interface — pin `bond0` (LOAD-BEARING, validated job 31604).** NCCL auto-picks a `100.126.x` IPoIB address for its control-plane bootstrap, but that `100.126.0.0/16` net is served by **four ambiguous `ib*` routes** per node and is **NOT routable node-to-node** → `socketStartConnect … No route to host` → bootstrap hangs to the wall (killed the first Stage-3 attempts 31572/31584/31589). The **routable inter-node iface is `bond0` (10.10.10.0/25)** — the default route + what each node's hostname resolves to (`getent hosts <host>` → `10.10.10.x`), so `MASTER_ADDR=<hostname>` is already correct. **Fix: `export NCCL_SOCKET_IFNAME=bond0 GLOO_SOCKET_IFNAME=bond0 NCCL_SOCKET_FAMILY=AF_INET`** — bootstrap/rendezvous over the routable ethernet; **IB + MNNVL still carry the data plane**.
- **MNNVL is the intended, supported NVL72 path — keep it ENABLED** (do NOT set `NCCL_MNNVL_ENABLE=0`). The earlier `Cuda failure 801 'operation not supported'` (job 31572) was a *downstream symptom of the bootstrap picking a bad interface on that node-pair*, not a fabric/IMEX block: the host fabric is healthy (`nvidia-smi -q` → `Fabric State: Completed, Success`) and the IMEX channels are injected into the container. With the `bond0` bootstrap fix, a 2-node all-reduce runs clean over MNNVL (no 801, no route-loop) — 31604. IB-fallback (`NCCL_MNNVL_ENABLE=0`) is NOT needed and would forfeit NVL72 bandwidth.
- **One container task per node** (`--ntasks-per-node=1`); torchrun spawns the 4 local ranks inside. Pyxis passes the SLURM task env (incl. `MASTER_ADDR`/`SLURM_PROCID` + exported batch vars) into the container by default. `NCCL_DEBUG=INFO` to confirm the NVL/IB transport. OT-Agent's default axolotl launcher is `torchrun -m axolotl.cli.train <cfg>` (`hpc/sft_launch_utils.py`).

## 7. Access / SLURM / storage (brief — full facts in `ops.md`)
- **`ssh EmpireAI_Beta`** (2FA; operator warms the ControlMaster socket, **reaped within minutes** → all heavy work `sbatch`-detached; ride the socket non-interactively). **`bash -lc` wraps EVERY remote cmd** or SLURM/Pyxis are invisible (Bright module env). SLURM **25.05.6**; binaries `/cm/local/apps/slurm/current/bin`.
- User **`bf996`**, **`--account=ny_chinmayh_datacomp`** (SU charging live). QoS: `test` (0.5×, ≤4 GPU/6h), `interactive`, `standard` (≤36 GPU/48h, production default), `long`, `priority`.
- **HOME `/mnt/home/bf996`** (VAST) = primary storage: `~/images` (`.sqsh`), `~/scripts`, `~/logs`, `~/hf_cache`. `/tmp` = node-local scratch (enroot sandbox + build unpack). Only the `beta` GPU partition exists (no CPU-only path).
