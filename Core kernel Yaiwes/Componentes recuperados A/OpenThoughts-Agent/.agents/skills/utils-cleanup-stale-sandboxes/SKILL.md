---
name: utils-cleanup-stale-sandboxes
description: >-
  Delete stale Daytona sandboxes across ALL THREE orgs (DataComp, DataCompData,
  DataCompRL) in one pass. Runs `scripts/daytona/cleanup_stale_sandboxes.py`
  three times — once per org — each time setting the org's API key via
  `--api-key-env` so the script queries and deletes in the correct org. Default
  threshold is 60 minutes of inactivity; `--delete` actually removes them (dry
  run otherwise). Use when the Daytona sandbox count is climbing (eval/datagen/RL
  sandboxes left behind after jobs finish), when a sweep flags stale sandboxes,
  or when approaching the org snapshot/sandbox cap.
---

# utils-cleanup-stale-sandboxes

Delete stale Daytona sandboxes across the three orgs.

## When to use

- Daytona sandbox count is climbing — stale sandboxes left behind after eval / datagen / RL jobs finish.
- A sweep flags stale sandboxes or the org approaches its cap.
- Before a large eval, datagen, or RL launch.
- Routine hygiene during heavy operations.

## The three orgs

| Org | API key env var | Typical sandboxes |
|---|---|---|
| **DataComp** (main) | `DAYTONA_API_KEY` | Eval (terminus-2 agent sandboxes) |
| **DataCompData** | `DAYTONA_DATA_API_KEY` | Datagen (trace-generation rollouts) |
| **DataCompRL** | `DAYTONA_RL_API_KEY` | RL (SkyRL/GRPO agentic rollouts) |

Source `$DC_AGENT_SECRET_ENV` to set all three variables. `--api-key-env` selects the org for each invocation.

## How to invoke

**Locally (Mac)** — uses the otagent conda env's Python:

```bash
set -a; source "${DC_AGENT_SECRET_ENV:?set DC_AGENT_SECRET_ENV to the secrets file first}"; set +a

PY=/Users/benjaminfeuer/miniconda3/envs/otagent/bin/python
SCRIPT=scripts/daytona/cleanup_stale_sandboxes.py
THRESHOLD=60   # minutes of inactivity

for KEY_ENV in DAYTONA_API_KEY DAYTONA_DATA_API_KEY DAYTONA_RL_API_KEY; do
    echo "============================================"
    echo "Org: $KEY_ENV"
    echo "============================================"
    $PY $SCRIPT --api-key-env "$KEY_ENV" --threshold "$THRESHOLD" --delete
    echo
done
```

**Dry run:** omit `--delete`.

```bash
for KEY_ENV in DAYTONA_API_KEY DAYTONA_DATA_API_KEY DAYTONA_RL_API_KEY; do
    $PY $SCRIPT --api-key-env "$KEY_ENV" --threshold "$THRESHOLD"
done
```

**Custom threshold** — pass `--threshold <minutes>` (default 60):

```bash
# Only clean sandboxes inactive for >2 hours
THRESHOLD=120
```

## Flags

| Flag | Default | Purpose |
|---|---|---|
| `--delete` | off (dry run) | Actually delete stale sandboxes |
| `--threshold` | 60 | Minutes of inactivity before a sandbox is considered stale |
| `--api-key-env` | `DAYTONA_API_KEY` | Which env var holds the org's API key |

## Gotchas

- **Must source `$DC_AGENT_SECRET_ENV` first** — all three `DAYTONA_*` env vars must be
  set before running the loop, or the script will exit with
  `ERROR: ... not set in environment`.
- **Run from the otagent env** — the `daytona` SDK must be installed (it is in
  the `otagent` conda env; NOT in the base env). Use the full interpreter path
  `/Users/benjaminfeuer/miniconda3/envs/otagent/bin/python`.
- **RL (`DAYTONA_RL_API_KEY`) may have long-lived sandboxes.** Raise its threshold if active sandboxes are selected.
- **Dry run first** when unsure.
