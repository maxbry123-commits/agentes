"""Browser Vision -- VisionAnalyzer: Screenshot -> LLM -> Description.

Connects browser screenshots with vision-capable LLMs.
Uses core/vision.py for backend-agnostic message formatting
and UnifiedLLMClient for LLM communication.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from cognithor.core.vision import (
    build_vision_message,
    format_for_backend,
)
from cognithor.utils.logging import get_logger

log = get_logger(__name__)


# ── Configuration ────────────────────────────────────────────────────


@dataclass
class VisionConfig:
    """Configuration for the VisionAnalyzer."""

    enabled: bool = False
    model: str = ""
    backend_type: str = "ollama"
    max_image_size_bytes: int = 20_000_000  # 20 MB
    max_page_content_chars: int = 15_000
    analysis_temperature: float = 0.3


# ── Result ─────────────────────────────────────────────────────────


@dataclass
class VisionAnalysisResult:
    """Result of a vision analysis."""

    success: bool = False
    description: str = ""
    elements: list[dict[str, Any]] = field(default_factory=list)
    error: str = ""


# ── Default-Prompts ──────────────────────────────────────────────────

_DEFAULT_ANALYSIS_PROMPT = (
    "Analysiere diesen Screenshot einer Webseite. Beschreibe:\n"
    "1. Die Seitenstruktur und das Layout\n"
    "2. Interaktive Elemente (Buttons, Links, Formulare)\n"
    "3. Sichtbare Fehlermeldungen oder Warnungen\n"
    "4. Den aktuellen Zustand der Seite\n"
    "5. Nutze auch den mitgelieferten HTML-Kontext, falls vorhanden\n"
    "Antworte auf Deutsch, kompakt und strukturiert."
)

_FIND_ELEMENT_PROMPT_TEMPLATE = (
    "Finde auf diesem Screenshot das folgende Element: '{description}'\n\n"
    "Falls sichtbar, beschreibe:\n"
    "- Position auf der Seite (oben/mitte/unten, links/mitte/rechts)\n"
    "- Aussehen (Farbe, Größe, Text)\n"
    "- Möglichen CSS-Selector oder XPath-Hinweis (nutze auch den HTML-Kontext)\n"
    "- Ob es klickbar/interaktiv aussieht\n\n"
    "Falls NICHT sichtbar, antworte exakt mit: NOT FOUND"
)

_DESCRIBE_PAGE_PROMPT = (
    "Beschreibe diese Webseite in 1-2 Sätzen: Was zeigt sie, "
    "welcher Typ ist es (Shop, Login, Artikel, etc.)?"
)

_DESKTOP_ANALYSIS_PROMPT = (
    "Analysiere diesen Desktop-Screenshot. Identifiziere ALLE sichtbaren "
    "UI-Elemente.\n\n"
    "Fuer JEDES Element liefere:\n"
    "- name: Beschreibender Name (z.B. 'Adressleiste', 'Suchfeld', 'Rechner')\n"
    "- type: window | button | textfield | menu | icon | tab | scrollbar | link | other\n"
    "- x: X-Pixel-Koordinate der Mitte des Elements\n"
    "- y: Y-Pixel-Koordinate der Mitte des Elements\n"
    "- w: Breite in Pixeln (geschaetzt)\n"
    "- h: Hoehe in Pixeln (geschaetzt)\n"
    "- text: Sichtbarer Text im Element (falls vorhanden)\n"
    "- clickable: true/false\n\n"
    "Antworte NUR mit validem JSON:\n"
    '{"elements": [{"name": "...", "type": "...", "x": 0, "y": 0, '
    '"w": 0, "h": 0, "text": "...", "clickable": true}]}'
)

_DESKTOP_CONTEXTUAL_PROMPT_SUFFIX = (
    "\n\nKontext: {context}\nFokussiere auf Elemente die fuer diese Aufgabe relevant sind."
)


def _parse_desktop_elements(raw_response: str) -> list[dict[str, Any]]:
    """Parse structured UI elements from vision model response.

    Uses a 4-tier fallback strategy:
    1. Direct json.loads
    2. Extract ```json ... ``` markdown block
    3. Find JSON object containing "elements" in response
    4. Empty list fallback
    """
    import json
    import re

    # Tier 1: direct parse
    try:
        data = json.loads(raw_response)
        if isinstance(data, dict) and "elements" in data:
            return _validate_elements(data["elements"])
    except (json.JSONDecodeError, ValueError):
        pass

    # Tier 2: markdown code block
    md_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", raw_response, re.DOTALL)
    if md_match:
        try:
            data = json.loads(md_match.group(1))
            if isinstance(data, dict) and "elements" in data:
                return _validate_elements(data["elements"])
        except (json.JSONDecodeError, ValueError):
            pass

    # Tier 3: find JSON object in response
    json_match = re.search(r"\{[\s\S]*\"elements\"[\s\S]*\}", raw_response)
    if json_match:
        try:
            data = json.loads(json_match.group())
            if isinstance(data, dict) and "elements" in data:
                return _validate_elements(data["elements"])
        except (json.JSONDecodeError, ValueError):
            pass

    # Tier 4: empty list
    return []


def _validate_elements(elements: Any) -> list[dict[str, Any]]:
    """Validate and normalize element dicts from vision model."""
    if not isinstance(elements, list):
        return []

    validated = []
    for el in elements:
        if not isinstance(el, dict):
            continue
        if "name" not in el or "x" not in el or "y" not in el:
            continue
        validated.append(
            {
                "name": str(el.get("name", "")),
                "type": str(el.get("type", "other")),
                "x": int(el.get("x", 0)),
                "y": int(el.get("y", 0)),
                "w": int(el.get("w", 0)),
                "h": int(el.get("h", 0)),
                "text": str(el.get("text", "")),
                "clickable": bool(el.get("clickable", False)),
            }
        )

    return validated


# ── VisionAnalyzer ───────────────────────────────────────────────────


class VisionAnalyzer:
    """Connects browser screenshots with vision LLMs.

    Args:
        llm_client: A UnifiedLLMClient (or compatible object with chat() method).
        config: VisionConfig with model/backend settings.
    """

    def __init__(self, llm_client: Any, config: VisionConfig) -> None:
        self._llm = llm_client
        self._config = config
        self._call_count = 0
        self._error_count = 0
        self._total_duration_ms = 0

    @property
    def is_enabled(self) -> bool:
        return self._config.enabled and bool(self._config.model)

    async def analyze_screenshot(
        self,
        screenshot_b64: str,
        prompt: str = "",
        page_content: str = "",
    ) -> VisionAnalysisResult:
        """Analyzes a screenshot with the vision LLM.

        Args:
            screenshot_b64: Base64-encoded screenshot (PNG).
            prompt: Optional custom prompt (default: page structure analysis).
            page_content: Optional cleaned HTML content of the page.

        Returns:
            VisionAnalysisResult with description or error.
        """
        if not self.is_enabled:
            return VisionAnalysisResult(error="Vision nicht aktiviert")

        if not screenshot_b64:
            return VisionAnalysisResult(error="Kein Screenshot-Daten")

        prompt = prompt or _DEFAULT_ANALYSIS_PROMPT
        return await self._send_vision_request(screenshot_b64, prompt, page_content)

    async def find_element_by_vision(
        self,
        screenshot_b64: str,
        description: str,
        page_content: str = "",
    ) -> VisionAnalysisResult:
        """Searches for an element on the screenshot by description.

        Args:
            screenshot_b64: Base64-encoded screenshot.
            description: Description of the element to find.
            page_content: Optional cleaned HTML content of the page.

        Returns:
            VisionAnalysisResult -- elements contains hints for locating.
        """
        if not self.is_enabled:
            return VisionAnalysisResult(error="Vision nicht aktiviert")

        prompt = _FIND_ELEMENT_PROMPT_TEMPLATE.format(description=description)
        result = await self._send_vision_request(screenshot_b64, prompt, page_content)

        if result.success and "NOT FOUND" in result.description.upper():
            result.success = False
            result.error = f"Element nicht gefunden: {description}"

        return result

    async def describe_page(self, screenshot_b64: str, page_content: str = "") -> str:
        """Short page description (or empty string if disabled).

        Args:
            screenshot_b64: Base64-encoded screenshot.
            page_content: Optional cleaned HTML content of the page.

        Returns:
            Short page description or "".
        """
        if not self.is_enabled:
            return ""

        result = await self._send_vision_request(
            screenshot_b64, _DESCRIBE_PAGE_PROMPT, page_content
        )
        return result.description if result.success else ""

    async def analyze_desktop(
        self,
        screenshot_b64: str,
        prompt: str = "",
        task_context: str = "",
    ) -> VisionAnalysisResult:
        """Analyze a desktop screenshot and identify UI elements with coordinates.

        Unlike analyze_screenshot (browser-focused), this method is optimized
        for desktop environments: pixel coordinates instead of CSS selectors,
        window detection, taskbar elements, etc.

        Args:
            screenshot_b64: Base64-encoded screenshot (PNG).
            prompt: Optional custom prompt (default: desktop element detection).
            task_context: Optional task description to focus the analysis.

        Returns:
            VisionAnalysisResult with description and elements list.
        """
        if not self.is_enabled:
            return VisionAnalysisResult(error="Vision nicht aktiviert")

        if not screenshot_b64:
            return VisionAnalysisResult(error="Kein Screenshot-Daten")

        effective_prompt = prompt or _DESKTOP_ANALYSIS_PROMPT
        if task_context and not prompt:
            effective_prompt += _DESKTOP_CONTEXTUAL_PROMPT_SUFFIX.format(context=task_context)

        result = await self._send_vision_request(screenshot_b64, effective_prompt)

        if result.success and result.description:
            result.elements = _parse_desktop_elements(result.description)

        return result

    async def extract_text_from_screenshot(
        self,
        screenshot_b64: str,
    ) -> VisionAnalysisResult:
        """Extract all visible text from a screenshot (OCR-like).

        Uses the vision model to read text from the screen, without
        structured element detection. Optimized for content extraction.
        """
        if not self.is_enabled:
            return VisionAnalysisResult(error="Vision nicht aktiviert")

        if not screenshot_b64:
            return VisionAnalysisResult(error="Kein Screenshot-Daten")

        prompt = (
            "Lies ALLEN sichtbaren Text in diesem Screenshot ab. "
            "Gib den Text zeilenweise wieder, so wie er auf dem Bildschirm "
            "erscheint. Antworte NUR mit dem extrahierten Text, kein JSON, "
            "keine Erklaerungen."
        )
        return await self._send_vision_request(screenshot_b64, prompt)

    def stats(self) -> dict[str, Any]:
        return {
            "enabled": self.is_enabled,
            "model": self._config.model,
            "backend": self._config.backend_type,
            "calls": self._call_count,
            "errors": self._error_count,
            "total_duration_ms": self._total_duration_ms,
        }

    # ── Internal ─────────────────────────────────────────────────────

    async def _send_vision_request(
        self,
        screenshot_b64: str,
        prompt: str,
        page_content: str = "",
    ) -> VisionAnalysisResult:
        """Sends a screenshot + prompt to the vision LLM."""
        start = time.monotonic()
        self._call_count += 1

        try:
            if page_content:
                truncated = page_content[: self._config.max_page_content_chars]
                prompt = f"{prompt}\n\n## Seiten-HTML (bereinigt)\n```html\n{truncated}\n```"

            msg = build_vision_message(prompt, [screenshot_b64])
            formatted = format_for_backend(msg, self._config.backend_type)

            response = await self._llm.chat(
                model=self._config.model,
                messages=[formatted],
                temperature=self._config.analysis_temperature,
            )

            # Evaluate response -- UnifiedLLMClient returns Ollama format
            content = ""
            if isinstance(response, dict):
                content = response.get("message", {}).get("content", "")
            elif hasattr(response, "content"):
                content = response.content
            else:
                content = str(response)

            duration_ms = int((time.monotonic() - start) * 1000)
            self._total_duration_ms += duration_ms

            log.debug(
                "vision_analysis_done",
                model=self._config.model,
                duration_ms=duration_ms,
                response_len=len(content),
            )

            return VisionAnalysisResult(
                success=True,
                description=content,
            )

        except Exception as exc:
            self._error_count += 1
            duration_ms = int((time.monotonic() - start) * 1000)
            self._total_duration_ms += duration_ms

            log.warning(
                "vision_analysis_failed",
                model=self._config.model,
                error=str(exc),
                duration_ms=duration_ms,
            )

            return VisionAnalysisResult(
                success=False,
                error=f"Vision-Analyse fehlgeschlagen: {exc}",
            )
