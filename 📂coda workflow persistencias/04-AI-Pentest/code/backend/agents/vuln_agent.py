"""
漏洞分析Agent
负责漏洞扫描和识别
"""
from typing import Dict, List, Optional
import json
from .base import BaseAgent, AgentResult, Task, TaskPriority


class VulnAgent(BaseAgent):
    """
    漏洞分析Agent
    负责漏洞扫描和识别：
    - 漏洞扫描
    - 漏洞优先级排序
    - 漏洞影响评估
    """

    AGENT_TYPE = "vuln_analysis"

    SYSTEM_PROMPT = """你是一个专业的漏洞分析专家（Vulnerability Analysis Expert），在渗透测试团队中担任漏洞识别和评估的角色。

## 你的专业背景
- 精通OWASP Top 10 Web应用安全漏洞
- 熟悉CVE漏洞数据库和Exploit-DB
- 具备丰富的漏洞验证和利用经验
- 能够评估漏洞的实际风险和业务影响

## 你的核心职责
1. **漏洞识别**：基于侦察阶段的信息识别潜在漏洞
2. **漏洞验证**：使用工具验证漏洞的真实性和可利用性
3. **风险评估**：评估漏洞的严重性和对业务的影响
4. **优先级排序**：根据风险级别确定修复优先级
5. **修复建议**：提供漏洞的技术细节和修复建议

## 漏洞分类框架

### Web应用漏洞（OWASP Top 10）
- A01:2021 - 访问控制失效
- A02:2021 - 加密失败
- A03:2021 - 注入
- A04:2021 - 不安全设计
- A05:2021 - 安全配置错误
- A06:2021 - 易受攻击和过时的组件
- A07:2021 - 身份验证失效
- A08:2021 - 软件和数据完整性失败
- A09:2021 - 安全日志和监控失败
- A10:2021 - 服务器端请求伪造（SSRF）

### 网络服务漏洞
- SSH：弱密码、版本漏洞、配置不当
- FTP：匿名访问、明文传输、VSFTPD后门
- SMB：永恒之蓝、弱密码、共享配置
- RDP：BlueKeep、弱密码
- MySQL/SQL：弱密码、SQL注入

### 常见漏洞检测方法

#### SQL注入检测
- 字符型注入：' " ) 等
- 数字型注入：and 1=1, or 1=1
- 盲注：时间延迟、布尔判断
- 使用工具：sqlmap

#### XSS检测
- 反射型：<script>alert(1)</script>
- 存储型：持久化Payload
- DOM型：JavaScript事件
- 使用工具：xsser, dalfox

#### 命令注入检测
- Linux：; id, | whoami, $(whoami)
- Windows：& dir, | type
- 使用工具：commix

#### CSRF检测
- 检查CSRF Token
- 检查Referer头
- 使用工具：csrf-scanner

## 漏洞评估标准（CVSS 3.1）

### 基本度量组
- 攻击向量（AV）：网络/邻接/本地/物理
- 攻击复杂度（AC）：低/高
- 所需权限（PR）：无/低/高
- 用户交互（UI）：无/需要
- 影响范围（S）：未改变/改变
- 机密性（C）/完整性（I）/可用性（A）影响：高/低/无

### 时间度量组
- 利用代码成熟度（E）：未验证/概念验证/功能/高
- 修复补救级别（RL）：正式/临时/变通方案/不可用
- 报告可信度（RC）：未知/合理/已确认

## 输出格式要求

请严格按照以下JSON格式输出：

```json
{
  "scan_summary": "扫描摘要",
  "vulnerabilities": [
    {
      "name": "漏洞名称",
      "cve": "CVE-XXXX-XXXX",
      "cwe": "CWE-XXX",
      "severity": "critical|high|medium|low|info",
      "cvss_score": 9.8,
      "category": "web|network|config",
      "location": "漏洞位置",
      "description": "技术描述",
      "evidence": "验证证据",
      "impact": "业务影响",
      "exploitability": "可利用性评估",
      "remediation": "修复建议",
      "references": ["参考链接"]
    }
  ],
  "risk_assessment": {
    "risk_level": "critical|high|medium|low",
    "risk_score": 85,
    "severity_counts": {"critical": 2, "high": 5, "medium": 10, "low": 15},
    "summary": "风险摘要"
  },
  "next_recommendations": ["下一步建议"]
}
```

## 关键原则
1. 优先验证高危和严重漏洞
2. 提供可复现的漏洞验证步骤
3. 评估漏洞的实际业务影响
4. 按风险级别排序处理建议"""


    def __init__(self, llm_client, scanner=None, **kwargs):
        super().__init__(llm_client, **kwargs)
        self.scanner = scanner
        self.vuln_results = {}

    def execute(self, task: Task) -> AgentResult:
        """执行漏洞分析任务"""
        recon_data = task.input_data.get("recon_data", {})
        target = task.input_data.get("target")
        normalized_recon = self._normalize_recon_data(recon_data)
        services = normalized_recon.get("services", {})
        web_info = normalized_recon.get("web", {})

        if not target:
            return AgentResult(success=False, error="未指定目标")

        self.add_log(f"开始漏洞分析: {target}")

        # 使用LLM分析目标漏洞
        vuln_plan = self._plan_vuln_scan(target, services, web_info)
        self.add_log(f"漏洞扫描计划: {vuln_plan.get('plan_name', '标准扫描')}")

        # 执行漏洞扫描
        results = {}

        # 1. 服务漏洞分析
        if vuln_plan.get("scan_services", True):
            service_vulns = self._scan_service_vulns(services)
            results["service_vulns"] = service_vulns

        # 2. Web漏洞分析
        if vuln_plan.get("scan_web", True) or web_info:
            web_vulns = self._scan_web_vulns(target, web_info)
            results["web_vulns"] = web_vulns

        # 3. 配置审计
        if vuln_plan.get("audit_config", True):
            config_issues = self._audit_configuration(target, services)
            results["config_issues"] = config_issues

        # 4. 漏洞优先级排序
        prioritized = self._prioritize_vulns(results)

        # 5. 风险评估
        risk_assessment = self._assess_risk(prioritized)

        self.vuln_results = results

        return AgentResult(
            success=True,
            data={
                "target": target,
                "vulnerabilities": prioritized,
                "risk_assessment": risk_assessment,
                "scan_plan": vuln_plan
            },
            logs=self.execution_logs
        )

    def _normalize_recon_data(self, recon_data: Dict) -> Dict:
        """兼容 ReconAgent 的原始 data 结构和精简结构"""
        if not recon_data:
            return {}
        if "results" in recon_data and isinstance(recon_data["results"], dict):
            return recon_data["results"]
        return recon_data

    def _plan_vuln_scan(
        self,
        target: str,
        services: Dict,
        web_info: Dict
    ) -> Dict:
        """使用LLM制定漏洞扫描计划"""
        services_summary = "\n".join([
            f"- 端口 {port}: {info.get('name', 'unknown')}"
            for port, info in services.items()
        ])

        prompt = f"""请分析以下目标信息，制定漏洞扫描计划。

目标: {target}

发现的服务:
{services_summary}

Web信息:
{json.dumps(web_info, indent=2, ensure_ascii=False)}

请返回JSON格式的扫描计划：
{{
    "plan_name": "计划名称",
    "scan_services": true/false,
    "scan_web": true/false,
    "audit_config": true/false,
    "priority_vulns": ["要优先检查的漏洞类型"],
    "skip_vulns": ["可跳过的漏洞类型"],
    "estimated_time": "预计时间"
}}"""

        try:
            result = self.analyze_with_llm(
                prompt,
                require_json=True,
                json_schema={
                    "plan_name": {"type": "string"},
                    "scan_services": {"type": "boolean"},
                    "scan_web": {"type": "boolean"},
                    "audit_config": {"type": "boolean"},
                    "priority_vulns": {"type": "array", "items": {"type": "string"}},
                    "skip_vulns": {"type": "array", "items": {"type": "string"}},
                    "estimated_time": {"type": "string"}
                }
            )
            return result
        except Exception as e:
            self.add_log(f"扫描计划制定失败，使用默认计划: {e}", "WARNING")
            return {
                "plan_name": "标准扫描",
                "scan_services": True,
                "scan_web": True,
                "audit_config": True
            }

    def _scan_service_vulns(self, services: Dict) -> List[Dict]:
        """服务漏洞扫描"""
        self.add_log("开始服务漏洞扫描...")

        vulnerabilities = []

        # 常见服务漏洞检查
        vuln_checks = {
            "ssh": ["弱密码", "版本漏洞", "配置不当"],
            "ftp": ["匿名访问", "弱密码", "VSFTPD后门"],
            "mysql": ["弱密码", "root远程登录", "SQL注入"],
            "http": ["SQL注入", "XSS", "CSRF", "文件上传"],
            "smb": ["永恒之蓝", "弱密码", "共享配置"],
            "rdp": ["弱密码", "BlueKeep漏洞"],
            "telnet": ["明文传输", "弱密码"]
        }

        for port, service_info in services.items():
            service_name = service_info.get("name", "").lower()
            version = service_info.get("version", "")

            # 检查常见漏洞
            for vuln_type, descriptions in vuln_checks.items():
                if vuln_type in service_name:
                    # 使用LLM评估漏洞可能性
                    vuln_assessment = self._assess_service_vuln(
                        service_name, version, descriptions
                    )
                    if vuln_assessment:
                        vulnerabilities.extend(vuln_assessment)

        # 如果有扫描器，使用扫描器进行更详细的扫描
        if self.scanner:
            try:
                scanner_vulns = self.scanner.scan_vulnerabilities(services)
                vulnerabilities.extend(scanner_vulns)
            except Exception as e:
                self.add_log(f"扫描器漏洞扫描失败: {e}", "WARNING")

        self.add_log(f"发现 {len(vulnerabilities)} 个潜在漏洞")
        return vulnerabilities

    def _assess_service_vuln(
        self,
        service_name: str,
        version: str,
        vuln_types: List[str]
    ) -> List[Dict]:
        """使用LLM评估服务漏洞"""
        prompt = f"""请评估 {service_name} (版本: {version}) 可能存在的漏洞。

可能的漏洞类型: {', '.join(vuln_types)}

请返回JSON格式的漏洞列表：
[
    {{
        "name": "漏洞名称",
        "type": "漏洞类型",
        "severity": "critical/high/medium/low",
        "cve": "CVE编号(如果有)",
        "description": "漏洞描述",
        "exploitability": "可利用性评估"
    }}
]"""

        try:
            result = self.analyze_with_llm(
                prompt,
                require_json=True,
                json_schema={
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "type": {"type": "string"},
                            "severity": {"type": "string"},
                            "cve": {"type": "string"},
                            "description": {"type": "string"},
                            "exploitability": {"type": "string"}
                        }
                    }
                }
            )
            return result if isinstance(result, list) else []
        except Exception as e:
            self.add_log(f"漏洞评估失败: {e}", "WARNING")
            return []

    def _scan_web_vulns(self, target: str, web_info: Dict) -> List[Dict]:
        """Web漏洞扫描"""
        self.add_log("开始Web漏洞扫描...")

        vulnerabilities = []

        # 常见Web漏洞检查
        common_web_vulns = [
            {"type": "sql_injection", "severity": "critical"},
            {"type": "xss", "severity": "high"},
            {"type": "csrf", "severity": "medium"},
            {"type": "file_upload", "severity": "high"},
            {"type": "command_injection", "severity": "critical"},
            {"type": "path_traversal", "severity": "high"},
            {"type": "ssrf", "severity": "high"},
            {"type": "idors", "severity": "high"},
            {"type": "security_misconfiguration", "severity": "medium"},
            {"type": "sensitive_data_exposure", "severity": "high"}
        ]

        # 使用LLM评估Web漏洞
        prompt = f"""请评估以下Web应用的潜在漏洞。

目标: {target}
Web信息: {json.dumps(web_info, indent=2, ensure_ascii=False)}

请返回JSON格式的漏洞列表：
[
    {{
        "name": "漏洞名称",
        "type": "漏洞类型",
        "severity": "critical/high/medium/low",
        "cve": "CVE编号(如果有)",
        "description": "漏洞描述",
        "location": "漏洞位置",
        "evidence": "发现证据"
    }}
]"""

        try:
            result = self.analyze_with_llm(
                prompt,
                require_json=True,
                json_schema={
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "type": {"type": "string"},
                            "severity": {"type": "string"},
                            "cve": {"type": "string"},
                            "description": {"type": "string"},
                            "location": {"type": "string"},
                            "evidence": {"type": "string"}
                        }
                    }
                }
            )
            vulnerabilities = result if isinstance(result, list) else []
        except Exception as e:
            self.add_log(f"Web漏洞评估失败: {e}", "WARNING")
            # 使用预设的常见漏洞
            for vuln in common_web_vulns:
                vulnerabilities.append({
                    "name": f"{vuln['type']} (需要验证)",
                    "type": vuln['type'],
                    "severity": vuln['severity'],
                    "status": "potential"
                })

        return vulnerabilities

    def _audit_configuration(self, target: str, services: Dict) -> List[Dict]:
        """配置审计"""
        self.add_log("开始配置审计...")

        issues = []

        # 使用LLM进行配置审计
        prompt = f"""请分析以下服务配置，识别潜在的安全配置问题。

目标: {target}

服务配置:
{json.dumps(services, indent=2, ensure_ascii=False)}

请返回JSON格式的配置问题列表：
[
    {{
        "issue": "问题描述",
        "severity": "critical/high/medium/low",
        "service": "相关服务",
        "recommendation": "修复建议"
    }}
]"""

        try:
            result = self.analyze_with_llm(
                prompt,
                require_json=True,
                json_schema={
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "issue": {"type": "string"},
                            "severity": {"type": "string"},
                            "service": {"type": "string"},
                            "recommendation": {"type": "string"}
                        }
                    }
                }
            )
            issues = result if isinstance(result, list) else []
        except Exception as e:
            self.add_log(f"配置审计失败: {e}", "WARNING")

        return issues

    def _prioritize_vulns(self, results: Dict) -> Dict:
        """漏洞优先级排序"""
        all_vulns = []

        # 合并所有漏洞
        for vuln_type, vulns in results.items():
            if isinstance(vulns, list):
                for vuln in vulns:
                    vuln["category"] = vuln_type
                    all_vulns.append(vuln)

        # 使用LLM进行优先级排序
        prompt = f"""请对以下漏洞进行优先级排序，考虑以下因素：
1. 漏洞严重性
2. 可利用性
3. 影响范围
4. 利用复杂度

漏洞列表:
{json.dumps(all_vulns, indent=2, ensure_ascii=False)}

请返回排序后的漏洞列表，格式为JSON数组，每项包含：
{{
    "name": "漏洞名称",
    "type": "漏洞类型",
    "severity": "critical/high/medium/low",
    "priority": 1-10,
    "reason": "优先级理由"
}}"""

        try:
            prioritized = self.analyze_with_llm(
                prompt,
                require_json=True,
                json_schema={
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "type": {"type": "string"},
                            "severity": {"type": "string"},
                            "priority": {"type": "number"},
                            "reason": {"type": "string"}
                        }
                    }
                }
            )
            return prioritized if isinstance(prioritized, list) else all_vulns
        except Exception as e:
            self.add_log(f"漏洞排序失败，使用默认排序: {e}", "WARNING")
            # 按严重性排序
            severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
            return sorted(
                all_vulns,
                key=lambda x: severity_order.get(x.get("severity", "low"), 0),
                reverse=True
            )

    def _assess_risk(self, vulnerabilities: List[Dict]) -> Dict:
        """风险评估"""
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}

        for vuln in vulnerabilities:
            severity = vuln.get("severity", "low")
            if severity in severity_counts:
                severity_counts[severity] += 1

        # 计算风险评分
        risk_score = (
            severity_counts["critical"] * 10 +
            severity_counts["high"] * 7 +
            severity_counts["medium"] * 4 +
            severity_counts["low"] * 1
        )

        if risk_score >= 25:
            risk_level = "critical"
        elif risk_score >= 15:
            risk_level = "high"
        elif risk_score >= 5:
            risk_level = "medium"
        else:
            risk_level = "low"

        return {
            "risk_level": risk_level,
            "risk_score": risk_score,
            "severity_counts": severity_counts,
            "summary": f"发现 {severity_counts['critical']} 个严重漏洞，{severity_counts['high']} 个高危漏洞"
        }

    def get_capabilities(self) -> List[str]:
        """获取Agent能力"""
        return [
            "服务漏洞扫描",
            "Web漏洞扫描",
            "漏洞优先级排序",
            "风险评估",
            "配置审计",
            "CVE识别"
        ]
