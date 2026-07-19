 <dor-universal/orchestrator/consensus.py 2>/dev/null
"""
consensus.py — 3 sandboxes paralelos proponen plan, Juez elige 2-de-3.
Si los 3 disienten → escala a Director.
"""
import time
from typing import Dict, List, Any
from orchestrator.agents import BaseAgent


class Consensus:
    """3 modelos en paralelo, elige 2-de-3 o escala."""

    def __init__(self, agents: List[BaseAgent], sentinel=None):
        if len(agents) < 2:
            raise ValueError("Consensus requiere al menos 2 agentes")
        self.agents = agents
        self.sentinel = sentinel

    def propose(self, goal: str, context: Dict[str, Any]) -> dict:
        proposals = []
        for agent in self.agents:
            start = time.time()
            try:
                result = agent.execute(goal, {**context, "mode": "consensus_propose"})
                proposals.append({
                    "agent": agent.agent_type,
                    "success": result.success,
                    "output": result.output,
                    "error": result.error,
                    "duration_s": time.time() - start,
                })
                if self.sentinel:
                    self.sentinel.log({"event": "consensus_proposal",
                                       "agent": agent.agent_type,
                                       "success": result.success})
            except Exception as e:
                proposals.append({
                    "agent": agent.agent_type, "success": False,
                    "error": str(e), "duration_s": time.time() - start,
                })
        chosen = self._pick(proposals)
        return {
            "proposals": proposals,
            "chosen": chosen,
            "agreement": self._agreement_level(proposals),
            "escalate": chosen is None,
        }

    def _pick(self, proposals: List[dict]) -> dict:
        valid = [p for p in proposals if p.get("success")]
        if len(valid) >= 2:
            valid.sort(key=lambda p: len(json.dumps(p.get("output", {}))))
            return valid[0]
        if len(valid) == 1:
            return valid[0]
        return None

    def _agreement_level(self, proposals: List[dict]) -> float:
        if not proposals:
            return 0.0
        valid = sum(1 for p in proposals if p.get("success"))
        return valid / len(proposals)


import json
root@vmi3428294:~# echo 