---
license: mit
tags:
- harbor
- agent-tasks
- competitive-programming
- optimization
- graded-reward
---

# FrontierSmith — Graded-Reward Harbor Tasks (v1)

10 open-ended **competitive-programming optimization** tasks in OpenThoughts-Agent /
Harbor format. The agent writes a C++17 heuristic to `/app/solution.cpp`; an
**in-container judge** grades it on 10 hidden cases and thresholds the result
into a binary Harbor reward.

## ⚠️ This is a NEW task contract: graded → thresholded binary

These are **open-ended optimization** problems — exact optima are intractable and
**no closed-form gold solution exists** ("heuristic approaches are expected").
The upstream checker emits a **continuous quality ratio in [0,1]** per case
(higher is better; infeasible output = 0). The in-container judge averages the 10
per-case ratios into a continuous score, then thresholds it:

> `reward = "1"  iff  mean_ratio >= TAU,  else "0"`

So **"pass" means "the submission beat the deterministic baseline by a margin"**,
**NOT** that it found an optimal/closed-form solution. Each task's `TAU` is set
**per problem, above its baseline ratio** (the do-nothing or the upstream
deterministic judge-baseline), and is recorded in `task.toml` (`tau`,
`tau_justification`) and in `tests/judge_meta.json`. Per-task TAU and the
oracle-heuristic's measured mean ratio:

| task | baseline ratio | TAU | heuristic mean ratio |
|---|---|---|---|
| frontiersmith-1  | 0.10 | 0.18 | 0.374 |
| frontiersmith-2  | 0.00 | 0.07 | 0.265 |
| frontiersmith-3  | 0.50 | 0.54 | 0.650 |
| frontiersmith-4  | 0.50 | 0.54 | 0.653 |
| frontiersmith-5  | 0.00 | 0.12 | 0.403 |
| frontiersmith-6  | 0.50 | 0.51 | 0.551 |
| frontiersmith-7  | 0.20 | 0.23 | 0.289 |
| frontiersmith-8  | 0.50 | 0.62 | 0.904 |
| frontiersmith-9  | 0.50 | 0.51 | 0.570 |
| frontiersmith-10 | 0.00 | 0.20 | 0.699 |

(The `0.50` baselines mean "matching the upstream deterministic judge-baseline" —
beating it requires ratio > 0.50.)

## Single-container, no judge sidecar

Verification runs **entirely inside the one task container**: `tests/test.sh`
invokes `tests/run_judge.py`, which compiles the vendored testlib special-checker
(`tests/chk.cc` + `tests/testlib.h`), runs `/app/solution.cpp` on each
`tests/testdata/*.in` with the problem's time/memory limits, parses the checker's
`Ratio:` value per case, averages, and thresholds at TAU. There is **no
docker-compose, no go-judge sidecar, no host bind-mounts** — the upstream
`frontier-cs-algorithm` adapter's compose/sidecar topology was re-implemented
in-process so the dataset is Daytona-snapshot-safe. All per-problem assets live
under `tests/` (mounted at `/tests`, not part of the environment hash), so the
shared `environment/Dockerfile` is byte-identical across all 10 tasks →
**exactly 1 unique Daytona snapshot**.

## Oracle solutions

Because no gold solution exists, each `solution/solve.sh` writes a hand/teacher-
authored **heuristic** C++ solver to `/app/solution.cpp` that is chosen so its
mean ratio clears TAU. Validation: **10/10 oracle heuristics clear their TAU** via
the Daytona oracle gate; **1 unique snapshot**.

## Attribution / license

The problem content (statements, testlib generators/checkers, test cases) is
derived from the **MIT-licensed** upstream [FrontierCS/Frontier-CS](https://github.com/FrontierCS/Frontier-CS)
repository — these 10 problems correspond to upstream algorithmic problems
**306–315** (`frontiersmith_1..10`). The companion paper repo
[FrontierCS/FrontierSmith](https://github.com/FrontierCS/FrontierSmith)
("Synthesizing Open-Ended Coding Problems at Scale") withholds the generators/
orchestrator; only this fixed seed set of 10 problems is redistributable, under
**MIT** with attribution. The Harbor conversion, in-container judge, TAU thresholds,
and heuristic oracle solutions are original to OpenThoughts-Agent.
