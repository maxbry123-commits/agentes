---
name: rl-standard-job-cleanup
description: >-
  Preserve + publish a finished STANDARD (non-agentic GRPO) SkyRL RL checkpoint — the Delphi/rlvr/dapo
  math-and-reasoning cells launched via rl-standard-launch-leonardo (raw sbatch of hpc/skyrl_standard/leonardo/*,
  logger=console, NO Harbor/Daytona/trace_jobs). Covers: cancel pending retries, pick the BEST checkpoint by
  the trailing-5 EMA of reward via `parse_skyrl_metrics.py --format standard` (chain-aware, capped at the
  latest saved step), flatten weights to repo root, secret-scan, `hf upload` (Leonardo sbatch-tunnel) to
  laion/<run>-<step>-<size>B with the size suffix DERIVED FROM THE EXPORTED WEIGHTS (never the base-model
  name), DB register (--training-type RL + cross-user FK pre-check) ONLY for DB-registerable cells, clean up,
  and fire the Delphi downstream eval suite on the post-RL ckpt (defers to eval-standard-launch §5b). The ONLY
  artifacts are the model + the metric CSVs/report + the tracker scores — there is NO trace dataset. Use when
  a standard/non-agentic GRPO RL run finishes and needs uploading + (maybe) registering. DISTINCT from
  rl-agentic-job-cleanup, which is the AGENTIC (Harbor/Daytona) path with a companion trace dataset.
---

> ⚠ **Do not add comments to YAMLs. Report your recommendations directly to the supervisor.**

# rl-standard-job-cleanup

Cleanup for a finished **standard (non-agentic) GRPO** SkyRL run on Leonardo. It publishes
**`laion/<run_name>-<step>-<size>B`** with root-level weights and metric CSVs/report; add a Supabase
`models` row only for DB-registerable series (§7).

**Not the agentic cleanup.** Standard GRPO has no `trace_jobs/`, `trainer_log.jsonl`, trial, or batch-error outputs.

## What this cleanup drops vs the agentic one
- **No training-trace dataset** (`make_and_upload_trace_dataset` / `penfever/<job>`) — no Harbor rollouts, no `trace_jobs/`. Omit the agentic "Training Traces" README section.
- **No `trial_stats.csv` / `batch_errors`** — per-trial `result.json` is agentic only.
- **No `trainer_log.jsonl`** — `logger=console`; the `.out` chain is canonical. Publish `metrics.csv`,
  `vllm_metrics.csv`, `report.md`, and `reward_plot.png`.

## Cross-cutting rules
- **`hf upload`, NEVER `hf upload-large-folder`** (deprecated stub + deadlocks on HF LFS 429s). `hf upload` is additive (safe to re-run; resumes from `.cache/huggingface/`). Never use `huggingface_hub.upload_folder()` without `delete_patterns=[]` — it clobbers files absent locally.
- **`--private` is a no-value flag** — default is PUBLIC; omit it.
- Run `parse_skyrl_metrics.py` from the **`otagent` conda env** (matplotlib/pandas; the RL uv venv lacks them).
- **Leonardo login-node killer (~100 s):** a login-node `hf upload` is SIGKILLed at ~100 s regardless of detach. **Use the sbatch+tunnel pattern** (`.agents/ops/leonardo/ops.md` → "Leonardo HF Upload — Use sbatch, NOT the Login Node"). The tunnel depends on the `~/.ssh/leonardo_daytona` step-ca cert (~12 h) — a fast publickey failure means refresh the cert.
- **GPFS hygiene:** never `find`/`du` on `$WORK`; locate the `.out` via `scontrol show job <id> -o` (`StdOut=`/`%Z`) or a depth-1 `ls`; `rm -rf` cleanup runs detached (no sizing first).
- **Run on a login node** (login02/03/04 — login01 false-drains).

## 0. Cancel pending retries
```bash
squeue -u $USER --format='%.18i %.90j %.8T' | grep <RUN_NAME>
scancel <retry_job_ids>
```

## 1. Locate the run dir + the FULL `.out` chain
Standard RL writes to `$WORK/rl_ckpts/<RUN_NAME>` (`$WORK=/leonardo_work/AIFAC_5C0_290/bfeuer00`):
```bash
WORK=/leonardo_work/AIFAC_5C0_290/bfeuer00
RUN_DIR=$WORK/rl_ckpts/<RUN_NAME>
ls -d $RUN_DIR/exports/global_step_*/        # HF-exportable checkpoints (every hf_save_interval steps)
cat $RUN_DIR/latest_ckpt_global_step.txt     # last saved step — the selection CAP
```
The `.out` files are `%x_%j.out` in the **sbatch CWD** — `hpc/skyrl_standard/leonardo/<JobName>_<jobid>.out` (standard RL has no `experiments/<job>/logs/` dir). A chain restart = one `.out` per link:
```bash
cd $WORK/code/OpenThoughts-Agent/hpc/skyrl_standard/leonardo
ls -lt *<RUN_NAME>*_*.out      # collect ALL chain links (sorted by jobid/time)
```

## 2. Pick the BEST checkpoint + emit the metrics — `parse_skyrl_metrics.py --format standard`
Computes trailing-5 `reward/avg_raw_reward` EMA (α=1/3), intersects on-disk exports, caps at the latest saved
step, and emits `metrics.csv`, `vllm_metrics.csv`, `report.md`, and `reward_plot.png`. Run from **otagent**.

**Tool-presence pre-check:** if `--format standard` is missing, sync only this file, never a full `git pull`:
```bash
cd $WORK/code/OpenThoughts-Agent
scripts/analysis/parse_skyrl_metrics.py --help 2>/dev/null | grep -q 'standard' || \
  grep -q "format" scripts/analysis/parse_skyrl_metrics.py || echo "MISSING --format standard"
# If missing, fetch JUST the tool (does NOT touch other live-applied edits):
git fetch origin penfever/working
git checkout origin/penfever/working -- scripts/analysis/parse_skyrl_metrics.py
```

The CLI takes one log and output folder, not individual `.out` files. Stage the real chain links in a clean folder,
excluding `*_rayw*.out` and `*_rayhead*.out`:
```bash
OUTLOGS=$WORK/rl_cleanup/<RUN_NAME>/outlogs
OUT=$WORK/rl_cleanup/<RUN_NAME>/metrics
mkdir -p $OUTLOGS
# Copy ALL real chain-link TRAINING .out logs (one per restart link) — NOT the _rayw*/_rayhead worker logs:
cd $WORK/code/OpenThoughts-Agent/hpc/skyrl_standard/leonardo
for f in *<RUN_NAME>*_*.out; do
  case "$f" in *_rayw*|*_rayhead*) continue;; esac
  cp "$f" $OUTLOGS/
