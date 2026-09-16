from __future__ import annotations

import json
from typing import Any

from core.agent_base import Agent, AgentContext, AgentResult
from core.state import ResearchState
from schemas.base import new_id
from tools.llm_budget import llm_budget_allows, llm_usage_values, record_llm_usage
from tools.llm_client import OpenAICompatibleClient, extract_json_object
from tools.model_router import ModelRoute, ModelRouter


class PaperTriageAgent(Agent):
    name = "paper_triage"

    def __init__(self, llm_client: OpenAICompatibleClient | None = None):
        self.llm_client = llm_client or OpenAICompatibleClient()

    def run(self, state: ResearchState, context: AgentContext) -> AgentResult:
        papers = state.values.get("papers", [])
        selected = self._rule_based_triage(state, papers)
        llm_call_ids: list[str] = []
        llm_success = 0
        if context.settings.get("enable_llm") and len(papers) > 0:
            route = ModelRouter(state.topic).route_for(self.name)
            calls_before = int(state.values.get("llm_calls_used", 0))
            llm_selected, record = self._try_llm_triage(state, context.settings, route, papers)
            call_id = new_id("llm_call")
            context.artifact_store.save_json(state.run_id, "llm_calls", call_id, record)
            llm_call_ids.append(call_id)
            if llm_selected is not None:
                selected = llm_selected
                llm_success = 1
            state.values["triage_llm_call_count"] = int(state.values.get("llm_calls_used", 0)) - calls_before
            state.values["triage_llm_record_count"] = len(llm_call_ids)
            state.values["triage_llm_success_count"] = llm_success

        state.values["selected_papers"] = selected
        context.artifact_store.save_json(state.run_id, "triage", "paper_triage", selected)
        artifacts = {"triage": ["paper_triage"]}
        if llm_call_ids:
            artifacts["llm_calls"] = llm_call_ids
        notes = [f"selected {len(selected)} papers for reading"]
        if context.settings.get("enable_llm"):
            notes.append(f"triage LLM success={llm_success}")
        return AgentResult(
            notes=notes,
            artifacts=artifacts,
            values={
                "selected_paper_count": len(selected),
                "triage_llm_success_count": llm_success,
                **llm_usage_values(state),
            },
        )

    def _rule_based_triage(self, state: ResearchState, papers: list[dict]) -> list[dict]:
        keywords = {keyword.lower() for keyword in state.topic.keywords()}
        selected = []
        for paper in papers:
            text = f"{paper.get('title', '')} {paper.get('abstract', '')}".lower()
            matches = sum(1 for keyword in keywords if keyword.lower() in text)
            paper["relevance_score"] = min(1.0, 0.4 + 0.2 * matches)
            paper["triage_reason"] = (
                "selected from topic seed keywords"
                if paper.get("source") == "offline_seed"
                else "selected by keyword overlap"
            )
            if paper["relevance_score"] >= 0.4:
                selected.append(paper)
        return selected

    def _try_llm_triage(
        self,
        state: ResearchState,
        settings: dict[str, Any],
        route: ModelRoute,
        papers: list[dict],
    ) -> tuple[list[dict] | None, dict[str, Any]]:
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
        if not papers:
            record["status"] = "skipped_no_papers"
            return None, record
        allowed, reason = llm_budget_allows(state, settings)
        if not allowed:
            record["status"] = reason
            record.update(llm_usage_values(state))
            return None, record

        messages = self._build_llm_messages(state, papers)
        record["prompt_chars"] = sum(len(m.get("content", "")) for m in messages)
        response = self.llm_client.chat(route, messages, temperature=0.1, max_tokens=2000)
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
        scored = payload.get("papers")
        if not isinstance(scored, list) or len(scored) == 0:
            record["status"] = "missing_papers_list"
            record["response_preview"] = response.text[:1000]
            return None, record

        selected = self._merge_triage(papers, scored)
        record["status"] = "ok"
        record["response_preview"] = response.text[:1000]
        return selected, record

    def _build_llm_messages(self, state: ResearchState, papers: list[dict]) -> list[dict[str, str]]:
        candidates = []
        for i, p in enumerate(papers):
            candidates.append({
                "index": i,
                "title": p.get("title", "")[:300],
                "abstract": p.get("abstract", "")[:600],
                "year": p.get("year", ""),
            })
        payload = {
            "topic": state.topic.topic_name,
            "research_goal": state.topic.research_goal.get("short", ""),
            "primary_area": state.topic.domain.get("primary_area", ""),
            "keywords": state.topic.keywords(),
            "candidates": candidates,
        }
        return [
            {
                "role": "system",
                "content": (
                    "You triage research papers for a literature review. "
                    "For each paper, assign a relevance_score (0.0-1.0) and a decision: read, skim, or discard. "
                    "Return only one valid JSON object with key 'papers' mapping to an array of "
                    "{index, relevance_score, decision, reason}. "
                    "Prefer papers that match the topic's primary area and research goal. "
                    "Keep decision reasons under 120 characters."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(payload, ensure_ascii=False, indent=2)[:14000],
            },
        ]

    def _merge_triage(self, original: list[dict], scored: list[dict]) -> list[dict]:
        score_map: dict[int, dict] = {}
        for item in scored:
            idx = item.get("index")
            if isinstance(idx, int) and 0 <= idx < len(original):
                score_map[idx] = item
        selected = []
        for i, paper in enumerate(original):
            llm = score_map.get(i, {})
            paper["relevance_score"] = float(llm.get("relevance_score", paper.get("relevance_score", 0.4)))
            decision = str(llm.get("decision", "read")).strip().lower()
            reason = str(llm.get("reason", "")).strip()
            paper["triage_decision"] = decision if decision in {"read", "skim", "discard"} else "read"
            paper["triage_reason"] = reason or paper.get("triage_reason", "LLM triage")
            if paper["triage_decision"] in {"read", "skim"}:
                selected.append(paper)
        return selected
