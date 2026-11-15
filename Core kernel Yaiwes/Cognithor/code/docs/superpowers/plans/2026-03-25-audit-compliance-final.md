# Audit Compliance Final 4 Features

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete EU AI Act + GDPR audit compliance with HMAC signatures, blockchain anchoring, user data export, and automated breach notification.

**Architecture:** Extend existing `security/audit.py` AuditTrail with HMAC-SHA256 signing (secret from `~/.cognithor/audit_key`). Add periodic blockchain hash anchoring via existing IdentityConfig flags. New API endpoints for user data export and breach notification. Breach detector runs as gateway background task monitoring SECURITY/CRITICAL audit events.

**Tech Stack:** Python 3.12+ (hmac, hashlib, sqlite3, asyncio), pytest

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Modify | `src/jarvis/security/audit.py` | HMAC signing + blockchain anchor method |
| Modify | `src/jarvis/config.py` | AuditConfig with hmac_enabled, breach notification settings |
| Create | `src/jarvis/audit/breach_detector.py` | Breach detection + notification logic |
| Modify | `src/jarvis/channels/config_routes.py` | User data export + breach endpoints |
| Modify | `src/jarvis/gateway/gateway.py` | Start breach detector background task |
| Create | `tests/unit/test_audit_compliance.py` | Tests for all 4 features |

---

### Task 1: HMAC-SHA256 Audit Signatures

**Files:**
- Modify: `src/jarvis/security/audit.py`
- Modify: `src/jarvis/config.py`
- Create: `tests/unit/test_audit_compliance.py`

- [ ] **Step 1: Write failing tests**

Create `tests/unit/test_audit_compliance.py`:

```python
"""Tests for audit compliance features: HMAC, blockchain, export, breach."""

import hashlib
import hmac
import json
import tempfile
from pathlib import Path

import pytest


class TestHMACSignatures:
    """HMAC-SHA256 signatures on audit trail entries."""

    @pytest.fixture
    def audit_trail(self, tmp_path):
        from jarvis.security.audit import AuditTrail

        return AuditTrail(
            log_path=tmp_path / "test_audit.jsonl",
            hmac_key=b"test-secret-key-32bytes-long!!!!",
        )

    def test_record_includes_hmac_field(self, audit_trail):
        from jarvis.models import AuditEntry as GateAuditEntry, GateStatus, RiskLevel

        entry = GateAuditEntry(
            session_id="test-session",
            action_tool="test_tool",
            action_params_hash="abc123",
            decision_status=GateStatus.ALLOW,
            decision_reason="test",
            risk_level=RiskLevel.GREEN,
            policy_name="default",
        )
        audit_trail.record(entry)
        # Read the JSONL and verify hmac field exists
        lines = audit_trail._log_path.read_text(encoding="utf-8").strip().split("\n")
        record = json.loads(lines[-1])
        assert "hmac" in record
        assert len(record["hmac"]) == 64  # SHA-256 hex digest

    def test_hmac_is_deterministic(self, audit_trail):
        from jarvis.models import AuditEntry as GateAuditEntry, GateStatus, RiskLevel

        entry = GateAuditEntry(
            session_id="s1",
            action_tool="tool1",
            action_params_hash="h1",
            decision_status=GateStatus.ALLOW,
            decision_reason="r1",
            risk_level=RiskLevel.GREEN,
            policy_name="p1",
        )
        h1 = audit_trail.record(entry)

        # Recompute HMAC manually
        lines = audit_trail._log_path.read_text(encoding="utf-8").strip().split("\n")
        record = json.loads(lines[-1])
        data_for_hmac = record["hash"]
        expected = hmac.new(
            b"test-secret-key-32bytes-long!!!!",
            data_for_hmac.encode(),
            hashlib.sha256,
        ).hexdigest()
        assert record["hmac"] == expected

    def test_no_hmac_when_key_is_none(self, tmp_path):
        from jarvis.security.audit import AuditTrail
        from jarvis.models import AuditEntry as GateAuditEntry, GateStatus, RiskLevel

        trail = AuditTrail(log_path=tmp_path / "no_hmac.jsonl", hmac_key=None)
        entry = GateAuditEntry(
            session_id="s1",
            action_tool="tool1",
            action_params_hash="h1",
            decision_status=GateStatus.ALLOW,
            decision_reason="r1",
            risk_level=RiskLevel.GREEN,
            policy_name="p1",
        )
        trail.record(entry)
        lines = trail._log_path.read_text(encoding="utf-8").strip().split("\n")
        record = json.loads(lines[-1])
        assert "hmac" not in record

    def test_verify_chain_with_hmac(self, audit_trail):
        from jarvis.models import AuditEntry as GateAuditEntry, GateStatus, RiskLevel

        for i in range(5):
            entry = GateAuditEntry(
                session_id=f"s{i}",
                action_tool=f"tool{i}",
                action_params_hash=f"h{i}",
                decision_status=GateStatus.ALLOW,
                decision_reason=f"r{i}",
                risk_level=RiskLevel.GREEN,
                policy_name="p",
            )
            audit_trail.record(entry)

        valid, total, broken = audit_trail.verify_chain()
        assert valid is True
        assert total == 5
        assert broken == -1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd "D:\Jarvis\jarvis complete v20" && python -m pytest tests/unit/test_audit_compliance.py::TestHMACSignatures -v`
