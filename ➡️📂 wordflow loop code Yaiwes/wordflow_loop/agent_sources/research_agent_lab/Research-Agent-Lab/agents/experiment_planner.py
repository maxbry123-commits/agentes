from __future__ import annotations

from dataclasses import asdict
import json
from typing import Any

from core.agent_base import Agent, AgentContext, AgentResult
from core.state import ResearchState
from schemas.base import new_id
from schemas.experiment_plan import ExperimentPlan
from tools.llm_budget import llm_budget_allows, llm_usage_values, record_llm_usage
from tools.llm_client import OpenAICompatibleClient, extract_json_object
from tools.model_router import ModelRoute, ModelRouter


class ExperimentPlannerAgent(Agent):
    name = "experiment_planner"

    def __init__(self, llm_client: OpenAICompatibleClient | None = None):
        self.llm_client = llm_client or OpenAICompatibleClient()

    def run(self, state: ResearchState, context: AgentContext) -> AgentResult:
        plan = self._rule_based_plan(state)
        llm_call_ids: list[str] = []
        llm_success = 0
        if context.settings.get("enable_llm"):
            route = ModelRouter(state.topic).route_for(self.name)
            calls_before = int(state.values.get("llm_calls_used", 0))
            llm_plan, record = self._try_llm_plan(state, context.settings, route, plan)
            call_id = new_id("llm_call")
            context.artifact_store.save_json(state.run_id, "llm_calls", call_id, record)
            llm_call_ids.append(call_id)
            if llm_plan is not None:
                plan = llm_plan
                llm_success = 1
            state.values["experiment_planner_llm_call_count"] = (
                int(state.values.get("llm_calls_used", 0)) - calls_before
            )
            state.values["experiment_planner_llm_record_count"] = len(llm_call_ids)
            state.values["experiment_planner_llm_success_count"] = llm_success

        context.artifact_store.save_json(state.run_id, "experiment_plans", plan.experiment_id, plan)
        state.values["experiment_plans"] = [asdict(plan)]
        artifacts = {"experiment_plans": [plan.experiment_id]}
        if llm_call_ids:
            artifacts["llm_calls"] = llm_call_ids
        notes = ["created controlled experiment plan"]
        if context.settings.get("enable_llm"):
            notes.append(f"experiment planner LLM success={llm_success}")
        return AgentResult(
            notes=notes,
            artifacts=artifacts,
            values={
                "experiment_plan_count": 1,
                "experiment_planner_llm_success_count": llm_success,
                **llm_usage_values(state),
            },
        )

    def _rule_based_plan(self, state: ResearchState) -> ExperimentPlan:
        opportunity = state.values.get("opportunities", [{}])[0]
        codebase_report = state.values.get("codebase_report", {})
        allowed_files = codebase_report.get("suggested_first_patch_files") or state.topic.allowed_auto_edit()
        metrics = list(state.topic.experiment_metrics)
        historical = state.values.get("historical_method_cards", []) or []
        for card in historical[:5]:
            for m in card.get("metrics", []) or []:
                if m not in metrics:
                    metrics.append(m)
        ablation = [
            "baseline unchanged",
            "minimal modification enabled",
            "modification disabled with same config",
        ]
        if historical:
            for card in historical[:3]:
                for idea in card.get("reusable_ideas_for_current_topic", []) or []:
                    if isinstance(idea, str) and idea not in ablation:
                        ablation.append(f"historical insight: {idea}")
                        break
            ablation = ablation[:5]
        return ExperimentPlan(
            name=opportunity.get("title", f"First experiment for {state.topic.topic_name}"),
            hypothesis=opportunity.get("hypothesis", ""),
            baseline=self._baseline_hint(state),
            modification=opportunity.get("technical_strategy", ""),
            files_to_change=allowed_files,
            dataset=str(state.topic.current_status.get("dataset", "")),
            training_config={
                "mode": "smoke-first",
                "epochs": state.topic.current_status.get("default_epochs", "to_confirm"),
                "batch_size": state.topic.current_status.get("default_batch_size", "to_confirm"),
            },
            metrics=metrics,
            ablation_studies=ablation,
            acceptance_criteria={
                "must_run": True,
                "requires_human_approval_before_code_edit": True,
                "metric_check": "compare against baseline on the same split",
                "no_data_leakage": True,
            },
            rollback_plan="keep changes as a reviewable patch; do not auto-commit",
        )

    def _try_llm_plan(
        self,
        state: ResearchState,
        settings: dict[str, Any],
        route: ModelRoute,
        base_plan: ExperimentPlan,
    ) -> tuple[ExperimentPlan | None, dict[str, Any]]:
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
        if not state.values.get("opportunities"):
            record["status"] = "skipped_no_opportunity"
            return None, record
        allowed, reason = llm_budget_allows(state, settings)
        if not allowed:
            record["status"] = reason
            record.update(llm_usage_values(state))
            return None, record

        messages = self._build_llm_messages(state, base_plan)
        record["prompt_chars"] = sum(len(message["content"]) for message in messages)
        response = self.llm_client.chat(route, messages, temperature=0.1, max_tokens=2600)
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
        plan = self._plan_from_payload(state, payload, base_plan)
        record["status"] = "ok"
        record["response_preview"] = response.text[:1000]
        return plan, record

    def _build_llm_messages(
        self,
        state: ResearchState,
        base_plan: ExperimentPlan,
    ) -> list[dict[str, str]]:
        codebase = state.values.get("codebase_report", {})
        payload = {
            "topic": state.topic.to_dict(),
            "method_cards": (
                state.values.get("method_cards", [])[:4]
                + (state.values.get("historical_method_cards", []) or [])[:4]
            ),
            "synthesis_report": state.values.get("synthesis_report", "")[:5000],
            "opportunity": (state.values.get("opportunities", [{}]) or [{}])[0],
            "codebase_report": {
                "repo_path": codebase.get("repo_path"),
                "integration_points": codebase.get("integration_points", []),
                "suggested_first_patch_files": codebase.get("suggested_first_patch_files", []),
                "protected_files": codebase.get("protected_files", []),
            },
            "base_plan": asdict(base_plan),
        }
        fields = [
            "name",
            "hypothesis",
            "baseline",
            "modification",
            "files_to_change",
            "dataset",
            "training_config",
            "metrics",
            "ablation_studies",
            "acceptance_criteria",
            "rollback_plan",
            "commands",
        ]
        return [
            {
                "role": "system",
                "content": (
                    "You convert evidence-backed research opportunities into controlled experiment plans. "
                    "Return only one valid JSON object matching the requested fields. "
                    "Keep plans small, smoke-test first, and do not propose edits outside allowed files."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Required fields: {', '.join(fields)}\n"
                    "The plan must include concrete files_to_change, commands (list of shell command strings like "
                    "['python main.py --train 1 --max_epochs 5']), "
                    "ablation_studies, acceptance_criteria, and rollback_plan. "
                    "Do not claim metric improvement before an experiment runs.\n\n"
                    + json.dumps(payload, ensure_ascii=False, indent=2)[:15000]
                ),
            },
        ]

    def _plan_from_payload(
        self,
        state: ResearchState,
        payload: dict[str, Any],
        base_plan: ExperimentPlan,
    ) -> ExperimentPlan:
        allowed = set(state.topic.allowed_auto_edit())
        files = self._as_str_list(payload.get("files_to_change"), base_plan.files_to_change)
        if allowed:
            files = [path for path in files if self._is_allowed_file(path, allowed)]
            if not files:
                files = base_plan.files_to_change
        criteria = self._as_dict(payload.get("acceptance_criteria"), base_plan.acceptance_criteria)
        criteria.setdefault("requires_human_approval_before_code_edit", True)
        criteria.setdefault("must_run", True)
        return ExperimentPlan(
            experiment_id=base_plan.experiment_id,
            name=self._as_str(payload.get("name"), base_plan.name),
            hypothesis=self._as_str(payload.get("hypothesis"), base_plan.hypothesis),
            baseline=self._as_str(payload.get("baseline"), base_plan.baseline),
            modification=self._as_str(payload.get("modification"), base_plan.modification),
            files_to_change=files,
            dataset=self._as_str(payload.get("dataset"), base_plan.dataset),
            training_config=self._as_dict(payload.get("training_config"), base_plan.training_config),
            metrics=self._as_str_list(payload.get("metrics"), base_plan.metrics),
            ablation_studies=self._as_str_list(
                payload.get("ablation_studies"), base_plan.ablation_studies
            ),
            acceptance_criteria=criteria,
            rollback_plan=self._as_str(payload.get("rollback_plan"), base_plan.rollback_plan),
            commands=self._as_str_list(payload.get("commands"), base_plan.commands),
        )

    def _baseline_hint(self, state: ResearchState) -> str:
        baselines = state.topic.current_status.get("baseline_methods", [])
        if isinstance(baselines, list) and baselines:
            return ", ".join(str(item) for item in baselines)
        return str(state.topic.current_status.get("baseline", "current baseline"))

    def _is_allowed_file(self, path: str, allowed_patterns: set[str]) -> bool:
        normalized = path.replace("\\", "/")
        for pattern in allowed_patterns:
            prefix = pattern.replace("\\", "/").rstrip("*")
            if normalized.startswith(prefix):
                return True
        return False

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

    def _as_dict(self, value: Any, fallback: dict[str, object]) -> dict[str, object]:
        if isinstance(value, dict):
            return {str(key): item for key, item in value.items()}
        return dict(fallback)
