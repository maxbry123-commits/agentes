#!/usr/bin/env python3
"""
AI-Pentest: 基于大模型的自动化渗透测试系统
FastAPI 后端服务
"""
import os
import sys
import json
import asyncio
import subprocess
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.helpers import load_config, validate_target, check_dependencies, ensure_dir
from utils.logger import get_logger
from core.orchestrator import Orchestrator
from core.report_generator import ReportGenerator
from core.result_normalizer import attach_normalized_result, normalize_task_result

# 全局变量
config = None
orchestrator = None
logger = None
active_tasks: Dict[str, Dict] = {}
scan_workers: Dict[str, asyncio.Task] = {}
scan_session_index: Dict[str, str] = {}


def _resolve_results_dir() -> str:
    raw_dir = (
        config.get("system", {}).get("results_dir", "./results")
        if isinstance(config, dict)
        else "./results"
    )
    if os.path.isabs(raw_dir):
        return raw_dir
    return os.path.abspath(os.path.join(os.path.dirname(__file__), raw_dir))


def _safe_load_json(filepath: str) -> Optional[Dict[str, Any]]:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            payload = json.load(f)
        return payload if isinstance(payload, dict) else None
    except Exception as exc:
        if logger:
            logger.warning(f"读取历史报告失败 {filepath}: {exc}")
        return None


def _register_recovered_task(
    task_id: str,
    *,
    result: Optional[Dict[str, Any]] = None,
    target: str = "",
    completed_at: str = "",
    session_id: str = "",
    report_files: Optional[Dict[str, str]] = None,
):
    task = active_tasks.setdefault(
        task_id,
        {
            "id": task_id,
            "status": "completed",
            "progress": 100,
            "current_phase": "completed",
            "current_phase_label": "测试完成",
            "status_detail": "已从历史结果恢复",
        },
    )

    task.update(
        {
            "status": "completed",
            "progress": 100,
            "current_phase": "completed",
            "current_phase_label": "测试完成",
            "status_detail": task.get("status_detail") or "已从历史结果恢复",
        }
    )

    if result and not task.get("result"):
        task["result"] = result
    if target and not task.get("target"):
        task["target"] = target
    if completed_at and not task.get("completed_at"):
        task["completed_at"] = completed_at
    if session_id and not task.get("session_id"):
        task["session_id"] = session_id

    merged_report_files = dict(task.get("report_files") or {})
    merged_report_files.update(report_files or {})
    if merged_report_files:
        task["report_files"] = merged_report_files

    return task


def _recover_task_from_results(task_id: str) -> Optional[Dict[str, Any]]:
    results_dir = _resolve_results_dir()
    if not os.path.isdir(results_dir):
        return None

    suffix = task_id.replace("scan_", "", 1) if task_id.startswith("scan_") else task_id
    session_path = os.path.join(results_dir, f"session_{suffix}.json")
    report_files = {
        fmt: os.path.join(results_dir, f"report_{task_id}.{ext}")
        for fmt, ext in {"json": "json", "html": "html", "markdown": "md"}.items()
        if os.path.exists(os.path.join(results_dir, f"report_{task_id}.{ext}"))
    }

    result = None
    target = ""
    completed_at = ""
    session_id = ""

    if os.path.exists(session_path):
        session_data = _safe_load_json(session_path)
        if session_data:
            result = session_data
            target = session_data.get("target", "")
            completed_at = session_data.get("end_time", "") or session_data.get("completed_at", "")
            session_id = session_data.get("session_id", "")

    if result is None and report_files.get("json"):
        report_data = _safe_load_json(report_files["json"])
        if report_data:
            result = {
                "target": report_data.get("meta", {}).get("target", ""),
                "status": "completed",
                "results": {
                    "report": {
                        "success": True,
                        "data": {
                            "report": report_data,
                        },
                    }
                },
            }
            target = report_data.get("meta", {}).get("target", "")

    if not completed_at:
        timestamp_source = (
            report_files.get("json")
            or next(iter(report_files.values()), None)
            or (session_path if os.path.exists(session_path) else None)
        )
        if timestamp_source and os.path.exists(timestamp_source):
            completed_at = datetime.fromtimestamp(os.path.getmtime(timestamp_source)).isoformat()

    if not report_files and result is None:
        return None

    return _register_recovered_task(
        task_id,
        result=result,
        target=target,
        completed_at=completed_at,
        session_id=session_id,
        report_files=report_files,
    )


def _recover_persisted_reports() -> int:
    results_dir = _resolve_results_dir()
    if not os.path.isdir(results_dir):
        return 0

    recovered = 0
    recovered_task_ids = set()

    for filename in os.listdir(results_dir):
        task_id: Optional[str] = None
        if filename.startswith("session_") and filename.endswith(".json"):
            suffix = filename[len("session_") : -len(".json")]
            task_id = f"scan_{suffix}" if suffix else None
        elif filename.startswith("report_scan_"):
            basename, _ext = os.path.splitext(filename)
            task_id = basename.replace("report_", "", 1)

        if not task_id or task_id in recovered_task_ids:
            continue

        task = _recover_task_from_results(task_id)
        if task:
            recovered_task_ids.add(task_id)
            recovered += 1

    return recovered


def _get_completed_task(task_id: str) -> Optional[Dict[str, Any]]:
    task = active_tasks.get(task_id)
    if task:
        return task
    return _recover_task_from_results(task_id)


def _parse_iso_datetime(value: str) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except Exception:
        return None


def _format_duration_label(seconds: int) -> str:
    if seconds <= 0:
        return "0s"
    if seconds < 60:
        return f"{seconds}s"
    minutes, remaining_seconds = divmod(seconds, 60)
    if minutes < 60:
        return f"{minutes}m {remaining_seconds}s"
    hours, remaining_minutes = divmod(minutes, 60)
    return f"{hours}h {remaining_minutes}m"


def _extract_task_duration_seconds(task: Dict[str, Any], result: Dict[str, Any]) -> int:
    direct_duration = task.get("duration")
    if isinstance(direct_duration, int) and direct_duration >= 0:
        return direct_duration

    start_dt = (
        _parse_iso_datetime(task.get("started_at", ""))
        or _parse_iso_datetime(task.get("created_at", ""))
        or _parse_iso_datetime(result.get("start_time", ""))
    )
    end_dt = (
        _parse_iso_datetime(task.get("completed_at", ""))
        or _parse_iso_datetime(result.get("end_time", ""))
    )
    if start_dt and end_dt:
        return max(0, int((end_dt - start_dt).total_seconds()))
    return 0


