"""Sentinela stub — DUAL.04"""
from __future__ import annotations
from typing import Any

class Sentinela:
    def __init__(self):
        self.active_contracts: dict[str, str] = {}

    def select(self, process_type: str) -> str | None:
        return self.active_contracts.get(process_type)

    def authorize(self, contract_id: str, context: dict[str, Any]) -> bool:
        return True  # stub

    def register(self, process_type: str, contract_id: str) -> None:
        self.active_contracts[process_type] = contract_id

if __name__ == "__main__":
    s = Sentinela()
    s.register("code_change", "C12")
    print("sentinela_stub ready", s.select("code_change"))
