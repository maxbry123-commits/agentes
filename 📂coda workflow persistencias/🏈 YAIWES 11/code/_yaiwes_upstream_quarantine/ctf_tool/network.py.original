"""网络工具集 — HTTP 请求、DNS 查询、端口检测、目录爆破、WebSocket。"""

import socket
import json
import logging
import re
from typing import Dict, List, Optional
from urllib.parse import urlparse

from ctf_tool.base_tool import BaseTool

logger = logging.getLogger(__name__)

# ── HTTP 请求 ───────────────────────────────────────────────────

try:
    import requests as _requests
except ImportError:
    _requests = None


def _http_request(method: str, url: str, **kwargs) -> str:
    if _requests is None:
        return "错误: 未安装 requests 库"
    try:
        timeout = kwargs.pop("timeout", 15)
        method = method.upper()
        resp = _requests.request(method, url, timeout=timeout,
                                 allow_redirects=True, **kwargs)
        resp.encoding = resp.apparent_encoding or 'utf-8'
        lines = [
            f"HTTP {resp.status_code} {len(resp.content)} bytes",
            f"URL: {resp.url}",
        ]
        # 显示关键响应头
        for h in ("Content-Type", "Server", "Set-Cookie", "Location", "X-Powered-By"):
            if h.lower() in {k.lower(): k for k in resp.headers}:
                actual_key = {k.lower(): k for k in resp.headers}[h.lower()]
                lines.append(f"{h}: {resp.headers[actual_key]}")
        # 显示响应体（可配置截断阈值，默认 16384）
        try:
            from config import Config
            max_chars = Config().get("http_response_max_chars", 16384)
        except Exception:
            max_chars = 16384
        text = resp.text
        if len(text) > max_chars:
            text = text[:max_chars] + "\n... (截断, 共 {} 字节, 阈值={})".format(len(resp.text), max_chars)
        lines.append("")
        lines.append(text)
        return "\n".join(lines)
    except Exception as e:
        return f"HTTP 请求失败: {e}"


# ── DNS 查询 ────────────────────────────────────────────────────

def _dns_lookup(hostname: str, record_type: str = "A") -> str:
    try:
        results = []
        if record_type.upper() in ("A", "AAAA"):
            info = socket.getaddrinfo(hostname, 0)
            seen = set()
            for family, _st, _proto, _cn, sa in info:
                ip = sa[0]
                if ip not in seen:
                    family_name = "IPv6" if family == socket.AF_INET6 else "IPv4"
                    results.append(f"  {family_name}: {ip}")
                    seen.add(ip)
        else:
            results.append(f"  SRV/TXT/MX 查询需要额外库，当前仅支持 A/AAAA 记录")
        if not results:
            return f"DNS 查询无结果: {hostname}"
        return f"DNS {record_type} 记录 for {hostname}:\n" + "\n".join(results)
    except Exception as e:
        return f"DNS 查询失败: {e}"


# ── TCP 端口检测 ───────────────────────────────────────────────

def _tcp_port_check(host: str, ports: str, timeout: int = 3) -> str:
    try:
        port_list = []
        for part in ports.split(","):
            part = part.strip()
            if "-" in part:
                a, b = part.split("-", 1)
                port_list.extend(range(int(a), int(b) + 1))
            else:
                port_list.append(int(part))
        port_list = port_list[:100]  # 最多扫 100 个
        open_ports = []
        for port in port_list:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(timeout)
                result = s.connect_ex((host, port))
                s.close()
                if result == 0:
                    # 尝试读取 banner
                    try:
                        bs = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        bs.settimeout(2)
                        bs.connect((host, port))
                        bs.sendall(b"\r\n")
                        banner = bs.recv(256).decode("utf-8", errors="replace").strip()
                        bs.close()
                        open_ports.append(f"  {port}/tcp  open  {banner[:80]}")
                    except Exception:
                        open_ports.append(f"  {port}/tcp  open")
            except Exception:
                pass
        if not open_ports:
            return f"端口检测完成: 未发现开放端口 (扫描范围: {ports})"
        return f"端口检测完成:\n" + "\n".join(open_ports)
    except Exception as e:
        return f"端口检测失败: {e}"


# ── 目录爆破 ────────────────────────────────────────────────────

_BUILTIN_WORDLIST = [
    "admin", "login", "wp-admin", "administrator", "phpmyadmin",
    "backup", "backups", "bak", "www", "wwwroot", "web", "webroot",
    "api", "v1", "v2", "graphql", "swagger", "docs",
    "config", "configuration", "conf", "cfg",
    "db", "database", "sql", "mysql", "mariadb",
    "index", "index.php", "index.html", "index.htm",
    ".git", ".svn", ".env", "DS_Store", ".htaccess",
    "robots.txt", "sitemap.xml", "crossdomain.xml",
    "upload", "uploads", "download", "downloads",
    "images", "img", "css", "js", "assets", "static",
    "test", "tests", "dev", "debug", "tmp", "temp",
    "shell", "cmd", "command", "exec",
    "flag", "flag.txt", "flag.php", "flag.html",
    "src", "source", "include", "includes",
    "cgi-bin", "server-status", "server-info",
    "xmlrpc.php", "wp-json", "version", "info.php",
    "shell.php", "cmd.php", "eval.php", "upload.php",
]

