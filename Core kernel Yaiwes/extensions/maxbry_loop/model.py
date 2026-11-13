"""Task execution adapters.

MockModel: offline deterministic.
GatewayModel: routes llm.complete via IntelligenceGateway (RouterHTTP or Mock).
NEVER call OpenAI/Anthropic APIs directly from the loop.
"""
from __future__ import annotations

from typing import Any, Protocol


class TaskModel(Protocol):
    def execute(self, task, goal) -> dict: ...


class MockModel:
    """Marks tasks done with deterministic evidence (no network)."""

    def execute(self, task, goal):
        return {
            "status": "done",
            "result": f"MOCK completed: {task.title}",
            "evidence": [f"mock:{task.id}"],
        }


class GatewayModel:
    """Production path: Loop → IntelligenceGateway → Router Universal.

    gateway must implement execute(GatewayRequest) -> GatewayResponse
    (wordflow_kernel.gateway.IntelligenceGateway).
    """

    def __init__(self, gateway: Any, capability: str = "llm.complete"):
        self.gateway = gateway
        self.capability = capability

    def generate(self, prompt: str) -> str:
        """T27: text path only via gateway.complete (T26)."""
        complete = getattr(self.gateway, "complete", None)
        if callable(complete):
            return str(complete(str(prompt)))
        from wordflow_kernel.gateway.intelligence import make_request

        req = make_request("t27", self.capability, {"prompt": str(prompt)})
        res = self.gateway.execute(req)
        return str(res.output.get("text", ""))

    def execute(self, task, goal):
        # Late import to keep maxbry_loop usable without kernel on pure mock paths
        from wordflow_kernel.gateway.intelligence import make_request

        messages = [
            {
                "role": "system",
                "content": "Execute the task; return concise result. Wordflow continuous loop.",
            },
            {
                "role": "user",
                "content": (
                    f"GOAL:\n{goal.text}\n\n"
                    f"TASK: {task.title}\n{task.description}\n"
                    f"ACCEPTANCE: {task.acceptance}"
                ),
            },
        ]
        req = make_request(
            task_id=task.id,
            capability=self.capability,
            payload={"messages": messages, "loop": "maxbry_v2"},
            policy={"required_capabilities": ["coding"]},
        )
        res = self.gateway.execute(req)
        if res.status in ("DENY", "ERROR"):
            return {
                "status": "blocked",
                "result": str(res.output),
                "evidence": [f"gateway:{res.status}"],
            }
        text = str(res.output.get("text", res.output))
        status = "done" if res.status in ("OK", "MOCK") else "blocked"
        return {
            "status": status,
            "result": text,
            "evidence": [
                f"gateway:{res.status}",
                f"provider:{res.provider}",
                f"evidence_hash:{res.evidence_hash}",
            ],
        }


def build_model(config: dict, gateway: Any | None = None):
    """Factory: provider mock | gateway."""
    provider = (config.get("model") or {}).get("provider", "mock")
    if provider == "mock" or gateway is None:
        return MockModel()
    if provider in ("gateway", "router"):
        return GatewayModel(gateway)
    # Unknown provider → fail closed to mock for safety (no silent vendor call)
    return MockModel()


if __name__ == "__main__":
    from wordflow_kernel.gateway.intelligence import MockIntelligenceGateway

    gw = MockIntelligenceGateway()
    model = GatewayModel(gw)
    assert model.generate("x") == "GATEWAY_STUB"
    print("ok", model.generate("x"))
