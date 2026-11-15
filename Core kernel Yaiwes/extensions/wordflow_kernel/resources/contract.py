"""ResourceContract — HF skill/dataset/space/kernel reference (immutable)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

AcquisitionMode = Literal["remote", "cache", "snapshot", "stream", "file", "auto"]
ResourceKind = Literal["skill", "dataset", "space", "model", "kernel", "file", "mcp"]


@dataclass(frozen=True)
class ResourceContract:
    resource_id: str
    provider: str  # huggingface | github | local
    kind: ResourceKind
    source_uri: str
    revision: str | None = None
    version: str | None = None
    capabilities: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()
    transport: str = "http"  # http | mcp | local
    entrypoint: str | None = None
    local_cache: str | None = None
    license: str | None = None
    requires_auth: bool = False
    trusted: bool = False
    acquisition_mode: AcquisitionMode = "auto"
    allowed_modes: tuple[AcquisitionMode, ...] = ("remote", "snapshot", "file", "stream")
    metadata: tuple[tuple[str, str], ...] = ()  # frozen-friendly key/value pairs

    def pin_key(self) -> str:
        return f"{self.provider}:{self.resource_id}@{self.revision or self.version or 'unpinned'}"
