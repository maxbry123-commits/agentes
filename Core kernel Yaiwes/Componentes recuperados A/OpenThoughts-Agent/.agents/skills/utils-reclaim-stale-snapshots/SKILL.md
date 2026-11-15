---
name: utils-reclaim-stale-snapshots
description: >-
  Reclaim idle Daytona SNAPSHOTS org-wide to free space under the 60-snapshot cap,
  using scripts/daytona/daytona_snapshot_manager.py. Deletes only harbor__ per-
  environment snapshots idle past the standing threshold GT'd in
  .agents/projects/daytona/daytona.md — NEVER the shared
  base/template images (daytonaio/sandbox:*, daytona-*, windows-*), which do not
  rebuild-on-demand. Use when a datagen/eval launch hits SnapshotCapExceeded, when a
  monitor sweep finds the cap full, or as routine cap hygiene. This is the org-wide
  RECLAIM tool; to shrink a SINGLE dataset's unique-environment count instead, use
  datagen-reduce-dataset-snapshots. Snapshots are a DIFFERENT resource from sandboxes
  (for sandbox cleanup use utils-cleanup-stale-sandboxes).
---

# utils-reclaim-stale-snapshots

Free Daytona snapshot quota by deleting idle `harbor__<hash>__snapshot` environments under the hard cap of **60**.

## Why this is safe (and what it must never touch)

Harbor builds one snapshot per task-environment hash (`harbor__<hash>__snapshot`). `auto_snapshot` rebuilds a
deleted idle snapshot on demand.

The base/template images (`daytonaio/sandbox:*`, `daytona-gpu`, `daytona-medium/large/small`, `windows-*`) are
shared and do not rebuild on demand. Keep `--name-prefix harbor__` so only Harbor snapshots are eligible.

For snapshots, `state=active` means built and available. Staleness uses `last_used_at`, falling back to
`created_at`; live-job environments remain below the idle threshold.

## Which org

Datagen/eval pre-build uses the **`cli` org** and `DAYTONA_API_KEY`. RL uses the separate `DAYTONA_RL_API_KEY` org.

## How to run

Always **audit (read-only) first**, then delete.

```bash
cd /Users/benjaminfeuer/Documents/OpenThoughts-Agent
source /Users/benjaminfeuer/miniconda3/etc/profile.d/conda.sh && conda activate otagent
source "${DC_AGENT_SECRET_ENV:?set DC_AGENT_SECRET_ENV to the secrets file first}"
PY=/Users/benjaminfeuer/miniconda3/envs/otagent/bin/python
SCRIPT=scripts/daytona/daytona_snapshot_manager.py

# 1. AUDIT — read-only, see what WOULD be reclaimed (at the stale threshold — see below)
$PY $SCRIPT --api-key-env DAYTONA_API_KEY --stale-days <threshold>

# 2. RECLAIM — actually delete the stale harbor__ snapshots
$PY $SCRIPT --api-key-env DAYTONA_API_KEY --stale-days <threshold> --delete-stale --yes
```

`--stale-days` accepts floats; use minutes/1440 for sub-day thresholds. The standing threshold is in
`.agents/projects/daytona/daytona.md` § "How to clean stale snapshots". Raise it for more conservative cleanup.

## Flags (this tool)

| Flag | Default | Purpose |
|---|---|---|
| `--api-key-env` | `DAYTONA_DATA_API_KEY` | Org key env var. **Use `DAYTONA_API_KEY`** for the cli/datagen org. |
| `--stale-days` | 14 | Idle-days threshold (float). Standing value GT'd in `.agents/projects/daytona/daytona.md` § "How to clean stale snapshots" — don't restate it here. |
| `--name-prefix` | `harbor__` | Only names starting with this are deletable. **Do not widen it** — the default guards base images. |
| `--delete-stale` | off (dry-run) | Actually delete. |
| `--yes` | off | Skip the confirm prompt (for scripted/cron use). |
| `--json` | off | Machine-readable output. |

## Gotchas

- **Source `$DC_AGENT_SECRET_ENV` + otagent env** — the `daytona` SDK lives in the otagent
  conda env; use the full interpreter path.
- **Never pass `--name-prefix ''`** with `--delete-stale` — that would make base
  images deletable. The tool is safe only with the `harbor__` default.
- Idle active `harbor__` snapshots are reclaimable.
- Reclaiming adds a one-time rebuild when the environment is next used.

## In the monitor sweep

The every-3-hours Iris sweep audits each tick and reclaims for blocked datagen refills or cap ≥ ~58/60. See
**monitor-cron-sweep-iris** §5.
