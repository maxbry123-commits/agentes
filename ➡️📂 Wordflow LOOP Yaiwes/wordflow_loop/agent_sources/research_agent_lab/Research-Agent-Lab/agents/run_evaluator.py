from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

from core.agent_base import Agent, AgentContext, AgentResult
from core.artifact_store import ArtifactStore
from core.state import ResearchState
from schemas.run_evaluation import RunEvaluationCheck, RunEvaluationReport


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


class RunEvaluationAgent(Agent):
    name = "run_evaluator"

    def run(self, state: ResearchState, context: AgentContext) -> AgentResult:
        checks: list[RunEvaluationCheck] = []

        checks.extend(_literature_checks(state))
        checks.extend(_retrieval_evaluation_checks(state, context.settings))
        checks.extend(_budget_checks(state, context.settings))
        checks.extend(_experiment_checks(state, context.settings))
        checks.extend(_tree_checks(state))
        checks.extend(_review_checks(state))
        checks.extend(_llm_call_checks(state, context.artifact_store))

        blocking = [c.message for c in checks if c.status == "fail" and c.severity == "blocker"]
        warnings = [c.message for c in checks if c.status in {"warn", "fail"} and c.severity != "blocker"]
        score = _score(checks)
        status = "block" if blocking else ("needs_review" if warnings or score < 85 else "pass")
        action = _recommended_action(status, checks)

        report = RunEvaluationReport(
            status=status,
            score=score,
            checks=checks,
            blocking_issues=blocking,
            warnings=warnings,
            recommended_next_action=action,
            summary=[
                f"status={status}",
                f"score={score}",
                f"checks={len(checks)}",
                f"blocking={len(blocking)}",
                f"warnings={len(warnings)}",
            ],
        )
        payload = asdict(report)
        context.artifact_store.save_json(
            state.run_id, "run_evaluations", report.evaluation_id, payload
        )
        state.values["run_evaluation"] = payload
        state.values["run_evaluation_status"] = status
        state.values["run_quality_score"] = score
        return AgentResult(
            notes=[f"run evaluation status={status} score={score}"],
            artifacts={"run_evaluations": [report.evaluation_id]},
            values={
                "run_evaluation": payload,
                "run_evaluation_status": status,
                "run_quality_score": score,
            },
        )


def _literature_checks(state: ResearchState) -> list[RunEvaluationCheck]:
    selected = _safe_int(state.values.get("selected_paper_count", 0))
    method_cards = _safe_int(state.values.get("method_card_count", 0) or len(state.values.get("method_cards", []) or []))
    unsupported = _safe_int(state.values.get("unsupported_evidence_count", 0))
    checks = [
        RunEvaluationCheck(
            name="literature_selected_papers",
            status="pass" if selected > 0 else "warn",
            severity="warning",
            message="selected papers are available" if selected > 0 else "no selected papers found",
            evidence={"selected_paper_count": selected},
        ),
        RunEvaluationCheck(
            name="method_cards",
            status="pass" if method_cards >= min(selected, 1) else "warn",
            severity="warning",
            message="method cards are available" if method_cards else "no method cards found",
            evidence={"method_card_count": method_cards, "selected_paper_count": selected},
        ),
        RunEvaluationCheck(
            name="evidence_support",
            status="pass" if unsupported == 0 else "fail",
            severity="warning",
            message="no unsupported evidence" if unsupported == 0 else f"{unsupported} unsupported evidence record(s)",
            evidence={"unsupported_evidence_count": unsupported},
        ),
    ]
    return checks


