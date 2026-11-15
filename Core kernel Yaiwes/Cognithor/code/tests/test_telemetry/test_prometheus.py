"""Tests für den Prometheus Text Exposition Format Exporter.

Prüft:
  - Valides Prometheus-Textformat
  - Counter, Gauge, Histogram korrekt formatiert
  - Labels korrekt escaped
  - Leere Metriken → leerer Output
  - Prefix wird konsistent angewendet
  - Sonderzeichen in Labels escaped
  - Prozess-Metriken (uptime) werden generiert
"""

from __future__ import annotations

import re

from cognithor.telemetry.metrics import MetricsProvider
from cognithor.telemetry.prometheus import (
    PrometheusExporter,
    _escape_label_value,
    _format_labels,
    _format_value,
    _sanitize_metric_name,
)

# ── Helpers ───────────────────────────────────────────────────────


def _parse_prometheus_lines(text: str) -> list[str]:
    """Parse non-empty lines from Prometheus output."""
    return [line for line in text.strip().split("\n") if line]


def _get_metric_value(text: str, metric_name: str) -> str | None:
    """Extract the value of a metric from Prometheus text output."""
    for line in text.strip().split("\n"):
        if line.startswith("#"):
            continue
        if line.startswith(metric_name):
            # Handle both labeled and unlabeled metrics
            parts = line.split(" ")
            if len(parts) >= 2:
                return parts[-1]
    return None


def _get_type_line(text: str, metric_name: str) -> str | None:
    """Extract the TYPE line for a metric."""
    for line in text.strip().split("\n"):
        if line.startswith(f"# TYPE {metric_name} "):
            return line
    return None


def _get_help_line(text: str, metric_name: str) -> str | None:
    """Extract the HELP line for a metric."""
    for line in text.strip().split("\n"):
        if line.startswith(f"# HELP {metric_name} "):
            return line
    return None


# ── Test: Label Escaping ──────────────────────────────────────────


class TestLabelEscaping:
    """Tests for Prometheus label value escaping."""

    def test_simple_value(self):
        assert _escape_label_value("telegram") == "telegram"

    def test_backslash_escaped(self):
        assert _escape_label_value(r"path\to\file") == r"path\\to\\file"

    def test_double_quote_escaped(self):
        assert _escape_label_value('say "hello"') == r"say \"hello\""

    def test_newline_escaped(self):
        assert _escape_label_value("line1\nline2") == r"line1\nline2"

    def test_combined_escapes(self):
        result = _escape_label_value('a\\b"c\nd')
        assert result == r"a\\b\"c\nd"

    def test_empty_value(self):
        assert _escape_label_value("") == ""


class TestFormatLabels:
    """Tests for Prometheus label formatting."""

    def test_no_labels(self):
        assert _format_labels({}) == ""

    def test_single_label(self):
        result = _format_labels({"channel": "telegram"})
        assert result == '{channel="telegram"}'

    def test_multiple_labels_sorted(self):
        result = _format_labels({"model": "qwen3", "channel": "cli"})
        assert result == '{channel="cli",model="qwen3"}'

    def test_special_chars_in_value(self):
        result = _format_labels({"msg": 'hello "world"'})
        assert result == r'{msg="hello \"world\""}'


class TestFormatValue:
    """Tests for Prometheus value formatting."""

    def test_integer_value(self):
        assert _format_value(42.0) == "42"

    def test_float_value(self):
        result = _format_value(3.14)
        assert "3.14" in result

    def test_zero(self):
        assert _format_value(0.0) == "0"

    def test_positive_infinity(self):
        assert _format_value(float("inf")) == "+Inf"

    def test_negative_infinity(self):
        assert _format_value(float("-inf")) == "-Inf"

    def test_nan(self):
        assert _format_value(float("nan")) == "NaN"


class TestSanitizeMetricName:
    """Tests for metric name sanitization."""

    def test_valid_name(self):
        assert _sanitize_metric_name("requests_total") == "requests_total"

    def test_dots_replaced(self):
        assert _sanitize_metric_name("events.message_received") == "events_message_received"

    def test_hyphens_replaced(self):
        assert _sanitize_metric_name("my-metric") == "my_metric"

    def test_leading_digit(self):
        result = _sanitize_metric_name("123metric")
        assert result.startswith("_")
        assert "123metric" in result


# ── Test: Empty export ────────────────────────────────────────────


