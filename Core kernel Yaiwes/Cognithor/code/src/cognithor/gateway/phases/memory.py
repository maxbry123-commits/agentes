"""Memory phase: Memory manager, hygiene, integrity, decision explainer.

Attributes handled:
  _memory_manager, _memory_hygiene, _integrity_checker, _decision_explainer
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from cognithor.utils.logging import get_logger

if TYPE_CHECKING:
    from cognithor.gateway.phases import PhaseResult

log = get_logger(__name__)


def declare_memory_attrs(config: Any) -> PhaseResult:
    """Return default values for memory attributes.

    Eagerly constructs instances where possible (matching original __init__).
    """
    result: PhaseResult = {
        "memory_manager": None,
        "memory_hygiene": None,
        "integrity_checker": None,
        "decision_explainer": None,
    }

    # Phase 12: Memory-Hygiene-Engine
    try:
        from cognithor.memory.hygiene import MemoryHygieneEngine

        result["memory_hygiene"] = MemoryHygieneEngine()
    except Exception:
        log.debug("memory_hygiene_init_skipped", exc_info=True)

    # Phase 26: Memory-Integrity
    try:
        from cognithor.memory.integrity import DecisionExplainer, IntegrityChecker

        result["integrity_checker"] = IntegrityChecker()
        result["decision_explainer"] = DecisionExplainer()
    except Exception:
        log.debug("memory_integrity_init_skipped", exc_info=True)

    return result


async def init_memory(config: Any, audit_logger: Any) -> PhaseResult:
    """Initialize memory manager.

    Args:
        config: CognithorConfig instance.
        audit_logger: AuditLogger for memory auditing.

    Returns:
        PhaseResult with memory_manager.
    """
    from cognithor.memory.manager import MemoryManager

    result: PhaseResult = {}

    memory_manager = MemoryManager(config, audit_logger=audit_logger)
    try:
        mem_stats = await memory_manager.initialize()
        log.info(
            "memory_initialized",
            chunks=mem_stats.get("chunks", 0),
            entities=mem_stats.get("entities", 0),
            embedding_cache=mem_stats.get("embedding_cache_size", 0),
        )
    except Exception:
        log.error("memory_initialize_failed", exc_info=True)
        mem_stats = {}
    result["memory_manager"] = memory_manager

    return result