done
ls $OUTLOGS/

/leonardo_work/AIFAC_5C0_290/bfeuer00/miniforge3/envs/otagent/bin/python \
  scripts/analysis/parse_skyrl_metrics.py \
  --format standard \
  --run_dir $RUN_DIR \
  --save_every 20 \
  $OUTLOGS \
  $OUT
```
- **`--save_every`** MUST equal the run's `trainer.hf_save_interval` (Delphi default **20**). Verify in the `.out` launch line (`trainer.hf_save_interval=…`). Selection excludes the first save and starts at `2*save_every`.
- **CHAIN-AWARE — stage ALL real `.out` links, not one.** A chain's first link(s) often have **0 train lines** (engine bring-up); a single mid-chain `.out` under-covers the EMA window and can pick the wrong step. First-seen-wins per step, so overlapping links are safe to include.
- The tool prints the EMA table + `CHOSEN STEP: <best>` and writes it into `report.md`. Record `BEST=<best>`; the export to publish is `$RUN_DIR/exports/global_step_<BEST>/policy/`.
- **NO STEP CHOSEN** (e.g. only `global_step_20` exists, or no reward lines parsed): inspect `report.md`'s EMA table; a scancelled-early run's only eligible ckpt may be the largest saved multiple of `save_every` ≤ cap — fall back to that and note it. Never publish the first save (`global_step_20`).

## 3. Flatten model files to the upload-dir ROOT
HF model files MUST sit at the base of the uploaded dir — not under `policy/`:
```bash
UPLOAD_DIR=$WORK/rl_cleanup/<RUN_NAME>/upload-<BEST>
mkdir -p $UPLOAD_DIR
cp $RUN_DIR/exports/global_step_<BEST>/policy/* $UPLOAD_DIR/
ls $UPLOAD_DIR/      # *.safetensors, config.json, tokenizer files all at root
```

## 4. Derive the size suffix from exported weights
The repo is `laion/<run_name>-<BEST>-<size>B`. Compute `<size>B` from `config.json` and safetensor parameters;
never parse it from the run or base-model name:
```bash
/leonardo_work/AIFAC_5C0_290/bfeuer00/miniforge3/envs/otagent/bin/python - "$UPLOAD_DIR" <<'PY'
import json, sys, glob, os
d = sys.argv[1]
cfg = json.load(open(os.path.join(d, "config.json")))
H = cfg.get("hidden_size"); L = cfg.get("num_hidden_layers"); V = cfg.get("vocab_size")
# 1) Exact: sum param counts from the safetensors index (preferred).
idx = glob.glob(os.path.join(d, "*.safetensors.index.json"))
total = None
if idx:
    wm = json.load(open(idx[0])).get("metadata", {})
    total = wm.get("total_parameters") or wm.get("total_size")  # total_size = BYTES, not params
    if total and "total_parameters" not in wm:
        total = None  # only had byte size; fall through to header sum
if total is None:
    # Sum tensor numels from each shard header (no torch load needed).
    import struct
    total = 0
    for f in glob.glob(os.path.join(d, "*.safetensors")):
        with open(f, "rb") as fh:
            n = struct.unpack("<Q", fh.read(8))[0]
            hdr = json.loads(fh.read(n))
        for name, meta in hdr.items():
            if name == "__metadata__": continue
            shp = meta.get("shape", [])
            cnt = 1
            for s in shp: cnt *= s
            total += cnt
# 2) Cross-check with the transformer estimate 12*L*H^2 + embeddings(2*V*H).
est = 12 * L * H * H + 2 * (V or 0) * H if (H and L) else None
print(f"config: hidden_size={H} layers={L} vocab={V}")
print(f"summed params = {total/1e9:.2f}B" if total else "summed params = (unknown)")
if est: print(f"estimate 12*L*H^2 + 2*V*H = {est/1e9:.2f}B (sanity cross-check)")
b = total or est
print(f"\nSIZE SUFFIX => {round(b/1e9)}B  (repo: laion/<run_name>-<BEST>-{round(b/1e9)}B)")
PY
```
Use summed parameters; the estimate is a cross-check. If they differ by >~15%, prefer summed and note it. Round to
the nearest whole G (9.7B → `10B`).

## 5. Copy the launch config + scan for secrets
```bash
cp $WORK/code/OpenThoughts-Agent/hpc/skyrl_standard/leonardo/run_delphi_math_rl.sh   $UPLOAD_DIR/rl_run_script.sh 2>/dev/null
cp $WORK/code/OpenThoughts-Agent/hpc/skyrl_standard/leonardo/sbatch_delphi_math_rl.sh $UPLOAD_DIR/rl_sbatch.sh    2>/dev/null
trufflehog filesystem $UPLOAD_DIR --no-update    # if installed; else the grep fallback:
grep -rIE '(sk-[a-zA-Z0-9]{20,}|AKIA[0-9A-Z]{16}|ghp_[a-zA-Z0-9]{36}|hf_[a-zA-Z0-9]{34}|eyJ[a-zA-Z0-9._-]+)' $UPLOAD_DIR
```
Remove/redact anything found before upload (HF runs TruffleHog post-upload; catch it first).

## 6. Stage the metrics alongside the model, then upload — `laion/<run_name>-<BEST>-<size>B`
Fold metric outputs into the upload dir (runs are `WANDB_MODE=offline`, so these are the only persistent record):
```bash
mkdir -p $UPLOAD_DIR/training_logs
cp $OUT/metrics.csv $OUT/vllm_metrics.csv $OUT/report.md $OUT/reward_plot.png $UPLOAD_DIR/training_logs/ 2>/dev/null
cp $WORK/code/OpenThoughts-Agent/hpc/skyrl_standard/leonardo/<JobName>_*.out      $UPLOAD_DIR/training_logs/    2>/dev/null
```
Upload via the **Leonardo sbatch-tunnel** (NOT a login-node `hf upload` — dies at ~100 s). Use the sbatch
template in `.agents/ops/leonardo/ops.md` ("sbatch template for HF upload"); point `cd` at `$UPLOAD_DIR` and
the command at:
```bash
$CMD_PREFIX /leonardo_work/AIFAC_5C0_290/bfeuer00/miniforge3/envs/otagent/bin/hf upload \
    laion/<run_name>-<BEST>-<size>B . . --repo-type=model
```

## 7. Register in the DB (`--training-type RL`) — ONLY if the series is DB-registerable
**Confirm the cell's series is DB-registerable BEFORE registering.** Several standard-RL series are
HF-upload-only (the Delphi scaling-laws RL cells, like the SFT grid). **If it's ambiguous, STOP and flag — do
NOT auto-register a no-DB series** (it pollutes the registry; artifacts are consumed by an eval grid). Honor
`enable_db_registration: false` and documented no-DB series (`crud-otagent-supabase` → "Per-series exceptions").

**Base model (`--base-model`)** = the checkpoint the RL trained FROM — the sbatch/run-script `MODEL_PATH`
(read from the `.out` launch line `trainer.policy.model.path=…` or the sbatch `MODEL_PATH=` token), e.g.
`laion/delphi-1e21-…-sft`. `--base-model` resolves to the `base_model_id` self-FK — it must name an
already-registered `models` row (register/point it first if not, per `crud-otagent-supabase`).

Standard GRPO does not auto-push a canonical `laion/<run>` duplicate, so there's usually no auto-row to
delete. **Still run the cross-user FK pre-check** before any delete/mutate; restrict writes to rows you own:
```python
other_users_fk = (c.table("sandbox_jobs").select("id,username,model_id")
    .eq("model_id", stray_row_id).neq("username", os.environ.get("USER","bfeuer00")).execute())
if other_users_fk.data:
    print(f"SKIPPING delete — {len(other_users_fk.data)} other-user rows FK'd; surface + leave it.")
```
Then register (`--training-type RL` REQUIRED — defaults to SFT):
```bash
python scripts/database/manual_db_push.py \
  --hf-model-id laion/<run_name>-<BEST>-<size>B \
  --base-model laion/delphi-…-sft \
  --dataset-name <rlvr_math|gsm8k|aime|…> \
  --training-type RL
```

## 8. Clean up the run dir
After upload and applicable DB registration are confirmed on HF, free disk. Use detached `rm -rf`; never `du` or
`find` first. Verify inode reclaim afterward
(`jutil project dataquota -p <project>` / `df -i`):
```bash
nohup rm -rf $WORK/rl_ckpts/<RUN_NAME> >/dev/null 2>&1 &   # detached; keep $UPLOAD_DIR until HF verified
```
Keep `$WORK/rl_cleanup/<RUN_NAME>/` (staging + metrics) until you've confirmed the HF repo lists the
weights + `training_logs/`, then remove it too.

## 9. Fire the Delphi eval suite on the post-RL checkpoint
Score the uploaded ckpt on the lab's fixed downstream suite. **DEFERS to `eval-standard-launch` → "§5b.
Evaluate a (post-RL) checkpoint on the Delphi eval suite"** — do not re-document it here. That section runs
the canonical `delphi_eval.sbatch` (MATH500 / AIME24 10-seed / gsm8k, pass@1, temp 0.7, delphi_v0 template,
STAGE=`rl`) on Leonardo against the uploaded `laion/` repo. One-line invocation (pre-cache the repo on the
login node first, per that skill §3):
```bash
RUN=<run_name>-<BEST>-<size>B   # the repo §6 just published
sbatch --job-name="delphi-eval-$RUN" \
  /leonardo_work/AIFAC_5C0_290/bfeuer00/experiments/delphi-eval/delphi_eval.sbatch laion/$RUN $RUN rl
```
Add the submitted row to **`main_rl_evals/SCORES.md`** (`🚀 eval submitted` + job id); harvest via
`eval-standard-cleanup`. **HF-upload-only, NEVER DB** — same series rule as §7.
