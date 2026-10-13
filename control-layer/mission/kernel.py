from dataclasses import dataclass


@dataclass(frozen=True)
class MissionKernel:
    """Objeto inmutable de misión (SOURCE: SALIDA_1_CAPA_CONTROL_PARTE_2 §29 + §30).

    El agente nunca modifica este objeto.
    Se verifica antes de cada paso.
    """
    mission_id: str
    goal: str
    constraints: tuple[str, ...]
    rules: tuple[str, ...]
    allowed_tools: tuple[str, ...]
    forbidden_tools: tuple[str, ...]
    success_criteria: tuple[str, ...]
    stop_criteria: tuple[str, ...]
    plan_steps: tuple[str, ...] = ()

    def allows(self, tool: str) -> bool:
        if tool in self.forbidden_tools:
            return False
        if self.allowed_tools and tool not in self.allowed_tools:
            return False
        return True