def _extract_success_rate(task: Dict[str, Any], result: Dict[str, Any]) -> int:
    normalized = normalize_task_result({"id": task.get("id", ""), **task, "result": result})
    return normalized.get("summary", {}).get("success_rate", 0)


def _is_placeholder_attack_graph(graph: Optional[Dict[str, Any]]) -> bool:
    if not isinstance(graph, dict):
        return True
    steps = ((graph.get("attack_chain") or {}).get("steps")) or []
    exploits = graph.get("vulnerability_exploits") or []
    nodes = ((graph.get("network_topology") or {}).get("nodes")) or []
    if steps or exploits:
        return False
    return len(nodes) <= 1


def _attack_graph_needs_refresh(graph: Optional[Dict[str, Any]]) -> bool:
    if _is_placeholder_attack_graph(graph):
        return True
    if not isinstance(graph, dict):
        return True
    steps = ((graph.get("attack_chain") or {}).get("steps")) or []
    exploit_steps = [step for step in steps if isinstance(step, dict) and step.get("phase") == "exploit"]
    if exploit_steps and not any(step.get("payload") for step in exploit_steps):
        return True
    return False


def _get_all_known_tasks() -> List[Dict[str, Any]]:
    _recover_persisted_reports()
    return list(active_tasks.values())


def _build_activity_data(tasks: List[Dict[str, Any]]) -> Dict[str, List[Any]]:
    daily: Dict[str, Dict[str, int]] = {}
    for task in tasks:
        created_at = (
            task.get("created_at")
            or task.get("started_at")
            or task.get("completed_at")
            or ""
        )
        created_dt = _parse_iso_datetime(created_at)
        if not created_dt:
            continue

        label = created_dt.strftime("%m-%d")
        bucket = daily.setdefault(label, {"scans": 0, "vulns": 0})
        bucket["scans"] += 1

        normalized = normalize_task_result(task)
        bucket["vulns"] += normalized.get("summary", {}).get("vuln_count", 0)

    labels = sorted(daily.keys())[-7:]
    return {
        "labels": labels,
        "scans": [daily[label]["scans"] for label in labels],
        "vulns": [daily[label]["vulns"] for label in labels],
    }


def _phase_label(phase: Optional[str]) -> str:
    labels = {
        "init": "初始化",
        "recon": "信息收集",
        "vuln": "漏洞分析",
        "exploit": "漏洞利用",
        "report": "报告生成",
        "completed": "测试完成",
        "failed": "测试失败",
    }
    if not phase:
        return ""
    return labels.get(phase, phase)


def _bridge_task_event(event: Dict[str, Any]):
    """将会话事件桥接到扫描任务状态，提供工具级可观测性"""
    session_id = event.get("session_id")
    if not session_id:
        return

    task_id = scan_session_index.get(session_id)
    if not task_id or task_id not in active_tasks:
        return

    event_type = event.get("event_type")
    details = event.get("details", {}) or {}
    summary = event.get("summary", "")
    current_task = active_tasks.get(task_id, {})
    update: Dict[str, Any] = {
        "last_event_type": event_type,
        "last_event_at": event.get("timestamp"),
        "last_event_summary": summary,
    }

    phase = details.get("phase") or current_task.get("current_phase")
    if phase:
        update["current_phase"] = phase
        update["current_phase_label"] = _phase_label(phase)

    round_id = event.get("round_id")
    if round_id:
        update["current_round_id"] = round_id

    if event_type == "round_started":
        metadata = details.get("metadata", {}) or {}
        update["status_detail"] = summary or "新一轮协作已开始"
        update["round_index"] = metadata.get("round_index")
    elif event_type == "tool_call_started":
        tool_name = details.get("tool")
        if not tool_name and details.get("tools"):
            tool_name = " / ".join(details.get("tools", []))
        update["current_tool"] = tool_name or "unknown_tool"
        update["tool_status"] = "running"
        update["status_detail"] = summary or f"开始执行工具: {update['current_tool']}"
    elif event_type == "tool_call_completed":
        tool_name = details.get("tool") or current_task.get("current_tool")
        update["current_tool"] = tool_name or ""
        update["tool_status"] = "completed"
        update["status_detail"] = summary or f"工具执行完成: {tool_name}"
    elif event_type == "thinking_started":
        update["analysis_status"] = "running"
        update["status_detail"] = summary or "开始进行分析"
    elif event_type == "thinking_completed":
        update["analysis_status"] = "completed"
        update["status_detail"] = summary or "分析完成"
    elif event_type == "thinking_failed":
        update["analysis_status"] = "failed"
        update["status_detail"] = summary or "分析失败"
    elif event_type == "task_started":
        update["status_detail"] = summary or "阶段任务开始"
    elif event_type == "task_completed":
        update["status_detail"] = summary or "阶段任务完成"
    elif event_type == "task_failed":
        update["status_detail"] = summary or "阶段任务失败"
    elif event_type == "round_completed":
        update["status_detail"] = summary or "当前轮次已完成"
    elif event_type == "decision_finalized":
        update["status_detail"] = summary or "阶段决策已收敛"
    elif event_type == "session_completed":
        update["status_detail"] = summary or "测试会话已完成"
    elif event_type == "session_failed":
        update["status_detail"] = summary or "测试会话失败"

    _update_scan_task(task_id, **update)


