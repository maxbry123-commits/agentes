"""Tests fuer F-023: Audio-Accumulator ohne Max-Size.

Prueft dass:
  - AudioAccumulator.MAX_BYTES existiert (100 MB default)
  - add_chunk() bei Ueberschreitung ValueError wirft
  - Normale Chunks weiterhin akzeptiert werden
  - _total_bytes korrekt gezaehlt wird
  - Genau am Limit wird noch akzeptiert
  - Knapp ueber dem Limit wird abgelehnt
  - ValueError-Message die Groesse enthaelt
  - clear() den Zaehler zuruecksetzt (danach wieder Chunks moeglich)
  - _handle_audio_chunk sendet voice_error bei Ueberschreitung
  - Source-Code die Fixes enthaelt
"""

from __future__ import annotations

import base64
import inspect

import pytest

from cognithor.channels.voice_bridge import AudioAccumulator, VoiceWebSocketBridge

# ============================================================================
# AudioAccumulator Size-Limit Tests
# ============================================================================


class TestMaxBytesField:
    """Prueft das MAX_BYTES Feld."""

    def test_default_100mb(self) -> None:
        acc = AudioAccumulator()
        assert acc.MAX_BYTES == 104_857_600

    def test_custom_limit(self) -> None:
        acc = AudioAccumulator(MAX_BYTES=1024)
        assert acc.MAX_BYTES == 1024


class TestAddChunkSizeLimit:
    """Prueft dass add_chunk() bei Ueberschreitung ablehnt."""

    def test_small_chunk_accepted(self) -> None:
        acc = AudioAccumulator()
        data = base64.b64encode(b"A" * 1000).decode()
        acc.add_chunk(data)
        assert acc._total_bytes == 1000

    def test_multiple_chunks_accumulate(self) -> None:
        acc = AudioAccumulator(MAX_BYTES=5000)
        data = base64.b64encode(b"A" * 1000).decode()
        for _ in range(5):
            acc.add_chunk(data)
        assert acc._total_bytes == 5000

    def test_exceeding_limit_raises(self) -> None:
        acc = AudioAccumulator(MAX_BYTES=1000)
        data = base64.b64encode(b"A" * 600).decode()
        acc.add_chunk(data)  # 600 bytes

        over_data = base64.b64encode(b"B" * 500).decode()
        with pytest.raises(ValueError, match="Audio-Limit"):
            acc.add_chunk(over_data)  # 600 + 500 = 1100 > 1000

    def test_exactly_at_limit_accepted(self) -> None:
        acc = AudioAccumulator(MAX_BYTES=1000)
        data = base64.b64encode(b"A" * 1000).decode()
        acc.add_chunk(data)  # Genau 1000 = MAX_BYTES
        assert acc._total_bytes == 1000

    def test_one_byte_over_limit_rejected(self) -> None:
        acc = AudioAccumulator(MAX_BYTES=1000)
        data = base64.b64encode(b"A" * 1000).decode()
        acc.add_chunk(data)

        tiny = base64.b64encode(b"X").decode()
        with pytest.raises(ValueError):
            acc.add_chunk(tiny)  # 1001 > 1000

    def test_rejected_chunk_not_stored(self) -> None:
        """Abgelehnter Chunk darf nicht in chunks/total_bytes landen."""
        acc = AudioAccumulator(MAX_BYTES=500)
        data = base64.b64encode(b"A" * 400).decode()
        acc.add_chunk(data)

        over = base64.b64encode(b"B" * 200).decode()
        with pytest.raises(ValueError):
            acc.add_chunk(over)

        assert acc._total_bytes == 400
        assert len(acc.chunks) == 1

    def test_error_message_contains_sizes(self) -> None:
        """ValueError-Message zeigt aktuelle und max Groesse."""
        acc = AudioAccumulator(MAX_BYTES=1_048_576)  # 1 MB
        data = base64.b64encode(b"A" * 1_048_576).decode()
        acc.add_chunk(data)

        over = base64.b64encode(b"B" * 100_000).decode()
        with pytest.raises(ValueError, match="max 1 MB"):
            acc.add_chunk(over)

    def test_clear_resets_and_allows_new_chunks(self) -> None:
        """Nach clear() koennen wieder Chunks hinzugefuegt werden."""
        acc = AudioAccumulator(MAX_BYTES=500)
        data = base64.b64encode(b"A" * 500).decode()
        acc.add_chunk(data)

        acc.clear()
        assert acc._total_bytes == 0

        # Jetzt wieder moeglich
        acc.add_chunk(data)
        assert acc._total_bytes == 500


