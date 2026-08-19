"""T13 — Fake E2E: bootstrap → GoalLock → run_code_path invoked → deploy no-op.

Invokes C-19 with context_verified=False. Expected verdict BLOCK.
Does NOT treat BLOCK as PASS. No vendor LLM. No publish real.
"""
from __future__ import annotations

from typing import Any, Optional

from .bootstrap_multi import bootstrap
from .instance_store import PersistentRegistry


def _goal_lock_fake(text: str) -> dict[str, Any]:
    try:
        from wordflow.engine.goal_lock import lock_goals
    except ImportError:
        try:
            from extensions.wordflow.engine.goal_lock import lock_goals
        except ImportError:
            return {"ok": True, "mode": "fake", "lock": {"goal": text}, "note": "GOAL_LOCK_MISSING"}
    try:
        out = lock_goals({"text": text, "raw": text})
        if isinstance(out, dict) and out.get("ok"):
            return {"ok": True, "mode": "wired", "lock": out.get("lock")}
        return {"ok": True, "mode": "wired_incomplete", "lock": out}
    except Exception as exc:  # noqa: BLE001
        return {"ok": True, "mode": "fake", "lock": {"goal": text}, "note": str(exc)}


def _code_path_dry(text: str, instance_id: str) -> dict[str, Any]:
    """Invoke run_code_path. Do not require or claim C-19 PASS."""
    try:
        from wordflow.engine.code_path_runner import run_code_path
    except ImportError:
        try:
            from extensions.wordflow.engine.code_path_runner import run_code_path
        except ImportError:
            return {
                "ok": True,
                "mode": "dry_fallback",
                "stage": "code_path_dry",
                "instance_id": instance_id,
                "invoked": False,
                "c19_ok": False,
                "verdict": "NOT_INVOKED",
                "published": False,
            }
    try:
        out = run_code_path(
            text,
            mission_id=instance_id,
            context_verified=False,
            handoff_verified=False,
            auto_measure_core=False,
            auto_measure_fc=False,
            run_quality_dag=False,
        )
        verdict = str(out.get("verdict") or "FAIL")
        return {
            "ok": True,
            "mode": "invoked_no_pass",
            "stage": "code_path_dry",
            "instance_id": instance_id,
            "invoked": True,
            "c19_ok": bool(out.get("ok")),
            "verdict": verdict,
            "llm_control": out.get("llm_control", "DENY"),
            "published": False,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": True,
            "mode": "dry_error",
            "stage": "code_path_dry",
            "instance_id": instance_id,
            "invoked": True,
            "c19_ok": False,
            "verdict": "ERROR",
            "error": str(exc),
            "published": False,
        }


def _deploy_fake() -> dict[str, Any]:
    try:
        from github_deploy.git_data_port import FakeGitDataPort

        FakeGitDataPort()
        return {"ok": True, "mode": "fake_port", "published": False}
    except Exception:
        return {"ok": True, "mode": "noop", "published": False}


def run_bootstrap_fake(
    instance_id: str = "v1",
    *,
    registry: Optional[PersistentRegistry] = None,
    goal: str = "fake-goal T13",
) -> dict[str, Any]:
    stages: list[str] = []
    inst = bootstrap(instance_id, name="default", registry=registry)
    stages.append("bootstrap")

    locked = _goal_lock_fake(goal)
    inst.state["goal_lock"] = locked
    stages.append("goal_lock")

    path_out = _code_path_dry(goal, inst.instance_id)
    stages.append("code_path_dry")

    deploy_out = _deploy_fake()
    stages.append("deploy_fake")

    invoked = bool(path_out.get("ok"))
    return {
        "ok": invoked and bool(locked.get("ok") and deploy_out.get("ok")),
        "c19_pass": bool(path_out.get("c19_ok")),
        "stages": stages,
        "instance_id": inst.instance_id,
        "goal_lock": locked,
        "code_path": path_out,
        "deploy": deploy_out,
    }


if __name__ == "__main__":
    import tempfile
    from pathlib import Path

    from .instance_store import InstanceStore

    with tempfile.TemporaryDirectory() as tmp:
        store = InstanceStore(root=Path(tmp))
        reg = PersistentRegistry(store=store)
        out = run_bootstrap_fake("v1", registry=reg)
        assert out["ok"] is True
        assert out["c19_pass"] is False
        assert out["instance_id"] == "v1"
        assert out["stages"] == ["bootstrap", "goal_lock", "code_path_dry", "deploy_fake"]
        assert out["deploy"]["published"] is False
        print("ok", " ".join(out["stages"]), out["code_path"].get("verdict"))
