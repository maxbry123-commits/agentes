"""Compatibility shim for Harbor dataset-config classes.

Harbor unified ``LocalDatasetConfig`` and ``RegistryDatasetConfig`` into a single
``DatasetConfig`` class:

  - Local datasets:    ``DatasetConfig(path=Path(...))``
  - Registry datasets: ``DatasetConfig(name="...")``
  - Discrimination:    ``cfg.is_local()`` / ``cfg.is_registry()`` /
                       ``cfg.is_package()``

This module exposes the legacy names regardless of which Harbor version is
installed so existing OT-Agent callers keep working.

Usage::

    from scripts.harbor._harbor_compat import (
        LocalDatasetConfig,
        RegistryDatasetConfig,
        is_local_dataset,
    )

    config.datasets = [LocalDatasetConfig(path=path)]  # works on both Harbors
    ...
    if is_local_dataset(dataset):                       # safe replacement for
        ...                                             # isinstance(..., LocalDatasetConfig)
"""

from __future__ import annotations

import asyncio
import inspect

try:
    # Legacy Harbor: distinct classes.
    from harbor.models.job.config import (  # type: ignore[attr-defined]
        LocalDatasetConfig,
        RegistryDatasetConfig,
    )

    _UNIFIED_DATASET_CONFIG = False
except ImportError:
    # Unified Harbor: one DatasetConfig class handles both shapes.
    from harbor.models.job.config import DatasetConfig as _DatasetConfig

    LocalDatasetConfig = _DatasetConfig
    RegistryDatasetConfig = _DatasetConfig
    _UNIFIED_DATASET_CONFIG = True


def is_local_dataset(dataset) -> bool:
    """Return True iff ``dataset`` represents a local-path dataset.

    Safe replacement for ``isinstance(dataset, LocalDatasetConfig)`` that works
    on both legacy and unified Harbor. On unified Harbor ``LocalDatasetConfig
    is DatasetConfig``, so the legacy isinstance check would return True for
    ALL DatasetConfig instances; the unified ``is_local()`` checks ``path is
    not None``.
    """
    if hasattr(dataset, "is_local") and callable(dataset.is_local):
        return bool(dataset.is_local())
    return isinstance(dataset, LocalDatasetConfig)


__all__ = [
    "LocalDatasetConfig",
    "RegistryDatasetConfig",
    "is_local_dataset",
    "_UNIFIED_DATASET_CONFIG",
    "OrchestratorEvent",
    "TrialEvent",
    "TRIAL_COMPLETED_EVENT",
    "OrchestratorConfig",
    "build_job_config_kwargs",
    "set_orchestrator_field",
    "get_orchestrator_field",
    "add_trial_completed_hook",
    "create_job",
    "create_job_async",
    "_UNIFIED_ORCHESTRATOR",
]


# ---------------------------------------------------------------------------
# Orchestrator-concept breaking change.
#
# Legacy Harbor: OrchestratorEvent from harbor.orchestrators.base, OrchestratorConfig
# nested on JobConfig, hooks via job._orchestrator.add_hook.
# Unified Harbor: harbor.orchestrators is gone; TrialEvent.END replaces
# OrchestratorEvent.TRIAL_COMPLETED; OrchestratorConfig removed (n_concurrent_trials,
# quiet, retry are top-level on JobConfig); hooks via Job.add_hook / on_trial_completed.
# This shim hides the difference so existing callers keep working.
# ---------------------------------------------------------------------------

try:
    # Legacy Harbor: distinct orchestrator module.
    from harbor.orchestrators.base import OrchestratorEvent  # type: ignore[import-not-found]

    TrialEvent = OrchestratorEvent
    TRIAL_COMPLETED_EVENT = OrchestratorEvent.TRIAL_COMPLETED
    _UNIFIED_ORCHESTRATOR = False
except ImportError:
    # Unified Harbor: TrialEvent.END replaces OrchestratorEvent.TRIAL_COMPLETED.
    from harbor.trial.hooks import TrialEvent  # type: ignore[attr-defined]

    OrchestratorEvent = TrialEvent  # type: ignore[assignment]
    TRIAL_COMPLETED_EVENT = TrialEvent.END
    _UNIFIED_ORCHESTRATOR = True


try:
    # Legacy Harbor: OrchestratorConfig was a nested dataclass on JobConfig.
    from harbor.models.job.config import OrchestratorConfig  # type: ignore[attr-defined]

    _HAS_ORCHESTRATOR_CONFIG = True
except ImportError:
    OrchestratorConfig = None  # type: ignore[assignment, misc]
    _HAS_ORCHESTRATOR_CONFIG = False


def build_job_config_kwargs(
    *,
    n_concurrent_trials: int | None = None,
    quiet: bool | None = None,
    retry: object | None = None,
    **other_kwargs,
) -> dict:
    """Return the right shape of kwargs for ``JobConfig(**kwargs)``.

    On legacy Harbor: nests concurrency/quiet/retry inside an
    ``orchestrator=OrchestratorConfig(...)`` parameter.
    On unified Harbor: places them at the top level.

    Other kwargs (``job_name``, ``jobs_dir``, ``datasets``, ``agents``, etc.)
    are forwarded as-is. Pass ``None`` to skip a field entirely.
    """
    kwargs: dict = dict(other_kwargs)
    if _HAS_ORCHESTRATOR_CONFIG and OrchestratorConfig is not None:
        orch_kwargs: dict = {}
        if n_concurrent_trials is not None:
            orch_kwargs["n_concurrent_trials"] = n_concurrent_trials
        if quiet is not None:
            orch_kwargs["quiet"] = quiet
        if retry is not None:
            orch_kwargs["retry"] = retry
        if orch_kwargs:
            kwargs["orchestrator"] = OrchestratorConfig(**orch_kwargs)
    else:
        if n_concurrent_trials is not None:
            kwargs["n_concurrent_trials"] = n_concurrent_trials
        if quiet is not None:
            kwargs["quiet"] = quiet
        if retry is not None:
            kwargs["retry"] = retry
    return kwargs


