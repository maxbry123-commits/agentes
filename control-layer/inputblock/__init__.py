"""InputBlock · captura literal · hash chain · TTL · classifier · 0% LLM."""

from .store import InputBlock, InputStore, Criticality
from .reader import InputBlockReader, ChainBrokenError
from .vault import VaultBackup
from .classifier import ClassifyResult, InputKind, classify, classify_block_content

__all__ = [
    "InputBlock",
    "InputStore",
    "Criticality",
    "InputBlockReader",
    "ChainBrokenError",
    "VaultBackup",
    "ClassifyResult",
    "InputKind",
    "classify",
    "classify_block_content",
]
