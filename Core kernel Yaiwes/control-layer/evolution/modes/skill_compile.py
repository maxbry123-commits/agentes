"""EVO.04 · skill → DSL/DAG/Sheriff."""
from __future__ import annotations
from typing import Any
from ..pipeline import EvolutionMode, EvolutionRequest
from ..source_reuse import SourceReuseDecision

class ModeSkillCompile:
    mode = EvolutionMode.SKILL_COMPILE

    def run(self, req: EvolutionRequest, reuse: SourceReuseDecision) -> dict[str, Any]:
        skill_text = str(req.payload.get("skill_text") or req.payload.get("skill_path") or "")
        steps = list(req.payload.get("steps") or [])
        dag_nodes = []
        for i, step in enumerate(steps):
            if isinstance(step, str):
                node_id, title, llm = f"s{i}", step, False
            else:
                node_id = str(step.get("id") or f"s{i}")
                title = str(step.get("title") or step.get("name") or node_id)
                llm = bool(step.get("llm", False))
            dag_nodes.append({
                "id": node_id,
                "title": title,
                "deterministic": not llm,
                "sheriff": ["budget", "idempotency", "no_secrets_in_prompt"],
            })
        return {
            "candidate_id": f"skill_{req.capability_id}",
            "package_path": f"extensions/skills/{req.capability_id}",
            "evidence": {
                "mode": self.mode.value,
                "skill_ref": skill_text[:200],
                "dag_nodes": dag_nodes,
                "ratio_target": "90D_10LLM",
                "reuse": reuse.to_dict(),
            },
        }
