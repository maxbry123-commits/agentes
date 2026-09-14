"""Tests fuer das mehrstufige Verified Web Lookup (verified_lookup.py).

Testet:
  - Parallele Extraktion (Trafilatura + Browser)
  - Fakten-Extraktion per LLM
  - Konsens-Algorithmus (Heuristik + LLM)
  - Formatierung und Fehlerbehandlung
  - MCP-Tool-Registrierung
  - Edge Cases (keine Ergebnisse, LLM-Fehler, Timeout)
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock

import pytest

from cognithor.mcp.verified_lookup import (
    ExtractedFact,
    SourceResult,
    VerificationResult,
    VerifiedWebLookup,
    register_verified_lookup_tools,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture()
def config(tmp_path):
    from cognithor.config import CognithorConfig

    return CognithorConfig(cognithor_home=tmp_path)


@pytest.fixture()
def mock_web_tools() -> AsyncMock:
    """Mock WebTools mit Such- und Fetch-Ergebnissen."""
    web = AsyncMock()
    web.web_search = AsyncMock(
        return_value=(
            "1. Cognithor GitHub\n"
            "URL: https://github.com/Alex8791-cyber/cognithor\n"
            "Snippet: An autonomous AI agent OS\n\n"
            "2. Cognithor PyPI\n"
            "URL: https://pypi.org/project/cognithor/\n"
            "Snippet: Cognithor package\n\n"
            "3. HackerNews Discussion\n"
            "URL: https://news.ycombinator.com/item?id=99999\n"
            "Snippet: Discussion about cognithor stars\n"
        )
    )
    web.web_fetch = AsyncMock(
        return_value="Cognithor has 142 stars on GitHub. It is an autonomous AI agent."
    )
    return web


@dataclass
class MockBrowserResult:
    success: bool = True
    text: str = "GitHub - cognithor: 142 stars. An AI agent OS by Alexander Soellner."
    url: str = "https://github.com/Alex8791-cyber/cognithor"
    title: str = "Cognithor"
    screenshot_path: str | None = None
    error: str | None = None


@pytest.fixture()
def mock_browser() -> AsyncMock:
    """Mock BrowserTool mit navigate-Ergebnis."""
    browser = AsyncMock()
    browser.navigate = AsyncMock(return_value=MockBrowserResult())
    return browser


@pytest.fixture()
def mock_llm_fn() -> AsyncMock:
    """Mock LLM-Funktion die strukturierte Fakten zurueckgibt."""

    async def _llm(prompt: str, model: str = "") -> str:
        if "Extract factual claims" in prompt:
            return json.dumps(
                {
                    "facts": [
                        {
                            "claim": "Cognithor has 142 GitHub stars",
                            "value": "142",
                            "type": "number",
                        }
                    ]
                }
            )
        elif "Multiple sources" in prompt:
            return json.dumps(
                {
                    "answer": "Cognithor hat 142 Stars auf GitHub.",
                    "confidence": 0.92,
                    "discrepancies": [],
                }
            )
        return "{}"

    return AsyncMock(side_effect=_llm)


@pytest.fixture()
def lookup(config, mock_web_tools, mock_browser, mock_llm_fn) -> VerifiedWebLookup:
    """Vollstaendig konfiguriertes VerifiedWebLookup."""
    vl = VerifiedWebLookup(config)
    vl._set_web_tools(mock_web_tools)
    vl._set_browser_tool(mock_browser)
    vl._set_llm_fn(mock_llm_fn, "test-model")
    return vl


# ============================================================================
# Test: Hauptmethode verified_lookup
# ============================================================================


class TestVerifiedLookup:
    """Tests fuer die Hauptmethode."""

    @pytest.mark.asyncio
    async def test_full_pipeline(self, lookup: VerifiedWebLookup) -> None:
        """Voller Pipeline-Durchlauf mit allen Agenten."""
        result = await lookup.verified_lookup(
            query="Wie viele GitHub Stars hat cognithor?",
            num_sources=3,
        )
        assert "Verifizierte Antwort" in result
        assert "Konfidenz" in result
        assert "Quellen" in result
        assert "142" in result

    @pytest.mark.asyncio
    async def test_no_web_tools(self, config) -> None:
        """Fehler wenn WebTools nicht verfuegbar."""
        vl = VerifiedWebLookup(config)
        result = await vl.verified_lookup(query="test")
        assert "Fehler" in result or "error" in result.lower()
        assert "WebTools" in result

    @pytest.mark.asyncio
    async def test_no_search_results(self, config, mock_web_tools) -> None:
        """Behandlung leerer Suchergebnisse."""
        mock_web_tools.web_search = AsyncMock(return_value="Keine Ergebnisse gefunden.")
        vl = VerifiedWebLookup(config)
        vl._set_web_tools(mock_web_tools)
        result = await vl.verified_lookup(query="nonexistent topic xyz123")
        assert "Keine Suchergebnisse" in result

    @pytest.mark.asyncio
    async def test_search_exception(self, config, mock_web_tools) -> None:
        """Fehlerbehandlung bei Suchfehler."""
        mock_web_tools.web_search = AsyncMock(side_effect=RuntimeError("Network error"))
        vl = VerifiedWebLookup(config)
        vl._set_web_tools(mock_web_tools)
        result = await vl.verified_lookup(query="test")
        assert "fehlgeschlagen" in result

    @pytest.mark.asyncio
    async def test_num_sources_clamped(self, lookup: VerifiedWebLookup) -> None:
        """num_sources wird auf 2-5 begrenzt."""
        result = await lookup.verified_lookup(query="test", num_sources=1)
        assert "Verifizierte Antwort" in result  # min 2 Quellen
        result = await lookup.verified_lookup(query="test", num_sources=10)
        assert "Verifizierte Antwort" in result  # max 5 Quellen


# ============================================================================
# Test: Parallele Extraktion
# ============================================================================


class TestParallelExtraction:
    """Tests fuer die parallele URL-Extraktion."""

    @pytest.mark.asyncio
    async def test_trafilatura_and_browser_called(
        self, lookup: VerifiedWebLookup, mock_web_tools, mock_browser
    ) -> None:
        """Beide Extraktionsmethoden werden parallel aufgerufen."""
        await lookup.verified_lookup(query="test")
        # Trafilatura sollte fuer alle URLs aufgerufen werden
        assert mock_web_tools.web_fetch.call_count >= 2
        # Browser sollte fuer mindestens 1 URL aufgerufen werden
        assert mock_browser.navigate.call_count >= 1

    @pytest.mark.asyncio
    async def test_browser_failure_graceful(self, lookup: VerifiedWebLookup, mock_browser) -> None:
        """Browser-Fehler fuehrt nicht zum Gesamtausfall."""
        mock_browser.navigate = AsyncMock(side_effect=RuntimeError("Browser crash"))
        result = await lookup.verified_lookup(query="test")
        # Trafilatura-Ergebnisse genuegen
        assert "Verifizierte Antwort" in result

    @pytest.mark.asyncio
    async def test_trafilatura_failure_browser_fallback(
        self, lookup: VerifiedWebLookup, mock_web_tools, mock_browser
    ) -> None:
        """Wenn Trafilatura scheitert, genuegt Browser-Ergebnis."""
        mock_web_tools.web_fetch = AsyncMock(return_value="")
        # Ensure browser is set as v14 (no extract_text)
        del mock_browser.extract_text
        lookup._set_browser_agent(None)
        lookup._set_browser_tool(mock_browser)
        result = await lookup.verified_lookup(query="test")
        assert "Verifizierte Antwort" in result or "142" in result

    @pytest.mark.asyncio
    async def test_no_browser_tool_available(self, config, mock_web_tools, mock_llm_fn) -> None:
        """Funktioniert auch ohne Browser-Tool (nur Trafilatura)."""
        vl = VerifiedWebLookup(config)
        vl._set_web_tools(mock_web_tools)
        vl._set_llm_fn(mock_llm_fn, "test")
        result = await vl.verified_lookup(query="test")
        assert "Verifizierte Antwort" in result


# ============================================================================
# Test: Fakten-Extraktion
# ============================================================================


class TestFactExtraction:
    """Tests fuer die LLM-basierte Faktenextraktion."""

    @pytest.mark.asyncio
    async def test_facts_extracted(self, lookup: VerifiedWebLookup) -> None:
        """Fakten werden korrekt aus LLM-Antwort extrahiert."""
        facts = await lookup._extract_facts(
            text="Cognithor has 142 stars on GitHub.",
            query="How many stars?",
            source_url="https://github.com/test",
        )
        assert len(facts) >= 1
        assert facts[0].value == "142"
        assert facts[0].fact_type == "number"
        assert facts[0].source_url == "https://github.com/test"

    @pytest.mark.asyncio
    async def test_facts_empty_without_llm(self, config) -> None:
        """Ohne LLM werden keine Fakten extrahiert."""
        vl = VerifiedWebLookup(config)
        facts = await vl._extract_facts("some text", "query")
        assert facts == []

    @pytest.mark.asyncio
    async def test_facts_malformed_json(self, config) -> None:
        """Kaputtes JSON von LLM wird graceful behandelt."""

        async def _bad_llm(prompt: str, model: str = "") -> str:
            return "This is not valid JSON at all"

        vl = VerifiedWebLookup(config)
        vl._set_llm_fn(AsyncMock(side_effect=_bad_llm), "test")
        facts = await vl._extract_facts("text", "query")
        assert facts == []

    @pytest.mark.asyncio
    async def test_facts_llm_exception(self, config) -> None:
        """LLM-Exception wird graceful behandelt."""
        vl = VerifiedWebLookup(config)
        vl._set_llm_fn(AsyncMock(side_effect=RuntimeError("LLM down")), "test")
        facts = await vl._extract_facts("text", "query")
        assert facts == []

    @pytest.mark.asyncio
    async def test_facts_with_think_tags(self, config) -> None:
        """qwen3 <think> Tags werden korrekt entfernt."""

        async def _think_llm(prompt: str, model: str = "") -> str:
            return (
                "<think>Hmm let me think about this...</think>\n"
                '{"facts": [{"claim": "test", "value": "42", "type": "number"}]}'
            )

        vl = VerifiedWebLookup(config)
        vl._set_llm_fn(AsyncMock(side_effect=_think_llm), "test")
        facts = await vl._extract_facts("text", "query")
        assert len(facts) == 1
        assert facts[0].value == "42"


# ============================================================================
# Test: Konsens-Algorithmus
# ============================================================================


class TestConsensus:
    """Tests fuer den Konsens-Algorithmus."""

    @pytest.mark.asyncio
    async def test_agreement_with_matching_facts(self, lookup: VerifiedWebLookup) -> None:
        """Uebereinstimmende Fakten ergeben hohen Agreement-Score."""
        facts = [
            ExtractedFact("stars", "142", "number", "url1"),
            ExtractedFact("stars", "142", "number", "url2"),
        ]
        sources = [
            SourceResult("url1", "text1", "trafilatura", True),
            SourceResult("url2", "text2", "browser", True),
        ]
        result = await lookup._build_consensus(
            "how many stars?",
            facts,
            sources,
            "de",
        )
        assert result.agreement >= 0.8
        assert len(result.discrepancies) == 0

    @pytest.mark.asyncio
    async def test_disagreement_detected(self, lookup: VerifiedWebLookup) -> None:
        """Widersprueche werden erkannt."""
        facts = [
            ExtractedFact("stars", "142", "number", "url1"),
            ExtractedFact("stars", "120", "number", "url2"),
        ]
        sources = [
            SourceResult("url1", "text1", "trafilatura", True),
            SourceResult("url2", "text2", "browser", True),
        ]
        result = await lookup._build_consensus(
            "how many stars?",
            facts,
            sources,
            "de",
        )
        assert len(result.discrepancies) >= 1

    @pytest.mark.asyncio
    async def test_empty_facts_and_sources(self, lookup: VerifiedWebLookup) -> None:
        """Leere Fakten und Quellen ergeben niedrige Konfidenz."""
        result = await lookup._build_consensus("query", [], [], "de")
        assert result.confidence == 0.0
        assert "Keine" in result.answer

    @pytest.mark.asyncio
    async def test_consensus_without_llm(self, config) -> None:
        """Ohne LLM wird heuristischer Konsens genutzt."""
        vl = VerifiedWebLookup(config)
        facts = [
            ExtractedFact("stars", "142", "number", "url1"),
        ]
        sources = [SourceResult("url1", "has 142 stars" * 10, "trafilatura", True)]
        result = await vl._build_consensus("query", facts, sources, "de")
        # Fallback: bester Source-Text
        assert result.answer != ""
        assert result.confidence <= 1.0


# ============================================================================
# Test: Formatierung
# ============================================================================


class TestFormatResult:
    """Tests fuer die Ergebnis-Formatierung."""

    def test_high_confidence_format(self) -> None:
        """Hochkonfidentes Ergebnis wird korrekt formatiert."""
        result = VerificationResult(
            answer="Cognithor hat 142 Stars.",
            confidence=0.92,
            facts=[ExtractedFact("stars", "142", "number", "url1")],
            sources=[
                SourceResult("https://github.com/test", "text", "trafilatura", True, 150.0),
                SourceResult("https://github.com/test", "text", "browser", True, 800.0),
            ],
            agreement=0.95,
            duration_ms=1200.0,
        )
        formatted = VerifiedWebLookup._format_result(result, "test")
        assert "92%" in formatted
        assert "142 Stars" in formatted
        assert "Quellen (2 geprueft)" in formatted
        assert "95% Uebereinstimmung" in formatted
        assert "Hohe Uebereinstimmung" in formatted
        assert "1200ms" in formatted

    def test_low_confidence_with_discrepancies(self) -> None:
        """Niedrigkonfidentes Ergebnis mit Diskrepanzen."""
        result = VerificationResult(
            answer="Unklar.",
            confidence=0.3,
            facts=[
                ExtractedFact("stars", "142", "number", "url1"),
                ExtractedFact("stars", "120", "number", "url2"),
            ],
            sources=[
                SourceResult("url1", "t", "trafilatura", True),
            ],
            agreement=0.3,
            discrepancies=["142 vs 120"],
            duration_ms=500.0,
        )
        formatted = VerifiedWebLookup._format_result(result, "test")
        assert "30%" in formatted
        assert "Diskrepanzen" in formatted
        assert "142 vs 120" in formatted
        assert "Geringe Uebereinstimmung" in formatted

    def test_no_facts_format(self) -> None:
        """Ergebnis ohne Fakten (kein Quellenabgleich-Abschnitt)."""
        result = VerificationResult(answer="Keine Fakten.", confidence=0.1)
        formatted = VerifiedWebLookup._format_result(result, "test")
        assert "Quellenabgleich" not in formatted


# ============================================================================
# Test: MCP-Registrierung
# ============================================================================


class TestRegistration:
    """Tests fuer die MCP-Tool-Registrierung."""

    def test_register_returns_instance(self, config) -> None:
        """Registrierung gibt VerifiedWebLookup-Instanz zurueck."""
        mcp = MagicMock()
        result = register_verified_lookup_tools(mcp, config)
        assert isinstance(result, VerifiedWebLookup)

    def test_register_calls_register_builtin_handler(self, config) -> None:
        """register_builtin_handler wird 2x aufgerufen (verified_lookup + deep_research)."""
        mcp = MagicMock()
        register_verified_lookup_tools(mcp, config)
        assert mcp.register_builtin_handler.call_count == 2
        tool_names = [c[1]["tool_name"] for c in mcp.register_builtin_handler.call_args_list]
        assert "verified_web_lookup" in tool_names
        assert "deep_research" in tool_names

    @pytest.mark.asyncio
    async def test_registered_handler_callable(self, config) -> None:
        """Registrierter Handler ist aufrufbar."""
        mcp = MagicMock()
        register_verified_lookup_tools(mcp, config)
        handler = mcp.register_builtin_handler.call_args[1]["handler"]
        # Ohne WebTools gibt es eine Fehlermeldung (kein Crash)
        result = await handler(query="test")
        assert "Fehler" in result or "error" in result.lower() or "WebTools" in result


# ============================================================================
# Test: Datenmodelle
# ============================================================================


class TestDataModels:
    """Tests fuer die Datenmodell-Defaults."""

    def test_extracted_fact_defaults(self) -> None:
        fact = ExtractedFact(claim="test", value="42", fact_type="number")
        assert fact.source_url == ""

    def test_source_result_defaults(self) -> None:
        src = SourceResult(url="https://x.com", text="t", method="traf", success=True)
        assert src.duration_ms == 0.0

    def test_verification_result_defaults(self) -> None:
        res = VerificationResult(answer="a", confidence=0.5)
        assert res.facts == []
        assert res.sources == []
        assert res.agreement == 0.0
        assert res.discrepancies == []
        assert res.duration_ms == 0.0