def _extract_report_payload(result: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not isinstance(result, dict):
        return None
    results = result.get("results", {})
    if not isinstance(results, dict):
        return None
    report_section = results.get("report", {})
    if not isinstance(report_section, dict):
        return None
    report_data_wrapper = report_section.get("data", {})
    if not isinstance(report_data_wrapper, dict):
        return None
    report_data = report_data_wrapper.get("report")
    return report_data if isinstance(report_data, dict) else None


def _render_report_content(result: Dict[str, Any], format: str) -> Any:
    generator = ReportGenerator(config.get("system", {}))
    embedded_report = _extract_report_payload(result)
    if embedded_report:
        return generator.generate_from_report_data(embedded_report, format)
    return generator.generate(result, format)


def _persist_report_files(task_id: str, result: Dict[str, Any]) -> Dict[str, str]:
    generator = ReportGenerator(config.get("system", {}))
    saved_files: Dict[str, str] = {}
    for fmt in ("json", "html", "markdown"):
        content = _render_report_content(result, fmt)
        filepath = generator.save_report(content, f"report_{task_id}", fmt)
        saved_files[fmt] = filepath
    return saved_files


# Pydantic 模型
class TargetCreate(BaseModel):
    name: str
    ip: str
    description: Optional[str] = ""


class ScanCreate(BaseModel):
    target: str
    scan_type: str = "quick"  # quick, full, vuln, web
    phases: List[str] = ["recon", "vuln", "exploit", "report"]
    depth: str = "normal"  # quick, normal, deep
    timeout: int = 300


class ConfigUpdate(BaseModel):
    llm_provider: Optional[str] = None
    api_keys: Optional[Dict[str, str]] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None


# 应用生命周期
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global config, orchestrator, logger, scan_workers
    
    # 启动时初始化
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    config = load_config(config_path)
    
    logger = get_logger(
        level=config.get("system", {}).get("log_level", "INFO"),
        log_file=config.get("system", {}).get("log_file")
    )
    
    # 初始化模型配置管理器
    results_dir = config.get("system", {}).get("results_dir", "./results")
    model_config_file = os.path.join(results_dir, "model_config.json")
    from core.model_config import get_model_config_manager
    model_config_manager = get_model_config_manager(model_config_file)
    
    # 初始化Orchestrator，传入模型配置管理器
    orchestrator = Orchestrator(config, model_config_manager)
    original_add_event = orchestrator.event_store.add_event

    def bridged_add_event(*args, **kwargs):
        event = original_add_event(*args, **kwargs)
        _bridge_task_event(event)
        return event

    orchestrator.event_store.add_event = bridged_add_event
    
    # 确保结果目录存在
    ensure_dir(results_dir)
    recovered_reports = _recover_persisted_reports()
    if recovered_reports:
        logger.info(f"已恢复 {recovered_reports} 个历史报告任务")
    
    logger.info("AI-Pentest API 服务启动")
    
    yield
    
    # 关闭时清理
    for worker in list(scan_workers.values()):
        worker.cancel()
    logger.info("AI-Pentest API 服务关闭")


# 创建FastAPI应用
app = FastAPI(
    title="AI-Pentest API",
    description="基于大模型的自动化渗透测试系统 API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== 系统状态 API ====================

@app.get("/api/system/status")
async def get_system_status():
    """获取系统状态"""
    deps = check_dependencies()
    
    return {
        "status": "running",
        "version": "1.0.0",
        "llm_provider": config.get("llm", {}).get("provider", "deepseek"),
        "tools": deps,
        "active_tasks": len(active_tasks),
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/system/stats")
async def get_system_stats():
    """获取系统统计"""
    tasks = _get_all_known_tasks()
    running_tasks = [task for task in tasks if task.get("status") == "running"]
    completed_tasks = [task for task in tasks if task.get("status") == "completed"]

    normalized_tasks = [normalize_task_result(task) for task in tasks]
    unique_targets = {item.get("target") for item in normalized_tasks if item.get("target")}

    vulnerabilities = 0
    reports = 0
    session_summaries: List[Dict[str, Any]] = []

    for task in completed_tasks:
        normalized = normalize_task_result(task)
        vulnerabilities += normalized.get("summary", {}).get("vuln_count", 0)
        report_files = task.get("report_files", {}) or {}
        if normalized.get("report", {}).get("ready") or report_files:
            reports += 1

        session_summaries.append({
            "id": task.get("id"),
            "target": normalized.get("target", ""),
            "status": task.get("status", ""),
            "progress": task.get("progress", 0),
            "completed_at": task.get("completed_at", ""),
            "vuln_count": normalized.get("summary", {}).get("vuln_count", 0),
            "flag_count": normalized.get("summary", {}).get("flag_count", 0),
        })

    session_summaries.sort(key=lambda item: item.get("completed_at", ""), reverse=True)

    return {
        "active_targets": len(unique_targets),
        "active_targets_change": 0,
        "scan_tasks": len(tasks),
        "scan_tasks_change": 0,
        "vulnerabilities": vulnerabilities,
        "vulnerabilities_change": 0,
        "reports": reports,
        "reports_change": 0,
        "running_tasks": len(running_tasks),
        "sessions": session_summaries[:10],
        "activity_data": _build_activity_data(tasks),
    }


@app.get("/api/system/tools")
async def get_tools_status():
    """获取工具状态"""
    import shutil
    
    # Kali工具路径映射
    kali_tool_paths = {
        "nmap": "/usr/bin/nmap",
        "masscan": "/usr/bin/masscan",
        "nikto": "/usr/bin/nikto",
        "dirb": "/usr/bin/dirb",
        "whatweb": "/usr/bin/whatweb",
        "sqlmap": "/usr/bin/sqlmap",
        "hydra": "/usr/bin/hydra",
        "medusa": "/usr/bin/medusa",
        "john": "/usr/bin/john",
        "hashcat": "/usr/bin/hashcat",
        "searchsploit": "/usr/bin/searchsploit",
        "msfconsole": "/usr/bin/msfconsole",
        "msfvenom": "/usr/bin/msfvenom",
        "gobuster": "/usr/bin/gobuster",
        "ffuf": "/usr/bin/ffuf",
        "nuclei": "/usr/bin/nuclei",
    }
    
    # 预定义的工具列表（无论是否安装都显示）- 完整Kali工具集
    predefined_tools = [
        # 网络扫描工具
        {"name": "nmap", "category": "network", "description": "网络发现和安全审计工具", "executable": "nmap"},
        {"name": "masscan", "category": "network", "description": "快速互联网端口扫描器", "executable": "masscan"},
        {"name": "netcat", "category": "network", "description": "网络瑞士军刀", "executable": "nc"},
        {"name": "netdiscover", "category": "network", "description": "ARP扫描工具", "executable": "netdiscover"},
        {"name": "arp-scan", "category": "network", "description": "ARP扫描和指纹识别", "executable": "arp-scan"},
        
        # Web扫描工具
        {"name": "nikto", "category": "web", "description": "Web服务器漏洞扫描器", "executable": "nikto"},
        {"name": "dirb", "category": "web", "description": "Web目录扫描器", "executable": "dirb"},
        {"name": "gobuster", "category": "web", "description": "目录/文件/DNS扫描", "executable": "gobuster"},
        {"name": "whatweb", "category": "web", "description": "Web指纹识别工具", "executable": "whatweb"},
        {"name": "sqlmap", "category": "web", "description": "SQL注入自动化工具", "executable": "sqlmap"},
        {"name": "xsstrike", "category": "web", "description": "XSS漏洞扫描器", "executable": "xsstrike"},
        {"name": "dalfox", "category": "web", "description": "XSS漏洞扫描工具", "executable": "dalfox"},
        {"name": "commix", "category": "web", "description": "命令注入漏洞利用工具", "executable": "commix"},
        {"name": "wpscan", "category": "web", "description": "WordPress安全扫描器", "executable": "wpscan"},
        {"name": "ffuf", "category": "web", "description": "快速Web模糊测试工具", "executable": "ffuf"},
        
        # 暴力破解工具
        {"name": "hydra", "category": "brute_force", "description": "快速网络登录破解器", "executable": "hydra"},
        {"name": "medusa", "category": "brute_force", "description": "并行网络登录审计工具", "executable": "medusa"},
        {"name": "john", "category": "brute_force", "description": "密码破解工具", "executable": "john"},
        {"name": "hashcat", "category": "brute_force", "description": "高级密码恢复工具", "executable": "hashcat"},
        {"name": "crunch", "category": "brute_force", "description": "密码字典生成工具", "executable": "crunch"},
        {"name": "cewl", "category": "brute_force", "description": "从网站生成密码字典", "executable": "cewl"},
        
        # 漏洞扫描工具
        {"name": "searchsploit", "category": "vulnerability", "description": "Exploit-DB漏洞搜索工具", "executable": "searchsploit"},
        {"name": "msfconsole", "category": "vulnerability", "description": "Metasploit框架控制台", "executable": "msfconsole"},
        {"name": "msfvenom", "category": "vulnerability", "description": "Metasploit payload生成器", "executable": "msfvenom"},
        {"name": "nuclei", "category": "vulnerability", "description": "基于模板的漏洞扫描器", "executable": "nuclei"},
        {"name": "spiderfoot", "category": "vulnerability", "description": "自动化OSINT工具", "executable": "spiderfoot"},
        
        # 漏洞利用工具
        {"name": "metasploit", "category": "exploit", "description": "渗透测试框架", "executable": "msfconsole"},
        {"name": "empire", "category": "exploit", "description": "Post-exploitation框架", "executable": "empire"},
        
        # 信息收集工具
        {"name": "recon-ng", "category": "recon", "description": "Web reconnaissance框架", "executable": "recon-ng"},
        {"name": "sublist3r", "category": "recon", "description": "子域名枚举工具", "executable": "sublist3r"},
        {"name": "amass", "category": "recon", "description": "子域名枚举和发现", "executable": "amass"},
        {"name": "whois", "category": "recon", "description": "WHOIS查询工具", "executable": "whois"},
        {"name": "dig", "category": "recon", "description": "DNS查询工具", "executable": "dig"},
        
        # 后渗透工具
        {"name": "responder", "category": "post_exploit", "description": "LLMNR/NBT-NS欺骗工具", "executable": "responder"},
        {"name": "crackmapexec", "category": "post_exploit", "description": "Active Directory渗透测试", "executable": "crackmapexec"},
        {"name": "secretsdump", "category": "post_exploit", "description": "Windows凭据转储工具", "executable": "secretsdump"},
        
        # 无线网络工具
        {"name": "aircrack-ng", "category": "wireless", "description": "无线网络安全审计工具", "executable": "aircrack-ng"},
        {"name": "wireshark", "category": "wireless", "description": "网络协议分析器", "executable": "wireshark"},
        
        # 社会工程工具
        {"name": "setoolkit", "category": "social_engineering", "description": "Social-Engineer Toolkit", "executable": "setoolkit"},
        
        # 取证工具
        {"name": "autopsy", "category": "forensics", "description": "数字取证工具", "executable": "autopsy"},
        {"name": "binwalk", "category": "forensics", "description": "二进制分析工具", "executable": "binwalk"},
    ]
    
    # 获取执行历史统计
    usage_stats = {}
    if orchestrator and hasattr(orchestrator.tool_manager, '_execution_history'):
        history = orchestrator.tool_manager._execution_history
        for record in history:
            tool_name = record.tool_name
            if tool_name not in usage_stats:
                usage_stats[tool_name] = 0
            usage_stats[tool_name] += 1
    
    # 计算最大使用次数用于百分比
    max_usage = max(usage_stats.values()) if usage_stats else 1
    
    tools = []
    for tool in predefined_tools:
        # 检查工具是否安装
        installed = shutil.which(tool["executable"]) is not None
        version = ""
        path = ""
        
        if installed:
            # 获取工具路径
            path = shutil.which(tool["executable"]) or ""
            
            # 获取版本信息
            try:
                result = subprocess.run([tool["executable"], "--version"], capture_output=True, text=True, timeout=5)
                version = result.stdout.strip().split('\n')[0][:30] if result.stdout else "installed"
            except:
                version = "installed"
        else:
            # 检查Kali默认路径
            kali_path = kali_tool_paths.get(tool["executable"])
            if kali_path and os.path.exists(kali_path):
                path = kali_path
                installed = True
                version = "installed (Kali)"
        
        count = usage_stats.get(tool["name"], 0)
        tools.append({
            "name": tool["name"],
            "category": tool["category"],
            "description": tool["description"],
            "executable": tool["executable"],
            "installed": installed,
            "path": path,
            "version": version or "N/A",
            "status": "available" if installed else "not_installed",
            "usage_count": count
        })
    
    # 分类统计
    category_stats = {}
    for t in tools:
        cat = t["category"]
        if cat not in category_stats:
            category_stats[cat] = {"total": 0, "installed": 0}
        category_stats[cat]["total"] += 1
        if t["installed"]:
            category_stats[cat]["installed"] += 1
    
    # 使用统计
    usage_list = [
        {"name": t["name"], "count": t["usage_count"], "percentage": int(t["usage_count"] / max_usage * 100) if max_usage > 0 else 0, "color": "#00d4ff"}
        for t in tools if t["usage_count"] > 0
    ]
    usage_list.sort(key=lambda x: x["count"], reverse=True)
    
    return {
        "tools": tools,
        "category_stats": category_stats,
        "usage_stats": usage_list[:5],
        "total_tools": len(tools),
        "installed_tools": len([t for t in tools if t["installed"]])
    }


# ==================== 目标管理 API ====================

@app.get("/api/targets")
async def list_targets():
    """获取目标列表"""
    sessions = orchestrator.list_sessions() if orchestrator else []
    
    targets = []
    seen = set()
    
    for session in sessions:
        target_ip = session.get("target", "")
        if target_ip and target_ip not in seen:
            seen.add(target_ip)
            targets.append({
                "id": session["session_id"],
                "name": target_ip,
                "ip": target_ip,
                "status": session["status"],
                "last_scan": session.get("start_time", "")
            })
    
    return {"targets": targets}


@app.post("/api/targets")
async def create_target(target: TargetCreate):
    """创建新目标"""
    validation = validate_target(target.ip)
    if not validation["valid"]:
        raise HTTPException(status_code=400, detail="无效的目标格式")
    
    return {
        "id": f"target_{int(datetime.now().timestamp())}",
        "name": target.name,
        "ip": target.ip,
        "description": target.description,
        "status": "created"
    }


# ==================== 扫描任务 API ====================

def _update_scan_task(task_id: str, **fields):
    """更新扫描任务状态"""
    if task_id in active_tasks:
        fields["updated_at"] = datetime.now().isoformat()
        active_tasks[task_id].update(fields)


async def run_scan_task(task_id: str, scan_config: ScanCreate):
    """后台执行扫描任务"""
    global active_tasks, scan_workers
    
    try:
        _update_scan_task(
            task_id,
            status="running",
            progress=5,
            current_phase="init",
            current_phase_label="初始化",
            status_detail="任务已创建，等待扫描执行",
            started_at=datetime.now().isoformat()
        )

        def handle_progress(update: Dict[str, Any]) -> None:
            task_update = dict(update)
            session_id = task_update.get("session_id")
            if session_id:
                scan_session_index[session_id] = task_id
            task_update.pop("result", None)
            _update_scan_task(task_id, **task_update)

        # 将阻塞式扫描放到线程中执行，避免卡住 FastAPI 事件循环
        result = await asyncio.to_thread(
            orchestrator.run_test,
            target=scan_config.target,
            mode="auto",
            phases=scan_config.phases,
            progress_callback=handle_progress
        )

        # 如果任务已被标记取消，不覆盖取消状态
        if active_tasks.get(task_id, {}).get("status") == "cancelled":
            _update_scan_task(task_id, completed_at=datetime.now().isoformat())
            return

        report_files: Dict[str, str] = {}
        try:
            if _extract_report_payload(result):
                report_files = _persist_report_files(task_id, result)
        except Exception as save_error:
            logger.warning(f"报告落盘失败 {task_id}: {save_error}")

        _update_scan_task(
            task_id,
            status="completed",
            progress=100,
            current_phase="completed",
            current_phase_label="测试完成",
            status_detail="扫描任务已完成",
            result=result,
            report_files=report_files,
            completed_at=datetime.now().isoformat()
        )

    except asyncio.CancelledError:
        _update_scan_task(
            task_id,
            status="cancelled",
            status_detail="任务已取消",
            completed_at=datetime.now().isoformat()
        )
        raise
    except Exception as e:
        _update_scan_task(
            task_id,
            status="failed",
            status_detail=str(e),
            error=str(e),
            completed_at=datetime.now().isoformat()
        )
    finally:
        scan_workers.pop(task_id, None)


@app.post("/api/scan/start")
async def start_scan(scan: ScanCreate):
    """启动扫描任务"""
    global scan_workers
    validation = validate_target(scan.target)
    if not validation["valid"]:
        raise HTTPException(status_code=400, detail="无效的目标格式")
    
    task_id = f"scan_{int(datetime.now().timestamp())}"
    
    active_tasks[task_id] = {
        "id": task_id,
        "target": scan.target,
        "scan_type": scan.scan_type,
        "status": "pending",
        "progress": 0,
        "created_at": datetime.now().isoformat(),
        "phases": scan.phases,
        "depth": scan.depth,
        "timeout": scan.timeout
    }
    
    # 真正后台执行，避免阻塞 API
    scan_workers[task_id] = asyncio.create_task(
        run_scan_task(task_id, scan),
        name=f"scan-worker-{task_id}"
    )
    
    return {
        "task_id": task_id,
        "status": "started",
        "target": scan.target
    }


@app.get("/api/scan/tasks")
async def list_scan_tasks():
    """获取扫描任务列表"""
    tasks = [attach_normalized_result(task) for task in _get_all_known_tasks()]
    tasks.sort(key=lambda item: item.get("created_at", ""), reverse=True)
    return {"tasks": tasks}


@app.get("/api/scan/task/{task_id}")
async def get_scan_task(task_id: str):
    """获取扫描任务详情"""
    task = active_tasks.get(task_id) or _get_completed_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return attach_normalized_result(task)


@app.delete("/api/scan/task/{task_id}")
async def cancel_scan_task(task_id: str):
    """取消扫描任务"""
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    active_tasks[task_id]["status"] = "cancelled"
    active_tasks[task_id]["completed_at"] = datetime.now().isoformat()

    worker = scan_workers.get(task_id)
    if worker and not worker.done():
        worker.cancel()

    session_id = active_tasks.get(task_id, {}).get("session_id")
    if session_id and scan_session_index.get(session_id) == task_id:
        scan_session_index.pop(session_id, None)

    return {"status": "cancelled", "task_id": task_id}


# ==================== 漏洞管理 API ====================

@app.get("/api/vulnerabilities")
async def list_vulnerabilities(
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None)
):
    """获取漏洞列表"""
    vulnerabilities = []
    
    for task in _get_all_known_tasks():
        if task.get("status") == "completed" and task.get("result"):
            normalized = normalize_task_result(task)
            for vuln in normalized.get("vuln", {}).get("items", []):
                vuln_info = {
                    "id": f"vuln_{len(vulnerabilities)}",
                    "name": vuln.get("name", "Unknown"),
                    "severity": vuln.get("severity", "low"),
                    "cve": vuln.get("cve", ""),
                    "description": vuln.get("description", ""),
                    "target": normalized.get("target", ""),
                    "status": "open",
                    "discovered_at": normalized.get("timestamps", {}).get("completed_at", "")
                }
                
                # 过滤
                if severity and vuln_info["severity"] != severity:
                    continue
                if status and vuln_info["status"] != status:
                    continue
                if search and search.lower() not in vuln_info["name"].lower():
                    continue
                
                vulnerabilities.append(vuln_info)
    
    return {"vulnerabilities": vulnerabilities, "total": len(vulnerabilities)}


@app.get("/api/vulnerabilities/stats")
async def get_vulnerability_stats():
    """获取漏洞统计"""
    stats = {"critical": 0, "high": 0, "medium": 0, "low": 0, "total": 0}
    
    for task in _get_all_known_tasks():
        if task.get("status") == "completed" and task.get("result"):
            counts = normalize_task_result(task).get("vuln", {}).get("severity_counts", {})
            for sev, count in counts.items():
                if sev in stats:
                    stats[sev] += count
                    stats["total"] += count
    
    return stats


# ==================== 报告 API ====================

@app.get("/api/reports")
async def list_reports():
    """获取报告列表"""
    _recover_persisted_reports()
    reports = []
    
    for task_id, task in [(item.get("id"), item) for item in _get_all_known_tasks()]:
        if task.get("status") != "completed":
            continue

        try:
            result = task.get("result", {})
            if not isinstance(result, dict):
                continue
            normalized = normalize_task_result(task)
            report_data = normalized.get("report", {}).get("payload", {})
            report_files = task.get("report_files", {}) or {}
            duration_seconds = _extract_task_duration_seconds(task, result)
            success_rate = normalized.get("summary", {}).get("success_rate", _extract_success_rate(task, result))

            reports.append({
                "id": task_id,
                "task_id": task_id,
                "name": f"渗透测试报告 - {normalized.get('target', 'Unknown')}",
                "target": normalized.get("target", ""),
                "risk_level": normalized.get("report", {}).get("risk_level", "unknown"),
                "vulns": normalized.get("summary", {}).get("vuln_count", 0),
                "flags": normalized.get("summary", {}).get("flag_count", 0),
                "success_rate": success_rate,
                "duration_seconds": duration_seconds,
                "duration": _format_duration_label(duration_seconds),
                "created_at": normalized.get("timestamps", {}).get("completed_at", ""),
                "formats": [fmt for fmt in ("html", "markdown", "json") if fmt in report_files] or ["html", "markdown", "json"],
                "normalized_result": normalized,
            })
        except Exception as exc:
            if logger:
                logger.warning(f"跳过异常历史报告 {task_id}: {exc}")
    
    reports.sort(key=lambda item: item.get("created_at", ""), reverse=True)
    return {"reports": reports}


@app.get("/api/reports/{task_id}")
async def get_report(task_id: str, format: str = Query("json")):
    """获取报告详情"""
    task = _get_completed_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="报告不存在")

    result = task.get("result")
    
    if not result:
        raise HTTPException(status_code=400, detail="任务未完成或无结果")
    
    content = _render_report_content(result, format)
    
    if format == "json":
        return JSONResponse(content=json.loads(content) if isinstance(content, str) else content)
    
    return {"content": content, "format": format}


@app.get("/api/reports/{task_id}/download")
async def download_report(task_id: str, format: str = Query("html")):
    """下载报告文件"""
    if format not in {"json", "html", "markdown"}:
        raise HTTPException(status_code=400, detail="不支持的报告格式")

    task = _get_completed_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="报告不存在")

    result = task.get("result")
    
    if not result:
        raise HTTPException(status_code=400, detail="任务未完成或无结果")
    
    generator = ReportGenerator(config.get("system", {}))
    filename = f"report_{task_id}.{format}"
    report_files = task.get("report_files", {}) or {}
    filepath = report_files.get(format)
    if not filepath or not os.path.exists(filepath):
        content = _render_report_content(result, format)
        filepath = generator.save_report(content, f"report_{task_id}", format)
        report_files[format] = filepath
        task["report_files"] = report_files
    
    return FileResponse(
        filepath,
        filename=filename,
        media_type="application/octet-stream"
    )


