"""
网络扫描工具
集成Nmap、Masscan等网络扫描工具
"""
from typing import Dict, List, Optional, Any
import re
import json
import xml.etree.ElementTree as ET
from .base import BaseTool, ToolResult, ToolCategory, ToolInfo, ToolRegistry


@ToolRegistry.register
class NetworkScanner(BaseTool):
    """
    网络扫描工具
    使用Nmap进行端口扫描、服务识别、OS检测
    """

    TOOL_INFO = ToolInfo(
        name="nmap",
        category=ToolCategory.NETWORK,
        description="网络发现和安全审计工具",
        executable="nmap",
        install_command="apt install nmap -y",
        documentation_url="https://nmap.org/docs.html"
    )

    # 端口服务映射
    COMMON_PORTS = {
        "21": "ftp", "22": "ssh", "23": "telnet", "25": "smtp",
        "53": "dns", "80": "http", "110": "pop3", "139": "netbios",
        "143": "imap", "443": "https", "445": "smb", "993": "imaps",
        "995": "pop3s", "3306": "mysql", "3389": "rdp", "5432": "postgresql",
        "5900": "vnc", "6379": "redis", "8080": "http-proxy", "8443": "https-alt"
    }

    def __init__(self, config: Dict = None):
        super().__init__(config)
        self.timing = config.get("timing", "T4") if config else "T4"
        self.default_args = config.get("default_args", "-sV -sC") if config else "-sV -sC"

    def execute(self, target: str, options: Dict = None) -> ToolResult:
        """
        执行网络扫描

        Args:
            target: 目标IP或CIDR
            options: 扫描选项
                - scan_type: 扫描类型 (quick, full, vuln)
                - ports: 指定端口
                - scripts: NSE脚本
                - os_detection: OS检测
        """
        options = options or {}
        scan_type = options.get("scan_type", "quick")

        if not self.is_available():
            return ToolResult(
                success=False,
                error=f"工具 {self.TOOL_INFO.name} 不可用"
            )

        # 构建命令
        command = self._build_command(target, scan_type, options)

        try:
            result = self._run_command(command, timeout=options.get("timeout", 600))
            parsed = self.parse_output(result.stdout)

            return ToolResult(
                success=True,
                output=parsed,
                raw_output=result.stdout,
                metadata={"command": " ".join(command)}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e)
            )

    def _build_command(self, target: str, scan_type: str, options: Dict) -> List[str]:
        """构建Nmap命令"""
        command = ["nmap"]

        # 扫描类型
        if scan_type == "quick":
            command.extend(["-T4", "-F"])  # 快速扫描，常用端口
        elif scan_type == "full":
            command.extend(["-T4", "-p-"])  # 全端口扫描
        elif scan_type == "vuln":
            command.extend(["-T4", "-sV", "--script=vuln"])  # 漏洞扫描
        elif scan_type == "service":
            command.extend(["-T4", "-sV", "-sC"])  # 服务版本检测
        else:
            command.extend(["-T4", "-F"])

        # 自定义端口
        if options.get("ports"):
            command.extend(["-p", options["ports"]])

        # OS检测
        if options.get("os_detection"):
            command.append("-O")

        # 自定义脚本
        if options.get("scripts"):
            command.extend(["--script", options["scripts"]])

        # 输出格式
        command.extend(["-oX", "-"])  # XML输出到stdout

        command.append(target)
        return command

    def parse_output(self, raw_output: str) -> Dict:
        """解析Nmap输出"""
        result = {
            "hosts": [],
            "open_ports": [],
            "services": {},
            "os": None,
            "summary": {}
        }

        try:
            # 尝试解析XML输出
            root = ET.fromstring(raw_output)

            for host in root.findall(".//host"):
                host_info = self._parse_host(host)
                result["hosts"].append(host_info)

                # 收集开放端口
                for port in host_info.get("ports", []):
                    if port.get("state") == "open":
                        result["open_ports"].append({
                            "port": port["port"],
                            "protocol": port["protocol"],
                            "service": port.get("service", "unknown"),
                            "version": port.get("version", ""),
                            "banner": port.get("banner", "")
                        })

                # 收集OS信息
                if host_info.get("os"):
                    result["os"] = host_info["os"]

        except ET.ParseError:
            # 如果不是XML，尝试解析文本输出
            result = self._parse_text_output(raw_output)

        # 生成摘要
        result["summary"] = {
            "total_hosts": len(result["hosts"]),
            "total_open_ports": len(result["open_ports"]),
            "unique_services": list(set(
                p["service"] for p in result["open_ports"] if p["service"] != "unknown"
            ))
        }

        return result

    def _parse_host(self, host_elem) -> Dict:
        """解析单个主机信息"""
        host_info = {
            "address": None,
            "hostname": None,
            "ports": [],
            "os": None,
            "status": None
        }

        # 地址
        addr = host_elem.find("address[@addrtype='ipv4']")
        if addr is not None:
            host_info["address"] = addr.get("addr")

        # 主机名
        hostname = host_elem.find(".//hostname")
        if hostname is not None:
            host_info["hostname"] = hostname.get("name")

        # 状态
        status = host_elem.find("status")
        if status is not None:
            host_info["status"] = status.get("state")

        # 端口
        for port in host_elem.findall(".//port"):
            port_info = {
                "port": port.get("portid"),
                "protocol": port.get("protocol"),
                "state": port.find("state").get("state") if port.find("state") is not None else "unknown"
            }

            # 服务信息
            service = port.find("service")
            if service is not None:
                port_info["service"] = service.get("name", "unknown")
                port_info["version"] = service.get("version", "")
                port_info["product"] = service.get("product", "")

            # 脚本输出
            for script in port.findall(".//script"):
                if "banner" in script.get("id", "").lower():
                    port_info["banner"] = script.get("output", "")

            host_info["ports"].append(port_info)

        # OS检测
        os_match = host_elem.find(".//osmatch")
        if os_match is not None:
            host_info["os"] = {
                "name": os_match.get("name"),
                "accuracy": os_match.get("accuracy")
            }

        return host_info

    def _parse_text_output(self, output: str) -> Dict:
        """解析文本格式的输出"""
        result = {
            "hosts": [],
            "open_ports": [],
            "services": {},
            "os": None,
            "summary": {}
        }

        lines = output.split('\n')
        current_host = None

        for line in lines:
            # 匹配开放端口
            port_match = re.match(
                r'(\d+)/(tcp|udp)\s+open\s+(\S+)(?:\s+(.+))?',
                line.strip()
            )
            if port_match:
                port, proto, service, extra = port_match.groups()
                port_info = {
                    "port": port,
                    "protocol": proto,
                    "service": service,
                    "state": "open",
                    "version": extra or ""
                }
                result["open_ports"].append(port_info)

            # 匹配OS
            os_match = re.search(r'OS details: (.+)', line)
            if os_match:
                result["os"] = {"name": os_match.group(1), "accuracy": "unknown"}

        return result

    def scan_ports(self, target: str, depth: str = "normal") -> Dict:
        """
        便捷方法：端口扫描

        Args:
            target: 目标IP
            depth: 扫描深度 (quick, normal, deep)
        """
        scan_types = {
            "quick": "quick",
            "normal": "service",
            "deep": "full"
        }

        result = self.execute(target, {
            "scan_type": scan_types.get(depth, "service")
        })

        if result.success:
            return result.output
        return {"open_ports": [], "error": result.error}

    def detect_os(self, target: str) -> Dict:
        """便捷方法：操作系统检测"""
        result = self.execute(target, {
            "scan_type": "quick",
            "os_detection": True
        })

        if result.success:
            return result.output.get("os", {})
        return {"error": result.error}

    def scan_vulns(self, target: str) -> Dict:
        """便捷方法：漏洞扫描"""
        result = self.execute(target, {
            "scan_type": "vuln"
        })
        return result.to_dict()


