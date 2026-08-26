"""G6 adapter integration surface.

Reuse the real runtime adapter at extensions/wordflow_kernel/gateway/openclaw_http.py;
no duplicate transport implementation is introduced.
"""
from extensions.wordflow_kernel.gateway.openclaw_http import OpenClawHTTPGateway

__all__ = ["OpenClawHTTPGateway"]