# ==================== Agent API ====================

# Agent活动记录存储
agent_activities: List[Dict] = []

def add_agent_activity(agent_name: str, activity_type: str, content: str, details: Dict = None):
    """添加Agent活动记录"""
    activity = {
        "id": f"act_{int(datetime.now().timestamp() * 1000)}",
        "agent": agent_name,
        "type": activity_type,
        "content": content,
        "details": details or {},
        "timestamp": datetime.now().isoformat()
    }

    if orchestrator and hasattr(orchestrator, "interaction_bus"):
        event = orchestrator.interaction_bus.emit_event(
            session_id=(details or {}).get("session_id", "global"),
            event_type=activity_type,
            summary=content,
            agent=agent_name,
            round_id=(details or {}).get("round_id"),
            details=details or {}
        )
        activity["event_id"] = event.get("event_id")

    agent_activities.append(activity)
    if len(agent_activities) > 100:
        agent_activities.pop(0)
    return activity


@app.get("/api/agents/status")
async def get_agents_status():
    """获取Agent状态"""
    if not orchestrator:
        return {"agents": []}
    
    agent_status = orchestrator.get_agent_status() if hasattr(orchestrator, 'get_agent_status') else {}
    
    agents = [
        {"name": "CoordinatorAgent", "display_name": "协同调度", "status": agent_status.get("coordinator", "idle"), "last_active": "-", "color": "#06b6d4"},
        {"name": "ReconAgent", "display_name": "信息收集", "status": agent_status.get("recon", "idle"), "last_active": "-", "color": "#00d4ff"},
        {"name": "VulnAgent", "display_name": "漏洞分析", "status": agent_status.get("vuln", "idle"), "last_active": "-", "color": "#8b5cf6"},
        {"name": "ExploitAgent", "display_name": "漏洞利用", "status": agent_status.get("exploit", "idle"), "last_active": "-", "color": "#f59e0b"},
        {"name": "ReportAgent", "display_name": "报告生成", "status": agent_status.get("report", "idle"), "last_active": "-", "color": "#10b981"},
    ]
    
    return {"agents": agents}


