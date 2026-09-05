"""T15 — run_preflight(instance_id) offline checks.

Does not skip fail_closed. No network.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from .fail_closed import FailClosedError, assert_ficha_or_fail
from .ficha_loader import load_ficha, validate_ficha


def _pkg_dir() -> Path:
    return Path(__file__).resolve().parent


def _check_ficha() -> dict[str, Any]:
    path = _pkg_dir() / "ficha.v2.json"
    if not path.is_file():
        return {"name": "ficha", "ok": False, "detail": "ficha.v2.json missing"}
    data = load_ficha(path)
    errors = validate_ficha(data)
    return {
        "name": "ficha",
        "ok": not errors,
        "detail": errors or data.get("artifact_id") or data.get("id"),
        "ficha": data,
    }


def _check_fail_closed(ficha: dict[str, Any] | None) -> dict[str, Any]:
    if ficha is None:
        return {"name": "fail_closed", "ok": False, "detail": "no ficha"}
    try:
        assert_ficha_or_fail(ficha)
        return {"name": "fail_closed", "ok": True, "detail": "pass"}
    except FailClosedError as exc:
        return {"name": "fail_closed", "ok": False, "detail": str(exc)}


def _check_repo_truth() -> dict[str, Any]:
    path = _pkg_dir() / "repo_truth.py"
    if path.is_file():
        return {"name": "repo_truth", "ok": True, "detail": "repo_truth.py present"}
    try:
        from . import repo_truth  # noqa: F401

        return {"name": "repo_truth", "ok": True, "detail": "import ok"}
    except Exception as exc:
        return {"name": "repo_truth", "ok": False, "detail": str(exc)}


def _check_env_min() -> dict[str, Any]:
    ok = sys.version_info >= (3, 10)
    return {
        "name": "env_min",
        "ok": ok,
        "detail": f"python {sys.version_info.major}.{sys.version_info.minor}",
    }


def run_preflight(instance_id: str = "v1") -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    blockers: list[str] = []

    ficha_c = _check_ficha()
    checks.append({k: v for k, v in ficha_c.items() if k != "ficha"})
    if not ficha_c["ok"]:
        blockers.append("ficha")

    fc = _check_fail_closed(ficha_c.get("ficha") if ficha_c["ok"] else None)
    checks.append(fc)
    if not fc["ok"]:
        blockers.append("fail_closed")

    rt = _check_repo_truth()
    checks.append(rt)
    if not rt["ok"]:
        blockers.append("repo_truth")

    env = _check_env_min()
    checks.append(env)
    if not env["ok"]:
        blockers.append("env_min")

    return {
        "ok": len(blockers) == 0,
        "checks": checks,
        "blockers": blockers,
        "instance_id": instance_id,
    }


if __name__ == "__main__":
    out = run_preflight("v1")
    print("ok" if out["ok"] else "BLOCK", out["blockers"], [c["name"] for c in out["checks"]])
    if not out["ok"]:
        raise SystemExit("preflight blockers: " + ",".join(out["blockers"]))
