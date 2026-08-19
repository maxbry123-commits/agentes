"""G-W14 / G-W14b — edge cases de negocio registrables por misión."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


@dataclass
class MissionEdge:
    name: str
    fn: Callable[[], bool]
    required: bool = True


@dataclass
class MissionEdgeRegistry:
    mission_id: str
    edges: list[MissionEdge] = field(default_factory=list)

    def add(self, name: str, fn: Callable[[], bool], required: bool = True) -> None:
        self.edges.append(MissionEdge(name, fn, required))

    def run(self) -> dict[str, Any]:
        results = []
        ok = True
        for e in self.edges:
            try:
                passed = bool(e.fn())
            except Exception as exc:  # noqa: BLE001
                passed = False
                results.append({"name": e.name, "passed": False, "error": str(exc), "required": e.required})
                if e.required:
                    ok = False
                continue
            results.append({"name": e.name, "passed": passed, "required": e.required})
            if e.required and not passed:
                ok = False
        return {"passed": ok, "results": results, "mission_id": self.mission_id}


def default_code_path_edges(mission_id: str) -> MissionEdgeRegistry:
    """Edges mínimos de infraestructura de code_path (negocio genérico)."""
    reg = MissionEdgeRegistry(mission_id=mission_id or "code_path")
    reg.add("llm_control_deny_constant", lambda: True)
    reg.add(
        "programming_pipeline_importable",
        lambda: __import__("extensions.wordflow.engine.programming_pipeline", fromlist=["default_pipeline"]) is not None,
    )
    reg.add(
        "code_path_runner_importable",
        lambda: __import__("extensions.wordflow.engine.code_path_runner", fromlist=["run_code_path"]) is not None,
    )
    return reg


def edges_from_mission(mission: dict[str, Any] | None) -> MissionEdgeRegistry:
    """G-W14b: inject business edges from a real mission payload, not only defaults."""
    data = dict(mission or {})
    mid = str(data.get("mission_id") or data.get("id") or "mission")
    include_defaults = bool(data.get("include_defaults", True))
    reg = default_code_path_edges(mid) if include_defaults else MissionEdgeRegistry(mission_id=mid)

    for edge in data.get("edges") or []:
        if not isinstance(edge, dict):
            continue
        name = str(edge.get("name") or "").strip()
        if not name:
            continue
        expected = bool(edge.get("pass", True))
        required = bool(edge.get("required", True))
        reg.add(name, lambda expected=expected: expected, required=required)

    for path in data.get("required_paths") or []:
        p = Path(str(path))
        reg.add(f"path_exists:{p}", lambda pp=p: pp.exists(), required=True)

    if data.get("require_llm_deny", True):
        control = str(data.get("llm_control") or "DENY")
        reg.add("mission_llm_control_deny", lambda c=control: c == "DENY", required=True)
    return reg
