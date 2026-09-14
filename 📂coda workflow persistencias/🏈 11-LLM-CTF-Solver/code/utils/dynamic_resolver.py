"""动态工具解析器 — 根据用户反馈中的工具名：
1. 通过 SSH 检索远程服务器上的工具是否存在
2. 动态懒加载已配置但尚未连接的 MCP 服务

用法:
    resolver = DynamicToolResolver(ssh_config)
    configs = resolver.resolve(["nmap", "sqlmap", "burpsuite"])
    # configs 包含能在远程服务器上找到的工具的 function_config
"""

import re
import logging
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)

# 常见渗透测试工具名 → 命令行调用名映射
# 注意: GUI 工具 (burpsuite/wireshark/ghidra) 不在此列表中 — 它们通过 MCP 加载
_KNOWN_TOOLS: Dict[str, str] = {
    # Web 测试
    "sqlmap": "sqlmap",
    "dirb": "dirb",
    "gobuster": "gobuster",
    "ffuf": "ffuf",
    "wfuzz": "wfuzz",
    "nikto": "nikto",
    "whatweb": "whatweb",
    "wpscan": "wpscan",
    "joomscan": "joomscan",
    "droopescan": "droopescan",
    # 网络扫描
    "nmap": "nmap",
    "masscan": "masscan",
    "rustscan": "rustscan",
    "netcat": "nc",
    "nc": "nc",
    "socat": "socat",
    # 漏洞利用
    "metasploit": "msfconsole",
    "msf": "msfconsole",
    "msfvenom": "msfvenom",
    "searchsploit": "searchsploit",
    "exploitdb": "searchsploit",
    # 密码攻击
    "hydra": "hydra",
    "john": "john",
    "hashcat": "hashcat",
    "medusa": "medusa",
    "hash-identifier": "hash-identifier",
    # 嗅探/CLI
    "tcpdump": "tcpdump",
    "tshark": "tshark",
    "mitmproxy": "mitmproxy",
    "bettercap": "bettercap",
    "responder": "responder",
    # 枚举
    "enum4linux": "enum4linux",
    "smbclient": "smbclient",
    "snmpwalk": "snmpwalk",
    "onesixtyone": "onesixtyone",
    "rpcclient": "rpcclient",
    # 隐写
    "steghide": "steghide",
    "zsteg": "zsteg",
    "binwalk": "binwalk",
    "foremost": "foremost",
    "exiftool": "exiftool",
    "strings": "strings",
    "file": "file",
    "xxd": "xxd",
    # 密码学
    "openssl": "openssl",
    "gpg": "gpg",
    "sage": "sage",
    "python3": "python3",
    "python": "python3",
    # 逆向
    "gdb": "gdb",
    "radare2": "radare2",
    "r2": "radare2",
    "rizin": "rizin",
    "objdump": "objdump",
    "readelf": "readelf",
    "strace": "strace",
    "ltrace": "ltrace",
    "jadx": "jadx",
    "apktool": "apktool",
    "dex2jar": "dex2jar",
    # 杂项
    "curl": "curl",
    "wget": "wget",
    "git": "git",
    "docker": "docker",
}

# 常见工具名匹配模式
_TOOL_PATTERNS = [
    # 中文：使用/用 X
    re.compile(r"(?:使用|用|调用|执行|运行|通过|借助)\s*([a-zA-Z][a-zA-Z0-9._-]{0,30})"),
    # 英文：use/run/try/launch X
    re.compile(r"\b(?:use|run|try|launch|invoke|call)\s+([a-zA-Z][a-zA-Z0-9._-]{0,30})\b", re.IGNORECASE),
    # "X 扫描/测试/爆破/分析/枚举"
    re.compile(r"\b([a-zA-Z][a-zA-Z0-9._-]{0,30})\s*(?:扫描|测试|爆破|分析|枚举|注入|嗅探|抓包|反编译)"),
]


