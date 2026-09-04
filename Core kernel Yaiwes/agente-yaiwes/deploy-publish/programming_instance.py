"""
Contrato de datos para una instancia de ejecucion del motor de programacion.

Cada ProgrammingInstance representa UNA ejecucion concreta y aislada del
code-programming-engine: tiene su propio handle, su propio tenant, su propio
slot de API/credencial y su propio estado. El motor (definicion de stages,
gates, quality bar) es una sola pieza compartida; esta clase es lo que se
multiplica para permitir paralelismo real sin duplicar el motor.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4


DEFAULT_PROFILE = "strict_forensic"
FAST_PROFILE = "fast"
VALID_PROFILES = (DEFAULT_PROFILE, FAST_PROFILE)


class InstanceStatus(Enum):
    """Estados posibles de una instancia. Las transiciones validas se
    controlan en InstancePoolManager, no aqui."""

    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    DESTROYED = "destroyed"


@dataclass
class ApiSlot:
    """Credencial y proveedor asignados a una instancia concreta.
    Vive en la instancia, nunca en el motor: por eso varias instancias
    pueden usar APIs distintas sin copiar el motor."""

    provider: str
    credential_ref: str
    endpoint: str | None = None


@dataclass
class ProgrammingInstance:
    """Una ejecucion aislada del motor de programacion de code.

    handle: identificador unico de esta ejecucion concreta (no del workflow).
    tenant_id: cliente/proyecto propietario; nunca se comparte entre tenants.
    mission_id: objetivo/tarea que origino esta instancia.
    profile: nivel de enforcement forense aplicado (strict_forensic|fast).
    engine_binding: que ejecutor real atiende esta instancia (adapter-layer).
    idempotency_key: evita que un reintento cree una segunda instancia para
    la misma tarea si la primera ya quedo registrada (patron durable).
    """

    tenant_id: str
    mission_id: str
    api_slot: ApiSlot
    engine_binding: str
    parent_workflow_id: str
    profile: str = DEFAULT_PROFILE
    handle: str = field(default_factory=lambda: str(uuid4()))
    status: InstanceStatus = InstanceStatus.CREATED
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    budget_slot: int = 1
    idempotency_key: str | None = None

    def validate(self) -> None:
        """Valida invariantes minimas antes de admitir la instancia en el pool.

        Lanza ValueError si algo requerido falta o es invalido. Fail-closed:
        una instancia invalida nunca debe llegar a ejecutar codigo real.
        """
        if not self.tenant_id:
            raise ValueError("tenant_id es obligatorio")
        if not self.mission_id:
            raise ValueError("mission_id es obligatorio")
        if self.profile not in VALID_PROFILES:
            raise ValueError(f"profile invalido: {self.profile}")
        if not self.engine_binding:
            raise ValueError("engine_binding es obligatorio")
