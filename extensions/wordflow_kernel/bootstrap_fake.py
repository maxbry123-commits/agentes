"""T13 — Fake E2E: bootstrap → GoalLock → code_path dry → deploy no-op.

No vendor LLM. No publish real.
"""
from __future__ import annotations

from typing import Any, Optional

from .bootstrap_multi import bootstrap
from .instance_store import PersistentRegistry


def _goal_lock_fake(text: str) -> dict[str, Any]:
    try:
        from wordflow.engine.goal_lock import lock_goals

        out = lock_goals({"text": text, "raw": text})
        if isinstance(out, dict) and out.get("ok"):
            return {"ok": True, "mode": "wired", "lock": out.get("lock")}
    except Exception as exc:
        return {"ok": True, "mode": "fake", "lock": {"goal": text}, "note": str(exc)}
    return {"ok": True, "mode": "fake", "lock": {"goal": text}}


def _code_path_dry(text: str, instance_id: str) -> dict[str, Any]:
    """Dry/fake: do not require full C-19 context/handoff PASS."""
    return {
        "ok": True,
        "mode": "dry",
        "stage": "code_path_dry",
        "instance_id": instance_id,
        "input": text[:80],
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

    ok = bool(locked.get("ok") and path_out.get("ok") and deploy_out.get("ok"))
    return {
        "ok": ok,
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
        assert out["instance_id"] == "v1"
        assert out["stages"] == ["bootstrap", "goal_lock", "code_path_dry", "deploy_fake"]
        assert out["deploy"]["published"] is False
        print("PASS", " ".join(out["stages"]))
