from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest

from cognithor.memory.cag.builders.native import NativeLlamaCppBuilder
from cognithor.memory.cag.models import CacheEntry


def _entry(cache_id: str = "core", text: str = "hello") -> CacheEntry:
    return CacheEntry(
        cache_id=cache_id,
        content_hash="h",
        normalized_text=text,
        token_count=1,
        source_tier="core",
        created_at="2026-01-01T00:00:00Z",
        model_id="test",
    )


class TestNativeLlamaCppBuilder:
    @pytest.mark.asyncio
    async def test_is_available_true(self):
        fake_mod = ModuleType("llama_cpp")
        with patch.dict(sys.modules, {"llama_cpp": fake_mod}):
            b = NativeLlamaCppBuilder()
            assert await b.is_available() is True

    @pytest.mark.asyncio
    async def test_is_available_false(self):
        with patch.dict(sys.modules, {"llama_cpp": None}):
            b = NativeLlamaCppBuilder()
            assert await b.is_available() is False

    def test_supports_native_state(self):
        assert NativeLlamaCppBuilder().supports_native_state() is True

    @pytest.mark.asyncio
    async def test_prepare_prefix_same_as_prefix_builder(self):
        from cognithor.memory.cag.builders.prefix import PrefixCacheBuilder

        entries = [_entry("b", "bb"), _entry("a", "aa")]
        native = await NativeLlamaCppBuilder().prepare_prefix(entries, "m")
        prefix = await PrefixCacheBuilder().prepare_prefix(entries, "m")
        assert native == prefix

    @pytest.mark.asyncio
    async def test_build_state_mocked(self, tmp_path):
        mock_llama_cls = MagicMock()
        mock_llm = MagicMock()
        mock_llama_cls.return_value = mock_llm
        mock_llm.tokenize.return_value = [1, 2, 3]

        fake_mod = ModuleType("llama_cpp")
        fake_mod.Llama = mock_llama_cls  # type: ignore[attr-defined]

        target = tmp_path / "state.bin"
        with patch.dict(sys.modules, {"llama_cpp": fake_mod}):
            b = NativeLlamaCppBuilder()
            result = await b.build_state("hello", "/fake/model.gguf", target)

        assert result == target
        mock_llm.tokenize.assert_called_once()
        mock_llm.eval.assert_called_once_with([1, 2, 3])
        mock_llm.save_state.assert_called_once_with(str(target))

    @pytest.mark.asyncio
    async def test_load_state_mocked(self, tmp_path):
        mock_llama_cls = MagicMock()
        mock_llm = MagicMock()
        mock_llama_cls.return_value = mock_llm

        fake_mod = ModuleType("llama_cpp")
        fake_mod.Llama = mock_llama_cls  # type: ignore[attr-defined]

        state_file = tmp_path / "state.bin"
        state_file.write_bytes(b"fake")

        with patch.dict(sys.modules, {"llama_cpp": fake_mod}):
            b = NativeLlamaCppBuilder()
            result = await b.load_state(state_file, "/fake/model.gguf")

        assert result is mock_llm
        mock_llm.load_state.assert_called_once_with(str(state_file))
