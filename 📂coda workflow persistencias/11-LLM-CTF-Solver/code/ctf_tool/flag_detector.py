"""Flag 自动正则检测 — 在 LLM 分析前预扫描工具输出中的 flag 模式。"""

import re
from typing import List, Optional

# 常见 CTF flag 格式（按优先级排序 — 具体赛事前缀优先于通用模式）
_FLAG_PATTERNS = [
    # 具体赛事前缀（避免被通用 CTF/HTB 子串匹配截断）
    re.compile(r'(?:shellmates|inctf|picoCTF|csaw|hitcon|defcon|sekai|asis|angstrom|b01lers|corctf|dice|DUCTF|idek|kalmar|LITCTF|maple|osu|pbctf|plaid|port|ractf|squ1rrel|sunshinectf|TFCCTF|tsgctf|uiuctf|utctf|vishwaCTF|wacon|wpictf|zer0pts)\{[^}]+\}', re.IGNORECASE),
    # 通用已知格式
    re.compile(r'flag\{[^}]+\}', re.IGNORECASE),
    re.compile(r'CTF\{[^}]+\}', re.IGNORECASE),
    re.compile(r'HTB\{[^}]+\}'),
    # 通用兜底：前缀 ≥3 字符 + 大括号内容 ≥10 字符
    re.compile(r'[A-Za-z0-9_]{3,}\{[A-Za-z0-9_!@#$%^&*()\-+=.\[\]|:;<>?,/~` ]{10,}\}'),
]

# 明确不是 flag 的模式（降低误报）
_FALSE_POSITIVE_PATTERNS = [
    re.compile(r'^(?:function|const|let|var|class|import|export|require)\s*[A-Za-z0-9_]*\s*\{'),
    re.compile(r'^\s*"[A-Za-z0-9_]+"\s*:\s*\{'),  # JSON key
    re.compile(r'\{[^}]*"[^}"]*"[^}]*\}'),  # 含引号的值
    re.compile(r'\{\s*\}'),  # 空大括号（代码常见，非 flag）
    re.compile(r'<[^>]+\{[^}]*\}[^>]*>'),  # HTML 标签内含大括号
    re.compile(r'[a-z]+://[^}]*\{[^}]*\}'),  # URL 中含大括号（非 flag）
]


def _is_false_positive(match_text: str) -> bool:
    """检查匹配文本是否为已知误报模式。"""
    for fp in _FALSE_POSITIVE_PATTERNS:
        if fp.search(match_text):
            return True
    return False


def detect_flag(text: str) -> Optional[str]:
    """扫描文本，返回第一个匹配的 flag（按优先级，排除误报）。"""
    if not text:
        return None
    for pattern in _FLAG_PATTERNS:
        for match in pattern.finditer(text):
            candidate = match.group(0)
            if not _is_false_positive(candidate):
                return candidate
    return None


def extract_all_flags(text: str) -> List[str]:
    """提取文本中所有匹配的 flag（排除误报）。"""
    if not text:
        return []
    results: List[str] = []
    for pattern in _FLAG_PATTERNS:
        for match in pattern.finditer(text):
            candidate = match.group(0)
            if not _is_false_positive(candidate):
                results.append(candidate)
    return results
