---
name: datagen-reduce-dataset-snapshots
description: >-
  Reduce the Daytona snapshot (unique-environment) count of a Harbor task dataset
  below the cap by editing its patcher's environment-build logic, without breaking
  task quality. Use when a dataset is flagged "SnapshotCapExceeded" / "N unique
  environments" with N over the threshold (target < 10), e.g. swegym at 906. The
  loop: set snapshot+oracle thresholds → count → diagnose the env-hash driver →
  group/unionize Dockerfiles in the patcher → regenerate + upload → re-count →
  TWO-TIER quality gate (harbor infra smoke + `--stages oracle` gold-patch yield) →
  navigate the snapshot↔fidelity tradeoff within a bounded iteration budget → record.
  Runs LOCALLY on the Mac + Daytona (no GPU).
---

# datagen-reduce-dataset-snapshots

Harbor's Daytona backend builds **one container snapshot per unique environment
directory**, keyed by a content hash of `environment/` — which for our patchers is
**just `environment/Dockerfile`** (solution/tests/metadata live in sibling dirs and
don't affect the hash). Daytona enforces a HARD org cap (40) and a per-launch
`max_new_snapshots` (10). A dataset whose tasks each render a distinct Dockerfile
explodes to ~1 snapshot/task and is unlaunchable. **Fix:** make the patcher render a
small shared set of Dockerfiles (grouped by a coarse key like Python version); clone
the repo + run repo-specific install at agent/verifier runtime instead of image-build
time, so thousands of tasks collapse onto a handful of environments.

## Thresholds — set BEFORE regenerating (step 0, write in the log)

Snapshot reduction is **lossy**: fewer envs → less each task's env is tailored → some
repos' installs stop reproducing the gold patch → oracle yield drops. You are choosing
an operating point on the snapshot↔fidelity curve, not "fixing a bug" — decide these
up front to avoid an unbounded chase:

- **Snapshot ceiling:** hard `< 10` (ideally ≤ 8). Non-negotiable — it's the cap.
  (20 is the "skip the dataset" line; this skill pulls a dataset back under it.)
- **Oracle-yield floor:** a number set up front (e.g. **≥ 80%** for a dataset destined
  for RL/datagen verification; lower only with explicit reason). Without a pre-set
  floor every result looks "one more round will help" and you over-fit `get_specs` to
  the 40-task sample.
- **Iteration budget:** max regenerate→oracle rounds (e.g. **2–3**). Each round is a
  full regenerate + upload + oracle sample (slow + Daytona builds); diminishing returns
  set in fast once the easy repo-family fixes are in.
- **Sample size for the yield estimate:** 40 is a usable read; don't re-sample
  endlessly chasing a ±few-point wobble — that is not signal.

## Authoritative count tool

`scripts/harbor/count_snapshots_from_tasks.py` computes the exact content-hash dedup
count Daytona's `auto_snapshot` path uses (`get_task_environment_hash` /
`analyze_task_dockerfiles`). Run it on a **local task dir** (post-extraction or
post-generation), not a live HF id, to skip the registry round-trip:

```bash
PY=/Users/benjaminfeuer/miniconda3/envs/otagent/bin/python
$PY -m scripts.harbor.count_snapshots_from_tasks --local-dataset <tasks_dir>
# read the "UNIQUE ENVIRONMENTS (SNAPSHOTS): N" line
```

For an uploaded HF dataset, extract first:
```bash
$PY -m scripts.datagen.extract_tasks_from_parquet \
  --parquet <hf-id> --output_dir /tmp/snapcount-<slug> --on_exist overwrite
$PY -m scripts.harbor.count_snapshots_from_tasks --local-dataset /tmp/snapcount-<slug>
```

## The cycle

1. **Count the current artifact.** Extract the flagged HF dataset → count. Confirm
   it's genuinely over threshold — use the tool above, not row counts.