def extract_tool_mentions(text: str) -> Set[str]:
    """从自然语言反馈中提取提到的工具名称。"""
    mentioned: Set[str] = set()

    # 模式匹配
    for pattern in _TOOL_PATTERNS:
        for m in pattern.finditer(text):
            name = m.group(1).lower()
            # 跳过过于通用的词
            if name in {"the", "this", "that", "and", "for", "can", "you", "get",
                        "set", "new", "all", "one", "two", "our", "how", "now",
                        "not", "out", "will", "with", "from", "your", "have",
                        "been", "were", "they", "them", "then", "than", "some",
                        "just", "also", "very", "much", "many", "more", "most",
                        "make", "made", "like", "into", "over", "such", "only",
                        "other", "each", "every", "both", "few", "after",
                        "before", "between", "through", "during", "about",
                        "above", "below", "under", "again", "once", "here",
                        "there", "where", "which", "what", "when", "would",
                        "could", "should", "need", "want", "see", "know",
                        "think", "take", "give", "find", "tell", "ask", "try",
                        "show", "look", "say", "read", "write", "back", "next",
                        "first", "last", "good", "well", "same", "case",
                        "while", "being", "does", "done", "doing", "still"}:
                continue
            mentioned.add(name)

    # 已知工具名直接匹配
    lower_text = text.lower()
    for known_name in _KNOWN_TOOLS:
        if known_name in lower_text:
            mentioned.add(known_name)

    return mentioned


