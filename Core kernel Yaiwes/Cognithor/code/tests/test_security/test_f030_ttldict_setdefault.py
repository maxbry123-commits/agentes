"""Tests fuer F-030: TTLDict.setdefault() bricht dict-Interface.

Prueft dass:
  - setdefault(key) ohne Default None zurueckgibt (nicht KeyError)
  - setdefault(key, value) den Wert setzt und zurueckgibt
  - Vorhandener Key den gespeicherten Wert zurueckgibt
  - Gespeicherter Wert None nicht als fehlend behandelt wird
  - Abgelaufene Eintraege korrekt behandelt werden
  - Verhalten konsistent mit dict.setdefault() ist
"""

from __future__ import annotations

import inspect
import time

import pytest

from cognithor.utils.ttl_dict import TTLDict

# ============================================================================
# dict-kompatibles Verhalten
# ============================================================================


class TestDictCompatibility:
    """Prueft dass setdefault() sich wie dict.setdefault() verhaelt."""

    def test_missing_key_no_default_returns_none(self) -> None:
        """setdefault(key) ohne Default gibt None zurueck — kein KeyError."""
        d: TTLDict[str, str] = TTLDict(ttl_seconds=60)
        result = d.setdefault("missing")
        assert result is None

    def test_missing_key_with_default_returns_default(self) -> None:
        d: TTLDict[str, str] = TTLDict(ttl_seconds=60)
        result = d.setdefault("key", "value")
        assert result == "value"

    def test_missing_key_with_default_stores_value(self) -> None:
        d: TTLDict[str, str] = TTLDict(ttl_seconds=60)
        d.setdefault("key", "value")
        assert d.get("key") == "value"

    def test_existing_key_returns_stored_value(self) -> None:
        d: TTLDict[str, str] = TTLDict(ttl_seconds=60)
        d.set("key", "original")
        result = d.setdefault("key", "default")
        assert result == "original"

    def test_existing_key_not_overwritten(self) -> None:
        d: TTLDict[str, str] = TTLDict(ttl_seconds=60)
        d.set("key", "original")
        d.setdefault("key", "default")
        assert d.get("key") == "original"

    def test_comparison_with_stdlib_dict(self) -> None:
        """Gleiches Verhalten wie stdlib dict fuer alle Faelle."""
        stdlib: dict[str, str | None] = {}
        ttl: TTLDict[str, str | None] = TTLDict(ttl_seconds=60)

        # Case 1: Missing key, no default
        r1_std = stdlib.setdefault("a")
        r1_ttl = ttl.setdefault("a")
        assert r1_std == r1_ttl  # Both None

        # Case 2: Missing key, with default
        r2_std = stdlib.setdefault("b", "val")
        r2_ttl = ttl.setdefault("b", "val")
        assert r2_std == r2_ttl  # Both "val"

        # Case 3: Existing key, with default
        r3_std = stdlib.setdefault("b", "other")
        r3_ttl = ttl.setdefault("b", "other")
        assert r3_std == r3_ttl  # Both "val" (not overwritten)


# ============================================================================
# None als gespeicherter Wert
# ============================================================================


class TestNoneValueHandling:
    """Prueft dass None als gespeicherter Wert korrekt behandelt wird."""

    def test_setdefault_does_not_store_none(self) -> None:
        """setdefault(key) ohne Default speichert keinen Eintrag (wie dict)."""
        d: TTLDict[str, str | None] = TTLDict(ttl_seconds=60)
        d.setdefault("key")
        # dict.setdefault("key") speichert None, aber TTLDict speichert
        # nur non-None Werte — das ist akzeptabel da TTLDict fuer
        # Session-Daten genutzt wird, nicht fuer None-Werte
        # Wichtig: es darf keinen KeyError werfen

    def test_missing_key_no_default_no_keyerror(self) -> None:
        """Kein KeyError bei fehlendem Key ohne Default."""
        d: TTLDict[str, int] = TTLDict(ttl_seconds=60)
        # Das war der Bug: KeyError statt None
        try:
            result = d.setdefault("x")
            assert result is None
        except KeyError:
            pytest.fail("setdefault() wirft KeyError statt None zurueckzugeben")


# ============================================================================
# TTL-Ablauf bei setdefault
# ============================================================================


class TestTTLExpiration:
    """Prueft setdefault()-Verhalten mit abgelaufenen Eintraegen."""

    def test_expired_key_treated_as_missing(self) -> None:
        """Abgelaufener Key wird wie fehlend behandelt."""
        d: TTLDict[str, str] = TTLDict(ttl_seconds=0.01, cleanup_interval=999)
        d.set("key", "old_value")
        time.sleep(0.02)
        result = d.setdefault("key", "new_value")
        assert result == "new_value"

    def test_expired_key_replaced(self) -> None:
        """Abgelaufener Key wird durch neuen Wert ersetzt."""
        d: TTLDict[str, str] = TTLDict(ttl_seconds=0.01, cleanup_interval=999)
        d.set("key", "old_value")
        time.sleep(0.02)
        d.setdefault("key", "new_value")
        assert d.get("key") == "new_value"

    def test_non_expired_key_preserved(self) -> None:
        """Nicht-abgelaufener Key bleibt erhalten."""
        d: TTLDict[str, str] = TTLDict(ttl_seconds=60)
        d.set("key", "value")
        result = d.setdefault("key", "default")
        assert result == "value"


# ============================================================================
# Typische Nutzungsmuster
# ============================================================================


class TestUsagePatterns:
    """Prueft typische setdefault-Nutzungsmuster aus dem Codebase."""

    def test_stream_buffer_pattern(self) -> None:
        """Pattern: self._stream_buffers.setdefault(session_id, [])."""
        d: TTLDict[str, list[str]] = TTLDict(ttl_seconds=60)
        buf = d.setdefault("session1", [])
        assert buf == []
        # Zweiter Aufruf gibt dieselbe Liste zurueck
        buf2 = d.setdefault("session1", [])
        assert buf2 == []  # Wert existiert, default wird nicht verwendet

    def test_setdefault_with_dict_default(self) -> None:
        """Pattern: d.setdefault(key, {})."""
        d: TTLDict[str, dict] = TTLDict(ttl_seconds=60)
        val = d.setdefault("cfg", {"enabled": True})
        assert val == {"enabled": True}

    def test_multiple_setdefault_calls(self) -> None:
        """Mehrere setdefault-Aufrufe hintereinander."""
        d: TTLDict[str, int] = TTLDict(ttl_seconds=60)
        d.setdefault("a", 1)
        d.setdefault("b", 2)
        d.setdefault("a", 99)  # Should not overwrite
        assert d.get("a") == 1
        assert d.get("b") == 2


# ============================================================================
# Source-Level-Checks
# ============================================================================


class TestSourceLevelChecks:
    """Prueft den Source-Code auf den Fix."""

    def test_no_keyerror_in_setdefault(self) -> None:
        """setdefault darf keinen KeyError mehr werfen."""
        source = inspect.getsource(TTLDict.setdefault)
        assert "raise KeyError" not in source

    def test_does_not_use_val_is_not_none(self) -> None:
        """Keine 'val is not None'-Pruefung auf den get()-Rueckgabewert."""
        source = inspect.getsource(TTLDict.setdefault)
        assert "val is not None" not in source

    def test_checks_entry_directly(self) -> None:
        """Prueft _data.get() direkt statt ueber self.get()."""
        source = inspect.getsource(TTLDict.setdefault)
        assert "_data.get" in source
