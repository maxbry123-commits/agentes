"""
报告生成器
生成渗透测试报告
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import os


class ReportGenerator:
    """
    报告生成器
    支持多种格式输出
    """

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.output_dir = self.config.get("results_dir", "./results")

    def generate(
        self,
        session_data: Dict,
        format: str = "json"
    ) -> str:
        """
        生成报告

        Args:
            session_data: 会话数据
            format: 输出格式 (json, html, markdown)

        Returns:
            报告内容
        """
        embedded_report = (
            session_data.get("results", {})
            .get("report", {})
            .get("data", {})
            .get("report")
            if isinstance(session_data, dict) else None
        )
        if isinstance(embedded_report, dict):
            return self.generate_from_report_data(embedded_report, format)

        if format == "json":
            return self._generate_json(session_data)
        elif format == "html":
            return self._generate_html(session_data)
        elif format == "markdown":
            return self._generate_markdown(session_data)
        else:
            raise ValueError(f"不支持的格式: {format}")

    def generate_from_report_data(self, report: Dict, format: str = "json") -> str:
        """根据 ReportAgent 生成的结构化报告输出不同格式"""
        if format == "json":
            return json.dumps(report, ensure_ascii=False, indent=2)
        if format == "html":
            return self._generate_html_from_report(report)
        if format == "markdown":
            return self._generate_markdown_from_report(report)
        raise ValueError(f"不支持的格式: {format}")

    def _generate_json(self, data: Dict) -> str:
        """生成JSON报告"""
        return json.dumps(data, ensure_ascii=False, indent=2)

    def _generate_html(self, data: Dict) -> str:
        """生成HTML报告"""
        results = data.get("results", {})
        recon = results.get("recon", {}).get("data", {})
        vuln = results.get("vuln", {}).get("data", {})
        exploit = results.get("exploit", {}).get("data", {})

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>渗透测试报告 - {data.get('target', 'Unknown')}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: white;
            padding: 40px 20px;
            text-align: center;
            margin-bottom: 30px;
        }}
        .header h1 {{ font-size: 2.5em; margin-bottom: 10px; }}
        .header .meta {{ opacity: 0.8; font-size: 1.1em; }}
        .card {{
            background: white;
            border-radius: 10px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .card h2 {{
            color: #1a1a2e;
            border-bottom: 3px solid #e94560;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        .severity-critical {{ color: #d32f2f; font-weight: bold; }}
        .severity-high {{ color: #f57c00; font-weight: bold; }}
        .severity-medium {{ color: #fbc02d; font-weight: bold; }}
        .severity-low {{ color: #388e3c; font-weight: bold; }}
        .vuln-item {{
            border-left: 4px solid #e94560;
            padding: 15px;
            margin: 10px 0;
            background: #fafafa;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #1a1a2e;
            color: white;
        }}
        tr:hover {{ background: #f5f5f5; }}
        .risk-meter {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin: 20px 0;
        }}
        .risk-bar {{
            flex: 1;
            height: 30px;
            background: #e0e0e0;
            border-radius: 15px;
            overflow: hidden;
        }}
        .risk-fill {{
            height: 100%;
            border-radius: 15px;
            transition: width 0.5s;
        }}
        .timeline {{
            position: relative;
            padding-left: 30px;
        }}
        .timeline::before {{
            content: '';
            position: absolute;
            left: 10px;
            top: 0;
            bottom: 0;
            width: 2px;
            background: #e94560;
        }}
        .timeline-item {{
            position: relative;
            margin-bottom: 20px;
        }}
        .timeline-item::before {{
            content: '';
            position: absolute;
            left: -24px;
            top: 5px;
            width: 12px;
            height: 12px;
            background: #e94560;
            border-radius: 50%;
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔒 渗透测试报告</h1>
        <div class="meta">
            目标: {data.get('target', 'Unknown')} |
            日期: {data.get('start_time', '')[:10]} |
            状态: {data.get('status', 'Unknown')}
        </div>
    </div>

    <div class="container">
        <!-- 执行摘要 -->
        <div class="card">
            <h2>📋 执行摘要</h2>
            <p>{self._get_executive_summary(data)}</p>
        </div>

        <!-- 信息收集 -->
        <div class="card">
            <h2>🔍 信息收集结果</h2>
            <h3>开放端口</h3>
            {self._generate_ports_html(recon.get('open_ports', []))}
            <h3>服务信息</h3>
            {self._generate_services_html(recon.get('services', {}))}
        </div>

        <!-- 漏洞发现 -->
        <div class="card">
            <h2>🚨 漏洞发现</h2>
            {self._generate_vulns_html(vuln.get('vulnerabilities', []))}
        </div>

        <!-- 利用结果 -->
        <div class="card">
            <h2>⚡ 利用结果</h2>
            {self._generate_exploits_html(exploit)}
        </div>

        <!-- 时间线 -->
        <div class="card">
            <h2>📅 测试时间线</h2>
            <div class="timeline">
                {self._generate_timeline_html(data.get('timeline', []))}
            </div>
        </div>

        <!-- 修复建议 -->
        <div class="card">
            <h2>💡 修复建议</h2>
            {self._generate_recommendations_html(vuln.get('vulnerabilities', []))}
        </div>
    </div>

    <div class="footer">
        <p>报告由 AI-Pentest Agent System 自动生成</p>
        <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
</body>
</html>"""
        return html

    def _generate_markdown(self, data: Dict) -> str:
        """生成Markdown报告"""
        results = data.get("results", {})
        recon = results.get("recon", {}).get("data", {})
        vuln = results.get("vuln", {}).get("data", {})

        md = f"""# 渗透测试报告

**目标:** {data.get('target', 'Unknown')}
**测试日期:** {data.get('start_time', '')[:10]}
**状态:** {data.get('status', 'Unknown')}

---

## 执行摘要

{self._get_executive_summary(data)}

---

## 信息收集结果

### 开放端口

{self._generate_ports_md(recon.get('open_ports', []))}

### 服务信息

{self._generate_services_md(recon.get('services', {}))}

---

## 漏洞发现

{self._generate_vulns_md(vuln.get('vulnerabilities', []))}

---

## 修复建议

{self._generate_recommendations_md(vuln.get('vulnerabilities', []))}

---

## 测试时间线

{self._generate_timeline_md(data.get('timeline', []))}

---

*报告由 AI-Pentest Agent System 自动生成*
*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        return md

    def _get_executive_summary(self, data: Dict) -> str:
        """获取执行摘要"""
        results = data.get("results", {})
        vuln_data = results.get("vuln", {}).get("data", {})
        exploit_data = results.get("exploit", {}).get("data", {})

        vulns = vuln_data.get("vulnerabilities", [])
        successful_exploits = exploit_data.get("results", {}).get("successful", [])

        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for vuln in vulns:
            severity = vuln.get("severity", "low").lower()
            if severity in severity_counts:
                severity_counts[severity] += 1

        return f"""本次渗透测试针对目标 {data.get('target', 'Unknown')} 进行。