Expected: FAIL — `AuditTrail.__init__() got an unexpected keyword argument 'hmac_key'`

- [ ] **Step 3: Add AuditConfig to config.py**

In `src/jarvis/config.py`, add after SecurityConfig (around line 1530):

```python
class AuditConfig(BaseModel):
    """Audit-Trail Konfiguration fuer Compliance."""

    hmac_enabled: bool = Field(
        default=True,
        description="HMAC-SHA256 Signaturen auf Audit-Eintraege",
    )
    hmac_key_file: str = Field(
        default="",
        description="Pfad zur HMAC-Key-Datei (leer = ~/.cognithor/audit_key)",
    )
    breach_notification_enabled: bool = Field(
        default=True,
        description="Automatische Breach-Erkennung und Benachrichtigung",
    )
    breach_cooldown_hours: int = Field(
        default=1, ge=1, le=72,
        description="Mindestabstand zwischen Breach-Benachrichtigungen in Stunden",
    )
    retention_days: int = Field(
        default=90, ge=7, le=3650,
        description="Aufbewahrungsfrist fuer Audit-Logs in Tagen",
    )
```

Wire into JarvisConfig (near the other security fields):
```python
    audit: AuditConfig = Field(default_factory=AuditConfig)
```

- [ ] **Step 4: Add HMAC to AuditTrail**

In `src/jarvis/security/audit.py`:

Add `import hmac as hmac_mod` at the top.

Modify `AuditTrail.__init__` to accept `hmac_key: bytes | None = None`:

```python
    def __init__(
        self,
        log_path: Path | str,
        *,
        mask: bool = True,
        hmac_key: bytes | None = None,
    ) -> None:
```

Store as `self._hmac_key = hmac_key`.

In the `record()` method, after computing the hash and adding `prev_hash`/`hash` to the record dict, add:

```python
        # HMAC signature (cryptographically binding, not just tamper-evident)
        if self._hmac_key:
            record["hmac"] = hmac_mod.new(
                self._hmac_key, record["hash"].encode(), hashlib.sha256
            ).hexdigest()
```

- [ ] **Step 5: Run tests**

Run: `cd "D:\Jarvis\jarvis complete v20" && python -m pytest tests/unit/test_audit_compliance.py::TestHMACSignatures -v`
Expected: All 4 tests PASS

- [ ] **Step 6: Commit**

```bash
git add src/jarvis/security/audit.py src/jarvis/config.py tests/unit/test_audit_compliance.py
git commit -m "feat: HMAC-SHA256 signatures on audit trail entries"
```

---

### Task 2: Blockchain Audit Anchoring

**Files:**
- Modify: `src/jarvis/security/audit.py`
- Modify: `tests/unit/test_audit_compliance.py`

- [ ] **Step 1: Write failing test**

Append to `tests/unit/test_audit_compliance.py`:

