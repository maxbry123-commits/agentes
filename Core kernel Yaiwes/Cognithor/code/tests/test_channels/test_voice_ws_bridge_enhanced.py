"""Enhanced tests for VoiceMessageHandler (voice_ws_bridge) -- additional coverage.

Covers: synthesize_response exception path, _convert_to_wav success path,
ext_map lookup, various audio types.
"""

from __future__ import annotations

import base64
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cognithor.channels.voice_ws_bridge import VoiceMessageHandler, VoiceWebSocketBridge

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    d = tmp_path / "voice_ws"
    d.mkdir()
    return d


@pytest.fixture
def handler(workspace: Path) -> VoiceMessageHandler:
    return VoiceMessageHandler(workspace_dir=workspace)


class TestVoiceMessageHandlerAlias:
    def test_backward_compat_alias(self) -> None:
        assert VoiceWebSocketBridge is VoiceMessageHandler


class TestSynthesizeResponseException:
    @pytest.mark.asyncio
    async def test_synthesis_exception(self, handler: VoiceMessageHandler) -> None:
        """Exception during synthesis returns None."""
        mock_media = MagicMock()
        mock_media.text_to_speech = AsyncMock(side_effect=RuntimeError("TTS crash"))
        handler._media = mock_media

        result = await handler.synthesize_response("Hello world")
        assert result is None


class TestConvertToWavSuccess:
    @pytest.mark.asyncio
    async def test_ffmpeg_success(self, handler: VoiceMessageHandler, workspace: Path) -> None:
        """Successful ffmpeg conversion returns the wav path."""
        input_file = workspace / "test.webm"
        input_file.write_bytes(b"\x00" * 100)

        wav_path = input_file.with_suffix(".wav")
        # Create the wav file so it "exists" after conversion
        wav_path.write_bytes(b"RIFF" + b"\x00" * 40)

        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(b"", b""))

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            result = await handler._convert_to_wav(input_file)

        assert result == wav_path


class TestTranscribeVoiceMessageExtMap:
    @pytest.mark.asyncio
    async def test_ogg_mime_type(self, handler: VoiceMessageHandler) -> None:
        """audio/ogg uses .ogg extension."""
        from cognithor.mcp.media import MediaResult

        audio_b64 = base64.b64encode(b"\x00" * 50).decode()
        mock_media = MagicMock()
        mock_media.transcribe_audio = AsyncMock(
            return_value=MediaResult(success=True, text="OGG result")
        )
        handler._media = mock_media

        with patch("asyncio.create_subprocess_exec", side_effect=FileNotFoundError):
            result = await handler.transcribe_voice_message(audio_b64, audio_type="audio/ogg")

        assert result == "OGG result"

    @pytest.mark.asyncio
    async def test_mp3_mime_type(self, handler: VoiceMessageHandler) -> None:
        """audio/mp3 uses .mp3 extension."""
        from cognithor.mcp.media import MediaResult

        audio_b64 = base64.b64encode(b"\x00" * 50).decode()
        mock_media = MagicMock()
        mock_media.transcribe_audio = AsyncMock(
            return_value=MediaResult(success=True, text="MP3 result")
        )
        handler._media = mock_media

        with patch("asyncio.create_subprocess_exec", side_effect=FileNotFoundError):
            result = await handler.transcribe_voice_message(audio_b64, audio_type="audio/mp3")

        assert result == "MP3 result"

    @pytest.mark.asyncio
    async def test_mpeg_mime_type(self, handler: VoiceMessageHandler) -> None:
        """audio/mpeg uses .mp3 extension."""
        from cognithor.mcp.media import MediaResult

        audio_b64 = base64.b64encode(b"\x00" * 50).decode()
        mock_media = MagicMock()
        mock_media.transcribe_audio = AsyncMock(
            return_value=MediaResult(success=True, text="MPEG result")
        )
        handler._media = mock_media

        with patch("asyncio.create_subprocess_exec", side_effect=FileNotFoundError):
            result = await handler.transcribe_voice_message(audio_b64, audio_type="audio/mpeg")

        assert result == "MPEG result"

    @pytest.mark.asyncio
    async def test_mp4_mime_type(self, handler: VoiceMessageHandler) -> None:
        """audio/mp4 uses .m4a extension."""
        from cognithor.mcp.media import MediaResult

        audio_b64 = base64.b64encode(b"\x00" * 50).decode()
        mock_media = MagicMock()
        mock_media.transcribe_audio = AsyncMock(
            return_value=MediaResult(success=True, text="M4A result")
        )
        handler._media = mock_media

        with patch("asyncio.create_subprocess_exec", side_effect=FileNotFoundError):
            result = await handler.transcribe_voice_message(audio_b64, audio_type="audio/mp4")

        assert result == "M4A result"

    @pytest.mark.asyncio
    async def test_wav_no_conversion_needed(self, handler: VoiceMessageHandler) -> None:
        """audio/wav does not need conversion."""
        from cognithor.mcp.media import MediaResult

        audio_b64 = base64.b64encode(b"RIFF" + b"\x00" * 50).decode()
        mock_media = MagicMock()
        mock_media.transcribe_audio = AsyncMock(
            return_value=MediaResult(success=True, text="WAV result")
        )
        handler._media = mock_media

        # No ffmpeg mock needed since wav doesn't trigger conversion
        result = await handler.transcribe_voice_message(audio_b64, audio_type="audio/wav")

        assert result == "WAV result"

    @pytest.mark.asyncio
    async def test_unknown_mime_type_defaults_webm(self, handler: VoiceMessageHandler) -> None:
        """Unknown MIME type defaults to .webm extension."""
        from cognithor.mcp.media import MediaResult

        audio_b64 = base64.b64encode(b"\x00" * 50).decode()
        mock_media = MagicMock()
        mock_media.transcribe_audio = AsyncMock(
            return_value=MediaResult(success=True, text="Unknown type")
        )
        handler._media = mock_media

        with patch("asyncio.create_subprocess_exec", side_effect=FileNotFoundError):
            result = await handler.transcribe_voice_message(audio_b64, audio_type="audio/unknown")

        assert result == "Unknown type"


class TestHandleWSVoiceMessageEdgeCases:
    @pytest.mark.asyncio
    async def test_custom_language(self, handler: VoiceMessageHandler) -> None:
        """Custom language parameter is passed through."""
        from cognithor.mcp.media import MediaResult

        audio_b64 = base64.b64encode(b"\x00" * 50).decode()
        mock_media = MagicMock()
        mock_media.transcribe_audio = AsyncMock(
            return_value=MediaResult(success=True, text="English result")
        )
        handler._media = mock_media

        with patch("asyncio.create_subprocess_exec", side_effect=FileNotFoundError):
            result = await handler.handle_ws_voice_message(
                {
                    "type": "voice_message",
                    "audio_base64": audio_b64,
                    "audio_type": "audio/webm",
                    "language": "en",
                }
            )

        assert result["type"] == "voice_transcription"
        assert result["text"] == "English result"
        # Verify language was passed to transcribe_audio
        call_kwargs = mock_media.transcribe_audio.call_args[1]
        assert call_kwargs["language"] == "en"
