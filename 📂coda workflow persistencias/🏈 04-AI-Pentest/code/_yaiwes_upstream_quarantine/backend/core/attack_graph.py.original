"""
攻击链路与网络拓扑生成模块
自动生成渗透测试的可视化攻击链和网络拓扑图
"""
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import uuid
from urllib.parse import urlparse

from .result_normalizer import normalize_task_result


@dataclass
class NetworkNode:
    """网络节点"""
    id: str
    name: str
    node_type: str  # target, server, database, service, asset
    ip: str
    os: str = ""
    services: List[str] = field(default_factory=list)
    vulnerabilities: List[str] = field(default_factory=list)
    status: str = "unknown"  # compromised, scanned, secured, unknown
    position: Dict = field(default_factory=dict)  # x, y coordinates

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.node_type,
            "ip": self.ip,
            "os": self.os,
            "services": self.services,
            "vulnerabilities": self.vulnerabilities,
            "status": self.status,
            "position": self.position
        }


@dataclass
class NetworkEdge:
    """网络连接"""
    id: str
    source: str
    target: str
    edge_type: str  # network, attack, exploit, pivot
    label: str = ""
    status: str = "active"  # active, blocked, failed

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "source": self.source,
            "target": self.target,
            "type": self.edge_type,
            "label": self.label,
            "status": self.status
        }


@dataclass
class AttackStep:
    """攻击步骤"""
    id: str
    order: int
    phase: str  # recon, vuln, exploit, post-exploit, pivot
    action: str
    target: str
    technique: str  # MITRE ATT&CK technique
    success: bool
    timestamp: str
    details: str = ""
    evidence: List[str] = field(default_factory=list)
    flag: str = ""
    endpoint: str = ""
    method: str = ""
    payload: Any = None

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "order": self.order,
            "phase": self.phase,
            "action": self.action,
            "target": self.target,
            "technique": self.technique,
            "success": self.success,
            "timestamp": self.timestamp,
            "details": self.details,
            "evidence": self.evidence,
            "flag": self.flag,
            "endpoint": self.endpoint,
            "method": self.method,
            "payload": self.payload,
        }


@dataclass
class AttackChain:
    """攻击链"""
    id: str
    name: str
    description: str
    start_time: str
    end_time: str
    steps: List[AttackStep]
    total_duration: int = 0  # seconds
    success_rate: float = 0.0

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "steps": [s.to_dict() for s in self.steps],
            "total_duration": self.total_duration,
            "success_rate": self.success_rate
        }


@dataclass
class VulnerabilityExploit:
    """漏洞利用记录"""
    id: str
    vuln_type: str
    vuln_name: str
    severity: str
    target: str
    exploit_method: str
    success: bool
    impact: str
    poc: str = ""
    timestamp: str = ""

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "vuln_type": self.vuln_type,
            "vuln_name": self.vuln_name,
            "severity": self.severity,
            "target": self.target,
            "exploit_method": self.exploit_method,
            "success": self.success,
            "impact": self.impact,
            "poc": self.poc,
            "timestamp": self.timestamp
        }


@dataclass
class AttackGraphResult:
    """攻击图结果"""
    task_id: str
    network_topology: Dict  # nodes and edges
    attack_chain: AttackChain
    vulnerability_exploits: List[VulnerabilityExploit]
    summary: Dict
    generated_at: str

    def to_dict(self) -> Dict:
        return {
            "task_id": self.task_id,
            "network_topology": self.network_topology,
            "attack_chain": self.attack_chain.to_dict(),
            "vulnerability_exploits": [v.to_dict() for v in self.vulnerability_exploits],
            "summary": self.summary,
            "generated_at": self.generated_at
        }


