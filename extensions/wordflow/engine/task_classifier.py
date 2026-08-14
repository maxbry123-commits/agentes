# -*- coding: utf-8 -*-
"""TaskClassifier + DecisionGate — T0k. Pre-LLM routing. 0% LLM."""
from __future__ import annotations

import hashlib
import json
import re
import uuid
from typing import Any

DET_PAT = re.compile(
    r"\b(git\s+(status|diff|log|add|commit)|ls\b|cat\s+|sha256|hash|json\s*schema|"
    r"validar\s+schema|compile_input|emit_ping|pytest|unittest)\b",
    re.I,
)
SEARCH_PAT = re.compile(
    r"\b(buscar|search|web_search|grep|find\s+in\s+repo|documentaci[oó]n)\b", re.I
)
PLAN_PAT = re.compile(
    r"\b(planificar|plan\b|desglosar|arquitectura|diseñar|breakdown|objective\s*:)\b", re.I
)
REASON_PAT = re.compile(
    r"\b(por\s+qu[eé]|analiza|razon|explain|diseña|prop[oó]n|comparar|trade-?off)\b", re.I
)
MEMORY_PAT = re.compile(
    r"\b(memoria|memory\s*refresh|recordar|contexto\s+previo|bit[aá]cora)\b", re.I
)
HYBRID_PAT = re.compile(
    r"\b(implementar|codigo|code\s+and\s+design|refactor)\b", re.I
)


def _hash(body: dict[str, Any]) -> str:
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def classify_task(
    text: str,
    *,
    explicit_route: str | None = None,
    form_incomplete: bool = False,
) -> dict[str, Any]:
    reasons: list[str] = []
    signals: dict[str, bool] = {
        "det": bool(DET_PAT.search(text or "")),
        "search": bool(SEARCH_PAT.search(text or "")),
        "plan": bool(PLAN_PAT.search(text or "")) or form_incomplete,
        "reason": bool(REASON_PAT.search(text or "")),
        "memory": bool(MEMORY_PAT.search(text or "")),
        "hybrid": bool(HYBRID_PAT.search(text or "")),
        "form_incomplete": form_incomplete,
    }

    allowed = {
        "DETERMINISTIC",
        "SEARCH",
        "ANALYSIS",
        "REASONING",
        "HYBRID",
        "PLANNING",
        "MEMORY_REFRESH",
    }
    if explicit_route and explicit_route in allowed:
        route = explicit_route
        reasons.append(f"explicit:{explicit_route}")
    elif signals["memory"] and not signals["reason"]:
        route = "MEMORY_REFRESH"
        reasons.append("memory_keywords")
    elif signals["plan"] and form_incomplete:
        route = "PLANNING"
        reasons.append("form_incomplete_planning")
    elif signals["plan"] and signals["reason"]:
        route = "PLANNING"
        reasons.append("plan+reason")
    elif signals["det"] and not (signals["reason"] or signals["plan"] or signals["hybrid"]):
        route = "DETERMINISTIC"
        reasons.append("deterministic_ops")
    elif signals["search"] and not signals["reason"]:
        route = "SEARCH"
        reasons.append("search_ops")
    elif signals["hybrid"]:
        route = "HYBRID"
        reasons.append("implement_code")
    elif signals["reason"]:
        route = "REASONING"
        reasons.append("analysis_keywords")
    elif signals["plan"]:
        route = "PLANNING"
        reasons.append("plan_keywords")
    else:
        route = "ANALYSIS"
        reasons.append("default_analysis")

    use_llm = route not in ("DETERMINISTIC", "SEARCH")
    if route == "SEARCH":
        use_llm = False

    body: dict[str, Any] = {
        "schema_version": "1.0",
        "class_id": f"tc_{uuid.uuid4().hex[:12]}",
        "route": route,
        "use_llm": use_llm,
        "reasons": reasons,
        "signals": signals,
    }
    body["class_hash"] = _hash({k: v for k, v in body.items() if k != "class_hash"})
    return body


def decision_gate(classification: dict[str, Any]) -> dict[str, Any]:
    route = classification.get("route")
    use_llm = bool(classification.get("use_llm"))
    if route == "DETERMINISTIC":
        return {
            "ok": True,
            "call_engine": False,
            "call_llm": False,
            "reason": "DETERMINISTIC_NO_LLM",
            "route": route,
        }
    if route == "SEARCH":
        return {
            "ok": True,
            "call_engine": False,
            "call_llm": False,
            "reason": "SEARCH_INDEX_FIRST",
            "route": route,
        }
    if route == "MEMORY_REFRESH":
        return {
            "ok": True,
            "call_engine": True,
            "call_llm": False,
            "reason": "MEMORY_PORT_ONLY",
            "route": route,
            "engine_hint": "hermes_memory",
        }
    if route == "PLANNING":
        return {
            "ok": True,
            "call_engine": True,
            "call_llm": True,
            "reason": "PLANNING_PORT",
            "route": route,
            "engine_hint": "openclaw+hermes",
        }
    return {
        "ok": True,
        "call_engine": True,
        "call_llm": use_llm,
        "reason": "COGNITIVE_ROUTE",
        "route": route,
    }
