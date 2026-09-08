"""Deterministic completion-policy evaluation.

The first portable policy is intentionally narrow: every declared acceptance
criterion is required.  Keeping the evaluator in a small, side-effect-free
module lets emitters, runtime adapters, and contract validation share exactly
the same success semantics.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Final, Literal, TypeAlias, cast

CompletionMode: TypeAlias = Literal["all_required", "all_required_verified_evidence"]
DEFAULT_COMPLETION_MODE: Final[CompletionMode] = "all_required"
VERIFIED_EVIDENCE_MODE: Final[CompletionMode] = "all_required_verified_evidence"
SUPPORTED_COMPLETION_MODES: Final[tuple[CompletionMode, ...]] = (
    DEFAULT_COMPLETION_MODE,
    VERIFIED_EVIDENCE_MODE,
)

_RECORD_PREFIX = ".loop/evidence/"


class CompletionPolicyError(ValueError):
    """The requested completion policy is malformed or unsupported."""


def normalize_completion_policy(policy: object | None = None) -> dict[str, CompletionMode]:
    """Return the canonical JSON form of a supported completion policy.

    ``None`` is the compatibility default for terminal@1 records created before
    the policy field existed.  New writers should always persist the returned
    object explicitly.
    """
    if policy is None:
        mode: object = DEFAULT_COMPLETION_MODE
    elif isinstance(policy, str):
        mode = policy
    elif isinstance(policy, Mapping):
        unexpected = sorted(str(key) for key in policy if key != "mode")
        if unexpected:
            raise CompletionPolicyError(
                "completion_policy contains unsupported fields: " + ", ".join(unexpected)
            )
        if "mode" not in policy:
            raise CompletionPolicyError("completion_policy.mode is required")
        mode = policy.get("mode")
    else:
        raise CompletionPolicyError(
            "completion_policy must be null, a mode string, or an object with a mode field"
        )

    if mode not in SUPPORTED_COMPLETION_MODES:
        supported = ", ".join(SUPPORTED_COMPLETION_MODES)
        raise CompletionPolicyError(
            f"unsupported completion policy mode {mode!r}; expected one of: {supported}"
        )
    return {"mode": cast(CompletionMode, mode)}


def criteria_satisfy_completion(
    criteria_met: Mapping[str, object],
    policy: object | None = None,
) -> bool:
    """Return whether a criteria map satisfies the declared policy.

    An empty map never proves completion.  Values must be the boolean singleton
    ``True``; truthy substitutes such as ``1`` are deliberately rejected.
    """
    normalized = normalize_completion_policy(policy)
    if normalized["mode"] in SUPPORTED_COMPLETION_MODES:
        # The criteria half is deliberately shared: the verified-evidence mode raises
        # the EVIDENCE bar, never the criteria bar.
        return bool(criteria_met) and all(value is True for value in criteria_met.values())
    raise AssertionError(f"unhandled completion policy: {normalized!r}")


def policy_requires_verified_evidence(policy: object | None = None) -> bool:
    """True when this policy's evidence bar is hash-verified records, not path strings."""
    return normalize_completion_policy(policy)["mode"] == VERIFIED_EVIDENCE_MODE


def evidence_entry_is_record_shaped(entry: object) -> bool:
    """The structural half of the bar — the most a pure, I/O-free layer can honestly check."""
    return (isinstance(entry, str) and entry.startswith(_RECORD_PREFIX)
            and entry.endswith(".json") and ".." not in entry)


def unmet_required_criteria(criteria_met: Mapping[str, object]) -> tuple[str, ...]:
    """Return stable string identifiers for criteria not proven true."""
    return tuple(sorted(key for key, value in criteria_met.items() if value is not True))
