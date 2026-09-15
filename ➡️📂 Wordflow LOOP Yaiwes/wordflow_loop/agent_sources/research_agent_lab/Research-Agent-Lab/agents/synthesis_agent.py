from __future__ import annotations

import json
from typing import Any

from core.agent_base import Agent, AgentContext, AgentResult
from core.state import ResearchState
from schemas.base import new_id
from tools.llm_budget import llm_budget_allows, llm_usage_values, record_llm_usage
from tools.llm_client import OpenAICompatibleClient, extract_json_object
from tools.model_router import ModelRoute, ModelRouter


class SynthesisAgent(Agent):
    name = "synthesis"

    def __init__(self, llm_client: OpenAICompatibleClient | None = None):
        self.llm_client = llm_client or OpenAICompatibleClient()

    def run(self, state: ResearchState, context: AgentContext) -> AgentResult:
        cards = state.values.get("method_cards", [])
        text = self._rule_based_report(state)
        llm_call_ids: list[str] = []
        llm_success = 0
        if context.settings.get("enable_llm"):
            route = ModelRouter(state.topic).route_for(self.name)
            calls_before = int(state.values.get("llm_calls_used", 0))
            llm_text, record = self._try_llm_synthesis(state, context.settings, route)
            call_id = new_id("llm_call")
            context.artifact_store.save_json(state.run_id, "llm_calls", call_id, record)
            llm_call_ids.append(call_id)
            if llm_text:
                text = llm_text
                llm_success = 1
            state.values["synthesis_llm_call_count"] = int(state.values.get("llm_calls_used", 0)) - calls_before
            state.values["synthesis_llm_record_count"] = len(llm_call_ids)
            state.values["synthesis_llm_success_count"] = llm_success

        context.artifact_store.save_text(state.run_id, "reports", "synthesis_report", text)
        state.values["synthesis_report"] = text
        artifacts = {"reports": ["synthesis_report"]}
        if llm_call_ids:
            artifacts["llm_calls"] = llm_call_ids
        notes = ["wrote synthesis report"]
        if context.settings.get("enable_llm"):
            notes.append(f"synthesis LLM success={llm_success}")
        return AgentResult(
            notes=notes,
            artifacts=artifacts,
            values={
                "synthesis_llm_success_count": llm_success,
                **llm_usage_values(state),
            },
        )

    def _rule_based_report(self, state: ResearchState) -> str:
        cards = state.values.get("method_cards", [])
        metrics = ", ".join(state.topic.experiment_metrics) or "topic-specific metrics"
        report = [
            f"# Synthesis Report: {state.topic.topic_name}",
            "",
            "## Scope",
            state.topic.research_goal.get("short", state.topic.research_goal.get("long", "")),
            "",
            "## Current Evidence Level",
            "This V1 run used offline seed papers unless online tools were enabled.",
            "Strong conclusions require full-paper parsing and evidence confirmation.",
            "",
            "## Method Themes",
        ]
        for card in cards[:8]:
            report.append(f"- {card['task']}: {', '.join(card.get('input_modalities', []))}")
        report.extend(
            [
                "",
                "## Evaluation Metrics",
                metrics,
            ]
        )
        return "\n".join(report).strip() + "\n"

    def _try_llm_synthesis(
        self,
        state: ResearchState,
        settings: dict[str, Any],
        route: ModelRoute,
    ) -> tuple[str | None, dict[str, Any]]:
        record: dict[str, Any] = {
            "agent": self.name,
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
        cards = state.values.get("method_cards", [])
        if not cards:
            record["status"] = "skipped_no_method_cards"
            return None, record
        allowed, reason = llm_budget_allows(state, settings)
        if not allowed:
            record["status"] = reason
            record.update(llm_usage_values(state))
            return None, record

        messages = self._build_llm_messages(state)
        record["prompt_chars"] = sum(len(message["content"]) for message in messages)
        response = self.llm_client.chat(route, messages, temperature=0.2, max_tokens=1800)
        record["response_chars"] = len(response.text)
        record["usage"] = response.usage
        record["attempts"] = response.attempts
        record_llm_usage(state, response.usage)
        if not response.ok:
            record["status"] = "error"
            record["error"] = response.error[:500]
            return None, record

        payload = extract_json_object(response.text)
        if payload is None:
            record["status"] = "invalid_json"
            record["response_preview"] = response.text[:1000]
            return None, record
        report = str(payload.get("report_markdown", "")).strip()
        if not report:
            record["status"] = "missing_report_markdown"
            record["response_preview"] = response.text[:1000]
            return None, record
        record["status"] = "ok"
        record["response_preview"] = response.text[:1000]
        warnings = payload.get("evidence_warnings", [])
        if isinstance(warnings, list):
            state.values["synthesis_evidence_warnings"] = [str(item) for item in warnings]
        return report + "\n", record

    def _build_llm_messages(self, state: ResearchState) -> list[dict[str, str]]:
        context_payload = {
            "topic": state.topic.to_dict(),
            "method_cards": state.values.get("method_cards", [])[:8],
            "checked_evidence": state.values.get("checked_evidence", [])[:16],
            "selected_context_summary": [
                {
                    "paper_id": item.get("paper_id"),
                    "context_id": item.get("context_id"),
                    "chunk_count": len(item.get("chunks", [])),
                }
                for item in state.values.get("selected_contexts", [])[:8]
            ],
        }
        return [
            {
                "role": "system",
                "content": (
                    "You write evidence-constrained research synthesis reports. "
                    "Return only one valid JSON object with keys report_markdown and evidence_warnings. "
                    "Do not make strong claims unless supported by evidence_ids or method card fields."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Write a concise synthesis report for the current topic. "
                    "Use Markdown in report_markdown. Mark unsupported conclusions as pending verification. "
                    "Include practical implications for the current codebase only when the provided context supports them.\n\n"
                    + json.dumps(context_payload, ensure_ascii=False, indent=2)[:14000]
                ),
            },
        ]