def _retrieval_evaluation_checks(
    state: ResearchState, settings: dict[str, Any]
) -> list[RunEvaluationCheck]:
    enabled = bool(settings.get("enable_retrieval_evaluation"))
    report = state.values.get("retrieval_evaluation")
    if not enabled:
        return []
    if not isinstance(report, dict):
        return [RunEvaluationCheck(
            name="retrieval_evaluation",
            status="warn",
            severity="warning",
            message="retrieval evaluation was enabled but no report was produced",
            evidence={"enable_retrieval_evaluation": enabled},
        )]
    status = str(report.get("status", "unknown"))
    score = _safe_int(report.get("score", 0) or 0)
    if status == "block":
        return [RunEvaluationCheck(
            name="retrieval_evaluation",
            status="fail",
            severity="blocker",
            message=f"retrieval evaluation blocked run: score={score}",
            evidence={
                "retrieval_status": status,
                "retrieval_score": score,
                "blocking_issues": report.get("blocking_issues", []),
            },
        )]
    if status == "needs_review":
        return [RunEvaluationCheck(
            name="retrieval_evaluation",
            status="warn",
            severity="warning",
            message=f"retrieval evaluation needs review: score={score}",
            evidence={
                "retrieval_status": status,
                "retrieval_score": score,
                "warnings": report.get("warnings", []),
            },
        )]
    if status == "pass":
        return [RunEvaluationCheck(
            name="retrieval_evaluation",
            status="pass",
            severity="info",
            message=f"retrieval evaluation status={status} score={score}",
            evidence={"retrieval_status": status, "retrieval_score": score},
        )]
    return [RunEvaluationCheck(
        name="retrieval_evaluation",
        status="warn",
        severity="warning",
        message=f"retrieval evaluation returned unknown status: {status}",
        evidence={"retrieval_status": status, "retrieval_score": score},
    )]


def _budget_checks(state: ResearchState, settings: dict[str, Any]) -> list[RunEvaluationCheck]:
    calls = _safe_int(state.values.get("llm_calls_used", 0))
    tokens = _safe_int(state.values.get("llm_tokens_used", 0))
    call_budget = settings.get("llm_call_budget")
    token_budget = settings.get("llm_token_budget")
    checks: list[RunEvaluationCheck] = []
    if isinstance(call_budget, int) and call_budget >= 0:
        checks.append(RunEvaluationCheck(
            name="llm_call_budget",
            status="pass" if calls <= call_budget else "fail",
            severity="blocker",
            message="LLM call budget ok" if calls <= call_budget else f"LLM call budget exceeded: {calls}>{call_budget}",
            evidence={"llm_calls_used": calls, "llm_call_budget": call_budget},
        ))
    elif settings.get("enable_llm"):
        checks.append(RunEvaluationCheck(
            name="llm_call_budget",
            status="warn",
            severity="warning",
            message="LLM is enabled but no call budget is configured; unlimited calls possible",
            evidence={"llm_calls_used": calls},
        ))
    if isinstance(token_budget, int) and token_budget >= 0:
        checks.append(RunEvaluationCheck(
            name="llm_token_budget",
            status="pass" if tokens <= token_budget else "fail",
            severity="blocker",
            message="LLM token budget ok" if tokens <= token_budget else f"LLM token budget exceeded: {tokens}>{token_budget}",
            evidence={"llm_tokens_used": tokens, "llm_token_budget": token_budget},
        ))
    elif settings.get("enable_llm"):
        checks.append(RunEvaluationCheck(
            name="llm_token_budget",
            status="warn",
            severity="warning",
            message="LLM is enabled but no token budget is configured; unlimited tokens possible",
            evidence={"llm_tokens_used": tokens},
        ))
    return checks


