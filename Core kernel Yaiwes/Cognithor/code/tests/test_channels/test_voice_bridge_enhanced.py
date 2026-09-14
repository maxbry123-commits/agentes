"""Enhanced tests for VoiceWebSocketBridge -- additional coverage.

Covers: initialize() paths (whisper load, cuda/cpu, import error, exception),
_handle_audio_stop empty transcription, _transcribe (ffmpeg, whisper exec).
"""

from __future__ import annotations

import base64
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cognithor.channels.voice_bridge import AudioAccumulator, VoiceWebSocketBridge

if TYPE_CHECKING:
    from pathlib import Path


class TestInitialize:
    @pytest.mark.asyncio
    async def test_initialize_whisper_import_error(self, tmp_path: Path) -> None:
        bridge = VoiceWebSocketBridge(workspace_dir=tmp_path)
        with patch.dict("sys.modules", {"faster_whisper": None}):
            result = await bridge.initialize()
        assert result is False
        assert bridge._stt_engine is None

    @pytest.mark.asyncio
    async def test_initialize_with_cuda(self, tmp_path: Path) -> None:
        bridge = VoiceWebSocketBridge(workspace_dir=tmp_path)
        mock_model = MagicMock()

        mock_whisper_mod = MagicMock()
        mock_whisper_mod.WhisperModel = MagicMock(return_value=mock_model)

        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = True

        with patch.dict("sys.modules", {"faster_whisper": mock_whisper_mod, "torch": mock_torch}):
            result = await bridge.initialize()

        assert result is True
        assert bridge._stt_engine is mock_model
        # Verify WhisperModel was called with cuda and float16
        call_kwargs = mock_whisper_mod.WhisperModel.call_args
        assert call_kwargs[1]["device"] == "cuda"
        assert call_kwargs[1]["compute_type"] == "float16"

    @pytest.mark.asyncio
    async def test_initialize_cpu_no_torch(self, tmp_path: Path) -> None:
        bridge = VoiceWebSocketBridge(workspace_dir=tmp_path)
        mock_model = MagicMock()

        mock_whisper_mod = MagicMock()
        mock_whisper_mod.WhisperModel = MagicMock(return_value=mock_model)

        with patch.dict("sys.modules", {"faster_whisper": mock_whisper_mod, "torch": None}):
            result = await bridge.initialize()

        assert result is True
        assert bridge._stt_engine is mock_model
        call_kwargs = mock_whisper_mod.WhisperModel.call_args
        assert call_kwargs[1]["device"] == "cpu"
        assert call_kwargs[1]["compute_type"] == "int8"

    @pytest.mark.asyncio
    async def test_initialize_whisper_exception(self, tmp_path: Path) -> None:
        bridge = VoiceWebSocketBridge(workspace_dir=tmp_path)

        mock_whisper_mod = MagicMock()
        mock_whisper_mod.WhisperModel = MagicMock(side_effect=RuntimeError("model load error"))

        with patch.dict("sys.modules", {"faster_whisper": mock_whisper_mod, "torch": None}):
            result = await bridge.initialize()

        assert result is False
        assert bridge._stt_engine is None


class TestHandleAudioStopEmptyTranscription:
    @pytest.mark.asyncio
    async def test_empty_transcription_result(self, tmp_path: Path) -> None:
        """When transcription returns empty text, send empty transcription + ready status."""
        bridge = VoiceWebSocketBridge(workspace_dir=tmp_path)
        send_fn = AsyncMock()

        async def mock_transcribe(acc):
            return ""

        bridge._transcribe = mock_transcribe  # type: ignore[assignment]
        bridge._stt_engine = MagicMock()

        # Start + chunk + stop
        await bridge.handle_ws_message(
            "sess1",
            {"type": "audio_start", "format": "webm"},
            send_fn,
        )
        await bridge.handle_ws_message(
            "sess1",
            {"type": "audio_chunk", "data": base64.b64encode(b"\x00" * 5000).decode()},
            send_fn,
        )
        send_fn.reset_mock()

        result = await bridge.handle_ws_message(
            "sess1",
            {"type": "audio_stop"},
            send_fn,
        )

        assert result is None
        calls = [c[0][0] for c in send_fn.call_args_list]
        # Should have processing status, empty transcription, and ready status
        types = [c["type"] for c in calls]
        assert "voice_status" in types
        assert "transcription" in types
        transcription = next(c for c in calls if c["type"] == "transcription")
        assert transcription["text"] == ""
        assert transcription["final"] is True

    @pytest.mark.asyncio
    async def test_whitespace_transcription_result(self, tmp_path: Path) -> None:
        bridge = VoiceWebSocketBridge(workspace_dir=tmp_path)
        send_fn = AsyncMock()

        async def mock_transcribe(acc):
            return "   "

        bridge._transcribe = mock_transcribe  # type: ignore[assignment]
        bridge._stt_engine = MagicMock()

        await bridge.handle_ws_message(
            "sess1",
            {"type": "audio_start", "format": "webm"},
            send_fn,
        )
        await bridge.handle_ws_message(
            "sess1",
            {"type": "audio_chunk", "data": base64.b64encode(b"\x00" * 5000).decode()},
            send_fn,
        )
        send_fn.reset_mock()

        result = await bridge.handle_ws_message(
            "sess1",
            {"type": "audio_stop"},
            send_fn,
        )
        assert result is None


