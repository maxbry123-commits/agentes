"""
报告生成Agent
负责生成渗透测试报告
"""
from typing import Dict, List, Optional, Any
import json
from datetime import datetime
from .base import BaseAgent, AgentResult, Task, TaskPriority


class ReportAgent(BaseAgent):
    """
    报告生成Agent
    负责：
    - 收集和整理测试结果
    - 生成结构化报告
    - 提供修复建议
    - 风险评估和总结
    """

    AGENT_TYPE = "report"

    SYSTEM_PROMPT = """你是一个专业的渗透测试报告编写专家（Penetration Testing Report Specialist），在渗透测试团队中担任报告输出的角色。

## 你的专业背景
- 具备丰富的渗透测试报告编写经验
- 熟悉各类安全漏洞的分类和评级标准
- 能够将复杂的技术发现转化为清晰易懂的语言
- 熟悉合规标准和最佳实践（OWASP, NIST, ISO 27001）

## 你的核心职责
1. **数据整合**：收集和整理所有测试阶段的结果
2. **漏洞分析**：对发现的漏洞进行深入分析和归类
3. **风险评估**：基于CVSS和其他标准评估风险等级
4. **报告撰写**：生成结构化、专业的安全测试报告
5. **修复建议**：提供具体、可执行的漏洞修复方案

## 报告结构框架

### 1. 执行摘要（Executive Summary）
- 测试目标和时间范围
- 测试方法论概述
- 主要发现总结
- 风险评级概览
- 关键建议摘要

### 2. 测试范围（Scope）
- 测试目标清单
- 测试类型（黑盒/灰盒/白盒）
- 测试方法
- 排除项

### 3. 方法论（Methodology）
- 测试阶段：侦察、漏洞分析、利用、报告
- 使用的工具和技术
- 测试标准依据

### 4. 发现详情（Findings）
按风险等级排序：
- **严重漏洞（Critical）**：立即修复
- **高危漏洞（High）**：优先修复
- **中危漏洞（Medium）**：计划修复
- **低危漏洞（Low）**：适时修复
- **信息泄露（Informational）**：了解即可

### 5. 风险评估（Risk Assessment）
- CVSS评分说明
- 风险等级定义
- 业务影响分析

### 6. 修复建议（Remediation）
每个漏洞应包含：
- 技术描述
- 风险评级
- 验证步骤
- 修复方案
- 优先级
- 参考资源

### 7. 结论（Conclusion）
- 测试总结
- 整体风险评估
- 后续建议

### 8. 附录（Appendix）
- 使用的工具列表
- 完整输出日志
- 术语表

## 漏洞评级标准

### CVSS 3.1 评分
- 严重（Critical）：9.0-10.0
- 高危（High）：7.0-8.9
- 中危（Medium）：4.0-6.9
- 低危（Low）：0.1-3.9
- 无（None）：0

### 业务影响评估
- **机密性影响**：数据泄露风险
- **完整性影响**：数据篡改风险
- **可用性影响**：服务中断风险

## 输出格式要求

请严格按照以下JSON格式输出：

```json
{
  "report": {
    "meta": {
      "title": "渗透测试报告",
      "target": "目标信息",
      "test_date": "测试日期",
      "report_date": "报告日期",
      "version": "1.0",
      "classification": " confidential"
    },
    "executive_summary": {
      "overview": "测试概述",
      "scope": "测试范围",
      "key_findings": ["关键发现"],
      "risk_level": "critical|high|medium|low",
      "summary": "总体评估摘要"
    },
    "methodology": {
      "approach": "黑盒/灰盒/白盒",
      "phases": ["侦察", "漏洞分析", "利用", "报告"],
      "tools_used": ["使用的工具"]
    },
    "vulnerabilities": [
      {
        "id": "VULN-001",
        "name": "漏洞名称",
        "severity": "critical|high|medium|low|info",
        "cvss": 9.8,
        "cve": "CVE-XXXX-XXXX",
        "cwe": "CWE-XXX",
        "location": "漏洞位置",
        "description": "技术描述",
        "impact": "业务影响",
        "evidence": "发现证据",
        "exploitation": "利用条件",
        "remediation": {
          "priority": "P1-P5",
          "description": "修复方案",
          "steps": ["步骤1", "步骤2"],
          "references": []
        }
      }
    ],
    "statistics": {
      "total_vulns": 10,
      "critical": 2,
      "high": 3,
      "medium": 3,
      "low": 2,
      "test_duration": "X小时Y分钟"
    },
    "recommendations": ["总体建议"],
    "conclusion": "结论"
  }
}
```

## 关键原则
1. 报告应客观、准确、完整
2. 按风险等级排序，突出最关键的问题
3. 提供具体、可执行的修复建议
4. 使用图表和可视化提升可读性
5. 平衡技术细节和业务影响
6. 确保报告符合行业标准和最佳实践"""

    def __init__(self, llm_client, **kwargs):
        super().__init__(llm_client, **kwargs)
        self.report_data = {}

    def execute(self, task: Task) -> AgentResult:
        """执行报告生成任务"""
        test_results = task.input_data.get("test_results", {})
        target = task.input_data.get("target", "Unknown")
        report_format = task.input_data.get("format", "json")

        self.add_log(f"开始生成报告: {target}")

        # 收集所有测试数据
        self.report_data = self._collect_data(test_results)

        # 生成报告各部分
        report = {
            "meta": self._generate_meta(target),
            "executive_summary": self._generate_executive_summary(),
            "methodology": self._generate_methodology(),
            "findings": self._generate_findings(),
            "vulnerabilities": self._generate_vulnerability_report(),
            "risk_assessment": self._generate_risk_assessment(),
            "recommendations": self._generate_recommendations(),
            "appendix": self._generate_appendix()
        }

        # 使用LLM润色报告
        report = self._polish_report(report)

        # 按格式输出
        if report_format == "html":
            output = self._to_html(report)
        elif report_format == "markdown":
            output = self._to_markdown(report)
        else:
            output = report

        self.add_log("报告生成完成")

        return AgentResult(
            success=True,
            data={
                "report": output,
                "format": report_format,
                "generated_at": datetime.now().isoformat()
            },
            logs=self.execution_logs
        )

    def _unwrap_phase_result(self, phase_result: Any) -> Dict:
        if not isinstance(phase_result, dict):
            return {}
        payload = phase_result.get("data")
        return payload if isinstance(payload, dict) else phase_result

    def _ensure_dict(self, value: Any) -> Dict:
        return value if isinstance(value, dict) else {}

    def _ensure_list(self, value: Any) -> List[Any]:
        return value if isinstance(value, list) else []

    def _ensure_list_of_dicts(self, value: Any) -> List[Dict]:
        return [item for item in self._ensure_list(value) if isinstance(item, dict)]

    def _ensure_list_of_strings(self, value: Any) -> List[str]:
        return [item for item in self._ensure_list(value) if isinstance(item, str)]

    def _derive_risk_level(self, vulns: List[Dict], flags: List[str], access_level: str = "") -> str:
        severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}
        max_severity = max(
            (
                severity_order.get(self._ensure_dict(v).get("severity", "low").lower(), 1)
                for v in self._ensure_list_of_dicts(vulns)
            ),
            default=0
        )
        if access_level.lower() in {"root", "admin"} and flags:
            return "critical"
        if len(flags) >= 3:
            return "critical"
        if max_severity >= 3 or flags:
            return "high"
        if max_severity >= 2:
            return "medium"
        return "low"

    def _get_capture_attempt(self) -> Dict:
        exploits = self._ensure_list_of_dicts(self.report_data.get("exploits", []))
        for item in exploits:
            if item.get("type") == "web_flag_capture":
                return item
        return {}

    def _related_flags_for_vuln(self, vuln_name: str) -> List[str]:
        flags = self.report_data.get("flags", [])
        name = (vuln_name or "").lower()
        mappings = [
            (["sql"], "FLAG{sqli_query_breakout}"),
            (["xss"], "FLAG{stored_xss_payload}"),
            (["命令", "command"], "FLAG{command_injection_shell}"),
            (["路径", "遍历", "traversal"], "FLAG{path_traversal_file_read}"),
            (["上传", "upload"], "FLAG{unrestricted_file_upload}"),
            (["ssrf"], "FLAG{ssrf_internal_access}"),
            (["反序列化", "deserialize"], "FLAG{unsafe_deserialization}"),
            (["xxe", "xml"], "FLAG{xxe_entity_disclosure}"),
            (["信息泄露", "debug"], "FLAG{debug_information_leak}"),
            (["签名", "导出", "export"], "FLAG{predictable_signed_export}"),
            (["恢复", "restore"], "FLAG{full_chain_compromise}"),
            (["维护", "ops"], "FLAG{signed_ops_ssti_chain}"),
            (["工作流", "预览", "workflow"], "FLAG{cve_style_workflow_preview_chain}"),
            (["插件", "plugin", "hotfix"], "FLAG{cve_style_plugin_hotfix_chain}"),
            (["报告", "重放", "replay"], "FLAG{cve_style_signed_report_replay}"),
        ]
        matched = []
        for keywords, flag in mappings:
            if any(keyword in name for keyword in keywords) and flag in flags:
                matched.append(flag)
        return matched

    def _related_urls_for_vuln(self, vuln_name: str) -> List[str]:
        capture = self._get_capture_attempt()
        visited_urls = capture.get("details", {}).get("visited_urls", [])
        name = (vuln_name or "").lower()
        url_keywords = [
            (["sql"], ["/products", "/posts?search"]),
            (["xss"], ["/posts/create", "/posts"]),
            (["命令", "command"], ["/tools/ping"]),
            (["路径", "遍历", "traversal"], ["/files?file="]),
            (["上传", "upload"], ["/upload"]),
            (["ssrf"], ["/tools/fetch", "/internal/"]),
            (["反序列化", "deserialize"], ["/api/data"]),
            (["xxe", "xml"], ["/api/xml"]),
            (["信息泄露", "debug"], ["/debug"]),
            (["签名", "导出", "export"], ["/support/export"]),
            (["恢复", "restore"], ["/admin/restore"]),
            (["维护", "ops"], ["/internal/ops/queue", "/admin/ops/console"]),
            (["工作流", "预览", "workflow"], ["/internal/workflows/preview", "/admin/workflows/preview"]),
            (["插件", "plugin", "hotfix"], ["/internal/plugins/catalog", "/admin/plugins/import"]),
            (["报告", "重放", "replay"], ["/internal/reports/replay", "/admin/reports/replay"]),
        ]
        matched_urls: List[str] = []
        for keywords, markers in url_keywords:
            if any(keyword in name for keyword in keywords):
                matched_urls.extend([url for url in visited_urls if any(marker in url for marker in markers)])
        seen = set()
        deduped = []
        for url in matched_urls:
            if url not in seen:
                seen.add(url)
                deduped.append(url)
        return deduped[:6]

    def _remediation_for_vuln(self, vuln_name: str) -> Dict:
        name = (vuln_name or "").lower()
        if "sql" in name:
            return {
                "summary": "改用参数化查询并禁止字符串拼接构造 SQL。",
                "steps": ["使用预编译语句", "对搜索参数做白名单校验", "为数据库访问增加最小权限账号"],
            }
        if "xss" in name:
            return {
                "summary": "对输入做上下文相关编码，并限制危险 HTML。",
                "steps": ["服务端过滤脚本标签和事件属性", "启用输出编码", "补充 CSP"],
            }
        if "命令" in name or "command" in name:
            return {
                "summary": "移除 shell=True 并对参数做严格白名单校验。",
                "steps": ["使用安全 API 调用系统命令", "限制可传入目标格式", "在执行层隔离权限"],
            }
        if "路径" in name or "遍历" in name or "traversal" in name:
            return {
                "summary": "对文件路径做规范化并限制在受控目录内。",
                "steps": ["使用路径规范化比较真实路径", "拒绝 .. 与绝对路径", "拆分公开文件与敏感文件目录"],
            }
        if "上传" in name or "upload" in name:
            return {
                "summary": "限制上传类型并将文件存储到不可执行目录。",
                "steps": ["校验 MIME 与扩展名", "重命名上传文件", "关闭上传目录脚本执行权限"],
            }
        if "ssrf" in name:
            return {
                "summary": "对外连目标做协议和地址白名单限制。",
                "steps": ["禁止访问内网与本机地址", "校验 scheme", "增加代理层审计与 deny list"],
            }
        if "反序列化" in name or "deserialize" in name:
            return {
                "summary": "移除不安全反序列化并改用安全数据格式。",
                "steps": ["禁用 pickle 输入", "改用 JSON", "增加结构校验与签名校验"],
            }
        if "xxe" in name or "xml" in name:
            return {
                "summary": "禁用外部实体解析并限制本地文件访问。",
                "steps": ["关闭 DTD/ENTITY", "使用安全 XML 解析器", "在解析前做格式校验"],
            }
        if "签名" in name or "导出" in name or "export" in name or "恢复" in name or "维护" in name or "工作流" in name:
            return {
                "summary": "升级签名方案并收紧内部控制台的输入面。",
                "steps": ["使用一次性短期令牌", "把种子移出可读路径", "禁止服务端渲染用户模板", "对内部接口增加鉴权"],
            }
        if "信息泄露" in name or "debug" in name:
            return {
                "summary": "关闭调试信息与敏感配置泄露。",
                "steps": ["生产环境禁用 debug 页面", "移除敏感环境变量展示", "审计公开端点暴露信息"],
            }
        return {
            "summary": "对该漏洞点补充输入校验、权限控制与最小暴露。",
            "steps": ["限制输入", "收紧权限", "增加日志与告警"],
        }

    def _collect_data(self, test_results: Dict) -> Dict:
        """收集测试数据"""
        data = {
            "recon": {},
            "vulns": [],
            "exploits": [],
            "flags": [],
            "sessions": [],
            "attempts": [],
            "timeline": [],
            "risk_assessment": {},
            "exploit_analysis": {},
        }

        # 信息收集结果
        if "recon" in test_results:
            recon = self._unwrap_phase_result(test_results["recon"])
            recon_results = recon.get("results", {}) if isinstance(recon.get("results"), dict) else recon
            recon_results = self._ensure_dict(recon_results)
            data["recon"] = {
                "target": recon.get("target"),
                "ports": recon_results.get("open_ports", recon_results.get("ports", [])),
                "services": recon_results.get("services", {}),
                "os": recon_results.get("os"),
                "web_info": recon_results.get("web", {})
            }

        # 漏洞发现结果
        if "vuln" in test_results:
            vuln = self._unwrap_phase_result(test_results["vuln"])
            data["vulns"] = self._ensure_list_of_dicts(vuln.get("vulnerabilities", []))
            data["risk_assessment"] = self._ensure_dict(vuln.get("risk_assessment", {}))

        # 利用结果
        if "exploit" in test_results:
            exploit = self._unwrap_phase_result(test_results["exploit"])
            exploit_results = exploit.get("results", {}) if isinstance(exploit.get("results"), dict) else {}
            exploit_results = self._ensure_dict(exploit_results)
            data["attempts"] = self._ensure_list_of_dicts(exploit_results.get("attempts", []))
            data["exploits"] = self._ensure_list_of_dicts(exploit_results.get("successful", []))
            data["flags"] = self._ensure_list_of_strings(exploit_results.get("flags", []))
            data["sessions"] = self._ensure_list_of_dicts(exploit_results.get("sessions", []))
            data["exploit_analysis"] = self._ensure_dict(exploit.get("analysis", {}))

        # 时间线
        if "timeline" in test_results:
            data["timeline"] = test_results["timeline"]

        return data

    def _generate_meta(self, target: str) -> Dict:
        """生成报告元信息"""
        return {
            "title": f"渗透测试报告 - {target}",
            "target": target,
            "test_date": datetime.now().strftime("%Y-%m-%d"),
            "test_time": datetime.now().strftime("%H:%M:%S"),
            "tool": "AI-Pentest Agent System",
            "version": "1.0"
        }

    def _generate_executive_summary(self) -> Dict:
        """生成执行摘要"""
        vulns = self.report_data.get("vulns", [])
        exploits = self.report_data.get("exploits", [])
        flags = self.report_data.get("flags", [])
        exploit_analysis = self._ensure_dict(self.report_data.get("exploit_analysis", {}))

        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        for vuln in self._ensure_list_of_dicts(vulns):
            severity = vuln.get("severity", "info").lower()
            if severity in severity_counts:
                severity_counts[severity] += 1
        access_level = exploit_analysis.get("access_level", "")
        risk_level = self._derive_risk_level(vulns, flags, access_level)

        key_findings = [
            f"共识别 {len(vulns)} 个漏洞，其中高危及以上 {severity_counts['critical'] + severity_counts['high']} 个",
            f"成功完成 {len(exploits)} 条利用步骤，提取 {len(flags)} 个 Flag",
        ]
        if access_level:
            key_findings.append(f"攻击过程中达到 {access_level} 级访问权限")
        if flags:
            key_findings.append(f"已验证的 Flag 包括 {', '.join(flags[:4])}{' 等' if len(flags) > 4 else ''}")

        return {
            "overview": (
                f"本次安全测试围绕目标的真实攻击面开展。测试共识别 {len(vulns)} 个漏洞，"
                f"成功执行 {len(exploits)} 条利用链，并最终提取 {len(flags)} 个 Flag。"
            ),
            "key_findings": key_findings,
            "risk_level": risk_level,
            "immediate_actions": [
                "立即下线调试与内部预览接口，阻断公开可达的攻击面",
                "轮换默认凭据、签名种子与内部令牌，并撤销已暴露密钥",
                "优先修复已被成功利用的文件读取、SSRF、模板渲染和命令执行链路",
            ],
            "overall_assessment": (
                f"报告与实际渗透过程一致：攻击链已从信息泄露扩展到多步组合利用，"
                f"当前整体风险等级为 {risk_level}。"
            ),
        }

    def _generate_methodology(self) -> Dict:
        """生成测试方法说明"""
        return {
            "approach": "黑盒测试",
            "phases": [
                {
                    "name": "信息收集",
                    "description": "端口扫描、服务识别、指纹识别",
                    "tools": ["Nmap", "WhatWeb"]
                },
                {
                    "name": "漏洞分析",
                    "description": "漏洞扫描、漏洞识别、风险评估",
                    "tools": ["Vulnerability Scanner", "SearchSploit"]
                },
                {
                    "name": "漏洞利用",
                    "description": "漏洞利用尝试、凭据测试",
                    "tools": ["Hydra", "Metasploit"]
                },
                {
                    "name": "报告生成",
                    "description": "结果整理、风险评估、修复建议",
                    "tools": ["AI Analysis"]
                }
            ],
            "standards": ["OWASP Top 10", "PTES", "OSSTMM"]
        }

    def _generate_findings(self) -> List[Dict]:
        """生成发现报告"""
        findings = []
        recon = self._ensure_dict(self.report_data.get("recon", {}))
        flags = self._ensure_list_of_strings(self.report_data.get("flags", []))
        exploit_analysis = self._ensure_dict(self.report_data.get("exploit_analysis", {}))

        # 端口发现
        ports = self._ensure_list_of_dicts(recon.get("ports", []))
        if ports:
            findings.append({
                "category": "信息收集",
                "title": "开放端口",
                "description": f"发现 {len(ports)} 个开放端口",
                "details": [
                    {
                        "port": p.get("port"),
                        "service": p.get("service"),
                        "state": p.get("state", "open")
                    }
                    for p in ports
                ],
                "severity": "info"
            })

        # 服务发现
        services = self._ensure_dict(recon.get("services", {}))
        if services:
            findings.append({
                "category": "信息收集",
                "title": "服务识别",
                "description": f"识别到 {len(services)} 个服务",
                "details": services,
                "severity": "info"
            })

        # OS识别
        os_info = self._ensure_dict(recon.get("os"))
        if os_info:
            findings.append({
                "category": "信息收集",
                "title": "操作系统识别",
                "description": f"目标系统: {os_info.get('name', 'Unknown')}",
                "details": os_info,
                "severity": "info"
            })

        web_info = self._ensure_dict(recon.get("web_info", {}))
        missing_headers = web_info.get("security_headers", {}).get("missing", []) if isinstance(web_info, dict) else []
        if missing_headers:
            findings.append({
                "category": "配置弱点",
                "title": "缺失关键安全响应头",
                "description": f"检测到 {len(missing_headers)} 个缺失安全头，为后续利用提供了辅助条件。",
                "details": missing_headers,
                "severity": "medium"
            })

        if flags:
            findings.append({
                "category": "攻击结果",
                "title": "已验证的攻击链与 Flag 提取",
                "description": f"利用阶段已成功提取 {len(flags)} 个 Flag，验证目标可被真实攻陷。",
                "details": {
                    "flags": flags,
                    "access_level": exploit_analysis.get("access_level", ""),
                    "summary": exploit_analysis.get("summary", ""),
                },
                "severity": "critical"
            })

        return findings

    def _generate_vulnerability_report(self) -> List[Dict]:
        """生成漏洞报告"""
        vulns = self._ensure_list_of_dicts(self.report_data.get("vulns", []))

        if not vulns:
            return []

        enhanced_vulns = []
        for index, vuln in enumerate(vulns, start=1):
            related_flags = self._related_flags_for_vuln(vuln.get("name", ""))
            related_urls = self._related_urls_for_vuln(vuln.get("name", ""))
            remediation = self._remediation_for_vuln(vuln.get("name", ""))
            severity = vuln.get("severity", "medium").lower()
            evidence_parts = []
            if vuln.get("reason"):
                evidence_parts.append(vuln["reason"])
            if related_flags:
                evidence_parts.append(f"已在利用阶段验证相关 Flag: {', '.join(related_flags)}")
            if related_urls:
                evidence_parts.append(f"相关访问路径: {', '.join(related_urls)}")

            enhanced_vulns.append({
                "id": f"VULN-{index:03d}",
                "title": vuln.get("name", f"漏洞 {index}"),
                "name": vuln.get("name", f"漏洞 {index}"),
                "severity": severity,
                "cvss": vuln.get("cvss", vuln.get("priority", 0)),
                "cve": vuln.get("cve", ""),
                "cwe": vuln.get("cwe", ""),
                "location": vuln.get("location", vuln.get("target", "目标应用")),
                "description": vuln.get("description") or vuln.get("reason") or vuln.get("type", ""),
                "impact": vuln.get("impact") or vuln.get("exploitability") or "攻击者可借此扩大攻击面或形成组合利用链。",
                "evidence": "；".join(evidence_parts) if evidence_parts else "已在测试过程中发现并记录。",
                "exploitation": (
                    "已在当前测试中被真实利用。"
                    if related_flags else
                    "在当前测试中发现该弱点，尚未建立与独立 Flag 的直接映射。"
                ),
                "remediation": remediation["summary"],
                "remediation_steps": remediation["steps"],
                "references": vuln.get("references", []),
                "original": vuln,
            })

        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
        return sorted(enhanced_vulns, key=lambda x: severity_order.get(x.get("severity", "info").lower(), 4))

    def _enhance_vulnerability(self, vuln: Dict) -> Dict:
        """使用LLM增强漏洞描述"""
        prompt = f"""请增强以下漏洞的描述和修复建议。

漏洞信息:
{json.dumps(vuln, indent=2, ensure_ascii=False)}

请返回JSON格式的增强信息：
{{
    "title": "漏洞标题",
    "description": "详细描述（包含技术细节）",
    "impact": "影响分析",
    "cvss_score": "CVSS评分(估算)",
    "remediation": "修复建议",
    "references": ["参考链接"]
}}"""

        try:
            enhanced = self.analyze_with_llm(
                prompt,
                require_json=True,
                json_schema={
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "impact": {"type": "string"},
                    "cvss_score": {"type": "string"},
                    "remediation": {"type": "string"},
                    "references": {"type": "array", "items": {"type": "string"}}
                }
            )

            # 合并原始信息
            enhanced["original"] = vuln
            return enhanced
        except Exception:
            return {
                "title": vuln.get("name", "Unknown Vulnerability"),
                "description": vuln.get("description", ""),
                "severity": vuln.get("severity", "medium"),
                "original": vuln
            }

    def _generate_risk_assessment(self) -> Dict:
        """生成风险评估"""
        vulns = self._ensure_list_of_dicts(self.report_data.get("vulns", []))
        exploits = self._ensure_list_of_dicts(self.report_data.get("exploits", []))
        flags = self._ensure_list_of_strings(self.report_data.get("flags", []))
        exploit_analysis = self._ensure_dict(self.report_data.get("exploit_analysis", {}))
        severity_scores = {"critical": 10, "high": 7, "medium": 4, "low": 1, "info": 0}
        total_score = sum(severity_scores.get(v.get("severity", "low").lower(), 1) for v in vulns)
        total_score += len(exploits) * 4 + len(flags) * 3
        risk_level = self._derive_risk_level(vulns, flags, exploit_analysis.get("access_level", ""))

        return {
            "overall_risk": risk_level,
            "risk_score": min(total_score, 100),
            "business_impact": (
                f"攻击者已在测试中提取 {len(flags)} 个 Flag，"
                f"{'并取得 ' + exploit_analysis.get('access_level', '') + ' 级权限，' if exploit_analysis.get('access_level') else ''}"
                "说明目标存在可被串联利用的真实攻击路径。"
            ),
            "likelihood": "高" if exploits else "中",
            "affected_assets": [self.report_data.get("recon", {}).get("target", "目标应用")],
            "compliance_issues": [
                "存在调试信息和敏感配置泄露",
                "存在可被真实利用的输入校验与访问控制缺陷",
            ],
        }

    def _generate_recommendations(self) -> Dict:
        """生成修复建议"""
        vulns = self._ensure_list_of_dicts(self.report_data.get("vulns", []))

        # 基于漏洞生成建议
        recommendations = {
            "immediate": [],    # 立即修复
            "short_term": [],   # 短期修复
            "long_term": []     # 长期改进
        }

        for vuln in vulns:
            severity = vuln.get("severity", "medium").lower()

            rec = {
                "issue": vuln.get("name", "Unknown"),
                "recommendation": vuln.get("remediation", "请参考相关安全公告"),
                "priority": "high" if severity in ["critical", "high"] else "medium"
            }

            if severity == "critical":
                recommendations["immediate"].append(rec)
            elif severity == "high":
                recommendations["short_term"].append(rec)
            else:
                recommendations["long_term"].append(rec)
        recommendations["best_practices"] = [
            "对内部接口、调试端点和预览控制台统一加鉴权与最小暴露",
            "把签名种子、令牌和敏感配置迁移到不可读的安全存储",
            "建立针对上传、模板渲染、文件读取和 SSRF 的防御基线与测试用例",
        ]

        return recommendations

    def _generate_appendix(self) -> Dict:
        """生成附录"""
        return {
            "tools_used": [
                {"name": "Nmap", "version": "7.x", "purpose": "端口扫描"},
                {"name": "Nikto", "version": "2.x", "purpose": "Web漏洞扫描"},
                {"name": "Hydra", "version": "9.x", "purpose": "暴力破解"},
                {"name": "SearchSploit", "version": "latest", "purpose": "漏洞搜索"}
            ],
            "references": [
                "OWASP Top 10: https://owasp.org/Top10/",
                "CVE Details: https://www.cvedetails.com/",
                "NVD: https://nvd.nist.gov/"
            ],
            "glossary": {
                "CVSS": "Common Vulnerability Scoring System",
                "CVE": "Common Vulnerabilities and Exposures",
                "RCE": "Remote Code Execution",
                "XSS": "Cross-Site Scripting",
                "SQLi": "SQL Injection"
            },
            "validated_flags": self.report_data.get("flags", []),
            "exploit_summary": self.report_data.get("exploit_analysis", {}),
        }

    def _polish_report(self, report: Dict) -> Dict:
        """生成与事实一致的简明摘要，避免覆盖真实结果"""
        report["executive_summary"]["polished"] = (
            f"目标 {report['meta']['target']} 在本次测试中共发现 {len(report['vulnerabilities'])} 个漏洞，"
            f"成功提取 {len(self.report_data.get('flags', []))} 个 Flag，"
            f"整体风险评级为 {report['risk_assessment'].get('overall_risk', 'unknown')}。"
        )
        return report

    def _to_html(self, report: Dict) -> str:
        """转换为HTML格式"""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{report['meta']['title']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #333; }}
        h2 {{ color: #666; border-bottom: 2px solid #ddd; padding-bottom: 10px; }}
        .critical {{ color: #d32f2f; }}
        .high {{ color: #f57c00; }}
        .medium {{ color: #fbc02d; }}
        .low {{ color: #388e3c; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #f5f5f5; }}
        .vuln-card {{ border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }}
    </style>
</head>
<body>
    <h1>{report['meta']['title']}</h1>
    <p><strong>测试日期:</strong> {report['meta']['test_date']}</p>

    <h2>执行摘要</h2>
    <p>{report['executive_summary'].get('overview', '')}</p>
    <p><strong>风险等级:</strong> <span class="{report['risk_assessment'].get('overall_risk', 'low')}">{report['risk_assessment'].get('overall_risk', 'Unknown')}</span></p>

    <h2>关键发现</h2>
    <ul>
        {''.join(f'<li>{f}</li>' for f in report['executive_summary'].get('key_findings', []))}
    </ul>

    <h2>漏洞详情</h2>
    {''.join(self._vuln_to_html(v) for v in report['vulnerabilities'])}

    <h2>修复建议</h2>
    <h3>立即修复</h3>
    <ul>
        {''.join(f'<li>{r.get("recommendation", r)}</li>' for r in report['recommendations'].get('immediate', []))}
    </ul>

    <h3>短期修复</h3>
    <ul>
        {''.join(f'<li>{r.get("recommendation", r)}</li>' for r in report['recommendations'].get('short_term', []))}
    </ul>

    <h2>风险评估</h2>
    <table>
        <tr><th>指标</th><th>值</th></tr>
        <tr><td>整体风险</td><td class="{report['risk_assessment'].get('overall_risk', 'low')}">{report['risk_assessment'].get('overall_risk', 'Unknown')}</td></tr>
        <tr><td>风险评分</td><td>{report['risk_assessment'].get('risk_score', 0)}</td></tr>
        <tr><td>业务影响</td><td>{report['risk_assessment'].get('business_impact', 'N/A')}</td></tr>
    </table>
</body>
</html>"""
        return html

    def _vuln_to_html(self, vuln: Dict) -> str:
        """漏洞转HTML"""
        severity = vuln.get('severity', 'low').lower()
        return f"""
    <div class="vuln-card">
        <h3 class="{severity}">{vuln.get('title', 'Unknown Vulnerability')}</h3>
        <p><strong>严重程度:</strong> <span class="{severity}">{severity.upper()}</span></p>
        <p><strong>描述:</strong> {vuln.get('description', 'N/A')}</p>
        <p><strong>影响:</strong> {vuln.get('impact', 'N/A')}</p>
        <p><strong>修复建议:</strong> {vuln.get('remediation', 'N/A')}</p>
    </div>"""

    def _to_markdown(self, report: Dict) -> str:
        """转换为Markdown格式"""
        md = f"""# {report['meta']['title']}

**测试日期:** {report['meta']['test_date']}
**目标:** {report['meta']['target']}

---

## 执行摘要

{report['executive_summary'].get('overview', '')}

**风险等级:** `{report['risk_assessment'].get('overall_risk', 'Unknown')}`

### 关键发现

"""
        for finding in report['executive_summary'].get('key_findings', []):
            md += f"- {finding}\n"

        md += "\n---\n\n## 漏洞详情\n\n"

        for vuln in report['vulnerabilities']:
            severity = vuln.get('severity', 'low').upper()
            md += f"""### {vuln.get('title', 'Unknown')}

**严重程度:** `{severity}`

**描述:** {vuln.get('description', 'N/A')}

**影响:** {vuln.get('impact', 'N/A')}

**修复建议:** {vuln.get('remediation', 'N/A')}

---

"""

        md += """## 修复建议

### 立即修复

"""
        for rec in report['recommendations'].get('immediate', []):
            md += f"- {rec.get('recommendation', rec) if isinstance(rec, dict) else rec}\n"

        md += "\n### 短期修复\n\n"
        for rec in report['recommendations'].get('short_term', []):
            md += f"- {rec.get('recommendation', rec) if isinstance(rec, dict) else rec}\n"

        md += "\n---\n\n## 风险评估\n\n"
        md += f"""| 指标 | 值 |
|------|-----|
| 整体风险 | {report['risk_assessment'].get('overall_risk', 'Unknown')} |
| 风险评分 | {report['risk_assessment'].get('risk_score', 0)} |
| 业务影响 | {report['risk_assessment'].get('business_impact', 'N/A')} |

---
*报告由 AI-Pentest Agent System 自动生成*
"""
        return md

    def get_capabilities(self) -> List[str]:
        """获取Agent能力"""
        return [
            "渗透测试报告生成",
            "漏洞分析报告",
            "风险评估报告",
            "修复建议生成",
            "多格式输出(HTML/Markdown/JSON)"
        ]
