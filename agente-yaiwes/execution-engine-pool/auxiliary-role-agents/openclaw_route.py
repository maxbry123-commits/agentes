"""Wordflow → OpenClaw cable.

The existing OpenClawEngine remains unchanged. This route composes the
registered engine with the validated OpenClawHTTPGateway adapter.
"""
from __future__ import annotations

from wordflow_kernel.engines.openclaw_stub import OpenClawEngine
from wordflow_kernel.engines.port import EngineRequest, EngineResult
from agente_yaiwes.execution_engine_pool.adapter_layer.openclaw_http_gateway import OpenClawHTTPGateway


def reason_with_openclaw(request: EngineRequest) -> EngineResult:
    """Execute the existing OpenClawEngine through the OpenClaw HTTP gateway."""
    return OpenClawEngine().reason(request, OpenClawHTTPGateway())
