"""TemporalAdapter — ejemplo concreto del AgentAdapter.
SOURCE: adapters/base.py + Temporal CLI ya descargado.
"""
from typing import Any
from .base import AgentAdapter


class TemporalAdapter(AgentAdapter):
    def execute(self, universal_package: dict[str, Any]) -> dict[str, Any]:
        # Stub: en producción llamaría al binary temporal
        return {
            "stdout": "temporal workflow started",
            "stderr": "",
            "exit_code": 0,
            "artifacts": [],
        }

    def health(self) -> dict[str, Any]:
        return {"alive": True, "version": "1.7.3", "latency_ms": 5}

    def capabilities(self) -> list[str]:
        return ["workflow", "durable_execution", "retry", "signals"]

    def limits(self) -> dict[str, Any]:
        return {"max_context": 0, "max_runtime_s": 86400, "ram_mb": 256}

    def contracts_supported(self) -> list[str]:
        return ["C03", "C28"]

    def sandbox_profile(self) -> dict[str, Any]:
        return {"tipo": "none", "limites": {}, "aislamiento": "process"}

    def evidence_output(self) -> dict[str, Any]:
        return {
            "result": "ok",
            "commands_used": [],
            "files_changed": [],
            "tests_passed": [],
            "confidence": 100,
        }
