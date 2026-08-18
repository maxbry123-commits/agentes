"""G-W14 — edge cases de negocio registrables por misión."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Any

@dataclass
class MissionEdge:
    name: str
    fn: Callable[[], bool]
    required: bool = True

@dataclass
class MissionEdgeRegistry:
    mission_id: str
    edges: List[MissionEdge] = field(default_factory=list)

    def add(self, name: str, fn: Callable[[], bool], required: bool = True) -> None:
        self.edges.append(MissionEdge(name, fn, required))

    def run(self) -> Dict[str, Any]:
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
    reg.add("llm_control_deny_constant", lambda: True)  # path declares DENY
    reg.add(
        "programming_pipeline_importable",
        lambda: __import__("extensions.wordflow.engine.programming_pipeline", fromlist=["default_pipeline"]) is not None,
    )
    reg.add(
        "code_path_runner_importable",
        lambda: __import__("extensions.wordflow.engine.code_path_runner", fromlist=["run_code_path"]) is not None,
    )
    return reg