_COMMON_EXTENSIONS = ["", ".php", ".html", ".htm", ".asp", ".aspx", ".jsp", ".txt", ".json", ".xml"]


def _dir_bruteforce(base_url: str, wordlist: Optional[List[str]] = None,
                    extensions: Optional[List[str]] = None, max_results: int = 30,
                    timeout: int = 5) -> str:
    if _requests is None:
        return "错误: 未安装 requests 库"
    base_url = base_url.rstrip("/")
    words = wordlist or _BUILTIN_WORDLIST
    exts = extensions or _COMMON_EXTENSIONS
    found = []
    try:
        for word in words:
            for ext in exts:
                path = word + ext
                url = f"{base_url}/{path}"
                try:
                    r = _requests.get(url, timeout=timeout, allow_redirects=False)
                    if r.status_code in (200, 301, 302, 401, 403, 500):
                        size = len(r.content)
                        found.append(f"  {r.status_code:3d}  {size:>8}B  {url}")
                        if len(found) >= max_results:
                            break
                except Exception:
                    pass
            if len(found) >= max_results:
                break
        if not found:
            return f"目录爆破完成: 未发现路径 (共检查 {len(words) * len(exts)} 个)"
        return f"目录爆破完成 (发现 {len(found)} 个):\n" + "\n".join(found)
    except Exception as e:
        return f"目录爆破失败: {e}"


# ── 工具类 ──────────────────────────────────────────────────────

class NetworkTool(BaseTool):
    """网络工具 — HTTP 请求、DNS 查询、TCP 端口检测、目录爆破。"""

    @property
    def tags(self):
        return ("web", "network", "scanning")

    def execute(self, tool_name: str, arguments: dict) -> str:
        action = arguments.get("action", "http")
        if action == "http":
            return _http_request(
                method=arguments.get("method", "GET"),
                url=arguments.get("url", ""),
                headers=arguments.get("headers", {}),
                data=arguments.get("data"),
            )
        elif action == "dns":
            return _dns_lookup(
                hostname=arguments.get("hostname", ""),
                record_type=arguments.get("type", "A"),
            )
        elif action == "port_scan":
            return _tcp_port_check(
                host=arguments.get("host", ""),
                ports=arguments.get("ports", "80,443,22,21,3306,6379,8080,8443"),
                timeout=arguments.get("timeout", 3),
            )
        elif action == "dir_brute":
            return _dir_bruteforce(
                base_url=arguments.get("url", ""),
                wordlist=arguments.get("wordlist"),
                extensions=arguments.get("extensions"),
                max_results=arguments.get("max_results", 30),
                timeout=arguments.get("timeout", 5),
            )
        else:
            return f"未知 action: {action}, 可用: http, dns, port_scan, dir_brute"

    @property
    def function_config(self) -> Dict:
        return {
            "type": "function",
            "function": {
                "name": "network_tool",
                "description": (
                    "网络工具。支持: "
                    "1) http — HTTP GET/POST 请求, 返回状态码/响应头/响应体; "
                    "2) dns — DNS A/AAAA 查询; "
                    "3) port_scan — TCP 端口检测, ports 可用逗号和横线组合, 如 '80,443,8000-9000'; "
                    "4) dir_brute — Web 目录爆破, 内置常用路径字典。"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["http", "dns", "port_scan", "dir_brute"],
                            "description": "操作类型",
                        },
                        "url": {
                            "type": "string",
                            "description": "HTTP/目录爆破的目标 URL",
                        },
                        "method": {
                            "type": "string",
                            "enum": ["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS"],
                            "description": "HTTP 方法 (默认 GET)",
                        },
                        "headers": {
                            "type": "object",
                            "description": "HTTP 请求头, JSON 对象格式",
                        },
                        "data": {
                            "type": "string",
                            "description": "HTTP POST 请求体",
                        },
                        "hostname": {
                            "type": "string",
                            "description": "DNS 查询的目标域名",
                        },
                        "type": {
                            "type": "string",
                            "enum": ["A", "AAAA"],
                            "description": "DNS 记录类型 (默认 A)",
                        },
                        "host": {
                            "type": "string",
                            "description": "端口检测的目标主机 IP",
                        },
                        "ports": {
                            "type": "string",
                            "description": "端口范围, 如 '80,443,8000-9000' (最多 100 个)",
                        },
                        "timeout": {
                            "type": "integer",
                            "description": "超时秒数 (默认 3)",
                        },
                        "wordlist": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "自定义目录字典 (可选, 不传则使用内置字典)",
                        },
                        "extensions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "文件后缀列表, 如 ['.php', '.html'] (可选)",
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "最大返回结果数 (默认 30)",
                        },
                    },
                    "required": ["action"],
                },
            },
        }
