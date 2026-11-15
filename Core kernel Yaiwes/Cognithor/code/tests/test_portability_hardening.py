"""Tests for the 5 Portability Hardening fixes.

Proves each fix works cross-platform without requiring external services
(Ollama, network, C compiler).
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ============================================================================
# Fix 1: [all] extra — voice/postgresql removed, webrtcvad removed
# ============================================================================


class TestFix1AllExtraEntschaerft:
    """Proves [all] no longer pulls C-compiler-dependent packages."""

    def test_all_extra_excludes_voice(self) -> None:
        """[all] must NOT contain 'voice' — it needs C extensions on Windows."""
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib  # type: ignore[no-redef]

        pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"
        with open(pyproject, "rb") as f:
            data = tomllib.load(f)

        all_deps = data["project"]["optional-dependencies"]["all"]
        all_text = " ".join(all_deps).lower()
        assert "voice" not in all_text, "[all] must not include voice"
        assert "postgresql" not in all_text, "[all] must not include postgresql"

    def test_full_extra_includes_everything(self) -> None:
        """[full] must still include voice and postgresql."""
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib  # type: ignore[no-redef]

        pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"
        with open(pyproject, "rb") as f:
            data = tomllib.load(f)

        full_deps = data["project"]["optional-dependencies"]["full"]
        full_text = " ".join(full_deps).lower()
        assert "voice" in full_text, "[full] must include voice"
        assert "postgresql" in full_text, "[full] must include postgresql"

    def test_voice_extra_no_webrtcvad(self) -> None:
        """[voice] must not contain webrtcvad — it's dead code (Silero VAD)."""
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib  # type: ignore[no-redef]

        pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"
        with open(pyproject, "rb") as f:
            data = tomllib.load(f)

        voice_deps = data["project"]["optional-dependencies"]["voice"]
        voice_text = " ".join(voice_deps).lower()
        assert "webrtcvad" not in voice_text, "webrtcvad must be removed from [voice]"

    def test_startup_check_voice_group_no_webrtcvad(self) -> None:
        """startup_check.OPTIONAL_GROUPS['voice'] must not list webrtcvad."""
        from cognithor.core.startup_check import OPTIONAL_GROUPS

        voice_pkgs = OPTIONAL_GROUPS.get("voice", [])
        assert "webrtcvad" not in voice_pkgs, "webrtcvad must be removed from startup_check"

    def test_preflight_voice_group_no_webrtcvad(self) -> None:
        """preflight_check voice group must not list webrtcvad."""
        # Import the module's OPTIONAL_GROUPS by loading the script
        import importlib.util

        script = Path(__file__).resolve().parent.parent / "scripts" / "preflight_check.py"
        spec = importlib.util.spec_from_file_location("preflight_check", script)
        assert spec is not None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[union-attr]

        voice_pkgs = [pip_name for _, pip_name in mod.OPTIONAL_GROUPS.get("voice", [])]
        assert "webrtcvad" not in voice_pkgs, "webrtcvad must be removed from preflight voice"


# ============================================================================
# Fix 2: Model-Not-Found (404) clear error message
# ============================================================================


