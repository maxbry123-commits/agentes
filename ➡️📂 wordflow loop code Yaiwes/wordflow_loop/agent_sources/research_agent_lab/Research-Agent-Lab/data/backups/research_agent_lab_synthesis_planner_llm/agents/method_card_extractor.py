from __future__ import annotations

from dataclasses import asdict
from typing import Any

from core.agent_base import Agent, AgentContext, AgentResult
from core.state import ResearchState
from schemas.base import new_id
from schemas.method_card import MethodCard
from tools.llm_client import OpenAICompatibleClient, extract_json_object
from tools.model_router import ModelRoute, ModelRouter


class MethodCardExtractorAgent(Agent):
    name = "method_card_extractor"

    def __init__(self, llm_client: OpenAICompatibleClient | None = None):
        self.llm_client = llm_client or OpenAICompatibleClient()

    def run(self, state: ResearchState, context: AgentContext) -> AgentResult:
        evidence_by_paper: dict[str, list[str]] = {}
        for evidence in state.values.get("checked_evidence", []):
            if evidence.get("is_usable"):
                evidence_by_paper.setdefault(evidence["paper_id"], []).append(evidence["evidence_id"])
        parsed_by_paper = {item["paper_id"]: item for item in state.values.get("parsed_papers", [])}

        modalities = self._input_modalities(state)
        use_llm = bool(context.settings.get("enable_llm"))
        route = ModelRouter(state.topic).route_for(self.name)
        cards: list[MethodCard] = []
        llm_call_ids: list[str] = []
        llm_success_count = 0
        for paper in state.values.get("selected_papers", []):
            parsed_text = parsed_by_paper.get(paper["paper_id"], {}).get("text_excerpt", "")
            evidence_ids = evidence_by_paper.get(paper["paper_id"], [])
            card = self._rule_based_card(
                state=state,
                paper=paper,
                parsed_text=parsed_text,
                modalities=modalities,
                evidence_ids=evidence_ids,
            )
            if use_llm:
                llm_card, call_record = self._try_llm_card(
                    state=state,
                    paper=paper,
                    parsed_text=parsed_text,
                    base_card=card,
                    evidence_ids=evidence_ids,
                    route=route,
                    settings=context.settings,
                )
                call_id = new_id("llm_call")
                context.artifact_store.save_json(state.run_id, "llm_calls", call_id, call_record)
                llm_call_ids.append(call_id)
                if llm_card is not None:
                    card = llm_card
                    llm_success_count += 1
            cards.append(card)

        artifact_ids: list[str] = []
        for card in cards:
            context.artifact_store.save_json(
                state.run_id, "method_cards", card.method_card_id, card
            )
            artifact_ids.append(card.method_card_id)

        state.values["method_cards"] = [asdict(card) for card in cards]
        notes = [f"extracted {len(cards)} method cards"]
        if use_llm:
            notes.append(
                f"method-card LLM successes: {llm_success_count}; "
                f"records: {len(llm_call_ids)}; api calls used: {int(state.values.get('llm_calls_used', 0))} via {route.model}"
            )
        artifacts = {"method_cards": artifact_ids}
        if llm_call_ids:
            artifacts["llm_calls"] = llm_call_ids
        return AgentResult(
            notes=notes,
            artifacts=artifacts,
            values={
                "method_card_count": len(cards),
                "method_card_llm_call_count": int(state.values.get("llm_calls_used", 0)),
                "method_card_llm_record_count": len(llm_call_ids),
                "method_card_llm_success_count": llm_success_count,
                "llm_calls_used": int(state.values.get("llm_calls_used", 0)),
                "llm_tokens_used": int(state.values.get("llm_tokens_used", 0)),
            },
        )

    def _rule_based_card(
        self,
        state: ResearchState,
        paper: dict[str, Any],
        parsed_text: str,
        modalities: list[str],
        evidence_ids: list[str],
    ) -> MethodCard:
        return MethodCard(
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
            evidence_ids=evidence_ids,
        )

    def _try_llm_card(
        self,
        state: ResearchState,
        paper: dict[str, Any],
        parsed_text: str,
        base_card: MethodCard,
        evidence_ids: list[str],
        route: ModelRoute,
        settings: dict[str, Any],
    ) -> tuple[MethodCard | None, dict[str, Any]]:
        record: dict[str, Any] = {
            "agent": self.name,
            "paper_id": paper["paper_id"],
            "provider": route.provider,
            "model": route.model,
            "api_key_env": route.api_key_env,
            "route_enabled": route.enabled,
            "task_difficulty": route.task_difficulty,
            "status": "pending",
        }
        if route.provider in {"offline", "local", "rule_based"}:
            record["status"] = "skipped_offline_route"
            return None, record
        if not parsed_text.strip():
            record["status"] = "skipped_no_parsed_text"
            return None, record

        allowed, reason = self._llm_budget_allows(state=state, settings=settings)
        if not allowed:
            record["status"] = reason
            record["llm_calls_used"] = state.values.get("llm_calls_used", 0)
            record["llm_tokens_used"] = state.values.get("llm_tokens_used", 0)
            return None, record

        messages = self._build_llm_messages(state, paper, parsed_text)
        record["prompt_chars"] = sum(len(message["content"]) for message in messages)
        response = self.llm_client.chat(route, messages, temperature=0.1, max_tokens=3200)
        record["response_chars"] = len(response.text)
        record["usage"] = response.usage
        record["attempts"] = response.attempts
        self._record_llm_usage(state, response.usage)
        if not response.ok:
            record["status"] = "error"
            record["error"] = response.error[:500]
            return None, record

        payload = extract_json_object(response.text)
        if payload is None:
            record["status"] = "invalid_json"
            record["response_preview"] = response.text[:1000]
            return None, record

        card = self._card_from_llm_payload(state, paper, base_card, payload, evidence_ids)
        record["status"] = "ok"
        record["response_preview"] = response.text[:1000]
        return card, record

    def _llm_budget_allows(self, state: ResearchState, settings: dict[str, Any]) -> tuple[bool, str]:
        call_budget = settings.get("llm_call_budget")
        token_budget = settings.get("llm_token_budget")
        calls_used = int(state.values.get("llm_calls_used", 0))
        tokens_used = int(state.values.get("llm_tokens_used", 0))
        if isinstance(call_budget, int) and call_budget >= 0 and calls_used >= call_budget:
            return False, "skipped_call_budget"
        if isinstance(token_budget, int) and token_budget >= 0 and tokens_used >= token_budget:
            return False, "skipped_token_budget"
        return True, "allowed"

    def _record_llm_usage(self, state: ResearchState, usage: dict[str, Any]) -> None:
        state.values["llm_calls_used"] = int(state.values.get("llm_calls_used", 0)) + 1
        total_tokens = usage.get("total_tokens", 0)
        try:
            token_count = int(total_tokens)
        except (TypeError, ValueError):
            token_count = 0
        state.values["llm_tokens_used"] = int(state.values.get("llm_tokens_used", 0)) + token_count

    def _build_llm_messages(
        self,
        state: ResearchState,
        paper: dict[str, Any],
        parsed_text: str,
    ) -> list[dict[str, str]]:
        fields = [
            "task",
            "problem_setting",
            "input_modalities",
            "output",
            "model_architecture",
            "temporal_modeling",
            "fusion_strategy",
            "training_objective",
            "datasets",
            "metrics",
            "main_results",
            "limitations",
            "reusable_ideas_for_current_topic",
            "implementation_difficulty",
            "risk",
        ]
        excerpt = parsed_text[:8000]
        return [
            {
                "role": "system",
                "content": (
                    "You extract structured method cards from research paper text. "
                    "Return only one valid JSON object with no markdown."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Topic: {state.topic.topic_name}\n"
                    f"Research goal: {state.topic.research_goal.get('short', '')}\n"
                    f"Paper title: {paper.get('title', '')}\n"
                    f"Required JSON fields: {', '.join(fields)}\n"
                    "Use arrays for modalities, datasets, metrics, limitations, reusable ideas, and risk. "
                    "Use objects for model_architecture and fusion_strategy. "
                    "If a field is not supported by the excerpt, write a cautious empty value or limitation.\n\n"
                    f"Paper excerpt:\n{excerpt}"
                ),
            },
        ]

    def _card_from_llm_payload(
        self,
        state: ResearchState,
        paper: dict[str, Any],
        base_card: MethodCard,
        payload: dict[str, Any],
        evidence_ids: list[str],
    ) -> MethodCard:
        risk = self._as_str_list(payload.get("risk"), base_card.risk)
        verification_risk = "llm-extracted card requires human verification against source PDF"
        if verification_risk not in risk:
            risk.append(verification_risk)
        return MethodCard(
            paper_id=paper["paper_id"],
            method_card_id=base_card.method_card_id,
            task=self._as_str(payload.get("task"), base_card.task),
            problem_setting=self._as_str(payload.get("problem_setting"), base_card.problem_setting),
            input_modalities=self._as_str_list(
                payload.get("input_modalities"), base_card.input_modalities
            ),
            output=self._as_str(payload.get("output"), base_card.output),
            model_architecture=self._as_str_dict(
                payload.get("model_architecture"), base_card.model_architecture
            ),
            temporal_modeling=self._as_str(payload.get("temporal_modeling"), base_card.temporal_modeling),
            fusion_strategy=self._as_str_dict(
                payload.get("fusion_strategy"), base_card.fusion_strategy
            ),
            training_objective=self._as_str(
                payload.get("training_objective"), base_card.training_objective
            ),
            datasets=self._as_str_list(payload.get("datasets"), base_card.datasets),
            metrics=self._as_str_list(payload.get("metrics"), base_card.metrics),
            main_results=self._as_str(payload.get("main_results"), base_card.main_results),
            limitations=self._as_str_list(payload.get("limitations"), base_card.limitations),
            reusable_ideas_for_current_topic=self._as_str_list(
                payload.get("reusable_ideas_for_current_topic"),
                base_card.reusable_ideas_for_current_topic,
            ),
            implementation_difficulty=self._as_str(
                payload.get("implementation_difficulty"), base_card.implementation_difficulty
            ),
            risk=risk,
            evidence_ids=evidence_ids,
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

    def _as_str(self, value: Any, fallback: str) -> str:
        if value is None:
            return fallback
        text = str(value).strip()
        return text or fallback

    def _as_str_list(self, value: Any, fallback: list[str]) -> list[str]:
        if isinstance(value, list):
            cleaned = [str(item).strip() for item in value if str(item).strip()]
            return cleaned or list(fallback)
        if isinstance(value, str) and value.strip():
            return [value.strip()]
        return list(fallback)

    def _as_str_dict(self, value: Any, fallback: dict[str, str]) -> dict[str, str]:
        if isinstance(value, dict):
            cleaned = {
                str(key).strip(): str(item).strip()
                for key, item in value.items()
                if str(key).strip() and str(item).strip()
            }
            return cleaned or dict(fallback)
        return dict(fallback)