测试共发现 {len(vulns)} 个安全漏洞，其中：
- 严重漏洞: {severity_counts['critical']} 个
- 高危漏洞: {severity_counts['high']} 个
- 中危漏洞: {severity_counts['medium']} 个
- 低危漏洞: {severity_counts['low']} 个

成功利用漏洞: {len(successful_exploits)} 个

建议尽快修复高危和严重漏洞，以降低安全风险。"""

    def _generate_ports_html(self, ports: List) -> str:
        """生成端口HTML"""
        if not ports:
            return "<p>未发现开放端口</p>"

        rows = ""
        for port in ports[:20]:
            rows += f"""
                <tr>
                    <td>{port.get('port', 'N/A')}</td>
                    <td>{port.get('protocol', 'tcp')}</td>
                    <td>{port.get('service', 'unknown')}</td>
                    <td>{port.get('version', 'N/A')}</td>
                </tr>"""

        return f"""
            <table>
                <tr><th>端口</th><th>协议</th><th>服务</th><th>版本</th></tr>
                {rows}
            </table>"""

    def _generate_services_html(self, services: Dict) -> str:
        """生成服务HTML"""
        if not services:
            return "<p>未识别到服务信息</p>"

        rows = ""
        for port, info in list(services.items())[:15]:
            rows += f"""
                <tr>
                    <td>{port}</td>
                    <td>{info.get('name', 'unknown')}</td>
                    <td>{info.get('version', 'N/A')}</td>
                    <td>{info.get('banner', 'N/A')[:50]}</td>
                </tr>"""

        return f"""
            <table>
                <tr><th>端口</th><th>服务</th><th>版本</th><th>Banner</th></tr>
                {rows}
            </table>"""

    def _generate_vulns_html(self, vulns: List) -> str:
        """生成漏洞HTML"""
        if not vulns:
            return "<p>未发现漏洞</p>"

        html = ""
        for vuln in vulns[:15]:
            severity = vuln.get("severity", "low").lower()
            html += f"""
            <div class="vuln-item">
                <h3 class="severity-{severity}">{vuln.get('name', 'Unknown')}</h3>
                <p><strong>严重程度:</strong> <span class="severity-{severity}">{severity.upper()}</span></p>
                <p><strong>CVE:</strong> {vuln.get('cve', 'N/A')}</p>
                <p><strong>描述:</strong> {vuln.get('description', 'N/A')}</p>
            </div>"""

        return html

    def _generate_exploits_html(self, exploit_data: Dict) -> str:
        """生成利用结果HTML"""
        successful = exploit_data.get("results", {}).get("successful", [])

        if not successful:
            return "<p>未成功利用漏洞</p>"

        html = "<ul>"
        for exp in successful:
            html += f"<li>{exp.get('step', 'Unknown')}: <strong class='severity-high'>成功</strong></li>"
        html += "</ul>"

        return html

    def _generate_timeline_html(self, timeline: List) -> str:
        """生成时间线HTML"""
        if not timeline:
            return "<p>无时间线记录</p>"

        html = ""
        for event in timeline:
            html += f"""
            <div class="timeline-item">
                <strong>{event.get('phase', 'Unknown')}</strong>
                <span style="color: #666; font-size: 0.9em;"> - {event.get('timestamp', '')}</span>
                <p>{event.get('description', '')}</p>
            </div>"""

        return html

    def _generate_recommendations_html(self, vulns: List) -> str:
        """生成修复建议HTML"""
        high_vulns = [v for v in vulns if v.get("severity", "").lower() in ["critical", "high"]]

        if not high_vulns:
            return "<p>无高危漏洞需要紧急修复</p>"

        html = "<ol>"
        for vuln in high_vulns[:10]:
            html += f"""
            <li>
                <strong>{vuln.get('name', 'Unknown')}</strong>
                <p>修复建议: {vuln.get('remediation', '请参考相关安全公告进行修复')}</p>
            </li>"""
        html += "</ol>"

        return html

    def _generate_ports_md(self, ports: List) -> str:
        """生成端口Markdown"""
        if not ports:
            return "未发现开放端口"

        md = "| 端口 | 协议 | 服务 | 版本 |\n|------|------|------|------|\n"
        for port in ports[:15]:
            md += f"| {port.get('port', 'N/A')} | {port.get('protocol', 'tcp')} | {port.get('service', 'unknown')} | {port.get('version', 'N/A')} |\n"
        return md

    def _generate_services_md(self, services: Dict) -> str:
        """生成服务Markdown"""
        if not services:
            return "未识别到服务信息"

        md = "| 端口 | 服务 | 版本 |\n|------|------|------|\n"
        for port, info in list(services.items())[:15]:
            md += f"| {port} | {info.get('name', 'unknown')} | {info.get('version', 'N/A')} |\n"
        return md

    def _generate_vulns_md(self, vulns: List) -> str:
        """生成漏洞Markdown"""
        if not vulns:
            return "未发现漏洞"

        md = ""
        for vuln in vulns[:15]:
            severity = vuln.get("severity", "low").upper()
            md += f"""
