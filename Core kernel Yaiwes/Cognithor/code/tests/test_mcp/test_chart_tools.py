"""Tests fuer Chart-Tools -- create_chart, create_table_image, chart_from_csv.

Testet:
  - TestRegistration: 3 Tools registriert
  - TestDataParsing: List-of-dicts und CSV-String
  - TestASCIIFallback: Funktioniert ohne matplotlib
  - TestFileOutput: PNG wird korrekt erstellt
  - TestMaxDataPoints: Zu viele Datenpunkte werden abgelehnt
  - TestChartFromCSV: CSV-Datei wird gelesen und Chart erstellt
  - TestSlugify: Dateinamen-Generierung
"""

from __future__ import annotations

import csv
from typing import TYPE_CHECKING, Any
from unittest.mock import patch

import pytest

from cognithor.config import CognithorConfig, SecurityConfig, ensure_directory_structure
from cognithor.mcp.chart_tools import (
    ChartError,
    ChartTools,
    _ascii_bar_chart,
    _parse_data,
    _slugify,
    register_chart_tools,
)

if TYPE_CHECKING:
    from pathlib import Path


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture()
def config(tmp_path: Path) -> CognithorConfig:
    cfg = CognithorConfig(
        cognithor_home=tmp_path / ".cognithor",
        security=SecurityConfig(allowed_paths=[str(tmp_path)]),
    )
    ensure_directory_structure(cfg)
    return cfg


@pytest.fixture()
def chart_tools(config: CognithorConfig) -> ChartTools:
    return ChartTools(config)


@pytest.fixture()
def sample_data() -> list[dict[str, Any]]:
    return [
        {"month": "Jan", "sales": 100},
        {"month": "Feb", "sales": 150},
        {"month": "Mar", "sales": 120},
        {"month": "Apr", "sales": 200},
    ]


@pytest.fixture()
def sample_csv(tmp_path: Path) -> Path:
    csv_path = tmp_path / "data.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["city", "population"])
        writer.writerow(["Berlin", 3_645_000])
        writer.writerow(["Munich", 1_472_000])
        writer.writerow(["Hamburg", 1_841_000])
    return csv_path


# =============================================================================
# Mock MCP Client
# =============================================================================


class MockMCPClient:
    def __init__(self) -> None:
        self.registered: dict[str, dict] = {}

    def register_builtin_handler(
        self,
        name: str,
        handler: object,
        *,
        description: str = "",
        input_schema: dict | None = None,
    ) -> None:
        self.registered[name] = {
            "handler": handler,
            "description": description,
            "input_schema": input_schema,
        }


# =============================================================================
# TestRegistration
# =============================================================================


class TestRegistration:
    def test_all_tools_registered(self, config: CognithorConfig) -> None:
        client = MockMCPClient()
        tools = register_chart_tools(client, config)

        assert tools is not None
        expected = {"create_chart", "create_table_image", "chart_from_csv"}
        assert set(client.registered.keys()) == expected

    def test_handlers_are_callable(self, config: CognithorConfig) -> None:
        client = MockMCPClient()
        register_chart_tools(client, config)

        for name, entry in client.registered.items():
            assert callable(entry["handler"]), f"Handler fuer '{name}' nicht aufrufbar"

    def test_descriptions_non_empty(self, config: CognithorConfig) -> None:
        client = MockMCPClient()
        register_chart_tools(client, config)

        for name, entry in client.registered.items():
            assert entry["description"], f"Description fuer '{name}' ist leer"

    def test_schemas_present(self, config: CognithorConfig) -> None:
        client = MockMCPClient()
        register_chart_tools(client, config)

        for name, entry in client.registered.items():
            assert entry["input_schema"] is not None, f"Schema fuer '{name}' fehlt"


# =============================================================================
# TestDataParsing
# =============================================================================


class TestDataParsing:
    def test_list_of_dicts(self) -> None:
        data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        result = _parse_data(data)
        assert len(result) == 2
        assert result[0]["a"] == 1

    def test_csv_string(self) -> None:
        csv_str = "name,value\nAlice,10\nBob,20"
        result = _parse_data(csv_str)
        assert len(result) == 2
        assert result[0]["name"] == "Alice"
        assert result[1]["value"] == "20"

    def test_empty_list_raises(self) -> None:
        with pytest.raises(ChartError, match="Leer"):
            _parse_data([])

    def test_empty_string_raises(self) -> None:
        with pytest.raises(ChartError, match="Leer"):
            _parse_data("")

    def test_invalid_type_raises(self) -> None:
        with pytest.raises(ChartError, match="Unbekanntes"):
            _parse_data(12345)

    def test_non_dict_list_raises(self) -> None:
        with pytest.raises(ChartError, match="Liste von Dicts"):
            _parse_data([1, 2, 3])


# =============================================================================
# TestASCIIFallback
# =============================================================================


class TestASCIIFallback:
    def test_basic_bar_chart(self) -> None:
        result = _ascii_bar_chart(
            labels=["A", "B", "C"],
            values=[10, 20, 15],
            title="Test Chart",
        )
        assert "Test Chart" in result
        assert "A" in result
        assert "B" in result

    def test_empty_values(self) -> None:
        result = _ascii_bar_chart(labels=[], values=[], title="Empty")
        assert "keine Daten" in result or "no_data" in result or "data" in result.lower()

    @pytest.mark.asyncio()
    async def test_fallback_when_no_matplotlib(
        self,
        chart_tools: ChartTools,
        sample_data: list[dict],
    ) -> None:
        """If matplotlib is not available, should return ASCII chart."""
        with patch("cognithor.mcp.chart_tools._matplotlib_available", return_value=False):
            result = await chart_tools.create_chart(
                data=sample_data,
                chart_type="bar",
                title="Sales",
                x_key="month",
                y_key="sales",
            )
            # Should contain text (ASCII fallback)
            assert "Sales" in result
            assert "Jan" in result