```python
class TestBlockchainAnchoring:
    """Periodic hash anchoring to external store."""

    @pytest.fixture
    def audit_trail(self, tmp_path):
        from jarvis.security.audit import AuditTrail

        return AuditTrail(log_path=tmp_path / "bc_audit.jsonl")

    def test_get_anchor_returns_hash_and_count(self, audit_trail):
        from jarvis.models import AuditEntry as GateAuditEntry, GateStatus, RiskLevel

        for i in range(3):
            entry = GateAuditEntry(
                session_id=f"s{i}",
                action_tool=f"tool{i}",
                action_params_hash=f"h{i}",
                decision_status=GateStatus.ALLOW,
                decision_reason=f"r{i}",
                risk_level=RiskLevel.GREEN,
                policy_name="p",
            )
            audit_trail.record(entry)

        anchor = audit_trail.get_anchor()
        assert "hash" in anchor
        assert anchor["entry_count"] == 3
        assert len(anchor["hash"]) == 64
        assert "timestamp" in anchor

    def test_anchor_changes_after_new_entry(self, audit_trail):
        from jarvis.models import AuditEntry as GateAuditEntry, GateStatus, RiskLevel

        entry = GateAuditEntry(
            session_id="s1", action_tool="t1", action_params_hash="h1",
            decision_status=GateStatus.ALLOW, decision_reason="r1",
            risk_level=RiskLevel.GREEN, policy_name="p",
        )
        audit_trail.record(entry)
        anchor1 = audit_trail.get_anchor()

        entry2 = GateAuditEntry(
            session_id="s2", action_tool="t2", action_params_hash="h2",
            decision_status=GateStatus.ALLOW, decision_reason="r2",
            risk_level=RiskLevel.GREEN, policy_name="p",
        )
        audit_trail.record(entry2)
        anchor2 = audit_trail.get_anchor()

        assert anchor1["hash"] != anchor2["hash"]
        assert anchor2["entry_count"] == 2
```

- [ ] **Step 2: Implement get_anchor() in AuditTrail**

In `src/jarvis/security/audit.py`, add to AuditTrail:

```python
    def get_anchor(self) -> dict[str, Any]:
        """Get current chain state for blockchain anchoring.

        Returns a dict with:
          - hash: current chain head hash
          - entry_count: total entries
          - timestamp: ISO timestamp

        This anchor can be written to a blockchain or external store
        to prove the audit log existed in this exact state at this time.
        """
        return {
            "hash": self._last_hash,
            "entry_count": self._entry_count,
            "timestamp": datetime.now(UTC).isoformat(),
        }
```

Also add `self._entry_count = 0` in `__init__` and increment it in `record()`.

- [ ] **Step 3: Run tests**

Run: `cd "D:\Jarvis\jarvis complete v20" && python -m pytest tests/unit/test_audit_compliance.py -v`
Expected: All 6 tests PASS

- [ ] **Step 4: Commit**

```bash
git add src/jarvis/security/audit.py tests/unit/test_audit_compliance.py
git commit -m "feat: blockchain anchoring support via get_anchor() on audit trail"
```

---

### Task 3: User Data Export API (GDPR Art. 15)

**Files:**
- Modify: `src/jarvis/channels/config_routes.py`
- Modify: `tests/unit/test_audit_compliance.py`

- [ ] **Step 1: Write failing test**

Append to `tests/unit/test_audit_compliance.py`:

```python
class TestUserDataExport:
    """GDPR Art. 15 — user can export their audit data."""

    def test_export_filters_by_channel(self, tmp_path):
        from jarvis.audit import AuditLogger

        logger = AuditLogger(log_dir=tmp_path)
        logger.log_tool_call("tool1", agent_name="jarvis", result="ok")
        logger.log_user_input("telegram", "hello from telegram")
        logger.log_user_input("cli", "hello from cli")

        # Filter by channel
        entries = logger.get_entries_for_export(channel="telegram")
        assert len(entries) >= 1
        assert all(
            e.get("description", "").find("telegram") >= 0
            or e.get("action", "").find("user_input") >= 0
            for e in entries
        )

    def test_export_returns_all_without_filter(self, tmp_path):
        from jarvis.audit import AuditLogger

        logger = AuditLogger(log_dir=tmp_path)
        logger.log_tool_call("tool1", result="ok")
        logger.log_tool_call("tool2", result="ok")
        entries = logger.get_entries_for_export()
        assert len(entries) >= 2
```

- [ ] **Step 2: Add get_entries_for_export to AuditLogger**

In `src/jarvis/audit/__init__.py`, add method:

