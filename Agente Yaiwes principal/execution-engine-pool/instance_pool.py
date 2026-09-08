"""
Gestor del pool de instancias del motor de programacion.

Responsabilidades:
- Crear instancias con handle unico (paralelismo sin colision).
- Aislar instancias por tenant_id (un tenant nunca ve estado de otro).
- Aplicar un tope de concurrencia por tenant (concurrency_cap).
- Controlar transiciones de estado validas (no saltos arbitrarios).
- Deduplicar por idempotency_key (un reintento no abre dos instancias).

Esta clase NO ejecuta codigo de programacion. Solo administra el ciclo de
vida de las instancias que apuntan al motor compartido
(code-programming-engine). El motor sigue siendo una unica definicion.
"""

from programming_instance import InstanceStatus, ProgrammingInstance


DEFAULT_CONCURRENCY_CAP = 10

_VALID_TRANSITIONS = {
    InstanceStatus.CREATED: (InstanceStatus.RUNNING, InstanceStatus.DESTROYED),
    InstanceStatus.RUNNING: (
        InstanceStatus.PAUSED,
        InstanceStatus.COMPLETED,
        InstanceStatus.FAILED,
    ),
    InstanceStatus.PAUSED: (InstanceStatus.RUNNING, InstanceStatus.DESTROYED),
    InstanceStatus.COMPLETED: (InstanceStatus.DESTROYED,),
    InstanceStatus.FAILED: (InstanceStatus.DESTROYED,),
    InstanceStatus.DESTROYED: (),
}


class ConcurrencyCapExceeded(Exception):
    """Se lanza cuando un tenant intenta abrir mas instancias de las permitidas."""


class InvalidTransition(Exception):
    """Se lanza cuando se pide un cambio de estado no permitido."""


class InstancePoolManager:
    """Administra instancias aisladas por tenant con tope de concurrencia."""

    def __init__(self, concurrency_cap: int = DEFAULT_CONCURRENCY_CAP):
        """concurrency_cap: maximo de instancias activas simultaneas por tenant."""
        self._concurrency_cap = concurrency_cap
        self._by_tenant: dict[str, dict[str, ProgrammingInstance]] = {}
        self._idempotency_index: dict[str, str] = {}

    def _active_count(self, tenant_id: str) -> int:
        """Cuenta instancias no destruidas de un tenant."""
        bucket = self._by_tenant.get(tenant_id, {})
        return sum(
            1 for inst in bucket.values() if inst.status != InstanceStatus.DESTROYED
        )

    def create_instance(self, instance: ProgrammingInstance) -> ProgrammingInstance:
        """Admite una instancia nueva en el pool tras validarla.

        Si idempotency_key ya existe, devuelve la instancia previa en vez
        de crear una duplicada (protege contra reintentos accidentales).
        Fail-closed: si el tenant esta en su tope de concurrencia, o la
        instancia no valida, se rechaza sin excepcion silenciosa.
        """
        instance.validate()
        if instance.idempotency_key:
            prior_handle = self._idempotency_index.get(instance.idempotency_key)
            if prior_handle:
                return self._by_tenant[instance.tenant_id][prior_handle]
        if self._active_count(instance.tenant_id) >= self._concurrency_cap:
            raise ConcurrencyCapExceeded(
                f"tenant {instance.tenant_id} alcanzo el tope de "
                f"{self._concurrency_cap} instancias activas"
            )
        bucket = self._by_tenant.setdefault(instance.tenant_id, {})
        bucket[instance.handle] = instance
        if instance.idempotency_key:
            self._idempotency_index[instance.idempotency_key] = instance.handle
        return instance

    def get_instance(self, tenant_id: str, handle: str) -> ProgrammingInstance | None:
        """Obtiene una instancia; solo dentro del bucket de su propio tenant."""
        return self._by_tenant.get(tenant_id, {}).get(handle)

    def list_active(self, tenant_id: str) -> list[ProgrammingInstance]:
        """Lista instancias no destruidas de un tenant, orden determinista."""
        bucket = self._by_tenant.get(tenant_id, {})
        active = [i for i in bucket.values() if i.status != InstanceStatus.DESTROYED]
        return sorted(active, key=lambda i: i.created_at)

    def transition(
        self, tenant_id: str, handle: str, new_status: InstanceStatus
    ) -> ProgrammingInstance:
        """Cambia el estado de una instancia si la transicion es valida."""
        instance = self.get_instance(tenant_id, handle)
        if instance is None:
            raise KeyError(f"instancia {handle} no encontrada para tenant {tenant_id}")
        allowed = _VALID_TRANSITIONS[instance.status]
        if new_status not in allowed:
            raise InvalidTransition(
                f"{instance.status.value} -> {new_status.value} no permitido"
            )
        instance.status = new_status
        return instance
