---
name: datagen-create-task-dataset
description: >-
  Create a FRESH, snapshot-safe Harbor task dataset from an arbitrary input — a
  raw non-Harbor HF dataset (e.g. allenai/TMax-15K), a generator codebase (e.g. a
  GitHub repo like FrontierSmith), or just natural-language instructions with no
  seed data. The pipeline is a sequence of IDEMPOTENT stages — triage (pick the
  entry stage) → task-generation → Harbor conversion → snapshot-safe patcher →
  oracle-solution generation → quality gate — each with its OWN empirical test
  before advancing, intermediate artifacts uploaded to HF (laion/, parquet). The
  end artifact is a Harbor task dataset whose oracle (gold) solutions verify at a
  high rate, with ≤ 6 (hard ≤ 10) unique Daytona snapshots. Use when asked to
  "make/convert/build a task dataset", "turn <HF dataset> into Harbor tasks", "run
  <generator repo> into a task set", or "create tasks from these instructions".
  Runs LOCALLY on the Mac + Daytona (no GPU; teachers via API/vLLM). Distinct from
  datagen-reduce-dataset-snapshots (that fixes an EXISTING Harbor dataset's snapshot
  count — it IS this skill's stage 3) and datagen-launch (that generates TRACES by
  running agents over an existing task dataset).
---

# datagen-create-task-dataset

Build a new **Harbor task dataset** — runnable agent tasks (`instruction.md` + `environment/Dockerfile` + `tests/` + `solution/`) that is **snapshot-safe** (few unique Daytona environments) and **oracle-verifiable** (gold solution makes tests pass). **Stage-based and idempotent**: pick the entry stage, each independently re-runnable, each with an **empirical gate** before advancing; every output uploads to HF (`laion/`, public parquet).

