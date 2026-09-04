"""Doble validación fingerprint ↔ contratos · detecta bugs del motor de reglas."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Set

from .fingerprint import Fingerprint


class ClassificationError(Exception):
    """Inconsistencia fingerprint vs set de contratos."""

    def __init__(self, code: str, detail: str):
        self.code = code
        super().__init__(f"{code}: {detail}")


@dataclass(frozen=True)
class ReverseReport:
    ok: bool
    errors: tuple[str, ...]


def reverse_validate(fp: Fingerprint, contracts: Iterable[str]) -> ReverseReport:
    """Si el set trae C47, ¿fingerprint decía secret=true? etc."""
    s: Set[str] = set(contracts)
    errors: List[str] = []

    if "C47" in s and not fp.is_secret:
        errors.append("C47_present_but_secret_false")
    if "C74" in s and not fp.is_secret:
        errors.append("C74_present_but_secret_false")
    if "C33" in s and not (fp.is_network or fp.is_exec or fp.op_type in {
        "NETWORK_CALL", "EXEC_COMMAND", "LLM_CALL", "CROSS_SYSTEM", "EXTERNAL_AGENT"
    }):
        # soft: C33 timeout puede aparecer por modifier band; no hard fail siempre
        pass
    if fp.is_secret and "C47" not in s and fp.is_write:
        errors.append("secret_write_without_C47")

    if errors:
        return ReverseReport(ok=False, errors=tuple(errors))
    return ReverseReport(ok=True, errors=())


def reverse_or_raise(fp: Fingerprint, contracts: Iterable[str]) -> ReverseReport:
    report = reverse_validate(fp, contracts)
    if not report.ok:
        raise ClassificationError("ERROR_DE_CLASIFICACION", "; ".join(report.errors))
    return report
