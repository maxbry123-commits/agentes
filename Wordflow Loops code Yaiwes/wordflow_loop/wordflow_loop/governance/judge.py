from __future__ import annotations

from ..contracts import LayerResult, Status


def check(result: LayerResult) -> list[str]:
    """Binary judge: no PASS while claims are unsupported or gaps remain."""
    errors: list[str] = []
    if result.status == Status.PASS and result.gaps:
        errors.append("open_gaps")
    if result.status == Status.PASS and not result.evidence:
        errors.append("unsupported_claim")
    return errors