### {vuln.get('name', 'Unknown')}

- **严重程度:** `{severity}`
- **CVE:** {vuln.get('cve', 'N/A')}
- **描述:** {vuln.get('description', 'N/A')}

"""
        return md

    def _generate_recommendations_md(self, vulns: List) -> str:
        """生成修复建议Markdown"""
        high_vulns = [v for v in vulns if v.get("severity", "").lower() in ["critical", "high"]]

        if not high_vulns:
            return "无高危漏洞需要紧急修复"

        md = ""
        for i, vuln in enumerate(high_vulns[:10], 1):
            md += f"{i}. **{vuln.get('name', 'Unknown')}**\n   - 修复建议: {vuln.get('remediation', '请参考相关安全公告')}\n\n"
        return md

    def _generate_timeline_md(self, timeline: List) -> str:
        """生成时间线Markdown"""
        if not timeline:
            return "无时间线记录"

        md = "| 时间 | 阶段 | 描述 |\n|------|------|------|\n"
        for event in timeline:
            md += f"| {event.get('timestamp', '')} | {event.get('phase', 'Unknown')} | {event.get('description', '')} |\n"
        return md

    def save_report(
        self,
        content: Any,
        filename: str,
        format: str = "json"
    ) -> str:
        """保存报告到文件"""
        os.makedirs(self.output_dir, exist_ok=True)

        extension = {"json": "json", "html": "html", "markdown": "md"}.get(format, "txt")
        filepath = os.path.join(self.output_dir, f"{filename}.{extension}")

        with open(filepath, 'w', encoding='utf-8') as f:
            if isinstance(content, (dict, list)):
                f.write(json.dumps(content, ensure_ascii=False, indent=2))
            else:
                f.write(str(content))

        return filepath

    def _generate_html_from_report(self, report: Dict) -> str:
        """将结构化报告渲染为 HTML"""
        exec_summary = report.get("executive_summary", {})
        risk = report.get("risk_assessment", {})
        recs = report.get("recommendations", {})
        vuln_cards = "".join(self._report_vuln_to_html(v) for v in report.get("vulnerabilities", []))
        key_findings = "".join(f"<li>{item}</li>" for item in exec_summary.get("key_findings", []))
        immediate = "".join(
            f"<li>{item.get('recommendation', item) if isinstance(item, dict) else item}</li>"
            for item in recs.get("immediate", [])
        )
        short_term = "".join(
            f"<li>{item.get('recommendation', item) if isinstance(item, dict) else item}</li>"
            for item in recs.get("short_term", [])
        )
        flags = "".join(f"<li>{flag}</li>" for flag in report.get("appendix", {}).get("validated_flags", []))

        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>{report.get('meta', {}).get('title', '渗透测试报告')}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; color: #222; }}
        h1 {{ color: #111827; }}
        h2 {{ color: #374151; border-bottom: 2px solid #e5e7eb; padding-bottom: 8px; }}
        .critical {{ color: #dc2626; }}
        .high {{ color: #ea580c; }}
        .medium {{ color: #ca8a04; }}
        .low {{ color: #16a34a; }}
        .info {{ color: #0284c7; }}
        .card {{ border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px; margin: 12px 0; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 12px; }}
        th, td {{ border: 1px solid #e5e7eb; padding: 10px; text-align: left; vertical-align: top; }}
        th {{ background: #f8fafc; }}
        code {{ background: #f3f4f6; padding: 2px 4px; border-radius: 4px; }}
    </style>
</head>
<body>
    <h1>{report.get('meta', {}).get('title', '渗透测试报告')}</h1>
    <p><strong>目标:</strong> {report.get('meta', {}).get('target', 'Unknown')}</p>
    <p><strong>测试日期:</strong> {report.get('meta', {}).get('test_date', '')}</p>
    <h2>执行摘要</h2>
    <p>{exec_summary.get('overview', '')}</p>
    <p><strong>整体风险:</strong> <span class="{risk.get('overall_risk', 'low')}">{risk.get('overall_risk', 'unknown')}</span></p>
    <ul>{key_findings}</ul>
    <h2>漏洞详情</h2>
    {vuln_cards or '<p>未发现漏洞</p>'}
    <h2>风险评估</h2>
    <table>
        <tr><th>指标</th><th>值</th></tr>
        <tr><td>整体风险</td><td>{risk.get('overall_risk', 'unknown')}</td></tr>
        <tr><td>风险评分</td><td>{risk.get('risk_score', 0)}</td></tr>
        <tr><td>业务影响</td><td>{risk.get('business_impact', '')}</td></tr>
        <tr><td>受影响资产</td><td>{', '.join(risk.get('affected_assets', []))}</td></tr>
    </table>
    <h2>修复建议</h2>
    <h3>立即修复</h3>
    <ul>{immediate or '<li>无</li>'}</ul>
    <h3>短期修复</h3>
    <ul>{short_term or '<li>无</li>'}</ul>
    <h2>已验证 Flag</h2>
    <ul>{flags or '<li>无</li>'}</ul>
</body>
</html>"""

    def _generate_markdown_from_report(self, report: Dict) -> str:
        """将结构化报告渲染为 Markdown"""
        exec_summary = report.get("executive_summary", {})
        risk = report.get("risk_assessment", {})
        recs = report.get("recommendations", {})
        lines = [
            f"# {report.get('meta', {}).get('title', '渗透测试报告')}",
            "",
            f"**目标:** {report.get('meta', {}).get('target', 'Unknown')}",
            f"**测试日期:** {report.get('meta', {}).get('test_date', '')}",
            "",
            "## 执行摘要",
            "",
            exec_summary.get("overview", ""),
            "",
            f"**整体风险:** `{risk.get('overall_risk', 'unknown')}`",
            "",
            "### 关键发现",
            "",
        ]
        for item in exec_summary.get("key_findings", []):
            lines.append(f"- {item}")
        lines.extend(["", "## 漏洞详情", ""])
        vulnerabilities = report.get("vulnerabilities", [])
        if vulnerabilities:
            for vuln in vulnerabilities:
                lines.extend([
                    f"### {vuln.get('title', vuln.get('name', 'Unknown'))}",
                    "",
                    f"- **严重程度:** `{vuln.get('severity', 'unknown')}`",
                    f"- **位置:** {vuln.get('location', 'Unknown')}",
                    f"- **描述:** {vuln.get('description', '')}",
                    f"- **证据:** {vuln.get('evidence', '')}",
                    f"- **修复建议:** {vuln.get('remediation', '')}",
                    "",
                ])
        else:
            lines.append("未发现漏洞")
            lines.append("")
        lines.extend(["## 修复建议", "", "### 立即修复", ""])
        for item in recs.get("immediate", []) or ["无"]:
            text = item.get("recommendation", item) if isinstance(item, dict) else item
            lines.append(f"- {text}")
        lines.extend(["", "### 短期修复", ""])
        for item in recs.get("short_term", []) or ["无"]:
            text = item.get("recommendation", item) if isinstance(item, dict) else item
            lines.append(f"- {text}")
        lines.extend(["", "## 已验证 Flag", ""])
        for flag in report.get("appendix", {}).get("validated_flags", []) or ["无"]:
            lines.append(f"- `{flag}`" if flag != "无" else "- 无")
        return "\n".join(lines)

    def _report_vuln_to_html(self, vuln: Dict) -> str:
        severity = vuln.get("severity", "low").lower()
        steps = "".join(f"<li>{step}</li>" for step in vuln.get("remediation_steps", []))
        return f"""
    <div class="card">
        <h3 class="{severity}">{vuln.get('title', vuln.get('name', 'Unknown Vulnerability'))}</h3>
        <p><strong>严重程度:</strong> <span class="{severity}">{severity}</span></p>
        <p><strong>位置:</strong> {vuln.get('location', 'Unknown')}</p>
        <p><strong>描述:</strong> {vuln.get('description', '')}</p>
        <p><strong>证据:</strong> {vuln.get('evidence', '')}</p>
        <p><strong>影响:</strong> {vuln.get('impact', '')}</p>
        <p><strong>修复建议:</strong> {vuln.get('remediation', '')}</p>
        <ul>{steps}</ul>
    </div>"""