@app.get("/api/agents/activities")
async def get_agent_activities(limit: int = Query(50)):
    """获取Agent活动记录"""
    if orchestrator and hasattr(orchestrator, "get_recent_agent_events"):
        events = orchestrator.get_recent_agent_events(limit=limit)
        activities = []
        for event in events:
            activities.append({
                "id": event.get("event_id"),
                "agent": event.get("agent"),
                "type": event.get("event_type"),
                "content": event.get("summary"),
                "details": event.get("details", {}),
                "timestamp": event.get("timestamp"),
                "session_id": event.get("session_id"),
                "round_id": event.get("round_id"),
            })
        return {"activities": activities}

    return {
        "activities": agent_activities[-limit:][::-1]  # 返回最近的记录，按时间倒序
    }


@app.post("/api/agents/activities")
async def create_agent_activity(activity: Dict):
    """添加Agent活动记录（供Agent调用）"""
    return add_agent_activity(
        activity.get("agent", "Unknown"),
        activity.get("type", "info"),
        activity.get("content", ""),
        activity.get("details")
    )


@app.websocket("/ws/agents")
async def websocket_agent_stream(websocket):
    """WebSocket实时推送Agent活动"""
    await websocket.accept()
    last_event_id = None
    try:
        while True:
            await asyncio.sleep(1)
            if orchestrator and hasattr(orchestrator, "get_latest_event"):
                latest_event = orchestrator.get_latest_event()
                if latest_event and latest_event.get("event_id") != last_event_id:
                    last_event_id = latest_event.get("event_id")
                    await websocket.send_json({
                        "type": "activity",
                        "data": latest_event
                    })
            elif agent_activities:
                await websocket.send_json({
                    "type": "activity",
                    "data": agent_activities[-1]
                })
    except Exception:
        pass


