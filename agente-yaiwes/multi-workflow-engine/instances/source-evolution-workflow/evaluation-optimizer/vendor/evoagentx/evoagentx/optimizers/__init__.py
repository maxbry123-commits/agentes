from __future__ import annotations
from importlib import import_module

__all__ = [
    "SEWOptimizer",
    "AFlowOptimizer",
    "TextGradOptimizer",
    "MiproOptimizer",
    "WorkFlowMiproOptimizer",
    "MapElitesOptimizer",
]

_EXPORTS = {
    "SEWOptimizer": ".sew_optimizer",
    "AFlowOptimizer": ".aflow_optimizer",
    "TextGradOptimizer": ".textgrad_optimizer",
    "MiproOptimizer": ".mipro_optimizer",
    "WorkFlowMiproOptimizer": ".mipro_optimizer",
    "MapElitesOptimizer": ".map_elites_optimizer",
}


def __getattr__(name: str):
    module_name = _EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    try:
        value = getattr(import_module(module_name, __name__), name)
    except ModuleNotFoundError as exc:
        if name in {"MiproOptimizer", "WorkFlowMiproOptimizer"} and exc.name == "optuna":
            raise ModuleNotFoundError(
                "Mipro optimizers require the optional dependency 'optuna'. "
                "Install it to use evoagentx.optimizers.MiproOptimizer or "
                "evoagentx.optimizers.WorkFlowMiproOptimizer."
            ) from exc
        raise

    globals()[name] = value
    return value


def __dir__():
    return sorted(set(globals()) | set(__all__))
