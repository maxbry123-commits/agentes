from dataclasses import dataclass
from typing import Literal

SpaceState = Literal["SLEEP", "STARTING", "RUNNING", "IDLE"]


@dataclass
class SpaceLifecycle:
    space_id: str
    state: SpaceState = "SLEEP"
    ttl_seconds: int = 300  # short by default for agents

    def wake(self) -> None:
        if self.state == "SLEEP":
            self.state = "STARTING"
            # real HF API call would go here
            self.state = "RUNNING"

    def mark_idle(self) -> None:
        if self.state == "RUNNING":
            self.state = "IDLE"

    def sleep_if_idle(self) -> bool:
        """Returns True if transitioned to SLEEP."""
        if self.state == "IDLE":
            self.state = "SLEEP"
            return True
        return False


class LifecycleManager:
    """Gestiona SLEEP/STARTING/RUNNING de los 5 HF (SOURCE: arquitectura final de hf.md)."""

    def __init__(self) -> None:
        self.spaces: dict[str, SpaceLifecycle] = {
            "hf1_control": SpaceLifecycle("hf1_control", ttl_seconds=1800),
            "hf2_backend_core": SpaceLifecycle("hf2_backend_core", ttl_seconds=900),
            "hf3_backend_agents": SpaceLifecycle("hf3_backend_agents", ttl_seconds=300),
            "hf4_frontend_core": SpaceLifecycle("hf4_frontend_core", ttl_seconds=900),
            "hf5_frontend_agents": SpaceLifecycle("hf5_frontend_agents", ttl_seconds=300),
        }

    def ensure_running(self, space_id: str) -> SpaceLifecycle:
        space = self.spaces[space_id]
        if space.state == "SLEEP":
            space.wake()
        return space
