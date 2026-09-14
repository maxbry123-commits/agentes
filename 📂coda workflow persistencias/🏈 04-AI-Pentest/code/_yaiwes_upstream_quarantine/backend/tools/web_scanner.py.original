"""
Web应用扫描工具
集成Nikto、Dirb、WhatWeb等Web安全扫描工具
"""
from typing import Dict, List, Optional, Any
import re
from .base import BaseTool, ToolResult, ToolCategory, ToolInfo, ToolRegistry
import subprocess


@ToolRegistry.register
class WebScanner(BaseTool):
    """
    Web应用扫描器
    集成多种Web扫描工具
    """

    TOOL_INFO = ToolInfo(
        name="web_scanner",
        category=ToolCategory.WEB,
        description="Web应用安全扫描工具集",
        executable="nikto"
    )

    def __init__(self, config: Dict = None):
        super().__init__(config)
        self.timeout = config.get("timeout", 300) if config else 300

    def execute(self, target: str, options: Dict = None) -> ToolResult:
        """
        执行Web扫描

        Args:
            target: 目标URL
            options: 扫描选项
        """
        options = options or {}
        scan_type = options.get("scan_type", "full")

        results = {}

        # 1. 使用WhatWeb进行技术识别
        tech_result = self._scan_technologies(target)
        results["technologies"] = tech_result

        # 2. 使用Nikto进行漏洞扫描
        if scan_type in ["full", "vuln"]:
            vuln_result = self._scan_vulnerabilities(target)
            results["vulnerabilities"] = vuln_result

        # 3. 目录枚举
        if scan_type in ["full", "directory"]:
            dir_result = self._scan_directories(target)
            results["directories"] = dir_result

        # 4. HTTP安全头检查
        headers_result = self._check_security_headers(target)
        results["security_headers"] = headers_result

        return ToolResult(
            success=True,
            output=results,
            metadata={"target": target, "scan_type": scan_type}
        )

    def _scan_technologies(self, url: str) -> Dict:
        """使用WhatWeb识别Web技术"""
        result = {"technologies": [], "server": None, "title": None}

        if not shutil.which("whatweb"):
            return result

        try:
            proc = subprocess.run(
                ["whatweb", "--color=never", "--log-json=/dev/stdout", url],
                capture_output=True,
                text=True,
                timeout=60
            )

            # 解析输出
            output = proc.stdout
            # WhatWeb输出较复杂，简化解析
            tech_patterns = [
                r'([A-Z][a-zA-Z]+(?:\s+\d+(?:\.\d+)*)?)'
            ]

            for pattern in tech_patterns:
                matches = re.findall(pattern, output)
                for match in matches:
                    if match not in result["technologies"]:
                        result["technologies"].append(match)

        except Exception:
            pass

        return result

    def _scan_vulnerabilities(self, url: str) -> List[Dict]:
        """使用Nikto扫描Web漏洞"""
        vulns = []

        if not shutil.which("nikto"):
            return vulns

        try:
            proc = subprocess.run(
                ["nikto", "-h", url, "-Format", "json", "-output", "-"],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            # 解析Nikto JSON输出
            try:
                data = json.loads(proc.stdout)
                for item in data.get("vulnerabilities", []):
                    vulns.append({
                        "id": item.get("id"),
                        "OSVDB": item.get("OSVDB"),
                        "method": item.get("method"),
                        "uri": item.get("uri"),
                        "msg": item.get("msg"),
                        "severity": self._assess_nikto_severity(item.get("msg", ""))
                    })
            except json.JSONDecodeError:
                # 尝试解析文本输出
                for line in proc.stdout.split('\n'):
                    if '+ ' in line and 'OSVDB' in line:
                        vulns.append({
                            "description": line.strip(),
                            "severity": "medium"
                        })

        except Exception:
            pass

        return vulns

    def _scan_directories(self, url: str) -> List[Dict]:
        """使用Dirb进行目录枚举"""
        dirs = []

        if not shutil.which("dirb"):
            return dirs

        wordlist = self.config.get(
            "wordlist",
            "/usr/share/wordlists/dirb/common.txt"
        ) if self.config else "/usr/share/wordlists/dirb/common.txt"

        try:
            proc = subprocess.run(
                ["dirb", url, wordlist, "-N", "404", "-S", "-w"],
                capture_output=True,
                text=True,
                timeout=300
            )

            # 解析Dirb输出
            for line in proc.stdout.split('\n'):
                # 匹配找到的目录
                match = re.match(r'\+\s+(http[s]?://\S+)\s+\(Code:\s*(\d+)\)', line)
                if match:
                    found_url, code = match.groups()
                    dirs.append({
                        "url": found_url,
                        "status_code": int(code),
                        "type": "directory" if code == "301" else "file"
                    })

        except Exception:
            pass

        return dirs

    def _check_security_headers(self, url: str) -> Dict:
        """检查HTTP安全头"""
        import requests

        headers_status = {
            "present": [],
            "missing": [],
            "issues": []
        }

        important_headers = [
            "X-Frame-Options",
            "X-Content-Type-Options",
            "X-XSS-Protection",
            "Content-Security-Policy",
            "Strict-Transport-Security",
            "Referrer-Policy",
            "Permissions-Policy"
        ]

        try:
            response = requests.head(url, timeout=10, verify=False)

            for header in important_headers:
                if header in response.headers:
                    headers_status["present"].append({
                        "header": header,
                        "value": response.headers[header]
                    })
                else:
                    headers_status["missing"].append(header)

            # 检查Server头泄露
            if "Server" in response.headers:
                server = response.headers["Server"]
                if any(v in server.lower() for v in ["apache", "nginx", "iis"]):
                    headers_status["issues"].append({
                        "issue": "Server version disclosure",
                        "header": "Server",
                        "value": server
                    })

            # 检查Powered-By头
            if "X-Powered-By" in response.headers:
                headers_status["issues"].append({
                    "issue": "Technology disclosure",
                    "header": "X-Powered-By",
                    "value": response.headers["X-Powered-By"]
                })

        except Exception:
            pass

        return headers_status

    def _assess_nikto_severity(self, msg: str) -> str:
        """评估Nikto发现的严重程度"""
        critical_keywords = ["sql injection", "rce", "remote code", "file upload"]
        high_keywords = ["xss", "csrf", "disclosure", "exposure", "unauthorized"]

        msg_lower = msg.lower()

        for kw in critical_keywords:
            if kw in msg_lower:
                return "critical"

        for kw in high_keywords:
            if kw in msg_lower:
                return "high"

        return "medium"

    def parse_output(self, raw_output: str) -> Any:
        """解析输出（由各子方法实现）"""
        return {"raw": raw_output}


@ToolRegistry.register
class NiktoScanner(BaseTool):
    """Nikto Web漏洞扫描器"""

    TOOL_INFO = ToolInfo(
        name="nikto",
        category=ToolCategory.WEB,
        description="Web服务器漏洞扫描器",
        executable="nikto",
        install_command="apt install nikto -y"
    )

    def execute(self, target: str, options: Dict = None) -> ToolResult:
        """执行Nikto扫描"""
        options = options or {}

        if not self.is_available():
            return ToolResult(success=False, error="Nikto不可用")

        command = ["nikto", "-h", target]

        if options.get("ssl"):
            command.append("-ssl")
        if options.get("port"):
            command.extend(["-p", str(options["port"])])

        command.extend(["-Format", "json", "-output", "-"])

        try:
            result = self._run_command(command, timeout=options.get("timeout", 300))
            parsed = self.parse_output(result.stdout)

            return ToolResult(
                success=True,
                output=parsed,
                raw_output=result.stdout
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    def parse_output(self, raw_output: str) -> Dict:
        """解析Nikto JSON输出"""
        import json

        result = {
            "vulnerabilities": [],
            "statistics": {}
        }

        try:
            data = json.loads(raw_output)

            for vuln in data.get("vulnerabilities", []):
                result["vulnerabilities"].append({
                    "osvdb": vuln.get("OSVDB"),
                    "method": vuln.get("method"),
                    "uri": vuln.get("uri"),
                    "description": vuln.get("msg"),
                    "severity": self._get_severity(vuln.get("OSVDB", ""))
                })

        except json.JSONDecodeError:
            # 解析文本输出
            for line in raw_output.split('\n'):
                if '+ ' in line:
                    result["vulnerabilities"].append({
                        "description": line.strip('+ ').strip(),
                        "severity": "info"
                    })

        return result

    def _get_severity(self, osvdb: str) -> str:
        """根据OSVDB ID评估严重程度"""
        # 简化处理，实际应根据OSVDB数据库查询
        return "medium"


@ToolRegistry.register
class DirbScanner(BaseTool):
    """Dirb目录扫描器"""

    TOOL_INFO = ToolInfo(
        name="dirb",
        category=ToolCategory.WEB,
        description="Web内容扫描器",
        executable="dirb",
        install_command="apt install dirb -y"
    )

    def execute(self, target: str, options: Dict = None) -> ToolResult:
        """执行Dirb扫描"""
        options = options or {}
        wordlist = options.get(
            "wordlist",
            "/usr/share/wordlists/dirb/common.txt"
        )

        if not self.is_available():
            return ToolResult(success=False, error="Dirb不可用")

        command = ["dirb", target, wordlist, "-S", "-w"]

        if options.get("extensions"):
            command.extend(["-X", options["extensions"]])

        try:
            result = self._run_command(command, timeout=options.get("timeout", 600))
            parsed = self.parse_output(result.stdout)

            return ToolResult(
                success=True,
                output=parsed,
                raw_output=result.stdout
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    def parse_output(self, raw_output: str) -> Dict:
        """解析Dirb输出"""
        result = {
            "found": [],
            "directories": [],
            "files": []
        }

        for line in raw_output.split('\n'):
            # 匹配发现的URL
            match = re.match(r'\+\s+(http[s]?://\S+)\s+\(Code:\s*(\d+)\)', line)
            if match:
                url, code = match.groups()
                item = {
                    "url": url,
                    "status_code": int(code)
                }
                result["found"].append(item)

                if code in ["301", "302"]:
                    result["directories"].append(item)
                else:
                    result["files"].append(item)

        return result


# 需要导入
import shutil
import json