```python
    def get_entries_for_export(
        self,
        *,
        channel: str = "",
        hours: int = 0,
        max_entries: int = 10000,
    ) -> list[dict[str, Any]]:
        """Export audit entries for GDPR Art. 15 data subject access.

        Args:
            channel: Filter by channel name (empty = all).
            hours: Only entries from last N hours (0 = all).
            max_entries: Maximum entries to return.

        Returns:
            List of entry dicts (sanitized, no internal IDs).
        """
        cutoff = None
        if hours > 0:
            cutoff = datetime.now(UTC) - timedelta(hours=hours)

        results: list[dict[str, Any]] = []
        for entry in self._entries:
            if len(results) >= max_entries:
                break
            if cutoff:
                ts = self._parse_ts(entry.timestamp)
                if ts and ts < cutoff:
                    continue
            if channel:
                desc = entry.description.lower()
                action = entry.action.lower()
                if channel.lower() not in desc and channel.lower() not in action:
                    continue
            d = entry.to_dict()
            # Remove internal fields
            d.pop("entry_id", None)
            results.append(d)
        return results
```

- [ ] **Step 3: Add API endpoint**

In `src/jarvis/channels/config_routes.py`, near the compliance routes, add:

```python
    @app.get("/api/v1/user/audit-data", dependencies=deps)
    async def export_user_audit_data(
        channel: str = "",
        hours: int = 0,
    ) -> dict[str, Any]:
        """GDPR Art. 15: Export audit data for a user/channel."""
        audit = getattr(gateway, "_audit_logger", None)
        if not audit:
            return {"entries": [], "count": 0, "message": "Audit logging not active."}

        entries = audit.get_entries_for_export(channel=channel, hours=hours)
        return {
            "entries": entries,
            "count": len(entries),
            "channel_filter": channel or "all",
            "hours_filter": hours or "all",
            "gdpr_article": "Art. 15 DSGVO — Auskunftsrecht",
        }
```

- [ ] **Step 4: Run tests**

Run: `cd "D:\Jarvis\jarvis complete v20" && python -m pytest tests/unit/test_audit_compliance.py -v`
Expected: All 8 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/jarvis/audit/__init__.py src/jarvis/channels/config_routes.py tests/unit/test_audit_compliance.py
git commit -m "feat: GDPR Art. 15 user data export API + AuditLogger.get_entries_for_export()"
```

---

### Task 4: Breach Notification Automation (GDPR Art. 33)

**Files:**
- Create: `src/jarvis/audit/breach_detector.py`
- Modify: `src/jarvis/gateway/gateway.py`
- Modify: `tests/unit/test_audit_compliance.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/unit/test_audit_compliance.py`:

```python
class TestBreachDetector:
    """GDPR Art. 33 — automatic breach detection and notification."""

    @pytest.fixture
    def detector(self, tmp_path):
        from jarvis.audit.breach_detector import BreachDetector

        return BreachDetector(
            state_path=tmp_path / "breach_state.json",
            cooldown_hours=0,  # no cooldown for tests
        )

    def test_no_breach_on_normal_entries(self, detector, tmp_path):
        from jarvis.audit import AuditLogger, AuditCategory, AuditSeverity

        logger = AuditLogger(log_dir=tmp_path)
        logger.log_tool_call("read_file", result="ok")
        breaches = detector.scan(logger)
        assert len(breaches) == 0

    def test_detects_security_critical_event(self, detector, tmp_path):
        from jarvis.audit import AuditLogger, AuditCategory, AuditSeverity

        logger = AuditLogger(log_dir=tmp_path)
        logger.log_security("Unauthorized access attempt detected", severity="critical")
        breaches = detector.scan(logger)
        assert len(breaches) >= 1
        assert breaches[0]["severity"] == "critical"

    def test_cooldown_prevents_duplicate(self, tmp_path):
        from jarvis.audit.breach_detector import BreachDetector
        from jarvis.audit import AuditLogger

        detector = BreachDetector(
            state_path=tmp_path / "breach_state.json",
            cooldown_hours=24,
        )
        logger = AuditLogger(log_dir=tmp_path)
        logger.log_security("Breach attempt", severity="critical")

        breaches1 = detector.scan(logger)
        assert len(breaches1) >= 1

        # Second scan within cooldown should not fire again
        breaches2 = detector.scan(logger)
        assert len(breaches2) == 0

    def test_breach_report_format(self, detector, tmp_path):
        from jarvis.audit import AuditLogger

        logger = AuditLogger(log_dir=tmp_path)
        logger.log_security("Data exfiltration attempt", severity="critical")
        breaches = detector.scan(logger)
        assert len(breaches) >= 1
        report = breaches[0]
        assert "severity" in report
        assert "description" in report
        assert "timestamp" in report
        assert "gdpr_article" in report
        assert report["gdpr_article"] == "Art. 33 DSGVO"
