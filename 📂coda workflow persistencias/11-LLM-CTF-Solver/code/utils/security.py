"""命令安全黑名单 — 拦截高危系统命令，保护运行环境不被意外破坏。"""

import re
import logging
from typing import List, Dict, Tuple

logger = logging.getLogger(__name__)

# 默认黑名单规则（面向 Linux 运行环境）。
# 每条规则包含 pattern（正则）和 reason（拦截原因）。
# 允许 CTF 攻击载荷通过（如反向 shell、提权 payload），
# 仅拦截会破坏 Agent 自身运行环境的高危操作。
_DEFAULT_BLACKLIST: List[Dict[str, str]] = [
    # ── 文件系统破坏 ──
    {
        "pattern": r"\brm\s+.*-rf\s+/(\*|\s|$)",
        "reason": "禁止递归删除根目录所有文件"
    },
    {
        "pattern": r"\brm\s+.*-rf\s+.*--no-preserve-root",
        "reason": "禁止绕过安全保护删除根目录"
    },
    {
        "pattern": r"\brm\s+-rf\s+~",
        "reason": "禁止递归删除用户主目录"
    },
    {
        "pattern": r"\brm\s+-rf\s+\$HOME",
        "reason": "禁止递归删除用户主目录"
    },
    {
        "pattern": r"\brm\s+-r\s+-f\s+/",
        "reason": "禁止递归删除根目录"
    },
    {
        "pattern": r"\bmkfs\.?\w*\s+/dev",
        "reason": "禁止格式化磁盘设备"
    },
    {
        "pattern": r"\bdd\s+if=/dev/zero\s+of=/dev",
        "reason": "禁止覆写磁盘设备"
    },
    {
        "pattern": r"\bdd\s+if=/dev/urandom\s+of=/dev",
        "reason": "禁止随机数据覆写磁盘设备"
    },

    # ── 系统控制 ──
    {
        "pattern": r"\bshutdown\s+-",
        "reason": "禁止关闭/重启系统"
    },
    {
        "pattern": r"\breboot\b",
        "reason": "禁止重启系统"
    },
    {
        "pattern": r"\bpoweroff\b",
        "reason": "禁止关闭系统"
    },

    # ── Fork 炸弹 ──
    {
        "pattern": r":[()\s]*\{[()\s]*:[|&][^}]*\}[^;]*;",
        "reason": "疑似 Fork 炸弹（Shell 函数递归调用）"
    },
    {
        "pattern": r"\bperl\s+-e\s+.*fork\s*\{.*fork\b",
        "reason": "疑似 Perl Fork 炸弹"
    },
    {
        "pattern": r"\bpython3?\s+-c\s+.*['\"]__import__\(['\"]os['\"]\)\.fork\(\)",
        "reason": "疑似 Python Fork 炸弹"
    },

    # ── 管道 / 重定向破坏 ──
    {
        "pattern": r"\bcat\s+/dev/null\s*>\s*/dev/sd[a-z]+",
        "reason": "禁止清空磁盘设备"
    },
    {
        "pattern": r"\>\s*/dev/sd[a-z]+",
        "reason": "禁止覆写磁盘设备"
    },

    # ── 编码绕过（base64 / hex 编码后管道执行） ──
    {
        "pattern": r"\bbase64\s+.*-d\s*.*\|",
        "reason": "禁止 base64 解码后管道执行（常见绕过手法）"
    },
    {
        "pattern": r"\bxxd\s+.*-r\s*-p?\s*.*\|",
        "reason": "禁止 hex 解码后管道执行（常见绕过手法）"
    },
    {
        "pattern": r"\bopenssl\s+base64\s+-d\s*.*\|",
        "reason": "禁止 OpenSSL base64 解码后管道执行"
    },

    # ── 管道到解释器（编码绕过最终执行路径） ──
    {
        "pattern": r"\|\s*(ba)?sh\b",
        "reason": "禁止管道到 shell 解释器"
    },
    {
        "pattern": r"\|\s*(d)?ash\b",
        "reason": "禁止管道到 dash 解释器"
    },
    {
        "pattern": r"\|\s*zsh\b",
        "reason": "禁止管道到 zsh 解释器"
    },
    {
        "pattern": r"\|\s*python3?\b",
        "reason": "禁止管道到 Python 解释器执行"
    },
    {
        "pattern": r"\|\s*perl\b",
        "reason": "禁止管道到 Perl 解释器执行"
    },
    {
        "pattern": r"\|\s*ruby\b",
        "reason": "禁止管道到 Ruby 解释器执行"
    },

    # ── 内联脚本执行 ──
    {
        "pattern": r"\bpython3?\s+-c\s+",
        "reason": "禁止 Python 内联脚本执行"
    },
    {
        "pattern": r"\bperl\s+-e\s+",
        "reason": "禁止 Perl 内联脚本执行"
    },
    {
        "pattern": r"\bruby\s+-e\s+",
        "reason": "禁止 Ruby 内联脚本执行"
    },
    {
        "pattern": r"\bphp\s+-r\s+",
        "reason": "禁止 PHP 内联脚本执行"
    },
    {
        "pattern": r"\bnode\s+-e\s+",
        "reason": "禁止 Node.js 内联脚本执行"
    },

    # ── rm 绕过变体 ──
    {
        "pattern": r"\brm\s+.*--no-preserve-root",
        "reason": "禁止绕过根目录保护删除"
    },

    # ── 权限提升后门 ──
    {
        "pattern": r"\becho\s+.*\s*>>\s*~/.ssh/authorized_keys",
        "reason": "禁止修改本地 SSH authorized_keys"
    },
    {
        "pattern": r"\becho\s+\S+\s+ALL=\(ALL\)\s+NOPASSWD:\s*ALL\s*>>\s*/etc/sudoers",
        "reason": "禁止修改 sudoers 文件"
    },
    {
        "pattern": r"\bcurl\s+\S+\s*\|?\s*(ba)?sh\b",
        "reason": "禁止 curl | sh 远程脚本执行（存在供应链风险）"
    },
    {
        "pattern": r"\bwget\s+\S+\s*-O\s*-?\s*\|?\s*(ba)?sh\b",
        "reason": "禁止 wget | sh 远程脚本执行（存在供应链风险）"
    },

    # ── 敏感服务停止 ──
    {
        "pattern": r"\bsystemctl\s+disable\s+sshd?\b",
        "reason": "禁止禁用 SSH 服务（会导致远程执行通道中断）"
    },
    {
        "pattern": r"\bsystemctl\s+stop\s+sshd?\b",
        "reason": "禁止停止 SSH 服务（会导致远程执行通道中断）"
    },
    {
        "pattern": r"\bkill(all|)\s+-9\s+[01]\b",
        "reason": "禁止 killer init 进程 (PID 0/1)"
    },
    {
        "pattern": r"\bkill(all|)\s+-s\s*9\s+[01]\b",
        "reason": "禁止 killer init 进程 (PID 0/1)"
    },
]


