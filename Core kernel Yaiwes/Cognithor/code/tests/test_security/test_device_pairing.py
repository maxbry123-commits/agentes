"""Tests fuer das Device Pairing System."""

from __future__ import annotations

import json
import tempfile
import time
from pathlib import Path

from cognithor.security.device_pairing import DevicePairingManager


def _make_manager(ttl_days: int = 180) -> DevicePairingManager:
    td = tempfile.mkdtemp()
    return DevicePairingManager(
        master_secret="test-secret-key-12345",
        storage_path=Path(td) / "devices.json",
        token_ttl_days=ttl_days,
    )


class TestCreatePairingToken:
    def test_creates_token(self):
        mgr = _make_manager()
        pt = mgr.create_pairing_token("iPhone 15")
        assert pt.token
        assert pt.device_id
        assert pt.expires_at > time.time()

    def test_device_registered(self):
        mgr = _make_manager()
        mgr.create_pairing_token("Pixel 9")
        devices = mgr.list_devices()
        assert len(devices) == 1
        assert devices[0]["name"] == "Pixel 9"
        assert devices[0]["active"]


class TestVerifyToken:
    def test_valid_token(self):
        mgr = _make_manager()
        pt = mgr.create_pairing_token("Test Device")
        assert mgr.verify_token(pt.token, pt.device_id)

    def test_wrong_token(self):
        mgr = _make_manager()
        pt = mgr.create_pairing_token("Test")
        assert not mgr.verify_token("wrong-token", pt.device_id)

    def test_wrong_device_id(self):
        mgr = _make_manager()
        pt = mgr.create_pairing_token("Test")
        assert not mgr.verify_token(pt.token, "wrong-id")

    def test_expired_token(self):
        mgr = _make_manager(ttl_days=0)
        pt = mgr.create_pairing_token("Expiring")
        # Token with 0 days TTL expires immediately
        mgr._devices[pt.device_id].expires_at = time.time() - 1
        assert not mgr.verify_token(pt.token, pt.device_id)

    def test_revoked_token(self):
        mgr = _make_manager()
        pt = mgr.create_pairing_token("Revokable")
        mgr.revoke_device(pt.device_id)
        assert not mgr.verify_token(pt.token, pt.device_id)

    def test_updates_last_seen(self):
        mgr = _make_manager()
        pt = mgr.create_pairing_token("Tracker")
        assert mgr._devices[pt.device_id].last_seen == 0.0
        mgr.verify_token(pt.token, pt.device_id)
        assert mgr._devices[pt.device_id].last_seen > 0


class TestRevokeDevice:
    def test_revoke_success(self):
        mgr = _make_manager()
        pt = mgr.create_pairing_token("Test")
        assert mgr.revoke_device(pt.device_id)
        devices = mgr.list_devices()
        assert devices[0]["revoked"]
        assert not devices[0]["active"]

    def test_revoke_unknown(self):
        mgr = _make_manager()
        assert not mgr.revoke_device("nonexistent")


class TestListDevices:
    def test_multiple_devices(self):
        mgr = _make_manager()
        mgr.create_pairing_token("Device A")
        mgr.create_pairing_token("Device B")
        mgr.create_pairing_token("Device C")
        assert len(mgr.list_devices()) == 3


class TestQRPayload:
    def test_payload_format(self):
        mgr = _make_manager()
        pt = mgr.create_pairing_token("Mobile")
        payload = mgr.qr_payload(pt, "192.168.1.100", 8741)
        data = json.loads(payload)
        assert data["type"] == "cognithor_pair"
        assert data["host"] == "192.168.1.100"
        assert data["port"] == 8741
        assert data["device_id"] == pt.device_id
        assert data["token"] == pt.token


class TestPersistence:
    def test_save_and_load(self):
        td = tempfile.mkdtemp()
        path = Path(td) / "devices.json"

        mgr1 = DevicePairingManager("secret", storage_path=path)
        pt = mgr1.create_pairing_token("Persistent")

        mgr2 = DevicePairingManager("secret", storage_path=path)
        assert len(mgr2.list_devices()) == 1
        assert mgr2.verify_token(pt.token, pt.device_id)


class TestCleanup:
    def test_removes_old_expired(self):
        mgr = _make_manager()
        pt = mgr.create_pairing_token("Old")
        # Make it expired + 31 days (past grace period)
        mgr._devices[pt.device_id].expires_at = time.time() - 86400 * 31
        removed = mgr.cleanup_expired()
        assert removed == 1
        assert len(mgr.list_devices()) == 0