2. **Diagnose the env-hash driver.** Find the patcher. **Most live in the shared
   `data/patchers/` dir** (`patch_<name>_tasks.py`, `patch_exp_rpt_*_tasks.py`,
   `patch_mix_h*_tasks.py`, `patch_code_contests_tasks.py`, …); only a few datasets
   keep a per-source-subdir patcher (`data/<name>/generate_patched.py`, e.g. swegym,
   swesmith). `ls data/patchers/ | grep -i <name>; ls -d data/<name> 2>/dev/null`.
   The unique-env count == number of **distinct rendered `Dockerfile` strings**. The
   explosion almost always comes from **per-task interpolation into the Dockerfile**:
   `repo@commit` in a build-time `git clone`/`RUN`, a per-instance base image, or
   per-task apt pins. Generate a small sample with the *current* patcher and count it
   — if the uploaded artifact is high but a fresh sample is low, the artifact is just
   **stale** (made by an older patcher) and step 4 is a pure regenerate+reupload.

3. **Rewrite the env logic to group (only if step 2's fresh sample is still high).**
   Make the Dockerfile depend on a **coarse grouping key** (e.g. Python version), not
   the task. The swegym pattern:
   - Base image + a **union** of system apt deps per group; nothing task-specific in
     the Dockerfile.
   - Move `git clone <repo>@<commit>` and repo-specific `pip install`/`make` into
     `instruction.md` (agent setup), `solution/solve.sh`, `tests/test.sh` — they run
     at trial time, against the shared image.
   - Keep a `get_specs(repo, version)` map so each repo still gets its correct Python
     + install command; only the *Dockerfile-affecting* part is coarsened.
   Re-generate a sample → count → iterate the grouping until **< 10**.

4. **Regenerate the full dataset + upload to a NEW repo.** Never overwrite the
   validated artifact; bump the version suffix (`...-validated-v2` → `...-v3`, or
   `...-snap-reduced`). Run the patcher with `--limit <=0>` (no limit),
   `--target-repo laion/<new-name>` (public per `feedback_hf_public_default`). Then
   re-extract + re-count the **uploaded** repo to confirm < 10 end-to-end.

5. **Quality gate — TWO-TIER (DO NOT SKIP).** Snapshot reduction is valid only if the
   tasks still build AND stay verifiable. Two distinct signals; conflating them is the
   classic mistake:

   - **Tier 1 — infra (harbor smoke):** does the env build + the agent run without
     crashing? Run:
     ```bash
     echo "laion/<new-name>" > /tmp/snap_check.md
     FORCE_COLOR=1 SAMPLE_SIZE=200 ./scripts/daytona/batch_validate_from_md.sh /tmp/snap_check.md
     # summary TSV: /Users/benjaminfeuer/Documents/agent-traces-analysis/summary.tsv
     ```
     Read `infra_rate`. **Ignore this script's `solve_rate`** — it's the *agent's*
     task-solve rate, low by design, NOT a measure of task well-formedness.
   - **Tier 2 — oracle correctness (THE real quality gate):** does the gold patch
     still make tests pass? `batch_validate` does NOT run this; run it explicitly:
     ```bash
     $PY scripts/daytona/validate_and_upload_from_hf.py \
       --repo_id laion/<new-name> --extract_dir <cache> \
       --stages oracle --sample_size 40 --sample_seed 42 --skip_upload \
       --keep_failed_dir <dir>/oracle_failures
     # prints "Success: S  Fail: F  Missing: M" → oracle pass = S/(S+F)
     ```
     A low oracle rate means the env/install/test harness no longer reproduces the
     conditions the patch needs — the env-collapse broke repo-specific installs.
   - **CAP-SAFETY: do NOT re-validate the OLD high-env artifact.** Sampling 200 (or
     40) tasks from a 906-env dataset tries to build that many snapshots and blasts
     the org cap. The new low-env artifact is cheap to validate; for a baseline use
     the old artifact's *recorded* validation number (tracker / a prior
     `summary.tsv`), or judge against the **floor set in step 0** above.
   - If oracle pass < threshold, the grouping broke some repos' installs — inspect
     `oracle_failures/` + `traces/`, fix the per-repo install in `get_specs`,
     regenerate, re-test (within the budget).

