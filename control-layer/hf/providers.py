from dataclasses import dataclass, field
from typing import Literal

ProviderName = Literal["local", "groq", "cerebras", "nvidia", "deepseek"]


@dataclass
class ProviderStatus:
    name: ProviderName
    status: Literal["READY", "BUSY", "DOWN", "QUOTA"] = "READY"
    latency_ms: int = 0
    failure_count: int = 0
    cost_weight: int = 1  # higher = more expensive


@dataclass
class ProviderRegistry:
    """Registro de proveedores (SOURCE: arquitectura final de hf.md)."""

    providers: dict[ProviderName, ProviderStatus] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.providers:
            self.providers = {
                "local": ProviderStatus("local", cost_weight=0),
                "groq": ProviderStatus("groq", latency_ms=42),
                "cerebras": ProviderStatus("cerebras", latency_ms=61),
                "nvidia": ProviderStatus("nvidia", latency_ms=110),
                "deepseek": ProviderStatus("deepseek", cost_weight=10),
            }

    def best_available(self, prefer_local: bool = True) -> ProviderName:
        if prefer_local and self.providers["local"].status == "READY":
            return "local"
        candidates = [
            p for p in self.providers.values()
            if p.status == "READY" and p.name != "deepseek"
        ]
        if not candidates:
            return "deepseek"
        return min(candidates, key=lambda p: (p.cost_weight, p.latency_ms)).name

    def mark_failure(self, name: ProviderName) -> None:
        self.providers[name].failure_count += 1
        if self.providers[name].failure_count >= 3:
            self.providers[name].status = "DOWN"