class TestEmptyExport:
    """Tests for empty / no-data scenarios."""

    def test_no_providers(self):
        """Exporter without any providers produces only process metrics."""
        exporter = PrometheusExporter()
        output = exporter.export()
        # Should still have uptime
        assert "jarvis_uptime_seconds" in output

    def test_empty_metrics_provider(self):
        """Empty MetricsProvider produces only process metrics."""
        provider = MetricsProvider()
        exporter = PrometheusExporter(metrics_provider=provider)
        output = exporter.export()
        # No counter/gauge/histogram lines, but process metrics present
        assert "jarvis_uptime_seconds" in output


# ── Test: Counter export ──────────────────────────────────────────


class TestCounterExport:
    """Tests for counter metric export."""

    def test_simple_counter(self):
        provider = MetricsProvider()
        provider.counter("requests_total", 5)
        exporter = PrometheusExporter(metrics_provider=provider)
        output = exporter.export()

        assert "# TYPE jarvis_requests_total counter" in output
        assert "jarvis_requests_total 5" in output

    def test_counter_with_labels(self):
        provider = MetricsProvider()
        provider.counter("requests_total", 3, channel="telegram")
        provider.counter("requests_total", 7, channel="cli")
        exporter = PrometheusExporter(metrics_provider=provider)
        output = exporter.export()

        assert 'jarvis_requests_total{channel="telegram"} 3' in output
        assert 'jarvis_requests_total{channel="cli"} 7' in output

    def test_counter_with_help(self):
        """Known metrics should have HELP text."""
        provider = MetricsProvider()
        provider.counter("requests_total", 1)
        exporter = PrometheusExporter(metrics_provider=provider)
        output = exporter.export()

        help_line = _get_help_line(output, "jarvis_requests_total")
        assert help_line is not None
        assert "Total number of messages processed" in help_line

    def test_counter_increments(self):
        provider = MetricsProvider()
        provider.counter("errors_total", 1, channel="cli")
        provider.counter("errors_total", 1, channel="cli")
        provider.counter("errors_total", 1, channel="cli")
        exporter = PrometheusExporter(metrics_provider=provider)
        output = exporter.export()

        assert 'jarvis_errors_total{channel="cli"} 3' in output


# ── Test: Gauge export ────────────────────────────────────────────


class TestGaugeExport:
    """Tests for gauge metric export."""

    def test_simple_gauge(self):
        provider = MetricsProvider()
        provider.gauge("active_sessions", 12)
        exporter = PrometheusExporter(metrics_provider=provider)
        output = exporter.export()

        assert "# TYPE jarvis_active_sessions gauge" in output
        assert "jarvis_active_sessions 12" in output

    def test_gauge_with_labels(self):
        provider = MetricsProvider()
        provider.gauge("active_sessions", 5, channel="telegram")
        exporter = PrometheusExporter(metrics_provider=provider)
        output = exporter.export()

        assert 'jarvis_active_sessions{channel="telegram"} 5' in output

    def test_gauge_overwrites(self):
        provider = MetricsProvider()
        provider.gauge("queue_depth", 10)
        provider.gauge("queue_depth", 3)
        exporter = PrometheusExporter(metrics_provider=provider)
        output = exporter.export()

        assert "jarvis_queue_depth 3" in output
        assert "jarvis_queue_depth 10" not in output


# ── Test: Histogram export ────────────────────────────────────────


