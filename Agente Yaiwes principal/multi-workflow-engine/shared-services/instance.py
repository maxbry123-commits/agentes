"""WordflowInstance + InstanceRegistry — S07/T07

API formal multi-instancia: N WordflowInstance aisladas sin reescribir el kernel.
Persistencia state.json = T08 (InstanceStore / PersistentRegistry).
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import re
import uuid

_VALID_NAME = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,63}$")
_STATUSES = frozenset({"created", "running", "paused", "terminated"})


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class WordflowInstance:
    instance_id: str
    name: str
    created_at: str
    config: Dict[str, Any] = field(default_factory=dict)
    state: Dict[str, Any] = field(default_factory=dict)
    status: str = "created"  # created | running | paused | terminated

    @classmethod
    def create(
        cls,
        name: str,
        config: Optional[Dict[str, Any]] = None,
        *,
        instance_id: Optional[str] = None,
    ) -> "WordflowInstance":
        if not name or not _VALID_NAME.match(name):
            raise ValueError(f"invalid instance name: {name!r}")
        return cls(
            instance_id=instance_id or str(uuid.uuid4())[:8],
            name=name,
            created_at=_utc_now(),
            config=dict(config or {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def set_status(self, status: str) -> None:
        if status not in _STATUSES:
            raise ValueError(f"invalid status: {status!r}")
        self.status = status


class InstanceRegistry:
    """Registro en memoria. Persistencia = T08 PersistentRegistry."""

    def __init__(self) -> None:
        self._instances: Dict[str, WordflowInstance] = {}

    def create(
        self,
        name: str,
        config: Optional[Dict[str, Any]] = None,
        *,
        instance_id: Optional[str] = None,
    ) -> WordflowInstance:
        if instance_id and instance_id in self._instances:
            raise KeyError(f"instance_id already registered: {instance_id}")
        inst = WordflowInstance.create(name, config, instance_id=instance_id)
        if inst.instance_id in self._instances:
            # colisión uuid muy improbable; reintentar una vez
            inst = WordflowInstance.create(name, config)
        self._instances[inst.instance_id] = inst
        return inst

    def get(self, instance_id: str) -> Optional[WordflowInstance]:
        return self._instances.get(instance_id)

    def get_or_raise(self, instance_id: str) -> WordflowInstance:
        inst = self.get(instance_id)
        if inst is None:
            raise KeyError(f"unknown instance_id: {instance_id}")
        return inst

    def list(self) -> List[WordflowInstance]:
        return list(self._instances.values())

    def count(self) -> int:
        return len(self._instances)

    def terminate(self, instance_id: str) -> WordflowInstance:
        inst = self.get_or_raise(instance_id)
        inst.set_status("terminated")
        return inst

    def remove(self, instance_id: str) -> bool:
        """Quita del registry (no borra disco; T08 store aparte)."""
        return self._instances.pop(instance_id, None) is not None

    def has(self, instance_id: str) -> bool:
        return instance_id in self._instances


# singleton default (tests / bootstrap)
default_registry = InstanceRegistry()


if __name__ == "__main__":
    reg = InstanceRegistry()
    a = reg.create("demo_a", {"mode": "v1"})
    b = reg.create("demo_b")
    assert reg.count() == 2
    assert reg.get(a.instance_id) is a
    reg.terminate(a.instance_id)
    assert a.status == "terminated"
    print("ok", reg.count(), [i.instance_id for i in reg.list()])
