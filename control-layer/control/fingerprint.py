"""Fingerprint Engine — 7 booleanos, 0% LLM.
SOURCE: SALIDA_4_CONTRATOS · CAPA DE CONTROL 4 (A2)
La entrada se reduce a una huella. El selector solo ve esto.
"""
from __future__ import annotations
from dataclasses import dataclass
import re


@dataclass(frozen=True)
class Fingerprint:
    action: str
    writes: bool
    network: bool
    external: bool
    credentials: bool
    irreversible: bool
    parallel: bool

    def as_dict(self) -> dict:
        return {
            "action": self.action,
            "writes": self.writes,
            "network": self.network,
            "external": self.external,
            "credentials": self.credentials,
            "irreversible": self.irreversible,
            "parallel": self.parallel,
        }


_WRITE = re.compile(r"\b(write|install|create|update|delete|push|commit|deploy)\b", re.I)
_NET = re.compile(r"\b(http|https|api|download|fetch|network)\b", re.I)
_CRED = re.compile(r"\b(token|secret|password|credential|key|auth)\b", re.I)
_IRREV = re.compile(r"\b(delete|drop|destroy|force|irreversible|push\s+--force)\b", re.I)
_PAR = re.compile(r"\b(parallel|concurrent|async|batch)\b", re.I)
_EXT = re.compile(r"\b(external|third.?party|github|remote)\b", re.I)


def build_fingerprint(text: str, action: str = "unknown") -> Fingerprint:
    t = text or ""
    return Fingerprint(
        action=action.lower(),
        writes=bool(_WRITE.search(t) or action.lower() in {"write", "install", "delete"}),
        network=bool(_NET.search(t)),
        external=bool(_EXT.search(t)),
        credentials=bool(_CRED.search(t)),
        irreversible=bool(_IRREV.search(t)),
        parallel=bool(_PAR.search(t)),
    )
