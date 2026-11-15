from __future__ import annotations

import copy
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse


def _safe_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _safe_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def _safe_str(value: Any) -> str:
    return value if isinstance(value, str) else ""


def _parse_json_object(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}
    return {}


def _parse_iso_datetime(value: str) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except Exception:
        return None


def _parse_duration_seconds(task: Dict[str, Any], result: Dict[str, Any]) -> int:
    direct_duration = task.get("duration")
    if isinstance(direct_duration, int) and direct_duration >= 0:
        return direct_duration

    start_time = (
        _safe_str(task.get("started_at"))
        or _safe_str(task.get("created_at"))
        or _safe_str(result.get("start_time"))
    )
    end_time = _safe_str(task.get("completed_at")) or _safe_str(result.get("end_time"))

    start_dt = _parse_iso_datetime(start_time)
    end_dt = _parse_iso_datetime(end_time)
    if start_dt and end_dt:
        return max(0, int((end_dt - start_dt).total_seconds()))
    return 0


def _format_duration_label(seconds: int) -> str:
    if seconds <= 0:
        return "0s"
    if seconds < 60:
        return f"{seconds}s"
    minutes, remain = divmod(seconds, 60)
    if minutes < 60:
        return f"{minutes}m {remain}s"
    hours, remain_minutes = divmod(minutes, 60)
    return f"{hours}h {remain_minutes}m"


def _extract_report_payload(result: Dict[str, Any]) -> Dict[str, Any]:
    report_section = _safe_dict(_safe_dict(result.get("results")).get("report"))
    report_data = _safe_dict(report_section.get("data"))
    return _safe_dict(report_data.get("report"))


def _extract_target_host(target: str) -> str:
    if not target:
        return "unknown"
    parsed = urlparse(target if "://" in target else f"http://{target}")
    return parsed.hostname or parsed.path or target


def _dedupe_strings(values: List[Any]) -> List[str]:
    seen = set()
    result: List[str] = []
    for item in values:
        if not isinstance(item, str):
            continue
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def _dedupe_flag_payloads(values: List[Any]) -> List[Dict[str, Any]]:
    seen = set()
    records: List[Dict[str, Any]] = []
    for item in values:
        if not isinstance(item, dict):
            continue
        flag = _safe_str(item.get("flag"))
        title = _safe_str(item.get("title"))
        endpoint = _safe_str(item.get("endpoint"))
        method = _safe_str(item.get("method")) or "GET"
        identity = (flag, title, endpoint, method)
        if identity in seen:
            continue
        seen.add(identity)
        records.append(
            {
                "flag": flag,
                "title": title or "真实利用记录",
                "endpoint": endpoint,
                "method": method,
                "payload": item.get("payload"),
                "note": _safe_str(item.get("note")),
                "related_artifacts": _safe_dict(item.get("related_artifacts")),
            }
        )
    return records


def _normalize_exploit_results(exploit_results: Dict[str, Any], report_payload: Dict[str, Any]) -> Dict[str, Any]:
    attempts = _safe_list(exploit_results.get("attempts"))
    successful_attempts = _safe_list(exploit_results.get("successful"))
    raw_flags = _safe_list(exploit_results.get("flags"))

    flag_payloads: List[Any] = []
    visited_urls: List[Any] = []
    auth_method = ""
    access_level = ""
    credential: Dict[str, Any] = {}

    for source in attempts + successful_attempts:
        if not isinstance(source, dict):
            continue
        details = _safe_dict(source.get("details"))
        flag_payloads.extend(_safe_list(details.get("flag_payloads")))
        visited_urls.extend(_safe_list(details.get("visited_urls")))
        if not auth_method:
            auth_method = _safe_str(details.get("auth_method"))
        if not access_level:
            access_level = _safe_str(details.get("access_level"))
        if not credential:
            credential = _safe_dict(details.get("credential"))

    appendix = _safe_dict(report_payload.get("appendix"))
    validated_flags = _safe_list(appendix.get("validated_flags"))
    normalized_flag_payloads = _dedupe_flag_payloads(flag_payloads)
    payload_flags = [item.get("flag") for item in normalized_flag_payloads]
    flags = _dedupe_strings(raw_flags + validated_flags + payload_flags)

    return {
        "attempts": attempts,
        "successful_attempts": successful_attempts,
        "flags": flags,
        "flag_payloads": normalized_flag_payloads,
        "visited_urls": _dedupe_strings(visited_urls),
        "auth_method": auth_method,
        "access_level": access_level,
        "credential": credential,
    }


def _severity_counts(vulnerabilities: List[Dict[str, Any]]) -> Dict[str, int]:
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for item in vulnerabilities:
        severity = _safe_str(item.get("severity")).lower()
        if severity in counts:
            counts[severity] += 1
    return counts


def _extract_risk_level(vuln_data: Dict[str, Any], report_payload: Dict[str, Any], flags: List[str]) -> str:
    report_risk = _safe_str(_safe_dict(report_payload.get("risk_assessment")).get("overall_risk"))
    if report_risk:
        return report_risk

    summary_risk = _safe_str(_safe_dict(report_payload.get("executive_summary")).get("risk_level"))
    if summary_risk:
        return summary_risk

    vuln_risk = _safe_str(_safe_dict(vuln_data.get("risk_assessment")).get("risk_level"))
    if vuln_risk:
        return vuln_risk

    counts = _severity_counts(_safe_list(vuln_data.get("vulnerabilities")))
    if counts["critical"] or len(flags) >= 3:
        return "critical"
    if counts["high"] or flags:
        return "high"
    if counts["medium"]:
        return "medium"
    return "low"


