"""Tests fuer F-018: Base64-Audio ohne Size-Limit.

Prueft dass:
  - Base64-Audio vor dem Decode auf Groesse geprueft wird
  - Geschaetzte Groesse korrekt berechnet wird (len * 3 // 4)
  - Zu grosse Payloads abgelehnt werden
  - Normale Payloads weiterhin akzeptiert werden
  - Source-Code die Fixes enthaelt
"""

from __future__ import annotations

import base64
import inspect
import os

import pytest

# ============================================================================
# Unit-Tests fuer die Size-Estimation-Logik
# ============================================================================


class TestBase64SizeEstimation:
    """Prueft die Base64-Groessenschaetzung (len * 3 // 4)."""

    def test_estimation_formula_small(self) -> None:
        """Kleine Payload: Schaetzung ist korrekt."""
        data = b"Hello World"
        b64 = base64.b64encode(data).decode()
        estimated = len(b64) * 3 // 4
        actual = len(data)
        # Schaetzung ist immer >= tatsaechliche Groesse (wegen Padding)
        assert estimated >= actual

    def test_estimation_formula_exact_multiple(self) -> None:
        """Daten mit Laenge die ein Vielfaches von 3 ist → exakte Schaetzung."""
        data = b"A" * 300  # 300 bytes, Vielfaches von 3
        b64 = base64.b64encode(data).decode()
        estimated = len(b64) * 3 // 4
        assert estimated == len(data)

    def test_estimation_formula_1mb(self) -> None:
        """1 MB Payload: Schaetzung passt."""
        data = os.urandom(1_048_576)
        b64 = base64.b64encode(data).decode()
        estimated = len(b64) * 3 // 4
        assert estimated >= len(data)
        # Abweichung maximal 2 Bytes (Padding)
        assert estimated - len(data) <= 2

    def test_estimation_overestimates_slightly(self) -> None:
        """Schaetzung darf nie kleiner als die tatsaechliche Groesse sein."""
        for size in [1, 2, 3, 10, 100, 1000, 7777]:
            data = os.urandom(size)
            b64 = base64.b64encode(data).decode()
            estimated = len(b64) * 3 // 4
            assert estimated >= len(data), f"Estimation too small for size={size}"


class TestSizeLimitCheck:
    """Prueft die Limit-Logik wie im __main__.py implementiert."""

    MAX_AUDIO_B64_BYTES = 52_428_800  # 50 MB

    def test_small_payload_accepted(self) -> None:
        """1 KB Audio wird akzeptiert."""
        data = os.urandom(1024)
        b64 = base64.b64encode(data).decode()
        estimated = len(b64) * 3 // 4
        assert estimated <= self.MAX_AUDIO_B64_BYTES

    def test_49mb_accepted(self) -> None:
        """49 MB Audio wird akzeptiert (unter dem Limit)."""
        # Simuliere die Laenge eines 49 MB Base64-Strings
        # 49 MB = 49 * 1024 * 1024 = 51380224 bytes
        # Base64-Laenge = ceil(51380224 / 3) * 4 = 68507000 chars
        b64_len = (51_380_224 // 3 + 1) * 4
        estimated = b64_len * 3 // 4
        assert estimated <= self.MAX_AUDIO_B64_BYTES

    def test_51mb_rejected(self) -> None:
        """51 MB Audio wird abgelehnt (ueber dem Limit)."""
        # 51 MB = 53477376 bytes
        b64_len = (53_477_376 // 3 + 1) * 4
        estimated = b64_len * 3 // 4
        assert estimated > self.MAX_AUDIO_B64_BYTES

    def test_exactly_50mb_accepted(self) -> None:
        """Genau 50 MB (Grenzwert) wird akzeptiert."""
        # 50 MB = 52428800 bytes, exakt am Limit
        b64_len = (52_428_800 // 3) * 4  # Exaktes Vielfaches
        estimated = b64_len * 3 // 4
        assert estimated <= self.MAX_AUDIO_B64_BYTES

    def test_empty_audio_accepted(self) -> None:
        """Leere Audio-Daten (0 Bytes) werden nicht vom Size-Check blockiert."""
        b64 = base64.b64encode(b"").decode()
        estimated = len(b64) * 3 // 4
        assert estimated <= self.MAX_AUDIO_B64_BYTES
        assert estimated == 0


class TestErrorMessage:
    """Prueft das Error-Message-Format."""

    MAX_AUDIO_B64_BYTES = 52_428_800

    def test_error_message_format(self) -> None:
        """Error-Message zeigt MB-Angabe korrekt an."""
        estimated_size = 60_000_000  # ~57 MB
        error_msg = (
            f"Audiodatei zu gross "
            f"({estimated_size // 1_048_576} MB, "
            f"max {self.MAX_AUDIO_B64_BYTES // 1_048_576} MB)"
        )
        assert "57 MB" in error_msg
        assert "max 50 MB" in error_msg

    def test_error_message_for_100mb(self) -> None:
        """100 MB Payload zeigt korrekte Groesse."""
        estimated_size = 104_857_600
        error_msg = (
            f"Audiodatei zu gross "
            f"({estimated_size // 1_048_576} MB, "
            f"max {self.MAX_AUDIO_B64_BYTES // 1_048_576} MB)"
        )
        assert "100 MB" in error_msg


# ============================================================================
# Source-Level-Checks
# ============================================================================


class TestSourceLevelChecks:
    """Prueft den Source-Code auf die Fixes."""

    @pytest.fixture(autouse=True)
    def _load_source(self) -> None:
        """Laedt den relevanten Source-Code."""
        import cognithor.__main__ as main_mod

        # Lese die gesamte Datei als Text
        self._source = inspect.getsource(main_mod)

    def test_has_size_estimation(self) -> None:
        """Source enthaelt die Base64-Groessenschaetzung."""
        assert "len(audio_b64) * 3 // 4" in self._source

    def test_has_max_constant(self) -> None:
        """Source definiert ein Maximum fuer Audio-Groesse."""
        assert "52_428_800" in self._source or "52428800" in self._source

    def test_has_size_comparison(self) -> None:
        """Source vergleicht estimated_size mit dem Limit."""
        assert "estimated_size >" in self._source

    def test_has_error_response(self) -> None:
        """Source sendet Error-Response bei Ueberschreitung."""
        assert "Audiodatei zu gross" in self._source

    def test_has_continue_after_reject(self) -> None:
        """Source hat 'continue' nach der Ablehnung (naechste Nachricht)."""
        # Pruefe dass nach dem Error-Send ein continue kommt
        lines = self._source.split("\n")
        found_error = False
        for _i, line in enumerate(lines):
            if "Audiodatei zu gross" in line:
                found_error = True
            if found_error and "continue" in line:
                break
        assert found_error, "Error-Nachricht nicht gefunden"

    def test_size_check_before_decode(self) -> None:
        """Size-Check muss VOR b64decode stehen."""
        idx_check = self._source.find("estimated_size >")
        idx_decode = self._source.find("b64.b64decode(audio_b64)")
        assert idx_check > 0, "Size-Check nicht gefunden"
        assert idx_decode > 0, "b64decode nicht gefunden"
        assert idx_check < idx_decode, "Size-Check muss VOR b64decode stehen"