class TestNormalOperation:
    """Prueft dass normaler Betrieb nicht beeintraechtigt wird."""

    def test_empty_accumulator(self) -> None:
        acc = AudioAccumulator()
        assert acc.is_empty
        assert acc._total_bytes == 0

    def test_get_blob_still_works(self) -> None:
        acc = AudioAccumulator()
        data1 = base64.b64encode(b"Hello").decode()
        data2 = base64.b64encode(b"World").decode()
        acc.add_chunk(data1)
        acc.add_chunk(data2)
        blob = acc.get_blob()
        assert blob == b"HelloWorld"

    def test_duration_estimate_still_works(self) -> None:
        acc = AudioAccumulator()
        data = base64.b64encode(b"A" * 12000).decode()
        acc.add_chunk(data)
        assert acc.duration_estimate_seconds == pytest.approx(1.0, abs=0.01)


# ============================================================================
# VoiceWebSocketBridge Error Handling
# ============================================================================


class TestBridgeErrorHandling:
    """Prueft dass _handle_audio_chunk den ValueError abfaengt."""

    @pytest.mark.asyncio
    async def test_chunk_error_sends_voice_error(self) -> None:
        """Bei Ueberschreitung wird voice_error an Client gesendet."""
        bridge = VoiceWebSocketBridge.__new__(VoiceWebSocketBridge)
        bridge._active_sessions = {}

        acc = AudioAccumulator(MAX_BYTES=100)
        data = base64.b64encode(b"A" * 50).decode()
        acc.add_chunk(data)
        bridge._active_sessions["s1"] = acc

        sent_messages: list[dict] = []

        async def mock_send(msg: dict) -> None:
            sent_messages.append(msg)

        over_data = base64.b64encode(b"B" * 200).decode()
        await bridge._handle_audio_chunk("s1", {"data": over_data}, mock_send)

        assert len(sent_messages) == 1
        assert sent_messages[0]["type"] == "voice_error"
        assert "Audio-Limit" in sent_messages[0]["error"]

    @pytest.mark.asyncio
    async def test_chunk_error_without_send_fn(self) -> None:
        """Ohne send_fn crasht es nicht."""
        bridge = VoiceWebSocketBridge.__new__(VoiceWebSocketBridge)
        bridge._active_sessions = {}

        acc = AudioAccumulator(MAX_BYTES=100)
        bridge._active_sessions["s1"] = acc

        over_data = base64.b64encode(b"B" * 200).decode()
        # Kein Crash ohne send_fn
        await bridge._handle_audio_chunk("s1", {"data": over_data})

    @pytest.mark.asyncio
    async def test_normal_chunk_no_error(self) -> None:
        """Normaler Chunk sendet keinen Fehler."""
        bridge = VoiceWebSocketBridge.__new__(VoiceWebSocketBridge)
        bridge._active_sessions = {}

        acc = AudioAccumulator()
        bridge._active_sessions["s1"] = acc

        sent_messages: list[dict] = []

        async def mock_send(msg: dict) -> None:
            sent_messages.append(msg)

        data = base64.b64encode(b"A" * 100).decode()
        await bridge._handle_audio_chunk("s1", {"data": data}, mock_send)

        assert len(sent_messages) == 0
        assert acc._total_bytes == 100


# ============================================================================
# Source-Level-Checks
# ============================================================================


class TestSourceLevelChecks:
    """Prueft den Source-Code auf die Fixes."""

    def test_accumulator_has_max_bytes(self) -> None:
        source = inspect.getsource(AudioAccumulator)
        assert "MAX_BYTES" in source

    def test_add_chunk_checks_size(self) -> None:
        source = inspect.getsource(AudioAccumulator.add_chunk)
        assert "_total_bytes" in source
        assert "MAX_BYTES" in source

    def test_add_chunk_raises_valueerror(self) -> None:
        source = inspect.getsource(AudioAccumulator.add_chunk)
        assert "ValueError" in source

    def test_handle_chunk_catches_error(self) -> None:
        source = inspect.getsource(VoiceWebSocketBridge._handle_audio_chunk)
        assert "ValueError" in source

    def test_handle_chunk_sends_voice_error(self) -> None:
        source = inspect.getsource(VoiceWebSocketBridge._handle_audio_chunk)
        assert "voice_error" in source
