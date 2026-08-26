"""Canonical OpenClaw connection adapter.

Copied from Refactoria/G7/new/openclaw_http_gateway.py after validation.
The adapter is intentionally outside the OpenClawEngine implementation so
future wiring does not require editing the engine file.
"""
from Refactoria.G7.new.openclaw_http_gateway import OpenClawHTTPGateway

__all__ = ["OpenClawHTTPGateway"]