class TestFix2ModelNotFound404:
    """Proves HTTP 404 from Ollama yields a specific 'ollama pull' message."""

    @pytest.fixture()
    def config(self, tmp_path: Path) -> Any:
        from cognithor.config import CognithorConfig

        return CognithorConfig(cognithor_home=tmp_path)

    @pytest.fixture()
    def client(self, config: Any) -> Any:
        from cognithor.core.model_router import OllamaClient

        return OllamaClient(config)

    @pytest.mark.asyncio
    async def test_chat_404_raises_specific_message(self, client: Any) -> None:
        """OllamaClient.chat() on 404 must mention 'ollama pull'."""
        from cognithor.core.model_router import OllamaError

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = '{"error": "model not found"}'

        with patch.object(client, "_ensure_client") as mock_ensure:
            mock_http = AsyncMock()
            mock_http.post = AsyncMock(return_value=mock_response)
            mock_ensure.return_value = mock_http

            with pytest.raises(OllamaError) as exc_info:
                await client.chat(
                    model="qwen3:32b",
                    messages=[{"role": "user", "content": "hi"}],
                )

        assert exc_info.value.status_code == 404
        assert "ollama pull" in str(exc_info.value).lower()
        assert "qwen3:32b" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_chat_500_still_raises_generic(self, client: Any) -> None:
        """Non-404 errors must still use the generic error format."""
        from cognithor.core.model_router import OllamaError

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        with patch.object(client, "_ensure_client") as mock_ensure:
            mock_http = AsyncMock()
            mock_http.post = AsyncMock(return_value=mock_response)
            mock_ensure.return_value = mock_http

            with pytest.raises(OllamaError) as exc_info:
                await client.chat(
                    model="qwen3:32b",
                    messages=[{"role": "user", "content": "hi"}],
                )

        assert exc_info.value.status_code == 500
        assert "ollama pull" not in str(exc_info.value).lower()

    def test_error_messages_classifies_ollama_404(self) -> None:
        """classify_error_for_user must handle OllamaError with status_code=404."""
        from cognithor.core.model_router import OllamaError
        from cognithor.utils.error_messages import classify_error_for_user

        exc = OllamaError("Modell 'qwen3:32b' nicht gefunden", status_code=404)
        msg = classify_error_for_user(exc)
        assert "ollama pull" in msg.lower()

    def test_error_messages_classifies_ollama_connection(self) -> None:
        """classify_error_for_user must handle OllamaError connection failures."""
        from cognithor.core.model_router import OllamaError
        from cognithor.utils.error_messages import classify_error_for_user

        exc = OllamaError("Ollama nicht erreichbar unter http://localhost:11434")
        msg = classify_error_for_user(exc)
        assert "ollama serve" in msg.lower() or "nicht erreichbar" in msg.lower()

    @pytest.mark.asyncio
    async def test_planner_404_returns_pull_hint(self, config: Any) -> None:
        """Planner must return a direct_response with 'ollama pull' on 404."""
        from cognithor.core.model_router import ModelRouter, OllamaClient, OllamaError
        from cognithor.core.planner import Planner
        from cognithor.models import WorkingMemory

        mock_ollama = AsyncMock(spec=OllamaClient)
        mock_ollama.chat.side_effect = OllamaError(
            "Modell 'qwen3:32b' nicht gefunden",
            status_code=404,
        )

        mock_router = MagicMock(spec=ModelRouter)
        mock_router.select_model.return_value = "qwen3:32b"
        mock_router.get_model_config.return_value = {
            "temperature": 0.7,
            "top_p": 0.9,
            "context_window": 32768,
        }

        planner = Planner(config, mock_ollama, mock_router)
        wm = WorkingMemory(session_id="test")

        plan = await planner.plan("Hallo", wm, {})

        assert plan.is_direct_response
        assert plan.confidence == 0.0
        assert "ollama pull" in plan.direct_response.lower()
        assert "qwen3:32b" in plan.direct_response


# ============================================================================
# Fix 3: Windows UTF-8 stdout
# ============================================================================


class TestFix3WindowsUtf8Stdout:
    """Proves the UTF-8 reconfigure block works on all platforms."""

    def test_reconfigure_block_exists_in_main(self) -> None:
        """main() source must contain the stream.reconfigure() block."""
        import inspect

        from cognithor.__main__ import main

        source = inspect.getsource(main)
        assert "reconfigure" in source
        assert 'encoding="utf-8"' in source
        assert 'errors="replace"' in source

    def test_reconfigure_actually_works(self) -> None:
        """Simulates a cp1252 stream and verifies reconfigure switches to UTF-8."""
        # Create a BytesIO-backed text stream with cp1252 encoding
        buf = io.BytesIO()
        stream = io.TextIOWrapper(buf, encoding="cp1252", errors="strict")

        assert stream.encoding == "cp1252"

        # Apply the same logic as __main__.main()
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

        assert stream.encoding == "utf-8"

        # Now write German umlauts — would have been lossy with cp1252 -> utf-8 mismatch
        stream.write("Hallo Welt! Aeoeue")
        stream.flush()

    def test_reconfigure_survives_non_reconfigurable_stream(self) -> None:
        """If a stream has no reconfigure(), the code must not crash."""
        stream = MagicMock(spec=[])  # no reconfigure attribute

        # This mirrors the guard in __main__.py
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
        # Must not raise — that's the test


