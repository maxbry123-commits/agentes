"""The one abstraction every shareable thing implements. Export walks
dependencies() into a closure; import calls import_() leaves-first, rewiring
cross-refs through the RemapTable. Secret redaction is centralized in closure +
ziputil so a new entity physically can't forget to scrub itself."""
from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, Protocol, runtime_checkable

from backend.apps.swarm.models import EntityType, Requirement


@dataclass
class DepRef:
    """A local reference one entity holds to another, before bundling."""
    type: EntityType
    local_id: str
    relation: str = ""


class ExportContext(Protocol):
    # Lets an entity rewrite its own cross-refs from local ids to bundle ids.
    def bundle_id_for(self, etype: EntityType, local_id: str) -> str | None: ...


class RemapTable:
    """bundle_id -> fresh local id, filled as import walks entities leaves-first."""

    def __init__(self) -> None:
        self.p_m: dict[str, str] = {}

    def assign(self, bundle_id: str, local_id: str) -> None:
        self.p_m[bundle_id] = local_id

    def local(self, bundle_id: str) -> str | None:
        return self.p_m.get(bundle_id)


@runtime_checkable
class Exportable(Protocol):
    type: ClassVar[EntityType]
    local_id: str
    name: str

    @classmethod
    def load(cls, local_id: str) -> "Exportable | None": ...
    def serialize(self, ctx: ExportContext) -> dict: ...
    def files(self) -> dict[str, bytes]: ...
    def dependencies(self) -> list[DepRef]: ...
    def requirements(self) -> list[Requirement]: ...
    @classmethod
    def import_(cls, payload: dict, files: dict[str, bytes], remap: RemapTable) -> str: ...
