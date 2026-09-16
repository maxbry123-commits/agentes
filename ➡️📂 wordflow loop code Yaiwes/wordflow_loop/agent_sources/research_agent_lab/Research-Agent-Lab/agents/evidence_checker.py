from __future__ import annotations

from core.agent_base import Agent, AgentContext, AgentResult
from core.state import ResearchState


class EvidenceCheckerAgent(Agent):
    name = "evidence_checker"

    def run(self, state: ResearchState, context: AgentContext) -> AgentResult:
        checked = []
        for evidence in state.values.get("evidence", []):
            quote = evidence.get("quote", "")
            support_level = evidence.get("support_level", "unsupported")
            checked.append(
                {
                    **evidence,
                    "is_usable": bool(quote) and support_level in {"strong", "weak", "inferred"},
                    "checker_note": "offline evidence needs human confirmation"
                    if support_level == "inferred"
                    else "evidence has source text",
                }
            )

        context.artifact_store.save_json(state.run_id, "evidence_checks", "evidence_checks", checked)
        state.values["checked_evidence"] = checked
        unsupported = sum(1 for item in checked if not item["is_usable"])
        return AgentResult(
            notes=[f"checked evidence records; unsupported={unsupported}"],
            artifacts={"evidence_checks": ["evidence_checks"]},
            values={"unsupported_evidence_count": unsupported},
        )
