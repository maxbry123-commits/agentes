"""
decision_on_demand.py
----------------------
La ÚNICA cápsula del kernel donde se permite llamar al LLM.
Recibe los módulos ya elegidos por expert_panel_router (SELECT) y hace:
  ADAPT     -> arma el prompt final por módulo
  IMPLEMENT -> lo manda al LLM (función inyectada, no hardcodeada aquí)
  RANK      -> opcionalmente ordena/agrupa las respuestas (Judge inyectado)

Nada de lógica de negocio del LLM vive aquí — solo orquesta la llamada.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from expert_panel_router import DEFAULT_BANK_PATH, ModuloRazonamiento, select_modulos


# Firma que debe cumplir cualquier proveedor de LLM que conectes
# (LiteLLM Router, DSPy, una llamada directa a una API, lo que sea).
LlmCallerFn = Callable[[str, int], str]

# Firma opcional para rankear/fusionar las respuestas (verdict-authority).
JuezFn = Callable[[str, list["RespuestaModulo"]], list["RespuestaModulo"]]


@dataclass(frozen=True)
class RespuestaModulo:
    artifact_id: str
    prompt_enviado: str
    respuesta: str


def _llm_caller_dummy(prompt: str, max_tokens: int) -> str:
    """Implementación de reemplazo para poder probar el flujo sin conectar
    todavía ninguna API real. Sustitúyela por LiteLLM Router, DSPy, etc.
    """
    return (
        f"[SIN LLM CONECTADO] Prompt recibido "
        f"({len(prompt)} chars, límite {max_tokens} tokens)."
    )


def adaptar_prompt(modulo: ModuloRazonamiento, tarea: str) -> str:
    """Paso ADAPT: combina el patrón genérico del módulo con la tarea
    concreta. No cambia el archivo del módulo — genera texto nuevo en
    memoria cada vez."""
    return (
        f"{modulo.descripcion}\n\n"
        f"Tarea a resolver: {tarea}\n\n"
        f"Responde aplicando específicamente ese patrón de pensamiento, "
        f"no una respuesta genérica."
    )


def ejecutar_modulos(
    tarea: str,
    modulos: list[ModuloRazonamiento],
    llm_caller: LlmCallerFn = _llm_caller_dummy,
) -> list[RespuestaModulo]:
    """Paso IMPLEMENT: corre cada módulo adaptado contra el LLM.
    Aquí es donde, en producción, reemplazarías el bucle secuencial por
    tu Multi-API Fabric en modo SPLIT/RACE para que corran en paralelo
    contra distintos proveedores — la firma de esta función no cambia.
    """
    resultados: list[RespuestaModulo] = []
    for modulo in modulos:
        prompt = adaptar_prompt(modulo, tarea)
        respuesta = llm_caller(prompt, modulo.max_tokens)
        resultados.append(
            RespuestaModulo(
                artifact_id=modulo.artifact_id,
                prompt_enviado=prompt,
                respuesta=respuesta,
            )
        )
    return resultados


def decidir(
    tarea: str,
    bank_path: Path = DEFAULT_BANK_PATH,
    top_k: int = 6,
    llm_caller: LlmCallerFn = _llm_caller_dummy,
    juez: Optional[JuezFn] = None,
) -> list[RespuestaModulo]:
    """Punto de entrada único de esta cápsula: SELECT -> ADAPT -> IMPLEMENT
    -> (RANK opcional). Esto es lo que el kernel llama; nunca al revés.
    """
    modulos = select_modulos(tarea, bank_path=bank_path, top_k=top_k)
    if not modulos:
        return []

    resultados = ejecutar_modulos(tarea, modulos, llm_caller=llm_caller)

    if juez is not None:
        resultados = juez(tarea, resultados)

    return resultados


if __name__ == "__main__":
    # Prueba mínima sin LLM real conectado, para verificar que el flujo corre.
    tarea_ejemplo = "Cómo puedo aumentar las ventas de mi tienda"
    salida = decidir(tarea_ejemplo)
    if not salida:
        print("No hay módulos en el banco todavía — agrega .yaml a reasoning_modules/")
    for r in salida:
        print(f"--- {r.artifact_id} ---")
        print(r.respuesta)
        print()
