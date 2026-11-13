# Axolotl — dependency overview

The SFT trainer used **only** for the Sera + CoderForge baseline reproductions. Everything else uses
LLaMA-Factory. Axolotl is deployed when the upstream paper's wire format requires it (Sera's OpenAI-native
`messages` with `tool_calls`+`train` fields; CoderForge's pre-tokenized `input_ids`/`labels`). Written
2026-06-14 from `notes/axolotl.md` + `baselines/`.

- **Version:** axolotl **v0.16.1**, in the **`sera-axolotl`** conda env (torch 2.9.1+cu130, Jupiter GH200 aarch64). Canonical install `/e/scratch/jureap59/feuer1/code/axolotl/`.
- **Configs:** `baselines/sera/configs/template_qwen3_8b_sera_v4.yaml`, `baselines/coderforge/configs/template_qwen3_8b_cf_v3.yaml` (templated with `__SIZE__`/`__NODES__` via `sed` before submit).
- **Launch (Sera/CoderForge baselines):** SLURM sbatch (`baselines/{sera,coderforge}/sbatch/axolotl_*.sbatch`), multi-node `srun + accelerate launch`, default **4 nodes** (16 GH200) + `zero3_bf16.json`, `booster`/`--account reformo`. Compute has no internet → run `axolotl preprocess` on the login node per size first to populate the offline HF cache.

---

## As of 2026-07: axolotl is a first-class SFT backend in `hpc.launch` (`--sft_backend axolotl`)

Merged to `penfever/working` (merge `02d676d0`, 2026-07-02) behind `--sft_backend {llamafactory,axolotl}`
(LF default; flag-off byte-identical). This is SEPARATE from the Sera/CoderForge sbatch path above.
- **Submodule** `sft/axolotl` @ `3c206072` = marin-community/axolotl `feuer/marin-fork-3feature-port` (axolotl
  **0.17.0.dev0**), carrying `delphi.jinja` + the `template_integrity` / `mfu` / `supabase_registry` plugins.
- **Wiring:** `hpc/sft_launch_utils.py` (`_train_entrypoint_args` → `-m axolotl.cli.train`; `_setup_environment`),
  `hpc/axolotl_config_utils.py` (LF-exp-args → axolotl-YAML translator + `_build_datasets`), configs under
  `sft/axolotl_configs/`, gate scripts under `sft/axolotl_gates/`.
- **Validated on TACC Vista (GH200 aarch64), `sft-axolotl` conda env** (torch 2.11.0+cu128, transformers 5.12.1,
  torchao 0.17.0): Stage 3 smoke GO, Stage 4 footgun-through-launcher GO (delphi chat_template byte-identical
  to canonical `delphi.jinja` across output + checkpoint dirs). **Delphi masking canary PASS** (job 802053,
  `sft/axolotl_configs/delphi_canary.yaml`): the `delphi` chat_template masks correctly — `<|start_think|>…
  <|end_think|>` reasoning + assistant answer TRAINED, user/system MASKED, Llama-3 turn structure segmented,
  **0 "Last turn is not trainable" skips** (verified via `axolotl.cli.preprocess --debug`; trainable fraction
  73–96%). So jinja-as-ground-truth (train==serve) holds for the real delphi path. (Stage 6 LF-vs-axolotl
  loss-match was NO-GO on guanaco/llama3, but that gap was a framework turn-masking divergence on a
  NON-canonical dataset — the delphi canary is the check that matters, and it passes.)