class DynamicToolResolver:
    """动态工具解析器 — 通过 SSH 发现远程工具并动态加载 MCP 服务。"""

    def __init__(self, ssh_config: dict = None):
        self._ssh_config = ssh_config or {}
        self._discovered: Dict[str, dict] = {}  # tool_name -> function_config
        self._not_found: Set[str] = set()       # 已确认不存在的工具（避免重复查询）
        self._probe_found: Set[str] = set()     # P1 探测结果：已知存在的工具
        self._probe_missing: Set[str] = set()   # P1 探测结果：已知缺失的工具

    @property
    def has_ssh(self) -> bool:
        return bool(self._ssh_config.get("host") and self._ssh_config.get("username"))

    def set_known_state(self, tools_found: list, tools_missing: list):
        """注入 P1 环境探测结果，避免重复 SSH 检查。

        已知存在的工具直接注册，已知缺失的工具直接跳过。
        探测结果中未覆盖的工具仍走原来的 SSH 检查流程。
        """
        self._probe_found = set(t.lower() for t in tools_found)
        self._probe_missing = set(t.lower() for t in tools_missing)
        logger.info("动态解析器已注入探测结果: %d 已知可用, %d 已知缺失",
                     len(self._probe_found), len(self._probe_missing))

    def resolve(self, tool_names: Set[str]) -> List[dict]:
        """解析工具名列表，返回可在远程服务器上找到的工具的 function_config。

        优先级: 已缓存 > P1 探测结果 > SSH 实时检查。
        """
        new_configs: List[dict] = []
        if not self.has_ssh or not tool_names:
            return new_configs

        for name in tool_names:
            name = name.lower().strip()
            if not name or len(name) < 2:
                continue

            # 已缓存
            if name in self._discovered:
                new_configs.append(self._discovered[name])
                continue
            if name in self._not_found:
                continue

            remote_cmd = _KNOWN_TOOLS.get(name, name)

            # P1 探测结果 — 已知可用，直接注册（跳过 SSH）
            if remote_cmd in self._probe_found or name in self._probe_found:
                cfg = self._build_shell_wrapper(name, remote_cmd)
                self._discovered[name] = cfg
                new_configs.append(cfg)
                logger.debug("远程工具已注册 (来自探测缓存): %s -> %s", name, remote_cmd)
                continue

            # P1 探测结果 — 已知缺失，直接跳过（跳过 SSH）
            if remote_cmd in self._probe_missing or name in self._probe_missing:
                self._not_found.add(name)
                logger.debug("远程工具已跳过 (探测缓存缺失): %s", name)
                continue

            # 未在探测结果中 — SSH 实时检查
            if self._check_remote(remote_cmd):
                cfg = self._build_shell_wrapper(name, remote_cmd)
                self._discovered[name] = cfg
                new_configs.append(cfg)
                logger.info(f"远程工具已发现: {name} -> {remote_cmd}")
            else:
                self._not_found.add(name)

        return new_configs

    def mark_available(self, tool_name: str):
        """标记工具为可用（P3: 中途安装成功后调用）。"""
        name = tool_name.lower().strip()
        self._not_found.discard(name)
        self._probe_missing.discard(name)
        self._probe_found.add(name)

    def _check_remote(self, cmd: str) -> bool:
        """通过 SSH 检查远程服务器上是否存在指定命令。"""
        # 白名单校验：只允许字母、数字、连字符、下划线、点号组成的合法命令名
        import re as _re
        if not _re.match(r'^[a-zA-Z0-9_./-]+$', cmd):
            logger.warning("拒绝非法的命令名: %s", cmd[:80])
            return False
        try:
            import paramiko
        except ImportError:
            logger.warning("paramiko 未安装，跳过远程工具发现")
            return False

        host = self._ssh_config.get("host", "127.0.0.1")
        port = self._ssh_config.get("port", 22)
        username = self._ssh_config.get("username", "")
        password = self._ssh_config.get("password", "")

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.WarningPolicy())

        try:
            client.connect(
                hostname=host, port=port, username=username, password=password,
                timeout=6, allow_agent=False, look_for_keys=False,
            )
            # 检查命令是否存在
            check_cmd = f"command -v {cmd} || which {cmd} || dpkg -l 2>/dev/null | grep -q '^ii.*{cmd}' || apt list --installed 2>/dev/null | grep -q '^{cmd}/'"
            _, stdout, stderr = client.exec_command(check_cmd, timeout=8)
            exit_code = stdout.channel.recv_exit_status()
            return exit_code == 0
        except Exception as e:
            logger.debug(f"SSH 工具检查失败 ({cmd}): {e}")
            return False
        finally:
            try:
                client.close()
            except Exception:
                pass

    def _build_shell_wrapper(self, name: str, remote_cmd: str) -> dict:
        """为发现的远程工具构建 function_config。"""
        desc_map = {
            "nmap": "网络端口扫描与服务探测",
            "sqlmap": "SQL 注入自动检测与利用",
            "hydra": "在线密码爆破 (支持多种协议)",
            "john": "离线密码破解 (John the Ripper)",
            "hashcat": "GPU 加速密码破解",
            "gobuster": "Web 目录/文件爆破",
            "ffuf": "Web Fuzzing",
            "dirb": "Web 目录扫描",
            "nikto": "Web 服务器漏洞扫描",
            "metasploit": "Metasploit 漏洞利用框架",
            "msfconsole": "Metasploit 控制台",
            "searchsploit": "Exploit-DB 本地搜索",
            "tcpdump": "网络流量抓包",
            "tshark": "命令行协议分析",
            "responder": "LLMNR/NBT-NS/mDNS 投毒",
            "enum4linux": "Windows/Samba 枚举",
            "steghide": "隐写数据嵌入与提取",
            "zsteg": "PNG/BMP LSB 隐写检测",
            "binwalk": "固件/文件嵌入式数据提取",
            "foremost": "文件雕刻恢复",
            "exiftool": "文件元数据读写",
            "openssl": "SSL/TLS 密码学工具包",
            "gdb": "GNU 调试器",
            "radare2": "逆向工程框架",
            "jadx": "Android APK/DEX 反编译",
            "apktool": "APK 解包/重打包",
            "netcat": "TCP/UDP 网络读写",
            "curl": "HTTP/FTP/多协议客户端",
            "python3": "Python 3 解释器",
        }
        desc = desc_map.get(name, f"远程工具: {remote_cmd}（通过 SSH 执行）")

        return {
            "type": "function",
            "function": {
                "name": f"remote_{name}",
                "description": (
                    f"[远程工具] {desc}。"
                    f"用法: 将 {name} 的命令行参数填入 content 字段，"
                    f"工具通过 SSH 在远程服务器上执行 {remote_cmd}。"
                ),
                "tags": ["remote", "dynamic", name],
                "parameters": {
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": f"{name} 的命令行参数（不含工具名）",
                        }
                    },
                    "required": ["content"],
                },
                "_dynamic": True,
                "_remote_cmd": remote_cmd,
            },
        }

    def get_all_discovered(self) -> List[dict]:
        """获取所有已发现的远程工具配置。"""
        return list(self._discovered.values())