class TestTranscribe:
    @pytest.mark.asyncio
    async def test_transcribe_no_engine(self, tmp_path: Path) -> None:
        bridge = VoiceWebSocketBridge(workspace_dir=tmp_path)
        bridge._stt_engine = None
        acc = AudioAccumulator()
        acc.add_chunk(base64.b64encode(b"\x00" * 100).decode())

        with pytest.raises(RuntimeError, match="Whisper nicht geladen"):
            await bridge._transcribe(acc)

    @pytest.mark.asyncio
    async def test_transcribe_wav_no_ffmpeg(self, tmp_path: Path) -> None:
        """WAV format doesn't need ffmpeg conversion."""
        bridge = VoiceWebSocketBridge(workspace_dir=tmp_path)
        mock_engine = MagicMock()
        mock_segment = MagicMock()
        mock_segment.text = "Test transcription"
        mock_engine.transcribe.return_value = ([mock_segment], MagicMock())
        bridge._stt_engine = mock_engine

        acc = AudioAccumulator(format="wav")
        acc.add_chunk(base64.b64encode(b"\x00" * 100).decode())

        result = await bridge._transcribe(acc)
        assert result == "Test transcription"

    @pytest.mark.asyncio
    async def test_transcribe_webm_with_ffmpeg(self, tmp_path: Path) -> None:
        """WebM format runs ffmpeg conversion."""
        bridge = VoiceWebSocketBridge(workspace_dir=tmp_path)
        mock_engine = MagicMock()
        mock_segment = MagicMock()
        mock_segment.text = "Hello world"
        mock_engine.transcribe.return_value = ([mock_segment], MagicMock())
        bridge._stt_engine = mock_engine

        acc = AudioAccumulator(format="webm")
        acc.add_chunk(base64.b64encode(b"\x00" * 100).decode())

        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(b"", b""))

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            result = await bridge._transcribe(acc)

        assert result == "Hello world"

    @pytest.mark.asyncio
    async def test_transcribe_webm_ffmpeg_not_found(self, tmp_path: Path) -> None:
        """WebM format when ffmpeg is not installed raises RuntimeError."""
        bridge = VoiceWebSocketBridge(workspace_dir=tmp_path)
        mock_engine = MagicMock()
        bridge._stt_engine = mock_engine

        acc = AudioAccumulator(format="webm")
        acc.add_chunk(base64.b64encode(b"\x00" * 100).decode())

        with patch("asyncio.create_subprocess_exec", side_effect=FileNotFoundError):
            with pytest.raises(RuntimeError, match="ffmpeg"):
                await bridge._transcribe(acc)

    @pytest.mark.asyncio
    async def test_transcribe_webm_ffmpeg_error(self, tmp_path: Path) -> None:
        """WebM format when ffmpeg returns error raises RuntimeError."""
        bridge = VoiceWebSocketBridge(workspace_dir=tmp_path)
        mock_engine = MagicMock()
        bridge._stt_engine = mock_engine

        acc = AudioAccumulator(format="webm")
        acc.add_chunk(base64.b64encode(b"\x00" * 100).decode())

        mock_proc = AsyncMock()
        mock_proc.returncode = 1
        mock_proc.communicate = AsyncMock(return_value=(b"", b"Error: invalid data"))

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            with pytest.raises(RuntimeError, match="ffmpeg"):
                await bridge._transcribe(acc)

    @pytest.mark.asyncio
    async def test_transcribe_ogg_format(self, tmp_path: Path) -> None:
        """OGG format also triggers ffmpeg conversion."""
        bridge = VoiceWebSocketBridge(workspace_dir=tmp_path)
        mock_engine = MagicMock()
        mock_segment = MagicMock()
        mock_segment.text = "OGG result"
        mock_engine.transcribe.return_value = ([mock_segment], MagicMock())
        bridge._stt_engine = mock_engine

        acc = AudioAccumulator(format="ogg")
        acc.add_chunk(base64.b64encode(b"\x00" * 100).decode())

        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(b"", b""))

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            result = await bridge._transcribe(acc)

        assert result == "OGG result"

    @pytest.mark.asyncio
    async def test_transcribe_multiple_segments(self, tmp_path: Path) -> None:
        """Multiple transcription segments are joined with spaces."""
        bridge = VoiceWebSocketBridge(workspace_dir=tmp_path)
        seg1 = MagicMock()
        seg1.text = "Hello"
        seg2 = MagicMock()
        seg2.text = "World"
        mock_engine = MagicMock()
        mock_engine.transcribe.return_value = ([seg1, seg2], MagicMock())
        bridge._stt_engine = mock_engine

        acc = AudioAccumulator(format="wav")
        acc.add_chunk(base64.b64encode(b"\x00" * 100).decode())

        result = await bridge._transcribe(acc)
        assert result == "Hello World"


class TestAudioAccumulatorExtra:
    def test_duration_estimate_mp3(self) -> None:
        """Non-webm, non-pcm format uses PCM calculation."""
        acc = AudioAccumulator(format="mp3", sample_rate=16000)
        acc.add_chunk(base64.b64encode(b"\x00" * 32000).decode())
        assert 0.9 < acc.duration_estimate_seconds < 1.1

    def test_get_blob_ordering(self) -> None:
        """Chunks are concatenated in order."""
        acc = AudioAccumulator()
        acc.add_chunk(base64.b64encode(b"AAA").decode())
        acc.add_chunk(base64.b64encode(b"BBB").decode())
        assert acc.get_blob() == b"AAABBB"
