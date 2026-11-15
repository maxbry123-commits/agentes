"""Mock tests for utils layer (embedding + llm) so external deps can be absent."""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from mmem.config import EmbeddingConfig, LLMConfig


# ── EmbeddingModel tests ─────────────────────────────────────────────

class TestEmbeddingModel:
    def _make_model(self):
        from mmem.utils.embedding import EmbeddingModel

        cfg = EmbeddingConfig(model_name="mock-model", dimension=384)
        model = EmbeddingModel(config=cfg)
        return model

    @patch("mmem.utils.embedding.EmbeddingModel._load")
    def test_embed_single(self, mock_load):
        model = self._make_model()
        fake_vec = np.random.randn(384).astype(np.float32)
        model._model = MagicMock()
        model._model.encode.return_value = fake_vec

        result = model.embed("hello")
        assert result.shape == (384,)
        assert result.dtype == np.float32
        model._model.encode.assert_called_once()

    @patch("mmem.utils.embedding.EmbeddingModel._load")
    def test_embed_batch(self, mock_load):
        model = self._make_model()
        fake_vecs = np.random.randn(3, 384).astype(np.float32)
        model._model = MagicMock()
        model._model.encode.return_value = fake_vecs

        result = model.embed_batch(["a", "b", "c"])
        assert result.shape == (3, 384)
        model._model.encode.assert_called_once()

    def test_dimension_property(self):
        model = self._make_model()
        assert model.dimension == 384

    @patch("mmem.utils.embedding.EmbeddingModel._load")
    def test_embed_returns_correct_dtype_even_if_model_returns_float64(self, mock_load):
        model = self._make_model()
        fake_vec = np.random.randn(384).astype(np.float64)
        model._model = MagicMock()
        model._model.encode.return_value = fake_vec

        result = model.embed("test")
        assert result.dtype == np.float32


# ── LLMClient tests ──────────────────────────────────────────────────

