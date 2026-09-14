"""结构化攻击面管理 — 目标/服务/漏洞 注册表。

在渗透测试过程中持续追踪已发现的目标主机、开放服务、技术栈和漏洞。
提供结构化摘要供 LLM Prompt 注入，以及 checkpoint 序列化。
"""

import logging
import re
import time
from dataclasses import dataclass, field, asdict, fields
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)

# M-17 修复：schema 版本契约
# - v1: 初始版本（Finding 含 id/dedup_key，Target 含 status，Service 含 status）
# 升级结构时同步 bump 此版本号，并在 _migrate_schema 中添加迁移逻辑
_SCHEMA_VERSION = 1
_SUPPORTED_VERSIONS = {0, 1}  # 0 = 历史无版本字段，按 v0 处理


@dataclass
class Service:
    """一个开放的网络服务。"""
    port: int
    protocol: str = "tcp"
    service_name: str = ""
    banner: str = ""
    status: str = "open"  # open / closed / filtered


@dataclass
class Target:
    """一个目标主机或域名。"""
    host: str
    host_type: str = "ip"  # ip / domain
    services: Dict[int, Service] = field(default_factory=dict)
    technologies: List[str] = field(default_factory=list)
    notes: str = ""
    status: str = "identified"  # identified / scanning / exploited / done


@dataclass
class Finding:
    """一个已发现的安全漏洞。"""
    id: str = ""
    type: str = ""
    severity: str = "info"
    target: str = ""
    evidence: str = ""
    confidence: str = "possible"  # confirmed / likely / possible
    cvss_base: float = 0.0
    owasp_category: str = ""
    affected_component: str = ""
    timestamp: float = 0.0
    dedup_key: str = ""


# ── 工具输出解析器 ─────────────────────────────────────────────

_PORT_SCAN_RE = re.compile(r"^\s*(\d+)/(tcp|udp)\s+(\S+)\s*(.*)$", re.MULTILINE)
_HTTP_URL_RE = re.compile(r"^URL:\s*(https?://[^\s]+)", re.MULTILINE)
_SERVER_RE = re.compile(r"^Server:\s*(.+)", re.MULTILINE)
_POWERED_BY_RE = re.compile(r"^X-Powered-By:\s*(.+)", re.MULTILINE)
_DNS_IPV4_RE = re.compile(r"IPv4:\s*(\d+\.\d+\.\d+\.\d+)", re.MULTILINE)
_DIR_FIND_RE = re.compile(r"^\s*\d{3}\s+\d+B\s+(https?://[^\s]+)", re.MULTILINE)


def _parse_host_from_tool_args(tool_args: dict) -> Optional[str]:
    """从工具参数中提取目标主机。"""
    for key in ("host", "hostname", "url"):
        val = tool_args.get(key)
        if val:
            if key == "url":
                from urllib.parse import urlparse
                parsed = urlparse(val)
                return parsed.hostname or val
            return val
    return None


def _extract_domain_from_url(url: str) -> Optional[str]:
    """从 URL 提取域名。"""
    from urllib.parse import urlparse
    parsed = urlparse(url)
    return parsed.hostname


# ── 管理器 ─────────────────────────────────────────────────────

