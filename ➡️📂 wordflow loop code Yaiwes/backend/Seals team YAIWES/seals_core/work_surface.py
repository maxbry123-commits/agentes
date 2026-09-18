"""
work_surface.py - P1-22/P1-23 FIX. work_surface debe ser explicito en el
contrato de tarea (BACKEND/FRONTEND/MIXED), nunca decidido solo por el
LLM. Frontend exige CODE PASS + BROWSER PASS + VISUAL PASS, nunca solo
que el codigo compile.
"""
from dataclasses import dataclass
from enum import Enum


class WorkSurface(str, Enum):
    BACKEND = "BACKEND"
    FRONTEND = "FRONTEND"
    MIXED = "MIXED"


@dataclass
class FrontendGateResult:
    code_pass: bool = False
    browser_pass: bool = False
    visual_pass: bool = False

    def pass_completo(self) -> tuple[bool, str]:
        """P1-23 regla dura: SOURCE CODE PASS no significa UI PASS.
        Los 3 son obligatorios, ninguno opcional."""
        if not self.code_pass:
            return False, "FALTA_CODE_PASS"
        if not self.browser_pass:
            return False, "FALTA_BROWSER_PASS"
        if not self.visual_pass:
            return False, "FALTA_VISUAL_PASS"
        return True, "CODE_PASS+BROWSER_PASS+VISUAL_PASS_completos"


def determinar_work_surface(tarea: dict) -> WorkSurface:
    """P1-22: work_surface viene EXPLICITO del contrato, no se infiere.
    Si no viene declarado, se falla cerrado a BACKEND (mas restrictivo,
    nunca se asume FRONTEND por defecto sin declaracion)."""
    declarado = tarea.get("work_surface")
    if declarado in (WorkSurface.BACKEND, WorkSurface.FRONTEND, WorkSurface.MIXED):
        return declarado
    if declarado in ("BACKEND", "FRONTEND", "MIXED"):
        return WorkSurface(declarado)
    return WorkSurface.BACKEND
