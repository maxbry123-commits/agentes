---
name: analyze-job-history-iris
description: Run the Iris harbor job-history analyzer (scripts/iris/analyze_iris_harbor_job.py) on a datagen/eval job and read its JSON sidecar for trustworthy throughput / preemption / productive-trial stats. Use whenever a status check needs REAL metrics (gen tok/s, cycles, non_empty rate, harbor exceptions) instead of an eyeballed log tail. It now queries the finelog log store directly (live ∪ GCS, deduped) — FAST (seconds, not minutes) and it ASSERTS completeness across all preempted attempts/generations, failing loud rather than returning fragments.
---

# analyze-job-history-iris

> **📍 Iris orientation — read first.** Before acting on anything in this skill, read the Iris **tools
> catalog** (`.agents/ops/iris/ops.md`) and the Iris **ops directory** (`.agents/ops/iris/` — the
> CoreWeave GPU particulars in `ops.md`, the TPU `marin` particulars in `ops.md`).
> They carry the binding access/preamble/gotchas and the helper-script inventory the steps below rely on.

`scripts/iris/analyze_iris_harbor_job.py` pulls an Iris job's **complete** log from the **finelog** store
(parquet, queried by SQL) — the live deployment **∪** the GCS archive, deduped on the monotonic `seq` — then
computes: §1 preemption count + time-to-preempt, §2 per-cycle trace progress (from harbor GCS output), §3
serving throughput. It writes a markdown report to `--output` and a **JSON sidecar** to `<output>.json`.
**Always read the sidecar with python — never eyeball the markdown.**

## This is now FAST and COMPLETE (the old "it's slow, page it" recipe is gone)

The analyzer used to paginate `iris job logs` by time windows — minutes per job, 15+ min on a multi-day job.
It now queries finelog directly: **seconds** for a training/small job, **~2–3 min** for a 60 h / 16M-row
datagen job. So:
- **You do NOT need the foreground-15-min-wait discipline, and you do NOT need a patient subagent.** Just run
  it inline. (A subagent is still fine for parallelism across many jobs — see the bottom — but the old
  "don't background it / don't yield" warnings no longer apply.)
- **Completeness is guaranteed or it fails loud.** It enumerates every attempt/generation from the controller
  SQLite (`task_attempts ⋈ tasks ⋈ jobs`), fetches live ∪ GCS, and asserts each attempt window is covered.
  Any uncovered window > `--max-coverage-gap-seconds` (default 600) **raises** and refuses to write a
  "successful" report. The sidecar carries `logs_complete` (bool) + `missing_windows` (list).

## Prerequisites (one-time)

1. **Run under the marin venv python** — it must import `finelog` / `rigging` / `duckdb`:
   `/Users/benjaminfeuer/Documents/marin/.venv/bin/python` (NOT the otagent env).
2. **IAP login for the live finelog half** (covers the recent, not-yet-archived "L0" tail — essential for
   RUNNING jobs). One-time, cached at `~/.config/marin/iap/marin.json`:
   ```bash
   OAUTHLIB_RELAX_TOKEN_SCOPE=1 /Users/benjaminfeuer/Documents/marin/.venv/bin/marin-login login marin
   ```
   (The `OAUTHLIB_RELAX_TOKEN_SCOPE=1` works around Google reordering the OAuth scopes — without it the login
   tracebacks at the final token-parse.) If the token expires, the analyzer's live fetch fails and the
   coverage check **fails loud** (it won't silently return the GCS-only fragment) — just re-run the login.

## Command

```bash
/Users/benjaminfeuer/Documents/marin/.venv/bin/python \
  /Users/benjaminfeuer/Documents/OpenThoughts-Agent/scripts/iris/analyze_iris_harbor_job.py \
  <job_id> --output /tmp/$(basename <job_id>)_history.md --resync
```

- `--resync` re-fetches; **omit it** to re-parse the cached merged log
  (`/tmp/iris_history_<job>.filtered.log` + `<...>.coverage.json`) instantly.
- `--max-coverage-gap-seconds N` (default 600) — the max allowed empty run inside an attempt window before
  it's a coverage failure. `--allow-incomplete` — opt out of the strict raise (records `logs_complete=false`
  + `missing_windows` and proceeds); use ONLY when you knowingly accept a fragment.
