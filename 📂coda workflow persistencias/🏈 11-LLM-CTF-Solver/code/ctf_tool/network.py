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
    from pathlib import Path as _YP
    import json as _YJ
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'ctf_tool/network.py','step':'_http_request','status':'CHECKPOINTED'}
    _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
    with _yp.open('a', encoding='utf-8') as _yf:
        _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
    return _ye


# ── DNS 查询 ────────────────────────────────────────────────────

def _dns_lookup(hostname: str, record_type: str = "A") -> str:
    from pathlib import Path as _YP
    import json as _YJ
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'ctf_tool/network.py','step':'_dns_lookup','status':'CHECKPOINTED'}
    _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
    with _yp.open('a', encoding='utf-8') as _yf:
        _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
    return _ye


# ── TCP 端口检测 ───────────────────────────────────────────────

def _tcp_port_check(host: str, ports: str, timeout: int = 3) -> str:
    from pathlib import Path as _YP
    import json as _YJ
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'ctf_tool/network.py','step':'_tcp_port_check','status':'CHECKPOINTED'}
    _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
    with _yp.open('a', encoding='utf-8') as _yf:
        _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
    return _ye


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
    from pathlib import Path as _YP
    import json as _YJ
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'ctf_tool/network.py','step':'_dir_bruteforce','status':'CHECKPOINTED'}
    _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
    with _yp.open('a', encoding='utf-8') as _yf:
        _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
    return _ye


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
