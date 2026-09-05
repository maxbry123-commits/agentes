# -*- coding: utf-8 -*-
"""EnvironmentCapabilityMap — T39. Deterministic env scan. 0% LLM.

Uses only stdlib; no network probes. Snapshot is declarative + optional hooks.
"""
from __future__ import annotations

import os
import platform
import shutil
from typing import Any, Callable


def scan_environment(
    *,
    extra_providers: list[Callable[[], dict[str, Any]]] | None = None,
    declared_services: dict[str, Any] | None = None,
) -> dict[str, Any]:
    compute = {
        "os": platform.system(),
        "arch": platform.machine(),
        "python": platform.python_version(),
        "cpu_count": os.cpu_count(),
    }
    tools = {
        "git": bool(shutil.which("git")),
        "docker": bool(shutil.which("docker")),
        "python": bool(shutil.which("python") or shutil.which("python3")),
    }
    env_flags = {
        "CI": bool(os.environ.get("CI")),
        "GITHUB_ACTIONS": bool(os.environ.get("GITHUB_ACTIONS")),
        "has_github_token_env": bool(
            os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        ),
        # never expose token value
    }
    services = dict(declared_services or {})
    providers_out: list[dict[str, Any]] = []
    for p in extra_providers or []:
        try:
            providers_out.append(p())
        except Exception as exc:  # noqa: BLE001
            providers_out.append({"ok": False, "error": str(exc)})

    return {
        "ok": True,
        "devices": {"platform": compute["os"], "arch": compute["arch"]},
        "compute": compute,
        "tools": tools,
        "env_flags": env_flags,
        "services": services,
        "providers": providers_out,
        "capabilities": _derive_caps(tools, env_flags, services),
    }


def _derive_caps(
    tools: dict[str, bool],
    env_flags: dict[str, bool],
    services: dict[str, Any],
) -> list[str]:
    caps: list[str] = ["local_runtime"]
    if tools.get("git"):
        caps.append("git_cli")
    if tools.get("docker"):
        caps.append("docker")
    if env_flags.get("has_github_token_env"):
        caps.append("github_token_present")
    if services.get("huggingface"):
        caps.append("hf_service")
    if services.get("ssh"):
        caps.append("ssh_remote")
    return caps
