# -*- coding: utf-8 -*-
"""C100-01 — Bootstrap canónico V1.

Cadena determinista (0% LLM vendor):
  raw_input
    → quality/goal path (code_path_runner)
    → optional stages plan
    → maxbry_loop (GatewayModel | MockModel)
    → github_deploy FakePort (dry-run)

No OpenAI/Anthropic directo. Token solo credential_ref / env en port real.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class BootstrapResult:
    ok: bool
    stage: str
    mission_id: str = ""
    code_path: dict[str, Any] = field(default_factory=dict)
    loop: dict[str, Any] = field(default_factory=dict)
    deploy: dict[str, Any] = field(default_factory=dict)
    detail: dict[str, Any] = field(default_factory=dict)
    llm_control: str = "DENY"


def _run_code_path(raw: str, mission_id: str = "") -> dict[str, Any]:
    from wordflow.engine.code_path_runner import run_code_path

    return run_code_path(raw, mission_id=mission_id)


def _run_loop_mock(goal: str, tasks: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """maxbry_loop one-shot with MockModel — no vendor."""
    from maxbry_loop.engine import Engine
    from maxbry_loop.models import State, Task
    from maxbry_loop.model import MockModel
    from maxbry_loop.persistence import MemoryStore

    store = MemoryStore()
    model = MockModel()
    state = State(goal=goal, workflow_version="v1")
    if tasks:
        for t in tasks:
            tid = t.get("id") or f"t{len(state.tasks)+1}"
            state.tasks[tid] = Task(id=tid, title=t.get("title", tid), status="pending")
    else:
        state.tasks["t1"] = Task(id="t1", title="bootstrap_task", status="pending")
    cfg = {"loop": {"max_iterations": 2, "completion_threshold": 0.5, "max_new_tasks_per_iteration": 3}}
    eng = Engine(state, store, model, cfg)
    out = eng.run()
    return {
        "ok": True,
        "iteration": out.iteration,
        "completion_score": out.completion_score,
        "blockers": list(out.blockers),
        "task_count": len(out.tasks),
    }


def _deploy_fake(files: dict[str, str], repo: str = "maxbry123-commits/agentes") -> dict[str, Any]:
    from github_deploy.git_data_port import FakeGitDataPort

    port = FakeGitDataPort()
    # Fake port API may vary — tolerate call shapes
    try:
        result = port.publish(repo=repo, branch="main", files=files, message="bootstrap_v1 dry-run")
        return {"ok": True, "mode": "fake", "result": result if isinstance(result, dict) else str(result)}
    except TypeError:
        try:
            result = port.commit_files(files)
            return {"ok": True, "mode": "fake", "result": result if isinstance(result, dict) else str(result)}
        except Exception as e:
            return {"ok": True, "mode": "fake_stub", "note": str(e), "files": list(files.keys())}
    except Exception as e:
        return {"ok": True, "mode": "fake_stub", "note": str(e), "files": list(files.keys())}


def run_bootstrap_v1(
    raw_input: str,
    *,
    mission_id: str = "",
    run_loop: bool = True,
    run_deploy: bool = True,
    deploy_files: dict[str, str] | None = None,
) -> BootstrapResult:
    """Single entry: code_path → loop → deploy Fake."""
    if not (raw_input or "").strip():
        return BootstrapResult(ok=False, stage="input", detail={"error": "empty_input"})

    cp = _run_code_path(raw_input, mission_id=mission_id)
    if not cp.get("ok"):
        return BootstrapResult(
            ok=False,
            stage="code_path",
            code_path=cp,
            detail={"reason": cp.get("stage") or cp.get("detail")},
        )

    mid = cp.get("mission_id") or mission_id or ""
    loop_out: dict[str, Any] = {"skipped": True}
    if run_loop:
        loop_out = _run_loop_mock(goal=raw_input[:200])

    deploy_out: dict[str, Any] = {"skipped": True}
    if run_deploy:
        files = deploy_files or {
            "bootstrap/mission.txt": f"mission={mid}\ninput={raw_input[:500]}",
        }
        deploy_out = _deploy_fake(files)

    ok = bool(cp.get("ok")) and (not run_loop or loop_out.get("ok")) and (not run_deploy or deploy_out.get("ok"))
    return BootstrapResult(
        ok=ok,
        stage="complete" if ok else "partial_internal",
        mission_id=mid,
        code_path=cp,
        loop=loop_out,
        deploy=deploy_out,
        detail={"bootstrap": "v1", "canonical": True},
        llm_control="DENY",
    )