def _extract_technologies(recon_data: Dict[str, Any]) -> List[str]:
    results = _safe_dict(recon_data.get("results"))
    web = _safe_dict(results.get("web"))
    technologies = _safe_dict(web.get("technologies"))
    return _dedupe_strings(_safe_list(technologies.get("technologies")))


def _extract_open_ports(recon_data: Dict[str, Any]) -> List[int]:
    results = _safe_dict(recon_data.get("results"))
    ports = _safe_dict(results.get("ports"))
    return [port for port in _safe_list(ports.get("open_ports")) if isinstance(port, int)]


def normalize_task_result(task: Dict[str, Any]) -> Dict[str, Any]:
    task_dict = _safe_dict(task)
    result = _safe_dict(task_dict.get("result"))
    if not result and _safe_dict(task_dict.get("results")):
        result = copy.deepcopy(task_dict)

    results = _safe_dict(result.get("results"))
    recon_data = _safe_dict(_safe_dict(results.get("recon")).get("data"))
    vuln_data = _safe_dict(_safe_dict(results.get("vuln")).get("data"))
    exploit_data = _safe_dict(_safe_dict(results.get("exploit")).get("data"))
    exploit_results = _safe_dict(exploit_data.get("results"))
    report_payload = _extract_report_payload(result)

    target = (
        _safe_str(task_dict.get("target"))
        or _safe_str(result.get("target"))
        or _safe_str(recon_data.get("target"))
        or _safe_str(vuln_data.get("target"))
        or _safe_str(exploit_data.get("target"))
        or _safe_str(_safe_dict(report_payload.get("meta")).get("target"))
        or "unknown"
    )
    session_id = (
        _safe_str(task_dict.get("session_id"))
        or _safe_str(result.get("session_id"))
        or _safe_str(task_dict.get("id")).replace("scan_", "session_", 1)
    )

    vulnerabilities = [item for item in _safe_list(vuln_data.get("vulnerabilities")) if isinstance(item, dict)]
    exploit = _normalize_exploit_results(exploit_results, report_payload)
    severity_counts = _severity_counts(vulnerabilities)
    duration_seconds = _parse_duration_seconds(task_dict, result)
    risk_level = _extract_risk_level(vuln_data, report_payload, exploit["flags"])

    attempts = exploit["attempts"]
    successful_attempts = exploit["successful_attempts"]
    success_rate = 0
    if attempts:
        success_rate = round((len(successful_attempts) / len(attempts)) * 100)
    elif exploit["flags"]:
        success_rate = 100

    return {
        "task_id": _safe_str(task_dict.get("id")),
        "session_id": session_id,
        "status": _safe_str(task_dict.get("status")),
        "target": target,
        "target_host": _extract_target_host(target),
        "scan_type": _safe_str(task_dict.get("scan_type")) or _safe_str(result.get("mode")) or "auto",
        "phases": [phase for phase in _safe_list(task_dict.get("phases") or list(results.keys())) if isinstance(phase, str)],
        "timestamps": {
            "created_at": _safe_str(task_dict.get("created_at")),
            "started_at": _safe_str(task_dict.get("started_at")) or _safe_str(result.get("start_time")),
            "completed_at": _safe_str(task_dict.get("completed_at")) or _safe_str(result.get("end_time")),
        },
        "duration_seconds": duration_seconds,
        "duration": _format_duration_label(duration_seconds),
        "recon": {
            "open_ports": _extract_open_ports(recon_data),
            "technologies": _extract_technologies(recon_data),
            "data": recon_data,
        },
        "vuln": {
            "items": vulnerabilities,
            "count": len(vulnerabilities),
            "severity_counts": severity_counts,
            "risk_level": risk_level,
            "data": vuln_data,
        },
        "exploit": {
            "attempts": attempts,
            "successful_attempts": successful_attempts,
            "flags": exploit["flags"],
            "flag_payloads": exploit["flag_payloads"],
            "visited_urls": exploit["visited_urls"],
            "auth_method": exploit["auth_method"],
            "access_level": exploit["access_level"],
            "credential": exploit["credential"],
            "flag_count": len(exploit["flags"]),
            "payload_count": len(exploit["flag_payloads"]),
            "success_rate": success_rate,
            "data": exploit_data,
        },
        "report": {
            "ready": bool(report_payload),
            "payload": report_payload,
            "risk_level": risk_level,
            "validated_flags": exploit["flags"],
        },
        "summary": {
            "vuln_count": len(vulnerabilities),
            "flag_count": len(exploit["flags"]),
            "payload_count": len(exploit["flag_payloads"]),
            "report_ready": bool(report_payload),
            "success_rate": success_rate,
            "risk_level": risk_level,
        },
        "raw": {
            "results": results,
        },
    }


def attach_normalized_result(task: Dict[str, Any]) -> Dict[str, Any]:
    normalized = normalize_task_result(task)
    enriched = dict(task)
    enriched["session_id"] = enriched.get("session_id") or normalized["session_id"]
    enriched["target"] = enriched.get("target") or normalized["target"]
    enriched["normalized_result"] = normalized
    return enriched

