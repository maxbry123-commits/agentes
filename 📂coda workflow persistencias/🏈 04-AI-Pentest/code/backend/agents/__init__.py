"""
CODA persistence-only agent surface for transformed AI_Pentest.

The upstream reconnaissance, vulnerability-analysis and exploitation agents are
not imported from this package in the transformed working tree. Their original
source remains recoverable from `_archives` for provenance and architecture
study, but CODA runtime does not expose or execute them.
"""
from .base import (
    BaseAgent,
    AgentStatus,
    AgentResult,
    Task,
    TaskPriority,
    SequentialAgent,
    ParallelAgent,
)
from .report_agent import ReportAgent
from .coordinator_agent import CoordinatorAgent

PERSISTENCE_ONLY_MODE = True
QUARANTINED_AGENT_ROLES = (
    "ReconAgent",
    "VulnAgent",
    "ExploitAgent",
)

__all__ = [
    "BaseAgent",
    "AgentStatus",
    "AgentResult",
    "Task",
    "TaskPriority",
    "SequentialAgent",
    "ParallelAgent",
    "ReportAgent",
    "CoordinatorAgent",
    "PERSISTENCE_ONLY_MODE",
    "QUARANTINED_AGENT_ROLES",
]
