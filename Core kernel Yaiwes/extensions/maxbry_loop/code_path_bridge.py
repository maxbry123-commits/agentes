"""Loop → run_code_path. Invokes C-19. Does not claim PASS.

context_verified defaults False → expected BLOCK. llm_control=DENY.
"""
from __future__ import annotations

from typing import Any


def dispatch_run_code_path(
    text: str,
    *,
    mission_id: str = "",
    context_verified: bool = False,
    handoff_verified: bool = False,
) -> dict[str, Any]:
    try:
        from wordflow.engine.code_path_runner import run_code_path
    except ImportError:
        try:
            from extensions.wordflow.engine.code_path_runner import run_code_path
        except ImportError:
            return {
                "ok": False,
                "invoked": False,
                "c19_ok": False,
                "verdict": "NOT_INVOKED",
                "error": "CODE_PATH_RUNNER_MISSING",
                "llm_control": "DENY",
            }
    try:
        out = run_code_path(
            text or "loop dispatch code_path",
            mission_id=mission_id,
            context_verified=context_verified,
            handoff_verified=handoff_verified,
            auto_measure_core=False,
            auto_measure_fc=False,
            run_quality_dag=False,
        )
        return {
            "ok": True,
            "invoked": True,
            "c19_ok": bool(out.get("ok")),
            "verdict": str(out.get("verdict") or "FAIL"),
            "llm_control": out.get("llm_control", "DENY"),
            "stage": out.get("stage"),
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "invoked": True,
            "c19_ok": False,
            "verdict": "ERROR",
            "error": str(exc),
            "llm_control": "DENY",
        }


if __name__ == "__main__":
    out = dispatch_run_code_path("objective: loop wire\nsuccess: invoke runner")
    assert out["invoked"] is True
    assert out.get("c19_ok") is False
    print("ok", out.get("verdict"))
