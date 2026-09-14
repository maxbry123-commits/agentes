"""工具输出解析器 — 用规则（而非 LLM）将冗长的工具输出压缩为结构化摘要。

减少发送给 LLM 的 token 量，同时保留所有关键信息（flag、端口、路径、漏洞等）。

用法:
    from utils.output_parser import OutputParser
    summary = OutputParser.parse(tool_name, raw_output)
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ── 公共工具 ──────────────────────────────────────────────────────────

_KEYWORDS = {
    # flag / 凭证
    "flag", "flag{", "ctf{", "CTF{", "FLAG{", "flag.txt",
    "password", "passwd", "pwd", "secret", "token", "key", "credential",
    "api_key", "apikey", "private_key", "access_key", "secret_key",
    # 认证 / 会话
    "Set-Cookie", "set-cookie", "set_cookie", "cookie", "Cookie",
    "Authorization", "Bearer", "jwt", "JWT", "eyJ",
    "session", "Session", "authenticated", "login", "logout",
    "csrf", "nonce", "xsrf",
    # 漏洞类型
    "vuln", "vulnerability", "injection", "xss", "sqli", "SQL injection",
    "lfi", "rfi", "ssti", "cmdi", "rce", "xxe", "ssrf",
    "deserialization", "deserialize", "overflow", "traversal",
    "upload", "shell", "exploit", "bypass", "backdoor",
    # 严重度 / 状态
    "error", "Error", "ERROR", "warning", "Warning", "critical", "high", "medium",
    "found", "Found", "success", "Success", "failed", "Failed", "Failure",
    # 服务 / 技术栈
    "admin", "root", "nginx", "apache", "tomcat", "iis",
    "php", "mysql", "postgresql", "mariadb", "mongodb", "redis",
    "python", "django", "flask", "node", "express", "react", "vue",
    # 加密 / 编码
    "encrypt", "decrypt", "cipher", "decode", "encode", "hash",
    "base64", "hex", "rot13", "xor", "aes", "rsa", "sha256", "md5",
    # 文件 / 路径
    "/etc/passwd", "/etc/shadow", ".bash_history", ".ssh/",
    "web.config", "wp-config", ".git/", ".env", ".htaccess",
    "robots.txt", "sitemap", "index.php", "admin.php", "login.php",
    # HTTP / 网络
    "HTTP/", "200 OK", "301 ", "302 ", "403 ", "404 ", "500 ",
    "Content-Type", "content-type", "X-Powered-By", "x-powered-by",
    "Server:", "server:", "Location:", "location:",
    # 端口 / 服务
    "open port", "tcp open", "PORT", "STATE", "SERVICE",
    # 数据模式
    "-----BEGIN", "PRIVATE KEY", "PUBLIC KEY", "CERTIFICATE",
}

# v3: 关键行模式 — 匹配这些模式的行即使在压缩时也强制保留
_CRITICAL_PATTERNS = [
    re.compile(r'set-cookie\s*:', re.IGNORECASE),
    re.compile(r'flag\{[a-zA-Z0-9_!@#$%^&*()\-+=]+}', re.IGNORECASE),
    re.compile(r'ctf\{[a-zA-Z0-9_!@#$%^&*()\-+=]+}', re.IGNORECASE),
    re.compile(r'eyJ[A-Za-z0-9\-_=]+\.[A-Za-z0-9\-_=]+\.[A-Za-z0-9\-_=]+'),  # JWT token
    re.compile(r'authorization\s*:', re.IGNORECASE),
    re.compile(r'bearer\s+', re.IGNORECASE),
    re.compile(r'token\s*[=:]\s*[\w\-_=]+\.[\w\-_=]+\.[\w\-_=]+'),  # token=xxx.yyy.zzz
]

# v3: JSON/XML 结构模式 — 结构化输出中保留有语义信息的关键字段行
_JSON_STRUCTURE_PATTERNS = [
    re.compile(r'"[^"]*"\s*:\s*"[^"]{4,}'),   # "key": "至少4字符的值" — 有信息量的键值对
    re.compile(r'"[^"]*"\s*:\s*\d+'),          # "key": 数字
    re.compile(r'"[^"]*"\s*:\s*(true|false)'), # "key": 布尔
]
_XML_STRUCTURE_PATTERNS = [
    re.compile(r'<\?xml\b', re.IGNORECASE),
    re.compile(r'<[a-zA-Z_][\w.-]*\s[^>]*>'),  # 带属性的开始标签
    re.compile(r'</[a-zA-Z_][\w.-]*>'),         # 闭合标签
    re.compile(r'<!\[CDATA\['),
]

# v3: HTML 结构模式 — HTTP 响应体压缩时保留的行
_HTML_STRUCTURE_PATTERNS = [
    re.compile(r'<\s*form\b', re.IGNORECASE),
    re.compile(r'<\s*input\b', re.IGNORECASE),
    re.compile(r'<\s*textarea\b', re.IGNORECASE),
    re.compile(r'<\s*select\b', re.IGNORECASE),
    re.compile(r'<\s*button\b', re.IGNORECASE),
    re.compile(r'<\s*script\b', re.IGNORECASE),
    re.compile(r'<\s*link\b', re.IGNORECASE),
    re.compile(r'<\s*meta\b', re.IGNORECASE),
    re.compile(r'<!--'),
    re.compile(r'name\s*=\s*["\']', re.IGNORECASE),
    re.compile(r'action\s*=\s*["\']', re.IGNORECASE),
    re.compile(r'method\s*=\s*["\']', re.IGNORECASE),
    re.compile(r'type\s*=\s*["\']\s*hidden', re.IGNORECASE),
    re.compile(r'csrf', re.IGNORECASE),
    re.compile(r'nonce\s*=\s*["\']', re.IGNORECASE),
]


def _is_critical_line(line: str) -> bool:
    """检查行是否包含关键模式（必须保留）。"""
    return any(p.search(line) for p in _CRITICAL_PATTERNS)


def _is_html_structure_line(line: str) -> bool:
    """检查行是否包含 HTML 结构元素（表单/输入/脚本/注释）。"""
    return any(p.search(line) for p in _HTML_STRUCTURE_PATTERNS)


def _is_json_structure_line(line: str) -> bool:
    """检查行是否包含有信息量的 JSON 键值对。"""
    return any(p.search(line) for p in _JSON_STRUCTURE_PATTERNS)


def _is_xml_structure_line(line: str) -> bool:
    """检查行是否包含 XML 结构标签。"""
    return any(p.search(line) for p in _XML_STRUCTURE_PATTERNS)


def _detect_content_type(text: str) -> str:
    """快速检测文本结构类型 (html / json / xml / plain)。"""
    head = text[:500].strip()
    if head.startswith("{") or head.startswith("["):
        return "json"
    if head.startswith("<?xml") or head.startswith("<"):
        # 区分 HTML 和 XML
        if re.search(r'<!DOCTYPE\s+html|<\s*html\b', head, re.IGNORECASE):
            return "html"
        if re.search(r'<\s*[a-zA-Z_][\w.-]*\s[^>]*>', head):
            return "xml"
    if re.search(r'<\s*(html|head|body|div|form|script|table)\b', head, re.IGNORECASE):
        return "html"
    return "plain"


def _has_keyword(line: str) -> bool:
    ll = line.lower()
    return any(kw in ll for kw in _KEYWORDS)


def _count_lines(text: str) -> int:
    return len(text.split("\n"))


def _truncate_middle(text: str, max_lines: int = 40,
                     keep_head: int = 8, keep_tail: int = 12) -> str:
    """保留首尾，压缩中间重复内容。"""
    lines = text.split("\n")
    if len(lines) <= max_lines:
        return text

    head = lines[:keep_head]
    tail = lines[-keep_tail:]
    body = lines[keep_head:-keep_tail]

    # 统计重复行模式
    unique_body = []
    seen = set()
    repeats = 0
    for line in body:
        stripped = line.strip()
        if stripped and stripped in seen:
            repeats += 1
            continue
        if stripped:
            seen.add(stripped)
        unique_body.append(line)

    compressed = head + unique_body + tail
    saved = len(lines) - len(compressed)

    return "\n".join(compressed) + f"\n[解析器] 已压缩: {len(lines)} 行 → {len(compressed)} 行 (去重 {repeats} 行, 截断 {saved} 行)"


# ═════════════════════════════════════════════════════════════════════
# 具体解析器
# ═════════════════════════════════════════════════════════════════════

class PortScanParser:
    """端口扫描结果解析。"""

    @staticmethod
    def can_parse(output: str) -> bool:
        return bool(re.search(r"\d+/tcp\s+open", output))

    @staticmethod
    def parse(output: str) -> str:
        open_ports = re.findall(r"^\s*(\d+/tcp)\s+open\s*(.*)", output, re.MULTILINE)
        if not open_ports:
            return output

        summary = f"[端口扫描] {len(open_ports)} 个端口开放\n"
        for port, banner in open_ports:
            service = banner.strip()[:60] if banner.strip() else "-"
            summary += f"  {port}  → {service}\n"

        # 追加原始输出中其他非端口行（如错误信息）
        extra = []
        for line in output.split("\n"):
            stripped = line.strip()
            if stripped and not re.match(r"\s*\d+/tcp", stripped) \
                    and "端口检测" not in stripped:
                if _has_keyword(stripped):
                    extra.append(stripped)
        if extra:
            summary += "\n[其他]\n" + "\n".join(extra[:5])

        return summary


class HttpResultParser:
    """HTTP 请求结果解析 (network_tool → http)"""

    @staticmethod
    def can_parse(output: str) -> bool:
        return bool(re.match(r"HTTP \d{3} \d+ bytes", output))

    @staticmethod
    def parse(output: str) -> str:
        lines = output.split("\n")
        status_line = lines[0] if lines else ""
        headers = []
        body_start = len(lines)
        for i, line in enumerate(lines[1:], 1):
            if line.strip() == "":
                body_start = i + 1
                break
            headers.append(line)

        body = "\n".join(lines[body_start:]) if body_start < len(lines) else ""

        result = f"{status_line}\n"
        # 保留所有响应头（Set-Cookie 等关键信息在头部）
        for h in headers:
            result += h + "\n"

        # 压缩 body：优先保留 HTML 结构行和关键安全模式行
        _HTTP_BODY_KEEP_HEAD = 1000
        _HTTP_BODY_KEEP_TAIL = 1000
        if len(body) > (_HTTP_BODY_KEEP_HEAD + _HTTP_BODY_KEEP_TAIL + 100):
            orig_lines = body.split("\n")
            head_lines = orig_lines[:_HTTP_BODY_KEEP_HEAD]
            tail_lines = orig_lines[-_HTTP_BODY_KEEP_TAIL:]
            middle_lines = orig_lines[_HTTP_BODY_KEEP_HEAD:-_HTTP_BODY_KEEP_TAIL]

            # 从中间区域提取 HTML 结构行和关键模式行
            extracted = []
            seen = set()
            for line in middle_lines:
                stripped = line.strip()
                if not stripped:
                    continue
                if _is_html_structure_line(line) or _is_critical_line(line):
                    if stripped not in seen:
                        seen.add(stripped)
                        extracted.append(line)

            body = "\n".join(head_lines)
            if extracted:
                body += f"\n... (压缩中段 {len(middle_lines)} 行, 保留 {len(extracted)} 行关键结构) ...\n"
                body += "\n".join(extracted) + "\n"
            else:
                body += f"\n... (压缩中段 {len(middle_lines)} 行) ...\n"
            body += "\n".join(tail_lines)

        if body:
            result += "\n" + body

        return result


class DirBruteParser:
    """目录爆破结果解析。"""

    @staticmethod
    def can_parse(output: str) -> bool:
        return "目录爆破" in output

    @staticmethod
    def parse(output: str) -> str:
        lines = output.split("\n")
        # 提取摘要行
        header = lines[0] if lines else ""
        # 提取发现条目
        findings = [l for l in lines if re.search(r"\d{3}\s+", l)]

        if not findings:
            return output

        # 状态码统计
        from collections import Counter
        codes = Counter()
        for f in findings:
            m = re.search(r"(\d{3})\s+", f)
            if m:
                codes[m.group(1)] += 1

        code_summary = ", ".join(f"{c}×{n}" for c, n in sorted(codes.items()))

        summary = f"{header}  [{code_summary}]\n"
        # 保留所有发现（通常不会太多）
        for f in findings:
            summary += f + "\n"

        return summary


class WebReconParser:
    """Web 侦查结果解析 (web_tools → recon)"""

    @staticmethod
    def can_parse(output: str) -> bool:
        return "=== Web 侦查" in output or "关键响应头" in output

    @staticmethod
    def parse(output: str) -> str:
        lines = output.split("\n")
        sections = {}
        current_section = "header"
        sections[current_section] = []

        for line in lines:
            if line.startswith("---") and line.endswith("---"):
                current_section = line.strip("- ").strip()
                sections[current_section] = []
            else:
                sections.setdefault(current_section, []).append(line)

        result_parts = [f"[Web Recon] {sections.get('header', [''])[0]}"]

        # 技术栈
        tech = sections.get("技术栈指纹", [])
        if tech:
            found = [t for t in tech if t.strip().startswith("+")]
            if found:
                result_parts.append(f"技术栈: {len(found)} 项 — " + ", ".join(t.strip("+ ") for t in found[:6]))

        # 关键响应头
        for section_name in ("关键响应头",):
            items = sections.get(section_name, [])
            for item in items:
                s = item.strip()
                if any(k in s.lower() for k in ("server", "x-powered", "set-cookie", "x-frame")):
                    result_parts.append(s)

        # 敏感文件
        sf = sections.get("敏感文件探测", [])
        if sf:
            found_files = [f for f in sf if f.strip().startswith("[")]
            if found_files:
                result_parts.append(f"敏感文件: {len(found_files)} 个 — " + ", ".join(f.strip() for f in found_files[:5]))

        # Cookie / 安全头分析
        for section_name in ("Cookie 分析",):
            items = sections.get(section_name, [])
            for item in items:
                if "⚠" in item:
                    result_parts.append(item.strip())

        # HTML 注释
        comments = sections.get("可疑 HTML 注释", [])
        if comments and any(c.strip() for c in comments if c.strip().startswith("[")):
            n = sum(1 for c in comments if c.strip().startswith("["))
            if n:
                result_parts.append(f"可疑 HTML 注释: {n} 条")

        # 缺失安全头
        missing = sections.get("", [])
        for m in missing:
            if "⚠" in m:
                result_parts.append(m.strip())

        return "\n".join(result_parts) if len(result_parts) > 1 else output


class VulnScanParser:
    """漏洞扫描结果解析 (SQLi/XSS/LFI/CMDI/SSTI)"""

    @staticmethod
    def can_parse(output: str) -> bool:
        patterns = [
            r"=== SQL 注入检测",
            r"=== XSS 检测",
            r"=== 命令注入检测",
            r"=== LFI / 路径遍历检测",
            r"=== SSTI 检测",
            r"=== 认证检测",
            r"=== 文件上传检测",
        ]
        return any(re.search(p, output) for p in patterns)

    @staticmethod
    def parse(output: str) -> str:
        lines = output.split("\n")
        # 提取标题
        title = ""
        findings = []
        headers_seen = set()

        for line in lines:
            s = line.strip()
            if s.startswith("==") and "检测" in s:
                title = s.strip("= ")
                continue
            # 保留漏洞发现行
            if s.startswith("⚠") or s.startswith("["):
                findings.append(s)
                continue
            # 保留关键统计信息
            if s.startswith("未") and "未发现" in s:
                summary_key = s.split("—")[0] if "—" in s else s
                if summary_key not in headers_seen:
                    headers_seen.add(summary_key)
                    findings.append(s)

        result = f"[{title}]\n" if title else "[漏洞扫描]\n"
        for f in findings:
            result += f + "\n"

        # 如果发现为空，至少保留结论行
        if not findings:
            for line in lines:
                s = line.strip()
                if "未发现" in s or "均未回显" in s:
                    result += s + "\n"
                    break

        return result


class GenericParser:
    """通用降级 — 按内容类型做结构化感知压缩，仅对纯文本回退关键词过滤+首尾截断。"""

    MIN_LENGTH = 800
    _KEEP_HEAD_LINES = 8
    _KEEP_TAIL_LINES = 15

    @staticmethod
    def can_parse(output: str) -> bool:
        return len(output) > GenericParser.MIN_LENGTH

    @staticmethod
    def parse(output: str) -> str:
        lines = output.split("\n")
        total = len(lines)
        content_type = _detect_content_type(output)

        # ── 结构化内容：保留结构行 + 关键行 + 首尾 ──
        if content_type in ("html", "json", "xml"):
            keep_indices = set(range(min(GenericParser._KEEP_HEAD_LINES, total)))
            keep_indices.update(range(max(0, total - GenericParser._KEEP_TAIL_LINES), total))

            structure_check = {
                "html": _is_html_structure_line,
                "json": _is_json_structure_line,
                "xml": _is_xml_structure_line,
            }[content_type]

            for i, line in enumerate(lines):
                stripped = line.strip()
                if not stripped:
                    continue
                if structure_check(line) or _is_critical_line(line) or _has_keyword(stripped):
                    keep_indices.add(i)
                    # 上下文窗口（前后各 2 行）
                    for offset in (-2, -1, 1, 2):
                        if 0 <= i + offset < total:
                            keep_indices.add(i + offset)

            keep = sorted(keep_indices)
            compressed = [lines[i] for i in keep]
            saved = total - len(compressed)

            result = "\n".join(compressed)
            if saved > 0:
                result += (
                    f"\n[解析器] 已压缩({content_type}): "
                    f"{total} 行 → {len(compressed)} 行 (过滤 {saved} 行)"
                )
            return result

        # ── 纯文本：关键词过滤 + 首尾截断 ──
        important = []
        for i, line in enumerate(lines):
            s = line.strip()
            if not s:
                continue
            if _has_keyword(s) or _is_critical_line(s):
                important.append((i, s))

        keep_indices = set(range(min(GenericParser._KEEP_HEAD_LINES, total)))
        keep_indices.update(range(max(0, total - GenericParser._KEEP_TAIL_LINES), total))
        for idx, _ in important:
            keep_indices.add(idx)
            if idx - 1 >= 0:
                keep_indices.add(idx - 1)
            if idx + 1 < total:
                keep_indices.add(idx + 1)

        keep = sorted(keep_indices)
        compressed = [lines[i] for i in keep]
        saved = total - len(compressed)

        result = "\n".join(compressed)
        if saved > 0:
            result += (
                f"\n[解析器] 已压缩: {total} 行 → {len(compressed)} 行 (过滤 {saved} 行)"
            )
        return result


# ═════════════════════════════════════════════════════════════════════
# 主入口
# ═════════════════════════════════════════════════════════════════════

_PARSERS = [
    PortScanParser(),
    WebReconParser(),
    VulnScanParser(),
    DirBruteParser(),
    HttpResultParser(),
]


_MIN_PARSE_LENGTH = 100  # 低于此长度直接透传，避免解析器添加额外元信息


def parse(tool_name: str, output: str) -> str:
    """解析工具输出，返回压缩后的摘要。

    Args:
        tool_name: 工具名称（如 network_tool, web_tools）
        output: 原始工具输出文本

    Returns:
        解析后的摘要文本（未匹配解析器时返回原始文本）。
    """
    if not output or len(output) < _MIN_PARSE_LENGTH:
        return output

    for parser in _PARSERS:
        if parser.can_parse(output):
            try:
                compressed = parser.parse(output)
                saved = len(output) - len(compressed)
                if saved > 50:
                    logger.debug("解析器 %s 节省 %d 字符 (%.0f%%)",
                                 type(parser).__name__, saved,
                                 saved / len(output) * 100)
                return compressed
            except Exception as e:
                logger.warning("解析器 %s 失败: %s, 回退原始输出",
                               type(parser).__name__, e)
                return output

    # 无特定解析器匹配 → 通用压缩
    if len(output) > GenericParser.MIN_LENGTH:
        return GenericParser.parse(output)

    return output
