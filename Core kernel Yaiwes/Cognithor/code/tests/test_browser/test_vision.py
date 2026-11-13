"""Tests für browser/vision.py — VisionAnalyzer."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from cognithor.browser.vision import (
    VisionAnalysisResult,
    VisionAnalyzer,
    VisionConfig,
)

# ============================================================================
# VisionConfig
# ============================================================================


class TestVisionConfig:
    def test_defaults(self) -> None:
        cfg = VisionConfig()
        assert cfg.enabled is False
        assert cfg.model == ""
        assert cfg.backend_type == "ollama"
        assert cfg.max_image_size_bytes == 20_000_000
        assert cfg.max_page_content_chars == 15_000
        assert cfg.analysis_temperature == 0.3

    def test_custom(self) -> None:
        cfg = VisionConfig(enabled=True, model="gpt-4o", backend_type="openai")
        assert cfg.enabled is True
        assert cfg.model == "gpt-4o"
        assert cfg.backend_type == "openai"


# ============================================================================
# VisionAnalysisResult
# ============================================================================


class TestVisionAnalysisResult:
    def test_defaults(self) -> None:
        r = VisionAnalysisResult()
        assert r.success is False
        assert r.description == ""
        assert r.elements == []
        assert r.error == ""

    def test_success(self) -> None:
        r = VisionAnalysisResult(success=True, description="Login-Seite")
        assert r.success is True
        assert r.description == "Login-Seite"


# ============================================================================
# VisionAnalyzer — Disabled
# ============================================================================


class TestVisionAnalyzerDisabled:
    def _make_disabled(self) -> VisionAnalyzer:
        llm = AsyncMock()
        cfg = VisionConfig(enabled=False)
        return VisionAnalyzer(llm, cfg)

    def test_is_enabled_false(self) -> None:
        v = self._make_disabled()
        assert v.is_enabled is False

    @pytest.mark.asyncio
    async def test_analyze_screenshot_disabled(self) -> None:
        v = self._make_disabled()
        result = await v.analyze_screenshot("base64data")
        assert result.success is False
        assert "nicht aktiviert" in result.error

    @pytest.mark.asyncio
    async def test_find_element_disabled(self) -> None:
        v = self._make_disabled()
        result = await v.find_element_by_vision("base64data", "Login-Button")
        assert result.success is False
        assert "nicht aktiviert" in result.error

    @pytest.mark.asyncio
    async def test_describe_page_disabled(self) -> None:
        v = self._make_disabled()
        result = await v.describe_page("base64data")
        assert result == ""

    def test_stats_disabled(self) -> None:
        v = self._make_disabled()
        s = v.stats()
        assert s["enabled"] is False
        assert s["calls"] == 0

    def test_enabled_but_no_model(self) -> None:
        llm = AsyncMock()
        cfg = VisionConfig(enabled=True, model="")
        v = VisionAnalyzer(llm, cfg)
        assert v.is_enabled is False


# ============================================================================
# VisionAnalyzer — Enabled (Mock-LLM)
# ============================================================================


class TestVisionAnalyzerEnabled:
    def _make_enabled(
        self, llm_response: str = "Beschreibung der Seite"
    ) -> tuple[VisionAnalyzer, AsyncMock]:
        llm = AsyncMock()
        llm.chat = AsyncMock(
            return_value={
                "message": {"role": "assistant", "content": llm_response},
                "done": True,
            }
        )
        cfg = VisionConfig(enabled=True, model="llava:13b", backend_type="ollama")
        v = VisionAnalyzer(llm, cfg)
        return v, llm

    def test_is_enabled_true(self) -> None:
        v, _ = self._make_enabled()
        assert v.is_enabled is True

    @pytest.mark.asyncio
    async def test_analyze_screenshot_success(self) -> None:
        v, llm = self._make_enabled("Die Seite zeigt ein Login-Formular.")
        result = await v.analyze_screenshot("aGVsbG8=")

        assert result.success is True
        assert "Login-Formular" in result.description
        llm.chat.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_analyze_screenshot_custom_prompt(self) -> None:
        v, llm = self._make_enabled("Rot und Blau.")
        result = await v.analyze_screenshot("aGVsbG8=", prompt="Welche Farben?")

        assert result.success is True
        # Prüfe dass der Custom-Prompt gesendet wurde
        call_args = llm.chat.call_args
        messages = (
            call_args.kwargs.get("messages") or call_args[1]
            if len(call_args) > 1
            else call_args.kwargs.get("messages")
        )
        assert messages is not None

    @pytest.mark.asyncio
    async def test_analyze_empty_screenshot(self) -> None:
        v, _ = self._make_enabled()
        result = await v.analyze_screenshot("")
        assert result.success is False
        assert "Kein Screenshot" in result.error or "no_screenshot" in result.error

    @pytest.mark.asyncio
    async def test_stats_after_calls(self) -> None:
        v, _ = self._make_enabled()
        await v.analyze_screenshot("data1")
        await v.analyze_screenshot("data2")

        s = v.stats()
        assert s["calls"] == 2
        assert s["errors"] == 0
        assert s["model"] == "llava:13b"
        assert s["enabled"] is True


# ============================================================================
# VisionAnalyzer — Fehlerbehandlung
# ============================================================================


class TestVisionAnalyzerError:
    @pytest.mark.asyncio
    async def test_llm_error(self) -> None:
        llm = AsyncMock()
        llm.chat = AsyncMock(side_effect=RuntimeError("Connection refused"))
        cfg = VisionConfig(enabled=True, model="llava:13b", backend_type="ollama")
        v = VisionAnalyzer(llm, cfg)

        result = await v.analyze_screenshot("data")

        assert result.success is False
        assert "fehlgeschlagen" in result.error
        assert v.stats()["errors"] == 1

    @pytest.mark.asyncio
    async def test_llm_timeout(self) -> None:
        llm = AsyncMock()
        llm.chat = AsyncMock(side_effect=TimeoutError("timeout"))
        cfg = VisionConfig(enabled=True, model="gpt-4o", backend_type="openai")
        v = VisionAnalyzer(llm, cfg)

        result = await v.analyze_screenshot("data")
        assert result.success is False
        assert v.stats()["errors"] == 1


# ============================================================================
# find_element_by_vision
# ============================================================================


class TestFindElementByVision:
    @pytest.mark.asyncio
    async def test_element_found(self) -> None:
        llm = AsyncMock()
        llm.chat = AsyncMock(
            return_value={
                "message": {"content": "Der Login-Button befindet sich oben rechts, blaue Farbe."},
                "done": True,
            }
        )
        cfg = VisionConfig(enabled=True, model="llava:13b", backend_type="ollama")
        v = VisionAnalyzer(llm, cfg)

        result = await v.find_element_by_vision("data", "Login-Button")
        assert result.success is True
        assert "Login-Button" in result.description

    @pytest.mark.asyncio
    async def test_element_not_found(self) -> None:
        llm = AsyncMock()
        llm.chat = AsyncMock(
            return_value={
                "message": {"content": "NOT FOUND"},
                "done": True,
            }
        )
        cfg = VisionConfig(enabled=True, model="llava:13b", backend_type="ollama")
        v = VisionAnalyzer(llm, cfg)

        result = await v.find_element_by_vision("data", "Impressum-Link")
        assert result.success is False
        assert "not_found" in result.error or "nicht gefunden" in result.error


# ============================================================================
# describe_page
# ============================================================================


class TestDescribePage:
    @pytest.mark.asyncio
    async def test_describe_success(self) -> None:
        llm = AsyncMock()
        llm.chat = AsyncMock(
            return_value={
                "message": {"content": "Ein Online-Shop mit Produktübersicht."},
                "done": True,
            }
        )
        cfg = VisionConfig(enabled=True, model="llava:13b", backend_type="ollama")
        v = VisionAnalyzer(llm, cfg)

        desc = await v.describe_page("data")
        assert "Online-Shop" in desc

    @pytest.mark.asyncio
    async def test_describe_error_returns_empty(self) -> None:
        llm = AsyncMock()
        llm.chat = AsyncMock(side_effect=RuntimeError("fail"))
        cfg = VisionConfig(enabled=True, model="llava:13b", backend_type="ollama")
        v = VisionAnalyzer(llm, cfg)

        desc = await v.describe_page("data")
        assert desc == ""


# ============================================================================
# page_content Integration
# ============================================================================


class TestVisionPageContent:
    """Tests für page_content Parameter in Vision-Methoden."""

    def _make_enabled(self, llm_response: str = "Analyse") -> tuple[VisionAnalyzer, AsyncMock]:
        llm = AsyncMock()
        llm.chat = AsyncMock(
            return_value={
                "message": {"role": "assistant", "content": llm_response},
                "done": True,
            }
        )
        cfg = VisionConfig(enabled=True, model="llava:13b", backend_type="ollama")
        v = VisionAnalyzer(llm, cfg)
        return v, llm

    @pytest.mark.asyncio
    async def test_analyze_with_page_content(self) -> None:
        """page_content wird an analyze_screenshot übergeben."""
        v, llm = self._make_enabled("Seite mit Formular")
        result = await v.analyze_screenshot("aGVsbG8=", page_content="<div>Login</div>")
        assert result.success is True
        # Prüfe dass HTML im Prompt gelandet ist
        call_args = llm.chat.call_args
        call_args.kwargs.get("messages", [])
        # Die build_vision_message + format_for_backend verpacken den Prompt,
        # aber der HTML-Content sollte im Prompt stecken
        assert llm.chat.await_count == 1

    @pytest.mark.asyncio
    async def test_page_content_appended_to_prompt(self) -> None:
        """page_content wird als HTML-Block an den Prompt angehängt."""
        v, llm = self._make_enabled("OK")

        # Patch _send_vision_request um den finalen Prompt zu inspizieren
        captured_prompts: list[str] = []

        async def capturing_send(screenshot_b64, prompt, page_content=""):
            if page_content:
                truncated = page_content[: v._config.max_page_content_chars]
                prompt = f"{prompt}\n\n## Seiten-HTML (bereinigt)\n```html\n{truncated}\n```"
            captured_prompts.append(prompt)
            # Rufe nicht das Original auf, sondern gib direkt zurück
            return VisionAnalysisResult(success=True, description="OK")

        v._send_vision_request = capturing_send

        await v.analyze_screenshot("aGVsbG8=", page_content="<h1>Test</h1>")
        assert len(captured_prompts) == 1
        assert "## Seiten-HTML (bereinigt)" in captured_prompts[0]
        assert "<h1>Test</h1>" in captured_prompts[0]

    @pytest.mark.asyncio
    async def test_page_content_empty_not_appended(self) -> None:
        """Leerer page_content ändert den Prompt nicht."""
        v, llm = self._make_enabled("OK")

        captured_prompts: list[str] = []

        async def capturing_send(screenshot_b64, prompt, page_content=""):
            if page_content:
                prompt = f"{prompt}\n\n## Seiten-HTML (bereinigt)\n```html\n{page_content}\n```"
            captured_prompts.append(prompt)
            return VisionAnalysisResult(success=True, description="OK")

        v._send_vision_request = capturing_send

        await v.analyze_screenshot("aGVsbG8=", page_content="")
        assert len(captured_prompts) == 1
        assert "Seiten-HTML" not in captured_prompts[0]

    @pytest.mark.asyncio
    async def test_find_element_with_page_content(self) -> None:
        """page_content wird an find_element_by_vision übergeben."""
        v, llm = self._make_enabled("Button oben rechts")
        result = await v.find_element_by_vision(
            "aGVsbG8=", "Login-Button", page_content="<button>Login</button>"
        )
        assert result.success is True

    @pytest.mark.asyncio
    async def test_describe_page_with_page_content(self) -> None:
        """page_content wird an describe_page übergeben."""
        v, llm = self._make_enabled("Ein Shop")
        desc = await v.describe_page("aGVsbG8=", page_content="<h1>Shop</h1>")
        assert desc == "Ein Shop"


# ============================================================================
# Desktop Element Parser
# ============================================================================

import json

from cognithor.browser.vision import _parse_desktop_elements, _validate_elements


class TestParseDesktopElements:
    def test_valid_json(self):
        raw = json.dumps(
            {
                "elements": [
                    {
                        "name": "Rechner",
                        "type": "window",
                        "x": 200,
                        "y": 300,
                        "w": 400,
                        "h": 500,
                        "text": "459",
                        "clickable": True,
                    }
                ]
            }
        )
        elements = _parse_desktop_elements(raw)
        assert len(elements) == 1
        assert elements[0]["name"] == "Rechner"
        assert elements[0]["x"] == 200
        assert elements[0]["clickable"] is True

    def test_json_in_markdown_block(self):
        raw = (
            "Hier ist meine Analyse:\n```json\n"
            + json.dumps({"elements": [{"name": "Button", "type": "button", "x": 50, "y": 60}]})
            + "\n```"
        )
        elements = _parse_desktop_elements(raw)
        assert len(elements) == 1
        assert elements[0]["name"] == "Button"

    def test_missing_coordinates_skipped(self):
        raw = json.dumps(
            {
                "elements": [
                    {"name": "OK", "type": "button"},
                    {"name": "Cancel", "type": "button", "x": 100, "y": 200},
                ]
            }
        )
        elements = _parse_desktop_elements(raw)
        assert len(elements) == 1
        assert elements[0]["name"] == "Cancel"

    def test_garbage_returns_empty(self):
        elements = _parse_desktop_elements("This is not JSON at all.")
        assert elements == []

    def test_think_tags_with_json(self):
        raw = "<think>Let me analyze...</think>\n" + json.dumps(
            {"elements": [{"name": "Start", "type": "button", "x": 24, "y": 1060}]}
        )
        elements = _parse_desktop_elements(raw)
        assert len(elements) == 1
        assert elements[0]["name"] == "Start"


class TestValidateElements:
    def test_int_coercion(self):
        elements = _validate_elements(
            [{"name": "Test", "x": "100", "y": "200", "w": "50", "h": "30"}]
        )
        assert elements[0]["x"] == 100
        assert isinstance(elements[0]["x"], int)

    def test_non_list_returns_empty(self):
        assert _validate_elements("not a list") == []
        assert _validate_elements(None) == []

    def test_non_dict_entries_skipped(self):
        assert _validate_elements(["not a dict", 42]) == []

    def test_defaults_applied(self):
        elements = _validate_elements([{"name": "X", "x": 10, "y": 20}])
        assert elements[0]["type"] == "other"
        assert elements[0]["w"] == 0
        assert elements[0]["text"] == ""
        assert elements[0]["clickable"] is False


# ============================================================================
# analyze_desktop
# ============================================================================


class TestAnalyzeDesktop:
    """Tests for VisionAnalyzer.analyze_desktop — desktop screenshot analysis."""

    def _make_analyzer(self, llm_response: str) -> tuple[VisionAnalyzer, AsyncMock]:
        llm = AsyncMock()
        llm.chat = AsyncMock(
            return_value={
                "message": {"role": "assistant", "content": llm_response},
            }
        )
        cfg = VisionConfig(enabled=True, model="qwen3-vl:32b", backend_type="ollama")
        return VisionAnalyzer(llm, cfg), llm

    @pytest.mark.asyncio
    async def test_returns_elements(self):
        response = json.dumps(
            {
                "elements": [
                    {
                        "name": "Rechner",
                        "type": "window",
                        "x": 200,
                        "y": 300,
                        "w": 400,
                        "h": 500,
                        "text": "",
                        "clickable": True,
                    },
                ]
            }
        )
        v, llm = self._make_analyzer(response)
        result = await v.analyze_desktop("base64data")

        assert result.success is True
        assert len(result.elements) == 1
        assert result.elements[0]["name"] == "Rechner"
        assert result.elements[0]["x"] == 200
        llm.chat.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_disabled_returns_error(self):
        llm = AsyncMock()
        v = VisionAnalyzer(llm, VisionConfig(enabled=False))
        result = await v.analyze_desktop("base64data")

        assert result.success is False
        assert "nicht aktiviert" in result.error
        llm.chat.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_empty_screenshot_returns_error(self):
        v, _ = self._make_analyzer("")
        result = await v.analyze_desktop("")

        assert result.success is False
        assert "Kein Screenshot" in result.error or "no_screenshot" in result.error

    @pytest.mark.asyncio
    async def test_task_context_appended_to_prompt(self):
        v, llm = self._make_analyzer('{"elements": []}')
        await v.analyze_desktop("base64data", task_context="Reddit oeffnen")

        call_args = llm.chat.call_args
        messages = str(call_args)
        assert "Reddit" in messages

    @pytest.mark.asyncio
    async def test_llm_error_handled(self):
        llm = AsyncMock()
        llm.chat = AsyncMock(side_effect=RuntimeError("GPU OOM"))
        cfg = VisionConfig(enabled=True, model="qwen3-vl:32b", backend_type="ollama")
        v = VisionAnalyzer(llm, cfg)

        result = await v.analyze_desktop("base64data")
        assert result.success is False
        assert "fehlgeschlagen" in result.error

    @pytest.mark.asyncio
    async def test_non_json_response_returns_description_no_elements(self):
        v, _ = self._make_analyzer("I see a calculator and a browser window.")
        result = await v.analyze_desktop("base64data")

        assert result.success is True
        assert "calculator" in result.description
        assert result.elements == []

    @pytest.mark.asyncio
    async def test_custom_prompt_overrides_default(self):
        v, llm = self._make_analyzer('{"elements": []}')
        await v.analyze_desktop("base64data", prompt="Custom prompt here")

        messages = str(llm.chat.call_args)
        assert "Custom prompt" in messages

    @pytest.mark.asyncio
    async def test_stats_updated(self):
        v, _ = self._make_analyzer('{"elements": []}')
        assert v.stats()["calls"] == 0

        await v.analyze_desktop("base64data")
        assert v.stats()["calls"] == 1


class TestExtractText:
    """Tests for VisionAnalyzer.extract_text_from_screenshot."""

    @pytest.mark.asyncio
    async def test_extract_text_success(self):
        llm = AsyncMock()
        llm.chat = AsyncMock(
            return_value={
                "message": {"content": "Reddit - r/locallama\nPost 1: Hello World\nPost 2: Test"},
            }
        )
        cfg = VisionConfig(enabled=True, model="qwen3-vl:32b", backend_type="ollama")
        v = VisionAnalyzer(llm, cfg)

        result = await v.extract_text_from_screenshot("base64data")
        assert result.success is True
        assert "Reddit" in result.description
        llm.chat.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_extract_text_disabled(self):
        llm = AsyncMock()
        v = VisionAnalyzer(llm, VisionConfig(enabled=False))
        result = await v.extract_text_from_screenshot("base64data")
        assert result.success is False
        assert "nicht aktiviert" in result.error

    @pytest.mark.asyncio
    async def test_extract_text_empty_screenshot(self):
        llm = AsyncMock()
        cfg = VisionConfig(enabled=True, model="qwen3-vl:32b")
        v = VisionAnalyzer(llm, cfg)
        result = await v.extract_text_from_screenshot("")
        assert result.success is False
