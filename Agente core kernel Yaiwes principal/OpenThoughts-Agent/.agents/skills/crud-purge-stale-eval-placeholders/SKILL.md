---
name: crud-purge-stale-eval-placeholders
description: >-
  Safely purge stale, never-populated `sandbox_jobs` placeholder rows (eval launches that
  died/stalled before scoring) from the OT-Agent Supabase registry. Removes ONLY dead
  `Pending`/`Started` rows WE OWN that are >36h old with null `metrics`/`stats`/`ended_at`,
  via the mandatory cross-user FK-safety pre-check + the REQUIRED grandchild→child→job
  cascade delete (`sandbox_trial_model_usage` → `sandbox_trials` → `sandbox_jobs`). Other
  users' stale rows are REPORTED, never deleted. DRY-RUN first, then delete, then re-read.
  Use when the registry is clogged with dead placeholder eval rows, when a sweep flags
  stale Pending/Started/"Running" eval entries, or when the eval listener's dedup is
  mis-firing on dead rows. The general CRUD/read/aggregation skill is `crud-otagent-supabase`.
---

# crud-purge-stale-eval-placeholders

A **guardrailed DELETE** of dead placeholder `sandbox_jobs` rows left when an eval launch dies/stalls before it scores. Every launch creates a placeholder (`Pending`→`Started`) before a result exists; if the run dies, the placeholder remains (no `Finished`, no `metrics`, no `stats`), clogging the table and the eval listener's dedup. Removes **only** the dead placeholders we own.

> **This is a DELETE on a shared table. The cross-user FK-safety pre-check (§2) and the cascade (§3) are both MANDATORY — a plain `sandbox_jobs` delete FK-fails Postgres `23503`, and skipping the ownership check can wipe another user's rows. DRY-RUN first, then delete, then re-read.**

## 0. Connect (run LOCALLY)

Run from the Mac with the `otagent` env; source the local secrets (sets `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY`).

```bash
cd /Users/benjaminfeuer/Documents
set -a; source "${DC_AGENT_SECRET_ENV:?set DC_AGENT_SECRET_ENV to the secrets file first}"; set +a
/Users/benjaminfeuer/miniconda3/envs/otagent/bin/python - <<'PY'
import os
from supabase import create_client
c = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"])
PY
```

- `SUPABASE_SERVICE_ROLE_KEY` bypasses RLS (full read/write) — nothing stops you mutating other users' rows, which is why §2 is mandatory.
- Schema DDL lives at `/Users/benjaminfeuer/Documents/OpenThoughts-Agent/schema/` — read `sandbox_jobs` / `sandbox_trials` / `sandbox_trial_model_usage` when unsure of a column.

## The `metrics` field has TWO shapes — always extract via the helper

`metrics` is jsonb and appears as **either** a list of `{"name","value"}` dicts **or** a plain dict. The qualifier (§1) tests `metrics is None` via this shape-robust helper — never via `metrics["accuracy"]` directly:

```python
def get_metric(metrics, key="accuracy"):   # key: "accuracy" or "accuracy_stderr"
    if metrics is None: return None
    if isinstance(metrics, dict):           # {"accuracy": 0.25, ...}
        return metrics.get(key)
    if isinstance(metrics, list):           # [{"name":"accuracy","value":0.25}, ...]
        for e in metrics:
            if isinstance(e, dict):
                if e.get("name") == key:    return e.get("value")
                if e.get(key) is not None:  return e.get(key)
    return None
```

## 1. What makes a row "stale and removable"

**Schema facts that drive the filter** (verified against `schema/sandbox_jobs`):
- Timestamps are `created_at` / `started_at` / `ended_at` / `submitted_at` — **there is NO `updated_at`.** Use `created_at` for absolute age, and `started_at` (set when the job leaves `Pending`) as the secondary recency gate.
- **`n_trials` is the PLANNED trial count from config, NOT progress** — a brand-new placeholder already has `n_trials=128`. Do **NOT** read `n_trials` as a "populated" signal.
- The real "never populated" signals are **`metrics IS NULL`** (no score) **AND `stats IS NULL`** (no per-trial progress). Empirically every `Pending`/`Started` row has BOTH null; a live job that had begun scoring would have a non-null `stats`. (`ended_at` is also always null for these.)
- `job_status` enum: `Pending` / `Started` / `Finished` (+ failure states). There is no literal `"Running"` status — a stale "running" entry is a stale **`Started`** row.

