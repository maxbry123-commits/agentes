# hpc/skyrl_standard/leonardo

The **reusable** STANDARD / non-agentic (GRPO) SkyRL launch machinery for CINECA
**Leonardo** (A100-64GB). This is the small, curated core kept in-repo:

- `run_gsm8k_canary.sh` + `sbatch_gsm8k_canary.sh` — the gsm8k GRPO canary
  smoke-test (fast 1-node sanity run that the launch pipeline is healthy).
- `math_dataset.py` — the MATH/aime dataset builder (parquet for the `aime` env).
- `note.txt` — canary provenance / knob notes.

## How it launches (NOT the iris agentic path)

These run via **raw `sbatch`** of the `sbatch_*.sh` scripts, which
`singularity exec` a **writable apptainer sandbox dir** and use the external
uv-resolved `marin_venv`. This is deliberately **not** `python -m hpc.launch` +
a YAML and **not** a `.sif` / `--rl_use_conda` — that YAML-driven flow is the
Iris *agentic* (Harbor/Daytona) path. Standard GRPO on Leonardo has no
Harbor/Daytona/`trace_jobs/` and logs to `console`.

- Governing skill: **`rl-standard-launch-leonardo`**
- Cleanup skill:  **`rl-standard-job-cleanup`**

## History

This dir was carved out of the misnamed `hpc/skyrl_yaml/leonardo/` (it never held
YAML) on **2026-07-08**. The full script sets for the COMPLETED experiments that
also lived there were migrated out of the repo to the local experiment tracker:

- `experiments/complete/delphi/scripts/` — the Delphi math-RL run/sbatch scripts + `rl_dataset_prep.py` (+ `leonardo_rl_grid.md`).
- `experiments/complete/gsm8k_grid_leonardo/scripts/` — the gsm8k / MATH / ext2 accuracy-grid launchers + `harvest.py`.
- `experiments/complete/opd_grid_leonardo/scripts/` — the OPD + throughput-grid launchers.