def set_orchestrator_field(config, field: str, value) -> None:
    """Apply what used to be ``config.orchestrator.<field> = value``.

    On legacy Harbor: writes ``config.orchestrator.<field>`` (the nested
    OrchestratorConfig).
    On unified Harbor: writes ``config.<field>`` at the top level of the
    JobConfig, because the orchestrator nesting was flattened.

    Use this in place of direct attribute assignment so callers don't need
    to know which Harbor version is installed.
    """
    orch = getattr(config, "orchestrator", None)
    if orch is not None:
        setattr(orch, field, value)
        return
    setattr(config, field, value)


def get_orchestrator_field(config, field: str, default=None):
    """Read what used to be ``config.orchestrator.<field>``.

    Falls back to the unified Harbor's top-level field when the legacy
    nested ``orchestrator`` is absent. Returns ``default`` if neither
    location has the field.

    Supports both Pydantic models and plain dicts (the latter for raw YAML
    pre-validation: new YAML may have top-level ``n_concurrent_trials``,
    old YAML may have nested ``orchestrator: {n_concurrent_trials: N}``).
    """
    # Dict-form (parsed YAML before Pydantic validation).
    if isinstance(config, dict):
        orch = config.get("orchestrator")
        if isinstance(orch, dict) and field in orch:
            return orch[field]
        if field in config:
            return config[field]
        return default

    # Pydantic / dataclass form.
    orch = getattr(config, "orchestrator", None)
    if orch is not None:
        v = getattr(orch, field, None)
        if v is not None:
            return v
    return getattr(config, field, default)


def add_trial_completed_hook(job, callback) -> None:
    """Attach ``callback`` to the trial-completed event on ``job``.

    Resolution order (most preferred first):
      1. ``job.on_trial_completed(callback)`` — unified Harbor convenience method.
      2. ``job.add_hook(TRIAL_COMPLETED_EVENT, callback)`` — unified Harbor public API.
      3. ``job._orchestrator.add_hook(TRIAL_COMPLETED_EVENT, callback)`` — legacy.

    Raises ``RuntimeError`` if none of the surfaces exist (unknown Harbor API).
    """
    if hasattr(job, "on_trial_completed") and callable(job.on_trial_completed):
        job.on_trial_completed(callback)
        return
    if hasattr(job, "add_hook") and callable(job.add_hook):
        job.add_hook(TRIAL_COMPLETED_EVENT, callback)
        return
    orch = getattr(job, "_orchestrator", None)
    if orch is not None and hasattr(orch, "add_hook"):
        orch.add_hook(TRIAL_COMPLETED_EVENT, callback)
        return
    raise RuntimeError(
        "Unable to attach trial-completed hook: Job exposes neither "
        "on_trial_completed nor add_hook nor _orchestrator.add_hook. "
        "Harbor API may have changed again — update _harbor_compat.py."
    )


# ---------------------------------------------------------------------------
# Job construction: ``Job(config)`` → ``await Job.create(config)``.
#
# Unified Harbor split construction: Job.__init__ is sync but requires
# _task_configs/_metrics pre-resolved (async); the public constructor is the
# async classmethod Job.create(config). Direct Job(config) raises ValueError.
# Legacy Job(config, **kwargs) also accepted extras like enable_progress_log;
# the new Job.create() only takes config (extras dropped on the unified path).
# ---------------------------------------------------------------------------


def _uses_async_factory(JobCls) -> bool:
    """Detect whether ``JobCls`` exposes the new async ``create`` classmethod."""
    create = getattr(JobCls, "create", None)
    if create is None:
        return False
    return inspect.iscoroutinefunction(create)


def create_job(JobCls, config, **kwargs):
    """Sync helper to instantiate a Harbor ``Job`` across legacy/unified APIs.

    Resolution order:
      1. ``Job.create`` exists as async classmethod → ``asyncio.run(JobCls.create(config))``.
         ``kwargs`` are dropped (unified API only takes ``config``).
      2. Else → ``JobCls(config, **kwargs)`` (legacy direct construction).

    MUST be called from synchronous context (uses ``asyncio.run``). For async
    callers, use ``create_job_async`` instead.
    """
    if _uses_async_factory(JobCls):
        return asyncio.run(JobCls.create(config))
    return JobCls(config, **kwargs)


async def create_job_async(JobCls, config, **kwargs):
    """Async helper to instantiate a Harbor ``Job`` across legacy/unified APIs.

    Resolution order:
      1. ``Job.create`` exists as async classmethod → ``await JobCls.create(config)``.
         ``kwargs`` are dropped (unified API only takes ``config``).
      2. Else → ``JobCls(config, **kwargs)`` (legacy direct construction).
    """
    if _uses_async_factory(JobCls):
        return await JobCls.create(config)
    return JobCls(config, **kwargs)
