"""Environment setup for Iris task containers."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from hpc.iris.accelerator import ResolvedIrisAccelerator


# Object-storage credential/endpoint keys that must NOT be forwarded from the
# launch host into a CoreWeave GPU task pod. The cw-us-east-02a cluster projects
# an ``iris-task-env`` k8s Secret into every task pod via ``envFrom`` (because
# storage.remote_state_dir is an s3:// URI); that Secret already carries the
# correct in-cluster R2 credentials + endpoint (AWS_ACCESS_KEY_ID /
# AWS_SECRET_ACCESS_KEY / AWS_ENDPOINT_URL / AWS_REGION / FSSPEC_S3). Explicit
# container ``env`` entries take precedence over ``envFrom``, so forwarding the
# launch host's AWS_*/LAION_* (a DIFFERENT account, no endpoint) would CLOBBER
# the pod's injected creds and make Harbor's ``--jobs-dir=s3://marin-us-east-02a/...``
# write fail with HeadObject 400. We let the cluster-injected creds win, exactly as
# rl/cloud/launch_rl_iris.py does for the RL rendezvous. NOTE: the default object
# store moved R2 (s3://marin-na) -> CW (s3://marin-us-east-02a) on 2026-07-05
# (marin c7caecc95a); pods now inject CW creds+AWS_ENDPOINT_URL and can no longer
# reach s3://marin-na (R2).
_GPU_STORAGE_CRED_KEYS = frozenset(
    {
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_SESSION_TOKEN",
        "AWS_ENDPOINT_URL",
        "AWS_REGION",
        "AWS_DEFAULT_REGION",
        "LAION_ENDPOINT",
        "LAION_ACCESS_KEY",
        "LAION_SECRET_KEY",
        "LAION_BUCKET_NAME",
        "MARIN_PREFIX",
        "R2_ENDPOINT",
        "R2_ACCESS_KEY_ID",
        "R2_SECRET_ACCESS_KEY",
    }
)


def default_secrets_env() -> str | None:
    """Return the default launch-host secrets file if one exists."""
    default = os.environ.get("OT_AGENT_SECRETS_ENV") or os.path.expanduser(
        "~/Documents/secrets.env"
    )
    return default if os.path.isfile(default) else None


def load_secrets_env_into_os_environ(secrets_env: str | None) -> int:
    """Read ``secrets_env`` (KEY=VALUE) into ``os.environ`` on the launch host."""
    if not secrets_env:
        return 0
    path = Path(secrets_env).expanduser().resolve()
    if not path.is_file():
        return 0
    loaded = 0
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].lstrip()
        if "=" not in line:
            continue
        k, _, v = line.partition("=")
        k = k.strip()
        v = v.strip()
        if len(v) >= 2 and v[0] == v[-1] and v[0] in ("'", '"'):
            v = v[1:-1]
        if not k:
            continue
        os.environ[k] = v  # file overrides shell
        loaded += 1
    return loaded


def apply_iris_runtime_env(
    *,
    env_vars: dict[str, str],
    args: argparse.Namespace,
    accelerator: ResolvedIrisAccelerator,
    output_mode: str,
    remote_output_dir: str,
    extras: list[str],
) -> None:
    """Apply OT-Agent Iris runtime defaults in-place to ``env_vars``."""
    if accelerator.uses_iris_serve:
        # TPU Iris jobs use the cross-host serve path: iris runs the entrypoint
        # on EVERY VM of the slice, so the worker's LocalHarborRunner.run()
        # brings up ONE cross-host Ray cluster and gates harbor to the driver
        # rank (IRIS_TASK_ID==0). GPU Iris jobs use the normal single-pod
        # Ray/vLLM path and do neither.
        env_vars.setdefault("OT_AGENT_IRIS_SERVE", "1")
        env_vars.setdefault(
            "OT_AGENT_IRIS_RENDEZVOUS_DIR",
            f"{remote_output_dir.rstrip('/')}/_ray_rendezvous",
        )

    # Wire the iris controller's XLA persistent cache to the region-matched GCS
    # bucket (TPU + gcs output only). Disable with OT_AGENT_XLA_CACHE_BASE=disabled.
    if accelerator.is_tpu and output_mode == "gcs" and args.gcs_output_dir:
        cache_root = args.gcs_output_dir.rstrip("/").rsplit("/ot-agent", 1)[0]
        env_vars.setdefault(
            "OT_AGENT_XLA_CACHE_BASE",
            f"{cache_root}/ot-agent/xla_cache",
        )

    # OT-Agent's build_support.py syncs the sft/llamafactory git submodule at
    # every editable install; inside the iris worker there's no git remote for
    # it, so opt out when no sft-* extra is requested.
    if not any(e.startswith("sft-") for e in extras):
        env_vars.setdefault("OT_AGENT_SKIP_SFT_SYNC", "1")

    # Force uv and subprocesses to use /app/.venv and copied wheels at runtime.
    env_vars.setdefault("UV_PROJECT_ENVIRONMENT", "/app/.venv")
    env_vars.setdefault("VIRTUAL_ENV", "/app/.venv")
    env_vars.setdefault("UV_LINK_MODE", "copy")
    env_vars.setdefault("OT_AGENT_INHERIT_SUBPROC_LOGS", "1")

    if accelerator.is_tpu:
        env_vars.setdefault("VLLM_SKIP_FLAG_DISCOVERY", "1")
        env_vars.setdefault("VLLM_SKIP_RAY_PROBE", "1")
        env_vars.setdefault("MODEL_IMPL_TYPE", "vllm")

    # Run:AI Model Streamer config for S3-compatible safetensor reads.
    env_vars.setdefault("RUNAI_STREAMER_S3_USE_VIRTUAL_ADDRESSING", "False")
    env_vars.setdefault("AWS_EC2_METADATA_DISABLED", "true")

    _forward_launcher_env(env_vars)
    # On the GPU path, drop the launch host's object-storage creds so the pod's
    # injected R2 creds win (see _GPU_STORAGE_CRED_KEYS). On TPU keep them —
    # the TPU serve path reads weights from marin/laion object storage.
    exclude = _GPU_STORAGE_CRED_KEYS if accelerator.is_gpu else frozenset()
    _load_worker_secrets_env(
        env_vars, getattr(args, "secrets_env", None), exclude_keys=exclude
    )
    if accelerator.is_gpu:
        # Belt-and-suspenders: strip any storage creds that slipped in (e.g. via
        # a harbor-config env block) so nothing overrides the pod's R2 envFrom.
        stripped = [
            k for k in _GPU_STORAGE_CRED_KEYS if env_vars.pop(k, None) is not None
        ]
        if stripped:
            print(
                f"[iris] GPU path: withheld launch-host storage creds "
                f"({', '.join(sorted(stripped))}) so the pod's injected R2 creds win.",
                flush=True,
            )
    else:
        _alias_s3_credentials(env_vars)


def _forward_launcher_env(env_vars: dict[str, str]) -> None:
    launcher_env_passthrough = (
        "DAYTONA_API_KEY",
        "DAYTONA_JWT_TOKEN",
        "DAYTONA_ORGANIZATION_ID",
        "DAYTONA_API_URL",
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "GOOGLE_API_KEY",
        "GEMINI_API_KEY",
        "TOGETHER_API_KEY",
        "FIREWORKS_API_KEY",
        "SUPABASE_URL",
        "SUPABASE_KEY",
        "SUPABASE_SERVICE_ROLE_KEY",
    )
    for key in launcher_env_passthrough:
        value = os.environ.get(key)
        if value:
            env_vars.setdefault(key, value)


def _load_worker_secrets_env(
    env_vars: dict[str, str],
    secrets_env: str | None,
    *,
    exclude_keys: frozenset[str] = frozenset(),
) -> None:
    if not secrets_env:
        return
    secrets_path = Path(secrets_env).expanduser().resolve()
    if not secrets_path.exists():
        raise FileNotFoundError(f"--secrets-env file not found: {secrets_path}")
    loaded: list[str] = []
    skipped: list[str] = []
    for raw_line in secrets_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].lstrip()
        if "=" not in line:
            continue  # malformed; skip
        k, _, v = line.partition("=")
        k = k.strip()
        v = v.strip()
        if len(v) >= 2 and v[0] == v[-1] and v[0] in ("'", '"'):
            v = v[1:-1]
        if not k:
            continue
        if k in exclude_keys:
            skipped.append(k)
            continue
        env_vars[k] = v  # file values override passthrough
        loaded.append(k)
    print(
        f"[iris] Secrets:    loaded {len(loaded)} entries from "
        f"{secrets_path}: {', '.join(sorted(loaded))}",
        flush=True,
    )
    if skipped:
        print(
            f"[iris] Secrets:    withheld {len(skipped)} storage creds "
            f"(GPU pod uses cluster-injected R2): {', '.join(sorted(skipped))}",
            flush=True,
        )


def _alias_s3_credentials(env_vars: dict[str, str]) -> None:
    endpoint_in_yaml = env_vars.get("AWS_ENDPOINT_URL")
    is_marin_endpoint = (
        endpoint_in_yaml is not None and "storage.googleapis.com" in endpoint_in_yaml
    )
    has_marin = "MARIN_HMAC_ACCESS_ID" in env_vars and "MARIN_HMAC_SECRET" in env_vars
    has_laion = "LAION_ENDPOINT" in env_vars
    aliased: list[str] = []

    if has_marin and (is_marin_endpoint or not has_laion):
        env_vars.setdefault("AWS_ENDPOINT_URL", "https://storage.googleapis.com")
        env_vars["AWS_ACCESS_KEY_ID"] = env_vars["MARIN_HMAC_ACCESS_ID"]
        env_vars["AWS_SECRET_ACCESS_KEY"] = env_vars["MARIN_HMAC_SECRET"]
        aliased = [
            "AWS_ENDPOINT_URL ← https://storage.googleapis.com",
            "AWS_ACCESS_KEY_ID ← MARIN_HMAC_ACCESS_ID",
            "AWS_SECRET_ACCESS_KEY ← MARIN_HMAC_SECRET",
        ]
    elif has_laion:
        if "AWS_ENDPOINT_URL" not in env_vars:
            env_vars["AWS_ENDPOINT_URL"] = env_vars["LAION_ENDPOINT"]
            aliased.append("AWS_ENDPOINT_URL ← LAION_ENDPOINT")
        if "LAION_ACCESS_KEY" in env_vars:
            env_vars["AWS_ACCESS_KEY_ID"] = env_vars["LAION_ACCESS_KEY"]
            aliased.append("AWS_ACCESS_KEY_ID ← LAION_ACCESS_KEY")
        if "LAION_SECRET_KEY" in env_vars:
            env_vars["AWS_SECRET_ACCESS_KEY"] = env_vars["LAION_SECRET_KEY"]
            aliased.append("AWS_SECRET_ACCESS_KEY ← LAION_SECRET_KEY")

    if aliased:
        print(
            f"[iris] Aliased for runai_streamer S3 against "
            f"{env_vars.get('AWS_ENDPOINT_URL', '<unset>')}: "
            f"{', '.join(aliased)}",
            flush=True,
        )
