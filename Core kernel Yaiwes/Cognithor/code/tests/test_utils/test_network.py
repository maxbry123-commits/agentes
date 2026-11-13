"""Tests fuer Netzwerk-Utilities."""

from __future__ import annotations

from cognithor.utils.network import (
    get_primary_bind_host,
    get_reachable_url,
    is_loopback,
    is_tailscale_ip,
    is_trusted_ip,
)


class TestIsLoopback:
    def test_ipv4_loopback(self):
        assert is_loopback("127.0.0.1")

    def test_ipv4_loopback_other(self):
        assert is_loopback("127.0.0.2")

    def test_ipv6_loopback(self):
        assert is_loopback("::1")

    def test_localhost(self):
        assert is_loopback("localhost")

    def test_not_loopback(self):
        assert not is_loopback("192.168.1.1")

    def test_tailscale_not_loopback(self):
        assert not is_loopback("100.100.1.1")


class TestIsTailscaleIp:
    def test_tailscale_cgnat(self):
        assert is_tailscale_ip("100.64.0.1")

    def test_tailscale_typical(self):
        assert is_tailscale_ip("100.100.50.25")

    def test_tailscale_upper_bound(self):
        assert is_tailscale_ip("100.127.255.255")

    def test_not_tailscale(self):
        assert not is_tailscale_ip("192.168.1.1")

    def test_loopback_not_tailscale(self):
        assert not is_tailscale_ip("127.0.0.1")

    def test_public_100(self):
        # 100.0.0.1 is outside CGNAT range (100.64/10)
        assert not is_tailscale_ip("100.0.0.1")


class TestIsTrustedIp:
    def test_loopback_trusted(self):
        assert is_trusted_ip("127.0.0.1")

    def test_ipv6_loopback_trusted(self):
        assert is_trusted_ip("::1")

    def test_tailscale_trusted(self):
        assert is_trusted_ip("100.100.1.1")

    def test_lan_not_trusted(self):
        assert not is_trusted_ip("192.168.1.100")

    def test_public_not_trusted(self):
        assert not is_trusted_ip("8.8.8.8")


class TestGetPrimaryBindHost:
    def test_explicit_host(self):
        assert get_primary_bind_host("192.168.1.50") == "192.168.1.50"

    def test_no_tailscale_defaults_localhost(self):
        # Without Tailscale, should default to 127.0.0.1
        # (may be 0.0.0.0 if Tailscale IS running on the test machine)
        host = get_primary_bind_host(None)
        assert host in ("127.0.0.1", "0.0.0.0")


class TestGetReachableUrl:
    def test_localhost_bind(self):
        url = get_reachable_url("127.0.0.1", 8741)
        assert url == "http://localhost:8741"

    def test_specific_host(self):
        url = get_reachable_url("192.168.1.50", 9000)
        assert url == "http://192.168.1.50:9000"

    def test_wildcard_bind(self):
        url = get_reachable_url("0.0.0.0", 8741)
        # Should resolve to a concrete IP, not 0.0.0.0
        assert "0.0.0.0" not in url
        assert ":8741" in url
