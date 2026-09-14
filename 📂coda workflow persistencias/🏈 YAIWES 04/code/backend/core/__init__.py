"""
CODA persistence-safe core surface.

The transformed package exposes event/message persistence and reporting helpers.
The upstream pentest orchestrator/decision engine are intentionally not imported
at package import time because they coordinate offensive agents/tools.
"""
from .event_store import EventStore, InteractionEvent, InteractionMessage, InteractionRound
from .interaction_bus import InteractionBus
from .report_generator import ReportGenerator

PERSISTENCE_ONLY_MODE = True
QUARANTINED_CORE_CONTROLLERS = ("Orchestrator", "TestSession", "DecisionEngine")

__all__ = [
    "EventStore",
    "InteractionEvent",
    "InteractionMessage",
    "InteractionRound",
    "InteractionBus",
    "ReportGenerator",
    "PERSISTENCE_ONLY_MODE",
    "QUARANTINED_CORE_CONTROLLERS",
]