def _experiment_checks(state: ResearchState, settings: dict[str, Any]) -> list[RunEvaluationCheck]:
    results = state.values.get("experiment_results") or []
    if not results:
        experiments_enabled = bool(settings.get("enable_experiments"))
        return [RunEvaluationCheck(
            name="experiment_results",
            status="fail" if experiments_enabled else "pass",
            severity="blocker" if experiments_enabled else "info",
            message=(
                "experiments were enabled but no experiment results were produced"
                if experiments_enabled
                else "experiments disabled; no experiment results expected"
            ),
            evidence={"enable_experiments": experiments_enabled},
        )]
    errors = [r for r in results if isinstance(r, dict) and r.get("status") == "error"]
    unparsed = [r for r in results if isinstance(r, dict) and r.get("status") == "unparsed"]
    return [
        RunEvaluationCheck(
            name="experiment_errors",
            status="pass" if not errors else "fail",
            severity="blocker",
            message="no experiment execution errors" if not errors else f"{len(errors)} experiment error(s)",
            evidence={"error_count": len(errors)},
        ),
        RunEvaluationCheck(
            name="experiment_unparsed",
            status="pass" if not unparsed else "warn",
            severity="warning",
            message="all experiment results parsed" if not unparsed else f"{len(unparsed)} unparsed experiment result(s)",
            evidence={"unparsed_count": len(unparsed)},
        ),
    ]


def _tree_checks(state: ResearchState) -> list[RunEvaluationCheck]:
    tree = state.values.get("experiment_tree")
    if not isinstance(tree, dict) or not tree.get("nodes"):
        return [RunEvaluationCheck(
            name="experiment_tree",
            status="pass",
            severity="info",
            message="no experiment tree to evaluate",
            evidence={},
        )]
    nodes = tree.get("nodes") or []
    root_id = tree.get("root_id", "")
    node_ids = {n.get("node_id") for n in nodes}
    selected_without_result = [
        n.get("node_id") for n in nodes
        if n.get("status") == "selected" and not (
            isinstance(n.get("result"), dict) and n["result"].get("status")
        )
    ]
    pending = [
        n for n in nodes
        if n.get("status") == "pending" and n.get("depth", 0) < tree.get("max_depth", 2)
    ]
    max_active = int(tree.get("max_active_nodes", 3) or 3)
    checks = [
        RunEvaluationCheck(
            name="tree_root_exists",
            status="pass" if root_id in node_ids else "fail",
            severity="blocker",
            message="experiment tree root exists" if root_id in node_ids else f"experiment tree root missing: {root_id}",
            evidence={"root_id": root_id, "node_count": len(nodes)},
        ),
        RunEvaluationCheck(
            name="tree_selected_nodes",
            status="pass" if not selected_without_result else "fail",
            severity="blocker",
            message="no selected nodes without result" if not selected_without_result else f"selected nodes without result: {selected_without_result}",
            evidence={"selected_without_result": selected_without_result},
        ),
        RunEvaluationCheck(
            name="tree_active_width",
            status="pass" if len(pending) <= max_active else "fail",
            severity="warning",
            message="pending branch count within max active" if len(pending) <= max_active else f"pending branches exceed max active: {len(pending)}>{max_active}",
            evidence={"pending_count": len(pending), "max_active_nodes": max_active},
        ),
    ]
    checks.extend(_tree_bidirectional_checks(nodes, root_id))
    return checks


def _tree_bidirectional_checks(nodes: list[dict], root_id: str) -> list[RunEvaluationCheck]:
    node_map = {n.get("node_id"): n for n in nodes}
    problems: list[str] = []
    for node in nodes:
        nid = node.get("node_id")
        for cid in node.get("children_ids", []) or []:
            child = node_map.get(cid)
            if not child:
                problems.append(f"{nid} references missing child {cid}")
            elif child.get("parent_id") != nid:
                problems.append(f"{nid}->{cid} but child parent_id={child.get('parent_id')}")
    for node in nodes:
        nid = node.get("node_id")
        pid = node.get("parent_id")
        if nid == root_id:
            if pid:
                problems.append(f"root node {nid} has parent_id={pid}, should be empty")
            continue
        if not pid:
            problems.append(f"{nid} is not root but has no parent_id")
            continue
        parent = node_map.get(pid)
        if not parent:
            problems.append(f"{nid} parent_id={pid} but parent not found")
        elif nid not in (parent.get("children_ids") or []):
            problems.append(f"{nid} parent_id={pid} but parent does not list it in children_ids")
    return [RunEvaluationCheck(
        name="tree_bidirectional_links",
        status="pass" if not problems else "fail",
        severity="warning",
        message="tree parent/child links are consistent" if not problems else "; ".join(problems[:5]),
        evidence={"problem_count": len(problems), "problems": problems[:10]},
    )]


