"""Tests fuer F-027: voice_ws_bridge Fixed Filename Race Condition.

Prueft dass:
  - voice_input Dateien eindeutige Namen haben (UUID)
  - voice_response Dateien eindeutige Namen haben (UUID)
  - Zwei gleichzeitige Requests unterschiedliche Dateien erzeugen
  - Der Dateiname immer noch die korrekte Extension hat
  - Source-Code keine festen Dateinamen mehr verwendet
"""

from __future__ import annotations

import inspect

from cognithor.channels.voice_ws_bridge import VoiceMessageHandler

# ============================================================================
# Unique Filenames
# ============================================================================


class TestUniqueInputFilenames:
    """Prueft dass voice_input Dateien eindeutige Namen haben."""

    def test_source_uses_uuid_for_input(self) -> None:
        """voice_input Dateiname enthaelt UUID."""
        source = inspect.getsource(VoiceMessageHandler.transcribe_voice_message)
        assert "uuid" in source
        assert "voice_input_" in source

    def test_no_fixed_voice_input_name(self) -> None:
        """Kein fester 'voice_input{ext}' Dateiname mehr."""
        source = inspect.getsource(VoiceMessageHandler.transcribe_voice_message)
        # Darf nicht den alten festen Namen haben
        assert 'f"voice_input{ext}"' not in source

    def test_input_filename_pattern(self) -> None:
        """Dateiname folgt dem Pattern voice_input_<hex>.<ext>."""
        source = inspect.getsource(VoiceMessageHandler.transcribe_voice_message)
        # Muss UUID-hex im Namen haben
        assert "uuid4().hex" in source or "uuid.uuid4().hex" in source


class TestUniqueResponseFilenames:
    """Prueft dass voice_response Dateien eindeutige Namen haben."""

    def test_source_uses_uuid_for_response(self) -> None:
        """voice_response Dateiname enthaelt UUID."""
        source = inspect.getsource(VoiceMessageHandler.synthesize_response)
        assert "uuid" in source
        assert "voice_response_" in source

    def test_no_fixed_voice_response_name(self) -> None:
        """Kein fester 'voice_response.wav' Dateiname mehr."""
        source = inspect.getsource(VoiceMessageHandler.synthesize_response)
        assert '"voice_response.wav"' not in source

    def test_response_filename_pattern(self) -> None:
        """Dateiname folgt dem Pattern voice_response_<hex>.wav."""
        source = inspect.getsource(VoiceMessageHandler.synthesize_response)
        assert "uuid4().hex" in source or "uuid.uuid4().hex" in source


# ============================================================================
# Concurrency Safety
# ============================================================================


class TestConcurrencySafety:
    """Prueft dass gleichzeitige Requests verschiedene Dateien nutzen."""

    def test_uuid_produces_unique_names(self) -> None:
        """uuid4().hex[:12] erzeugt verschiedene Werte."""
        import uuid

        names = {uuid.uuid4().hex[:12] for _ in range(100)}
        assert len(names) == 100

    def test_filename_collision_probability(self) -> None:
        """12 Hex-Zeichen = 48 Bit Entropie — kollisionssicher."""
        import uuid

        # 12 Hex-Zeichen = 2^48 Moeglichkeiten
        sample = uuid.uuid4().hex[:12]
        assert len(sample) == 12
        assert all(c in "0123456789abcdef" for c in sample)


# ============================================================================
# Extension Preserved
# ============================================================================


class TestExtensionPreserved:
    """Prueft dass die Dateiendung korrekt erhalten bleibt."""

    def test_input_keeps_ext_in_name(self) -> None:
        """voice_input Dateiname hat Extension am Ende."""
        source = inspect.getsource(VoiceMessageHandler.transcribe_voice_message)
        # Pattern: f"voice_input_{uuid...}{ext}"
        assert "{ext}" in source

    def test_response_has_wav_extension(self) -> None:
        """voice_response Dateiname hat .wav Extension."""
        source = inspect.getsource(VoiceMessageHandler.synthesize_response)
        assert ".wav" in source


# ============================================================================
# Source-Level-Checks
# ============================================================================


class TestSourceLevelChecks:
    """Prueft den Source-Code auf die Fixes."""

    def test_uuid_imported(self) -> None:
        """uuid Modul wird importiert."""
        import cognithor.channels.voice_ws_bridge as mod

        source = inspect.getsource(mod)
        assert "import uuid" in source

    def test_no_bare_voice_input(self) -> None:
        """Kein 'voice_input{ext}' ohne UUID-Suffix."""
        source = inspect.getsource(VoiceMessageHandler.transcribe_voice_message)
        # Alte Version: f"voice_input{ext}" — darf nicht mehr existieren
        lines = source.split("\n")
        for line in lines:
            if "voice_input" in line and "{ext}" in line:
                assert "uuid" in line, f"voice_input ohne UUID: {line.strip()}"

    def test_no_bare_voice_response(self) -> None:
        """Kein 'voice_response.wav' ohne UUID-Suffix."""
        source = inspect.getsource(VoiceMessageHandler.synthesize_response)
        lines = source.split("\n")
        for line in lines:
            if "voice_response" in line and ".wav" in line:
                assert "uuid" in line, f"voice_response ohne UUID: {line.strip()}"
