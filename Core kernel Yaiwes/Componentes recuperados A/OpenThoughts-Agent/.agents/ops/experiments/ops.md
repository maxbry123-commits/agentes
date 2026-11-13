# Experiments workspace — `/Users/benjaminfeuer/Documents/experiments`

Local per-experiment workspace. Each experiment or series has a source-of-truth tracker subdirectory.

> In-flight series live in `experiments/active/<name>/`; finished series live in `experiments/complete/<name>/`.

> Datagen experiments are flat `active/<model>-<ctx>-datagen-<taskset>-<cluster>/` siblings, not `active/datagen/` children. Keep ops facts in `.agents/ops/<cluster>/`, procedures in `datagen-launch-*`, and history in `~/Documents/agent_logs/`.

This holds local working state and trackers. `notes/` is the knowledge base, `agent_logs/` is dated remediation history, and cluster-side `experiments/` holds `logs/`, `configs/`, `sbatch/`, and `checkpoints/`.

## Convention

- One named subdirectory per experiment/series; datagen uses flat `<model>-<ctx>-datagen-<taskset>-<cluster>`.
- Trackers are usually `*.md`, with optional plots or per-run directories. `a3/` contains `a3_rl_tracker.md`, `a3_rl_experiments.md`, `a3_skipped_datasets.md`, `reward_plots/`, and a PDF report.
- Naming varies: inspect `*.md` first and use the user-named or most status-like tracker as source of truth.

## How to use it

- Create `experiments/active/<name>/` with a tracker; record the queue/plan and update status. Follow experiment pointers for canonical trackers.
- On a completed or changed run, update its tracker and `~/Documents/agent_logs/YYYY-MM-DD_<topic>.md`.
- This workspace is not OT-Agent git-tracked. Keep only trackers and small plots/reports; keep artifacts/checkpoints on cluster scratch.

## Migrating an experiment to `complete/`

Move concluded experiments from `active/` to `complete/` in one pass:

1. Move with `git mv`/`mv experiments/active/<name>/ experiments/complete/<name>/` and fix hard-coded `active/` references.
2. Remove every keep-N, refill, cron, or monitor rule from live cron and canonical `monitor-restore`, `monitor-restore-iris`, and `monitor-cron-sweep` references.
3. Add `CLOSED.md` with the conclusion date, final result/verdict (or its location), and retired rules.
4. Log closure in `~/Documents/agent_logs/YYYY-MM-DD_<topic>.md`.

Move `complete/ → active/` only when the operator explicitly re-opens it, then deliberately restore its autonomous rule.
