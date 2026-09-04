# Levanter — facts & how experiments are specced

JAX foundation-model training library (the engine under marin's pretrain/midtrain/SFT steps).
Learned 2026-06-29 while pulling Delphi midtraining configs. Source of truth = the marin monorepo
checkout `/Users/benjaminfeuer/Documents/marin/lib/levanter` (published to PyPI as `marin-levanter`).
See also `marin-executor` (how it's launched) and `mum` (how to find run configs). Grug is **not** a
Levanter frontend — see `[grug]` notes / `marin/.agents/projects/grugformer.md`.

---

## What it is (correct the "SFT engine" misconception)

- A **full** LLM/foundation-model training library — **pretraining, midtraining (CPT), SFT, eval,
  export** — not specifically an SFT engine. SFT is a *mode* of `train_lm`, not a separate engine.
- Stack: **Haliax** named tensors (`NamedArray` + explicit `Axis`) over **Equinox** modules;
  **draccus** dataclass configs; `AsyncDataset` data pipeline. Runs **TPU + GPU**.
- **Bitwise deterministic** (same config → same result across preempt/resume).

## How experiments are specced — a draccus dataclass tree, one per entry point

- Entry points live in `lib/levanter/src/levanter/main/`: `train_lm.py`, `train_dpo.py`, `lora_lm.py`,
  `eval_lm.py`, `export_lm_to_hf.py`, `sample_lm.py`, `train_asr.py`, … Each has a root config dataclass.
- `train_lm` → **`TrainLmConfig`** (`src/levanter/main/train_lm.py:42`), composed of nested sub-configs:
  - `data: LmDataConfig` — tokenizer, `cache_dir`, `components` (per-component `source` = url|hf + `format`
    = chat for SFT), **`train_weights`** (the mixture map — this is the `pNNmNN` Delphi mix), `shuffle`.
  - `trainer: TrainerConfig` — `train_batch_size`, `num_train_steps`, `mp` (precision e.g. `p=f32,c=bfloat16`),
    `per_device_parallelism`, `tracker` (wandb).
  - `model: LmConfig` (default `LlamaConfig`) — `type: llama`, dims, heads, `rope`, etc.
  - `optimizer: OptimizerConfig` (default `AdamConfig`) — `learning_rate`, `weight_decay`, `warmup`, schedule.
  - `train_seq_len`, `initialize_from_hf` / `initialize_from_checkpoint_path` (CPT/SFT/midtrain **init**),
    `hf_save_path`/`hf_upload`, `eval_harness`, `adapter` (LoRA).
- Polymorphism: a **`type:` field** selects the variant (model `type: llama`, optimizer/tracker/data-source
  types) — draccus discriminated unions.

## Authoring + running it (the raw-Levanter path)

- A **YAML** populates the tree (`lib/levanter/config/*.yaml` — e.g. `llama3_small_fast.yaml`,
  `train_lm_config` shapes; SFT example `train_lm_llama3_tulu_sft.yaml` uses `train_weights: {tulu: 1.0}` +
  `format: {type: chat}`).
- Run via the draccus entry (`levanter.config.main(main)()` at `train_lm.py:428`):
  `python -m levanter.main.train_lm --config_path config/<f>.yaml --trainer.num_train_steps 5000` (any field
  CLI-overridable with dotted keys).
- **SFT / midtraining are just `train_lm` with a different data block + init** — SFT = chat-format component +
  `initialize_from_hf`; midtrain/CPT = a `train_weights` mixture + `initialize_from_{hf,checkpoint_path}`.

## Where the RESOLVED config is persisted (this is how to recover what a run actually used)

A finished run writes its full resolved config to its GCS run dir — **but the filename depends on the launch path**:
- **Script/midtrain-launch** → `gs://…/checkpoints/<run>/train_lm_config.yaml` (+ a run manifest, e.g.
  `midtrain_manifest.json`).
- **marin-executor launch** → no `train_lm_config.yaml`; the config is inside `.executor_info` under
  `config.train_config` (`jq '.config.train_config'`). See the `marin-executor` doc.
This split is why the same experiment family can have two artifact shapes (and why `mum run` finds some configs
but not others — see `mum`).

## Worked example (Delphi K=0.20 midtraining = TrainLmConfig instances)
`data.train_weights` = the pNNmNN mixture (math `nemotron_cc_math_v1/4plus` + Nemotron-CC web replay);
`initialize_from_hf` = the matching base; optimizer = Muon dual-LR (`learning_rate` matrix + `adam_lr`),
`lr_schedule: linear`, `warmup: 0.1`, `min_lr_ratio: 0`; tokenizer `meta-llama/Meta-Llama-3.1-8B`, seq_len 4096,
`block_cross_document_attention: true`. Configs pulled to `~/Documents/experiments/active/midtrain-25B/configs/`.

## Checkpoint & resume gotchas (production — `delphi_1e22`, 2026-07-11)

- **⚠ RESUME-ONLY OOM = BFC-allocator fragmentation → fix with the `cuda_async` DEFRAG allocator.** A large-model
  run trains fine from step 0 but, on RESUME, semi-deterministically OOMs at (or a few thousand steps after) the
  first post-resume step: `RESOURCE_EXHAUSTED: … allocate <N>GiB [executable_name='jit__train_step']`, while the BFC
  free-map shows plenty of FREE HBM but **no contiguous hole**. Cause: on resume, tensorstore materializes params +
  Adam μ/ν on-device in a layout differing from the compiled step's, and the default **BFC allocator can't compact**
  → the step's large transient contiguous block can't be placed against the load-fragmented heap (steady-state
  in-place reuse never has to). Fragmentation, not a real shortage — marin issue **#7115** (proper upstream fix =
  buffer donation across the resume boundary). **FIX (allocator plumbing only, math-neutral): switch to `cuda_async`**
  — `JAX_PJRT_CLIENT_CREATE_OPTIONS=allocator:cuda_async` (env: `SINGULARITYENV_…`; + mirror in the executor's
  `trainer.jax_config` as `"jax_pjrt_client_create_options":"allocator:cuda_async"`, re-listing the DEFAULT_JAX_CONFIG
  keys since supplying `jax_config` REPLACES them). **⚠ ALLOCATOR-ENV TRAP (version-specific):** on jax/jaxlib
  **0.10.1 + `jax_cuda13`** the allocator comes from the PJRT create-options dict, populated ONLY by
  `JAX_PJRT_CLIENT_CREATE_OPTIONS` — so **`XLA_PYTHON_CLIENT_ALLOCATOR=platform` is INERT** (older-JAX flag), and
  `TF_GPU_ALLOCATOR=cuda_malloc_async` is inert too (a TF var). Verify via `device.memory_stats()['pool_bytes']` —
  **None = cuda_async (good), numeric = still BFC**. **Do NOT also set `XLA_PYTHON_CLIENT_MEM_FRACTION`** with
  cuda_async (0.90 shrinks out-of-pool headroom to ~6.5 GB — risky for NCCL/cublas; the 0.75 default leaves ~16 GB).

- **⚠ Wall-SIGKILL mid-save orphans a metadata-only staging checkpoint that POISONS resume discovery.** If SIGKILL'd
  at the wall *during* a save, Levanter leaves a ghost `step-<N>/` in the atomic-write staging mirror
  `<exp>/tmp/checkpoints-temp/…/checkpoints/step-<N>/` with **only `metadata.json` (~80 B)** — no `d/`, no
  `manifest.ocdbt`, no tensors (post-save cleanup + atomic rename never ran). Discovery scans INTO the staging
  mirror, sees the ghost `> ` the last complete step, picks it → **all ranks `FileNotFoundError` on every tensor
  leaf in <33s, 0 steps**, every afterany resume identical. The crash-teardown `grpc … UNAVAILABLE … Connection
  refused` is NOISE, not the cause (`jax.distributed.initialize` actually succeeded — ranks jointly log "Discovered
  latest checkpoint at step-<ghost>"; don't chase a coordinator red herring). **Fix:** `rm -rf
  <exp>/tmp/checkpoints-temp` (the real `checkpoints/step-*` tree is untouched) → discovery falls back to the last
  complete step (verify the ghost is metadata-only + the fallback has `d/`+`manifest.ocdbt` first). **Durable guard:**
  `rm -rf "$OUT/tmp/checkpoints-temp"` before `srun` so every relaunch self-cleans.

- **Save cadence vs mean-time-to-failure:** `keep: [{every: N}]` retains only every-N permanent keeps; the 30m
  rolling "latest" is NOT reliably rediscovered after an abnormal (wedge/OOM-hang) termination → resume lands on the
  last every-N keep. On a flaky cluster where the job dies BETWEEN keeps, it re-resumes the same keep = a
  no-progress loop. Make `keep` frequent enough to bank progress inside the mean-time-to-failure.

(Full write-ups: `agent_logs/2026-07-10_1e22_dod_resume_chain_jax_coordinator_death.md`.)

## Throughput / mesh perf gotchas

- **delphi_1e22 SFT (dense ~9.7B, 16×A100, seq 4096, packed) ran at MFU ~18% packed** (`throughput/mfu` median
  ~18.3%, job 49038797). **The cause of that throughput level is UNQUANTIFIED** — no profiler trace or ablation
  has been run, so no contributor has been shown to dominate. Grounded notes on the geometry: the device grid is
  logical `[16,1]` pure-FSDP (`[4,4]` is the *physical* 4-node×4-GPU topology, NOT a tunable axis map — reshaping
  it is not a free lever). Unranked candidate contributors: **per-device batch = 1** (`train_batch_size 16 / 16
  GPUs`, `per_device_parallelism -1` → small GEMM tiles); **cross-node FSDP** (Leonardo 4×A100/node → 16-way FSDP
  spans 4 nodes every layer); **remat recompute** (an involuntary-rematerialization warning was observed at
  bring-up but never quantified). Config knobs if you diagnose one matters: `gradient_checkpointing:
  bool|ScanCheckpointPolicy|str` (`models/llama.py:80`; policies `haliax/_src/scan.py`), and the higher-EV
  `per_device_parallelism 1→2` (attacks batch=1; ~9.7 GB/device on 64 GB → ample headroom). **Diagnose before
  mitigating** — the cheap confirmation experiment (~50-step `save_all` ablation / `jax.profiler` trace) is in
  `agent_logs/2026-07-12_delphi1e22_mfu_attribution_audit.md`.
- **MEASURED apples-to-apples (both PACKED, 2026-07-13): Levanter 18.3% vs LF 15.8% per-step MFU — Levanter is
  ~1.15× FASTER, not slower.** On the IDENTICAL packed 9.7B / 16×A100 / batch-16 / seq-4096 workload (both process
  ~65536 real-token positions/step, dense-causal 4096² attention, same analytic 4.082e15 FLOPs/step): Levanter
  4.5 s/it → 18.3%; **LF-packed (job 49296206, `packing:true`) 5.19 s/it → 15.8%** (5853 steps / 93633 packed
  examples). So once the packing confound is removed, Levanter is competitive-to-slightly-BETTER per step; the
  "involuntary-remat / XLA ~2× gap" narrative is NOT supported.
- **⚠ The earlier "LF 35.7% (~2× per-step)" number was a MIRAGE — do not cite it.** It compared packed-Levanter
  against the UNPACKED LF baseline (job 46798799, 2.29 s/it), whose `mfu_percent_theoretical` 35.7% counts FULL
  4096-position work the run never did: unpacked ran short/variable-length sequences (fa2 skips padded keys →
  real attention ~`valid_targets_mean` 681² ≪ 4096²; and/or dynamic-pad-to-batch-max shrinks the MLP too), so its
  2.29 s/it reflects far LESS compute than the analytic assumed → inflated %. Packing forces genuine full-4096 work
  and the true LF number (15.8%) drops below Levanter's. (Operator's "variable-length packing" caveat, confirmed.)
  Full write-up: `agent_logs/2026-07-13_lf_packed_mfu_reversal.md`; config comparison + baseline artifacts:
  `experiments/active/delphi-sft-levanter-parity/lf_baseline_1e22_mfu/`.

## MFU calculation technique (Levanter vs LLaMA-Factory — apples-to-apples)
To compare framework MFU on the SAME model/hardware, get each side's number, then normalize the formula:
- **Levanter MFU** = wandb `throughput/mfu`. Offline runs (Leonardo `WANDB_MODE=offline`): read the offline run's
  `files/wandb-summary.json` key `throughput/mfu` — it is NOT printed to stdout. Formula =
  `levanter.utils.flop_utils.lm_flops_per_token` (mlp + qkv_proj + dense_proj + **full attention** `2·seq²·heads·head_dim`
  + `lm_head`) × 3 (fwd+bwd) × seq ÷ (devices × peak); peak from hardware (A100 bf16 = 312 TFLOPs).
- **LLaMA-Factory MFU** = set `include_mfu: true` → `all_results.json` fields `mfu_percent_theoretical` +
  `achieved_tflops_per_gpu_theoretical` (code: `llamafactory/extras/misc.py::compute_mfu_from_trainer`; printed
  as `MFU (HF): …` by `train/sft/workflow.py`; peak via `PEAK_TFLOPS_PER_GPU` or a device lookup). ⚠ The
  **non-theoretical** `mfu_percent`/`total_flos` triplet comes from HF Trainer `total_flos` and is frequently
  BROKEN (accounting/overflow — e.g. `total_flos` 6.95e14 for a 9.7B×34720-step run → 0.0002% MFU); **always use
  the `*_theoretical` fields.** (HF `total_flos` = `6·N_non-embedding·tokens`, and counts PADDED tokens.)
- **Verify the formulas are comparable** by back-computing FLOPs/token = `achieved_TFLOPs/GPU × devices ÷ (tokens/s)`
  for each and checking both land near `6N` (they matched at ≈6.25e10 for delphi 1e22 → the % numbers are directly
  comparable).
- **⚠ MFU ≠ useful efficiency when PACKING differs.** An unpacked run counts padding FLOPs as "utilization" → its
  MFU is inflated. For the real comparison use **real-token throughput** (weight tokens/s by the real fraction: LF
  `valid_targets_mean/seq`; a packed Levanter run ≈ 1.0) and/or **end-to-end wall-clock for the same dataset**
  (`steps × s/it`) — packing gives ~6.5× fewer steps and can flip a per-step MFU deficit into a net win.
- **Formula-independent shortcut:** for two runs of the SAME config (same `6N`, `tokens/step = batch×seq`, devices,
  peak), **MFU ratio = inverse step-time ratio** — you only need each run's s/it to compare per-step efficiency.

## Sequence packing (chat SFT) — ON by default, and the step-count trap

- **`ChatLmDatasetFormat` PACKS by default.** With `pack` unset, `_effective_pack()` (`data/datasets.py:365`)
  returns `True` for chat → builds a greedy packer (`GreedyPrepackedDataset`, `max_segments_per_example=64`)
  that fills each `seq_len` slot with multiple conversations. There is **no chat pad-to-seq_len path**
  (`pack=="pad"` raises `NotImplementedError`). Cross-sample isolation is correct: the packer emits
  `segment_ids` + `AttentionMask.causal().with_segment_ids(…)` and `block_cross_document_attention` defaults
  `True` — no attention leak between packed conversations, per-segment completion mask preserved.
- **⚠ STEP-COUNT TRAP (bit delphi_1e22): `num_train_steps` must account for packing.** Levanter SFT is
  step-based (no config-level epoch cap wired — the `EpochDataset(max_epochs=N)` primitive at
  `data/dataset.py:362` exists but is not constructed by `train_lm`). Computing `num_train_steps` as
  `rows / weight / global_batch` assumes **one doc per slot** → with packing (~6 docs/slot for short
  instruction data) that's **~6× too many steps = ~6× over-training** (delphi_1e22 ran 34,722 steps = ~6.5
  epochs; near-zero loss = the symptom). For 1 packed epoch use `packed_examples / weight / global_batch`
  (`packed_examples ≈ total_tokens / seq_len`). (Observed 2026-07-12.)
