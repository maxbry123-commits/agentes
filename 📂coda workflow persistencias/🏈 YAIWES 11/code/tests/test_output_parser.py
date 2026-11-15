"""output_parser.py 测试 — 各解析器正确压缩/保留关键信息。"""

from utils.output_parser import parse


class TestPortScanParser:
    """端口扫描结果解析。"""

    def test_extracts_open_ports(self):
        out = "端口检测完成:\n  80/tcp  open  Apache httpd\n  443/tcp  open  nginx"
        result = parse("network_tool", out)
        assert "80/tcp" in result
        assert "Apache" in result
        assert "nginx" in result

    def test_empty_result(self):
        out = "端口检测完成: 未发现开放端口"
        result = parse("network_tool", out)
        assert "未发现" in result

    def test_single_port(self):
        out = "端口检测完成:\n  8080/tcp  open  Tomcat"
        result = parse("network_tool", out)
        assert "8080/tcp" in result


class TestHttpResultParser:
    """HTTP 响应解析。"""

    def test_status_and_headers(self):
        out = "HTTP 200 1024 bytes\nContent-Type: text/html\nServer: nginx\n\n<html>body</html>"
        result = parse("network_tool", out)
        assert "HTTP 200" in result
        assert "Server: nginx" in result
        assert "body" in result

    def test_error_status(self):
        out = "HTTP 500 0 bytes\n\nInternal Server Error"
        result = parse("network_tool", out)
        assert "HTTP 500" in result


class TestDirBruteParser:
    """目录爆破解析。"""

    def test_found_directories(self):
        out = "目录爆破完成 (发现 3 个):\n  200  100B  /admin\n  301  300B  /api"
        result = parse("network_tool", out)
        assert "/admin" in result
        assert "/api" in result

    def test_nothing_found(self):
        out = "目录爆破完成: 未发现路径 (共检查 340 个)"
        result = parse("network_tool", out)
        assert "未发现" in result


class TestWebReconParser:
    """Web 侦查解析。"""

    def test_tech_stack(self):
        out = (
            "=== Web 侦查: http://target.com ===\n"
            "--- 技术栈指纹 ---\n"
            "  + WordPress\n  + PHP"
        )
        result = parse("web_tools", out)
        assert "WordPress" in result
        assert "PHP" in result

    def test_sensitive_files(self):
        out = (
            "=== Web 侦查: http://target.com ===\n"
            "--- 敏感文件探测 ---\n"
            "  [200] /robots.txt (120B)\n"
            "  [403] /.git/HEAD (0B)"
        )
        result = parse("web_tools", out)
        assert "/robots.txt" in result
        assert "/.git" in result

    def test_missing_security_headers(self):
        out = (
            "=== Web 侦查: http://target.com ===\n"
            "⚠ 缺失安全头:\n"
            "  - 缺少 CSP"
        )
        result = parse("web_tools", out)
        assert "CSP" in result or "缺失" in result


class TestVulnScanParser:
    """漏洞扫描检测解析。"""

    def test_sqli_finding(self):
        out = (
            "=== SQL 注入检测: http://x.com ===\n"
            "测试参数: id\n"
            "  [错误型] 单引号: MySQL syntax error\n"
            "⚠ 发现 1 个 SQL 注入迹象"
        )
        result = parse("web_tools", out)
        assert "SQL" in result or "错误型" in result

    def test_xss_finding(self):
        out = (
            "=== XSS 检测: http://x.com ===\n"
            "  [反射] script — Payload 原样回显 (高危)\n"
            "⚠ 发现 1 个 XSS 迹象"
        )
        result = parse("web_tools", out)
        assert "XSS" in result or "反射" in result

    def test_no_vuln(self):
        out = "=== SQL 注入检测: http://x.com ===\n未发现 SQL 注入迹象"
        result = parse("web_tools", out)
        assert "未发现" in result


class TestGenericParser:
    """通用降级压缩。"""

    def test_short_output_passthrough(self):
        """短输出直接透传。"""
        text = "Everything is fine, no issues."
        assert parse("unknown", text) == text

    def test_long_output_compressed(self):
        """长输出应被压缩。"""
        lines = [f"line {i}: data" for i in range(200)]
        text = "\n".join(lines)
        result = parse("unknown", text)
        result_lines = result.split("\n")
        assert len(result_lines) < len(lines)
        assert "[解析器]" in result

    def test_keywords_preserved_in_long_output(self):
        """含关键词的行应保留。"""
        lines = [f"line {i}: ok" for i in range(100)]
        lines.insert(50, "critical: buffer overflow found")
        result = parse("unknown", "\n".join(lines))
        assert "buffer overflow" in result

    def test_empty_output_passthrough(self):
        assert parse("x", "") == ""
        assert parse("x", None) is None


class TestEdgeCases:
    """边界情况。"""

    def test_output_just_under_threshold(self):
        """刚好低于解析阈值（100 字符）应透传。"""
        text = "a" * 99
        assert parse("x", text) == text

    def test_output_at_threshold(self):
        """刚好达到解析阈值。"""
        text = "a" * 100
        result = parse("x", text)
        assert result is not None  # 不崩溃即可

    def test_unicode_content(self):
        """Unicode 内容不应导致编码错误。"""
        text = "端口扫描结果:\n  80/tcp  开放  Apache\n中文内容测试"
        result = parse("network_tool", text)
        assert "80/tcp" in result
