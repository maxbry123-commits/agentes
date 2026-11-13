# `hpc/harbor_yaml/` — single source of truth for Harbor harness config YAMLs

`hpc/harbor_yaml/` is **THE** authoritative home for every Harbor harness config YAML in the
repo — the configs consumed by the Harbor agentic harness via `harbor jobs start --config`
(eval) and the unified launcher / listener (datagen + eval). If you are looking for "which
config is authoritative," the answer is: **here.** No other location holds a *real* Harbor
config (the one documented exception below is not part of the central launch surface).

> **NO symlinks.** As of commit `b355163f` there are no `eval/configs/dcagent_*` compat
> symlinks. Both `eval/{jupiter,leonardo}/eval_harbor.sbatch` resolvers and the listener's
> `_resolve_agent_name_from_config_yaml()` take a `--config-yaml <basename>` and resolve it
> **directly** from `hpc/harbor_yaml/eval/configs/`. Edit configs here; there is no second
> place to keep in sync.

A **Harbor config** carries the harness schema (`orchestrator` / `environment` / `verifier` /
`agents` / `datasets` / `timeout_multiplier` …). It is NOT a vLLM serving config
(`baseline_model_configs*.yaml`, `api_model_configs.yaml`), a listener cluster-config
(`eval/clusters/*.yaml`), or a benchmark preset (`eval/presets/*.yaml`) — those are separate
layers and live elsewhere on purpose.

## Layout

```
hpc/harbor_yaml/
├── eval/                                   # agentic-EVAL Harbor configs
│   ├── dcagent_eval_defaults.yaml          # CANONICAL 8B-class default (timeout_multiplier 2.0)
│   ├── dcagent_eval_defaults_32b.yaml      # CANONICAL 32B-class default (timeout_multiplier 16.0)
│   ├── configs/                            # the SLURM listener/sbatch `--config-yaml` family
│   │   ├── dcagent_eval_config.yaml             # listener default (terminus-2)
│   │   ├── dcagent_eval_config_no_override.yaml # LIVE Leonardo + every preset's default
│   │   ├── dcagent_eval_config_swe_agent.yaml
│   │   ├── dcagent_eval_config_openhands{,_qwen3_coder,_toolcall}.yaml
│   │   ├── dcagent_eval_config_mini_swe_agent.yaml
│   │   └── dcagent_eval_config_aider_agent_nothink.yaml
│   ├── eval_ctx{32k,131k}.yaml             # named context-length eval harnesses
│   ├── eval_{mini_swe,openhands}_ctx*.yaml # installed-harness eval variants
│   ├── {openhands,swe_agent}_ctx32k_eval_.yaml
│   └── extra/                              # debug / API / 100-task / kira / yarn / modal variants
├── datagen/                                # non-agentic + API datagen Harbor configs
├── datagen_apptainer/  datagen_docker/  datagen_podman/   # runtime-specific trace-gen configs
```

## The size-selection rule (eval defaults)

The unified eval listener selects the canonical default **by model size**, so a normal
agentic eval needs no `--harbor-config` flag:

| model size (param count from HF name) | selected config                          | timeout multiplier |
|---|---|---|
| **8B-class** (≤ ~14B; 1.5B/7B/8B/14B)  | `hpc/harbor_yaml/eval/dcagent_eval_defaults.yaml`        | **2×** (in the file) |
| **32B-class** (~28–42B; incl. MoE 30b-a3b) | `hpc/harbor_yaml/eval/dcagent_eval_defaults_32b.yaml` | **16×** (in the file) |
| out-of-band / no size token in name    | base default `dcagent_eval_defaults.yaml` | 2× (+ logged note) |

The two files have an identical body; **only `timeout_multiplier` differs.** Keep them in
sync. The multiplier lives IN the file (not a CLI default). See
`.agents/skills/eval-agentic-launch/SKILL.md` §3b for the full policy.

## How `--config-yaml` resolves (no symlinks)

The live SLURM path takes a **bare basename** on `--config-yaml` and resolves it directly
from `hpc/harbor_yaml/eval/configs/`:
- `eval/leonardo/eval_harbor.sbatch` (the LIVE Leonardo path) and the
  `eval/jupiter/eval_harbor.sbatch` (Jupiter path) resolve the basename against `hpc/harbor_yaml/eval/configs/`.
- All `eval/presets/*.yaml` forward `config_yaml: dcagent_eval_config_no_override.yaml`.
- The listener's `_resolve_agent_name_from_config_yaml()` resolves the same way.

There is **no** `eval/configs/dcagent_*` shim anymore (deleted in `b355163f`). Edit the config
**here** under `hpc/harbor_yaml/eval/configs/` — it is the only copy.

## Documented exception (real Harbor config that intentionally lives elsewhere)

This is NOT part of the central launch surface and is kept in place on purpose:

- **`data/nl2bash_sampled_verified/validation/job.yaml`** — a dataset-local validation
  fixture (a tiny `agents: [oracle]` local-docker config with relative `jobs_dir:
  ../local_runs/...`), used only by its sibling `validate.sh`. It travels with its dataset
  and is not a launch config.

## Deprecated configs — DO NOT resurrect

The `eval_ctx*_non_it*.yaml` / `ctx32k_non_it_16x_eval_.yaml` family was **deleted**
(commit `928698e0`). They carried the `penfever/temp-override`-era `mean-drop-ei` /
`accuracy-drop-ei` metrics that no Marin-branch Harbor `JobConfig` accepts — loading one
raises a `JobConfig` ValidationError. **Do not re-add `mean-drop-ei` / `accuracy-drop-ei`
metrics or recreate these configs.** Use the size-selected `dcagent_eval_defaults{,_32b}.yaml`.