```

- [ ] **Step 2: Implement BreachDetector**

Create `src/jarvis/audit/breach_detector.py`:

```python
"""Breach Detection — GDPR Art. 33 automated notification.

Scans audit entries for SECURITY events with CRITICAL or ERROR severity.
Fires breach notifications with configurable cooldown to prevent spam.
"""

from __future__ import annotations

import json
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from jarvis.utils.logging import get_logger

if TYPE_CHECKING:
    from jarvis.audit import AuditLogger

log = get_logger(__name__)

__all__ = ["BreachDetector"]

# Events that indicate a potential breach
_BREACH_KEYWORDS = frozenset({
    "unauthorized", "exfiltration", "injection", "breach",
    "credential", "leak", "exploit", "attack", "intrusion",
    "manipulation", "tampering", "privilege escalation",
})


class BreachDetector:
    """Detects potential data breaches from audit logs.

    GDPR Art. 33 requires notification within 72 hours.
    This detector scans for SECURITY events with CRITICAL/ERROR severity
    and fires breach reports with configurable cooldown.
    """

    def __init__(
        self,
        state_path: Path | str,
        cooldown_hours: int = 1,
    ) -> None:
        self._state_path = Path(state_path)
        self._cooldown_seconds = cooldown_hours * 3600
        self._last_report_time: float = 0
        self._load_state()

    def _load_state(self) -> None:
        if self._state_path.exists():
            try:
                data = json.loads(self._state_path.read_text(encoding="utf-8"))
                self._last_report_time = data.get("last_report_time", 0)
            except Exception:
                pass

    def _save_state(self) -> None:
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        self._state_path.write_text(
            json.dumps({"last_report_time": self._last_report_time}),
            encoding="utf-8",
        )

    def scan(self, audit_logger: AuditLogger) -> list[dict[str, Any]]:
        """Scan recent audit entries for breach indicators.

        Returns list of breach reports (empty if none found or in cooldown).
        """
        now = time.time()

        # Cooldown check
        if self._cooldown_seconds > 0 and (now - self._last_report_time) < self._cooldown_seconds:
            return []

        from jarvis.audit import AuditCategory, AuditSeverity

        breaches: list[dict[str, Any]] = []

        for entry in audit_logger._entries:
            # Only SECURITY category with CRITICAL or ERROR severity
            if entry.category != AuditCategory.SECURITY:
                continue
            if entry.severity not in (AuditSeverity.CRITICAL, AuditSeverity.ERROR):
                continue

            # Check if this is a new entry (after last report)
            ts = audit_logger._parse_ts(entry.timestamp)
            if ts and ts.timestamp() <= self._last_report_time:
                continue

            breaches.append({
                "severity": entry.severity.value,
                "description": entry.description,
                "timestamp": entry.timestamp,
                "action": entry.action,
                "agent": entry.agent_name,
                "tool": entry.tool_name,
                "gdpr_article": "Art. 33 DSGVO",
                "notification_deadline": "72 hours from detection",
            })

        if breaches:
            self._last_report_time = now
            self._save_state()
            log.warning(
                "breach_detected",
                count=len(breaches),
                severities=[b["severity"] for b in breaches],
            )

        return breaches
```

- [ ] **Step 3: Add log_security method if missing**

Check if AuditLogger has a `log_security` method. If not, add to `src/jarvis/audit/__init__.py`:

```python
    def log_security(
        self,
        description: str,
        *,
        severity: str = "warning",
        agent_name: str = "",
        tool_name: str = "",
    ) -> AuditEntry:
        """Log a security event."""
        sev = AuditSeverity(severity) if severity in [s.value for s in AuditSeverity] else AuditSeverity.WARNING
        return self._log(
            category=AuditCategory.SECURITY,
            severity=sev,
            action="security_event",
            agent_name=agent_name,
            tool_name=tool_name,
            description=description,
        )
