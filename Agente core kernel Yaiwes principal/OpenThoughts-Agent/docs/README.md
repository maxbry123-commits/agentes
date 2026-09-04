# `docs/` — OpenThoughts-Agent reference documentation

Centralized, labeled reference docs for the OT-Agent subsystems. Operational
how-tos (the per-task skills) and machine/cluster particulars live under
`.agents/` (skills / ops / projects) — this directory holds the longer-form
subsystem references.

| Doc | Covers |
|---|---|
| [`RL_PIPELINE.md`](RL_PIPELINE.md) | End-to-end RL (SkyRL/GRPO) training pipeline. |
| [`DATASET_GENERATION.md`](DATASET_GENERATION.md) | Datagen / trace-generation pipeline. |
| [`EVAL_GUIDE.md`](EVAL_GUIDE.md) | Cluster-diagnostic eval listener stack — firing categories, Pinggy, vLLM serving patterns, failure-mode catalog, resume, recovery scripts. |
| [`PREFERRED_HARNESS_REPRODUCTION.md`](PREFERRED_HARNESS_REPRODUCTION.md) | Per-model recipes for reproducing paper accuracy via the author's intended scaffold (Cat 3 of the eval guide). |
| [`RESUME_HANDOFF.md`](RESUME_HANDOFF.md) | Cross-cluster eval-listener resume bug catalogue + verification checklist (G10/G12/G13 + harbor #1617). |
| [`HARBOR_YAML_GROUND_TRUTH.md`](HARBOR_YAML_GROUND_TRUTH.md) | `hpc/harbor_yaml/` as the single source of truth for Harbor harness configs — layout, size-selection rule, `--config-yaml` resolution (no symlinks), deprecated-config blocklist. |
