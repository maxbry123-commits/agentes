"""Cognithor Red-Team-Testing Framework (Deprecation-Shim).

This module exists only for backward compatibility.
All classes and functions now live in ``cognithor.security.red_team``.

A ``DeprecationWarning`` is issued on import.
"""

from __future__ import annotations

import warnings as _warnings

_warnings.warn(
    "cognithor.security.redteam is deprecated -- please use cognithor.security.red_team.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export everything from the canonical module
from cognithor.security.red_team import (
    AttackCategory,
    AttackPayload,
    AttackPlaybook,
    AttackResult,
    AttackSeverity,
    AttackVector,
    CICDGenerator,
    CICDPlatform,
    JailbreakSimulator,
    MemoryPoisonSimulator,
    PenetrationSuite,
    PoisonPayload,
    PromptFuzzer,
    PromptInjectionTester,
    RedTeamFramework,
    RedTeamReport,
    RedTeamRunner,
    ScanPolicy,
    ScanResult,
    SecurityFinding,
    SecurityScanner,
    Severity,
    TestResult,
    VulnerabilityReport,
)

__all__ = [
    "AttackCategory",
    "AttackPayload",
    "AttackPlaybook",
    "AttackResult",
    "AttackSeverity",
    "AttackVector",
    "CICDGenerator",
    "CICDPlatform",
    "JailbreakSimulator",
    "MemoryPoisonSimulator",
    "PenetrationSuite",
    "PoisonPayload",
    "PromptFuzzer",
    "PromptInjectionTester",
    "RedTeamFramework",
    "RedTeamReport",
    "RedTeamRunner",
    "ScanPolicy",
    "ScanResult",
    "SecurityFinding",
    "SecurityScanner",
    "Severity",
    "TestResult",
    "VulnerabilityReport",
]
