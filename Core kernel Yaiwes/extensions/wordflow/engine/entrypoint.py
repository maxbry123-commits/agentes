# -*- coding: utf-8 -*-
"""Wordflow entrypoint — A-WF-07. 0% LLM."""
from __future__ import annotations

from typing import Any

from .main_loop import run_main_12


def run_wordflow(
    raw: dict[str, Any] | None,
    **kwargs: Any,
) -> dict[str, Any]:
    state = run_main_12(raw, **kwargs)
    return {
        "ok": state.get("status") == "COMPLETED",
        "status": state.get("status"),
        "stop_reason": state.get("stop_reason"),
        "block_id": (state.get("block") or {}).get("block_id"),
        "block_hash": (state.get("block") or {}).get("block_hash"),
        "tasks": state.get("tasks") or [],
        "council": (state.get("council") or {}).get("decision"),
        "sentinel": (state.get("sentinel") or {}).get("verdict"),
        "goals_out_done": [
            k
            for k, v in (state.get("goals_out") or {}).items()
            if v.get("status") == "DONE"
        ],
        "checkpoint": state.get("checkpoint"),
        "step_results": state.get("step_results"),
        "raw_state": state,
    }
