"""Trust-Resolver fuer Workspace-Vertrauen.

Bestimmt ob ein Pfad vertrauenswuerdig ist basierend auf:
  - Allowlist (auto_trust)
  - Denylist (deny)
  - Default-Policy (require_approval)

Integriert sich in den Gatekeeper fuer File-Operationen und Computer Use.

Bibel-Referenz: Phase 2, Verbesserung 4.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

from cognithor.utils.logging import get_logger

log = get_logger(__name__)


# Trust-Prompt-Erkennung in Tool-Output
TRUST_PROMPT_CUES = [
    "do you trust the files in this folder",
    "trust this folder",
    "allow and continue",
    "yes, proceed",
    "vertrauen sie diesem ordner",
]


@dataclass
class TrustConfig:
    """Konfiguration fuer den Trust-Resolver."""

    allowlisted: list[str] = field(default_factory=list)
    denied: list[str] = field(default_factory=list)
    default_policy: str = "require_approval"  # "auto_trust" | "require_approval" | "deny"


class TrustResolver:
    """Bestimmt Trust-Level fuer Workspace-Pfade."""

    def __init__(self, config: TrustConfig | None = None) -> None:
        self._config = config or TrustConfig()
        log.debug(
            "trust_resolver_initialized",
            allowlisted=len(self._config.allowlisted),
            denied=len(self._config.denied),
            default_policy=self._config.default_policy,
        )

    @classmethod
    def from_jarvis_config(cls, config: Any) -> TrustResolver:
        """Erstellt TrustResolver aus CognithorConfig."""
        trust_cfg = getattr(config, "trust", None)
        if trust_cfg is None:
            return cls()
        return cls(
            TrustConfig(
                allowlisted=list(getattr(trust_cfg, "allowlisted", [])),
                denied=list(getattr(trust_cfg, "denied", [])),
                default_policy=getattr(trust_cfg, "default_policy", "require_approval"),
            )
        )

    def evaluate(self, cwd: str) -> tuple[str, str]:
        """Bestimmt Trust-Decision fuer einen Pfad.

        Args:
            cwd: Zu pruefender Pfad.

        Returns:
            (decision, reason) — decision: "auto_trust" | "require_approval" | "deny"
        """
        resolved = os.path.realpath(cwd)

        for allowed in self._config.allowlisted:
            try:
                if resolved.startswith(os.path.realpath(allowed)):
                    return ("auto_trust", f"Path within allowlisted root '{allowed}'")
            except (OSError, ValueError):
                continue

        for denied_path in self._config.denied:
            try:
                if resolved.startswith(os.path.realpath(denied_path)):
                    return ("deny", f"Path within denied root '{denied_path}'")
            except (OSError, ValueError):
                continue

        return (self._config.default_policy, "Path not in allowlist or denylist")

    def detect_trust_prompt_in_output(self, text: str) -> bool:
        """Erkennt ob ein Tool-Output einen Trust-Prompt enthaelt."""
        lower = text.lower()
        return any(cue in lower for cue in TRUST_PROMPT_CUES)
