---
name: datagen-job-cleanup
description: >-
  Post-run cleanup for a datagen (trace-generation) job on Iris/CoreWeave or an HPC cluster
  (Jupiter/Leonardo/Perlmutter): get the generated traces onto HF (penfever org) and free temporary
  disk. There is NO model checkpoint — the
  artifact is the trace dataset. Covers the TIMEOUT-strands-traces gotcha (uploads silently never run),
  the ONE-level trace_jobs nesting (vs RL's double-nest), the real-vs-failed sanity check (avg_turns ≈ 1.0
  = dead run, don't upload), the otagent-env uploader, the non-empty HF verify, and safe disk cleanup
  (one-off task dirs vs shared canonical tasks; leave Daytona snapshots). Use when a datagen/trace job
  finishes (COMPLETED or TIMEOUT) and its traces need uploading + verifying, or when consolidating a
  chunked datagen run. Distinct from RL/SFT cleanup (those publish a model checkpoint).
---

# datagen-job-cleanup

After a datagen (trace-generation) job terminates, follow these steps to get the traces onto HF and free
disk. Unlike RL/SFT there is no model checkpoint — the artifact is the trace dataset.

## 0. Recognize the common case: TIMEOUT stranded the traces
Datagen jobs run to a wall-clock `--time_limit`; on TIMEOUT, Harbor's terminal trace-upload step is killed
mid-run, leaving completed trials on disk but **no upload**. A clean COMPLETED exit usually uploads
automatically; a TIMEOUT almost never does. Either way, do NOT assume the upload happened — verify (step 4).
```bash
sacct -j <jobid> -X --format=JobID,JobName%55,State,Elapsed,End -n
```

## 1. Locate the trace_jobs dir (ONE-level nesting for datagen)
Datagen writes to `<run_dir>/trace_jobs/<inner_run_name>/<task>__<id>/` — a SINGLE level of nesting under
`trace_jobs/`, NOT the double-nest `<run>/<run>/trace_jobs` of the RL path. The `--job_dir` you pass to the
uploader must be the dir that DIRECTLY CONTAINS the `<task>__<id>` trial dirs, i.e. `trace_jobs/<inner_run_name>`:
```bash
# Direct-ssh launches land under experiments/; --experiments_dir launches under ot-baf.
RUN=/e/scratch/jureap59/feuer1/OpenThoughts-Agent/experiments/<job_name>   # or /e/data1/.../ot-baf/<job_name>
INNER=$(ls -d $RUN/trace_jobs/*/ 2>/dev/null | head -1); echo "$INNER"
```

### Iris/CoreWeave durable S3 layout

`--s3-output-dir` is a campaign/root prefix, not a per-job destination. The
shared Iris output resolver appends the Iris job name and routes Harbor to:

```text
<s3-output-root>/<iris-job>/trace_jobs/<harbor-job>/<trial>/result.json
```

For example, launch with
`--s3-output-dir s3://marin-us-east-02a/iris/<campaign>`, not with a URI ending
in `$JOB`. Eval and datagen both use the `IrisOutputPaths` plan in
`hpc/iris/outputs.py`; do not reproduce this path construction in a launcher.

Run S3 cleanup inside a `cw-rno2a` Iris worker so the transfer uses cluster
credentials and bandwidth:

```bash
python scripts/harbor/cleanup_coreweave_datagen_s3.py \
  --target '<job>|s3://marin-us-east-02a/iris/<campaign>/<job>|penfever/<repo>'
```

The downloader lists the prefix once, downloads with bounded parallelism and
adaptive S3 retries, applies the realness gate, uploads in one Hub commit,
reloads the published train split, and removes only its worker-local temporary
copy. It never deletes the durable S3 source. Repeat `--target` to process
several completed jobs serially and idempotently.

### Consolidate named relaunches without dropping retries

When a dataset row has several independently launched `-rN` attempts, give
their durable `trial_uri` values as a comma-separated prefix list in one
target. The cleanup tool creates a separate local run directory for each
prefix, retains each run's `config.json`, then exports their trials into the
one requested Hub repository. Repeated task IDs are intentional independent
samples and are retained; only exact copied artifacts must not be counted
twice. Do not point the tool at only the newest retry.

```bash
python scripts/harbor/cleanup_coreweave_datagen_s3.py \
  --target '<dataset>|s3://.../first-attempt,s3://.../retry-r2|penfever/<dataset>-traces'
```

`--no_literal_tokens`, `--single_commit`, and `--skip_register` are cleanup
tool defaults; pass only `--target` arguments to this wrapper. Its reusable,
git-tracked implementation is
`scripts/harbor/cleanup_coreweave_datagen_s3.py`.

Jobs launched before the shared-path fix may have the malformed rescue layout
`<root>/<iris-job>/<harbor-job>/<trial>` with no `trace_jobs` component. The
cleanup tool recognizes this existing layout from `result.json` parents, but
new launchers must only write the canonical layout above.

## 2. Sanity-check the trials are REAL before uploading
A served `/v1/models` healthcheck does NOT mean generation worked. Compute avg turn count + exception
rate: if avg turns ≈ 1.0, the run is near-total failure (e.g. endpoint healthy + many `result.json`, but
every trial a 1-turn `InternalServerError` from a dead EngineCore). A real run has multi-step trajectories
(turns > 1) + a tolerable exception rate (tezos datagen ~20-25% AgentTimeout is normal).
```bash
# trajectory.json is a dict with a "steps" list; turns ≈ len(steps).
$OTAGENT_PY - <<'PY'
import json, glob, os, statistics
inner = os.environ["INNER"]
dirs = glob.glob(os.path.join(inner, "*__*/"))
turns, exc = [], 0
for d in dirs:
    tj = os.path.join(d, "agent", "trajectory.json")
    if os.path.exists(tj):
        t = json.load(open(tj))
        turns.append(len(t.get("steps", [])) if isinstance(t, dict) else len(t))
    r = os.path.join(d, "result.json")
    if os.path.exists(r):
        if (json.load(open(r)).get("exception_info") or {}).get("exception_type"): exc += 1
print(f"trials={len(dirs)} avg_turns={statistics.mean(turns):.2f} exceptions={exc}" if turns else "no trajectories")
PY
```
If avg_turns ≈ 1.0 → the run failed; do NOT upload. Diagnose instead (read a trial's `exception.txt` + the
`_vllm.log` for the engine-side error) and write an agent_log; the traces are not worth keeping.

## 3. Upload the traces to HF penfever org
From the `otagent` conda env — the uploader needs `google.cloud.storage` + matplotlib, which `envs/rl` lacks:
```bash
# otagent env, source secrets first. $INNER = the dir DIRECTLY containing the <task>__<id> trial dirs.
python -m scripts.harbor.make_and_upload_trace_dataset \
  --job_dir "$INNER" \
  --repo_id penfever/<descriptive-name> \
  --episodes last \
  --served_model <the exact served model ref> \   # required for decodable literals
  --include_literal_tokens \                       # REQUIRE literals (fail loud if 0 bind)
  --single_commit                                  # ONE HF commit — avoids the 128-commit/hr 429 on big sets
```
Default to the `penfever/` org + `--episodes last`. For a chunked launch, upload each chunk's trace_jobs to
its own `_chunk{i}` repo. Public by default (`feedback_hf_public_default`).

**Literals are AUTO-INCLUDED when present (no flag needed).** The uploader favors the durable
`literal.jsonl`: it auto-discovers the sibling `<experiments_dir>/logs/*_literal.jsonl` (searching
`--job_dir` and a few parents) and correlates the RecordProxy records into the trajectory step metrics so
the exported dataset carries the trainable `prompt_token_ids` / `completion_token_ids` / `logprobs`
columns. Requirements + knobs:
- **`--job_dir` must sit inside the experiments-dir tree** so the parent-walk reaches `…/logs/`. `$INNER`
  qualifies as long as the local run dir still has its sibling `logs/` (local runs do).
- **⚠ Resolve the recorded output bucket — NEVER hardcode `gs://marin-models-{us,eu}`.** Jobs pin to a
  co-located **single-region** bucket (`gs://marin-us-east5`, …); older jobs are on the multi-region mirror.
  Resolve each job's ACTUAL recorded OUTER prefix (registry-first, iris-fallback):
  ```bash
  JOB=<job_name>
  OUT=$(/Users/benjaminfeuer/miniconda3/envs/otagent/bin/python -m hpc.iris.job_output_resolver "$JOB" \
        --cluster /Users/benjaminfeuer/Documents/marin/lib/iris/config/marin.yaml)   # e.g. gs://marin-us-east5/ot-agent/<job>
  mkdir -p /tmp/${JOB}_traces
  gsutil -m rsync -r "$OUT/" /tmp/${JOB}_traces/     # OUTER <job>/ — carries logs/*_literal.jsonl
  ```
  The resolver returns the correct bucket for both single- and multi-region jobs (`--cluster` is only
  consulted for the iris fallback when the job isn't in the local registry).
- **⚠ gs:// iris rescue — the INNER `<job>/` is the `--job_dir`, NOT the outer rescue root.** You rsync the
  **OUTER** `$OUT/` → `/tmp/<job>_traces` so `logs/*_literal.jsonl` rides along, but the trial dirs sit one
  level down at `/tmp/<job>_traces/<job>/<trial>`, so pass `--job_dir **/tmp/<job>_traces/<job>**` (the
  inner subdir that DIRECTLY contains the `<task>__<id>` dirs). Passing the outer `/tmp/<job>_traces` still
  uploads TEXT rows, but the extra `<job>/` prefix makes **0 trials bind → silent text-only dataset** (with
  `--include_literal_tokens` it fails loud instead). Also: `gsutil rsync` needs the local dest to EXIST —
  `mkdir -p` before the rsync.
- **⚠ Big datasets → add `--single_commit` (HF 128-commits/hour cap).** ~1 commit per shard; a
  multi-thousand-row set + any re-attempt blows past HF's **128 repo-commits/hour** limit → `429` mid-push
  → a partial dataset. `--single_commit` pushes the whole dataset in ONE commit → never trips the limit.
  (If you already 429'd, the repo may be partial/empty; wait ~1h for the window to reset, then re-run with
  `--single_commit`.)
- **Correlator is RAM-heavy — one upload at a time on a RAM-limited host.** Correlation holds ALL parsed
  records (token ids) in memory for chain-reconstruction; a big literal file (e.g. 1.5 GB) can flood a
  36 GB Mac. Run ONE upload at a time, never two concurrent. If one-at-a-time OOMs, offload to a bigger box
  or drop `messages` from records after `reconstruct_chains`.
- A job with **no** `literal.jsonl` exports text-only, byte-identical to before (parity).
- `--no_literal_tokens` forces text-only even when a `literal.jsonl` is present.
- `--include_literal_tokens` means REQUIRE: fails loud if literals are expected but none are found.
- The uploader FAILS LOUD if a `literal.jsonl` is present but 0 trials bind (a regression, not a valid
  dataset).
- **Pass `--served_model` on any literal upload.** Token-id columns are only decodable with the EXACT
  tokenizer the engine served (a same-family tokenizer decodes word tokens to garbage); the uploader stamps
  the model ref into `tokenizer_provenance.json` + the dataset-card README. For the opencode-131k campaign:
  `--served_model Qwen/Qwen3.5-122B-A10B-FP8` (or `gs://marin-models-us/ot-agent/models/Qwen/Qwen3.5-122B-A10B-FP8/`
  — storage root via `marin_prefix()`, see `.agents/ops/iris/ops.md` §rendezvous, don't
  hardcode the region bucket).
- **Schema-pin (OT-Agent `7c978b78`):** the exporter pins the literal token columns to an explicit nested
  type per shard. Datasets uploaded BEFORE `7c978b78` are degraded (under-populated literal yield, shards
  with no token columns, `load_dataset` `CastError`) — **re-rescue them to recover full yield.** Full
  reference (decoding, tokenizer provenance, re-rescue, literals→SFT): **`.agents/projects/harbor/ops.md`**
  (§ Literal-token trace datasets).

### Diagnose significant score/trajectory/export gaps

If numeric-result counts, `agent/trajectory.json` counts, and SFT-exported row
counts differ materially, do not infer the cause from aggregate yield. Run the
git-tracked analyzer against every retry prefix or local Harbor job directory:

```bash
python -m scripts.harbor.analyze_sft_export_gaps \
  --dataset s3://.../first-attempt \
  --dataset s3://.../retry-r2 \
  --output /tmp/<dataset>-sft-export-gap-analysis.json

# Local equivalent:
python -m scripts.harbor.analyze_sft_export_gaps \
  --dataset "$INNER" \
  --output /tmp/<dataset>-sft-export-gap-analysis.json
```

For S3 inputs, run inside a `cw-rno2a` Iris worker with the normal object-store
credentials so downloads remain in-region. The analyzer joins job-level reward
buckets to per-trial `result.json` and trajectory artifacts, preserves retry/run
provenance, and invokes the same conversation collection and dataset conversion
path as the exporter. Its JSON report accounts for both boundaries separately:

- numeric result identity → trial directory → `agent/trajectory.json`;
- `agent/trajectory.json` → collected conversation → SFT-ready dataset row.

Use the mutually exclusive reason counts and per-trial evidence to remediate
recoverable failures before uploading. Preserve the report in the experiment
artifacts or an `agent_logs/` escalation when the gap cannot be repaired. Do not
declare the numeric gate cleared from an aggregate counter until this join is
consistent.

## 4. Verify the HF dataset is non-empty
The repo may exist as a 0-row shell (a prior failed/partial upload, or Harbor pre-creating it); an existing
repo is NOT proof of success. Confirm row count:
```bash
curl -s -H "Authorization: Bearer $HF_TOKEN" \
  "https://huggingface.co/api/datasets/penfever/<descriptive-name>" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print('files:', len(d.get('siblings',[])), 'lastMod:', d.get('lastModified'))"
```
The uploader's own "Generating train split: N examples" line is ground truth — N must match the real
(non-1-turn) trial count from step 2. Zero files / 0 rows = the upload did not land; re-run step 3.

> **⚠ Re-uploading over a repo that had a prior TEXT-ONLY upload.** A leftover `train-00000-of-00001.parquet`
> from the earlier text-only push has a **no-token schema** that can MASK the new token-bearing shards →
> `count_populated_literal_rows` reads **0** even though the re-upload landed. If a post-upload verify shows
> 0 populated literals but the uploader logged a good `Literal yield`, **delete the stale text-only
> parquet(s)** (`huggingface_hub.HfApi().delete_file`) and re-verify. Cleaner: re-upload to a **fresh repo
> id** to avoid stale-shard masking entirely.

**Also verify the literal columns landed (jobs run with `--record_literal`).** The uploader prints a
`[trace-export] Literal yield: X/Y trials …` line — X should be > 0. Confirm in the pushed dataset:
```python
import datasets
from scripts.harbor.make_and_upload_trace_dataset import count_populated_literal_rows
ds = datasets.load_dataset("penfever/<descriptive-name>", split="train")
print("rows w/ literals:", count_populated_literal_rows(ds.data.table))   # must be > 0 for a --record_literal job
```
0 populated rows on a `--record_literal` job = the literals dropped — re-run step 3 with the correct
`--job_dir` (must reach the sibling `logs/`), or pass `--literal_log <gs://…/logs/<slug>_literal.jsonl>`.

## 5. Clean up disk (only after step 4 confirms the upload)
- **Remove the run/experiments dir** (trace_jobs is the bulk — tens of GB for a full tezos run):
  `rm -rf $RUN`
- **Remove the task directory IF it was a one-off / temp set** created just for this run — e.g. the symlink
  subsets under `…/ot-baf/tmp_tasks/<name>` made for a chunking smoke test, or a
  `scripts.datagen.extract_tasks_from_parquet` output you won't reuse. Do NOT delete the shared canonical
  task dirs under `/e/data1/datasets/playground/ot/tasks/<benchmark>` — reused across runs.
  ```bash
  rm -rf /e/data1/datasets/playground/ot-baf/tmp_tasks/<one-off-name>   # only if one-off
  ```
- **Daytona snapshots**: leave them — keyed by task-environment hash and shared across runs, so per-run
  deletion is unsafe.

---

## Operating notes

- **Auto-advance the MiniMax-M2.7 131k queue without asking between datasets** (96-row queue; cycle is
  mechanical). Tracker = `experiments/active/datagen/minimax-m2.7-tt/tracker.md`. Per-dataset cycle:
  extract tasks → launch chunks (`chunk_size 500`, `--chunk_array_max 5`, single-node, verifier-ON) → wait
  ALL chunks COMPLETE (validate via sacct, not empty squeue) → consolidate `_chunk{N}` via
  `join_hf_repos.py` + **verify row count == sum, each chunk near-full, no run_id gaps, realness
  (avg_turns>1)** → DELETE chunk repos (only after consolidated verified) → clean local dirs → launch next
  row. Target repo: `penfever/<source-basename>-minimax-m27-131k-traces`. **Only hard auto-skip =
  oversized-extraction rows** (≫10k rows busting the inode budget, e.g. knowledge-mcqa 616k) → ask.
  Snapshots: do NOT reclaim per-dataset (shared envs); track cumulative tally vs the org cap (see daytona
  doc). The 3h cron is the natural driver.
- **LLM-as-judge verifier rows (`openai/gpt-4o-mini`) can be silently reward-dead** (all 0.0) if
  `OPENAI_API_KEY` is invalid/revoked → judge 401 → reward defaults 0.0 while traces are genuine
  (`avg_turns` healthy). Tell at consolidation: `verifier_output` has `judge API error … 401` on ~all rows.
  **Check the REWARD DISTRIBUTION at consolidation, not just avg_turns.** Rows generated before the
  2026-06-11 fix (e.g. #22) stay reward-dead unless re-scored. User precedent: accept reward-dead rows as
  turns-only SFT data + advance (record the caveat in the tracker row). Test a key:
  `curl …/v1/chat/completions -H "Authorization: Bearer $OPENAI_API_KEY" …` → expect 200.