class AttackGraphGenerator:
    """攻击图生成器"""

    # MITRE ATT&CK 技术映射
    TECHNIQUE_MAP = {
        "port_scan": {"id": "T1595", "name": "Active Scanning"},
        "service_enum": {"id": "T1595.002", "name": "Service Scanning"},
        "vuln_scan": {"id": "T1595.002", "name": "Vulnerability Scanning"},
        "web_scan": {"id": "T1595.002", "name": "Web Application Scanning"},
        "brute_force": {"id": "T1110", "name": "Brute Force"},
        "sql_injection": {"id": "T1190", "name": "Exploit Public-Facing Application"},
        "command_injection": {"id": "T1190", "name": "Exploit Public-Facing Application"},
        "xss": {"id": "T1189", "name": "Drive-by Compromise"},
        "file_upload": {"id": "T1105", "name": "Ingress Tool Transfer"},
        "privilege_escalation": {"id": "T1068", "name": "Exploitation for Privilege Escalation"},
        "lateral_movement": {"id": "T1021", "name": "Remote Services"},
        "credential_dumping": {"id": "T1003", "name": "OS Credential Dumping"},
        "persistence": {"id": "T1053", "name": "Scheduled Task/Job"},
        "data_exfiltration": {"id": "T1041", "name": "Exfiltration Over C2 Channel"},
    }

    # 攻击阶段映射
    PHASE_MAP = {
        "recon": {"name": "信息收集", "order": 1, "color": "#3b82f6"},
        "vuln": {"name": "漏洞发现", "order": 2, "color": "#f59e0b"},
        "exploit": {"name": "漏洞利用", "order": 3, "color": "#ef4444"},
        "post_exploit": {"name": "后渗透", "order": 4, "color": "#8b5cf6"},
        "pivot": {"name": "横向移动", "order": 5, "color": "#ec4899"},
        "report": {"name": "报告生成", "order": 6, "color": "#10b981"},
    }

    def __init__(self):
        pass

    def _safe_dict(self, value: Any) -> Dict[str, Any]:
        return value if isinstance(value, dict) else {}

    def _safe_list(self, value: Any) -> List[Any]:
        return value if isinstance(value, list) else []

    def _parse_duration(self, start_time: str, end_time: str) -> int:
        if not start_time or not end_time:
            return 0
        try:
            return max(0, int((datetime.fromisoformat(end_time) - datetime.fromisoformat(start_time)).total_seconds()))
        except Exception:
            return 0

    def _extract_target_host(self, target: str) -> str:
        if not target:
            return "unknown"
        parsed = urlparse(target if "://" in target else f"http://{target}")
        return parsed.hostname or parsed.path or target

    def _normalize_task_data(self, task_data: Dict) -> Dict[str, Any]:
        normalized_result = normalize_task_result(task_data)
        return {
            "target": normalized_result["target"],
            "target_host": normalized_result["target_host"],
            "scan_type": normalized_result["scan_type"],
            "phases": normalized_result["phases"],
            "start_time": normalized_result["timestamps"]["started_at"] or datetime.now().isoformat(),
            "end_time": normalized_result["timestamps"]["completed_at"] or datetime.now().isoformat(),
            "duration": normalized_result["duration_seconds"],
            "results": self._safe_dict(self._safe_dict(task_data.get("result")).get("results") or task_data.get("results")),
            "recon_data": normalized_result["recon"]["data"],
            "vuln_data": normalized_result["vuln"]["data"],
            "exploit_data": normalized_result["exploit"]["data"],
            "report_data": normalized_result["report"]["payload"],
            "vulnerabilities": normalized_result["vuln"]["items"],
            "attempts": normalized_result["exploit"]["attempts"],
            "successful_attempts": normalized_result["exploit"]["successful_attempts"],
            "flag_payloads": normalized_result["exploit"]["flag_payloads"],
            "validated_flags": normalized_result["report"]["validated_flags"],
            "visited_urls": normalized_result["exploit"]["visited_urls"],
        }

    def generate_network_topology(self, scan_results: Dict) -> Dict:
        """根据扫描结果生成网络拓扑"""
        nodes = []
        edges = []
        node_map = {}
        normalized = self._normalize_task_data(scan_results)

        services = []
        ports_data = self._safe_dict(self._safe_dict(normalized["recon_data"].get("results")).get("ports"))
        open_ports = self._safe_list(ports_data.get("open_ports"))
        for port in open_ports:
            services.append({
                "name": f"Port {port}",
                "host": normalized["target_host"],
                "port": str(port),
                "protocol": "tcp",
            })

        if normalized["target"] != "unknown":
            target_id = "target_0"
            target_node = NetworkNode(
                id=target_id,
                name=normalized["target_host"],
                node_type="target",
                ip=normalized["target_host"],
                os="unknown",
                services=[str(port) for port in open_ports],
                vulnerabilities=[v.get("name", v.get("type", "unknown")) for v in normalized["vulnerabilities"][:10] if isinstance(v, dict)],
                status="compromised" if normalized["flag_payloads"] else "scanned",
                position={"x": 280, "y": 150},
            )
            nodes.append(target_node)
            node_map[normalized["target_host"]] = target_id

        # 处理发现的服务
        for i, service in enumerate(services):
            service_id = f"service_{i}"
            node = NetworkNode(
                id=service_id,
                name=service.get("name", f"Service-{i+1}"),
                node_type="service",
                ip=service.get("host", "unknown"),
                services=[service.get("port", "")],
                status="discovered",
                position={"x": 100 + i * 150, "y": 400}
            )
            nodes.append(node)

            # 创建连接
            host_ip = service.get("host", "")
            if host_ip in node_map:
                edges.append(NetworkEdge(
                    id=f"edge_service_{i}",
                    source=node_map[host_ip],
                    target=service_id,
                    edge_type="network",
                    label=f"{service.get('port', '')}/{service.get('protocol', 'tcp')}"
                ))

        # 添加攻击者节点
        attacker_node = NetworkNode(
            id="attacker",
            name="Attacker",
            node_type="attacker",
            ip="攻击源",
            status="active",
            position={"x": 50, "y": 150}
        )
        nodes.insert(0, attacker_node)

        # 创建攻击者到目标的连接
        for node in nodes[1:]:
            if node.node_type == "target" and node.status == "compromised":
                edges.insert(0, NetworkEdge(
                    id=f"edge_attack_{node.id}",
                    source="attacker",
                    target=node.id,
                    edge_type="attack",
                    label="攻击路径"
                ))

        return {
            "nodes": [n.to_dict() for n in nodes],
            "edges": [e.to_dict() for e in edges]
        }

    def generate_attack_chain(self, task_data: Dict) -> AttackChain:
        """根据任务数据生成攻击链"""
        steps = []
        order = 1
        normalized = self._normalize_task_data(task_data)
        phases = normalized.get("phases", [])
        recon_data = normalized["recon_data"]
        vuln_data = normalized["vuln_data"]
        exploit_data = normalized["exploit_data"]
        vulnerabilities = normalized["vulnerabilities"]
        flag_payloads = normalized["flag_payloads"]
        attempts = normalized["attempts"]

        # 信息收集阶段
        if "recon" in phases or normalized.get("scan_type"):
            recon_results = self._safe_dict(recon_data.get("results"))
            open_ports = self._safe_list(self._safe_dict(recon_results.get("ports")).get("open_ports"))
            technologies = self._safe_list(self._safe_dict(self._safe_dict(recon_results.get("web")).get("technologies")).get("technologies"))
            steps.append(AttackStep(
                id=f"step_{order}",
                order=order,
                phase="recon",
                action="端口扫描与服务识别",
                target=normalized["target"],
                technique="T1595",
                success=True,
                timestamp=normalized["start_time"],
                details=f"识别目标技术栈 {', '.join(technologies[:4]) or '未知'}，开放端口 {len(open_ports)} 个",
                evidence=[f"PORT:{port}" for port in open_ports] + [f"TECH:{tech}" for tech in technologies[:3]]
            ))
            order += 1

        # 漏洞发现阶段
        if "vuln" in phases or vulnerabilities:
            steps.append(AttackStep(
                id=f"step_{order}",
                order=order,
                phase="vuln",
                action="漏洞扫描与分析",
                target=normalized["target"],
                technique="T1595.002",
                success=len(vulnerabilities) > 0,
                timestamp=datetime.now().isoformat(),
                details=f"发现 {len(vulnerabilities)} 个漏洞: {', '.join([v.get('type', 'unknown') for v in vulnerabilities[:3] if isinstance(v, dict)])}",
                evidence=[v.get("name", "") for v in vulnerabilities if isinstance(v, dict)]
            ))
            order += 1

        # 漏洞利用阶段
        if "exploit" in phases or attempts or flag_payloads:
            # 优先展示真实命中的利用 payload，而不是旧的规划步骤
            for payload_item in flag_payloads:
                if not isinstance(payload_item, dict):
                    continue
                steps.append(AttackStep(
                    id=f"step_{order}",
                    order=order,
                    phase="exploit",
                    action=payload_item.get("title", "漏洞利用"),
                    target=normalized["target"],
                    technique=self.TECHNIQUE_MAP.get(self._infer_vuln_type(payload_item), {}).get("id", "T1190"),
                    success=True,
                    timestamp=datetime.now().isoformat(),
                    details=payload_item.get("note", ""),
                    evidence=[
                        payload_item.get("flag", ""),
                        f"{payload_item.get('method', 'GET')} {payload_item.get('endpoint', '')}",
                    ],
                    flag=payload_item.get("flag", ""),
                    endpoint=payload_item.get("endpoint", ""),
                    method=payload_item.get("method", ""),
                    payload=payload_item.get("payload"),
                ))
                order += 1

            if not flag_payloads:
                for attempt in attempts[:5]:
                    attempt = self._safe_dict(attempt)
                    details = self._safe_dict(attempt.get("details"))
                    steps.append(AttackStep(
                        id=f"step_{order}",
                        order=order,
                        phase="exploit",
                        action=attempt.get("step", attempt.get("type", "漏洞利用")),
                        target=normalized["target"],
                        technique=self.TECHNIQUE_MAP.get(attempt.get("type", ""), {}).get("id", "T1190"),
                        success=attempt.get("success", False),
                        timestamp=datetime.now().isoformat(),
                        details=details.get("message", ""),
                        evidence=self._safe_list(details.get("flags"))[:3],
                        payload=details.get("payload"),
                    ))
                    order += 1

        # 后渗透阶段
        if self._safe_dict(exploit_data.get("results")).get("successful"):
            steps.append(AttackStep(
                id=f"step_{order}",
                order=order,
                phase="post_exploit",
                action="高权限会话与敏感能力确认",
                target=normalized["target"],
                technique="T1068",
                success=True,
                timestamp=datetime.now().isoformat(),
                details="真实利用链已打通，目标进入高权限可控状态。",
                evidence=self._safe_list(normalized["validated_flags"])[:5]
            ))
            order += 1

        # 计算成功率
        successful_steps = len([s for s in steps if s.success])
        success_rate = successful_steps / len(steps) if steps else 0

        return AttackChain(
            id=str(uuid.uuid4()),
            name=f"攻击链 - {normalized['target']}",
            description=f"针对目标 {normalized['target']} 的渗透测试攻击链",
            start_time=normalized["start_time"],
            end_time=normalized["end_time"],
            steps=steps,
            total_duration=normalized["duration"],
            success_rate=success_rate
        )

    def generate_vulnerability_exploits(self, task_data: Dict) -> List[VulnerabilityExploit]:
        """生成漏洞利用记录"""
        exploits = []
        normalized = self._normalize_task_data(task_data)
        vulnerabilities = normalized["vulnerabilities"]
        payloads_by_flag = {
            item.get("flag"): item for item in normalized["flag_payloads"] if isinstance(item, dict)
        }
        extracted_flags = set(normalized["validated_flags"])
        for item in normalized["flag_payloads"]:
            if isinstance(item, dict) and item.get("flag"):
                extracted_flags.add(item["flag"])

        for i, vuln in enumerate(vulnerabilities):
            vuln = self._safe_dict(vuln)
            matched_payload = self._match_payload_to_vulnerability(vuln, payloads_by_flag)
            exploit = VulnerabilityExploit(
                id=f"exploit_{i}",
                vuln_type=vuln.get("type", "unknown"),
                vuln_name=vuln.get("name", vuln.get("title", "未知漏洞")),
                severity=vuln.get("severity", "medium"),
                target=vuln.get("target", normalized["target"]),
                exploit_method=matched_payload.get("title") or vuln.get("exploit_method", "自动利用"),
                success=bool(matched_payload),
                impact=matched_payload.get("note") or vuln.get("impact", "存在真实利用风险"),
                poc=json.dumps(matched_payload.get("payload", {}), ensure_ascii=False) if matched_payload else vuln.get("poc", ""),
                timestamp=vuln.get("timestamp", datetime.now().isoformat())
            )
            exploits.append(exploit)

        # 将真实命中的 payload 也补充为攻击记录，避免统计被粗粒度 vuln 结果吞掉
        existing_titles = {item.vuln_name for item in exploits}
        for index, payload_item in enumerate(normalized["flag_payloads"], start=len(exploits)):
            if not isinstance(payload_item, dict):
                continue
            title = payload_item.get("title", "真实利用")
            if title in existing_titles:
                continue
            exploits.append(
                VulnerabilityExploit(
                    id=f"exploit_{index}",
                    vuln_type=self._infer_vuln_type(payload_item),
                    vuln_name=title,
                    severity=self._severity_from_flag(payload_item.get("flag", "")),
                    target=normalized["target"],
                    exploit_method=f"{payload_item.get('method', 'GET')} {payload_item.get('endpoint', '')}",
                    success=True,
                    impact=payload_item.get("note", "已成功完成真实利用"),
                    poc=json.dumps(payload_item.get("payload", {}), ensure_ascii=False),
                    timestamp=datetime.now().isoformat(),
                )
            )

        return exploits

    def generate_summary(self, task_data: Dict, attack_chain: AttackChain,
                        exploits: List[VulnerabilityExploit]) -> Dict:
        """生成摘要"""
        normalized = self._normalize_task_data(task_data)
        # 统计漏洞利用情况
        exploit_stats = {
            "total": len(exploits),
            "successful": len([e for e in exploits if e.success]),
            "failed": len([e for e in exploits if not e.success]),
            "by_severity": {}
        }

        for e in exploits:
            sev = e.severity
            exploit_stats["by_severity"][sev] = exploit_stats["by_severity"].get(sev, 0) + 1

        # 统计攻击阶段
        phase_stats = {}
        for step in attack_chain.steps:
            phase = step.phase
            if phase not in phase_stats:
                phase_stats[phase] = {"total": 0, "success": 0}
            phase_stats[phase]["total"] += 1
            if step.success:
                phase_stats[phase]["success"] += 1

        return {
            "target": normalized.get("target", "unknown"),
            "scan_type": normalized.get("scan_type", "unknown"),
            "total_duration": attack_chain.total_duration,
            "attack_success_rate": attack_chain.success_rate,
            "exploit_stats": exploit_stats,
            "phase_stats": phase_stats,
            "compromised_assets": 1 if any(e.success for e in exploits) else 0,
            "recommendations": self._generate_recommendations(exploits)
        }

    def _generate_recommendations(self, exploits: List[VulnerabilityExploit]) -> List[str]:
        """生成修复建议"""
        recommendations = []

        # 根据漏洞类型生成建议
        vuln_types = set([e.vuln_type for e in exploits if e.success])

        if "sql_injection" in vuln_types:
            recommendations.append("实施参数化查询，防止SQL注入")
        if "xss" in vuln_types:
            recommendations.append("对所有用户输入进行HTML转义")
        if "command_injection" in vuln_types:
            recommendations.append("避免直接执行用户输入，使用白名单验证")
        if "file_upload" in vuln_types:
            recommendations.append("限制文件上传类型，实施内容检测")
        if "brute_force" in vuln_types:
            recommendations.append("实施账户锁定策略和多因素认证")

        if not recommendations:
            recommendations.append("继续保持安全编码实践")

        return recommendations

    def _infer_vuln_type(self, payload_item: Dict[str, Any]) -> str:
        endpoint = str(payload_item.get("endpoint", ""))
        title = str(payload_item.get("title", "")).lower()
        flag = str(payload_item.get("flag", "")).lower()

        if "sql" in title or "sqli" in flag:
            return "sql_injection"
        if "xss" in title or "xss" in flag:
            return "xss"
        if "ping" in endpoint or "command" in flag:
            return "command_injection"
        if "upload" in endpoint:
            return "file_upload"
        if "xml" in endpoint:
            return "xxe"
        if "fetch" in endpoint or "ssrf" in flag:
            return "ssrf"
        if "deserialize" in title or "api/data" in endpoint:
            return "deserialization"
        return "web_exploit"

    def _severity_from_flag(self, flag: str) -> str:
        critical_markers = ["full_chain", "ops_ssti", "workflow", "plugin_hotfix", "report_replay"]
        high_markers = ["command_injection", "path_traversal", "unsafe_deserialization", "xxe", "ssrf", "signed_export"]
        if any(marker in flag for marker in critical_markers):
            return "critical"
        if any(marker in flag for marker in high_markers):
            return "high"
        if "sqli" in flag or "upload" in flag or "xss" in flag:
            return "medium"
        return "low"

    def _match_payload_to_vulnerability(self, vuln: Dict[str, Any], payloads_by_flag: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        name = f"{vuln.get('name', '')} {vuln.get('type', '')}".lower()
        for flag, payload in payloads_by_flag.items():
            flag_text = str(flag).lower()
            title = str(payload.get("title", "")).lower()
            endpoint = str(payload.get("endpoint", "")).lower()
            if (
                ("配置" in name and "debug_information_leak" in flag_text)
                or ("信息泄露" in name and ("debug" in endpoint or "debug_information_leak" in flag_text))
                or ("csp" in name and "stored_xss_payload" in flag_text)
                or ("安全头" in name and ("stored_xss_payload" in flag_text or "sqli_query_breakout" in flag_text))
                or ("sql" in name and "sqli_query_breakout" in flag_text)
                or ("xss" in name and "stored_xss_payload" in flag_text)
                or title in name
            ):
                return payload
        return {}

    def generate_attack_graph(self, task_id: str, task_data: Dict) -> AttackGraphResult:
        """生成完整的攻击图"""
        normalized = self._normalize_task_data(task_data)

        # 生成网络拓扑
        network_topology = self.generate_network_topology(task_data)

        # 生成攻击链
        attack_chain = self.generate_attack_chain(task_data)

        # 生成漏洞利用记录
        exploits = self.generate_vulnerability_exploits(task_data)

        # 生成摘要
        summary = self.generate_summary(normalized, attack_chain, exploits)

        return AttackGraphResult(
            task_id=task_id,
            network_topology=network_topology,
            attack_chain=attack_chain,
            vulnerability_exploits=exploits,
            summary=summary,
            generated_at=datetime.now().isoformat()
        )


# 全局生成器实例
_generator: Optional[AttackGraphGenerator] = None


def get_attack_graph_generator() -> AttackGraphGenerator:
    """获取攻击图生成器实例"""
    global _generator
    if _generator is None:
        _generator = AttackGraphGenerator()
    return _generator
