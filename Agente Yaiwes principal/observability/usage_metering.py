"""
Medicion de uso por instancia, para metricas y facturacion en el modelo
SaaS. Se apoya en el mismo patron append-only que ya usa
extensions/wordflow/state/ledger.py del repo real
(componente wordflow.state.ledger, capacidad append_only_events).

En produccion, UsageMeter debe escribir sobre ese mismo ledger en vez de
una lista en memoria; aqui se entrega la interfaz minima para integrarlo.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class UsageRecord:
    """Un evento de consumo asociado a una instancia concreta."""

    tenant_id: str
    handle: str
    engine_binding: str
    started_at: str
    ended_at: str | None = None
    tokens_used: int = 0
    calls_made: int = 0


class UsageMeter:
    """Ledger append-only de consumo. En este proceso vive en memoria;
    integrar contra wordflow.state.ledger para persistencia real."""

    def __init__(self):
        self._records: list[UsageRecord] = []

    def start(self, tenant_id: str, handle: str, engine_binding: str) -> UsageRecord:
        """Registra el inicio de consumo de una instancia."""
        record = UsageRecord(
            tenant_id=tenant_id,
            handle=handle,
            engine_binding=engine_binding,
            started_at=datetime.now(timezone.utc).isoformat(),
        )
        self._records.append(record)
        return record

    def stop(self, handle: str, tokens_used: int = 0, calls_made: int = 0) -> None:
        """Cierra el registro de consumo de una instancia por su handle."""
        for record in reversed(self._records):
            if record.handle == handle and record.ended_at is None:
                record.ended_at = datetime.now(timezone.utc).isoformat()
                record.tokens_used = tokens_used
                record.calls_made = calls_made
                return
        raise KeyError(f"no hay registro abierto para handle {handle}")

    def usage_for_tenant(self, tenant_id: str) -> list[UsageRecord]:
        """Devuelve todos los registros de un tenant, orden cronologico."""
        return [r for r in self._records if r.tenant_id == tenant_id]