def _review_checks(state: ResearchState) -> list[RunEvaluationCheck]:
    review_status = str(state.values.get("review_status", "unknown"))
    return [RunEvaluationCheck(
        name="review_status",
        status="pass" if review_status == "pass" else "warn",
        severity="warning",
        message=f"review_status={review_status}",
        evidence={"review_status": review_status},
    )]


def _llm_call_checks(state: ResearchState, artifact_store: ArtifactStore) -> list[RunEvaluationCheck]:
    checks: list[RunEvaluationCheck] = []

    llm_agents: list[tuple[str, str, bool]] = [
        ("experiment_planner", "experiment_planner", True),
        ("method_card_extractor", "method_card", True),
        ("paper_triage", "triage", False),
        ("synthesis_agent", "synthesis", False),
    ]

    for agent_name, prefix, is_critical in llm_agents:
        record_count = _safe_int(state.values.get(f"{prefix}_llm_record_count", 0))
        success_count = _safe_int(state.values.get(f"{prefix}_llm_success_count", 0))
        if record_count == 0:
            continue
        if success_count > 0:
            continue
        severity = "blocker" if is_critical else "warning"
        status = "fail" if is_critical else "warn"
        checks.append(RunEvaluationCheck(
            name=f"llm_{prefix}_success",
            status=status,
            severity=severity,
            message=f"{agent_name} had {record_count} LLM call(s) but 0 succeeded",
            evidence={"agent": agent_name, "record_count": record_count, "success_count": success_count},
        ))

    call_files = artifact_store.list_artifacts(state.run_id, "llm_calls")
    non_ok_by_status: dict[str, list[str]] = {}
    for path in call_files:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        status = data.get("status", "")
        agent = data.get("agent", "unknown")
        if status != "ok":
            non_ok_by_status.setdefault(status, []).append(agent)

    for status, agents in non_ok_by_status.items():
        if status == "error":
            checks.append(RunEvaluationCheck(
                name="llm_errors",
                status="fail",
                severity="blocker",
                message=f"{len(agents)} LLM call(s) returned error: {', '.join(agents[:5])}",
                evidence={"error_call_count": len(agents), "agents": agents},
            ))
        elif status == "invalid_json":
            checks.append(RunEvaluationCheck(
                name="llm_invalid_json",
                status="warn",
                severity="warning",
                message=f"{len(agents)} LLM call(s) returned invalid_json: {', '.join(agents[:5])}",
                evidence={"invalid_json_call_count": len(agents), "agents": agents},
            ))
        else:
            checks.append(RunEvaluationCheck(
                name=f"llm_{status}",
                status="warn",
                severity="warning",
                message=f"{len(agents)} LLM call(s) returned {status}: {', '.join(agents[:5])}",
                evidence={"status": status, "call_count": len(agents), "agents": agents},
            ))

    if not checks:
        checks.append(RunEvaluationCheck(
            name="llm_call_quality",
            status="pass",
            severity="info",
            message="no LLM call quality issues detected",
            evidence={},
        ))

    return checks


def _score(checks: list[RunEvaluationCheck]) -> int:
    score = 100
    for check in checks:
        if check.status == "fail" and check.severity == "blocker":
            score -= 30
        elif check.status == "fail":
            score -= 15
        elif check.status == "warn":
            score -= 5
    return max(0, min(100, score))


def _recommended_action(status: str, checks: list[RunEvaluationCheck]) -> str:
    if status == "block":
        return "fix_blocking_issues_before_next_run"
    if any(c.status == "warn" for c in checks):
        return "review_warnings_before_expanding_budget"
    return "expand_budget_carefully"