@app.get("/api/sessions")
async def list_interaction_sessions():
    """获取可观测交互会话列表"""
    if not orchestrator or not hasattr(orchestrator, "event_store"):
        return {"sessions": []}
    return {"sessions": orchestrator.event_store.list_sessions()}


@app.get("/api/sessions/{session_id}")
async def get_interaction_session(session_id: str):
    """获取单个会话摘要信息"""
    if not orchestrator or not hasattr(orchestrator, "event_store"):
        raise HTTPException(status_code=404, detail="事件系统未初始化")

    session = orchestrator.event_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    return session


@app.get("/api/sessions/{session_id}/events")
async def get_session_events(session_id: str, limit: int = Query(200)):
    """获取会话事件流"""
    if not orchestrator or not hasattr(orchestrator, "get_session_events"):
        raise HTTPException(status_code=404, detail="事件系统未初始化")

    events = orchestrator.get_session_events(session_id, limit=limit)
    if not events and not orchestrator.event_store.get_session(session_id):
        raise HTTPException(status_code=404, detail="会话不存在")

    return {"session_id": session_id, "events": events}


@app.get("/api/sessions/{session_id}/rounds")
async def get_session_rounds(session_id: str):
    """获取会话中的多轮协作记录"""
    if not orchestrator or not hasattr(orchestrator, "get_session_rounds"):
        raise HTTPException(status_code=404, detail="事件系统未初始化")

    if not orchestrator.event_store.get_session(session_id):
        raise HTTPException(status_code=404, detail="会话不存在")

    return {
        "session_id": session_id,
        "rounds": orchestrator.get_session_rounds(session_id)
    }


