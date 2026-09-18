"""
tool_result.py - P0-17 FIX (integracion Meta Glimmer). Contrato tipado de
resultado de herramienta. Un error de tool NUNCA se convierte en string
suelto que despues alguien confunda con exito - siempre es un ToolResult
explicito, con error_type, y jamas cierra mision por si solo.
"""
from dataclasses import dataclass, field


@dataclass
class ToolResult:
    ok: bool
    error_type: str = ""  # "" si ok=True. Ej: NETWORK_ERROR, POLICY_DENIED, TIMEOUT
    stdout: str = ""
    stderr: str = ""
    exit_code: int | None = None
    artifacts: list[str] = field(default_factory=list)
    receipt: str = ""

    def como_observacion(self) -> dict:
        """P0-17: un ToolResult con error se convierte en OBSERVATION, no
        en un GAP generico ni en un PASS accidental."""
        return {
            "tipo": "OBSERVATION",
            "ok": self.ok,
            "error_type": self.error_type,
            "stderr": self.stderr[:500],
            "exit_code": self.exit_code,
        }
