---
name: datagen-launch-iris
description: Launch, monitor, and manually clean up a trajectory-generation (datagen) job on Marin's Iris TPU cluster via the OpenThoughts-Agent entrypoint. Use when asked to start, watch, rescue, or kill a datagen/tracegen run on Iris.
---

# datagen-launch-iris

> **📍 Iris orientation — read first.** Read the Iris **tools catalog** (`.agents/ops/iris/ops.md`) and the Iris **ops directory** (`.agents/ops/iris/` — `ops.md` for CoreWeave GPU, `ops.md` for TPU `marin`) for binding access/preamble/gotchas and the helper-script inventory. For **eval** jobs use **eval-agentic-launch-iris** instead.

## Required info (ask if missing)

1. `tasks` — `--tasks_input_path`: an **HF dataset id** (e.g. `DCAgent/exp_rpt_e2egit-v2`; the launcher `snapshot_download`s it and auto-explodes a `task_binary` parquet into task dirs) **or** a local tasks dir. Not both.
2. `slug` — short dataset name for the job name + HF repo (e.g. `e2egit-v2`).
3. Operating point — default **S1** (Qwen3.5-122B-A10B-FP8, 32k, v5p-8, single-host). Don't change configs unless asked.

## Prerequisites

- **Python 3.12 env** (the iris client writes the launcher's `sys.version_info` into the worker's `uv sync --python`): `source /Users/benjaminfeuer/miniconda3/etc/profile.d/conda.sh && conda activate otagent` (or call `/Users/benjaminfeuer/miniconda3/envs/otagent/bin/python`).
- **Secrets**: `source "$DC_AGENT_SECRET_ENV"` (`DAYTONA_API_KEY` for host-side snapshot pre-build, `HF_TOKEN` for upload, `MARIN_HMAC_*` for runai_streamer, `OPENAI_API_KEY` for LLM-judge datasets — see below). Also pass `--secrets-env <path>` so they reach the worker. Do not echo values.
- **LLM-judge datasets need `OPENAI_API_KEY` in the TRIAL env** (`laion/stackexchange-superuser-sandboxes-verified`, `laion/stackexchange-tezos-sandboxes-verified`, and any nemotron_gym `llm_judge`/`*_judge` set). Each task's `task.toml` carries `[verifier] env = { OPENAI_API_KEY = "${OPENAI_API_KEY}", JUDGE_MODEL = "${JUDGE_MODEL:-}" }`; harbor's verifier resolves that `${OPENAI_API_KEY}` **from the worker process env** (`harbor/src/harbor/verifier/verifier.py` `verify()` → `resolve_env_vars(merged_env)` → `environment.exec(env=…)`) and injects it into the Daytona verifier sandbox where the litellm/gpt-4o-mini judge runs. **The mechanism is already wired: nothing extra to pass** — `--secrets-env "$DC_AGENT_SECRET_ENV"` loads every KEY=VALUE from the secrets file (including `OPENAI_API_KEY`) into the iris worker's `env_vars` (`hpc/iris/env.py:_load_worker_secrets_env`, plus an explicit `OPENAI_API_KEY` passthrough at `_forward_launcher_env`), so the launch recipe below (which already passes `--secrets-env`) propagates the key end-to-end. **The `${OPENAI_API_KEY}` template is REQUIRED (no default)** — if the secrets file lacks it, harbor raises a ValueError at verify time (not a silent 0.0). Just make sure `OPENAI_API_KEY` is present in `$DC_AGENT_SECRET_ENV`.
- If a launch fails with `marin-iris client is too old`, run `git -C /Users/benjaminfeuer/Documents/marin pull --ff-only origin main` (editable install) — **not** `uv sync`.

## Launch