@app.get("/api/sessions/{session_id}/rounds/{round_id}/messages")
async def get_round_messages(session_id: str, round_id: str):
    """获取单轮协作中的消息详情"""
    if not orchestrator or not hasattr(orchestrator, "get_round_messages"):
        raise HTTPException(status_code=404, detail="事件系统未初始化")

    if not orchestrator.event_store.get_session(session_id):
        raise HTTPException(status_code=404, detail="会话不存在")

    return {
        "session_id": session_id,
        "round_id": round_id,
        "messages": orchestrator.get_round_messages(session_id, round_id)
    }


@app.get("/api/sessions/{session_id}/timeline")
async def get_session_timeline(session_id: str, limit: int = Query(200)):
    """会话时间线，前端可直接渲染事件流"""
    if not orchestrator or not hasattr(orchestrator, "get_session_events"):
        raise HTTPException(status_code=404, detail="事件系统未初始化")

    return {
        "session_id": session_id,
        "timeline": orchestrator.get_session_events(session_id, limit=limit)
    }


@app.websocket("/ws/sessions/{session_id}/events")
async def websocket_session_event_stream(websocket: WebSocket, session_id: str):
    """按会话推送实时事件"""
    await websocket.accept()
    last_event_id = None
    try:
        while True:
            await asyncio.sleep(1)
            if not orchestrator or not hasattr(orchestrator, "get_latest_event"):
                continue

            latest_event = orchestrator.get_latest_event(session_id=session_id)
            if latest_event and latest_event.get("event_id") != last_event_id:
                last_event_id = latest_event.get("event_id")
                await websocket.send_json({
                    "type": "session_event",
                    "session_id": session_id,
                    "data": latest_event
                })
    except Exception:
        pass


# ==================== 配置 API ====================

@app.get("/api/config")
async def get_config():
    """获取配置"""
    safe_config = config.copy()
    
    # 隐藏敏感信息
    if "llm" in safe_config and "api_keys" in safe_config["llm"]:
        for key in safe_config["llm"]["api_keys"]:
            safe_config["llm"]["api_keys"][key] = "********"
    
    return safe_config


@app.put("/api/config")
async def update_config(config_update: ConfigUpdate):
    """更新配置"""
    global config
    
    if config_update.llm_provider:
        config["llm"]["provider"] = config_update.llm_provider
    
    if config_update.api_keys:
        if "api_keys" not in config["llm"]:
            config["llm"]["api_keys"] = {}
        config["llm"]["api_keys"].update(config_update.api_keys)
    
    if config_update.temperature is not None:
        config["llm"]["request"]["temperature"] = config_update.temperature
    
    if config_update.max_tokens is not None:
        config["llm"]["request"]["max_tokens"] = config_update.max_tokens
    
    # 更新orchestrator（保持模型配置管理器）
    global orchestrator
    orchestrator = Orchestrator(config, get_model_manager())
    
    return {"status": "updated", "config": config}


# ==================== 模型配置 API ====================

from core.model_config import get_model_config_manager, ModelConfig

# 全局模型配置管理器
model_config_manager = None

def get_model_manager():
    """获取模型配置管理器"""
    global model_config_manager
    if model_config_manager is None:
        results_dir = config.get("system", {}).get("results_dir", "./results")
        config_file = os.path.join(results_dir, "model_config.json")
        model_config_manager = get_model_config_manager(config_file)
    return model_config_manager


class AgentModelUpdate(BaseModel):
    provider: str
    model_name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 4096
    timeout: Optional[int] = 120


@app.get("/api/models/providers")
async def get_model_providers():
    """获取支持的模型提供商列表"""
    manager = get_model_manager()
    return {
        "providers": manager.DEFAULT_PROVIDERS,
        "descriptions": {
            "deepseek": "DeepSeek - 深度求索大模型，性价比高，适合渗透测试",
            "glm": "智谱AI GLM-4 - 中文能力强，适合报告生成",
            "qwen": "阿里云通义千问 - 稳定可靠，适合分析任务",
            "openai": "OpenAI GPT - 能力强大，适合复杂推理",
            "custom": "自定义接口 - 支持任何OpenAI兼容接口"
        }
    }


@app.get("/api/models/config")
async def get_models_config():
    """获取所有Agent的模型配置"""
    manager = get_model_manager()
    return manager.get_all_configs()


@app.get("/api/models/agents")
async def get_agent_models():
    """获取所有Agent及其模型配置状态"""
    manager = get_model_manager()
    configs = manager.get_all_configs()
    
    agents = []
    for agent_name, agent_config in configs.get("agents", {}).items():
        model_config = agent_config.get("model_config", {})
        agents.append({
            "name": agent_name,
            "description": agent_config.get("description", ""),
            "enabled": agent_config.get("enabled", True),
            "provider": model_config.get("provider", "deepseek"),
            "model_name": model_config.get("model_name", ""),
            "base_url": model_config.get("base_url", ""),
            "temperature": model_config.get("temperature", 0.7),
            "max_tokens": model_config.get("max_tokens", 4096)
        })
    
    return {"agents": agents}


@app.put("/api/models/agents/{agent_name}")
async def update_agent_model(agent_name: str, update: AgentModelUpdate):
    """更新指定Agent的模型配置"""
    manager = get_model_manager()
    
    model_config = {
        "provider": update.provider,
        "model_name": update.model_name,
        "api_key": update.api_key or "",
        "base_url": update.base_url or "",
        "temperature": update.temperature,
        "max_tokens": update.max_tokens,
        "timeout": update.timeout
    }
    
    success = manager.set_agent_config(agent_name, model_config)
    
    if success:
        return {"status": "success", "message": f"Agent {agent_name} 模型配置已更新"}
    else:
        raise HTTPException(status_code=500, detail="更新配置失败")