class CommandBlacklist:
    """命令安全黑名单。

    用法:
        bl = CommandBlacklist(config_rules)
        safe, reason = bl.check("rm -rf /")
        if not safe:
            raise RuntimeError(reason)
    """

    def __init__(self, extra_rules: List[Dict[str, str]] = None):
        self.rules: List[Tuple[re.Pattern, str]] = []

        for rule in _DEFAULT_BLACKLIST:
            try:
                self.rules.append((re.compile(rule["pattern"], re.IGNORECASE), rule["reason"]))
            except re.error as e:
                logger.warning("黑名单规则正则错误 '%s': %s", rule.get("pattern", ""), e)

        # 从配置中加载额外规则（可覆盖默认规则或追加新规则）
        if extra_rules:
            action_map = {"append": [], "replace": []}
            for r in extra_rules:
                action_map.setdefault(r.get("action", "append"), []).append(r)

            if action_map["replace"]:
                logger.info("配置指定了 replace 动作，使用自定义黑名单替换默认规则")
                self.rules = []
                for rule in action_map["replace"]:
                    self._add_rule(rule)
            else:
                for rule in action_map["append"]:
                    self._add_rule(rule)

    def _add_rule(self, rule: Dict[str, str]) -> None:
        try:
            self.rules.append((re.compile(rule["pattern"], re.IGNORECASE), rule["reason"]))
        except re.error as e:
            logger.warning("跳过无效黑名单规则 '%s': %s", rule.get("pattern", ""), e)

    def check(self, command: str) -> Tuple[bool, str]:
        """检查命令是否安全。

        先在原始命令上检查黑名单，再对 base64/hex 编码片段解码后复检。

        Returns:
            (safe, reason): safe=True 表示命令可以执行；safe=False 时 reason 为拦截原因。
        """
        if not command or not isinstance(command, str):
            return True, ""

        # 第一轮：对原始命令做黑名单匹配
        for pattern, reason in self.rules:
            if pattern.search(command):
                return False, reason

        # 第二轮：预解码检测 — 提取 base64/hex 编码片段，解码后复检
        decoded_chunks = self._extract_encoded_chunks(command)
        for chunk in decoded_chunks:
            for pattern, reason in self.rules:
                if pattern.search(chunk):
                    return False, f"{reason} (解码后命中: {chunk[:80]}...)"

        return True, ""

    @staticmethod
    def _extract_encoded_chunks(command: str) -> List[str]:
        """从命令中提取 base64/hex 编码片段并尝试解码。

        覆盖模式:
          - echo <base64> | base64 -d
          - base64 -d <<< <base64>
          - printf '%s' <base64> | base64 -d
          - $'\\x72\\x6d' 格式 hex 转义
          - $(echo <base64> | base64 -d) 命令替换
        """
        import base64 as _b64
        chunks: List[str] = []

        # 1. 提取 base64 编码字符串（常见模式：独立的 base64 字符串）
        b64_matches = re.findall(
            r'(?:echo\s+|<<<\s*|printf\s+[^|]*\|?\s*)'
            r'([A-Za-z0-9+/=]{20,})'
            r'(?:\s*\|\s*base64\s+-d|\s*\|\s*openssl\s+base64\s+-d)',
            command, re.IGNORECASE
        )
        for b64_str in b64_matches:
            try:
                decoded = _b64.b64decode(b64_str, validate=True).decode("utf-8", errors="replace")
                if len(decoded) >= 4:
                    chunks.append(decoded)
            except Exception:
                pass

        # 2. 提取 $'...' hex 转义并解码
        hex_matches = re.findall(r"\$'((?:\\x[0-9a-fA-F]{2})+?)'", command)
        for hex_str in hex_matches:
            try:
                decoded = re.sub(r'\\x([0-9a-fA-F]{2})',
                                 lambda m: chr(int(m.group(1), 16)), hex_str)
                if len(decoded) >= 4:
                    chunks.append(decoded)
            except Exception:
                pass

        # 3. 检测 $(...) 命令替换 — 提取内部命令并递归检查
        sub_matches = re.findall(r'\$\(([^)]+)\)', command)
        for sub_cmd in sub_matches:
            if len(sub_cmd) >= 5:
                # 递归提取子命令中的编码片段
                inner = CommandBlacklist._extract_encoded_chunks(sub_cmd)
                chunks.extend(inner)
                # 同时把子命令本身加入检查（防多层嵌套）
                if re.search(r'(?:base64|xxd|openssl).*(?:-d|decode)', sub_cmd):
                    chunks.append(sub_cmd)

        return chunks

    def check_or_raise(self, command: str) -> None:
        """检查命令，不安全时抛出 RuntimeError。"""
        safe, reason = self.check(command)
        if not safe:
            msg = f"安全黑名单拦截: {reason}\n命令: {command[:200]}"
            logger.warning(msg)
            raise RuntimeError(msg)


# 全局单例（由 ToolUtils 或 solve_agent 初始化）
_global_blacklist: CommandBlacklist = None
_blacklist_lock = __import__('threading').Lock()


def get_blacklist() -> CommandBlacklist:
    """获取全局黑名单单例（线程安全）。"""
    global _global_blacklist
    if _global_blacklist is None:
        with _blacklist_lock:
            if _global_blacklist is None:
                _global_blacklist = CommandBlacklist()
    return _global_blacklist


def init_blacklist(extra_rules: List[Dict[str, str]] = None) -> CommandBlacklist:
    """初始化（或重新初始化）全局黑名单。"""
    global _global_blacklist
    with _blacklist_lock:
        _global_blacklist = CommandBlacklist(extra_rules)
    return _global_blacklist