class TestLLMClient:
    def _make_client(self):
        from mmem.utils.llm import LLMClient

        cfg = LLMConfig(
            api_key="test-key",
            base_url="http://fake",
            max_retries=3,
            timeout=10.0,
            backoff_base=1.0,  # no real wait in tests
            backoff_max=0.01,
        )
        return LLMClient(config=cfg)

    @patch("mmem.utils.llm.OpenAI")
    def test_chat_success(self, MockOpenAI):
        mock_client = MagicMock()
        MockOpenAI.return_value = mock_client
        mock_resp = MagicMock()
        mock_resp.choices = [MagicMock()]
        mock_resp.choices[0].message.content = "Hello!"
        mock_client.chat.completions.create.return_value = mock_resp

        client = self._make_client()
        client._client = mock_client
        result = client.chat("Hi")
        assert result == "Hello!"

    @patch("mmem.utils.llm.OpenAI")
    def test_chat_json_success(self, MockOpenAI):
        mock_client = MagicMock()
        MockOpenAI.return_value = mock_client
        mock_resp = MagicMock()
        mock_resp.choices = [MagicMock()]
        mock_resp.choices[0].message.content = '{"key": "value"}'
        mock_client.chat.completions.create.return_value = mock_resp

        client = self._make_client()
        client._client = mock_client
        result = client.chat_json("Give me JSON")
        assert result == {"key": "value"}

    @patch("mmem.utils.llm.OpenAI")
    def test_chat_json_strips_markdown_fence(self, MockOpenAI):
        mock_client = MagicMock()
        MockOpenAI.return_value = mock_client
        mock_resp = MagicMock()
        mock_resp.choices = [MagicMock()]
        mock_resp.choices[0].message.content = '```json\n{"a": 1}\n```'
        mock_client.chat.completions.create.return_value = mock_resp

        client = self._make_client()
        client._client = mock_client
        result = client.chat_json("Give JSON")
        assert result == {"a": 1}

    @patch("mmem.utils.llm.OpenAI")
    def test_chat_json_returns_empty_on_bad_json(self, MockOpenAI):
        mock_client = MagicMock()
        MockOpenAI.return_value = mock_client
        mock_resp = MagicMock()
        mock_resp.choices = [MagicMock()]
        mock_resp.choices[0].message.content = "not json at all"
        mock_client.chat.completions.create.return_value = mock_resp

        client = self._make_client()
        client._client = mock_client
        result = client.chat_json("Give JSON")
        assert result == {}

    @patch("mmem.utils.llm.OpenAI")
    def test_chat_json_strips_fence_with_trailing_text(self, MockOpenAI):
        mock_client = MagicMock()
        MockOpenAI.return_value = mock_client
        mock_resp = MagicMock()
        mock_resp.choices = [MagicMock()]
        mock_resp.choices[0].message.content = 'Here is the result:\n```json\n{"x": 2}\n```\nDone.'
        mock_client.chat.completions.create.return_value = mock_resp

        client = self._make_client()
        client._client = mock_client
        result = client.chat_json("Give JSON")
        assert result == {"x": 2}

    @patch("mmem.utils.llm.OpenAI")
    def test_chat_json_returns_list(self, MockOpenAI):
        mock_client = MagicMock()
        MockOpenAI.return_value = mock_client
        mock_resp = MagicMock()
        mock_resp.choices = [MagicMock()]
        mock_resp.choices[0].message.content = '[1, 2, 3]'
        mock_client.chat.completions.create.return_value = mock_resp

        client = self._make_client()
        client._client = mock_client
        result = client.chat_json("Give JSON")
        assert result == [1, 2, 3]

    @patch("mmem.utils.llm.OpenAI")
    def test_chat_json_returns_empty_on_scalar_json(self, MockOpenAI):
        mock_client = MagicMock()
        MockOpenAI.return_value = mock_client
        mock_resp = MagicMock()
        mock_resp.choices = [MagicMock()]
        mock_resp.choices[0].message.content = '42'
        mock_client.chat.completions.create.return_value = mock_resp

        client = self._make_client()
        client._client = mock_client
        result = client.chat_json("Give JSON")
        assert result == {}

    @patch("mmem.utils.llm.OpenAI")
    def test_chat_retries_on_rate_limit(self, MockOpenAI):
        from openai import RateLimitError

        mock_client = MagicMock()
        MockOpenAI.return_value = mock_client

        mock_resp_ok = MagicMock()
        mock_resp_ok.choices = [MagicMock()]
        mock_resp_ok.choices[0].message.content = "recovered"

        rate_err = RateLimitError(
            message="rate limited",
            response=MagicMock(status_code=429, headers={}),
            body=None,
        )
        mock_client.chat.completions.create.side_effect = [
            rate_err,
            mock_resp_ok,
        ]

        client = self._make_client()
        client._client = mock_client
        result = client.chat("test")
        assert result == "recovered"
        assert mock_client.chat.completions.create.call_count == 2

    @patch("mmem.utils.llm.OpenAI")
    def test_chat_raises_after_max_retries(self, MockOpenAI):
        mock_client = MagicMock()
        MockOpenAI.return_value = mock_client
        mock_client.chat.completions.create.side_effect = ValueError("permanent fail")

        client = self._make_client()
        client._client = mock_client
        with pytest.raises(ValueError, match="permanent fail"):
            client.chat("test")
        assert mock_client.chat.completions.create.call_count == 3


# ── Config validation tests ──────────────────────────────────────────

class TestConfigValidation:
    def test_write_config_rejects_bad_threshold(self):
        from mmem.config import WriteConfig

        with pytest.raises(Exception):
            WriteConfig(semantic_similarity_threshold=1.5)

    def test_retrieval_config_rejects_bad_discount(self):
        from mmem.config import RetrievalConfig

        with pytest.raises(Exception):
            RetrievalConfig(temporal_discount=0.0)  # gt=0, so 0.0 is invalid

    def test_llm_config_rejects_bad_temperature(self):
        with pytest.raises(Exception):
            LLMConfig(temperature=-0.1)

    def test_semantic_similarity_threshold_default_is_085(self):
        from mmem.config import WriteConfig

        cfg = WriteConfig()
        assert cfg.semantic_similarity_threshold == pytest.approx(0.85)

    def test_enable_causal_consolidation_default_true(self):
        from mmem.config import WriteConfig

        cfg = WriteConfig()
        assert cfg.enable_causal_consolidation is True

    def test_enable_fallback_extractor_default_true(self):
        from mmem.config import WriteConfig

        cfg = WriteConfig()
        assert cfg.enable_fallback_extractor is True

    def test_entity_merge_threshold_default(self):
        from mmem.config import WriteConfig

        cfg = WriteConfig()
        assert cfg.entity_merge_threshold == pytest.approx(0.90)

    def test_entity_merge_threshold_rejects_below_05(self):
        from mmem.config import WriteConfig

        with pytest.raises(Exception):
            WriteConfig(entity_merge_threshold=0.49)

    def test_entity_merge_threshold_rejects_above_1(self):
        from mmem.config import WriteConfig

        with pytest.raises(Exception):
            WriteConfig(entity_merge_threshold=1.01)