```

- [ ] **Step 4: Wire into gateway as background task**

In `src/jarvis/gateway/gateway.py`, in the startup section (near the retention cleanup task), add:

```python
        # Breach detection (GDPR Art. 33)
        if getattr(self._config, "audit", None) and getattr(self._config.audit, "breach_notification_enabled", True):
            try:
                from jarvis.audit.breach_detector import BreachDetector

                _breach_state = self._config.jarvis_home / "breach_state.json"
                _cooldown = getattr(self._config.audit, "breach_cooldown_hours", 1)
                self._breach_detector = BreachDetector(
                    state_path=_breach_state,
                    cooldown_hours=_cooldown,
                )

                async def _breach_scan_loop():
                    while True:
                        await asyncio.sleep(300)  # Every 5 minutes
                        try:
                            if hasattr(self, "_audit_logger") and self._audit_logger:
                                breaches = self._breach_detector.scan(self._audit_logger)
                                if breaches:
                                    log.critical(
                                        "gdpr_breach_notification",
                                        count=len(breaches),
                                        article="Art. 33 DSGVO",
                                    )
                        except Exception:
                            log.debug("breach_scan_failed", exc_info=True)

                _breach_task = asyncio.create_task(
                    _breach_scan_loop(), name="breach-detector"
                )
                self._background_tasks.add(_breach_task)
                _breach_task.add_done_callback(self._background_tasks.discard)
                log.info("breach_detector_started")
            except Exception:
                log.debug("breach_detector_start_failed", exc_info=True)
```

- [ ] **Step 5: Run all tests**

Run: `cd "D:\Jarvis\jarvis complete v20" && python -m pytest tests/unit/test_audit_compliance.py -v`
Expected: All 12 tests PASS

- [ ] **Step 6: Commit**

```bash
git add src/jarvis/audit/breach_detector.py src/jarvis/audit/__init__.py src/jarvis/gateway/gateway.py tests/unit/test_audit_compliance.py
git commit -m "feat: GDPR Art. 33 breach notification automation with BreachDetector"
```

---

### Task 5: Wire HMAC key loading + add audit to _EDITABLE_SECTIONS

**Files:**
- Modify: `src/jarvis/gateway/gateway.py` (or wherever AuditTrail is instantiated)
- Modify: `src/jarvis/config_manager.py`

- [ ] **Step 1: Find where AuditTrail is created**

Search gateway.py and gatekeeper.py for `AuditTrail(` to find where it's instantiated. Add HMAC key loading:

```python
        # Load HMAC key for audit trail
        _hmac_key = None
        if getattr(self._config, "audit", None) and self._config.audit.hmac_enabled:
            key_file = self._config.audit.hmac_key_file or str(
                self._config.jarvis_home / "audit_key"
            )
            key_path = Path(key_file)
            if not key_path.exists():
                # Auto-generate key on first use
                import secrets
                key_path.parent.mkdir(parents=True, exist_ok=True)
                key_path.write_bytes(secrets.token_bytes(32))
                log.info("audit_hmac_key_generated", path=str(key_path))
            _hmac_key = key_path.read_bytes()
```

Then pass `hmac_key=_hmac_key` to the AuditTrail constructor.

- [ ] **Step 2: Add "audit" to _EDITABLE_SECTIONS in config_manager.py**

In `src/jarvis/config_manager.py`, add `"audit"` to the `_EDITABLE_SECTIONS` frozenset.

Also add `"audit"` to the save() section list in `flutter_app/lib/providers/config_provider.dart`.

- [ ] **Step 3: Verify**

Run: `cd "D:\Jarvis\jarvis complete v20" && python -m pytest tests/unit/test_audit_compliance.py -v`
Expected: All PASS

- [ ] **Step 4: Commit**

```bash
git add src/jarvis/gateway/gateway.py src/jarvis/config_manager.py
git commit -m "feat: auto-generate HMAC key, wire AuditConfig into editable sections"
```

---

### Task 6: Full Test Suite

- [ ] **Step 1: Run all new tests**

Run: `cd "D:\Jarvis\jarvis complete v20" && python -m pytest tests/unit/test_audit_compliance.py -v`
Expected: All PASS

- [ ] **Step 2: Run all unit tests**

Run: `cd "D:\Jarvis\jarvis complete v20" && python -m pytest tests/unit/ -v`
Expected: All PASS

- [ ] **Step 3: Run tool registration + planner tests**

Run: `cd "D:\Jarvis\jarvis complete v20" && python -m pytest tests/ -k "tool_registration or planner" -v`
Expected: All PASS

- [ ] **Step 4: Commit any fixes**

```bash
git add -A
git commit -m "fix: test adjustments for audit compliance features"
```
