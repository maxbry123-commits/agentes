"""Unified per-model vLLM serve config — the single source of truth.

Replaces the two divergent sources of "what vLLM params does model X need":
  - eval/configs/model_configs.yaml (the eval-listener mono-file registry)
  - hpc/datagen_yaml/ (per-model datagen files)

Each model has ONE file at ``model_config/<org>/<slug>.yaml`` holding:
  - a small set of MODEL-INTRINSIC base fields (trust_remote_code, max_model_len,
    tool_call_parser, reasoning_parser, hf_overrides, limit_mm_per_prompt) — the
    constants that are the same regardless of who's serving;
  - ``subsystems:`` overlays keyed by consumer (``eval``, ``datagen``, ``iris``)
    carrying the workflow-specific stuff (TP/DP, swap_space, extra_args,
    conda_env, agent_kwargs). Intentional divergences (e.g. GLM-4.7 Pattern D
    omits parsers for eval but datagen needs them) live here;
  - ``variants:`` under each subsystem for hardware geometry (multi_gpu / gh200).

Resolution merge order (later wins): base -> subsystem(s) -> hardware variant.
"""

from model_config.resolver import (
    resolve_model_config,
    load_all_model_configs,
    find_model_file,
    MODEL_CONFIG_DIR,
)

__all__ = [
    "resolve_model_config",
    "load_all_model_configs",
    "find_model_file",
    "MODEL_CONFIG_DIR",
]
