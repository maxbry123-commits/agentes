"""Generic multi-source lead engine SDK.

This package is the source-agnostic replacement for the Reddit-specific
``cognithor.social`` module. Lead sources (Reddit, Hacker News, Discord,
RSS, etc.) live in agent packs and register themselves with the
``SourceRegistry`` at pack load time.

Public API (re-exported here for convenience):

- ``Lead``, ``LeadStatus``, ``LeadStats``, ``ScanResult`` — data models
- ``LeadStore`` — SQLCipher-backed persistence
- ``LeadSource`` — abstract base for source implementations
- ``SourceRegistry`` — runtime registry of registered sources
- ``LeadService`` — orchestrator (scan, store, list, draft, post)
"""

from __future__ import annotations

from cognithor.leads.models import Lead, LeadStats, LeadStatus, ScanResult
from cognithor.leads.registry import SourceRegistry
from cognithor.leads.service import LeadService
from cognithor.leads.source import LeadSource
from cognithor.leads.store import LeadStore

__all__ = [
    "Lead",
    "LeadService",
    "LeadSource",
    "LeadStats",
    "LeadStatus",
    "LeadStore",
    "ScanResult",
    "SourceRegistry",
]
