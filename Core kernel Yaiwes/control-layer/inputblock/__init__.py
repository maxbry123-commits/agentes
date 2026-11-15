"""InputBlock · captura literal · hash chain · TTL · classifier · critical gate."""

from .store import InputBlock, InputStore, Criticality
from .reader import InputBlockReader, ChainBrokenError
from .vault import VaultBackup
from .classifier import ClassifyResult, InputKind, classify, classify_block_content
from .critical_gate import CriticalConfirmRequired, CriticalGateResult, check_critical_confirm

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
    "CriticalConfirmRequired",
    "CriticalGateResult",
    "check_critical_confirm",
]
