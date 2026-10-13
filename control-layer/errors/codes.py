from enum import Enum


class ErrorCode(str, Enum):
    """Códigos de error normalizados (SOURCE: SALIDA_1_CAPA_CONTROL_PARTE_2 §23)."""

    E001 = "E001"  # Error de sintaxis / Missing Node
    E002 = "E002"  # Cycle detected
    E003 = "E003"  # Unknown ASSERT / Unknown ACTION
    E004 = "E004"  # Schema mismatch
    E005 = "E005"  # Variable no declarada
    E017 = "E017"  # ASSERT failed (generic)
    E031 = "E031"  # ASSERT SUCCESS specific

    ERROR_UNKNOWN_ACTION = "ERROR_UNKNOWN_ACTION"
    ERROR_UNKNOWN_FIELD = "ERROR_UNKNOWN_FIELD"
    ERROR_UNKNOWN_TOKEN = "ERROR_UNKNOWN_TOKEN"
    ERROR_CLASSIFICATION = "ERROR_CLASSIFICATION"


def format_error(code: ErrorCode, node: str | None = None, detail: str = "") -> str:
    parts = [f"ERROR={code.value}"]
    if node:
        parts.append(f"NODE={node}")
    if detail:
        parts.append(detail)
    parts.append("STATUS=FAILED")
    return " ".join(parts)