@app.post("/api/models/test/{agent_name}")
async def test_agent_model(agent_name: str):
    """测试指定Agent的模型连接"""
    manager = get_model_manager()
    result = manager.test_connection(agent_name)
    
    if result["success"]:
        return {"status": "success", "message": "连接测试成功", "details": result}
    else:
        return {"status": "failed", "error": result.get("error", "未知错误")}


@app.post("/api/models/agents/{agent_name}/toggle")
async def toggle_agent(agent_name: str, enabled: bool = True):
    """启用/禁用指定Agent"""
    manager = get_model_manager()
    success = manager.set_agent_enabled(agent_name, enabled)
    
    if success:
        return {"status": "success", "agent_name": agent_name, "enabled": enabled}
    else:
        raise HTTPException(status_code=404, detail=f"Agent {agent_name} 不存在")


@app.get("/api/team/status")
async def get_team_status():
    """获取团队状态"""
    agents_info = [
        {
            "name": "CoordinatorAgent",
            "display_name": "协调者",
            "role": "团队领导，负责协调和决策",
            "color": "#ef4444",
            "icon": "crown"
        },
        {
            "name": "ReconAgent",
            "display_name": "侦察专家",
            "role": "信息收集和目标侦察",
            "color": "#00d4ff",
            "icon": "search"
        },
        {
            "name": "VulnAgent",
            "display_name": "漏洞分析师",
            "role": "漏洞扫描和风险评估",
            "color": "#8b5cf6",
            "icon": "bug"
        },
        {
            "name": "ExploitAgent",
            "display_name": "攻击专家",
            "role": "漏洞利用和权限获取",
            "color": "#f59e0b",
            "icon": "target"
        },
        {
            "name": "ReportAgent",
            "display_name": "报告专家",
            "role": "生成渗透测试报告",
            "color": "#10b981",
            "icon": "file-text"
        }
    ]
    
    # 获取每个Agent的模型配置
    manager = get_model_manager()
    for agent in agents_info:
        config = manager.get_agent_config(agent["name"].replace("Agent", "").lower())
        if config:
            agent["model_provider"] = config.model_config.provider
            agent["model_name"] = config.model_config.model_name
            agent["enabled"] = config.enabled
    
    return {
        "team_name": "Red Team",
        "description": "渗透测试专家团队",
        "agents": agents_info
    }


# ==================== 活动日志 API ====================

@app.get("/api/activities")
async def get_activities(limit: int = Query(20)):
    """获取活动日志"""
    activities = []
    
    for task_id, task in list(active_tasks.items())[-limit:]:
        activities.append({
            "time": task.get("created_at", ""),
            "type": "info" if task.get("status") != "failed" else "error",
            "message": f"扫描任务 {task.get('status', 'unknown')} - {task.get('target', '')}",
            "agent": "System"
        })
        
        if task.get("started_at"):
            activities.append({
                "time": task.get("started_at", ""),
                "type": "info",
                "message": f"开始扫描 - {task.get('target', '')}",
                "agent": "Recon Agent"
            })
        
        if task.get("completed_at"):
            activities.append({
                "time": task.get("completed_at", ""),
                "type": "success",
                "message": f"扫描完成 - {task.get('target', '')}",
                "agent": "Report Agent"
            })
    
    # 按时间排序
    activities.sort(key=lambda x: x["time"], reverse=True)
    
    return {"activities": activities[:limit]}

# ==================== 攻击图与网络拓扑 API ====================

from core.attack_graph import AttackGraphGenerator, get_attack_graph_generator

# 攻击图存储
attack_graphs: Dict[str, Dict] = {}


@app.get("/api/attack-graph/{task_id}")
async def get_attack_graph(task_id: str):
    """获取指定任务的攻击图"""
    # 尝试从存储中获取
    if task_id in attack_graphs and not _attack_graph_needs_refresh(attack_graphs[task_id]):
        return attack_graphs[task_id]

    # 从任务数据生成攻击图
    task = _get_completed_task(task_id) or active_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    try:
        generator = get_attack_graph_generator()
        result = generator.generate_attack_graph(task_id, task)
        attack_graphs[task_id] = result.to_dict()
        return result.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成攻击图失败: {str(e)}")


@app.post("/api/attack-graph/generate")
async def generate_attack_graph(task_data: Dict):
    """根据提供的任务数据生成攻击图"""
    task_id = task_data.get("task_id", str(uuid.uuid4()))

    try:
        generator = get_attack_graph_generator()
        result = generator.generate_attack_graph(task_id, task_data)
        attack_graphs[task_id] = result.to_dict()
        return result.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成攻击图失败: {str(e)}")


@app.get("/api/attack-graph/topology/{task_id}")
async def get_network_topology(task_id: str):
    """获取网络拓扑"""
    if task_id not in attack_graphs:
        # 尝试生成
        await get_attack_graph(task_id)

    if task_id in attack_graphs:
        return {"topology": attack_graphs[task_id].get("network_topology", {})}
    raise HTTPException(status_code=404, detail="网络拓扑不存在")


@app.get("/api/attack-graph/chain/{task_id}")
async def get_attack_chain(task_id: str):
    """获取攻击链"""
    if task_id not in attack_graphs:
        await get_attack_graph(task_id)

    if task_id in attack_graphs:
        return {"chain": attack_graphs[task_id].get("attack_chain", {})}
    raise HTTPException(status_code=404, detail="攻击链不存在")


@app.get("/api/attack-graph/exploits/{task_id}")
async def get_vulnerability_exploits(task_id: str):
    """获取漏洞利用记录"""
    if task_id not in attack_graphs:
        await get_attack_graph(task_id)

    if task_id in attack_graphs:
        return {"exploits": attack_graphs[task_id].get("vulnerability_exploits", [])}
    raise HTTPException(status_code=404, detail="漏洞利用记录不存在")


@app.get("/api/attack-graph/list")
async def list_attack_graphs():
    """获取所有攻击图列表"""
    graphs = []
    for task_id, graph in attack_graphs.items():
        graphs.append({
            "task_id": task_id,
            "target": graph.get("summary", {}).get("target", "unknown"),
            "generated_at": graph.get("generated_at", ""),
            "success_rate": graph.get("summary", {}).get("attack_success_rate", 0)
        })
    return {"graphs": graphs}


# ==================== 主入口 ====================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