```bash
cd /Users/benjaminfeuer/Documents/OpenThoughts-Agent
source /Users/benjaminfeuer/miniconda3/etc/profile.d/conda.sh && conda activate otagent
source "${DC_AGENT_SECRET_ENV:?set DC_AGENT_SECRET_ENV to the secrets file first}"
TS=$(date +%Y%m%d-%H%M%S)
python data/cloud/launch_tracegen_iris.py \
  --harbor_config hpc/harbor_yaml/datagen/ctx32k_verified.yaml \
  --datagen_config hpc/datagen_yaml/qwen3_5_122b_a10b_fp8_runai_v5p8_s1.yaml \
  --tasks_input_path <HF-dataset-id | /abs/tasks/dir> \
  --tpu v5p-8 --preemptible \
  --n_concurrent 64 --n_attempts 1 --health_max_attempts 600 \
  --job_name "qwen3.5-122b-32k-<slug>-${TS}" \
  --secrets-env "$DC_AGENT_SECRET_ENV" \
  --upload_hf_repo penfever/<slug>-qwen3.5-122b-32k-traces \
  --no-wait
```

Flag notes:
- **Serve config resolves from `model_config/`** (commit `e792bfbb`): the launcher looks up the served model (from `--datagen_config`'s `engine.model` / `--model`) in `model_config/<org>/<slug>.yaml` and merges/forwards its `agent_kwargs` + applies serve intrinsics (`max_model_len`/`limit_mm`/`extra_args`) on the worker. `tp_size` + `harbor_config` are **ignored** on TPU (tp from chip count; harbor_config CLI-required). **Precedence: explicit CLI / `--datagen_config` values always win**; a model with no entry launches byte-unchanged (logged). Edit `model_config/<org>/<slug>.yaml`, never the generated `eval/configs/model_configs.yaml`.
- **OMIT `--gcs-output-dir` for the normal path.** The launcher auto-pins the job to the region with the most v5p-8 capacity and routes outputs to that region's co-located **single-region** bucket (`gs://marin-us-east5/ot-agent`, …; `output_bucket_for_region` in `hpc/iris/regions.py`). The registry records that URI, so rescue/analyze resolve it automatically (`hpc.iris.job_output_resolver`).
- **`--gcs-output-dir gs://marin-models-us/ot-agent` opts OUT of region pin + single-region routing** (forces multi-region bucket). Only pass to override — e.g. to escape a stuck-PENDING trap when one region's v5p-8 pool collapsed. Reverts outputs to pricier multi-region; prefer leaving the pin on.
- `ctx32k_verified.yaml` = verifier ON + `release_trial_payloads_in_memory` (bounds worker host-RAM so heavy/repo datasets don't OOM). Use the 32k config with the 32k S1 engine.
- `--health_max_attempts 600` mandatory (122B-FP8 cold compile ~60 min; default 100 ≈ 50 min kills the job before first serve).
- `--n_concurrent 64` = `max_num_seqs(64) × DP(1)`.
- Image `:tpu` at/after digest `ae085bc8` **auto-uploads** the HF repo on a clean (state-4) completion — no manual rescue needed.

After submit, confirm placement:
```bash
/Users/benjaminfeuer/Documents/marin/.venv/bin/iris --cluster=marin query \
  "SELECT job_id, state FROM jobs WHERE job_id='/benjaminfeuer/<job>'" -f csv
```
state 1=PENDING, 2=starting, 3=RUNNING, 4=SUCCEEDED, 5=FAILED, 6=KILLED.

## Monitor

```bash
/Users/benjaminfeuer/miniconda3/envs/otagent/bin/python \
  /Users/benjaminfeuer/Documents/OpenThoughts-Agent/scripts/iris/analyze_iris_harbor_job.py \
  /benjaminfeuer/<job> --output /tmp/<job>_history.md --resync
```
Read the `.json` sidecar (it paginates full history — don't eyeball `--tail`): `total_runtime_s`, `iris_preemption_count`, `cycles[]` (each with `did_serve`/`time_to_first_serve_s`), `serving_summary.gen_tps`/`.running` (n/mean/max), `non_empty_trials`/`total_trial_dirs` (productive rate), `harbor_exception_stats`. S1 baseline ≈ 400 mean / 1115 peak gen tok/s; short-task datasets (nl2bash, e2egit) run lower by nature — judge by productive trial rate, not tok/s alone.

**Did it auto-upload?** On a state-4 job from image `ae085bc8`+, check the repo exists before rescuing:
```bash
/Users/benjaminfeuer/miniconda3/envs/otagent/bin/python -c \
 "from huggingface_hub import HfApi; print(HfApi().dataset_info('penfever/<slug>-qwen3.5-122b-32k-traces').lastModified)"
```

**Traces → tool-calling SFT.** To turn the generated traces into SFT-ready rows (`role: tool` + structured `tool_calls`, not the lossy default `conversations` shape), use `harbor traces export --sft-format` → `.agents/projects/harbor/ops.md` § "SFT-ready traces with tool calling — `harbor traces export --sft-format`". For SFT decoded byte-exact from the served tokens instead (`--record_literal` jobs, TIS fidelity), see § "Literal-token trace datasets" in the same doc.

## Manual cleanup

**Kill** (only with explicit permission for a RUNNING/placed job):
```bash
/Users/benjaminfeuer/Documents/marin/.venv/bin/iris --cluster=marin job kill /benjaminfeuer/<job>
```

**Rescue banked traces** (any terminal job whose repo did NOT auto-create — killed, OOM, or pre-`ae085bc8` image). Rsync the GCS job dir local, then push:
```bash
source "${DC_AGENT_SECRET_ENV:?set DC_AGENT_SECRET_ENV to the secrets file first}"
OUT=$(/Users/benjaminfeuer/miniconda3/envs/otagent/bin/python -m hpc.iris.job_output_resolver <job> \
      --cluster /Users/benjaminfeuer/Documents/marin/lib/iris/config/marin.yaml)
mkdir -p /tmp/<job>_traces
gsutil -m rsync -r "$OUT/<job>/" /tmp/<job>_traces/
/Users/benjaminfeuer/miniconda3/envs/otagent/bin/python \
  /Users/benjaminfeuer/Documents/OpenThoughts-Agent/scripts/harbor/make_and_upload_trace_dataset.py \
  --job_dir /tmp/<job>_traces \
  --repo_id penfever/<slug>-qwen3.5-122b-32k-traces \
  --episodes last --filter none --skip_register
```
Resolve the RECORDED output prefix via `job_output_resolver` — never hardcode a bucket. `--skip_register` = upload only, no Supabase row. Repo is public.

**Daytona snapshot cap** — if a launch fails `SnapshotCapExceeded` on the shared `cli` org, delete ONLY broken (`MISSING`-state) `harbor__*` snapshots (never `ACTIVE` — may belong to running jobs):
```bash
source "${DC_AGENT_SECRET_ENV:?set DC_AGENT_SECRET_ENV to the secrets file first}"
/Users/benjaminfeuer/miniconda3/envs/otagent/bin/python - <<'PY'
import os
from hpc.snapshot_manager import _parse_org_arg, _SnapshotManager, list_snapshots
org=_parse_org_arg(f"cli={os.environ['DAYTONA_API_KEY']}")
mgr=_SnapshotManager([org]); client=mgr._client(org)
for snaps in list_snapshots([org]).values():
    for s in snaps:
        if s.name.startswith("harbor__") and s.state=="MISSING":
            client.snapshot.delete(client.snapshot.get(s.name)); print("deleted", s.name)
PY
```
Do NOT run broad `cleanup_unused_snapshots` against the shared `cli` org — it deletes by your task set and would remove teammates' ACTIVE snapshots. When the org is at cap with **0 MISSING** (all ACTIVE) but many idle `harbor__` leftovers, use the idle-gated reclaim via **utils-reclaim-stale-snapshots**: `daytona_snapshot_manager.py --name-prefix harbor__ --delete-stale` at the threshold in `.agents/projects/daytona/daytona.md`.

**Stuck PENDING** (no v5p-8 capacity): report it and relaunch UNPINNED (`--gcs-output-dir gs://marin-models-us/ot-agent` above). Kill the stuck submission only with permission.

## Current campaign: 131k A2 opencode (2026-07) — deltas from the 32k S1 default

Campaign specifics (dataset order, keep-3 state, per-arm status) live in the tracker: `/Users/benjaminfeuer/Documents/experiments/active/qwen3.5-122b-131k-datagen-opencode-iris/tracker.md`. Dated chronology: `~/Documents/agent_logs/2026-07-08_qwen3.5-122b-131k-datagen-opencode-iris_history.md`. Literal-trace decode/rescue reference: `.agents/projects/harbor/ops.md` (§ Literal-token trace datasets). Ingress topology (native `/proxy/t/*` capability-URL, token TTL, pinggy rollback): `.agents/ops/iris/ops.md`.

**Recipe deltas from the Launch block above:**
- `--datagen_config hpc/datagen_yaml/extra/qwen3_5_122b_a10b_fp8_runai_v5p8_131k_dp1_tp4_ep1_s32.yaml` (A2: TP4/DP1/EP-on/seqs32/131k), `--n_concurrent 32`.
- `--harbor_config hpc/harbor_yaml/datagen/opencode_ctx131k.yaml` — **FULL path required** (a bare `opencode_ctx131k.yaml` `FileNotFoundError`s on the worker — no config-dir fallback).
- `--agent opencode --record_literal` (literal-token capture; per-serve-unique log filenames so a preempt-resume can't clobber attempt-0's log).
- `--max-retries 200` — retry hard task failures. Iris separately tolerates 1,000 infrastructure preemptions per task. Tracegen launches also default `--max-task-failures 10`, so an isolated hard failure after several preemptions no longer aborts the whole resumable job while repeated failures still stop it. Override the cumulative guard explicitly only for bounded smokes. A resume **continues the same GCS serve dir** (one serve dir, rising task count) instead of restarting from task 1.
- repo naming `penfever/<slug>-qwen3.5-122b-131k-opencode-traces`.

**MODEL PATH GUARD (the #1 launch pitfall):** `--model gs://marin-models-us/ot-agent/models/Qwen/Qwen3.5-122B-A10B-FP8/` — the mirror, which streams via runai-streamer **direct-to-device (~0 local disk)**. **NEVER the bare HF id `Qwen/Qwen3.5-122B-A10B-FP8`** — that string is ONLY the uploader's `--served_model` provenance stamp; passing it as `--model` defeats streaming → vLLM `snapshot_download`s ~120GB → OOMs the 100GB worker disk → **startup hang (0 trials for hours, never self-heals)**. After launch, grep the job's log to confirm the baked command carries `--model gs://…`.

**Native ingress (pinggy retired):** add `--ingress_mode controller --ingress_host https://iris.oa.dev`. For the normal Marin TPU datagen path, the worker registers a LINK endpoint and mints locally because its controller is the Marin parent; Daytona receives `https://iris.oa.dev/proxy/t/<token>/otagent-<slug>/v1`. A CoreWeave-hosted serving job is different: submit it through the Marin meta-scheduler with `--target-cluster cw-us-east-02a`, wait for the endpoint mirror on Marin, and mint at Marin with the forwarded Marin login. Never send Daytona to `iris-cw-us-east-02a.oa.dev` or use a CoreWeave-peer-minted token. Route health: `curl -sk -w "%{http_code}" https://iris.oa.dev/proxy/t/badtoken/serve.nope/v1/models` → **401**.

**Liveness / wedge check — verify FRESHNESS, not just "activity present".** A RUNNING job can sit `state 3` with vLLM logs full of `running agent` lines yet be wedged — every line stamped at the SAME frozen timestamp. Judge by whether things ADVANCE over a short live window: (1) OUTER-dir GCS **trial-dir count grows** (sample, wait ~4–5 min, re-count); (2) harbor **`<done>/<total>` completed advances** / `result.json updated_at` is fresh; (3) vLLM emits **fresh** `chat/completions` `200 OK` + nonzero-and-moving `Running: N` (newest log TIMESTAMP recent, not frozen). Frozen on all three with an engine that served-then-stopped = confirmed wedge → kill+rescue+relaunch (standing kill authority). **Carve-out:** a job mid harbor GCS-`jobs_dir` **resume scan** after a preempt can be legitimately progress-frozen for up to ~6h WITH a *recent* engine-ready marker and NO prior serving on this attempt — that's NOT a wedge; don't kill (monitor-restore-iris §4c).

**Rescue vs RESUME policy (RESUME by default for sub-60% jobs):** when a job goes terminal short of completion, default to **RESUME** (relaunch the same arm → same baked `--job_name`/gs:// job dir → harbor continues the remaining tasks), NOT harvest a partial banked slice. **Rescue (banked-GCS → HF) ONLY when ≥60% complete** (`<done>/<total>` from the harbor `Mean:` line, or productive-trial dirs / total); below 60% a rescue just publishes a stub and burns the arm's identity.

**Harbor resume/export-push fix is NOT deployed in any current `:tpu` image:** the build's `uv pip install ".[datagen-tpu]"` resolved a **cached pre-fix `harbor==0.8.0` wheel**. Consequence: **every preemptible datagen job dies on its first preempt-resume export-push → banked-GCS rescue is the reliable harvester.** Real remedy (⚑ user decision): an image rebuild that busts the harbor wheel cache (bump harbor version / `HARBOR_COMMIT` + `--force-reinstall`, or fresh-from-GitHub source install), then VERIFY by grepping the installed `harbor/job.py` INSIDE the built image — see **build-tpu-image-iris**. **Fixing harbor code requires busting the cached wheel to take effect in an image rebuild** — the general lesson.

**Terminal-job triage — rescue vs BLOCKED (precheck before rescuing):**
- Worker in-job auto-upload lands **TEXT-ONLY** (the pinned `:tpu` predates the schema-pin fix) OR fails at **export-push** (harbor `FileExistsError` on preempt-resume — see caveat above) — both leave banked GCS trials + `logs/*_literal.jsonl` intact → **RESCUE** from GCS (see Manual cleanup) with `--served_model Qwen/Qwen3.5-122B-A10B-FP8`, verify `count_populated_literal_rows` ≈ correlation yield. "SUCCEEDED"/"repo exists" is NEVER proof of trainable literals — always check the true count.
- A job with **0 valid traces** (100% `steps:0` / `NonZeroAgentExitCodeError exit 127` = agent binary absent in the sandbox) is GARBAGE → mark **BLOCKED**, NOT rescuable, needs a full re-run after the sandbox-install fix. Spot-check a few trials' `result.json`/`exception.txt` before rescuing.

**Harbor editable guard:** the uploader imports harbor from `/Users/benjaminfeuer/Documents/harbor` — it MUST be on `main` (verify + `git checkout main && git pull` if drifted; `penfever/working` RETIRED) before any rescue, or the export crashes.

## Guardrails

- **Kill authority:** a HEALTHY (progressing) running job → NEVER kill without explicit permission. A CLEARLY-DOOMED / mis-launched job making 0 progress for hours that won't self-heal (bare-HF-id disk-full hang, exit-127 garbage, or a severed-Daytona zombie — frozen samples AND frozen harbor exception counters) MAY be killed + relaunched correctly WITHOUT asking (standing authorization, 2026-07-07); log it to the tracker.
- NEVER stop/restart/bounce a HEALTHY RUNNING job or the Iris cluster without explicit permission in the current thread.
- NEVER read/write GCS across regions (cost). Keep everything in the bucket-matched US region.
- Rescue + snapshot-MISSING cleanup are safe maintenance; killing a running job and broad snapshot pruning are not — confirm first.
