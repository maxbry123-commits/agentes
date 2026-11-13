from __future__ import annotations

from dataclasses import asdict
import re
from typing import Any

from core.agent_base import Agent, AgentContext, AgentResult
from core.state import ResearchState
from schemas.experiment_result import ExperimentResult


_METRIC_PATTERNS = [
    re.compile(r"--\s*(ADE|FDE|minADE|minFDE)\s*\(\d+s\)\s*:\s*([\d.]+)", re.IGNORECASE),
    re.compile(r"(ADE|FDE|minADE|minFDE|MR|miss_rate|collision_rate|diversity)\s*[:=]\s*([\d.]+)", re.IGNORECASE),
    re.compile(r"(Average\s*)?(ADE|FDE)\s*[=:]?\s*([\d.]+)", re.IGNORECASE),
    re.compile(r"([\w_]+)\s*=\s*([\d.]+)"),
]

_STATUS_FAILED_PATTERNS = [
    re.compile(r"(Error|Exception|Traceback|CUDA out of memory|RuntimeError)", re.IGNORECASE),
    re.compile(r"^\s*FAIL", re.MULTILINE),
]

_LOG_TAIL_CHARS = 2000


def _extract_success_metric(text: str, metric_spec: dict) -> float | None:
    pattern = metric_spec.get("pattern")
    if not pattern:
        return None
    try:
        match = re.search(str(pattern), text, re.IGNORECASE)
    except re.error:
        return None
    if not match:
        return None
    try:
        return float(match.group(1))
    except (IndexError, TypeError, ValueError):
        return None


def _check_criteria(metrics: dict[str, float], criteria: dict, text: str = "") -> tuple[bool, list[dict]]:
    targets = criteria.get("metrics", [])
    if not targets:
        return True, []
    results = []
    for t in targets:
        if not isinstance(t, dict):
            continue
        name = str(t.get("name", "")).lower()
        if not name:
            continue
        actual = metrics.get(name)
        if actual is None:
            actual = _extract_success_metric(text, t)
        if actual is None:
            results.append({"metric": name, "pass": False, "reason": "not found"})
            continue
        try:
            target = float(t.get("target", 0))
        except (TypeError, ValueError):
            results.append({"metric": name, "pass": False, "reason": f"bad target: {t.get('target')}"})
            continue
        direction = t.get("direction", "gte")
        ok = actual >= target if direction != "lte" else actual <= target
        results.append({"metric": name, "actual": actual, "target": target, "pass": ok})
    return all(r["pass"] for r in results), results


def parse_experiment_output(
    experiment_id: str,
    stdout: str,
    stderr: str,
    returncode: int,
    command: str,
    expected_metrics: list[str] | None = None,
    duration_seconds: float = 0.0,
    success_criteria: dict | None = None,
) -> ExperimentResult:
    combined = f"{stdout}\n{stderr}"
    result = ExperimentResult(
        experiment_id=experiment_id,
        run_command=command,
        duration_seconds=duration_seconds,
    )

    if returncode != 0:
        result.status = "error"
        result.error_message = _extract_error(combined)
        result.log_tail = combined[-_LOG_TAIL_CHARS:]
        result.notes.append(f"returncode={returncode}")
        return result

    result.smoke_passed = True
    result.eval_passed = True
    result.metrics = _extract_metrics(combined, expected_metrics or [])

    if _has_failure_signal(combined):
        result.status = "failed"
        result.smoke_passed = False
        result.notes.append("failure pattern detected in output")
    elif result.metrics and _has_expected_metrics(result.metrics, expected_metrics or []):
        result.status = "passed"
    elif result.metrics:
        result.status = "unparsed"
        result.notes.append(
            f"metrics found {list(result.metrics.keys())} "
            f"but none match expected {expected_metrics or 'N/A'}; check log_tail"
        )
    else:
        result.status = "unparsed"
        result.notes.append("no metrics found in output; check log_tail")

    result.log_tail = combined[-_LOG_TAIL_CHARS:]

    if success_criteria and isinstance(success_criteria, dict):
        criteria_mode = str(success_criteria.get("mode", ""))
        if criteria_mode in {"metric", "both"}:
            criteria_pass, criteria_results = _check_criteria(
                result.metrics, success_criteria, combined
            )
            result.criteria_results = criteria_results
            if not criteria_pass and result.status == "passed":
                result.status = "failed"
                result.notes.append("criteria not met")

    return result


def _extract_metrics(text: str, expected: list[str]) -> dict[str, float]:
    metrics: dict[str, float] = {}
    for pattern in _METRIC_PATTERNS:
        for match in pattern.finditer(text):
            if len(match.groups()) == 2:
                name, value = match.group(1), match.group(2)
            else:
                name, value = match.group(2), match.group(3)
            name = name.strip()
            key = name.lower()
            if key in metrics:
                continue
            try:
                val = float(value)
            except ValueError:
                continue
            metrics[key] = val
    return metrics


def _has_expected_metrics(metrics: dict[str, float], expected: list[str]) -> bool:
    if not expected:
        return True
    expected_lower = {name.lower() for name in expected}
    return bool(expected_lower.intersection(metrics.keys()))


def _has_failure_signal(text: str) -> bool:
    for pattern in _STATUS_FAILED_PATTERNS:
        if pattern.search(text):
            return True
    return False


def _extract_error(text: str) -> str:
    for pattern in _STATUS_FAILED_PATTERNS:
        m = pattern.search(text)
        if m:
            start = max(0, m.start() - 200)
            return text[start : start + 800]
    return text[-500:]


class ResultParserAgent(Agent):
    name = "result_parser"

    def run(self, state: ResearchState, context: AgentContext) -> AgentResult:
        output = state.values.get("experiment_output", {})
        experiment_id = (
            state.values.get("experiment_plans", [{}])[0].get("experiment_id", "unknown")
            if isinstance(state.values.get("experiment_plans"), list)
            else "unknown"
        )
        result = parse_experiment_output(
            experiment_id=experiment_id,
            stdout=str(output.get("stdout", "")),
            stderr=str(output.get("stderr", "")),
            returncode=int(output.get("returncode", -1)),
            command=str(output.get("command", "")),
            expected_metrics=state.topic.experiment_metrics,
            duration_seconds=float(output.get("duration_seconds", 0.0)),
        )
        context.artifact_store.save_json(state.run_id, "experiment_results", result.result_id, result)
        state.values["experiment_results"] = [asdict(result)]
        return AgentResult(
            notes=[f"experiment parsed: status={result.status}, metrics={list(result.metrics.keys())}"],
            artifacts={"experiment_results": [result.result_id]},
            values={"experiment_results": [asdict(result)]},
        )
