"""Vault backup · copia de bloques CRITICO fuera del store principal."""
from __future__ import annotations

import json
from pathlib import Path
from typing import List

from .store import Criticality, InputBlock, InputStore


class VaultBackup:
    def __init__(self, vault_path: Path) -> None:
        self.vault_path = vault_path
        self.vault_path.parent.mkdir(parents=True, exist_ok=True)

    def backup_critical(self, store: InputStore) -> int:
        n = 0
        with self.vault_path.open("a", encoding="utf-8") as f:
            for b in store:
                if b.criticality == Criticality.CRITICO:
                    f.write(json.dumps(b.to_dict(), ensure_ascii=False) + "\n")
                    n += 1
        return n

    def load_all(self) -> List[InputBlock]:
        if not self.vault_path.is_file():
            return []
        out: List[InputBlock] = []
        for line in self.vault_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                out.append(InputBlock.from_dict(json.loads(line)))
        return out
