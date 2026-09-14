"""Enhanced tests for ElevenLabsTTS -- additional coverage."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cognithor.channels.tts_elevenlabs import ElevenLabsConfig, ElevenLabsTTS


@pytest.fixture
def tts() -> ElevenLabsTTS:
    return ElevenLabsTTS(api_key="sk-test", voice_id="voice123", model="eleven_multilingual_v2")


class TestElevenLabsProperties:
    def test_api_key(self, tts: ElevenLabsTTS) -> None:
        assert tts.api_key == "sk-test"

    def test_voice_id(self, tts: ElevenLabsTTS) -> None:
        assert tts.voice_id == "voice123"

    def test_model(self, tts: ElevenLabsTTS) -> None:
        assert tts.model == "eleven_multilingual_v2"


class TestElevenLabsConfig:
    def test_defaults(self) -> None:
        c = ElevenLabsConfig()
        assert c.stability == 0.5
        assert c.similarity_boost == 0.75
        assert c.output_format == "mp3_44100_128"


class TestBuildUrl:
    def test_normal_url(self, tts: ElevenLabsTTS) -> None:
        url = tts._build_url(stream=False)
        assert "voice123" in url
        assert "/stream" not in url

    def test_stream_url(self, tts: ElevenLabsTTS) -> None:
        url = tts._build_url(stream=True)
        assert "/stream" in url


class TestBuildHeaders:
    def test_headers(self, tts: ElevenLabsTTS) -> None:
        h = tts._build_headers()
        assert h["xi-api-key"] == "sk-test"
        assert h["Content-Type"] == "application/json"


class TestBuildPayload:
    def test_payload(self, tts: ElevenLabsTTS) -> None:
        p = tts._build_payload("Hello World")
        assert p["text"] == "Hello World"
        assert p["model_id"] == "eleven_multilingual_v2"
        assert "voice_settings" in p


class TestSynthesize:
    @pytest.mark.asyncio
    async def test_synthesize_success(self, tts: ElevenLabsTTS) -> None:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = b"audio-data"

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_resp)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await tts.synthesize("Hello")
        assert result == b"audio-data"

    @pytest.mark.asyncio
    async def test_synthesize_api_error(self, tts: ElevenLabsTTS) -> None:
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.text = "Unauthorized"

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_resp)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await tts.synthesize("Hello")
        assert result == b""

    @pytest.mark.asyncio
    async def test_synthesize_request_error(self, tts: ElevenLabsTTS) -> None:
        import httpx

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(side_effect=httpx.RequestError("timeout"))

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await tts.synthesize("Hello")
        assert result == b""

    @pytest.mark.asyncio
    async def test_synthesize_http_status_error(self, tts: ElevenLabsTTS) -> None:
        import httpx

        mock_response = MagicMock()
        mock_response.status_code = 500

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(
            side_effect=httpx.HTTPStatusError("error", request=MagicMock(), response=mock_response)
        )

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await tts.synthesize("Hello")
        assert result == b""

    @pytest.mark.asyncio
    async def test_synthesize_unexpected_error(self, tts: ElevenLabsTTS) -> None:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(side_effect=RuntimeError("unexpected"))

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await tts.synthesize("Hello")
        assert result == b""


class TestStream:
    @pytest.mark.asyncio
    async def test_stream_success(self, tts: ElevenLabsTTS) -> None:
        mock_response = AsyncMock()
        mock_response.status_code = 200

        async def fake_iter(*args, **kwargs):
            yield b"chunk1"
            yield b"chunk2"

        mock_response.aiter_bytes = fake_iter

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.stream = MagicMock(
            return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=mock_response),
                __aexit__=AsyncMock(return_value=False),
            )
        )

        chunks = []
        with patch("httpx.AsyncClient", return_value=mock_client):
            async for chunk in tts.stream("Hello"):
                chunks.append(chunk)
        assert chunks == [b"chunk1", b"chunk2"]

    @pytest.mark.asyncio
    async def test_stream_api_error(self, tts: ElevenLabsTTS) -> None:
        mock_response = AsyncMock()
        mock_response.status_code = 500
        mock_response.aread = AsyncMock(return_value=b"error")

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.stream = MagicMock(
            return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=mock_response),
                __aexit__=AsyncMock(return_value=False),
            )
        )

        chunks = []
        with patch("httpx.AsyncClient", return_value=mock_client):
            async for chunk in tts.stream("Hello"):
                chunks.append(chunk)
        assert chunks == []

    @pytest.mark.asyncio
    async def test_stream_request_error(self, tts: ElevenLabsTTS) -> None:
        import httpx

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.stream = MagicMock(side_effect=httpx.RequestError("fail"))

        chunks = []
        with patch("httpx.AsyncClient", return_value=mock_client):
            async for chunk in tts.stream("Hello"):
                chunks.append(chunk)
        assert chunks == []