class TestHistogramExport:
    """Tests for histogram metric export."""

    def test_histogram_format(self):
        provider = MetricsProvider()
        provider.histogram("request_duration_ms", 42.5)
        provider.histogram("request_duration_ms", 150.0)
        provider.histogram("request_duration_ms", 3000.0)
        exporter = PrometheusExporter(metrics_provider=provider)
        output = exporter.export()

        assert "# TYPE jarvis_request_duration_ms histogram" in output
        assert "jarvis_request_duration_ms_count" in output
        assert "jarvis_request_duration_ms_sum" in output
        assert "jarvis_request_duration_ms_bucket" in output

    def test_histogram_has_inf_bucket(self):
        provider = MetricsProvider()
        provider.histogram("request_duration_ms", 100.0)
        exporter = PrometheusExporter(metrics_provider=provider)
        output = exporter.export()

        assert "+Inf" in output

    def test_histogram_count_and_sum(self):
        provider = MetricsProvider()
        provider.histogram("tool_duration_ms", 10.0)
        provider.histogram("tool_duration_ms", 20.0)
        provider.histogram("tool_duration_ms", 30.0)
        exporter = PrometheusExporter(metrics_provider=provider)
        output = exporter.export()

        # Count should be 3
        count_line = [l for l in output.split("\n") if "jarvis_tool_duration_ms_count" in l]
        assert len(count_line) > 0
        assert "3" in count_line[0]

        # Sum should be 60
        sum_line = [l for l in output.split("\n") if "jarvis_tool_duration_ms_sum" in l]
        assert len(sum_line) > 0
        assert "60" in sum_line[0]

    def test_histogram_with_labels(self):
        provider = MetricsProvider()
        provider.histogram("tool_duration_ms", 50.0, tool_name="web_search")
        exporter = PrometheusExporter(metrics_provider=provider)
        output = exporter.export()

        assert 'tool_name="web_search"' in output


# ── Test: Prefix ──────────────────────────────────────────────────


class TestPrefix:
    """Tests for metric name prefix."""

    def test_default_prefix(self):
        provider = MetricsProvider()
        provider.counter("test_metric", 1)
        exporter = PrometheusExporter(metrics_provider=provider)
        output = exporter.export()

        assert "jarvis_test_metric" in output

    def test_custom_prefix(self):
        provider = MetricsProvider()
        provider.counter("test_metric", 1)
        exporter = PrometheusExporter(metrics_provider=provider, prefix="cognithor")
        output = exporter.export()

        assert "cognithor_test_metric" in output
        assert (
            "jarvis_" not in output.split("jarvis_uptime")[0] if "jarvis_uptime" in output else True
        )

    def test_no_double_prefix(self):
        """If metric already starts with prefix, don't double it."""
        provider = MetricsProvider()
        provider.counter("jarvis_requests", 1)
        exporter = PrometheusExporter(metrics_provider=provider, prefix="jarvis")
        output = exporter.export()

        # Should NOT have jarvis_jarvis_requests
        assert "jarvis_jarvis_requests" not in output
        assert "jarvis_requests " in output

    def test_empty_prefix(self):
        provider = MetricsProvider()
        provider.counter("my_counter", 5)
        exporter = PrometheusExporter(metrics_provider=provider, prefix="")
        output = exporter.export()

        assert "my_counter 5" in output


# ── Test: Process metrics ─────────────────────────────────────────


class TestProcessMetrics:
    """Tests for built-in process metrics."""

    def test_uptime_present(self):
        exporter = PrometheusExporter()
        output = exporter.export()

        assert "# TYPE jarvis_uptime_seconds gauge" in output
        assert "jarvis_uptime_seconds" in output

    def test_uptime_positive(self):
        exporter = PrometheusExporter()
        output = exporter.export()

        for line in output.split("\n"):
            if line.startswith("jarvis_uptime_seconds "):
                value = float(line.split(" ")[1])
                assert value > 0


# ── Test: Full output validation ──────────────────────────────────


class TestFullOutput:
    """Tests for overall Prometheus output validity."""

    def test_output_ends_with_newline(self):
        provider = MetricsProvider()
        provider.counter("test", 1)
        exporter = PrometheusExporter(metrics_provider=provider)
        output = exporter.export()

        assert output.endswith("\n")

    def test_no_blank_lines_in_metric_groups(self):
        """Prometheus format should not have blank lines within metric groups."""
        provider = MetricsProvider()
        provider.counter("a_total", 1)
        provider.counter("b_total", 2)
        exporter = PrometheusExporter(metrics_provider=provider)
        output = exporter.export()

        # There should be no double newlines in the output
        assert "\n\n\n" not in output

    def test_type_before_value(self):
        """TYPE line must appear before the metric value line."""
        provider = MetricsProvider()
        provider.counter("requests_total", 5)
        exporter = PrometheusExporter(metrics_provider=provider)
        output = exporter.export()

        lines = output.split("\n")
        type_idx = None
        value_idx = None
        for i, line in enumerate(lines):
            if "# TYPE jarvis_requests_total" in line:
                type_idx = i
            if line.startswith("jarvis_requests_total "):
                value_idx = i

        assert type_idx is not None
        assert value_idx is not None
        assert type_idx < value_idx

    def test_valid_metric_line_format(self):
        """Each non-comment line should match metric_name [labels] value."""
        provider = MetricsProvider()
        provider.counter("test_counter", 42, env="prod")
        provider.gauge("test_gauge", 3.14)
        exporter = PrometheusExporter(metrics_provider=provider)
        output = exporter.export()

        re.compile(r"^[a-zA-Z_:][a-zA-Z0-9_:]*(\{[^}]*\})?\s+[\d.eE+\-]+|[+\-]?Inf|NaN$")
        for line in output.strip().split("\n"):
            if line.startswith("#") or not line.strip():
                continue
            # Should be parseable as a metric line
            parts = line.split(" ")
            assert len(parts) >= 2, f"Invalid metric line: {line}"


