# -*- coding: utf-8 -*-
"""T01 support tests: RouterHTTPGateway must fail closed without a router URL."""
from __future__ import annotations

import unittest

from extensions.wordflow_kernel.gateway.intelligence import make_request
from extensions.wordflow_kernel.gateway.router_http import RouterHTTPGateway


class TestRouterHTTPGateway(unittest.TestCase):
    def test_empty_router_url_denies_without_mock_fallback(self) -> None:
        gateway = RouterHTTPGateway(router_url="", allow_mock_fallback=False)
        request = make_request(
            task_id="T01",
            capability="llm.complete",
            payload={"prompt": "health-check"},
            policy={"vendor": "DENY"},
        )
        response = gateway.execute(request)
        self.assertEqual(response.status, "DENY")
        self.assertIsNone(response.provider)
        self.assertEqual(response.output.get("reason"), "ROUTER_URL_empty")


if __name__ == "__main__":
    unittest.main()
