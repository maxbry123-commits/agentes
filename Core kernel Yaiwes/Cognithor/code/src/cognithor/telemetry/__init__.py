"""Jarvis OpenTelemetry v19 -- Distributed Tracing & Metrics.

OTLP-compatible observability framework:
  - Distributed Tracing (W3C Trace Context)
  - Metrics (Counter, Histogram, Gauge)
  - Auto-instrumentation (gateway, graph, A2A, browser, LLM)
  - Sampling (AlwaysOn, Probabilistic, RateBased)
  - Export (OTLP-JSON, Console, InMemory)

Usage:
    from cognithor.telemetry import TelemetryHub

    hub = TelemetryHub(service_name="jarvis")
    with hub.trace_request("POST", "/chat") as span:
        span.set_attribute("user.id", "u123")
        hub.record_request("POST", 200, 42.5)
"""

from cognithor.telemetry.instrumentation import (
    TelemetryHub,
    measure,
    trace,
)
from cognithor.telemetry.metrics import MetricsProvider
from cognithor.telemetry.prometheus import PrometheusExporter
from cognithor.telemetry.tracer import (
    AlwaysOffSampler,
    AlwaysOnSampler,
    BatchProcessor,
    ConsoleProcessor,
    InMemoryProcessor,
    OTLPJsonExporter,
    ProbabilisticSampler,
    RateBasedSampler,
    Sampler,
    SpanContextManager,
    SpanExporter,
    SpanProcessor,
    TracerProvider,
)
from cognithor.telemetry.types import (
    HistogramDataPoint,
    MetricDataPoint,
    MetricDefinition,
    MetricKind,
    Span,
    SpanContext,
    SpanEvent,
    SpanKind,
    SpanLink,
    StatusCode,
    Trace,
    generate_span_id,
    generate_trace_id,
)

__all__ = [
    "AlwaysOffSampler",
    "AlwaysOnSampler",
    "BatchProcessor",
    "ConsoleProcessor",
    "HistogramDataPoint",
    "InMemoryProcessor",
    "MetricDataPoint",
    "MetricDefinition",
    "MetricKind",
    # Metrics
    "MetricsProvider",
    "OTLPJsonExporter",
    "ProbabilisticSampler",
    # Prometheus
    "PrometheusExporter",
    "RateBasedSampler",
    "Sampler",
    "Span",
    "SpanContext",
    "SpanContextManager",
    "SpanEvent",
    "SpanExporter",
    # Types
    "SpanKind",
    "SpanLink",
    "SpanProcessor",
    "StatusCode",
    # Instrumentation
    "TelemetryHub",
    "Trace",
    # Tracer
    "TracerProvider",
    "generate_span_id",
    "generate_trace_id",
    "measure",
    "trace",
]
