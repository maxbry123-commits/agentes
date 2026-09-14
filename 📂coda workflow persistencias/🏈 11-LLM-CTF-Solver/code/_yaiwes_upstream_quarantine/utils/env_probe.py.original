"""环境探测 — SSH 到 Kali 探测可用工具、Python 库、网络连通性。

启动时调用一次，生成环境摘要注入 LLM 每步 prompt，
消除"工具是否存在""网络是否可达""Python 能做什么"的信息盲区。
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# ── 探测项定义 ─────────────────────────────────────────────────

_TOOLS_TO_PROBE = [
    # 网络
    "nmap", "masscan", "netcat", "nc", "socat", "curl", "wget",
    # Web
    "sqlmap", "dirb", "gobuster", "ffuf", "nikto", "wpscan", "hydra",
    # 密码
    "john", "hashcat", "hash-identifier", "zip2john", "rar2john",
    # 隐写/取证
    "steghide", "zsteg", "binwalk", "foremost", "exiftool", "strings", "xxd", "file",
    # 逆向
    "gdb", "objdump", "strace", "ltrace", "strings",
    # 密码学
    "openssl", "gpg",
    # 漏洞利用
    "searchsploit", "msfconsole",
    # 开发
    "python3", "python", "pip3", "pip", "git",
    # ZIP 破解
    "bkcrack", "fcrackzip",
]

_PY_MODULES_TO_PROBE = [
    "Crypto", "gmpy2", "pwntools", "requests", "PIL",
    "numpy", "scapy", "paramiko", "zipfile", "tarfile",
    "hashlib", "base64", "zlib", "json", "re",
]

# ── 探测脚本 ───────────────────────────────────────────────────

def _build_probe_script() -> str:
    """构建在 Kali 上执行的探测脚本。一次性运行，减少 SSH 往返。"""
    lines = []

    # 1. 工具探测
    lines.append("echo '=== TOOLS ==='")
    for cmd in _TOOLS_TO_PROBE:
        lines.append(
            f"which {cmd} >/dev/null 2>&1 && echo 'FOUND:{cmd}' || echo 'MISS:{cmd}'"
        )

    # 2. Python 模块探测
    lines.append("echo '=== PY_MODULES ==='")
    mod_check = (
        "python3 -c \"\n"
        + "\n".join(
            f"try:\n __import__('{m}')\n print('FOUND:{m}')\nexcept:\n print('MISS:{m}')"
            for m in _PY_MODULES_TO_PROBE
        )
        + "\n\""
    )
    lines.append(mod_check)

    # 3. 网络连通性
    lines.append("echo '=== NETWORK ==='")
    lines.append(
        "curl -s --connect-timeout 5 https://github.com >/dev/null 2>&1"
        " && echo 'NET:github=OK' || echo 'NET:github=FAIL'"
    )
    lines.append(
        "curl -s --connect-timeout 5 https://pypi.org >/dev/null 2>&1"
        " && echo 'NET:pypi=OK' || echo 'NET:pypi=FAIL'"
    )

    # 4. OS 信息
    lines.append("echo '=== OS ==='")
    lines.append("uname -a")
    lines.append("cat /etc/os-release 2>/dev/null | head -3")

    lines.append("echo '=== END ==='")
    return "\n".join(lines)


# ── 结果解析 ───────────────────────────────────────────────────

def _parse_probe_output(output: str) -> Dict:
    """解析探测脚本输出为结构化字典。无 section marker 时整段作为 OS 信息。"""
    result = {
        "tools_found": [],
        "tools_missing": [],
        "py_modules_found": [],
        "py_modules_missing": [],
        "network": {},
        "os_info": "",
    }

    section = None
    raw_lines = []
    has_markers = "=== TOOLS ===" in output or "=== OS ===" in output

    for line in output.split("\n"):
        line = line.strip()
        if line == "=== TOOLS ===":
            section = "tools"
            continue
        elif line == "=== PY_MODULES ===":
            section = "py"
            continue
        elif line == "=== NETWORK ===":
            section = "net"
            continue
        elif line == "=== OS ===":
            section = "os"
            continue
        elif line == "=== END ===":
            break

        if section == "tools":
            if line.startswith("FOUND:"):
                result["tools_found"].append(line[6:])
            elif line.startswith("MISS:"):
                result["tools_missing"].append(line[5:])
        elif section == "py":
            if line.startswith("FOUND:"):
                result["py_modules_found"].append(line[6:])
            elif line.startswith("MISS:"):
                result["py_modules_missing"].append(line[5:])
        elif section == "net":
            if line.startswith("NET:") and "=" in line:
                k, v = line[4:].split("=", 1)
                result["network"][k] = v
        elif section == "os":
            if line:
                result["os_info"] += line + "\n"
        elif section is None and line:
            raw_lines.append(line)

    # 无 section marker 的原始输出（如最小探测回退） → 作为 OS 信息
    if not has_markers and raw_lines:
        result["os_info"] = "\n".join(raw_lines)
        # 尝试从中提取 python3 路径
        for rl in raw_lines:
            if "python3" in rl:
                result["tools_found"].append("python3")

    return result


# ── 探测入口 ───────────────────────────────────────────────────

def probe_environment() -> Optional[Dict]:
    """探测远程 Kali 环境。SSH 不可用或执行失败时返回 None。

    三层回退:
      1. 完整探测脚本 (30+ 工具 + Python 模块 + 网络 + OS)
      2. 若完整探测失败 → 最小探测 (uname + which python3)
      3. 若最小探测也失败 → 返回 None
    """
    try:
        from config import Config
        from ctf_tool.ssh_client import SSHClient

        ssh_cfg = Config.get_tool_config("ssh_shell")
        if not ssh_cfg.get("host") or not ssh_cfg.get("username"):
            logger.info("SSH 未配置 (host/username 为空)，跳过环境探测")
            return None

        host = ssh_cfg.get("host", "127.0.0.1")
        port = ssh_cfg.get("port", 22)
        logger.info("开始环境探测: %s@%s:%s", ssh_cfg.get("username"), host, port)

        client = SSHClient(
            hostname=host,
            port=port,
            username=ssh_cfg.get("username", ""),
            password=ssh_cfg.get("password", ""),
        )

        # ── 完整探测 (timeout=45s，留足 curl 5s*2 + which*35 的余量) ──
        try:
            script = _build_probe_script()
            output = client.exec(script, timeout=45)
        except Exception as exec_err:
            logger.warning("完整探测脚本执行失败: %s，尝试最小探测...", exec_err)
            try:
                output = client.exec("uname -a; which python3 2>/dev/null; cat /etc/os-release 2>/dev/null | head -2", timeout=10)
                logger.info("最小探测成功")
            except Exception as mini_err:
                logger.warning("最小探测也失败: %s", mini_err)
                return None

        result = _parse_probe_output(output)
        tools_total = len(result["tools_found"]) + len(result["tools_missing"])
        logger.info(
            "环境探测完成: 工具 %d/%d 可用, Python 模块 %d/%d 可用, 网络=%s, OS=%s",
            len(result["tools_found"]), tools_total,
            len(result["py_modules_found"]),
            len(result["py_modules_found"]) + len(result["py_modules_missing"]),
            result.get("network", {}),
            result.get("os_info", "").strip()[:60],
        )
        return result

    except ConnectionError as e:
        logger.warning("环境探测失败 — SSH 连接失败 (检查 Kali VM 是否运行、端口 %s): %s",
                       ssh_cfg.get("port", 22) if 'ssh_cfg' in dir() else "?", e)
        return None
    except Exception as e:
        logger.warning("环境探测失败 — 未预期错误: %s (%s)", e, type(e).__name__)
        return None


def detect_new_installations(output: str) -> list:
    """从工具输出中检测是否安装了新工具。返回工具名列表。"""
    import re
    found = []

    # apt install 成功 — "Setting up <pkg>" / "is already the newest version" / 0 upgraded, 1 newly installed
    if re.search(r'(?:Setting up|Unpacking|is already the newest version|newly installed|已安装)', output):
        pkgs = re.findall(r'(?:Setting up|Unpacking|Preparing to unpack)\s+(\S+)', output)
        for pkg in pkgs:
            name = pkg.split(":")[0].split("_")[0]  # strip arch/version
            if name and name not in found:
                found.append(name)
        # Also match "apt install -y <pkg>" style
        apt_installs = re.findall(r'apt(?:-get)?\s+install\s+(?:-y\s+)?(\S+)', output)
        for pkg in apt_installs:
            name = pkg.strip().split("=")[0]  # strip version constraint
            if name and name not in found:
                found.append(name)

    # pip install 成功 — "Successfully installed <pkg>"
    pip_installs = re.findall(r'Successfully installed\s+(.+)', output)
    for match in pip_installs:
        for pkg in match.split():
            pkg = pkg.strip().split("-")[0]  # strip version
            if pkg and pkg not in found:
                found.append(pkg)

    # git clone 成功
    if re.search(r'(?:Cloning into|Resolving deltas|正克隆到)', output):
        repo = re.findall(r"(?:Cloning into|正克隆到)\s+'?(\S+)'?", output)
        for r in repo:
            name = r.strip("'.").split("/")[-1].replace(".git", "")
            if name and name not in found:
                found.append(name)

    return found


def format_env_context(probe: Optional[Dict]) -> str:
    """将探测结果格式化为 LLM prompt 上下文块。"""
    if not probe:
        return ""

    parts = ["## Kali 执行环境\n"]

    # OS
    if probe.get("os_info", "").strip():
        parts.append(f"系统:\n{probe['os_info'].strip()}\n")

    # 可用工具
    if probe.get("tools_found"):
        parts.append(f"可用命令行工具: {', '.join(probe['tools_found'])}")

    # 缺失工具（只列重要的）
    missing_important = [t for t in probe.get("tools_missing", [])
                         if t in ("bkcrack", "fcrackzip", "gdb", "radare2",
                                  "ghidra", "jadx", "metasploit", "wpscan")]
    if missing_important:
        parts.append(f"缺失工具: {', '.join(missing_important)}"
                     f"（可用 apt install 安装）")

    # Python 模块
    if probe.get("py_modules_found"):
        parts.append(f"Python3 可用模块: {', '.join(probe['py_modules_found'])}")

    # 网络
    net = probe.get("network", {})
    if net:
        net_parts = []
        for target, status in net.items():
            net_parts.append(f"{target}={status}")
        parts.append(f"网络: {', '.join(net_parts)}")

    # 安装提示
    parts.append(
        "\n注意: Kali 上安装 Python 包用 apt install python3-<name>，"
        "不要用 pip install（被 PEP 668 限制）。安装系统工具用 apt install <name>。"
    )

    return "\n".join(parts) + "\n"