class AttackSurface:
    """攻击面管理器 — 集中注册/查询所有目标、服务与漏洞。"""

    def __init__(self):
        self.targets: Dict[str, Target] = {}  # host -> Target
        self.findings: List[Finding] = []
        self._finding_counter: int = 0
        self._covered_labels: Set[str] = set()  # 已覆盖的攻击面标签
        self.credentials_found: List[dict] = []  # [{source, type, value, target}]
        self._last_cred_suggestion_count: int = 0  # 已生成复用建议的凭据数

    # ── 凭据管理 ───────────────────────────────────────────────

    def add_credential(self, source: str, cred_type: str, value: str, target: str = ""):
        """添加发现的凭据。去重。"""
        for c in self.credentials_found:
            if c.get("value") == value:
                return
        self.credentials_found.append({
            "source": source, "type": cred_type, "value": value, "target": target,
        })
        logger.info("发现凭据: %s (%s) @ %s", cred_type, value[:40], target or source)

    def get_credentials_summary(self, include_header: bool = True) -> str:
        """凭据摘要，供 prompt 注入。include_header=False 时不含 Markdown 标题。"""
        if not self.credentials_found:
            return ""
        lines = []
        if include_header:
            lines.append("## 已获取凭据/密钥")
        for c in self.credentials_found:
            v = c['value'][:80]
            lines.append(f"- [{c['type']}] {v} (来源: {c['source']})")
        return "\n".join(lines) + "\n"

    def get_credential_reuse_suggestions(self) -> str:
        """为新发现的凭据生成具体复用建议，供 prompt 注入。

        只对自上次调用以来新增的凭据生成建议，避免重复。
        """
        new_count = len(self.credentials_found) - self._last_cred_suggestion_count
        if new_count <= 0:
            return ""

        new_creds = self.credentials_found[self._last_cred_suggestion_count:]
        self._last_cred_suggestion_count = len(self.credentials_found)

        # 收集所有已知服务端口，用于生成具体复用建议
        ssh_hosts = []   # [(host, port)]
        db_hosts = []    # [(host, port, service)]
        web_hosts = []   # [host]
        rdp_hosts = []
        for host, target in self.targets.items():
            for port, svc in target.services.items():
                sname = (svc.service_name or "").lower()
                banner = (svc.banner or "").lower()
                if port == 22 or "ssh" in sname or "ssh" in banner:
                    ssh_hosts.append((target.host, port))
                if port == 3306 or "mysql" in sname:
                    db_hosts.append((target.host, port, "MySQL"))
                if port == 5432 or "postgresql" in sname or "postgres" in sname:
                    db_hosts.append((target.host, port, "PostgreSQL"))
                if port == 3389 or "rdp" in sname:
                    rdp_hosts.append((target.host, port))
                if port in (80, 443, 8080, 8443) or "http" in sname:
                    web_hosts.append(target.host)

        lines = ["## 新凭据复用建议"]
        for c in new_creds:
            ctype = c.get("type", "")
            value = c.get("value", "")
            target = c.get("target", "")
            display_val = value[:60]
            lines.append(f"发现新凭据 [{ctype}] {display_val} (来源: {c.get('source', '')})")

            suggestions = self._build_reuse_suggestions(
                ctype, value, target, ssh_hosts, db_hosts, web_hosts, rdp_hosts
            )
            if suggestions:
                lines.append("建议立即尝试:")
                for s in suggestions:
                    lines.append(f"  - {s}")
            else:
                lines.append("  (暂无匹配的已知服务，可稍后凭据增多时复用)")
            lines.append("")

        return "\n".join(lines)

    @staticmethod
    def _build_reuse_suggestions(ctype: str, value: str, target: str,
                                  ssh_hosts: list, db_hosts: list,
                                  web_hosts: list, rdp_hosts: list) -> List[str]:
        """根据凭据类型和已知服务生成具体复用建议。"""
        suggestions = []

        # 解析 user:pass 格式的凭据
        username = ""
        password = value
        if ctype == "credential" and ":" in value:
            parts = value.split(":", 1)
            username = parts[0]
            password = parts[1]

        if ctype in ("password", "credential"):
            # SSH
            for host, port in ssh_hosts[:2]:
                user = username or "root"
                suggestions.append(f"SSH 登录 {host}:{port} (用户名: {user}, 密码: {password[:30]})")
            # 数据库
            for host, port, svc in db_hosts[:2]:
                user = username or ("root" if "mysql" in svc.lower() else "postgres")
                suggestions.append(f"{svc} 连接 {host}:{port} (用户名: {user}, 密码: {password[:30]})")
            # HTTP Basic Auth
            for host in web_hosts[:2]:
                proto = "https" if "443" in host else "http"
                user = username or "admin"
                suggestions.append(f"HTTP Basic Auth: {proto}://{host}/admin/ ({user}:{password[:30]})")
            # RDP
            for host, port in rdp_hosts[:1]:
                user = username or "administrator"
                suggestions.append(f"RDP 登录 {host}:{port} (用户名: {user}, 密码: {password[:30]})")

        elif ctype == "private_key":
            for host, port in ssh_hosts[:2]:
                suggestions.append(f"SSH 登录 {host}:{port} (使用私钥认证)")

        elif ctype == "jwt":
            for host in web_hosts[:2]:
                suggestions.append(f"Authorization: Bearer {value[:40]}... → {host}")

        elif ctype == "token":
            for host in web_hosts[:2]:
                suggestions.append(f"API 请求 {host} 时添加 Authorization: Bearer {value[:30]}...")
                suggestions.append(f"或尝试 X-API-Key: {value[:30]}... → {host}")

        elif ctype == "db_connection":
            suggestions.append(f"直接使用连接串访问数据库: {value[:60]}")

        elif ctype == "hash":
            suggestions.append(f"使用 hashcat 或 john 破解 Hash: {value[:40]}...")
            suggestions.append("破解后再尝试复用密码到 SSH/MySQL/HTTP 等服务")

        elif ctype == "secret":
            for host in web_hosts[:2]:
                suggestions.append(f"尝试作为 API 密钥访问 {host} 的管理接口")

        return suggestions

    # ── 目标 &#x6ce8;&#x518c; ──────────────────────────────────

    def get_or_create_target(self, host: str, host_type: str = "ip") -> Target:
        """获取或创建一个目标。"""
        key = host.lower()
        if key not in self.targets:
            self.targets[key] = Target(host=host, host_type=host_type)
        return self.targets[key]

    def add_service(self, host: str, port: int, protocol: str = "tcp",
                    service_name: str = "", banner: str = "",
                    status: str = "open") -> Service:
        """添加或更新一个服务。"""
        target = self.get_or_create_target(host)
        if port not in target.services:
            target.services[port] = Service(
                port=port, protocol=protocol,
                service_name=service_name, banner=banner, status=status,
            )
        else:
            existing = target.services[port]
            if service_name and not existing.service_name:
                existing.service_name = service_name
            if banner and not existing.banner:
                existing.banner = banner
        return target.services[port]

    def add_technology(self, host: str, tech: str):
        """记录目标使用的技术栈。"""
        target = self.get_or_create_target(host)
        if tech not in target.technologies:
            target.technologies.append(tech)

    def set_target_status(self, host: str, status: str):
        """更新目标状态。"""
        target = self.get_or_create_target(host)
        target.status = status

    # ── 漏洞 &#x6ce8;&#x518c; ──────────────────────────────────

    def add_finding(self, finding_type: str, severity: str, target: str,
                    evidence: str = "", confidence: str = "possible",
                    cvss_base: float = 0.0, owasp_category: str = "",
                    affected_component: str = "",
                    idor_elements: Optional[Dict] = None) -> Optional[Finding]:
        """添加一个漏洞发现（自动去重 + 证据分级校验）。

        Args:
            idor_elements: LLM 结构化输出的 IDOR 三要素判定
                {'traversable_id': bool, 'cross_user_chain': bool, 'no_ownership_check': bool}
                仅当 finding_type 为 IDOR/越权/Unauthorized Access 时生效。
        """
        import hashlib

        # ── IDOR 三要素校验（基于 LLM 结构化输出，不再依赖关键词匹配）──
        if "idor" in finding_type.lower() or "越权" in finding_type or "unauthorized" in finding_type.lower():
            validated = self._validate_idor_three_elements(idor_elements, confidence)
            if validated == "reject":
                logger.debug("IDOR 三要素校验未通过，降级为 candidate: %s", affected_component)
                confidence = "possible"
                severity = "info"

        attack_vector = AttackSurface._extract_attack_vector(evidence, finding_type)
        dedup_raw = f"{target}|{affected_component}|{attack_vector}"
        dedup_key = hashlib.md5(dedup_raw.encode()).hexdigest()[:16]

        # 去重检查
        for existing in self.findings:
            if existing.dedup_key == dedup_key:
                logger.debug("跳过重复发现: %s on %s", finding_type, target)
                return None

        self._finding_counter += 1
        finding = Finding(
            id=f"FIND-{self._finding_counter:03d}",
            type=finding_type,
            severity=severity,
            target=target,
            evidence=evidence[:500],
            confidence=confidence,
            cvss_base=cvss_base,
            owasp_category=owasp_category,
            affected_component=affected_component,
            timestamp=time.time(),
            dedup_key=dedup_key,
        )
        self.findings.append(finding)
        logger.info("新发现 [%s] %s — %s (%s)", finding.id, finding_type, target, severity)
        return finding

    @staticmethod
    def _extract_attack_vector(evidence: str, finding_type: str) -> str:
        """从 evidence 提取攻击向量并做标准化去重。

        对 SSRF 类证据做服务端规范化: gopher://127.0.0.1:6379 和
        dict://127.0.0.1:6379 都归一化为 'ssrf:redis'。
        """
        import re
        ev = (evidence or "").lower()
        # 提取 URL 中的 host:port，做服务端归一化
        m = re.search(r'(?:https?|file|gopher|dict)://([^\s/]{3,60})', ev)
        if m:
            hostport = m.group(1)
            proto = m.group(0).split("://")[0]
            # 端口映射: 同一内部服务不同协议 → 归一化
            if ":6379" in hostport or "redis" in hostport:
                return "ssrf:redis"
            if ":80" in hostport or ":443" in hostport or ":8080" in hostport or "iis" in ev or "asp" in ev:
                return "ssrf:internal_http"
            if proto == "file":
                return "ssrf:file_read"
            return f"ssrf:{proto}"
        # 非 SSRF: 用 协议/核心词 标准化
        for proto in ("gopher", "dict", "file", "http", "https"):
            if proto in ev:
                return proto
        core_type = re.sub(r'\s*\(.*', '', finding_type or "").strip()
        return core_type[:40] or "unknown"

    @staticmethod
    def _validate_idor_three_elements(idor_elements: Optional[Dict], confidence: str) -> str:
        """IDOR 三要素判定 — 基于 LLM 结构化输出而非关键词匹配。

        依赖 Analyzer 在分析时输出的 idor_elements 布尔字段进行语义判定，
        消除中英文关键词硬编码带来的措辞遗漏风险。

        Args:
            idor_elements: {'traversable_id': bool, 'cross_user_chain': bool, 'no_ownership_check': bool}
            confidence: 当前置信度

        Returns:
            "pass" — 通过校验，维持原定 confidence
            "reject" — 未通过，应将 confidence 降级为 possible
        """
        if confidence in ("confirmed", "likely"):
            return "pass"
        if not idor_elements or not isinstance(idor_elements, dict):
            return "reject"

        # 三要素满足任一即通过（LLM 已在分析时完成语义判断）
        if (idor_elements.get("traversable_id") or
                idor_elements.get("cross_user_chain") or
                idor_elements.get("no_ownership_check")):
            return "pass"
        return "reject"

    def add_covered_label(self, label: str):
        """标记攻击面已覆盖。"""
        self._covered_labels.add(label)

    # ── 工具输出解析 ─────────────────────────────────────────

    def analyze_step(self, tool_name: str, tool_args: dict, output: str,
                     analysis: dict):
        """分析一步的结果，结构化提取攻击面信息。

        从工具输出文本中解析主机/端口/服务/技术栈，从 analysis 中提取漏洞。
        """
        if not output:
            return

        host_from_args = _parse_host_from_tool_args(tool_args)

        # ── 端口扫描输出解析 ──
        if tool_name == "network_tool" and tool_args.get("action") == "port_scan":
            scan_host = host_from_args or "unknown"
            for match in _PORT_SCAN_RE.finditer(output):
                port = int(match.group(1))
                protocol = match.group(2)
                status = match.group(3)
                banner = match.group(4).strip()
                # 从 banner 推断服务名
                service_name = ""
                if banner:
                    known = {
                        "http": "http", "apache": "http", "nginx": "http",
                        "ssh": "ssh", "openssh": "ssh",
                        "ftp": "ftp", "smtp": "smtp", "mysql": "mysql",
                        "redis": "redis", "mongodb": "mongodb",
                        "postgresql": "postgresql", "dns": "dns",
                    }
                    banner_lower = banner.lower()
                    for keyword, svc in known.items():
                        if keyword in banner_lower:
                            service_name = svc
                            break
                self.add_service(scan_host, port, protocol, service_name, banner, status)

        # ── HTTP 响应解析 ──
        if tool_name == "network_tool" and tool_args.get("action") == "http":
            url = tool_args.get("url", "")
            host_from_url = _extract_domain_from_url(url)
            if host_from_url:
                self.get_or_create_target(host_from_url, "domain")
            # Server 标头 → 技术栈
            server_match = _SERVER_RE.search(output)
            if server_match:
                tech_host = host_from_url or host_from_args or "unknown"
                self.add_technology(tech_host, server_match.group(1))
            # X-Powered-By → 技术栈
            powered_match = _POWERED_BY_RE.search(output)
            if powered_match:
                tech_host = host_from_url or host_from_args or "unknown"
                self.add_technology(tech_host, powered_match.group(1))

        # ── DNS 解析输出 ──
        if tool_name == "network_tool" and tool_args.get("action") == "dns":
            hostname = tool_args.get("hostname", "")
            for ip_match in _DNS_IPV4_RE.finditer(output):
                ip = ip_match.group(1)
                target = self.get_or_create_target(ip, "ip")
                if hostname and hostname not in target.technologies:
                    target.technologies.append(f"resolves:{hostname}")

        # ── 目录爆破输出 ──
        if tool_name == "network_tool" and tool_args.get("action") == "dir_brute":
            base_url = tool_args.get("url", "")
            base_host = _extract_domain_from_url(base_url)
            if base_host:
                self.set_target_status(base_host, "scanned:dirs")

        # ── 从 analysis 提取漏洞 ──
        if analysis.get("vulnerability_found", False):
            vuln = analysis.get("vulnerability", {})
            if vuln and isinstance(vuln, dict):
                vtype = vuln.get("type", "unknown")
                severity = vuln.get("severity", "info")
                target = vuln.get("affected_component", host_from_args or "unknown")
                # 尝试从 tool_args 中补充 affected_component
                affected = vuln.get("affected_component", "")
                if not affected and host_from_args:
                    affected = host_from_args
                self.add_finding(
                    finding_type=vtype,
                    severity=severity,
                    target=target,
                    evidence=vuln.get("evidence", ""),
                    confidence=vuln.get("confidence", "possible"),
                    cvss_base=vuln.get("cvss_base", 0.0),
                    owasp_category=vuln.get("owasp_category", ""),
                    affected_component=affected,
                    idor_elements=vuln.get("idor_elements"),
                )

        # ── 攻击面覆盖标签 ──
        covered = analysis.get("attack_surface_covered", [])
        if isinstance(covered, list):
            for label in covered:
                if isinstance(label, str):
                    self.add_covered_label(label)

    # ── 摘要生成 ──

    def get_summary(self, max_targets: int = 10, max_findings: int = 10) -> str:
        """生成结构化的攻击面摘要供 LLM Prompt 注入。"""
        parts = ["【当前攻击面状态】"]

        # 目标列表
        if self.targets:
            parts.append(f"\n已发现目标 ({len(self.targets)}):")
            for i, (host, target) in enumerate(self.targets.items()):
                if i >= max_targets:
                    parts.append(f"  ... 及其他 {len(self.targets) - max_targets} 个目标")
                    break
                tech_str = f" [{', '.join(target.technologies)}]" if target.technologies else ""
                parts.append(f"  [{target.status}] {host}{tech_str}")
                # 服务
                for port in sorted(target.services.keys()):
                    svc = target.services[port]
                    banner_str = f" — {svc.banner[:60]}" if svc.banner else ""
                    svc_name = f" ({svc.service_name})" if svc.service_name else ""
                    parts.append(f"    {svc.port}/{svc.protocol}  {svc.status}{svc_name}{banner_str}")
        else:
            parts.append("\n  尚未发现目标")

        # 漏洞列表
        if self.findings:
            parts.append(f"\n已发现漏洞 ({len(self.findings)}):")
            for i, f in enumerate(self.findings):
                if i >= max_findings:
                    parts.append(f"  ... 及其他 {len(self.findings) - max_findings} 个")
                    break
                parts.append(f"  [{f.id}] [{f.severity.upper()}] {f.type} — {f.target}")
                if f.evidence:
                    parts.append(f"    证据: {f.evidence[:120]}")
        else:
            parts.append("\n  尚未发现漏洞")

        # 覆盖标签
        if self._covered_labels:
            parts.append(f"\n已覆盖攻击面 ({len(self._covered_labels)}):")
            labels = sorted(self._covered_labels)
            # 按行分组显示
            line = "  "
            for label in labels:
                candidate = f"{line}{label}, "
                if len(candidate) > 120:
                    parts.append(line.rstrip(", "))
                    line = f"  {label}, "
                else:
                    line = candidate
            if line.strip():
                parts.append(line.rstrip(", "))

        return "\n".join(parts)

    def get_findings_summary(self) -> str:
        """获取仅漏洞的摘要（用于报告生成）。"""
        if not self.findings:
            return "无已确认漏洞"
        lines = []
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
        sorted_f = sorted(self.findings, key=lambda f: severity_order.get(f.severity, 99))
        for f in sorted_f:
            lines.append(f"[{f.id}] [{f.severity.upper()}] {f.type} → {f.target}")
            if f.evidence:
                lines.append(f"      证据: {f.evidence[:200]}")
        return "\n".join(lines)

    def get_priority_findings(self, top_n: int = 3) -> str:
        """生成漏洞优先级队列摘要，供 prompt 注入。

        对未确认漏洞 (confidence != confirmed) 按 severity × confidence 评分排序，
        返回 top-N 条"建议优先验证/利用"的漏洞。
        """
        if not self.findings:
            return ""

        severity_weight = {"critical": 4.0, "high": 3.0, "medium": 2.0, "low": 1.0, "info": 0.5}
        confidence_weight = {"confirmed": 0.3, "likely": 1.0, "possible": 0.7}

        scored = []
        for f in self.findings:
            sw = severity_weight.get(f.severity, 0.5)
            cw = confidence_weight.get(f.confidence, 0.7)
            score = sw * cw
            scored.append((score, f))

        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[:top_n]
        if not top:
            return ""

        lines = ["## 建议优先关注 (漏洞优先级队列)"]
        for i, (score, f) in enumerate(top, 1):
            action_hint = "验证漏洞是否真实存在" if f.confidence != "confirmed" else "深入利用此已确认漏洞"
            lines.append(
                f"{i}. [{f.id}] [{f.severity.upper()}] {f.type} — {f.target} "
                f"(confidence: {f.confidence})"
            )
            if f.evidence:
                lines.append(f"   证据: {f.evidence[:100]}")
            lines.append(f"   → 建议: {action_hint}")
        return "\n".join(lines) + "\n"

    # ── 序列化（Checkpoint） ──

    def to_dict(self) -> dict:
        """序列化为可 JSON 序列化的 dict。"""
        return {
            "schema_version": _SCHEMA_VERSION,
            "targets": {
                host: {
                    "host": t.host,
                    "host_type": t.host_type,
                    "technologies": t.technologies,
                    "notes": t.notes,
                    "status": t.status,
                    "services": {
                        str(p): asdict(s) for p, s in t.services.items()
                    },
                }
                for host, t in self.targets.items()
            },
            "findings": [asdict(f) for f in self.findings],
            "finding_counter": self._finding_counter,
            "covered_labels": list(self._covered_labels),
            "credentials_found": self.credentials_found,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AttackSurface":
        """从 dict 恢复（带 schema 版本校验 + 字段容错）。

        M-17 修复：
        - 校验 schema_version：未知版本拒绝恢复（避免 silently 丢字段）
        - 已知版本走迁移函数升级结构
        - 单个 Target/Service/Finding 反序列化失败时跳过而非整体崩溃
        """
        # 版本校验
        version = data.get("schema_version", 0)  # 缺失字段视为 v0
        if version not in _SUPPORTED_VERSIONS:
            raise ValueError(
                f"AttackSurface checkpoint schema_version={version} 不受支持 "
                f"(当前支持 {_SUPPORTED_VERSIONS})，拒绝恢复以避免数据损坏"
            )
        # 迁移（v0 → v1 等）— 当前 v0/v1 结构相同，迁移为 no-op
        data = cls._migrate_schema(data, version)

        as_ = cls()
        as_._finding_counter = data.get("finding_counter", 0)
        as_._covered_labels = set(data.get("covered_labels", []))

        # Target / Service 容错反序列化
        for host, td in data.get("targets", {}).items():
            try:
                target = Target(
                    host=td["host"],
                    host_type=td.get("host_type", "ip"),
                    technologies=td.get("technologies", []),
                    notes=td.get("notes", ""),
                    status=td.get("status", "identified"),
                )
                for port_str, sd in td.get("services", {}).items():
                    try:
                        # 过滤未知字段（防止旧版字段已删除导致 TypeError）
                        # 用 dataclasses.fields 避免无默认值的必填字段导致实例化失败
                        valid_keys = {f.name for f in fields(Service)}
                        filtered_sd = {k: v for k, v in sd.items() if k in valid_keys}
                        target.services[int(port_str)] = Service(**filtered_sd)
                    except (TypeError, ValueError, KeyError) as e:
                        logger.warning("恢复 Service 失败 (port=%s): %s — 跳过", port_str, e)
                as_.targets[host] = target
            except (TypeError, ValueError, KeyError) as e:
                logger.warning("恢复 Target 失败 (host=%s): %s — 跳过", host, e)

        # Finding 容错反序列化
        valid_finding_keys = {f.name for f in fields(Finding)}
        for fd in data.get("findings", []):
            try:
                filtered_fd = {k: v for k, v in fd.items() if k in valid_finding_keys}
                as_.findings.append(Finding(**filtered_fd))
            except (TypeError, ValueError, KeyError) as e:
                logger.warning("恢复 Finding 失败: %s — 跳过", e)

        as_.credentials_found = data.get("credentials_found", [])
        # 恢复时所有已有凭据视为已建议过，避免恢复后重复注入
        as_._last_cred_suggestion_count = len(as_.credentials_found)
        return as_

    @staticmethod
    def _migrate_schema(data: dict, from_version: int) -> dict:
        """已知版本间的结构迁移。

        当前 v0 ↔ v1 结构相同（v0 是无 schema_version 字段的历史 checkpoint）。
        未来字段重命名/删除/新增必填字段时，在此添加迁移步骤：
            if from_version < 2:
                # v1 → v2: 例如 Finding.dedup_key 重命名为 dedup_id
                for f in data.get("findings", []):
                    if "dedup_key" in f and "dedup_id" not in f:
                        f["dedup_id"] = f.pop("dedup_key")
                data["schema_version"] = 2
        """
        return data