- **Launcher gotcha:** `hpc.launch` does NOT honor a config's hand-authored `datasets:` block — `_build_datasets`
  REBUILDS it from `--dataset` + `--messages/--role_tag/--content_tag` (defaults to sharegpt conversations/
  from/value). Pass those flags at launch; the in-config `datasets:` block is honored ONLY by direct
  `axolotl.cli.preprocess`. (aarch64: SDPA; TACC internet_node → `WANDB_MODE=disabled`; a stale `HF_TOKEN` in
  TACC `~/.bashrc` breaks `axolotl preprocess`'s `whoami` → `unset HF_TOKEN` or refresh.)
- **Bonus:** the LF parity baseline surfaced + fixed 4 latent LLaMA-Factory transformers-5.x bugs (LF fork pin
  `d20b8666`: `add_special_tokens` kwarg guard; launcher: short TMPDIR AF_UNIX fix, `report_to=none` on
  no-internet, `expandable_segments` — the last two now apply to BOTH backends).

---

## Load-bearing gotchas

1. **Post-train tokenizer/chat-template restoration (the 0%-SWE-bench bug).** Axolotl saves a stripped `tokenizer_config.json` + a bare 4-line `chat_template.jinja` that **don't handle `tool_calls` / `role: tool`** at serve time → vLLM silently drops every `tool_calls` field → the model is OOD at inference (training was healthy) → **0% on SWE-bench.** **Fix:** after training, overwrite the four tokenizer files (`tokenizer_config.json`, `tokenizer.json`, `vocab.json`, `merges.txt`) with the **stock base-model** versions AND delete `chat_template.jinja` from the HF repo (Ai2's released SERA-8B is byte-identical to stock Qwen3-8B tokenizer — mirror that). Script in `baselines/sera/README.md` §Post-training. (This is why the `feedback_axolotl_restore_tokenizer` memory existed.)
2. **DeepSpeed = `zero3_bf16.json` (currently NO CPU offload) — but CPU-offload is NOT impossible on aarch64 (myth corrected 2026-07-09).** The current config keeps Adam on GPU and shards params/grads/moments; `zero1.json` OOMs at 32k on 96GB once CCE is off. CPU offload was disabled after a `DeepSpeedCPUAdam` JIT-build failure in the `sft-axolotl` TACC env (GCC rejects the armv9 flags; jobs 816487/817101). ⚠ **That build failure is a TACC-env toolchain gap, NOT an aarch64 limitation** — the LLaMA-Factory stack builds CPU-offloaded Adam on Jupiter's aarch64 GH200 and fits the same Qwen3-32B@32k there (`ds_z3_offload_nomat`, `offload_optimizer:cpu`+`offload_param:cpu`). So offload IS achievable on this hardware. **ROOT CAUSE FOUND + FIXED (2026-07-09, commit `e4543faf`):** the TACC launcher set `TRITON_CC=gcc` but never exported `CC`/`CXX`, so DeepSpeed's `CPUAdamBuilder` grabbed nvc++ → rejected the armv9 flags. The `vista` block in `hpc/hpc.py` now exports `CC`/`CXX` → gcc/g++ 15.1.0 (same compiler as `TRITON_CC`), so a `DS_BUILD_CPU_ADAM=1` prebuild / runtime CPUAdam build now uses gcc. Offload is thus the *next* memory lever if needed — but **liger alone VALIDATED it: job `818130` (2026-07-09) hit ZERO CUDA OOM, fit the full forward + most of the first backward** (died on an unrelated transient IB node fault, `IBV_WC_RETRY_EXC_ERR` → NODE_FAIL, not memory). So **offload is NOT needed at Qwen3-32B @32k with liger on**; offload remains the lever only if we push context/size further. The liger passthrough itself is `hpc/axolotl_config_utils.py` (`enable_liger_kernel:true` → `LigerPlugin` + the four `liger_*` flags); confirmed active in-log (`Applying LIGER to qwen3 … fused_linear_cross_entropy:True`). **Do NOT propagate "aarch64 can't build cpu_adam / can't offload" as fact — it's false.**
3. **`CutCrossEntropyPlugin` disabled** (commented in YAML): on aarch64+torch2.9+FA2 it causes bf16 grad explosion (`grad_norm ~1e11` in 3–7 steps) → NaN loss masked as 0. Also set `max_grad_norm: 1.0` explicitly. (The CCE fork is still installed because import paths need it.)
4. **torchao missing on aarch64 → `builders` import fails.** Axolotl's `pyproject.toml` excludes torchao on aarch64 (`platform_machine != 'aarch64'`) but `src/axolotl/utils/callbacks/qat.py` imports it unconditionally (`from torchao.quantization.qat.embedding import FakeQuantizedEmbedding`), so `axolotl/core/builders/causal.py` fails at trainer setup with `ModuleNotFoundError: No module named 'torchao'`. **Fix (env, NOT a submodule patch): `pip install --no-deps torchao==0.17.0` into the axolotl env.** torchao 0.17.0 is a pure-Python `py3-none-any` wheel → installs clean on aarch64, torch untouched (2.11.0+cu128), and the QAT + builder imports then succeed (verified on TACC Vista, smoke job 801458). The `otagent`/LF env already ships torchao 0.17.0 on this cluster (`.agents/ops/tacc/ops.md`). *(Do NOT patch qat.py with try/except — that would diverge the pinned submodule; the pip install is the clean fix.)* Separately, `convert_axolotl_checkpoint.py` strips `_checkpoint_wrapped_module.` FSDP prefixes from state_dict keys so vLLM/sglang can load (required post-train step; canonical copy on Jupiter).
5. **Omit `hub_model_id`/`hub_strategy`** from the config: under `HF_HUB_OFFLINE=1` the in-training `init_hf_repo()` crashes `OfflineModeIsEnabled` — push manually after.
6. **sbatch needs the compiler env** (`CUDA_HOME`, `GCC_HOME`, `CC`/`CXX` for Triton JIT), `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`, offline flags, `NCCL_SOCKET_IFNAME=ib0`.
8. **`auto_resume_from_checkpoints` inherits `save_steps` (and other TrainingArguments) from a stale checkpoint's `trainer_state.json` — a "from-scratch" relaunch is NOT from-scratch if the output_dir has old checkpoints.** HF Trainer restores trainer-state on resume, so a checkpoint written by a prior run with `save_steps: 10` makes the NEW run save every 10 even though the rendered config + `args` say `save_steps: 200` (visible in-log as `save_steps: 200 (from args) != 10 (from trainer_state.json)`). It's cosmetically silent — training/loss are correct, only the save cadence (→ wall-clock overhead) is wrong. **Fix: to genuinely start from scratch, WIPE the output_dir first** (or set `auto_resume_from_checkpoints: false`); do NOT trust "output_dir clean" without verifying no `checkpoint-*/` remain. (Origin: TACC `_17` 32B run 824241/824242, 2026-07-12 — render was correctly `save_steps: 200` but it resumed a stale save_steps:10 ckpt → every-10 saves ≈ 30-50% wall overhead; let run to completion since restarting wastes more than it saves. `agent_logs/2026-07-12_tacc_axolotl32b_save_cadence_resume_inherit.md`.)
7. **DeepSpeed missing in `sft-axolotl` on TACC → ZeRO-3 configs crash at bring-up (~85s, exit 1).** The `sft-axolotl` env was validated only on the FSDP/single-node smoke + delphi canary paths, which never imported deepspeed. Any config with a truthy `deepspeed:` key (e.g. the 32B `zero3_bf16.json` parity config) crashes in `load_cfg → prepare_optim_env → setup_deepspeed_env → init_distributed_state → accelerate `PartialState.__init__`` with **`ImportError: DeepSpeed is not available => install it using pip3 install deepspeed`** (accelerate sees `ACCELERATE_USE_DEEPSPEED` set from the config but `is_deepspeed_available()` is False). Every rank fails config-load; the visible tail is only the secondary c10d/TCPStore `RendezvousConnectionError` teardown noise — grep the head of the log for the real `ImportError`. **Fix (env, NOT a config/code change): `pip install --no-build-isolation deepspeed==0.18.0` into `sft-axolotl` on a `-p gg` compute node** (matches the otagent env's version). Installs clean on aarch64 (pure-py wheel + small deps hjson/ninja/msgpack/py-cpuinfo), torch untouched (2.11.0+cu128), `is_deepspeed_available()` → True. **No DeepSpeedCPUAdam/FusedAdam JIT concern** because `zero3_bf16.json` has NO offload + NO optimizer block → HF passes the torch `adamw_torch_fused` optimizer straight through (verified TACC Vista, 2026-07-08, job 815248 install; fixed the 814549 crash).

---

## Qwen3-32B LF-parity SFT config (`sft/axolotl_configs/qwen3_32b_ot_sft_10k.yaml`)

Learning-parity port of the canonical LLaMA-Factory `sft/lf_configs/qwen3/32k_base_32b.yaml` (bs=96 variant)
onto the axolotl backend, on `open-thoughts/OpenThoughts-Agent-SFT-10K`. Launched via
`hpc.launch --job_type sft --sft_backend axolotl` (translator `hpc/axolotl_config_utils.py`; only
translator-recognized keys survive, so some LF-named keys are used — `lr_scheduler_type`→`lr_scheduler`,
`optim`→`optimizer`). Ground truth for the design decisions lives HERE, not in the YAML comments.

- **Learning-parity map (all learning-affecting knobs matched to LF):** effective batch 96 (micro=1,
  grad_accum derived = 96/num_nodes; 96 must be divisible by node count), LR 4e-5, cosine + warmup_ratio 0.1,
  7 epochs, seq_len 32768, `max_grad_norm 1e-4` (LF's aggressive clip, matched exactly), `adamw_torch_fused`
  (betas 0.9/0.999), weight_decay 0.0, mixed bf16 + fp32 master, gradient_checkpointing on, sample_packing off.
- **Chat-template / masking (the load-bearing correctness decision → use `chat_template: chatml`, NOT
  `qwen3.jinja`).** LF `template: qwen3` (a ReasoningTemplate) trains via `encode_multiturn` with
  `mask_history=False`+`enable_thinking=True` → plain ChatML, TRAINS EVERY assistant turn with inline
  `<think>…</think>` KEPT (no historical-think stripping), user/system masked. The axolotl `qwen3.jinja` is the
  *serving* template — it STRIPS `<think>` from all but the post-last-query turn → trains on far fewer reasoning
  tokens → DIVERGES from LF. Axolotl `chatml` emits `<|im_start|>{role}\n{content}<|im_end|>\n` verbatim with
  inline `<think>` on ALL turns = exact match to LF qwen3's `encode_multiturn`. `split_thinking:false` (set by
  the launcher's `_build_datasets`) keeps `<think>` inline so chatml never splits it out.
- **Deviations from LF:**
  - *sdpa vs LF fa2* — learning-neutral (both exact attention); axolotl uses sdpa because there's no
    flash-attn-2 wheel for torch 2.11+cu128 on aarch64 (`ops/tacc/ops.md`).
  - *liger — FIXED 2026-07-09 (was omitted).* LF runs `enable_liger_kernel:true`; the axolotl config now
    sets it too AND the translator (`hpc/axolotl_config_utils.py`, commit `e4543faf`) has a **liger
    passthrough**: `enable_liger_kernel:true` → appends `axolotl.integrations.liger.LigerPlugin` to `plugins`
    + emits `liger_rope`/`liger_rms_norm`/`liger_glu_activation`/`liger_fused_linear_cross_entropy: true`.
    Previously the translator SILENTLY DROPPED `enable_liger_kernel`/`plugins` (only assembled
    template_integrity/mfu/supabase) — so the key alone would have been a no-op; the passthrough is the
    load-bearing fix. Learning-neutral but **NOT memory-neutral**: `LigerFusedLinearCrossEntropy` fuses the
    LM head + CE so the full ~18 GB logit tensor (seq 32768 × vocab ~152k × bf16) never materializes — the
    exact allocation that OOM'd. Flag-off byte-identical (off-path emits no liger keys / no plugin).
  - *DeepSpeed offload OFF vs LF ON* — see gotcha #2. LF offloads optimizer+params to CPU; axolotl currently
    can't (TACC toolchain build gap, NOT an aarch64 limit) so fp32 optimizer states stay in HBM.
- **⚠ The 32B OOM (jobs 816487 @16-node, 817107 @32-node) — CONFIG GAP, not a hardware/capacity ceiling
  (2026-07-09).** The identical Qwen3-32B@32k FITS in LF on the same GH200 class. The axolotl OOM is the
  compounding of the two deviations above: (1) **no liger fused-CE** → the ~18 GB logit tensor (817107 OOM was
  `tried to allocate 18.00 GiB` in the first ZeRO-3 backward — matches), (2) **no CPU offload** → fp32 optimizer
  states in HBM. **The earlier "scale 16→32 nodes to halve the shard" fix was a MISDIAGNOSIS** — ZeRO-3 shards
  model states but NOT activations, so more nodes didn't touch the logit tensor and 817107 OOM'd again at 32
  nodes. **Real fix path (cheap config changes, reproduces LF's proven-fit setup): enable liger fused-CE
  (likely fits alone by killing the 18 GB tensor) + restore CPU offload (fix the cpu_adam toolchain).** NOT
  sequence-parallelism / more nodes. **IMPLEMENTED + RELAUNCHED 2026-07-09 (commit `e4543faf`):** liger
  passthrough added to the translator + `enable_liger_kernel:true` in the config + `CC`/`CXX` exported in the
  `vista` hpc.py block (offload prep). Relaunched at **16 nodes** (reverting the 32-node misdiagnosis bump)
  as **job 818130** — liger ONLY, offload still OFF, testing whether liger alone fits. First-backward verdict
  + any next-lever (restore offload) in `agent_logs/2026-07-09_sft_32b_axolotl_oom_config_gap.md`.
- **Multi-node dataset-prep (why the shared-`$SCRATCH` sentinel fast-path):** pre-tokenize ONCE via
  `axolotl preprocess` → writes the tokenized arrow + a `.axolotl_prepared_complete` sentinel to
  `dataset_prepared_path: $SCRATCH/axolotl_prepared/...`; the multi-node job then hits axolotl
  `FileLockLoader`'s LOCK-FREE fast-path (sentinel present → all ranks `load_from_disk` concurrently, no
  shared-FS FileLock). Axolotl loads datasets BEFORE dist-init, so it can't use a torch barrier like LF's
  `main_process_first` — the sentinel IS that barrier's equivalent. **NOT node-local `/tmp`** (per-rank builds
  desync → multi-node DEADLOCK at "Generating train split", job 815590 hung 1h10m). **NOT the default shared
  lock** (16 ranks serialize on one Lustre flock across a multi-min build → ENOLCK/ESTALE, jobs 815251/815508/
  815530). `$SCRATCH` is expanded by the launcher translator. (Sentinel fast-path = submodule `8bd0a508`.)

---

## Versioning

Flat monotonic suffix on HF repos: `-v2`, `-v3`, `-v6`, `-v7`, `-v8` (v4/v5 intentionally skipped to keep
the dataset-recipe version distinct from the run version). The dataset segment (e.g. `Sera-4.6-Lite-T2-v4-316`)
is separate from the run version (`-v3`). In-flight runs keep their names; the NEXT retrain takes the next
flat number. (See `.agents/skills/sft-job-cleanup` operating notes; matches `feedback_baseline_model_versioning`.)

Install recipe (env build + the two patches + the prebuilt aarch64 flash-attn wheel + the CCE fork) is in
`notes/axolotl.md`.
