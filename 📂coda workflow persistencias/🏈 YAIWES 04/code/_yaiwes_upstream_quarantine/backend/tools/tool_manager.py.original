"""
工具管理器
统一管理和调度所有安全工具
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import concurrent.futures
from threading import Lock

from .base import BaseTool, ToolResult, ToolCategory, ToolRegistry


@dataclass
class ToolExecutionRecord:
    """工具执行记录"""
    tool_name: str
    target: str
    success: bool
    execution_time: float
    result: ToolResult


class ToolManager:
    """
    工具管理器
    提供工具的统一管理和调度
    """

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self._lock = Lock()
        self._execution_history: List[ToolExecutionRecord] = []

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """获取工具实例"""
        tool_config = self.config.get("tools", {}).get(name, {})
        return ToolRegistry.get_tool(name, tool_config)

    def list_tools(self) -> List[str]:
        """列出所有已注册工具"""
        return ToolRegistry.list_tools()

    def list_available_tools(self) -> List[Dict]:
        """列出所有可用工具及其状态"""
        return ToolRegistry.get_available_tools()

    def get_tools_by_category(self, category: ToolCategory) -> List[BaseTool]:
        """按类别获取工具"""
        return ToolRegistry.get_tools_by_category(category)

    def execute_tool(
        self,
        tool_name: str,
        target: str,
        options: Dict = None
    ) -> ToolResult:
        """
        执行单个工具

        Args:
            tool_name: 工具名称
            target: 目标
            options: 执行选项

        Returns:
            ToolResult
        """
        import time

        tool = self.get_tool(tool_name)
        if not tool:
            return ToolResult(
                success=False,
                error=f"工具 '{tool_name}' 未注册"
            )

        if not tool.is_available():
            return ToolResult(
                success=False,
                error=f"工具 '{tool_name}' 不可用"
            )

        start_time = time.time()

        try:
            result = tool.execute(target, options)
        except Exception as e:
            result = ToolResult(
                success=False,
                error=f"工具执行异常: {str(e)}"
            )

        execution_time = time.time() - start_time

        # 记录执行历史
        record = ToolExecutionRecord(
            tool_name=tool_name,
            target=target,
            success=result.success,
            execution_time=execution_time,
            result=result
        )

        with self._lock:
            self._execution_history.append(record)

        return result

    def execute_tools_parallel(
        self,
        tools_and_targets: List[Dict],
        max_workers: int = 3
    ) -> Dict[str, ToolResult]:
        """
        并行执行多个工具

        Args:
            tools_and_targets: 工具和目标列表
                [{"tool": "nmap", "target": "192.168.1.1", "options": {}}, ...]
            max_workers: 最大并发数

        Returns:
            Dict[str, ToolResult]
        """
        results = {}

        def run_tool(item):
            tool_name = item["tool"]
            target = item["target"]
            options = item.get("options", {})
            return tool_name, self.execute_tool(tool_name, target, options)

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(run_tool, item): item
                for item in tools_and_targets
            }

            for future in concurrent.futures.as_completed(futures):
                try:
                    tool_name, result = future.result()
                    results[tool_name] = result
                except Exception as e:
                    item = futures[future]
                    results[item["tool"]] = ToolResult(
                        success=False,
                        error=str(e)
                    )

        return results

    def get_execution_history(self) -> List[Dict]:
        """获取执行历史"""
        return [
            {
                "tool": record.tool_name,
                "target": record.target,
                "success": record.success,
                "execution_time": record.execution_time
            }
            for record in self._execution_history
        ]

    def clear_history(self):
        """清空执行历史"""
        with self._lock:
            self._execution_history.clear()

    def get_tool_info(self, tool_name: str) -> Optional[Dict]:
        """获取工具信息"""
        tool = self.get_tool(tool_name)
        if tool:
            return tool.get_info()
        return None

    def check_tool_availability(self, tool_name: str) -> Dict:
        """检查工具可用性"""
        tool = self.get_tool(tool_name)
        if not tool:
            return {
                "available": False,
                "reason": "工具未注册"
            }

        info = tool.get_info()
        return {
            "available": info["status"] == "available",
            "status": info["status"],
            "version": info.get("version")
        }

    def get_recommended_tools(self, service: str) -> List[str]:
        """
        根据服务推荐工具

        Args:
            service: 服务名称 (ssh, http, smb, etc.)

        Returns:
            推荐的工具列表
        """
        recommendations = {
            "ssh": ["nmap", "hydra", "searchsploit"],
            "http": ["nmap", "nikto", "dirb", "web_scanner"],
            "https": ["nmap", "nikto", "dirb", "web_scanner"],
            "ftp": ["nmap", "hydra", "searchsploit"],
            "smb": ["nmap", "enum4linux", "searchsploit"],
            "mysql": ["nmap", "hydra", "searchsploit"],
            "rdp": ["nmap", "hydra", "searchsploit"],
            "telnet": ["nmap", "hydra"],
            "smtp": ["nmap", "hydra"],
            "vnc": ["nmap", "hydra"]
        }

        return recommendations.get(service.lower(), ["nmap"])

    # ============================================
    # 便捷方法：为 Agent 提供直接调用接口
    # ============================================

    def get_dns_info(self, target: str) -> Dict:
        """
        获取DNS信息

        Args:
            target: 目标域名或IP

        Returns:
            DNS信息字典
        """
        import socket
        import re

        dns_info = {
            "records": [],
            "a_records": [],
            "mx_records": [],
            "txt_records": [],
            "ns_records": []
        }

        try:
            # 提取域名
            from urllib.parse import urlparse
            if target.startswith("http"):
                parsed = urlparse(target)
                domain = parsed.netloc.split(":")[0]
            else:
                domain = target

            # 如果输入的是IP地址，直接返回
            ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
            if re.match(ip_pattern, domain):
                dns_info["a_records"] = [domain]
                dns_info["records"].append({"type": "A", "value": domain})
                dns_info["note"] = "Input is an IP address, no DNS lookup performed"
                return dns_info

            # 尝试使用 dnspython（如果已安装）
            try:
                import dns.resolver
                import dns.exception

                # A记录
                try:
                    answers = dns.resolver.resolve(domain, 'A')
                    dns_info["a_records"] = [str(rdata) for rdata in answers]
                    dns_info["records"].extend([{"type": "A", "value": str(rdata)} for rdata in answers])
                except dns.exception.DNSException:
                    pass

                # MX记录
                try:
                    answers = dns.resolver.resolve(domain, 'MX')
                    dns_info["mx_records"] = [str(rdata.exchange) for rdata in answers]
                    dns_info["records"].extend([{"type": "MX", "value": str(rdata.exchange)} for rdata in answers])
                except dns.exception.DNSException:
                    pass

                # TXT记录
                try:
                    answers = dns.resolver.resolve(domain, 'TXT')
                    dns_info["txt_records"] = [str(rdata) for rdata in answers]
                    dns_info["records"].extend([{"type": "TXT", "value": str(rdata)} for rdata in answers])
                except dns.exception.DNSException:
                    pass

                # NS记录
                try:
                    answers = dns.resolver.resolve(domain, 'NS')
                    dns_info["ns_records"] = [str(rdata) for rdata in answers]
                    dns_info["records"].extend([{"type": "NS", "value": str(rdata)} for rdata in answers])
                except dns.exception.DNSException:
                    pass

            except ImportError:
                # 使用 socket 作为备用
                try:
                    ip = socket.gethostbyname(domain)
                    dns_info["a_records"] = [ip]
                    dns_info["records"].append({"type": "A", "value": ip})
                except socket.gaierror:
                    dns_info["error"] = f"DNS resolution failed for {domain}"

        except Exception as e:
            dns_info["error"] = str(e)

        return dns_info

    def get_whois_info(self, target: str) -> Dict:
        """
        获取Whois信息

        Args:
            target: 目标域名

        Returns:
            Whois信息字典
        """
        whois_info = {
            "registrar": None,
            "creation_date": None,
            "expiration_date": None,
            "nameservers": [],
            "emails": []
        }

        try:
            import whois

            # 提取域名
            from urllib.parse import urlparse
            if target.startswith("http"):
                parsed = urlparse(target)
                domain = parsed.netloc.split(":")[0]
            else:
                domain = target

            w = whois.whois(domain)

            whois_info["registrar"] = w.registrar
            whois_info["creation_date"] = str(w.creation_date) if w.creation_date else None
            whois_info["expiration_date"] = str(w.expiration_date) if w.expiration_date else None
            whois_info["nameservers"] = w.name_servers if w.name_servers else []
            whois_info["emails"] = w.emails if w.emails else []

        except ImportError:
            whois_info["error"] = "python-whois 未安装，请运行: pip install python-whois"
        except Exception as e:
            whois_info["error"] = str(e)

        return whois_info

    def scan_ports(self, target: str, depth: str = "normal") -> Dict:
        """
        端口扫描

        Args:
            target: 目标IP或域名
            depth: 扫描深度 (quick, normal, deep)

        Returns:
            扫描结果字典
        """
        # 提取主机
        from urllib.parse import urlparse
        if target.startswith("http"):
            parsed = urlparse(target)
            host = parsed.netloc.split(":")[0]
        else:
            host = target

        # 尝试使用 nmap 工具
        nmap_result = self.execute_tool("nmap", host, {"scan_type": depth})

        if nmap_result.success:
            return {
                "open_ports": nmap_result.output.get("open_ports", []),
                "closed_ports": [],
                "filtered_ports": [],
                "services": nmap_result.output.get("services", {})
            }

        # 备用：使用 socket 进行基本端口扫描
        return self._basic_port_scan(host, depth)

    def _basic_port_scan(self, host: str, depth: str = "normal") -> Dict:
        """基本端口扫描（不依赖nmap）"""
        import socket

        # 根据深度选择端口范围
        port_ranges = {
            "quick": [21, 22, 23, 25, 53, 80, 110, 143, 443, 445, 993, 995, 3306, 3389, 5432, 8080, 8443],
            "normal": list(range(1, 1025)),
            "deep": list(range(1, 65536))
        }

        ports_to_scan = port_ranges.get(depth, port_ranges["normal"])
        open_ports = []

        for port in ports_to_scan:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex((host, port))
                if result == 0:
                    # 尝试获取服务名
                    service = self._guess_service_by_port(port)
                    open_ports.append({
                        "port": port,
                        "protocol": "tcp",
                        "service": service,
                        "state": "open"
                    })
                sock.close()
            except Exception:
                pass

        return {
            "open_ports": open_ports,
            "closed_ports": [],
            "filtered_ports": []
        }

    def _guess_service_by_port(self, port: int) -> str:
        """根据端口号猜测服务"""
        service_map = {
            21: "ftp", 22: "ssh", 23: "telnet", 25: "smtp",
            53: "dns", 80: "http", 110: "pop3", 143: "imap",
            443: "https", 445: "smb", 993: "imaps", 995: "pop3s",
            3306: "mysql", 3389: "rdp", 5432: "postgresql",
            6379: "redis", 8080: "http-proxy", 8443: "https-alt"
        }
        return service_map.get(port, "unknown")

    def detect_os(self, target: str) -> Dict:
        """
        操作系统检测

        Args:
            target: 目标IP或域名

        Returns:
            OS信息字典
        """
        # 提取主机
        from urllib.parse import urlparse
        if target.startswith("http"):
            parsed = urlparse(target)
            host = parsed.netloc.split(":")[0]
        else:
            host = target

        # 尝试使用 nmap 的 OS 检测
        nmap_result = self.execute_tool("nmap", host, {
            "scan_type": "quick",
            "os_detection": True
        })

        if nmap_result.success and nmap_result.output.get("os"):
            return nmap_result.output["os"]

        # 返回默认值
        return {
            "family": "Unknown",
            "version": None,
            "confidence": 0
        }

    def scan_web(self, target: str, scan_type: str = "full") -> Dict:
        """
        Web应用扫描

        Args:
            target: 目标URL

        Returns:
            Web扫描结果
        """
        # 确保URL格式正确
        if not target.startswith("http"):
            target = f"http://{target}"

        web_result = self.execute_tool("web_scanner", target, {"scan_type": scan_type})

        if web_result.success:
            return web_result.output

        # 备用：基本HTTP信息收集
        return self._basic_web_scan(target)

    def _basic_web_scan(self, url: str) -> Dict:
        """基本Web扫描（不依赖外部工具）"""
        import requests
        from urllib.parse import urlparse

        web_info = {
            "title": None,
            "server": None,
            "technologies": [],
            "interesting_paths": [],
            "cookies": [],
            "headers": {}
        }

        try:
            response = requests.get(url, timeout=10, verify=False, allow_redirects=True)

            # 获取标题
            import re
            title_match = re.search(r'<title[^>]*>([^<]+)</title>', response.text, re.IGNORECASE)
            if title_match:
                web_info["title"] = title_match.group(1).strip()

            # 获取服务器信息
            web_info["server"] = response.headers.get("Server")
            web_info["headers"] = dict(response.headers)

            # 检测技术栈
            powered_by = response.headers.get("X-Powered-By")
            if powered_by:
                web_info["technologies"].append(powered_by)

            # 获取Cookies
            web_info["cookies"] = [
                {"name": cookie.name, "value": cookie.value[:20] + "..." if len(cookie.value) > 20 else cookie.value}
                for cookie in response.cookies
            ]

            # 检查常见路径
            common_paths = ["/admin", "/login", "/api", "/robots.txt", "/sitemap.xml", "/.git", "/backup"]
            parsed = urlparse(url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"

            for path in common_paths:
                try:
                    check_response = requests.get(f"{base_url}{path}", timeout=5, verify=False)
                    if check_response.status_code in [200, 301, 302, 401, 403]:
                        web_info["interesting_paths"].append({
                            "path": path,
                            "status": check_response.status_code
                        })
                except Exception:
                    pass

        except Exception as e:
            web_info["error"] = str(e)

        return web_info

    def scan_vulnerabilities(self, services: Dict) -> List[Dict]:
        """
        漏洞扫描

        Args:
            services: 服务信息字典

        Returns:
            漏洞列表
        """
        vulnerabilities = []

        # 使用 vulnerability_scanner 工具
        for port, service_info in services.items():
            target = service_info.get("host", "unknown")
            vuln_result = self.execute_tool("vulnerability_scanner", target, {
                "services": {port: service_info}
            })

            if vuln_result.success:
                vulnerabilities.extend(vuln_result.output.get("vulnerabilities", []))

        return vulnerabilities

    def scan_target(self, target: str, scan_type: str = "full") -> Dict:
        """
        综合扫描目标

        Args:
            target: 目标IP/域名
            scan_type: 扫描类型 (quick, full, vuln)

        Returns:
            扫描结果
        """
        results = {
            "target": target,
            "scan_type": scan_type,
            "tools_used": [],
            "findings": {}
        }

        # 1. 端口扫描
        nmap_result = self.execute_tool(
            "nmap",
            target,
            {"scan_type": scan_type}
        )
        results["tools_used"].append("nmap")

        if nmap_result.success:
            results["findings"]["ports"] = nmap_result.output.get("open_ports", [])
            results["findings"]["services"] = nmap_result.output.get("services", {})
            results["findings"]["os"] = nmap_result.output.get("os")

        # 2. Web扫描（如果有HTTP服务）
        web_ports = ["80", "443", "8080", "8443"]
        web_targets = [
            p for p in results["findings"].get("ports", [])
            if p.get("port") in web_ports
        ]

        if web_targets:
            web_result = self.execute_tool(
                "web_scanner",
                f"http://{target}",
                {"scan_type": scan_type}
            )
            results["tools_used"].append("web_scanner")

            if web_result.success:
                results["findings"]["web"] = web_result.output

        # 3. 漏洞扫描
        if scan_type in ["full", "vuln"]:
            vuln_result = self.execute_tool(
                "vulnerability_scanner",
                target,
                {"services": results["findings"].get("services", {})}
            )
            results["tools_used"].append("vulnerability_scanner")

            if vuln_result.success:
                results["findings"]["vulnerabilities"] = vuln_result.output.get(
                    "vulnerabilities", []
                )

        return results
