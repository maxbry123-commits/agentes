"""Unwrap (possibly nested) exception groups to the first plain Exception.
anyio task groups deliver a concurrent CLI crash + cancellation as a
BaseExceptionGroup whose str() names the group, not the cause; classifying the
group instead of the member turns a retryable 429 into a raw error card."""
from typing import Optional


def first_real_exception(exc: BaseException) -> Optional[Exception]:
    if isinstance(exc, BaseExceptionGroup):
        for p_sub in exc.exceptions:
            p_found = first_real_exception(p_sub)
            if p_found is not None:
                return p_found
        return None
    return exc if isinstance(exc, Exception) else None
