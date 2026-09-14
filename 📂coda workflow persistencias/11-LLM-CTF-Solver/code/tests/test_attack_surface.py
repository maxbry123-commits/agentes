"""attack_surface.py 测试 — 目标/服务/漏洞的注册与去重。"""

from agent.attack_surface import AttackSurface, Target, Service, Finding


class TestAttackSurface:
    """攻击面管理器核心操作。"""

    def setup_method(self):
        self.asurf = AttackSurface()

    def test_initial_state(self):
        assert len(self.asurf.targets) == 0
        assert len(self.asurf.findings) == 0
        summary = self.asurf.get_summary()
        assert "尚未发现目标" in summary

    def test_get_or_create_target(self):
        t = self.asurf.get_or_create_target("192.168.1.1", "ip")
        assert t.host == "192.168.1.1"
        assert len(self.asurf.targets) == 1

    def test_duplicate_target_returns_same(self):
        t1 = self.asurf.get_or_create_target("10.0.0.1")
        t2 = self.asurf.get_or_create_target("10.0.0.1")
        assert t1 is t2
        assert len(self.asurf.targets) == 1

    def test_add_service(self):
        svc = self.asurf.add_service("10.0.0.1", 80, "tcp", "http")
        assert svc.port == 80
        assert svc.service_name == "http"
        target = self.asurf.targets["10.0.0.1"]
        assert 80 in target.services

    def test_duplicate_service_merged(self):
        self.asurf.add_service("10.0.0.1", 80, "tcp", "http")
        self.asurf.add_service("10.0.0.1", 80, "tcp", "apache")  # 更新 service_name
        target = self.asurf.targets["10.0.0.1"]
        assert len(target.services) == 1

    def test_add_finding(self):
        f = self.asurf.add_finding(
            finding_type="SQL Injection",
            severity="critical",
            target="10.0.0.1",
            evidence="SQL syntax error",
        )
        assert f is not None
        assert f.severity == "critical"
        assert len(self.asurf.findings) == 1

    def test_duplicate_finding_returns_none(self):
        self.asurf.add_finding("XSS", "high", "10.0.0.1", "reflected")
        f2 = self.asurf.add_finding("XSS", "high", "10.0.0.1", "reflected")
        assert f2 is None
        assert len(self.asurf.findings) == 1

    def test_get_summary_contains_info(self):
        self.asurf.get_or_create_target("10.0.0.1")
        self.asurf.add_service("10.0.0.1", 22, "tcp", "ssh")
        summary = self.asurf.get_summary()
        assert "10.0.0.1" in summary
        assert "22" in summary

    def test_serialize_roundtrip(self):
        self.asurf.get_or_create_target("10.0.0.1")
        self.asurf.add_service("10.0.0.1", 80, "tcp", "http")
        self.asurf.add_finding("SQLi", "high", "10.0.0.1", "error")

        data = self.asurf.to_dict()
        restored = AttackSurface.from_dict(data)

        assert "10.0.0.1" in restored.targets
        assert restored.targets["10.0.0.1"].services[80].port == 80
        assert len(restored.findings) == 1
        assert restored.findings[0].type == "SQLi"

    def test_empty_serialize(self):
        data = self.asurf.to_dict()
        restored = AttackSurface.from_dict(data)
        assert len(restored.targets) == 0
        assert len(restored.findings) == 0

    def test_add_technology(self):
        self.asurf.get_or_create_target("10.0.0.1")
        self.asurf.add_technology("10.0.0.1", "nginx")
        assert "nginx" in self.asurf.targets["10.0.0.1"].technologies

    def test_covered_labels(self):
        self.asurf.add_covered_label("port:80")
        self.asurf.add_covered_label("port:443")
        summary = self.asurf.get_summary()
        assert "port:80" in summary
        assert "port:443" in summary

    def test_analyze_step_port_scan(self):
        """端口扫描输出解析。"""
        tool_args = {"action": "port_scan", "host": "10.0.0.1"}
        output = "端口检测完成:\n  80/tcp  open  Apache httpd\n  22/tcp  open  OpenSSH"
        self.asurf.analyze_step("network_tool", tool_args, output, {})
        assert "10.0.0.1" in self.asurf.targets
        target = self.asurf.targets["10.0.0.1"]
        assert 80 in target.services
        assert 22 in target.services


class TestTarget:

    def test_create_target(self):
        t = Target(host="10.0.0.1")
        assert t.host == "10.0.0.1"
        assert t.host_type == "ip"

    def test_target_host_type_domain(self):
        t = Target(host="example.com", host_type="domain")
        assert t.host_type == "domain"


class TestService:

    def test_create_service(self):
        s = Service(port=80, protocol="tcp", service_name="http")
        assert s.port == 80
        assert s.service_name == "http"


class TestFinding:

    def test_create_finding(self):
        f = Finding(type="XSS", severity="high", affected_component="/page")
        assert f.type == "XSS"
        assert f.severity == "high"

    def test_finding_with_all_fields(self):
        f = Finding(
            type="SQLi", severity="critical", confidence="confirmed",
            evidence="error", cvss_base=9.0,
            affected_component="/login", owasp_category="A01",
        )
        assert f.cvss_base == 9.0
        assert f.owasp_category == "A01"
