from __future__ import annotations

import json as _json
from typing import TYPE_CHECKING

import pytest

from cognithor.core.vllm_backend import VLLMBackend, _attach_video_to_last_user

if TYPE_CHECKING:
    from pytest_httpx import HTTPXMock


BASE_URL = "http://localhost:8000/v1"


@pytest.fixture
def backend() -> VLLMBackend:
    return VLLMBackend(base_url=BASE_URL, timeout=5)


class TestAttachVideoHelper:
    def test_prepends_video_url_content_item_to_last_user(self):
        messages = [
            {"role": "system", "content": "you are helpful"},
            {"role": "user", "content": "What is in this?"},
        ]
        video = {"url": "http://x/a.mp4", "sampling": {"fps": 2.0}}
        new_messages, mm_kwargs = _attach_video_to_last_user(messages, video)

        # System message untouched
        assert new_messages[0] == messages[0]
        # Last user message converted to content-item list
        last = new_messages[-1]
        assert last["role"] == "user"
        assert isinstance(last["content"], list)
        assert last["content"][0] == {"type": "video_url", "video_url": {"url": "http://x/a.mp4"}}
        assert last["content"][1] == {"type": "text", "text": "What is in this?"}
        # mm kwargs shape
        assert mm_kwargs == {"mm_processor_kwargs": {"video": {"fps": 2.0}}}

    def test_num_frames_sampling(self):
        video = {"url": "http://x/a.mp4", "sampling": {"num_frames": 32}}
        _, mm_kwargs = _attach_video_to_last_user([{"role": "user", "content": "hi"}], video)
        assert mm_kwargs == {"mm_processor_kwargs": {"video": {"num_frames": 32}}}

    def test_empty_text_part_not_added(self):
        """If the user message content is already an empty string, don't
        inject a zero-length text part."""
        messages = [{"role": "user", "content": ""}]
        video = {"url": "http://x/a.mp4", "sampling": {"fps": 1.0}}
        new_messages, _ = _attach_video_to_last_user(messages, video)
        content_items = new_messages[-1]["content"]
        assert len(content_items) == 1  # only the video, no text
        assert content_items[0]["type"] == "video_url"

    def test_caller_messages_not_mutated(self):
        messages = [{"role": "user", "content": "orig"}]
        video = {"url": "http://x/a.mp4", "sampling": {"fps": 1.0}}
        _attach_video_to_last_user(messages, video)
        assert messages[0]["content"] == "orig"
        assert isinstance(messages[0]["content"], str)

    def test_preserves_text_when_last_user_already_has_list_content(self):
        """Regression: a prior image in the same turn makes content a list.
        The video helper must extract the text from that list, not drop it."""
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": "http://x/pic.png"}},
                    {"type": "text", "text": "Was ist auf dem Bild und im Video?"},
                ],
            }
        ]
        video = {"url": "http://x/a.mp4", "sampling": {"fps": 2.0}}
        new_messages, mm_kwargs = _attach_video_to_last_user(messages, video)

        last = new_messages[-1]
        assert last["role"] == "user"
        assert isinstance(last["content"], list)
        # The video must be present
        assert any(c.get("type") == "video_url" for c in last["content"])
        # The text must survive
        assert any(
            c.get("type") == "text" and c["text"] == "Was ist auf dem Bild und im Video?"
            for c in last["content"]
        )
        # The pre-existing image must survive
        assert any(
            c.get("type") == "image_url" and c["image_url"]["url"] == "http://x/pic.png"
            for c in last["content"]
        )

    def test_list_content_without_text_does_not_inject_empty_text(self):
        """If the existing list has no text item, the helper should not append
        a zero-length text content item."""
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": "http://x/pic.png"}},
                ],
            }
        ]
        video = {"url": "http://x/a.mp4", "sampling": {"fps": 1.0}}
        new_messages, _ = _attach_video_to_last_user(messages, video)

        last = new_messages[-1]
        texts = [c for c in last["content"] if c.get("type") == "text"]
        assert len(texts) == 0