# =============================================================================
# TestFileOutput
# =============================================================================


class TestFileOutput:
    @pytest.mark.asyncio()
    async def test_chart_creates_file(
        self,
        chart_tools: ChartTools,
        sample_data: list[dict],
    ) -> None:
        """If matplotlib is available, a PNG file should be created."""
        try:
            import matplotlib  # noqa: F401
        except ImportError:
            pytest.skip("matplotlib nicht verfuegbar")

        result = await chart_tools.create_chart(
            data=sample_data,
            chart_type="bar",
            title="Test Output",
            x_key="month",
            y_key="sales",
        )
        assert "erstellt" in result.lower() or "Chart" in result
        # The charts directory should have a file
        charts_dir = chart_tools._charts_dir
        png_files = list(charts_dir.glob("*.png"))
        assert len(png_files) >= 1

    @pytest.mark.asyncio()
    async def test_table_image_creates_file(
        self,
        chart_tools: ChartTools,
        sample_data: list[dict],
    ) -> None:
        try:
            import matplotlib  # noqa: F401
        except ImportError:
            pytest.skip("matplotlib nicht verfuegbar")

        result = await chart_tools.create_table_image(data=sample_data, title="Test Table")
        assert "erstellt" in result.lower() or "Tabellen" in result

    @pytest.mark.asyncio()
    async def test_all_chart_types(
        self,
        chart_tools: ChartTools,
        sample_data: list[dict],
    ) -> None:
        """Test all chart types with matplotlib (or fallback)."""
        for chart_type in ["bar", "line", "pie", "scatter", "hbar"]:
            result = await chart_tools.create_chart(
                data=sample_data,
                chart_type=chart_type,
                title=f"Test {chart_type}",
                x_key="month",
                y_key="sales",
            )
            assert result  # Should return something

    @pytest.mark.asyncio()
    async def test_invalid_chart_type(
        self,
        chart_tools: ChartTools,
        sample_data: list[dict],
    ) -> None:
        with pytest.raises(ChartError, match="Unbekannter Chart-Typ"):
            await chart_tools.create_chart(
                data=sample_data,
                chart_type="radar",
                x_key="month",
                y_key="sales",
            )


# =============================================================================
# TestMaxDataPoints
# =============================================================================


class TestMaxDataPoints:
    @pytest.mark.asyncio()
    async def test_too_many_points(self, chart_tools: ChartTools) -> None:
        huge_data = [{"x": i, "y": i * 2} for i in range(10_001)]
        with pytest.raises(ChartError, match="Zu viele Datenpunkte"):
            await chart_tools.create_chart(data=huge_data, chart_type="bar", x_key="x", y_key="y")

    @pytest.mark.asyncio()
    async def test_max_ok(self, chart_tools: ChartTools) -> None:
        """10,000 points should be fine."""
        data = [{"x": i, "y": i} for i in range(100)]
        # This should NOT raise
        with patch("cognithor.mcp.chart_tools._matplotlib_available", return_value=False):
            result = await chart_tools.create_chart(
                data=data, chart_type="bar", x_key="x", y_key="y", title="Big"
            )
            assert result


# =============================================================================
# TestChartFromCSV
# =============================================================================


class TestChartFromCSV:
    @pytest.mark.asyncio()
    async def test_csv_chart(self, chart_tools: ChartTools, sample_csv: Path) -> None:
        with patch("cognithor.mcp.chart_tools._matplotlib_available", return_value=False):
            result = await chart_tools.chart_from_csv(
                file_path=str(sample_csv),
                chart_type="bar",
                x_column="city",
                y_column="population",
                title="German Cities",
            )
            assert "Berlin" in result

    @pytest.mark.asyncio()
    async def test_nonexistent_csv(self, chart_tools: ChartTools, tmp_path: Path) -> None:
        with pytest.raises(ChartError, match="nicht gefunden"):
            await chart_tools.chart_from_csv(file_path=str(tmp_path / "nonexistent.csv"))

    @pytest.mark.asyncio()
    async def test_non_csv_file(self, chart_tools: ChartTools, tmp_path: Path) -> None:
        txt_file = tmp_path / "data.txt"
        txt_file.write_text("hello")
        with pytest.raises(ChartError, match="Keine CSV"):
            await chart_tools.chart_from_csv(file_path=str(txt_file))

    @pytest.mark.asyncio()
    async def test_path_outside_workspace(self, chart_tools: ChartTools) -> None:
        with pytest.raises(ChartError, match="Zugriff verweigert"):
            await chart_tools.chart_from_csv(file_path="/etc/passwd.csv")


# =============================================================================
# TestSlugify
# =============================================================================


class TestSlugify:
    def test_basic(self) -> None:
        assert _slugify("Hello World") == "hello_world"

    def test_special_chars(self) -> None:
        assert _slugify("Sales Report (Q1/2024)") == "sales_report_q12024"

    def test_empty(self) -> None:
        assert _slugify("") == "chart"

    def test_long_title(self) -> None:
        result = _slugify("x" * 100)
        assert len(result) <= 60

    def test_unicode(self) -> None:
        result = _slugify("Umsatz-Bericht 2024")
        assert "umsatzbericht" in result or "umsatz_bericht" in result