- **Cluster.** Default **marin/TPU**. For CoreWeave pass `--cluster cw-us-east-02a` (the finelog config name
  == the cluster name; it resolves `cw-us-east-02a` automatically). Still run under the **marin venv** python.
  **⚠ CoreWeave needs R2 archive creds, NOT IAP.** On cw the live half uses a k8s tunnel (no `marin-login`),
  but the archive half reads `s3://marin-na/finelog/cw-us-east-02a` (R2 — this literal is the historical store;
  the resolved root comes from `marin_prefix()`, see `.agents/ops/iris/ops.md` §rendezvous) — creds the Mac lacks, so the run
  crashes `FileNotFoundError: The specified bucket does not exist` unless you first source them from the
  `iris`-ns secret. **Procedure: `.agents/ops/iris/ops.md`.**
  **Also:** GPU-RL jobs have **no harbor trial sidecars**, so §2 is empty and most of the value is gone — for
  GPU-RL use **rl-job-health-deep-dive** instead. This analyzer is for **harbor-shaped jobs (datagen / agentic eval)**.
- **Completeness sanity:** the run prints `[enumerate] N attempt(s)`, `[merge] live=… + gcs=… -> deduped=…`,
  and `[coverage] COMPLETE` (or `INCOMPLETE` + the gaps). Confirm `logs_complete: true` in the sidecar before
  trusting the stats.

## Parse the sidecar (exact keys)

```bash
/Users/benjaminfeuer/Documents/marin/.venv/bin/python - /tmp/$(basename <job_id>)_history.md.json <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
g = d.get("serving_summary", {}).get("gen_tps", {}) or {}
r = d.get("serving_summary", {}).get("running", {}) or {}
cyc = d.get("cycles", []) or []
served = [c for c in cyc if c.get("did_serve")]
tfs = served[0]["time_to_first_serve_s"] if served else None
ne, tot = d.get("non_empty_trials"), d.get("total_trial_dirs")
rate = (ne / tot) if (ne is not None and tot) else None
exc = sorted((d.get("harbor_exception_stats") or {}).items(), key=lambda kv: -kv[1])[:5]
print(f"logs_complete    : {d.get('logs_complete')}  missing={len(d.get('missing_windows') or [])}")
print(f"runtime_h        : {round(d.get('total_runtime_s',0)/3600, 2)}")
print(f"preemptions      : {d.get('iris_preemption_count')}  (from_log={d.get('preempt_count_from_log')})")
print(f"state            : {d.get('state')}")
print(f"cycles           : total={len(cyc)} served={len(served)}")
print(f"t_first_serve_s  : {tfs}")
print(f"gen_tps          : n={g.get('n')} mean={round(g.get('mean',0),1)} peak={round(g.get('max',0),1)} median={round(g.get('median',0),1)}")
print(f"running          : mean={round(r.get('mean',0),1)} peak={round(r.get('max',0),1)}")
print(f"saturation_rate  : {d.get('serving_summary',{}).get('saturation_rate')}")
print(f"productive trials: {ne}/{tot} = {round(rate*100,1) if rate is not None else None}%")
print(f"harbor counts    : completed={d.get('harbor_n_completed')} errored={d.get('harbor_n_errored')} running={d.get('harbor_n_running')} pending={d.get('harbor_n_pending')} total={d.get('harbor_n_total_trials')}")
print(f"harbor_updated_at: {d.get('harbor_updated_at')}  (started {d.get('harbor_started_at')})")
print(f"top exceptions   : {exc}")
PY
```

**Check `logs_complete` first** — if it's `false`, the stats are computed over a fragment; investigate the
`missing_windows` (usually a stale IAP token → re-login) before trusting the numbers. The sidecar stores
**`total_runtime_s`** (seconds — divide by 3600), not `runtime_h`; `gen_tps`/`running` expose `max` (use as
"peak"), not `peak`; `harbor_exception_stats` is a `{name: count}` dict. S1 datagen baseline ≈ **gen mean 400
/ peak 1115** tok/s; short-task datasets run lower — judge health by the **productive trial rate**
(`non_empty/total`), not tok/s alone.

## ALSO report: mean reward + completed/total tasks (NOT in the sidecar)

