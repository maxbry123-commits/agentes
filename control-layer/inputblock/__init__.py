"""InputBlock · captura literal · hash chain · TTL · 0% LLM."""

from .store import InputBlock, InputStore, Criticality
from .reader import InputBlockReader, ChainBrokenError
from .vault import VaultBackup

__all__ = [
    "InputBlock",
    "InputStore",
    "Criticality",
    "InputBlockReader",
    "ChainBrokenError",
    "VaultBackup",
]
