"""Reverse Validator — doble validación forward+reverse.
SOURCE: SALIDA_4 §14.8
Si forward pide C47 pero fingerprint.credentials=false → ERROR_DE_CLASIFICACION.
"""
from __future__ import annotations
from .fingerprint import Fingerprint

# Contrato → condiciones esperadas en fingerprint
REVERSE_EXPECT: dict[str, dict[str, bool]] = {
    "C47": {"credentials": True},
    "C45": {"credentials": True},
    "C34": {"irreversible": True},
    "C35": {"irreversible": True},
    "C33": {"network": True},  # a menudo con network; soft
}


def reverse_ok(contracts: list[str] | tuple[str, ...], fp: Fingerprint) -> tuple[bool, str]:
    fp_d = fp.as_dict()
    for c in contracts:
        expect = REVERSE_EXPECT.get(c)
        if not expect:
            continue
        for key, val in expect.items():
            if key == "network" and c == "C33":
                continue  # soft
            if fp_d.get(key) is not val:
                return False, f"ERROR_DE_CLASIFICACION contract={c} expect {key}={val}"
    return True, "ok"