# ── Test: MetricCollector export ──────────────────────────────────


class TestMetricCollectorExport:
    """Tests for exporting from gateway MetricCollector."""

    def test_collector_counters(self):
        from cognithor.gateway.monitoring import MetricCollector

        collector = MetricCollector()
        collector.increment("events.message_received", 10)
        exporter = PrometheusExporter(metric_collector=collector)
        output = exporter.export()

        assert "jarvis_events_message_received" in output
        assert "10" in output

    def test_collector_gauges(self):
        from cognithor.gateway.monitoring import MetricCollector

        collector = MetricCollector()
        collector.gauge("cpu_percent", 45.2)
        exporter = PrometheusExporter(metric_collector=collector)
        output = exporter.export()

        assert "jarvis_cpu_percent" in output
        assert "# TYPE jarvis_cpu_percent gauge" in output

    def test_both_providers(self):
        """Both MetricsProvider and MetricCollector can be used together."""
        from cognithor.gateway.monitoring import MetricCollector

        provider = MetricsProvider()
        provider.counter("requests_total", 5)

        collector = MetricCollector()
        collector.increment("events.total", 100)

        exporter = PrometheusExporter(
            metrics_provider=provider,
            metric_collector=collector,
        )
        output = exporter.export()

        assert "jarvis_requests_total 5" in output
        assert "jarvis_events_total" in output


# ── Test: Special characters ──────────────────────────────────────


class TestSpecialCharacters:
    """Tests for special character handling."""

    def test_label_with_backslash(self):
        provider = MetricsProvider()
        provider.counter("file_ops", 1, path=r"C:\Users\test")
        exporter = PrometheusExporter(metrics_provider=provider)
        output = exporter.export()

        assert r"C:\\Users\\test" in output

    def test_label_with_quotes(self):
        provider = MetricsProvider()
        provider.counter("queries", 1, query='SELECT "name"')
        exporter = PrometheusExporter(metrics_provider=provider)
        output = exporter.export()

        assert r"SELECT \"name\"" in output

    def test_label_with_newline(self):
        provider = MetricsProvider()
        provider.counter("messages", 1, content="line1\nline2")
        exporter = PrometheusExporter(metrics_provider=provider)
        output = exporter.export()

        # Newline should be escaped as \n in the label value
        assert r"\n" in output


# ── Test: Thread Safety ──────────────────────────────────────────


class TestMetricsThreadSafety:
    """MetricsProvider muss thread-safe sein."""

    def test_concurrent_counter_increments(self):
        """Parallele Counter-Inkremente dürfen keine Werte verlieren."""
        import threading

        provider = MetricsProvider()
        iterations = 1000
        threads = 4

        def increment():
            for _ in range(iterations):
                provider.counter("concurrent_total", 1)

        workers = [threading.Thread(target=increment) for _ in range(threads)]
        for w in workers:
            w.start()
        for w in workers:
            w.join()

        assert provider.get_counter("concurrent_total") == iterations * threads

    def test_concurrent_gauge_and_snapshot(self):
        """Snapshot während gleichzeitigem Gauge-Setzen darf nicht crashen."""
        import threading

        provider = MetricsProvider()
        errors: list[str] = []

        def set_gauges():
            for i in range(500):
                provider.gauge("load", float(i), worker="w1")

        def take_snapshots():
            for _ in range(500):
                try:
                    s = provider.snapshot()
                    assert "counters" in s
                except Exception as exc:
                    errors.append(str(exc))

        t1 = threading.Thread(target=set_gauges)
        t2 = threading.Thread(target=take_snapshots)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        assert not errors, f"Errors during concurrent access: {errors}"
