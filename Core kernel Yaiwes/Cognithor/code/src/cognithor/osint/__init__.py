"""Human Investigation Module (HIM) — OSINT research and trust scoring."""

from cognithor.osint.him_agent import HIMAgent
from cognithor.osint.models import (
    ClaimResult,
    ClaimType,
    Evidence,
    Finding,
    GDPRScope,
    GDPRViolationError,
    HIMReport,
    HIMRequest,
    TrustScore,
    VerificationStatus,
)

__all__ = [
    "ClaimResult",
    "ClaimType",
    "Evidence",
    "Finding",
    "GDPRScope",
    "GDPRViolationError",
    "HIMAgent",
    "HIMReport",
    "HIMRequest",
    "TrustScore",
    "VerificationStatus",
]
