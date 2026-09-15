from __future__ import annotations

from dataclasses import asdict

from core.agent_base import Agent, AgentContext, AgentResult
from core.state import ResearchState
from schemas.method_card import MethodCard


class MethodCardExtractorAgent(Agent):
    name = "method_card_extractor"

    def run(self, state: ResearchState, context: AgentContext) -> AgentResult:
        evidence_by_paper: dict[str, list[str]] = {}
        for evidence in state.values.get("checked_evidence", []):
            if evidence.get("is_usable"):
                evidence_by_paper.setdefault(evidence["paper_id"], []).append(evidence["evidence_id"])
        parsed_by_paper = {item["paper_id"]: item for item in state.values.get("parsed_papers", [])}

        modalities = self._input_modalities(state)
        cards: list[MethodCard] = []
        for paper in state.values.get("selected_papers", []):
            parsed_text = parsed_by_paper.get(paper["paper_id"], {}).get("text_excerpt", "")
            cards.append(
                MethodCard(
                    paper_id=paper["paper_id"],
                    task=state.topic.domain.get("primary_area", state.topic.topic_name),
                    problem_setting=state.topic.research_goal.get("short", ""),
                    input_modalities=modalities,
                    output=self._output_hint(state),
                    model_architecture=self._architecture_hints(parsed_text),
                    fusion_strategy=self._fusion_hints(parsed_text),
                    datasets=state.topic.current_status.get("datasets", []),
                    metrics=state.topic.experiment_metrics,
                    reusable_ideas_for_current_topic=[
                        f"Investigate relevance of {paper.get('title')} to current topic"
                    ],
                    risk=self._risk(parsed_text),
                    evidence_ids=evidence_by_paper.get(paper["paper_id"], []),
                )
            )

        artifact_ids: list[str] = []
        for card in cards:
            context.artifact_store.save_json(
                state.run_id, "method_cards", card.method_card_id, card
            )
            artifact_ids.append(card.method_card_id)

        state.values["method_cards"] = [asdict(card) for card in cards]
        return AgentResult(
            notes=[f"extracted {len(cards)} method cards"],
            artifacts={"method_cards": artifact_ids},
            values={"method_card_count": len(cards)},
        )

    def _input_modalities(self, state: ResearchState) -> list[str]:
        modalities = state.topic.paper_schema.get("default_input_modalities")
        if isinstance(modalities, list):
            return [str(item) for item in modalities]
        secondary = state.topic.domain.get("secondary_areas", [])
        return [str(item) for item in secondary[:4]]

    def _output_hint(self, state: ResearchState) -> str:
        return str(state.topic.paper_schema.get("default_output", "research artifact"))

    def _architecture_hints(self, text: str) -> dict[str, str]:
        lower = text.lower()
        return {
            "encoder": "transformer/social encoder" if "transformer" in lower else "to be extracted from full paper",
            "decoder": "diffusion denoiser" if "diffusion" in lower else "to be extracted from full paper",
            "fusion_module": "language/intention conditioning" if ("language" in lower or "intention" in lower) else "to be extracted from full paper",
        }

    def _fusion_hints(self, text: str) -> dict[str, str]:
        lower = text.lower()
        if "cross-attention" in lower or "cross attention" in lower:
            return {"type": "cross-attention", "description": "detected from local PDF text"}
        if "language" in lower or "intention" in lower:
            return {"type": "conditioned", "description": "detected language/intention conditioning terms in local PDF text"}
        return {"type": "unknown", "description": "requires full-text parsing or human notes"}

    def _risk(self, text: str) -> list[str]:
        if text:
            return ["auto-extracted hints require human verification against full paper"]
        return ["offline seed card; verify against full paper before strong claims"]
