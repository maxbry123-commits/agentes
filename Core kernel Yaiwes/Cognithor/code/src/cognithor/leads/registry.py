"""Runtime registry for lead sources.

Sources register themselves during pack load. The registry is held on
``LeadService`` and consumed by REST routes (``/api/v1/leads/sources``),
the CLI, and the Flutter LeadsScreen.

Thread-safety: register/unregister/list are guarded by a lock because
multiple packs may load concurrently during Gateway Phase F init, and
the REST API may poll the registry on an async worker thread.
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cognithor.leads.source import LeadSource


class SourceRegistry:
    def __init__(self) -> None:
        self._sources: dict[str, LeadSource] = {}
        self._lock = threading.Lock()

    def register(self, source: LeadSource) -> None:
        """Add a source. Raises ValueError if source_id is already taken."""
        with self._lock:
            if source.source_id in self._sources:
                raise ValueError(f"LeadSource {source.source_id!r} already registered")
            self._sources[source.source_id] = source

    def unregister(self, source_id: str) -> None:
        """Remove a source. No-op if not registered."""
        with self._lock:
            self._sources.pop(source_id, None)

    def get(self, source_id: str) -> LeadSource | None:
        with self._lock:
            return self._sources.get(source_id)

    def list(self) -> list[LeadSource]:
        """Return a snapshot of all registered sources."""
        with self._lock:
            return list(self._sources.values())

    def __contains__(self, source_id: object) -> bool:
        with self._lock:
            return isinstance(source_id, str) and source_id in self._sources

    def __len__(self) -> int:
        with self._lock:
            return len(self._sources)
