from dataclasses import dataclass
from typing import Literal

Target = Literal["backend_core", "backend_agents", "frontend_core", "frontend_agents"]
Model = Literal["seed-coder", "nemotron", "nanbeige", "gemma", "deepseek"]
Provider = Literal["local", "groq", "cerebras", "nvidia", "deepseek"]


@dataclass(frozen=True)
class RouterDecision:
    target: Target
    model: Model
    provider: Provider
    parallel: bool
    wake: bool
    reason: str


class DecisionEngine:
    """Decision Engine del Router (SOURCE: arquitectura final de hf.md).

    No ejecuta. Solo clasifica y decide target/model/provider.
    """

    def decide(
        self,
        task_type: str,
        complexity: str,
        domain: Literal["backend", "frontend"],
        needs_parallel: bool = False,
        repair_count: int = 0,
    ) -> RouterDecision:
        # DeepSeek solo después de fallos locales
        if repair_count >= 2:
            return RouterDecision(
                target=f"{domain}_agents",
                model="deepseek",
                provider="deepseek",
                parallel=False,
                wake=True,
                reason="local models failed twice → DeepSeek last resort",
            )

        # Modelo por tipo de tarea
        if task_type in ("architecture", "planning", "review"):
            model: Model = "nemotron"
        elif task_type in ("light", "classify", "verify"):
            model = "gemma"
        else:
            model = "seed-coder"

        # Target y wake
        if needs_parallel:
            target: Target = f"{domain}_agents"
            wake = True
        else:
            target = f"{domain}_core"
            wake = False

        return RouterDecision(
            target=target,
            model=model,
            provider="local",
            parallel=needs_parallel,
            wake=wake,
            reason=f"{task_type}/{complexity} → {model} on {target}",
        )