## Always (local-Mac conventions)
- Python = `/Users/benjaminfeuer/miniconda3/envs/otagent/bin/python` (full path; symlinks fail in the sandbox). `source "${DC_AGENT_SECRET_ENV:?set DC_AGENT_SECRET_ENV first}"` for HF + Daytona + teacher keys.
- **PRE-FLIGHT (do at minute one): confirm `data.commons` imports cleanly** — `cd /Users/benjaminfeuer/Documents/OpenThoughts-Agent && <otagent python> -c "import data.commons"`. `data.commons` imports `harbor.trial.trial` at module level — a broken/mid-merge **local `harbor` clone** (`/Users/benjaminfeuer/Documents/harbor`; check `ls .git/MERGE_HEAD`, `git -C ../harbor status`) silently blocks every Daytona-dependent stage. If the import fails, **STOP and surface to the user** (do NOT resolve harbor merge conflicts yourself — it's core RL code).
- **All pipeline CODE lives in `/Users/benjaminfeuer/Documents/OpenThoughts-Agent/data/<dataset-slug>/`** (a `generate.py` + conversion helpers). The **snapshot-safety patcher** lives in `data/patchers/patch_<slug>_tasks.py` (`ls data/patchers/`). Study existing examples first: `data/nl2bash/`, `data/code_contests/`, `data/swegym/` and `data/patchers/patch_*_tasks.py`.
- **Dated logs → the ABSOLUTE path `/Users/benjaminfeuer/Documents/agent_logs/YYYY-MM-DD_<slug>_taskgen.md`** — NEVER a relative `agent_logs/` (resolves to the repo cwd). Record the chosen entry stage, each gate's numbers, every intermediate HF id, and the final snapshot/oracle numbers.
- HF uploads default **PUBLIC to `laion/`**; task datasets are never DB-registered.

## Sizing rule (decide at triage, write it in the log)
- **Real seed data → generate the MAXIMUM-size dataset** (no `--limit`; `--limit <=0` on the patchers = no cap). Don't subsample real corpora.
- **Synthetic (NL-only / teacher-generated) → pick a reasonable cap** from seed material × teacher cost. State the cap + reasoning up front.

## Stage 0 — TRIAGE: pick the entry stage (do this FIRST)
Stages are idempotent, so you can also resume a half-built dataset mid-pipeline.

| Input | Start at |
|---|---|
| **Raw non-Harbor HF dataset** (records that aren't Harbor tasks — e.g. `allenai/TMax-15K`) | **Stage 2 (Convert)** — map the seed records into Harbor task dirs. |
| **Generator codebase** (a repo that emits problems/tests — e.g. `FrontierCS/FrontierSmith`) | **Stage 1 (Generate)** — clone, understand its output, run it to produce seed material, THEN Stage 2. |
| **NL instructions, no seed data** | **Stage 1 (Generate)** — synthesize seed tasks with a teacher (capped per the sizing rule), THEN Stage 2. |
| **An existing Harbor dataset that's snapshot-unsafe / fails oracle** | **Stage 3 / 4** — this is the `datagen-reduce-dataset-snapshots` skill (stage 3) + the oracle gate (stage 4). |

Write the chosen entry + why in the dated log. If the input is ambiguous (e.g. a repo that's both a generator AND ships a dataset), inspect before committing; ASK the user if genuinely unclear.

**Compatibility pre-check (reject incompatible sources at triage, not 3 stages in):** confirm the source can become a Harbor task at all:
1. **Binary-verifiable reward?** Harbor's verifier is pass/fail — `tests/test_state.py` asserts `/logs/verifier/reward.txt == "1"`, and the oracle gate needs a gold solution that deterministically scores a pass. If the source's reward is **continuous/graded** (a 0–1 ratio, an optimization score that never hits 1.0) or **open-ended** (no deterministic gold solution — "heuristic approaches expected"), it does NOT fit the binary contract → STOP at triage and surface (building it requires redefining "pass" as a score threshold, a design change, not a pipeline run).
2. **Single-container environment?** Daytona builds ONE container per unique `environment/Dockerfile` — no `docker-compose`, no sidecar/judge services, no `privileged`, no host bind-mounts (no existing dataset uses compose). A source needing a multi-container topology can't run in the snapshot model without re-engineering the judge in-container → STOP at triage and surface it.
Either failing is a go/no-go for the user, not something to grind through the stages.

## Stage 1 — GENERATE seed material (generator-codebase / synthetic only)
- **Generator codebase:** clone to a scratch dir (NOT inside the repo), read its README + entrypoint, install its deps in a throwaway venv, run it to emit its native output (problems + tests + reference solutions). Capture raw output; do NOT yet force it into Harbor shape. Note its license + any API/teacher it calls.
- **NL-only / synthetic:** use a teacher (API via `data/generation` `InferenceEngine`, or a vLLM endpoint) to generate problem statements + reference solutions + tests, capped per the sizing rule.
- **Gate:** a handful of generated items are well-formed (problem text present, a runnable reference solution, ≥1 test that distinguishes pass/fail). Upload the raw seed to `laion/<slug>-seed` (parquet).

## Stage 2 — CONVERT to Harbor format
Write `data/<slug>/generate.py` (model it on `data/nl2bash/generate.py` / `data/code_contests/` and use `data/commons.py` helpers — `generate_tasks_from_questions`, `subsample_tasks_directory`/`limit_tasks_directory`, `upload_tasks_to_hf`). Each task dir must contain:
- `instruction.md` — the agent-facing problem (+ any runtime repo-clone/setup, so it stays OUT of the Dockerfile — see Stage 3).
- `environment/Dockerfile` — the build env. **This file's content-hash IS the snapshot key** (siblings don't affect it) — keep it SHARED across tasks (Stage 3).
- `tests/` — `test.sh` (runs the tests), `test_state.py` (asserts `/logs/verifier/reward.txt == "1"`), `config.json` (pass/fail test lists).
- `solution/` — `solve.sh` (the oracle/gold solution, typically a heredoc + `git apply` / direct edits). Empty/placeholder until Stage 4 if the source has no gold solution.
- task metadata (id, source, etc.).
- **Harbor mounts ONLY `environment/` (→ the image), `solution/` (→ `/solution`), and `tests/` (→ `/tests`) — there is NO `/setup_files` mount** (named in `TaskPaths` but NOT wired up; verified against harbor source 2026-06-22, TMax-15K). Any per-task setup that can't live in the shared Dockerfile (Stage 3) must be carried INSIDE `tests/` AND `solution/` (e.g. ship a `setup.sh` in both and have `test.sh`/`solve.sh` source it) and inlined into `instruction.md` for the agent — do NOT invent a `setup_files/` dir and expect it mounted. If the setup touches a cloned repo, add a `git config --global --add safe.directory '*'` hardening.
- **Gate:** extract a few tasks and confirm the schema matches a known-good dataset. Fast check = run a tiny **infra smoke** (Stage 5's tier-1) on ~5 tasks — does the env build + the harness run? Fix schema/Dockerfile errors here, before scaling up. Upload the converted set to `laion/<slug>-tasks-raw` (parquet) via `upload_tasks_to_hf`.

## Stage 3 — SNAPSHOT-SAFE (the patcher)
Harbor's Daytona backend builds **one snapshot per unique `environment/Dockerfile`**. A per-task Dockerfile (e.g. `repo@commit` baked in) explodes to ~1 snapshot/task and is unlaunchable. Make a patcher (`data/patchers/patch_<slug>_tasks.py`) render a **small shared set** of Dockerfiles. **Canonical template = `data/swegym/generate_patched.py` + the `datagen-reduce-dataset-snapshots` skill** (read it — Stage 3 IS that skill):
- Dockerfile = `FROM ubuntu:22.04` + Miniconda creating a `testbed` env at `python={python_version}`, interpolating ONLY a coarse key (`{python_version}`) + a per-version apt union (`{extra_packages}` from an `apt_map`). Nothing task-specific in the Dockerfile.
- Defer repo-specific `git clone @commit` + `pip install`/`make` into `instruction.md`, `solution/solve.sh`, `tests/test.sh` (run at trial time) via a `get_specs(repo, version)` map.
- **Gate (hard):** `$PY -m scripts.harbor.count_snapshots_from_tasks --local-dataset <tasks_dir>` → read `UNIQUE ENVIRONMENTS (SNAPSHOTS): N`. **Target N ≤ 6, hard ≤ 10.** Iterate the grouping until under. Regenerate the full dataset with `--limit <=0` `--target-repo laion/<slug>-tasks-patched` (NEW versioned repo — never overwrite a validated artifact), then re-extract + re-count the uploaded repo end-to-end.

## Stage 4 — ORACLE solutions
Every task needs a **known-correct** `solution/solve.sh` whose application makes `tests/` pass.
- **Source has gold solutions** (most converted datasets — the patch/diff/reference): write it into `solve.sh` (heredoc + `git apply`, per swegym).
- **No gold solution** (NL-only / some generators): generate with a teacher, then KEEP ONLY the ones that verify (the oracle gate below is also the filter).
- **Gate (THE real quality gate):**
  ```bash
  $PY scripts/daytona/validate_and_upload_from_hf.py \
    --repo_id laion/<slug>-tasks-patched --extract_dir <cache> \
    --stages oracle --sample_size 40 --sample_seed 42 --skip_upload \
    --keep_failed_dir <dir>/oracle_failures
  # prints "Success: S  Fail: F  Missing: M" → oracle pass = S/(S+F)
  ```
  **Target oracle pass ≥ 80%** (set the floor in the log before starting). Sub-floor → inspect `oracle_failures/`; the Stage-3 env-collapse broke some repos' installs, OR the gold solution/test is wrong. Fix `get_specs`/the test harness, regenerate, re-oracle (bounded budget, 2–3 rounds — see the reduce skill's tradeoff discipline).

## Stage 5 — QUALITY GATE (iterate until clean)
Tier-1 infra smoke (env builds + agent runs without crashing):
```bash
echo "laion/<slug>-tasks-patched" > /tmp/<slug>_check.md
FORCE_COLOR=1 SAMPLE_SIZE=200 ./scripts/daytona/batch_validate_from_md.sh /tmp/<slug>_check.md
# summary: /Users/benjaminfeuer/Documents/agent-traces-analysis/summary.tsv  (columns: dataset total infra_ok infra_rate solved solve_rate)
```
Read the THREE signals (all must hold to ship):
1. **`infra_rate` ≈ 1.0** — envs build + harness runs. Well below 1.0 = real infra failures → inspect `traces/` + `failures/`, fix, re-run.
2. **oracle pass ≥ floor** (Stage 4) — gold solutions verify. This is the correctness gate, NOT batch_validate's `solve_rate`.
3. **`solve_rate` reasonable for the difficulty** — the *weak agent's* (Qwen3-8B) task-solve rate. LOW for hard tasks (expected) but NOT ~0 across easy tasks (≈0 everywhere can signal mis-specified tasks/grading) and NOT ~1.0 on tasks meant to be hard (trivial/leaked answer). Judge against the dataset's intended difficulty.

Iterate Stages 3–5 until: snapshots ≤ 6, oracle ≥ floor, infra ≈ 1.0, solve_rate sane. Then the dataset is shippable.

## Finish
- The shippable artifact is `laion/<slug>-tasks-patched(-vN)`. Record in the dated log: every intermediate HF id, the final snapshot count, oracle pass %, infra_rate, solve_rate, and the entry stage taken.
- Add the dataset to the relevant tracker if one applies (e.g. `notes/ot-agent/task_repos/`). Clean up scratch/extract dirs.

## Guardrails
- **Empirical gate every stage — do not advance on a green count alone.** Snapshots-green + oracle-red is a FAILED dataset (broken reward signal).
- **Never raise/bypass the Daytona snapshot cap** — reduce the real count (snapshot-reduce skill). **Never overwrite a validated artifact** — new versioned repo each regenerate.
- If a stage is genuinely blocked (license forbids redistribution, generator needs a key we don't have, oracle floor unreachable at any <cap grouping) → STOP and surface the specifics; don't loop.
