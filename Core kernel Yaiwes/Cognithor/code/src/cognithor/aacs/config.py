"""AACS Central Configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

__all__ = ["AACS_CONFIG", "AACSConfig", "AACSFeatureFlags"]


@dataclass(frozen=True)
class AACSConfig:
    """Immutable configuration for AACS."""

    default_token_ttl: int = 300
    max_token_ttl: int = 3600
    min_token_ttl: int = 10
    max_delegation_depth: int = 5
    max_active_tokens_per_agent: int = 50
    nonce_cache_size: int = 10_000
    nonce_expiry_seconds: int = 7200
    trust_score_min: float = 0.0
    trust_score_max: float = 1.0
    trust_score_initial: float = 0.5
    trust_decay_rate: float = 0.01
    memory_tiers: dict[int, str] = field(
        default_factory=lambda: {
            1: "working",
            2: "task",
            3: "session",
            4: "knowledge",
            5: "system_config",
        }
    )
    key_store_path: Path = field(
        default_factory=lambda: Path.home() / ".cognithor" / "keys",
    )

    def validate(self) -> None:
        """Check configuration consistency."""
        assert self.min_token_ttl > 0, "min_token_ttl must be > 0"
        assert self.min_token_ttl <= self.default_token_ttl <= self.max_token_ttl
        assert self.max_delegation_depth >= 1
        assert 0.0 <= self.trust_score_initial <= 1.0


@dataclass
class AACSFeatureFlags:
    """Incremental activation of AACS components."""

    token_validation_enabled: bool = False
    audit_logging_enabled: bool = False
    mcp_gate_enabled: bool = False
    memory_gate_enabled: bool = False
    a2a_trust_boundary_enabled: bool = False
    dynamic_trust_scoring_enabled: bool = False
    enforcement_mode: str = "log_only"  # "log_only" | "enforce"


AACS_CONFIG = AACSConfig()
