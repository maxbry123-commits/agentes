"""Tests fuer den Network Endpoint Manager."""

from __future__ import annotations

import tempfile
from pathlib import Path

from cognithor.core.network_endpoints import (
    InterfaceType,
    NetworkEndpointManager,
    classify_ip,
    detect_interfaces,
)


class TestClassifyIp:
    def test_loopback_v4(self):
        assert classify_ip("127.0.0.1") == InterfaceType.LOOPBACK

    def test_loopback_v6(self):
        assert classify_ip("::1") == InterfaceType.LOOPBACK

    def test_localhost(self):
        assert classify_ip("localhost") == InterfaceType.LOOPBACK

    def test_tailscale(self):
        assert classify_ip("100.100.50.1") == InterfaceType.TAILSCALE

    def test_tailscale_edge(self):
        assert classify_ip("100.64.0.1") == InterfaceType.TAILSCALE

    def test_zerotier(self):
        assert classify_ip("172.28.1.1") == InterfaceType.ZEROTIER

    def test_zerotier_managed(self):
        assert classify_ip("10.147.0.5") == InterfaceType.ZEROTIER

    def test_lan_192(self):
        assert classify_ip("192.168.1.100") == InterfaceType.LAN

    def test_lan_10(self):
        assert classify_ip("10.0.0.1") == InterfaceType.LAN

    def test_public(self):
        assert classify_ip("8.8.8.8") == InterfaceType.UNKNOWN


class TestDetectInterfaces:
    def test_returns_list(self):
        result = detect_interfaces()
        assert isinstance(result, list)

    def test_loopback_always_present(self):
        result = detect_interfaces()
        loopbacks = [i for i in result if i.interface_type == InterfaceType.LOOPBACK.value]
        assert len(loopbacks) >= 1

    def test_interface_has_fields(self):
        result = detect_interfaces()
        for iface in result:
            assert iface.ip
            assert iface.interface_type
            assert iface.label


class TestNetworkEndpointManager:
    def _make(self) -> NetworkEndpointManager:
        td = tempfile.mkdtemp()
        return NetworkEndpointManager(config_path=Path(td) / "endpoints.json")

    def test_default_bind_host(self):
        mgr = self._make()
        host = mgr.get_bind_host()
        assert host in ("127.0.0.1", "0.0.0.0")

    def test_set_enabled_ips(self):
        mgr = self._make()
        mgr.set_enabled_ips(["192.168.1.50"])
        assert mgr.get_bind_host() == "0.0.0.0"

    def test_set_auto_detect(self):
        mgr = self._make()
        mgr.set_auto_detect(False)
        mgr.set_enabled_ips([])
        # With no enabled IPs and no auto-detect, only loopback
        assert mgr.get_bind_host() == "127.0.0.1"

    def test_persistence(self):
        td = tempfile.mkdtemp()
        path = Path(td) / "endpoints.json"
        mgr1 = NetworkEndpointManager(config_path=path)
        mgr1.set_enabled_ips(["10.0.0.5"])
        mgr2 = NetworkEndpointManager(config_path=path)
        assert "10.0.0.5" in mgr2._config.enabled_ips

    def test_get_detected_interfaces(self):
        mgr = self._make()
        ifaces = mgr.get_detected_interfaces()
        assert isinstance(ifaces, list)
        for i in ifaces:
            assert "ip" in i
            assert "enabled" in i
            assert "interface_type" in i
            assert "label" in i

    def test_get_active_ips(self):
        mgr = self._make()
        active = mgr.get_active_ips()
        assert isinstance(active, list)
        assert "127.0.0.1" in active  # Loopback always active