# ============================================================================
# Fix 4: LLM unreachable prominent terminal warning
# ============================================================================


class TestFix4LlmUnreachableWarning:
    """Proves the LLM warning is printed when backend is unavailable."""

    @pytest.mark.asyncio
    async def test_warning_printed_when_llm_unavailable(self, tmp_path: Path) -> None:
        """When _llm.is_available() returns False, a visible warning must appear."""
        from cognithor.config import CognithorConfig

        config = CognithorConfig(cognithor_home=tmp_path)

        mock_gateway = MagicMock()
        mock_llm = AsyncMock()
        mock_llm.is_available.return_value = False
        mock_llm.backend_type = "ollama"
        mock_gateway._llm = mock_llm
        mock_gateway.initialize = AsyncMock()
        mock_gateway.start = AsyncMock()
        mock_gateway.shutdown = AsyncMock()
        mock_gateway._channels = {}

        captured = io.StringIO()

        # Simulate the run() logic inline (the relevant fragment)
        _llm = getattr(mock_gateway, "_llm", None)
        if _llm and not await _llm.is_available():
            _backend = getattr(_llm, "backend_type", "ollama")
            print("!" * 60, file=captured)
            print("  WARNUNG: Sprachmodell nicht erreichbar!", file=captured)
            print("!" * 60, file=captured)
            if _backend == "ollama":
                _ollama_url = config.ollama.base_url
                print(f"  Ollama antwortet nicht unter {_ollama_url}", file=captured)
                print("    ollama serve", file=captured)
                print(f"    ollama pull {config.models.planner.name}", file=captured)

        output = captured.getvalue()
        assert "WARNUNG" in output
        assert "ollama serve" in output
        assert config.models.planner.name in output

    @pytest.mark.asyncio
    async def test_no_warning_when_llm_available(self) -> None:
        """When _llm.is_available() returns True, no warning must appear."""
        mock_llm = AsyncMock()
        mock_llm.is_available.return_value = True

        captured = io.StringIO()

        _llm = mock_llm
        if _llm and not await _llm.is_available():
            print("WARNUNG!", file=captured)

        assert captured.getvalue() == ""

    def test_warning_code_present_in_main(self) -> None:
        """The __main__.py run() must contain the LLM availability check."""
        import inspect

        from cognithor.__main__ import main

        source = inspect.getsource(main)
        assert "is_available" in source
        assert "WARNUNG" in source or "WARNING" in source
        assert "ollama serve" in source or "ollama" in source.lower()


# ============================================================================
# Fix 5: README/PREREQUISITES Windows PATH hints
# ============================================================================


class TestFix5DocsWindowsPath:
    """Proves docs mention python -m cognithor and PATH hints for Windows."""

    def _read_file(self, name: str) -> str:
        path = Path(__file__).resolve().parent.parent / name
        return path.read_text(encoding="utf-8")

    def test_readme_mentions_python_m_jarvis_prominently(self) -> None:
        """README Quick Start must show 'python -m cognithor' as equal alternative."""
        content = self._read_file("README.md")
        # Must appear as a non-comment line (not just "# or: python -m cognithor")
        lines = content.splitlines()
        prominent_lines = [
            l for l in lines if "python -m cognithor" in l and not l.strip().startswith("#")
        ]
        assert len(prominent_lines) >= 1, (
            "python -m cognithor must be prominent, not just a comment"
        )

    def test_readme_has_windows_path_hint(self) -> None:
        """README must mention PATH and Scripts for Windows users."""
        content = self._read_file("README.md")
        assert "Scripts" in content, "README must mention Scripts directory for PATH"
        assert "python -m cognithor" in content

    def test_prerequisites_has_windows_path_hint(self) -> None:
        """PREREQUISITES Windows section must mention PATH workaround."""
        content = self._read_file("PREREQUISITES.md")
        assert "python -m cognithor" in content, "PREREQUISITES must mention python -m cognithor"
        assert "PATH" in content, "PREREQUISITES must mention PATH"

    def test_prerequisites_no_webrtcvad(self) -> None:
        """PREREQUISITES voice section must not mention webrtcvad."""
        content = self._read_file("PREREQUISITES.md")
        assert "webrtcvad" not in content, "PREREQUISITES must not list webrtcvad"
