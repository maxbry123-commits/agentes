"""Task execution adapters.

MockModel: offline deterministic.
GatewayModel (VL-02): routes llm via IntelligenceGateway — never direct vendor API.
"""
from __future__ import annotations


class MockModel:
    """Marks tasks done with deterministic evidence (no network)."""

    def execute(self, task, goal):
        return {
            "status": "done",
            "result": f"MOCK completed: {task.title}",
            "evidence": [f"mock:{task.id}"],
        }
