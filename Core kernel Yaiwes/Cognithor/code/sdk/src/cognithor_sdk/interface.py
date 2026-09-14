"""Pack interfaces — stable contract between packs and Cognithor Core."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z\.-]+)?$")
_NS_PACK_RE = re.compile(r"^[a-z][a-z0-9-]{0,63}$")
_SHA256_RE = re.compile(r"^[a-f0-9]{64}$")


class Publisher(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    display_name: str
    website: str | None = None
    contact_email: str | None = None
    payout_provider: str | None = None


class RevenueShare(BaseModel):
    model_config = ConfigDict(extra="forbid")
    creator: int = Field(default=70, ge=0, le=100)
    platform: int = Field(default=30, ge=0, le=100)

    @model_validator(mode="after")
    def _sum_to_100(self) -> RevenueShare:
        if self.creator + self.platform != 100:
            raise ValueError("creator + platform must sum to 100")
        return self


class PricingTier(BaseModel):
    model_config = ConfigDict(extra="forbid")
    list_price: int = Field(ge=0)
    launch_price: int = Field(ge=0)
    post_launch_price: int = Field(ge=0)
    launch_cap: int = Field(ge=1)
    currency: str = "USD"


class PackManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: int = 1
    namespace: str
    pack_id: str
    version: str
    display_name: str
    description: str
    license: str
    min_cognithor_version: str
    max_cognithor_version: str | None = None
    entrypoint: str = "pack.py"
    eula_sha256: str
    publisher: Publisher
    revenue_share: RevenueShare = Field(default_factory=RevenueShare)
    lead_sources: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    checkout_url: str | None = None
    commercial_checkout_url: str | None = None
    pricing: dict[str, PricingTier] = Field(default_factory=dict)

    @field_validator("namespace")
    @classmethod
    def _validate_namespace(cls, v: str) -> str:
        if "/" in v or not _NS_PACK_RE.match(v):
            raise ValueError(f"namespace must match {_NS_PACK_RE.pattern!r}")
        return v

    @field_validator("pack_id")
    @classmethod
    def _validate_pack_id(cls, v: str) -> str:
        if "/" in v or not _NS_PACK_RE.match(v):
            raise ValueError(f"pack_id must match {_NS_PACK_RE.pattern!r}")
        return v

    @field_validator("version")
    @classmethod
    def _validate_version(cls, v: str) -> str:
        if not _SEMVER_RE.match(v):
            raise ValueError(f"version must be semver X.Y.Z, got {v!r}")
        return v

    @field_validator("eula_sha256")
    @classmethod
    def _validate_eula_hash(cls, v: str) -> str:
        if not _SHA256_RE.match(v):
            raise ValueError("eula_sha256 must be 64 lowercase hex chars")
        return v

    @property
    def qualified_id(self) -> str:
        return f"{self.namespace}/{self.pack_id}"


class PackContext(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    gateway: Any = None
    config: Any = None
    mcp_client: Any = None
    leads: Any = None


class AgentPack(ABC):
    def __init__(self, manifest: PackManifest) -> None:
        self.manifest = manifest

    @abstractmethod
    def register(self, context: PackContext) -> None: ...

    def unregister(self, context: PackContext) -> None:
        pass
