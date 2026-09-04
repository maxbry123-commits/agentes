---
name: datagen-standard-launch
description: >-
  Launch NON-AGENTIC (standard) data generation — plain vLLM/API completion generation with NO Harbor agent
  loop or Daytona sandboxes. Two paths: (1) Curator sharded datagen — the multi-node data-parallel
  run_curator_datagen_sharded.sbatch (one vLLM server per node, disjoint dataset slices, auto-resume, manual
  afterany restart chain, `curator` conda env, --account=reformo); (2) the declarative `generate.py` /
  class-based `generate_abstract.py` generators under data/ (data/generation BaseDataGenerator + InferenceEngine
  for OpenAI/Anthropic/vLLM). Use for bulk completion/synthetic-data generation. The AGENTIC trace-generation
  path (Harbor + Daytona rollouts, MiniMax/GLM trace sets) is the SEPARATE `datagen-launch` skill.
---

# datagen-standard-launch

Generate completions or synthetic data directly from a model, without Harbor or Daytona. For agentic trace-gen,
use `datagen-launch`.

---

## Path 1 — Curator sharded datagen (multi-node DP) — the primary path

`data/sbatches/run_curator_datagen_sharded.sbatch` runs one vLLM server per node over disjoint input slices and
merges the results. Default: **32 nodes** (`#SBATCH --nodes=32`, 4 GPUs/node), `--account=reformo` on Jupiter,
and the **`curator`** environment (not `otagent`).

**Auto-resume:** stable shard output paths
`data/sbatches/curator_runs/<model>__<dataset>__<N>shards/shard_<i>/checkpoint_*.parquet` let an `afterany`
restart resume after a SLURM timeout.

**Pre-req (login node, has internet):** cache the input dataset first —
```bash
conda activate curator
python -c "from datasets import load_dataset; ds=load_dataset('<dataset>',split='train'); print(len(ds))"
```

**Launch — positional args** `<model> <input_dataset> <output_repo> [limit] [save_every]`:
```bash
# Simple (no restarts):
sbatch data/sbatches/run_curator_datagen_sharded.sbatch <model> <input_dataset> <output_repo> [limit] [save_every]

# With restart chain (recommended for long datasets) — build the afterany chain MANUALLY:
FIRST=$(sbatch data/sbatches/run_curator_datagen_sharded.sbatch \
  <model> <input_dataset> <output_repo> [limit] [save_every] | awk '{print $4}')
PREV=$FIRST; for i in $(seq 1 6); do
  PREV=$(sbatch --dependency=afterany:$PREV \
    data/sbatches/run_curator_datagen_sharded.sbatch \
    <model> <input_dataset> <output_repo> [limit] [save_every] | awk '{print $4}')
done
```
- **`MAX_RESTARTS` is not implemented**; build the `--dependency=afterany:` chain by hand.
- **`save_every`: pass `700`, not the default 200** (the fifth positional arg).
- `limit` (4th arg) caps rows for a smoke run; omit for the full set.

---

## Path 2 — declarative / class-based generator scripts (`data/`)

`data/` has named pipeline directories in two styles:
- **Declarative `generate.py`** — self-contained scripts for local / one-off runs:
  ```bash
  python data/<dataset>/generate.py [--flags]
  ```
- **Class-based `generate_abstract.py`** — subclass `BaseDataGenerator` for HPC runs with launcher-managed vLLM
  endpoints, submitted through the unified launcher:
  ```bash
  python -m hpc.launch --job_type datagen \
    --datagen_script data/<dataset>/generate_abstract.py \
    --datagen_target_repo <org/repo> \
    --datagen_extra_args "--stage both --limit 2000"
  ```

Core modules in **`data/generation/`**: `base.py` (`BaseDataGenerator`), `schemas.py`
(`GenerationRequest`/`GenerationResult`), `engines.py` (`InferenceEngine` for OpenAI / Anthropic / vLLM).

---

## Cleanup / verification

Standard datagen pushes merged parquet shards to `<output_repo>`. Verify the row count and that the repo
self-populated; no Daytona/trace-export step applies. Cluster details: `.agents/ops/jupiter/`; launcher:
`.agents/projects/ot-agent/ot-agent.md`.
