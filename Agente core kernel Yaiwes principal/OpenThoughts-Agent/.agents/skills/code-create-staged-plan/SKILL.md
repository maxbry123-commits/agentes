---
name: code-create-staged-plan
description: >-
  DESIGN a non-trivial codebase change (Harbor / MarinSkyRL / vLLM / OT-Agent / LLaMA-Factory) as a
  dependency-ordered STAGED PLAN before writing code — a feature port, a multi-step fix with parity
  requirements, a refactor, a kernel/perf change. Produces a parent plan doc + per-stage scope docs under
  notes/<codebase>/ (each stage = scope + GO/NO-GO validation gate + cost), with global invariants
  (flag-off byte-identical, parity gates), a borrow-map of code anchors (which drift), and safety
  considerations. Evidence/scoping breadcrumbs go in dated agent_logs/. Use when the user says "scope/plan
  this change", "stage it out", "design before coding", or a change is too big/risky for one shot. Pairs
  with code-execute-staged-plan (which runs the plan).
---

# code-create-staged-plan

Turn a substantial change into a dependency-ordered staged plan with a gate at each step. Plans live in
`notes/<codebase>/`; scoping evidence lives in dated `agent_logs/`.

> Read an existing `notes/vllm/` plan before writing a new one.

## When to use
- A feature **port** (upstream → our fork), a **multi-step fix** (esp. with a parity/regression requirement), a **refactor**, a **kernel/perf** change, or any change too big or too risky to land in one commit.
- NOT for a one-line fix or a mechanical edit — just do those (and log if non-obvious).

## Where it lives
- **Plan and scope docs:** `/Users/benjaminfeuer/Documents/notes/<codebase>/` — one parent (`README.md` or `<change>_plan.md`) and one `stage<N>_<slug>_scope.md` per stage.
- **Evidence:** dated `/Users/benjaminfeuer/Documents/agent_logs/YYYY-MM-DD_<topic>.md`; cite it from the plan.

## Parent plan doc — required sections
1. **Header:** date · **status** (`scoped — propose-only; no code yet` at creation) · target repo + **canonical local path** + **isolated working-copy path** (the rsync-clone you'll branch in — see "Isolated working copy" below) + branch (the feature branch you'll cut in the clone, e.g. `feuer/<slug>`) · links to the evidence `agent_logs/`.
2. **Goal:** the precise, testable end state (e.g. "`dcp=N` rollout bit-identical to `dcp=1`: greedy token-ids identical + logprobs allclose atol 1e-2").
3. **Mechanism:** root cause or design rationale.
4. **Stage map:** `Stage | title | what | feature(s) | layer | cost (CPU / 1-GPU / N-GPU) | gate`. Each stage must be independently testable and build on a gated predecessor; mark the critical path.
5. **Global invariants** (assert in EVERY stage): the **flag-off / default-off byte-identical** contract (a new feature is a no-op until its flag flips — mirror the EP/CP scaffold no-op tests); the **parity gate** (the load-bearing equivalence, e.g. G2 bit-identical); regression bounds (don't break MLA / the other arms); **minimal diff** (no gratuitous API/config churn).
6. **Borrow map** (don't reinvent): the exact files/functions/line-anchors you'll touch or copy from — **and a standing note that anchors DRIFT** (reconfirm at impl time; they're from a dated read).
7. **Safety / reward-hacking** (where relevant): policy-invariance for RL reward shaping, ground-truth anchors, "down-weight not zero", parse-real-signals-only.
8. **Validation discipline:** per-stage, what proves the gate (flag-off byte-identical first → behavior-on test → GPU smoke on the correct SIF/env). Name the measurement (paired McNemar + pass@k, `torch.equal`, allclose tol at the bf16 floor — don't loosen a tol silently).

## Per-stage scope doc (`stage<N>_<slug>_scope.md`) — required sections
- **Header:** date · status (`scoped GO` / `blocked` / …) · companion = the parent · "no fix yet" if scope-only.
- **Why this is the next step.**
- **Change-set:** exactly what files change (or "test-only; no `<repo>/` source touched this stage").
- **Validation gate (GO/NO-GO):** the concrete pass condition + cost. This is what `code-execute-staged-plan` checks before advancing.
- **Composes with / depends on:** the upstream stages it assumes are already green.

## Isolated working copy — rsync-clone BEFORE you branch (do NOT branch the canonical clone)
Use this rsync-clone path only for `penfever/working` self-merge repos:
`~/Documents/{OpenThoughts-Agent,vllm}`. Marin forks (`harbor`, `MarinSkyRL`, `evalchemy`) use
git-worktree→PR→`main`. Never cut a feature branch on the canonical clone; rsync it to an isolated working
directory first:
```bash
# 1. rsync-clone the canonical repo (INCLUDING .git; skip heavy build/venv dirs) to an isolated copy
SLUG=<change-slug>; REPO=OpenThoughts-Agent          # or vllm  (marin-forks harbor/MarinSkyRL/evalchemy use worktree→PR→main instead)
SRC=/Users/benjaminfeuer/Documents/$REPO
DST=/Users/benjaminfeuer/Documents/staged-work/$SLUG/$REPO
mkdir -p "$(dirname "$DST")"
rsync -a --exclude='.venv' --exclude='__pycache__' --exclude='*.egg-info' --exclude='wandb/' "$SRC/" "$DST/"
# 2. confirm the canonical clone is clean + on penfever/working, then branch IN THE CLONE
cd "$DST" && git fetch origin && git checkout penfever/working && git pull --ff-only && git checkout -b feuer/$SLUG
```
- Keep the canonical clone on `penfever/working`.
- Record `staged-work/<slug>/<repo>` in the plan header; execute, commit, and push from it, then `git pull` other clones.
- The rsync clone is not the editable-installed copy; test clusters after push+pull. Use `mcp__ide__getDiagnostics` on clone files.
- Use one clone per touched repo; remove `staged-work/<slug>/` after merge.

## Discipline
- **Local clone is ground truth:** branch in an rsync clone; execution commits, pushes, and syncs rather than patching clusters.
- **Default-off:** flag-off is byte-identical.
- **Cheapest repro first:** stage 0 is usually a unit/CPU harness.
- At creation, plans are propose-only; hand off to `code-execute-staged-plan` for execution.
