"""Shared consumption of the ``model_config/`` registry for the launch entrypoints.

``model_config/resolver.py:resolve_model_config`` is the SINGLE layering
implementation (base intrinsics -> subsystem overlay -> hardware variant, with a
regex-pattern fallback from ``model_config/_patterns.yaml``). This module maps a
resolved config dict onto a launcher / local-runner ``argparse`` namespace so that
all six eval + datagen launch entrypoints resolve serve config the same way, with
no per-entrypoint drift.

Contract (mirrors the existing ``--preset`` precedence):
  * Explicit CLI flags (and datagen-config values already applied to ``args``)
    ALWAYS win; the model_config only fills in what the operator didn't specify.
  * A model with no ``model_config/`` entry (and no matching pattern) resolves to
    ``{}`` and leaves ``args`` untouched — launches for unregistered models behave
    exactly as before.
  * Every entrypoint emits one transparency log line showing applied vs ignored
    fields.

Field mapping:
  * Parallelism (``tensor_parallel_size`` / ``pipeline_parallel_size`` /
    ``data_parallel_size``) -> the corresponding ``args`` attributes.
  * vLLM serve intrinsics (``max_model_len`` / ``limit_mm_per_prompt`` /
    ``trust_remote_code`` / ``hf_overrides`` / ``swap_space`` /
    ``tool_call_parser`` / ``reasoning_parser`` / ``extra_args``) -> the same
    ``vllm serve`` CLI flags the datagen-config path produces, via
    ``hpc.vllm_utils._build_vllm_cli_args``, appended to ``args._vllm_cli_args``
    only where the datagen config hasn't already set that flag.
  * ``agent_kwargs`` -> merged (dedup by key; existing wins) into
    ``args.agent_kwarg``.
  * ``conda_env`` -> ignored (no runtime consumer in this launch path; the SLURM
    listener owns env activation).

NOTE: ``model_config/`` currently declares only the ``eval`` subsystem, which
holds the shared serve profile; datagen resolves against it too (``subsystem``
defaults to ``"eval"``) so tracegen picks up the same tp / max_model_len / etc.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

# vLLM serve intrinsics that map to `vllm serve` CLI flags via _build_vllm_cli_args
# (the SAME translation the datagen-config vllm_server block uses). Parallelism,
# agent_kwargs and conda_env are handled/ignored separately, so NOT listed here.
SERVE_VLLM_FIELDS: Tuple[str, ...] = (
    "max_model_len",
    "limit_mm_per_prompt",
    "trust_remote_code",
    "hf_overrides",
    "swap_space",
    "tool_call_parser",
    "reasoning_parser",
    "extra_args",
)

PARALLELISM_FIELDS: Tuple[str, ...] = (
    "tensor_parallel_size",
    "pipeline_parallel_size",
    "data_parallel_size",
)


def resolve_launch_config(
    model: Optional[str],
    hardware: Optional[str] = None,
    subsystem: str = "eval",
    log_prefix: str = "[model-config]",
) -> Dict[str, Any]:
    """Resolve ``model`` against ``model_config/`` (or ``{}`` on miss / no model)."""
    if not model:
        return {}
    try:
        from model_config.resolver import resolve_model_config

        return resolve_model_config(model, subsystem=subsystem, hardware=hardware) or {}
    except Exception as e:  # pragma: no cover - defensive; never break a launch
        print(
            f"{log_prefix} WARNING: model_config resolution failed for {model!r}: {e}"
        )
        return {}


def _kwarg_key(kw: str) -> str:
    return kw.split("=", 1)[0]


def merge_agent_kwargs(args, resolved: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    """Merge resolved ``agent_kwargs`` into ``args.agent_kwarg`` (dedup by key).

    Existing entries (from the CLI or an already-applied preset) win. Returns
    ``(applied, ignored)`` lists of ``key=value`` strings.
    """
    applied: List[str] = []
    ignored: List[str] = []
    mc_kwargs = resolved.get("agent_kwargs") or []
    if not mc_kwargs:
        return applied, ignored
    existing = list(getattr(args, "agent_kwarg", None) or [])
    keys = {_kwarg_key(k) for k in existing}
    for kw in mc_kwargs:
        if _kwarg_key(kw) in keys:
            ignored.append(kw)
        else:
            existing.append(kw)
            keys.add(_kwarg_key(kw))
            applied.append(kw)
    args.agent_kwarg = existing
    return applied, ignored


def _serve_dict(resolved: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for k in SERVE_VLLM_FIELDS:
        if k in resolved and resolved[k] not in (None, ""):
            v = resolved[k]
            # model_config stores extra_args as a whitespace-joined string;
            # _build_vllm_cli_args only expands a LIST, so normalize here.
            if k == "extra_args" and isinstance(v, str):
                v = v.split()
            out[k] = v
    return out


def _flag_base(tok: str) -> str:
    name = tok[2:]
    return name[3:] if name.startswith("no-") else name


def _existing_flag_bases(cli: List[str]) -> set:
    return {_flag_base(t) for t in cli if isinstance(t, str) and t.startswith("--")}


def apply_vllm_serve(args, resolved: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    """Fill ``args._vllm_cli_args`` with model_config serve flags not already set.

    Returns ``(applied, skipped)`` where ``applied`` is the list of newly added
    flag bases (``key`` or ``key=value``) and ``skipped`` the bases the
    datagen-config already provided (datagen wins).
    """
    from hpc.vllm_utils import _build_vllm_cli_args

    serve = _serve_dict(resolved)
    if not serve:
        return [], []

    mc_cli, mc_env = _build_vllm_cli_args(serve)
    # _build_vllm_cli_args injects `--no-enable-prefix-caching` as a
    # belt-and-suspenders opt-out when nothing requested prefix caching. That
    # heuristic is meant to run once over the WHOLE serve config; here it would
    # clobber the datagen-config / vLLM default, so drop it unless the
    # model_config actually asked for prefix caching.
    if (
        "--enable-prefix-caching" not in mc_cli
        and "--no-enable-prefix-caching" in mc_cli
    ):
        mc_cli = [t for t in mc_cli if t != "--no-enable-prefix-caching"]

    existing = list(getattr(args, "_vllm_cli_args", None) or [])
    existing_bases = _existing_flag_bases(existing)

    applied: List[str] = []
    skipped: List[str] = []
    add: List[str] = []
    i = 0
    while i < len(mc_cli):
        tok = mc_cli[i]
        if isinstance(tok, str) and tok.startswith("--"):
            base = _flag_base(tok)
            has_val = (i + 1 < len(mc_cli)) and not str(mc_cli[i + 1]).startswith("--")
            val = mc_cli[i + 1] if has_val else None
            if base in existing_bases:
                skipped.append(base)
            else:
                add.append(tok)
                if has_val:
                    add.append(val)
                existing_bases.add(base)
                applied.append(base if not has_val else f"{base}={val}")
            i += 2 if has_val else 1
        else:
            add.append(tok)
            i += 1

    if add:
        args._vllm_cli_args = existing + add
    if mc_env:
        env = dict(getattr(args, "_vllm_env_vars", None) or {})
        for k, v in mc_env.items():
            env.setdefault(k, v)  # datagen-config env wins
        args._vllm_env_vars = env

    return applied, skipped


def apply_parallelism(args, resolved: Dict[str, Any]) -> Dict[str, Any]:
    """Set parallelism args from model_config where not already specified."""
    applied: Dict[str, Any] = {}
    for f in PARALLELISM_FIELDS:
        if f in resolved and getattr(args, f, None) is None:
            setattr(args, f, resolved[f])
            applied[f] = resolved[f]
    return applied


def apply_to_runner(
    args,
    *,
    log_prefix: str,
    hardware: Optional[str] = None,
    subsystem: str = "eval",
    apply_parallelism_fields: bool = True,
    needs_local_vllm: bool = True,
) -> None:
    """Resolve + apply model_config onto a LocalHarborRunner's ``args``.

    ``apply_parallelism_fields=False`` (iris) leaves tp/pp/dp alone — iris derives
    tensor-parallel from the TPU chip count — and logs them as ignored.
    """
    resolved = resolve_launch_config(
        getattr(args, "model", None),
        hardware=hardware,
        subsystem=subsystem,
        log_prefix=log_prefix,
    )
    if not resolved:
        print(
            f"{log_prefix} model_config: no entry for {getattr(args, 'model', None)!r}; "
            f"using existing defaults."
        )
        return

    applied: Dict[str, Any] = {}
    ignored: Dict[str, Any] = {}

    ak_applied, ak_ignored = merge_agent_kwargs(args, resolved)
    if ak_applied:
        applied["agent_kwargs"] = ak_applied
    if ak_ignored:
        ignored["agent_kwargs(already-set)"] = ak_ignored

    if needs_local_vllm:
        if apply_parallelism_fields:
            applied.update(apply_parallelism(args, resolved))
        else:
            for f in PARALLELISM_FIELDS:
                if f in resolved:
                    ignored[f] = resolved[f]
        sv_applied, sv_skipped = apply_vllm_serve(args, resolved)
        if sv_applied:
            applied["serve"] = sv_applied
        if sv_skipped:
            ignored["serve(already-set)"] = sv_skipped

    if "conda_env" in resolved:
        ignored["conda_env"] = resolved["conda_env"]

    print(
        f"{log_prefix} model_config {getattr(args, 'model', None)}: "
        f"applied {applied}; ignored {ignored}"
    )


def apply_to_launcher(
    args,
    *,
    log_prefix: str,
    hardware: Optional[str] = None,
    subsystem: str = "eval",
    iris: bool = False,
) -> None:
    """Resolve + apply model_config at LAUNCH time (cloud / iris wrappers).

    The launcher genuinely applies ``agent_kwargs`` (they are forwarded via
    ``--agent_kwarg`` and dedup-merged again by the worker's run_eval/run_tracegen).
    The vLLM serve intrinsics + parallelism are resolved + applied downstream on
    the worker (which reads the same ``model_config/``); they are surfaced here for
    transparency. On iris, parallelism + ``harbor_config`` are noted as ignored
    (tp derives from the TPU chip count; ``--harbor_config`` is CLI-required).
    """
    resolved = resolve_launch_config(
        getattr(args, "model", None),
        hardware=hardware,
        subsystem=subsystem,
        log_prefix=log_prefix,
    )
    if not resolved:
        print(
            f"{log_prefix} model_config: no entry for {getattr(args, 'model', None)!r} "
            f"(resolution deferred to the worker if the model is inferred there)."
        )
        return

    applied: Dict[str, Any] = {}
    ignored: Dict[str, Any] = {}

    ak_applied, ak_ignored = merge_agent_kwargs(args, resolved)
    if ak_applied:
        applied["agent_kwargs"] = ak_applied
    if ak_ignored:
        ignored["agent_kwargs(already-set)"] = ak_ignored

    serve_note = {k: resolved[k] for k in SERVE_VLLM_FIELDS if k in resolved}
    par_fields = {k: resolved[k] for k in PARALLELISM_FIELDS if k in resolved}
    if iris:
        # tp derived from TPU chips; harbor_config CLI-required -> ignored on iris.
        for k, v in par_fields.items():
            ignored[k] = v
    else:
        serve_note.update(par_fields)

    if "conda_env" in resolved:
        ignored["conda_env"] = resolved["conda_env"]

    print(
        f"{log_prefix} model_config {getattr(args, 'model', None)}: applied {applied}; "
        f"serve-config (applied on worker): {serve_note}; ignored {ignored}"
    )