6. **Record in the tracker.** Add the new repo to
   `notes/RL/a3/a3_rl_tracker.md` (and, for datagen rows, the MiniMax tracker
   `experiments/active/datagen/minimax-m2.7-tt/tracker.md`): the new HF id,
   before→after snapshot count, and smoke-test infra/solve rates. Write a dated log to
   `/Users/benjaminfeuer/Documents/agent_logs/`.

## Decision at each round (don't iterate reflexively)

1. Oracle ≥ floor at < 10 snapshots → **SHIP** (record both numbers; done).
2. Oracle < floor, failures **cluster** on a few repo-families with identifiable
   missing install steps → **one targeted `get_specs` round** (add the apt pkg / pip
   constraint / install command for those families), regenerate, re-oracle. Spend a
   budget slot.
3. Oracle < floor, failures **spread evenly** (systemic — the shared env can't satisfy
   the repo diversity) → the **inherent tradeoff, not a bug**. Do NOT keep tweaking
   `get_specs`. Pick a coarser-but-larger grouping that still fits the cap (e.g. group
   by py-version **× repo-family** → maybe 8–15 envs instead of 5) and re-measure the
   (snapshots, oracle) point. Present the tradeoff curve.
4. Budget exhausted and still < floor at any ≤-cap grouping → **STOP and surface to
   the user** with the curve (e.g. "5 envs → 48% oracle; 12 → 74%; 30 → 91% but busts
   the 10-cap"). Shipping a lower-fidelity dataset, raising the floor, or shelving is
   the user's call, not an infinite loop's.

## Worked example — swegym (#31, 906 → 5 snapshots, a FAILED reduction)

`laion/swegym-tasks-patched-validated-v2`: 989 tasks → **906** unique envs (≈1:1).
The patcher `data/swegym/generate_patched.py` **already groups Dockerfiles by Python
version** (`get_specs()` interpolates only `{python_version}` + `{extra_packages}`
from a fixed `apt_map`, clones the repo at runtime), so v2 was a **stale artifact from
an older per-task patcher**. Regenerating with the current patcher →
`laion/swegym-tasks-patched-validated-v3` → **906 → 5 snapshots** (no patcher code
change). **But the quality gate exposed the tradeoff:** Tier-1 harbor smoke =
**100% infra** (looks great, would be mistaken for success); Tier-2 **oracle =
19/40 = 47.5%** — 5 shared py-version envs can't satisfy every repo's install. v3 is
**snapshots-green but oracle-red = a FAILED reduction**, not shippable.

## Guardrails

- **Never ship below the oracle floor just because snapshots are green.** A
  tiny-snapshot dataset whose gold patches don't verify is worse than useless for
  RL/datagen (the reward signal is broken). Snapshots-green + oracle-red is a
  **failed** reduction, recorded as such.
- **Never raise/bypass the Daytona cap** (`max_new_snapshots`, `max_org_snapshots`)
  or convert `SnapshotCapExceeded` to a warning — reduce the real count
  (`feedback_daytona_snapshot_caps_hard_limit`).
- **Never overwrite the existing validated artifact** — always a new versioned repo.
- Uploads are PUBLIC by default to `laion/`; `enable_db_registration` stays off (these
  are task datasets, not models).
- On the Mac, run everything with the `otagent` python
  (`/Users/benjaminfeuer/miniconda3/envs/otagent/bin/python`); `source
  "${DC_AGENT_SECRET_ENV:?set DC_AGENT_SECRET_ENV first}"` first (`.agents/secret.md`).
