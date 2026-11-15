"""Enhanced tests for WakeWordDetector -- additional coverage."""

from __future__ import annotations

import asyncio
import math
import struct
from unittest.mock import MagicMock, patch

import pytest

from cognithor.channels.wake_word import WakeWordDetector


def _make_silence(duration_ms: int = 50) -> bytes:
    n = int(16000 * duration_ms / 1000)
    return struct.pack(f"<{n}h", *([0] * n))


def _make_loud(duration_ms: int = 50) -> bytes:
    n = int(16000 * duration_ms / 1000)
    samples = [int(10000 * math.sin(2 * math.pi * 440 * i / 16000)) for i in range(n)]
    return struct.pack(f"<{n}h", *samples)


class TestWakeWordProperties:
    def test_defaults(self) -> None:
        d = WakeWordDetector()
        assert d.backend == "vosk"
        assert d.keywords == ["jarvis"]
        assert d.is_running is False

    def test_custom(self) -> None:
        d = WakeWordDetector(keywords=["hey", "ok"], backend="porcupine", sensitivity=0.7)
        assert d.keywords == ["hey", "ok"]
        assert d.backend == "porcupine"


class TestWakeWordLoad:
    @pytest.mark.asyncio
    async def test_load_vosk_not_installed(self) -> None:
        d = WakeWordDetector(backend="vosk")
        with patch.dict("sys.modules", {"vosk": None}):
            await d.load()
        assert d.backend == "energy"  # fallback

    @pytest.mark.asyncio
    async def test_load_porcupine_not_installed(self) -> None:
        d = WakeWordDetector(backend="porcupine")
        with patch.dict("sys.modules", {"pvporcupine": None}):
            await d.load()
        assert d.backend == "energy"

    @pytest.mark.asyncio
    async def test_load_energy_backend(self) -> None:
        d = WakeWordDetector(backend="energy")
        await d.load()
        assert d.backend == "energy"

    @pytest.mark.asyncio
    async def test_load_vosk_exception(self) -> None:
        d = WakeWordDetector(backend="vosk")
        mock_vosk = MagicMock()
        mock_vosk.Model.side_effect = RuntimeError("model error")

        with patch.dict("sys.modules", {"vosk": mock_vosk}):
            await d.load()
        assert d.backend == "energy"

    @pytest.mark.asyncio
    async def test_load_porcupine_exception(self) -> None:
        d = WakeWordDetector(backend="porcupine")
        mock_porcupine = MagicMock()
        mock_porcupine.create.side_effect = RuntimeError("model error")

        with patch.dict("sys.modules", {"pvporcupine": mock_porcupine}):
            await d.load()
        assert d.backend == "energy"


class TestWakeWordDetection:
    def test_energy_detect_silence(self) -> None:
        d = WakeWordDetector(backend="energy")
        assert d._detect_energy(_make_silence()) is False

    def test_energy_detect_loud(self) -> None:
        d = WakeWordDetector(backend="energy")
        assert d._detect_energy(_make_loud()) is True

    def test_energy_detect_too_short(self) -> None:
        d = WakeWordDetector(backend="energy")
        assert d._detect_energy(b"\x00") is False

    def test_detect_in_chunk_energy(self) -> None:
        d = WakeWordDetector(backend="energy")
        assert d.detect_in_chunk(_make_loud()) is True
        assert d.detect_in_chunk(_make_silence()) is False

    def test_detect_in_chunk_vosk_no_model(self) -> None:
        d = WakeWordDetector(backend="vosk")
        d._model = None
        assert d._detect_vosk(_make_silence()) is False

    def test_detect_in_chunk_porcupine_no_model(self) -> None:
        d = WakeWordDetector(backend="porcupine")
        d._model = None
        assert d._detect_porcupine(_make_silence()) is False

    def test_detect_vosk_with_model(self) -> None:
        d = WakeWordDetector(backend="vosk", keywords=["jarvis"])
        mock_model = MagicMock()
        mock_model.AcceptWaveform.return_value = True
        mock_model.Result.return_value = '{"text": "hey jarvis"}'
        d._model = mock_model

        assert d._detect_vosk(b"\x00\x00") is True

    def test_detect_vosk_partial(self) -> None:
        d = WakeWordDetector(backend="vosk", keywords=["jarvis"])
        mock_model = MagicMock()
        mock_model.AcceptWaveform.return_value = False
        mock_model.PartialResult.return_value = '{"partial": "jarvis"}'
        d._model = mock_model

        assert d._detect_vosk(b"\x00\x00") is True

    def test_detect_porcupine_found(self) -> None:
        d = WakeWordDetector(backend="porcupine")
        mock_model = MagicMock()
        mock_model.frame_length = 2
        mock_model.process.return_value = 0  # keyword index >= 0
        d._model = mock_model

        chunk = struct.pack("<4h", 1, 2, 3, 4)
        assert d._detect_porcupine(chunk) is True

    def test_detect_porcupine_not_found(self) -> None:
        d = WakeWordDetector(backend="porcupine")
        mock_model = MagicMock()
        mock_model.frame_length = 2
        mock_model.process.return_value = -1
        d._model = mock_model

        chunk = struct.pack("<4h", 1, 2, 3, 4)
        assert d._detect_porcupine(chunk) is False


class TestWakeWordListen:
    @pytest.mark.asyncio
    async def test_listen_detects_wake_word(self) -> None:
        d = WakeWordDetector(backend="energy")

        async def audio_gen():
            yield _make_loud(50)

        result = await d.listen(audio_gen())
        assert result is True

    @pytest.mark.asyncio
    async def test_listen_no_speech(self) -> None:
        d = WakeWordDetector(backend="energy")

        async def audio_gen():
            yield _make_silence(50)

        result = await d.listen(audio_gen())
        assert result is False

    @pytest.mark.asyncio
    async def test_listen_cancelled(self) -> None:
        d = WakeWordDetector(backend="energy")

        async def audio_gen():
            raise asyncio.CancelledError()
            yield  # unreachable, but needed for generator

        result = await d.listen(audio_gen())
        assert result is False

    def test_stop(self) -> None:
        d = WakeWordDetector()
        d._running = True
        d.stop()
        assert d.is_running is False
