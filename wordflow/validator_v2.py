"""Minimal Enchufe Universal v2 validator — DUAL.03"""
from __future__ import annotations
REQUIRED = ["artifact_id", "version", "estado", "categoria", "etapa", "contrato", "ejecucion", "seguridad", "firma"]
VALID_CATEGORIA = {"pipeline", "transversal", "acelerador"}
VALID_ETAPA = {"E", "P", "S", "T", "A"}

def validate_ficha(data: dict) -> tuple[bool, list[str]]:
    errors = []
    for k in REQUIRED:
        if k not in data:
            errors.append(f"missing required: {k}")
    if data.get("categoria") not in VALID_CATEGORIA:
        errors.append(f"invalid categoria: {data.get('categoria')}")
    if data.get("etapa") not in VALID_ETAPA:
        errors.append(f"invalid etapa: {data.get('etapa')}")
    if "contrato" in data and "rol" not in data["contrato"]:
        errors.append("contrato.rol missing")
    return len(errors) == 0, errors

if __name__ == "__main__":
    print("validator_v2 ready")
