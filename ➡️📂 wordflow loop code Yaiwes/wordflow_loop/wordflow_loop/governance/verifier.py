from __future__ import annotations

from ..contracts import LayerResult, Status


def check(result: LayerResult) -> list[str]:
    errors: list[str] = []
    if result.status == Status.PASS and not result.has_real_evidence():
        errors.append("pass_without_evidence")
    if result.gaps and result.status == Status.PASS:
        errors.append("pass_with_open_gaps")
    return errors
