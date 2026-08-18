"""WordflowInstance + Registry — S07/T07
N instancias aisladas sin reescribir el kernel.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional, List, Any
from datetime import datetime, timezone
import uuid

@dataclass
class WordflowInstance:
    instance_id: str
    name: str
    created_at: str
    config: Dict[str, Any] = field(default_factory=dict)
    state: Dict[str, Any] = field(default_factory=dict)
    status: str = "created"  # created | running | paused | terminated

    @classmethod
    def create(cls, name: str, config: Optional[Dict[str, Any]] = None) -> "WordflowInstance":
        return cls(
            instance_id=str(uuid.uuid4())[:8],
            name=name,
            created_at=datetime.now(timezone.utc).isoformat(),
            config=config or {},
        )

class InstanceRegistry:
    """Registro en memoria (persistencia state.json = T08)."""
    def __init__(self):
        self._instances: Dict[str, WordflowInstance] = {}

    def create(self, name: str, config: Optional[Dict[str, Any]] = None) -> WordflowInstance:
        inst = WordflowInstance.create(name, config)
        self._instances[inst.instance_id] = inst
        return inst

    def get(self, instance_id: str) -> Optional[WordflowInstance]:
        return self._instances.get(instance_id)

    def list(self) -> List[WordflowInstance]:
        return list(self._instances.values())

    def count(self) -> int:
        return len(self._instances)

# singleton default
default_registry = InstanceRegistry()
