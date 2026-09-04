---
name: code-execute-staged-plan
description: >-
  EXECUTE a staged codebase plan (from code-create-staged-plan or an existing notes/<codebase>/ plan) one
  stage at a time, gate-by-gate, while keeping the local clone ground truth and a dated agent_logs/ progress
  log. For each stage: re-read the scope + reconfirm the (drifting) code anchors, make the edit in the LOCAL
  clone on the feature branch, run the validation gate (flag-off byte-identical FIRST, then behavior-on /
  parity / GPU smoke on the right SIF/env), commit+push and sync to the cluster (vLLM = build from source,
  never rsync), update the plan status, and only THEN advance. Log every stage/debug session in
  agent_logs/YYYY-MM-DD_<topic>.md so long runs don't lose context. Use when the user says "execute/run the
  plan", "do stage N", or "continue the <X> port/fix".
---

# code-execute-staged-plan

Run a staged plan one stage, gate, and commit at a time. Keep the plan in `notes/<codebase>/` and a dated
progress log in `agent_logs/`.

## Inputs
- The **plan**: `notes/<codebase>/{README.md | <change>_plan.md}` + the per-stage `stage<N>_<slug>_scope.md`. Read the parent (goal + invariants + stage map) and the current stage's scope doc.
- The **progress log**: a dated `agent_logs/YYYY-MM-DD_<topic>.md` — the running record for this change. If one exists for the change, append; else create it.

## Per-stage loop
1. **Re-read the stage scope + RECONFIRM anchors.** The borrow-map line/file anchors drift — grep/open the real files now; don't trust line numbers from the plan's authoring date.
2. **Edit the local feature branch.** The clones are under `~/Documents/`; never hand-edit or patch-by-rsync a cluster. Keep the diff minimal.
3. **Run the validation gate, in order:**
   - **Flag-off byte-identical first** — prove the change is a no-op when its flag is off (`torch.equal` / golden test / the EP-CP no-op test pattern).
   - **Behavior-on / parity** — the stage's GO condition (e.g. `dcp=N`==`dcp=1` greedy bit-identical + logprobs allclose at the **bf16 floor** tol — don't loosen tol to pass).
   - **GPU smoke** where needed via `sbatch` on the correct SIF/env (`.agents/ops/<cluster>/ENVIRONMENT_MAP.md`; torch selects the runtime).
   - Lint/syntax via `mcp__ide__getDiagnostics`, not `py_compile`.
4. **Commit, push, and sync.** One descriptive commit per stage/logical unit. `git pull` the editable Python repos on the cluster; build vLLM from the committed source. Verify the cluster clone is at the pushed commit and clean.
5. **Record results:** update the stage scope and parent status (`Stage N ✅ DONE — commit <sha>, gate <result>`); append what changed, commit, gate numbers, blocker, and next step to `agent_logs/`.
6. **Advance only on GREEN.** A red/ambiguous gate stops the loop — diagnose (dispatch an investigative subagent if it's deep), log it, fix, re-gate. Don't paper over a failing parity gate.

## Progress-log discipline (`agent_logs/`)
- **One dated file per change/debug thread** (`YYYY-MM-DD_<topic>.md`); append across stages and sessions.
- Capture: the hypothesis, what was tried, **commit SHAs**, gate results (with numbers), what was ruled out, and the current blocker + next action. Future-you (or a fresh subagent) should be able to resume from the log alone.
- This log is ALSO the per-change failure/remediation record the cron sweep references for genuine FAILED jobs.

## Subagents (for parallel stages / deep investigations)
Dispatch with: edit local → commit/push → sync; secrets via env vars only (`source "$DC_AGENT_SECRET_ENV"`); reconfirm anchors; run and report the gate. Verify the gate claim before marking a stage DONE.

## On completion
When the final stage is green, mark the parent plan DONE with the commit range and headline gate, ensure the canonical branch and clusters are current, and write the closing `agent_logs/` entry. Note concrete follow-ups.