@ToolRegistry.register
class MasscanScanner(BaseTool):
    """Masscan快速端口扫描"""

    TOOL_INFO = ToolInfo(
        name="masscan",
        category=ToolCategory.NETWORK,
        description="快速互联网端口扫描器",
        executable="masscan",
        install_command="apt install masscan -y"
    )

    def __init__(self, config: Dict = None):
        super().__init__(config)
        self.rate = config.get("rate", 1000) if config else 1000

    def execute(self, target: str, options: Dict = None) -> ToolResult:
        """执行Masscan扫描"""
        options = options or {}
        ports = options.get("ports", "1-65535")
        rate = options.get("rate", self.rate)

        if not self.is_available():
            return ToolResult(success=False, error="Masscan不可用")

        command = [
            "masscan",
            target,
            "-p", ports,
            "--rate", str(rate),
            "-oL", "-"  # 文本输出
        ]

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
        """解析Masscan输出"""
        result = {"open_ports": []}

        for line in raw_output.split('\n'):
            # 格式: open port 80/tcp on 192.168.1.1
            match = re.match(r'open\s+port\s+(\d+)/(tcp|udp)\s+on\s+(\S+)', line)
            if match:
                port, proto, ip = match.groups()
                result["open_ports"].append({
                    "port": port,
                    "protocol": proto,
                    "address": ip,
                    "service": self._guess_service(port)
                })

        return result

    def _guess_service(self, port: str) -> str:
        """根据端口号猜测服务"""
        return NetworkScanner.COMMON_PORTS.get(port, "unknown")