class TestChatWithVideo:
    @pytest.mark.asyncio
    async def test_chat_with_video_sends_video_url_and_mm_kwargs(
        self, backend: VLLMBackend, httpx_mock: HTTPXMock
    ):
        httpx_mock.add_response(
            url=f"{BASE_URL}/chat/completions",
            status_code=200,
            json={
                "choices": [{"message": {"content": "A drone flying over a field."}}],
                "model": "mmangkad/Qwen3.6-27B-NVFP4",
                "usage": {"prompt_tokens": 100, "completion_tokens": 10, "total_tokens": 110},
            },
        )
        resp = await backend.chat(
            model="mmangkad/Qwen3.6-27B-NVFP4",
            messages=[{"role": "user", "content": "What's in this clip?"}],
            video={
                "url": "http://host.docker.internal:4711/media/abc.mp4",
                "sampling": {"fps": 2.0},
            },
        )
        assert resp.content == "A drone flying over a field."

        request = httpx_mock.get_requests()[0]
        body = _json.loads(request.content)

        last_msg = body["messages"][-1]
        assert last_msg["role"] == "user"
        assert isinstance(last_msg["content"], list)
        assert any(
            c.get("type") == "video_url"
            and c["video_url"]["url"] == "http://host.docker.internal:4711/media/abc.mp4"
            for c in last_msg["content"]
        )

        assert body["extra_body"]["mm_processor_kwargs"]["video"] == {"fps": 2.0}

    @pytest.mark.asyncio
    async def test_chat_without_video_does_not_set_extra_body(
        self, backend: VLLMBackend, httpx_mock: HTTPXMock
    ):
        """Regression: image-only or text-only requests must not grow an
        extra_body.mm_processor_kwargs key they don't need."""
        httpx_mock.add_response(
            url=f"{BASE_URL}/chat/completions",
            status_code=200,
            json={"choices": [{"message": {"content": "ok"}}], "model": "x"},
        )
        await backend.chat(
            model="Qwen/Qwen2.5-VL-7B-Instruct",
            messages=[{"role": "user", "content": "hi"}],
        )
        body = _json.loads(httpx_mock.get_requests()[0].content)
        assert "extra_body" not in body or "mm_processor_kwargs" not in body.get("extra_body", {})


class TestChatStreamWithVideo:
    @pytest.mark.asyncio
    async def test_chat_stream_sends_video_url_and_mm_kwargs(
        self, backend: VLLMBackend, httpx_mock: HTTPXMock
    ):
        """chat_stream must thread video kwarg into the SSE request body
        the same way chat() does."""
        # A minimal valid SSE response: one data chunk + [DONE]
        sse_body = b'data: {"choices":[{"delta":{"content":"A"},"index":0}]}\n\ndata: [DONE]\n\n'
        httpx_mock.add_response(
            url=f"{BASE_URL}/chat/completions",
            status_code=200,
            content=sse_body,
            headers={"content-type": "text/event-stream"},
        )

        chunks: list[str] = []
        async for chunk in backend.chat_stream(
            model="mmangkad/Qwen3.6-27B-NVFP4",
            messages=[{"role": "user", "content": "What's in this clip?"}],
            video={
                "url": "http://host.docker.internal:4711/media/abc.mp4",
                "sampling": {"fps": 2.0},
            },
        ):
            chunks.append(chunk)

        # Collected at least one chunk
        assert chunks

        request = httpx_mock.get_requests()[0]
        body = _json.loads(request.content)

        last_msg = body["messages"][-1]
        assert isinstance(last_msg["content"], list)
        assert any(
            c.get("type") == "video_url"
            and c["video_url"]["url"] == "http://host.docker.internal:4711/media/abc.mp4"
            for c in last_msg["content"]
        )
        assert body["extra_body"]["mm_processor_kwargs"]["video"] == {"fps": 2.0}
        assert body.get("stream") is True

    @pytest.mark.asyncio
    async def test_chat_stream_without_video_does_not_set_extra_body(
        self, backend: VLLMBackend, httpx_mock: HTTPXMock
    ):
        """Regression: text-only streaming requests must not grow an extra_body
        they don't need."""
        sse_body = b'data: {"choices":[{"delta":{"content":"ok"},"index":0}]}\n\ndata: [DONE]\n\n'
        httpx_mock.add_response(
            url=f"{BASE_URL}/chat/completions",
            status_code=200,
            content=sse_body,
            headers={"content-type": "text/event-stream"},
        )

        async for _ in backend.chat_stream(
            model="x",
            messages=[{"role": "user", "content": "hi"}],
        ):
            pass

        body = _json.loads(httpx_mock.get_requests()[0].content)
        assert "extra_body" not in body or "mm_processor_kwargs" not in body.get("extra_body", {})
