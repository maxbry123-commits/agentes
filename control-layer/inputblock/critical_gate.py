"""Critical gate · InputBlock CRITICO no arranca sin confirm explícito."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Sequence

from .store import Criticality, InputBlock


class CriticalConfirmRequired(Exception):
    def __init__(self, block_ids: list[str]):
        self.block_ids = block_ids
        super().__init__(f"critical_confirm_required:{','.join(block_ids)}")


@dataclass(frozen=True)
class CriticalGateResult:
    ok: bool
    critical_ids: tuple[str, ...]
    confirmed: bool
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def check_critical_confirm(
    blocks: Sequence[InputBlock],
    *,
    confirmed: bool = False,
    raise_on_block: bool = True,
) -> CriticalGateResult:
    """Si hay CRITICO y confirmed=False → bloquea arranque."""
    crit = tuple(b.block_id for b in blocks if b.criticality == Criticality.CRITICO)
    if not crit:
        return CriticalGateResult(ok=True, critical_ids=(), confirmed=True)
    if confirmed:
        return CriticalGateResult(ok=True, critical_ids=crit, confirmed=True)
    if raise_on_block:
        raise CriticalConfirmRequired(list(crit))
    return CriticalGateResult(
        ok=False,
        critical_ids=crit,
        confirmed=False,
        error="critical_confirm_required",
    )