Two fields the user always wants are **not** in the JSON sidecar — they live only on harbor's live TUI
**progress line** in the job logs, in the form `<completed>/<total> Mean: <reward>` (a quick `iris job logs`
tail — NOT the slow pager, fine to keep using):

```bash
/Users/benjaminfeuer/Documents/marin/.venv/bin/iris --cluster=marin job logs <job_id> --max-lines 8000 2>/dev/null \
  | grep -aoE '[0-9]+/[0-9]+ Mean: [-0-9.]+' | tail -1
# e.g. "11129/15713 Mean: 0.429"  ->  completed/total tasks = 11129/15713 (71% of dataset),  mean reward = 0.429
```

- **completed / total tasks** = the `N/M` — progress against the **whole dataset** (M is the dataset's task
  count). This is DIFFERENT from the sidecar's `non_empty_trials/total_trial_dirs` (the productive rate among
  *attempted* trials). Report both.
- **mean reward** = the `Mean: X` — the running mean verifier reward across completed trials.
- For a CoreWeave job use `--cluster cw-us-east-02a` (+ `KUBECONFIG=~/.kube/coreweave-iris-gpu`).
- Every analyzer report MUST include these two alongside the sidecar stats.

## Running many jobs / offloading to a subagent

It's fast now, so inline is usually fine. When sweeping SEVERAL jobs you can still offload to a subagent for
parallelism — but the prompt no longer needs the foreground-and-wait warnings. Use this template per job (or
list several):

> Run `analyze_iris_harbor_job.py` on `<job_id>` (cluster `marin`) **under the marin venv**:
> `/Users/benjaminfeuer/Documents/marin/.venv/bin/python /Users/benjaminfeuer/Documents/OpenThoughts-Agent/scripts/iris/analyze_iris_harbor_job.py <job_id> --output /tmp/<basename>_history.md --resync`.
> It queries finelog (live ∪ GCS) and takes seconds-to-~3min; it asserts completeness and FAILS LOUD on a gap
> (if it complains LIVE is unavailable, the IAP token expired — note it, don't paper over it). Then parse the
> sidecar `/tmp/<basename>_history.md.json` with python — confirm `logs_complete: true` — and report:
> `total_runtime_s`, `iris_preemption_count`, `cycles[].did_serve`/`time_to_first_serve_s`,
> `serving_summary.gen_tps.{n,mean,max}`, `serving_summary.running.{mean,max}`, `non_empty_trials`,
> `total_trial_dirs`, `harbor_exception_stats`, `harbor_updated_at`. ALSO run
> `iris --cluster=marin job logs <job_id> --max-lines 8000 | grep -aoE '[0-9]+/[0-9]+ Mean: [-0-9.]+' | tail -1`
> and report **mean reward** + **completed/total tasks** (NOT in the sidecar). Return a compact key:value
> report + a one-line health read. Do not paste raw markdown/logs.

A completed `<output>.json` with `logs_complete: true` means that job is done — re-parse it directly (no `--resync`).

## How completeness works (for when it fails)

- **Filter on the finelog `key` column** (the iris wire id incl. `:attempt`), NOT `source` (= the stream name
  `stdout`/`stderr`). `key LIKE '<job_or_coord>/%'` captures every task, every attempt, and (for an executor
  coordinator) every nested child generation at any depth.
- **Live ∪ GCS is mandatory:** the live finelog store evicts old segments (retention cap) to GCS, and the GCS
  archive lags the most recent (L0) segments by the compaction interval — so neither alone is complete for a
  multi-day job. The analyzer queries both and dedups on `seq`.
- A coverage `INCOMPLETE` almost always means the **IAP token expired** (live half empty → recent-L0 window
  uncovered). Re-run `marin-login login marin`. Genuine archive gaps are rare; if `--allow-incomplete` is ever
  needed, say so explicitly in the report.

## Related skills
- **monitor-cron-sweep-iris** / **monitor-job-tables** — the status sweeps that call this.
- **analyze-training-run-iris** — the Levanter/executor TRAINING equivalent (W&B step/gap, no harbor sidecars).
- **rl-job-health-deep-dive** — the GPU-RL equivalent (no harbor sidecars; uses the finelog).
