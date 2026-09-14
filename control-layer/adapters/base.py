"""Adapter universal 7 funciones.
SOURCE: SALIDA_2_6_IDEAS_PARTE_3 §16 + KER docs.

Cualquier agente (Temporal, OpenClaw, Hermes, Codex…) se conecta
implementando este contrato. Cero lógica de negocio aquí.
"""
from abc import ABC, abstractmethod
from typing import Any


class AgentAdapter(ABC):
    """Contrato mínimo para conectar cualquier agente a la Capa de Control."""

    @abstractmethod
    def execute(self, universal_package: dict[str, Any]) -> dict[str, Any]:
        """Ejecuta y devuelve {stdout, stderr, exit_code, artifacts}."""
        ...

    @abstractmethod
    def health(self) -> dict[str, Any]:
        """{alive, version, latency_ms}."""
        ...

    @abstractmethod
    def capabilities(self) -> list[str]:
        """["npm", "git", "python", "docker", ...]."""
        ...

    @abstractmethod
    def limits(self) -> dict[str, Any]:
        """{max_context, max_runtime_s, ram_mb}."""
        ...

    @abstractmethod
    def contracts_supported(self) -> list[str]:
        """["C03", "C47", "C52", ...]."""
        ...

    @abstractmethod
    def sandbox_profile(self) -> dict[str, Any]:
        """{tipo, límites, aislamiento}."""
        ...

    @abstractmethod
    def evidence_output(self) -> dict[str, Any]:
        """{result, commands_used, files_changed, tests_passed, confidence}."""
        ...
