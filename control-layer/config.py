"""Config flags · único lugar de feature flags · sin forks de código.

WORDFLOW / EXTENSION / DURABLE se leen de defaults + env + override dict.
"""
from __future__ import annotations

import os
from dataclasses import asdict, dataclass, field
from typing import Any, Mapping


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_str(name: str, default: str) -> str:
    return os.environ.get(name, default)


@dataclass
class ControlConfig:
    # caras duales
    enable_wordflow: bool = True
    enable_extension: bool = True
    enable_durable: bool = True

    # runtime
    state_dir: str = "./wordflow_state"
    default_ttl_sec: int = 86400 * 7
    strict_reverse: bool = False
    default_mount_mode: str = "dual"  # wordflow | extension | dual

    # sheriff / council
    enable_shadow: bool = True
    council_min_level: str = "MID"  # LOW nunca

    # seguridad
    block_on_quarantine: bool = True

    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def mount_mode_for(self, preferred: str | None = None) -> str:
        if preferred in ("wordflow", "extension", "dual"):
            return preferred
        if self.enable_wordflow and self.enable_extension:
            return "dual"
        if self.enable_extension and not self.enable_wordflow:
            return "extension"
        return "wordflow"


def load_config(overrides: Mapping[str, Any] | None = None) -> ControlConfig:
    """Defaults → env → overrides (gana el último)."""
    cfg = ControlConfig(
        enable_wordflow=_env_bool("WORDFLOW", True),
        enable_extension=_env_bool("EXTENSION", True),
        enable_durable=_env_bool("DURABLE", True),
        state_dir=_env_str("WORDFLOW_STATE_DIR", "./wordflow_state"),
        default_ttl_sec=int(os.environ.get("INPUT_TTL_SEC", str(86400 * 7))),
        strict_reverse=_env_bool("STRICT_REVERSE", False),
        default_mount_mode=_env_str("MOUNT_MODE", "dual"),
        enable_shadow=_env_bool("ENABLE_SHADOW", True),
        council_min_level=_env_str("COUNCIL_MIN_LEVEL", "MID"),
        block_on_quarantine=_env_bool("BLOCK_ON_QUARANTINE", True),
    )
    if overrides:
        for k, v in overrides.items():
            if hasattr(cfg, k) and k != "extra":
                setattr(cfg, k, v)
            else:
                cfg.extra[k] = v
    # normaliza mount mode
    if cfg.default_mount_mode not in ("wordflow", "extension", "dual"):
        cfg.default_mount_mode = cfg.mount_mode_for()
    return cfg


# singleton lazy
_CFG: ControlConfig | None = None


def get_config() -> ControlConfig:
    global _CFG
    if _CFG is None:
        _CFG = load_config()
    return _CFG


def reset_config(overrides: Mapping[str, Any] | None = None) -> ControlConfig:
    global _CFG
    _CFG = load_config(overrides)
    return _CFG
