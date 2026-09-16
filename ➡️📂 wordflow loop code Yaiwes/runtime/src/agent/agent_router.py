"""
Agent Router Module - PECP-MAXBRY-100x (Nodo T-012)
Ruteo determinista de agentes según la categoría y especificación de la tarea.
"""

from typing import Dict, Any, List, Optional
import json


class AgentRouter:
    """Selecciona el agente adecuado según reglas deterministas y capacidades requeridas."""

    DEFAULT_REGISTRY: List[Dict[str, Any]] = [
        {"id": "opencode", "capabilities": ["coding", "refactoring", "python", "js"], "priority": 1},
        {"id": "claude_code", "capabilities": ["architecture", "refactoring", "complex_reasoning"], "priority": 1},
        {"id": "openhands", "capabilities": ["tool_use", "terminal", "web_search"], "priority": 2},
        {"id": "aider", "capabilities": ["git_patch", "multi_file_editing"], "priority": 2}
    ]

    def __init__(self, registry: Optional[List[Dict[str, Any]]] = None) -> None:
        self.registry: List[Dict[str, Any]] = registry or self.DEFAULT_REGISTRY

    def select_agent(self, task_type: str, required_skills: List[str]) -> Dict[str, Any]:
        """
        Selecciona el mejor agente determinísticamente comparando coincidencias de habilidades.
        """
        best_agent: Optional[Dict[str, Any]] = None
        max_matches: int = -1

        for agent in self.registry:
            matches = len(set(required_skills).intersection(set(agent["capabilities"])))
            if matches > max_matches:
                max_matches = matches
                best_agent = agent
            elif matches == max_matches and best_agent is not None:
                if agent["priority"] < best_agent["priority"]:
                    best_agent = agent

        selected = best_agent or self.registry[0]
        return {
            "selected_agent_id": selected["id"],
            "matched_skills": max_matches,
            "status": "ROUTED"
        }


if __name__ == "__main__":
    print("=== TEST NODO T-012: AGENT ROUTER ===")
    router = AgentRouter()
    route_res = router.select_agent("coding", ["python", "refactoring"])
    print(json.dumps(route_res, indent=2))