**A row qualifies for removal iff ALL hold:**
1. `job_status IN ('Pending','Started')` — never `Finished`/a failure state.
2. `metrics IS NULL` (no real accuracy via `get_metric`) **AND `stats IS NULL`** (never populated).
3. `ended_at IS NULL` (didn't terminate into a recorded result).
4. **Age > 36h:** `created_at` ≥ 36h ago **AND**, if `started_at` is set, `started_at` ≥ 36h ago (whichever is more recent must still be older than 36h) — so a legitimately-RUNNING recent eval (`Pending`/`Started` but <36h) is EXCLUDED.

## 2. Cross-user FK safety (MANDATORY pre-check)

Restrict every delete to rows you own; **never** delete another user's rows without authorization.

**Default-scope to OUR rows** (the eval/re-eval owners `feuer1`, `bfeuer00`, `penfever`, `benjaminfeuer` — all four are the operator's own accounts; matches the sibling `crud-purge-below-gate-evals` OURS). Stale rows owned by GENUINELY OTHER users (`zhuang1`, `richard.zhuang`, …) are **REPORTED with counts, never deleted** — surface them to the supervisor. The match and the job-delete are both scoped by `username IN OURS` so a scope error cannot leak across users.

## 3. The cascade — `sandbox_jobs.id` IS FK'd (REQUIRED)

**`sandbox_jobs.id` IS FK'd by a child chain** — a plain delete fails Postgres `23503` foreign-key-violation. The chain is:

```
sandbox_trial_model_usage.trial_id → sandbox_trials.id → sandbox_jobs.id
         (grandchild)                     (child)            (job)
```

To delete a `sandbox_jobs` row you MUST cascade **grandchild → child → job**: delete its `sandbox_trial_model_usage` rows, then its `sandbox_trials` rows, then the `sandbox_jobs` row. The children carry NO `username` — ownership is TRANSITIVE from the job, so once you've asserted you own the JOB (§2), the whole cascade is FK-safe and yours. Still NEVER delete a job (or its cascade) you don't own.

## 4. Procedure — DRY-RUN, review, delete, re-read

```python
import os
from datetime import datetime, timezone, timedelta
from supabase import create_client
c = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"])
NOW = datetime.now(timezone.utc); CUTOFF_H = 36
OURS = {"feuer1", "bfeuer00", "penfever", "benjaminfeuer"}   # the operator's eval/re-eval owners we may delete

def age_h(ts):                          # hours since an ISO ts (None -> None)
    return None if not ts else (NOW - datetime.fromisoformat(ts)).total_seconds()/3600

def qualifies(r):
    if r["job_status"] not in ("Pending", "Started"):       return False
    if get_metric(r["metrics"]) is not None:                return False   # has a real score
    if r["stats"] is not None:                              return False   # has progress -> not "never populated"
    if r["ended_at"] is not None:                           return False   # terminated into a result
    ca = age_h(r["created_at"]); sa = age_h(r["started_at"])
    recent = min(x for x in (ca, sa) if x is not None)      # most-recent activity
    return recent is not None and recent > CUTOFF_H         # older than 36h

rows = c.table("sandbox_jobs").select(
    "id,job_name,username,job_status,created_at,started_at,ended_at,n_trials,metrics,stats,model_id,benchmark_id"
).in_("job_status", ["Pending", "Started"]).execute().data
q = [r for r in rows if qualifies(r)]

# Safety assert: nothing we matched may carry a real score/progress (never guess-delete)
bad = [r for r in q if r["stats"] is not None or get_metric(r["metrics"]) is not None]
assert not bad, f"STOP: {len(bad)} matched rows have stats/metrics — ambiguous, surface to supervisor"

ours   = [r for r in q if r["username"] in OURS]
others = [r for r in q if r["username"] not in OURS]
from collections import Counter
bm = {b["id"]: b["name"] for b in c.table("benchmarks").select("id,name").execute().data}
mn = {m["id"]: m["name"] for m in c.table("models").select("id,name").execute().data}
print(f"QUALIFY total={len(q)}  OURS={len(ours)}  OTHERS(report-only)={len(others)}")
print("OURS by user:", Counter(r['username'] for r in ours))
print("OTHERS by user:", Counter(r['username'] for r in others))
for r in ours[:10]:                     # sample: id, user, model, benchmark, status, age
    print(f"  {r['id']} | {r['username']} | {mn.get(r['model_id'],'?')[:40]} | "
          f"{bm.get(r['benchmark_id'],'?')} | {r['job_status']} | {age_h(r['created_at']):.0f}h")

# --- DELETE (ours only, idempotent, scoped id + username) — run AFTER reviewing the dry-run ---
# ⚠️ CASCADE: sandbox_jobs.id IS FK'd — `sandbox_trials.job_id → sandbox_jobs.id` and
# `sandbox_trial_model_usage.trial_id → sandbox_trials.id`. A plain sandbox_jobs delete FK-fails (23503);
# delete grandchild → child → job. Children carry no username (ownership transitive from the job you own).
DELETE = False                          # flip to True to execute
if DELETE:
    for r in ours:
        trial_ids = [t["id"] for t in
                     c.table("sandbox_trials").select("id").eq("job_id", r["id"]).execute().data]
        for i in range(0, len(trial_ids), 200):       # chunk to keep the IN() lists sane
            chunk = trial_ids[i:i+200]
            if chunk:
                c.table("sandbox_trial_model_usage").delete().in_("trial_id", chunk).execute()  # grandchild
        c.table("sandbox_trials").delete().eq("job_id", r["id"]).execute()                       # child
        c.table("sandbox_jobs").delete().eq("id", r["id"]).eq("username", r["username"]) \
         .in_("job_status", ["Pending", "Started"]).execute()                                    # job (yours)
    # re-read: confirm gone + that NO Finished/scored row was touched
    left = c.table("sandbox_jobs").select("id").in_("id", [r["id"] for r in ours]).execute().data
    fin  = c.table("sandbox_jobs").select("id").eq("job_status", "Finished") \
            .in_("id", [r["id"] for r in ours]).execute().data
    assert not left, f"{len(left)} of ours survived"; assert not fin, "touched a Finished row!"
    print(f"DELETED {len(ours)} ours; OTHERS left for supervisor: {Counter(r['username'] for r in others)}")
```

## Guardrails

- **Cross-user FK safety is MANDATORY.** Scope both the match and the job-delete by `username IN OURS`. Other users' stale rows are **reported with counts, never deleted**.
- **The cascade is REQUIRED.** `sandbox_jobs.id` IS FK'd; a plain delete fails `23503`. Delete grandchild (`sandbox_trial_model_usage`) → child (`sandbox_trials`) → job, in that order.
- **DRY-RUN first, then delete, then re-read.** Leave `DELETE = False` until you've reviewed the sample. After deleting, re-read to confirm the rows are gone AND that no `Finished`/scored row was touched (the post-delete assert).
- **Never guess-delete.** `STOP + surface` if any qualifying row has a non-null `stats`/`metrics` (ambiguous "never populated").
- **Never raise `CUTOFF_H`** — the 36h floor excludes legitimately-running recent evals.
- **`n_trials` is planned, not progress.** A placeholder already has `n_trials=128`; do not read it as a populated signal.
- **Reads are free; deletes are dangerous.** The service-role key bypasses RLS.

## Related

- **`crud-otagent-supabase`** — the general Supabase read/aggregate/write skill (ID/OOD scores, model registration, the full `get_metric`/`set_stat` helpers). Reach for that one for anything other than the stale-placeholder purge.
