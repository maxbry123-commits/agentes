"""
信息收集Agent
负责目标信息收集和侦察
"""
from typing import Dict, List, Optional
import json
from .base import BaseAgent, AgentResult, Task, TaskPriority


class ReconAgent(BaseAgent):
    """
    信息收集Agent
    负责对目标进行信息收集，包括：
    - 被动信息收集（DNS、Whois等）
    - 主动信息收集（端口扫描、服务识别）
    - 操作系统指纹识别
    - Web指纹识别
    """

    AGENT_TYPE = "recon"

    SYSTEM_PROMPT = """你是一个专业的安全侦察专家（Reconnaissance Expert），在渗透测试团队中担任信息收集阶段的负责人。

## 你的专业背景
- 10年以上的网络安全侦察经验
- 精通各种开源情报（OSINT）收集技术
- 熟悉网络协议和服务的深度分析
- 能够识别目标系统的潜在攻击面

## 你的核心职责
1. **被动信息收集**：通过公开渠道收集目标信息，不直接接触目标
2. **主动信息收集**：使用扫描工具发现目标的网络结构、开放端口、运行服务
3. **指纹识别**：识别操作系统、Web服务器、应用程序的类型和版本
4. **信息整合**：整理所有收集到的信息，为后续阶段提供情报支持

## 信息收集策略框架

### 第一阶段：目标分析
- 确定目标是网站、服务器、网络设备还是其他系统
- 识别目标的关联资产（域名、IP范围、子公司等）
- 评估目标的防御级别

### 第二阶段：被动侦察（不触发目标告警）
- DNS信息收集：nslookup, dig, whois查询
- 子域名枚举：使用暴力破解或字典猜测
- 邮件信息收集：MX记录、SMTP指纹
- 公开漏洞数据库搜索：搜索目标使用的技术栈的已知漏洞
- GitHub/GitLab代码搜索：查找泄露的敏感信息

### 第三阶段：主动侦察（谨慎使用）
- 端口扫描：nmap端口扫描，识别开放端口
- 服务识别：识别运行的服务及其版本
- 操作系统指纹识别：识别目标操作系统
- Web技术识别：识别Web服务器、CMS、框架等

## 工具使用规范

### 网络扫描工具（nmap）
- 快速扫描：nmap -T4 -F target
- 完整扫描：nmap -sV -sC -O -A target
- UDP扫描：nmap -sU target

### Web信息收集
- 目录扫描：dirb, gobuster, ffuf
- 指纹识别：whatweb, wappalyzer, builtwith
- 参数发现：paramspider, arjun

### DNS枚举
- 子域名：sublist3r, amass, assetfinder
- DNS区域传输：dig axfr
- DNS缓存嗅探：dnsenum

## 输出格式要求

请严格按照以下JSON格式输出：

```json
{
  "recon_summary": "本次侦察的摘要",
  "findings": {
    "passive": {
      "whois": {"registrar": "", "creation_date": "", "nameservers": []},
      "dns": {"a_records": [], "mx_records": [], "txt_records": [], "subdomains": []},
      "emails": [],
      "tech_stack": []
    },
    "active": {
      "open_ports": [{"port": 22, "service": "ssh", "version": "OpenSSH 7.4"}],
      "os": {"family": "Linux", "version": "CentOS 7"},
      "web": {"server": "Apache", "cms": "WordPress", "technologies": []}
    }
  },
  "attack_surface": ["可攻击的服务列表"],
  "next_recommendations": ["下一步建议"]
}
```

## 关键原则
1. 优先进行被动收集，避免触发IPS/IDS
2. 记录所有发现的信息及其来源
3. 识别目标的防御机制（WAF, CDN, IPS等）
4. 为漏洞分析阶段提供准确的目标情报"""


    def __init__(self, llm_client, scanner=None, **kwargs):
        super().__init__(llm_client, **kwargs)
        self.scanner = scanner  # 网络扫描器
        self.recon_results = {}

    def execute(self, task: Task) -> AgentResult:
        """执行信息收集任务"""
        target = task.input_data.get("target")
        target_type = task.input_data.get("target_type", "auto")  # auto, web, network
        scan_depth = task.input_data.get("scan_depth", "normal")  # quick, normal, deep

        if not target:
            return AgentResult(success=False, error="未指定目标")

        self.add_log(f"开始信息收集: {target}")

        # 使用LLM分析目标并制定策略
        strategy = self._analyze_target(target, target_type)
        self.add_log(f"选择的扫描策略: {strategy.get('strategy_name', '标准扫描')}")

        # 执行信息收集
        results = {}

        # 1. 基础信息收集
        if strategy.get("collect_passive", True):
            passive_info = self._collect_passive_info(target)
            results["passive"] = passive_info

        # 2. 端口扫描
        if strategy.get("scan_ports", True):
            port_results = self._scan_ports(target, scan_depth)
            results["ports"] = port_results

        # 3. 服务识别
        if strategy.get("identify_services", True):
            services = self._identify_services(target, results.get("ports", {}))
            results["services"] = services

        # 4. 操作系统识别
        if strategy.get("detect_os", True):
            os_info = self._detect_os(target)
            results["os"] = os_info

        # 5. Web信息收集（如果是Web目标）
        if target_type == "web" or strategy.get("is_web", False):
            web_info = self._collect_web_info(target, scan_depth)
            results["web"] = web_info

        # 使用LLM分析收集到的信息
        analysis = self._analyze_results(results)

        self.recon_results = results

        return AgentResult(
            success=True,
            data={
                "target": target,
                "results": results,
                "analysis": analysis,
                "strategy": strategy
            },
            logs=self.execution_logs
        )

    def _analyze_target(self, target: str, target_type: str) -> Dict:
        """使用LLM分析目标并制定扫描策略"""
        prompt = f"""请分析以下目标，并制定最佳的信息收集策略。

目标: {target}
指定类型: {target_type}

请返回JSON格式的策略：
{{
    "strategy_name": "策略名称",
    "is_web": true/false,
    "collect_passive": true/false,
    "scan_ports": true/false,
    "identify_services": true/false,
    "detect_os": true/false,
    "recommended_ports": ["22", "80", "443", ...],
    "scan_techniques": ["nmap", ...],
    "priority_info": ["需要优先收集的信息"]
}}"""

        try:
            result = self.analyze_with_llm(
                prompt,
                require_json=True,
                json_schema={
                    "strategy_name": {"type": "string"},
                    "is_web": {"type": "boolean"},
                    "collect_passive": {"type": "boolean"},
                    "scan_ports": {"type": "boolean"},
                    "identify_services": {"type": "boolean"},
                    "detect_os": {"type": "boolean"},
                    "recommended_ports": {"type": "array", "items": {"type": "string"}},
                    "scan_techniques": {"type": "array", "items": {"type": "string"}},
                    "priority_info": {"type": "array", "items": {"type": "string"}}
                }
            )
            return result
        except Exception as e:
            self.add_log(f"LLM策略分析失败，使用默认策略: {e}", "WARNING")
            return {
                "strategy_name": "标准扫描",
                "is_web": "http" in target.lower(),
                "collect_passive": True,
                "scan_ports": True,
                "identify_services": True,
                "detect_os": True
            }

    def _collect_passive_info(self, target: str) -> Dict:
        """被动信息收集"""
        self.add_log("执行被动信息收集...")
        passive_data = {
            "dns_records": [],
            "whois_info": None,
            "subdomains": []
        }

        # 如果有扫描器，使用扫描器进行被动收集
        if self.scanner:
            try:
                self.emit_event(
                    event_type="tool_call_started",
                    summary="开始执行被动信息收集",
                    details={"tools": ["dns", "whois"], "target": target}
                )
                # DNS查询
                dns_info = self.scanner.get_dns_info(target)
                passive_data["dns_records"] = dns_info.get("records", [])

                # Whois查询
                whois_info = self.scanner.get_whois_info(target)
                passive_data["whois_info"] = whois_info
                self.emit_event(
                    event_type="tool_call_completed",
                    summary="被动信息收集完成",
                    details={
                        "dns_record_count": len(passive_data["dns_records"]),
                        "has_whois": passive_data["whois_info"] is not None
                    }
                )
            except Exception as e:
                self.add_log(f"被动收集部分失败: {e}", "WARNING")

        return passive_data

    def _scan_ports(self, target: str, depth: str) -> Dict:
        """端口扫描"""
        self.add_log(f"执行端口扫描 (深度: {depth})...")

        port_results = {
            "open_ports": [],
            "closed_ports": [],
            "filtered_ports": []
        }

        if self.scanner:
            try:
                self.emit_event(
                    event_type="tool_call_started",
                    summary="开始执行端口扫描",
                    details={"tool": "scan_ports", "target": target, "depth": depth}
                )
                scan_results = self.scanner.scan_ports(target, depth)
                port_results = scan_results
                self.add_log(f"发现 {len(port_results.get('open_ports', []))} 个开放端口")
                self.emit_event(
                    event_type="tool_call_completed",
                    summary="端口扫描完成",
                    details={
                        "tool": "scan_ports",
                        "open_ports": len(port_results.get("open_ports", []))
                    }
                )
            except Exception as e:
                self.add_log(f"端口扫描失败: {e}", "WARNING")

        return port_results

    def _identify_services(self, target: str, port_results: Dict) -> Dict:
        """服务识别"""
        self.add_log("执行服务识别...")

        services = {}

        # 从端口结果中识别服务
        open_ports = port_results.get("open_ports", [])
        port_service_map = {
            "21": "ftp",
            "22": "ssh",
            "23": "telnet",
            "25": "smtp",
            "53": "dns",
            "80": "http",
            "110": "pop3",
            "143": "imap",
            "443": "https",
            "445": "smb",
            "3306": "mysql",
            "3389": "rdp",
            "5432": "postgresql",
            "8080": "http-proxy",
            "8443": "https-alt"
        }

        for port_info in open_ports:
            port = port_info.get("port")
            service = port_service_map.get(str(port), "unknown")
            services[port] = {
                "name": service,
                "version": port_info.get("version"),
                "banner": port_info.get("banner")
            }

        return services

    def _detect_os(self, target: str) -> Dict:
        """操作系统识别"""
        self.add_log("执行操作系统指纹识别...")

        os_info = {
            "family": "Unknown",
            "version": None,
            "confidence": 0
        }

        if self.scanner:
            try:
                self.emit_event(
                    event_type="tool_call_started",
                    summary="开始执行操作系统识别",
                    details={"tool": "detect_os", "target": target}
                )
                os_result = self.scanner.detect_os(target)
                os_info = os_result
                self.emit_event(
                    event_type="tool_call_completed",
                    summary="操作系统识别完成",
                    details={"tool": "detect_os", "os_family": os_info.get("family", "Unknown")}
                )
            except Exception as e:
                self.add_log(f"OS检测失败: {e}", "WARNING")

        return os_info

    def _collect_web_info(self, target: str, depth: str = "normal") -> Dict:
        """Web信息收集"""
        self.add_log("执行Web信息收集...")

        web_info = {
            "title": None,
            "server": None,
            "technologies": [],
            "interesting_paths": [],
            "cookies": []
        }

        if self.scanner:
            try:
                self.emit_event(
                    event_type="tool_call_started",
                    summary="开始执行Web信息收集",
                    details={"tool": "scan_web", "target": target, "depth": depth}
                )
                is_local_target = "127.0.0.1" in target or "localhost" in target
                scan_type = "quick" if is_local_target or depth != "deep" else "vuln"
                web_result = self.scanner.scan_web(target, scan_type=scan_type)
                web_info = web_result
                self.emit_event(
                    event_type="tool_call_completed",
                    summary="Web信息收集完成",
                    details={
                        "tool": "scan_web",
                        "technology_count": len(web_info.get("technologies", []))
                    }
                )
            except Exception as e:
                self.add_log(f"Web扫描失败: {e}", "WARNING")

        return web_info

    def _analyze_results(self, results: Dict) -> Dict:
        """使用LLM分析收集结果"""
        prompt = f"""请分析以下信息收集结果，提取关键信息并评估目标的安全性。

收集结果:
{json.dumps(results, indent=2, ensure_ascii=False)}

请返回：
1. 关键发现总结
2. 潜在攻击面
3. 建议的下一步行动
4. 风险评估（高/中/低）

请以JSON格式返回。"""

        try:
            analysis = self.analyze_with_llm(
                prompt,
                require_json=True,
                json_schema={
                    "key_findings": {"type": "array", "items": {"type": "string"}},
                    "attack_surface": {"type": "array", "items": {"type": "string"}},
                    "next_steps": {"type": "array", "items": {"type": "string"}},
                    "risk_level": {"type": "string", "enum": ["high", "medium", "low"]}
                }
            )
            return analysis
        except Exception as e:
            self.add_log(f"结果分析失败: {e}", "WARNING")
            return {
                "key_findings": ["信息收集完成"],
                "attack_surface": [],
                "next_steps": ["进行漏洞扫描"],
                "risk_level": "medium"
            }

    def get_capabilities(self) -> List[str]:
        """获取Agent能力"""
        return [
            "被动信息收集",
            "端口扫描",
            "服务识别",
            "操作系统检测",
            "Web指纹识别",
            "DNS枚举",
            "Whois查询"
        ]
