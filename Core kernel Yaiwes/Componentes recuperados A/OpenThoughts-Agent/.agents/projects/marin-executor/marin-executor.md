# Marin executor (ExecutorStep) — facts & gotchas

Marin's pipeline/experiment system: single-file Python specs that build a DAG of `ExecutorStep`s and dispatch
engines (Levanter, eval, tokenize, upload, …). Learned 2026-06-29 recovering Delphi midtraining configs.
See `levanter` (the engine it usually drives) and `mum` (finding run records).

> ## ⚠ RETIRED 2026-07-09 — the Executor + `ExecutorStep` are GONE (marin PR #6649; rjpower confirmed on our #7080)
> Marin **replaced the eager import-time content-addressed Executor with lazy typed `ArtifactStep`s** and
> **deleted the Executor** (`marin.execution.lazy`): experiments now build the step graph at *run* time from
> plain functions, addressed by explicit **`name@version`** (CALVER) instead of an md5-of-the-config-tree, with
> typed `Artifact` outputs (`LevanterCheckpoint`, `TokenizedCache`, …). Identity (`build_config(ctx)`, pure over
> a `StepContext` — literals bear identity, `ctx.output_path`/`prefix`/`region` don't) is separated from
> execution (compute rides the fn via `remote(fn, resources=…)`, never the graph node). So the whole "§Model /
> `ExecutorStep(...)`/`versioned(...)`/`this_output_path()`" section below is **HISTORICAL** for reading old
> runs; new work uses `ArtifactStep`.
> - **`StepRunner` + its per-step distributed lock SURVIVE** (`marin.execution.step_status` — `Acquired lock` /
>   `Lost lock race, retrying`, `rigging.distributed_lock`). **⚠ It DEADLOCKS an SPMD (srun N-rank GPU) step:**
>   one rank wins the lock and enters `jax.distributed.initialize()`+barrier while the other N−1 spin on the
>   lock forever and never join → hang at the N-process barrier (**issue #7080**; hit on the 4×4-A100 Delphi
>   SFT). **Workaround: bypass `StepRunner` and call the Levanter entrypoint (`train_lm.main`) directly in every
>   rank** (we env-gate it `DELPHI_DIRECT_RUN=1`), so all ranks form the mesh. rjpower's fix is logging/examples,
>   not auto-detection. Migrating a training path off the executor = rebuild on `ArtifactStep`/`remote(...)`.
> - **⚠ The direct-entrypoint path is NOT a hack — it's Marin/Levanter's SANCTIONED SLURM launch (validated 2026-07-09).**
>   There is deliberately **no "SLURM Fray backend"**: `remote(fn, resources=…)`→Fray is the *Iris/CW/Ray/TPU* dispatch
>   layer only. On SLURM the *scheduler itself* is the placement backend. `levanter/distributed.py`
>   `DistributedConfig.initialize()` (run by `train_lm.main` on every process) branches by cluster: Iris job context
>   (`get_job_info() is not None`) → `initialize_iris_jax()`; else auto-detect → **`LevanterSlurmCluster`** (a
>   `jax._src.clusters.SlurmCluster` subclass) reads `SLURM_*` directly (nodelist→coordinator addr, `SLURM_NTASKS`→
>   process count, `SLURM_PROCID`→id, `CUDA_VISIBLE_DEVICES`→local devices) and calls `jax.distributed.initialize()`
>   on every rank. So **the recommended multi-node-SLURM run = `srun` (1 task/proc) launching Levanter directly**,
>   which is precisely the `DELPHI_DIRECT_RUN` path. **Two decoupled layers:** *identity/graph* = `ArtifactStep`
>   (name@version, typed artifacts — cluster-agnostic, use it on Leonardo too); *execution/mesh* = cluster-specific
>   (`remote()`→Fray→`initialize_iris_jax` on Iris/CW; `srun`→`LevanterSlurmCluster` on SLURM). The `StepRunner` lock
>   only deadlocks because it inserts a single-winner dedup *in front of* an SPMD collective — skipping it on SLURM is
>   correct by design, not a compromise.
> - **The GCS artifact layout below (`.executor_info` etc.) still applies to OLD executor-launched runs** (Delphi
>   1e21/1e22 midtrains); `mum` + `gsutil cat .executor_info` still recover their configs. New `ArtifactStep`
>   runs use the `name@version` address + typed `Artifact.record`.

---

## Model

- An **experiment is a Python file** that constructs `ExecutorStep`s; the executor resolves a **versioned config
  hash**, output paths, and resources (TPU type, etc.), then runs the step's `fn` with the resolved config.
- A training step's `fn` is a Levanter entrypoint, e.g. `run_levanter_train_lm`, called with a resolved
  `TrainLmConfig` (the executor's `config.train_config`).
- User-facing knobs (seen in grug's `launch.py`): `ExecutorStep(...)`, `versioned(...)` (marks values that affect
  the step version/hash), `this_output_path()` (current step output root).

## GCS artifact layout — executor-launched run dir (`gs://marin-us-east5/checkpoints/<step-name>/`)

An executor-launched run writes **executor artifacts**, NOT a `train_lm_config.yaml`:
- **`.executor_info`** — JSON: `{name, fn_name, config}`. **`config.train_config` is the FULL resolved Levanter
  `TrainLmConfig`** (data + `train_weights` mixture, model, trainer, optimizer, `initialize_from_hf`, …).
  → recover a run's config with `gsutil cat gs://…/<run>/.executor_info | jq '.config.train_config'`.
- `.artifact.json`, `.executor_status` — artifact/exec metadata.
- `tracker_metrics.jsonl` — metrics stream.
- `checkpoints/` (Levanter/OCDBT), `hf/` (exported HF weights).

## The launch-path asymmetry (the key gotcha — bit us on the Delphi 1e21/1e22 runs)

The **same logical experiment family can have two different artifact shapes** depending on how it was launched:

| launch path | config artifact in run dir | W&B run name | `mum run` finds config? |
|---|---|---|---|
| **script / midtrain script** | `train_lm_config.yaml` (+ run manifest) | = the run id | ✅ yes |
| **marin executor** | `.executor_info` (`config.train_config`) | step label; the id often appears ONLY embedded in *derived* runs (eval/ppl) | ❌ 404 — query by name finds nothing |

Concretely: the 21 small Delphi midtraining runs (3e18–3e20) were script-launched → `train_lm_config.yaml`
present, W&B/`mum run` resolve them. The 6 large runs (1e21/1e22) were **executor-launched** → only
`.executor_info` carries the config; their `#6279` ids are step labels that exist only inside the
`clean_seen_…_eval-…` / `ppl-gap-score-…` derived runs (project `marin`), so `mum run` 404s and the W&B
per-run config endpoint has nothing to return. **GCS `.executor_info` is the authoritative recovery path for
executor-launched runs.**

## Launching an executor experiment onto Iris (the key gotcha — bit us launching the Delphi 1e23 25B midtrain)

**A bare `python experiments/foo.py` does NOT run on a TPU.** It runs `executor_main` with a `fray`
**LocalClient** (`fray.current_client: using LocalClient (fallback)`) and tries to train **in-process on the
launch host** → dies with `Failed to open libtpu.so`. The executor only dispatches to Iris when it runs
**inside an Iris job** (where `IRIS_TASK_ID` is set), so `current_client()` auto-detects the Iris backend
(`using Iris backend (auto-detected)`).

**Correct launch = a CPU `iris job run` coordinator that spawns the training as a nested Iris job:**
```bash
cd <marin repo>; source secrets.env     # secrets are NOT auto-injected — pass them explicitly
.venv/bin/iris --cluster=marin job run \
  --job-name <run>-coord \
  --region us-east5 \                    # pin so coordinator worker_region == executor's GCS-path-inferred region
  --cpu 1 --memory 2G --extra cpu \      # CPU-only coordinator; --extra cpu installs jax-CPU so imports work
  --priority interactive --max-retries 10 --no-wait \
  -e MARIN_PREFIX gs://marin-us-east5 -e HF_TOKEN "$HF_TOKEN" -e WANDB_API_KEY "$WANDB_API_KEY" \
  -- python experiments/<dir>/<exp>.py
```
- The coordinator (tiny CPU job) walks the DAG and submits each `@remote` step (e.g. the v5p-64 `with_tpu`
  training) as its **own nested Iris job**: `/<user>/<run>-coord/checkpoints-<step>-<hash>`. The child inherits
  the coordinator's env vars + `worker_region` (so pin the coordinator's `--region` to the data region or the
  child gets a **conflicting** region constraint vs the executor's GCS-path inference and never places).
- **Coordinator must be CPU-only** (`--cpu 1 --memory 2G`, `--extra cpu`) or it hogs a TPU node and deadlocks.
  `--memory ≥4G` or `--disk ≥10G` would need `--enable-extra-resources` — stay under it. Canonical pattern:
  `docs/explanations/executor.md`, `docs/tutorials/train-an-lm.md`.
- **Secrets/MARIN_PREFIX are NOT copied from the submitter shell** — pass via `-e` (OPS.md "job run gotchas").
- **File packaging:** `iris job run` bundles via `git ls-files --cached --others --exclude-standard`, so an
  **untracked-but-not-gitignored** experiment file DOES ship. Read NO host-local paths at DAG-build time
  (inline data blocks) — the coordinator runs on a remote worker.
- **Validate offline first:** `MARIN_PREFIX=gs://marin-us-east5 WANDB_MODE=disabled python experiments/foo.py
  --dry_run true` runs the executor locally in dry mode (LocalClient is fine for dry-run; it only validates the
  DAG/config, prints the resolved `Output_path`).

### v5p OOM lever (25B on v5p-64): `per_device_parallelism`
A 25B model on a v5p-64 (32 chips × ~95.7G HBM) **OOMs at first XLA compile** with
`per_device_parallelism=-1` (auto = batch/num_devices = 32 examples/device → activations overflow:
`CompileTimeHbmOom: Used 110.81G of 95.74G hbm`). Fix: set **`per_device_parallelism=4`** (microbatch 4/device
+ grad-accum; the value the 1e22 reference used) → cuts activation memory ~8×, fits. It is a **perf knob, math-
equivalent**, so it is **excluded from the executor config-version hash** (the output dir/`b6607e` hash is
UNCHANGED when you flip it). Device-memory fit is only exercised at the child's first compile — dry-run can't
catch it; watch the child's first compile for `RESOURCE_EXHAUSTED`.

## Practical
- To recover any run's exact config, prefer GCS over W&B: `gsutil ls gs://marin-us-east5/checkpoints/<run>/`,
  then either `train_lm_config.yaml` (script) or `.executor_info` → `config.train_config` (executor).
- GCS read access from the laptop works via `/opt/homebrew/bin/gsutil` (these config files are KB-scale — fine
  to pull; do NOT bulk-pull checkpoints cross-region).
- Health-checking a running training job (step progress + major gaps): the OT-Agent skill
  **analyze-training-run-iris** (W&B per-step history + `iris job summary` preemptions + GCS `step-*` cadence);
  the harbor analyzer does NOT apply to training runs (no trial sidecars).
