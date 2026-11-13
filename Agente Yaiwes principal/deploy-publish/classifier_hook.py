"""
Punto de decision: cuando un workflow debe abrir una instancia del motor
de programacion, y con que perfil, segun la complejidad de la tarea.

Esto vive conceptualmente en task_classifier + reasoning-kernel; se
entrega como funcion pura para integrarla en el classifier real sin
rediseñar el resto del loop. Si el pool esta lleno, NO se detiene el
sistema: devuelve None para que el llamador decida encolar o probar
otro engine_binding (fallback-chain-resolver).
"""

from instance_pool import ConcurrencyCapExceeded, InstancePoolManager
from programming_instance import ApiSlot, ProgrammingInstance


TRIVIAL = "trivial"
MEDIA = "media"
ALTA = "alta"
CRITICA = "critica"

BLAST_RADIUS_ALTA = 5
BLAST_RADIUS_MEDIA = 2

_PROFILE_BY_COMPLEXITY = {
    TRIVIAL: "fast",
    MEDIA: "fast",
    ALTA: "strict_forensic",
    CRITICA: "strict_forensic",
}


def requires_programming(task: dict) -> bool:
    """Determina si una tarea necesita el motor de programacion de code.

    Regla minima explicita, no heuristica oculta: la tarea debe declarar
    kind == 'code'. Ajustar aqui si task_classifier usa otra convencion.
    """
    return task.get("kind") == "code"


def classify_complexity(task: dict) -> str:
    """Clasifica complejidad segun blast_radius y criticality_tag ya
    definidos en el task_classifier existente del repo."""
    blast_radius = task.get("estimated_blast_radius", 1)
    critical = task.get("criticality_tag", False)
    if critical:
        return CRITICA
    if blast_radius >= BLAST_RADIUS_ALTA:
        return ALTA
    if blast_radius >= BLAST_RADIUS_MEDIA:
        return MEDIA
    return TRIVIAL


def dispatch_to_engine(
    task: dict,
    tenant_id: str,
    workflow_id: str,
    api_slot: ApiSlot,
    engine_binding: str,
    pool: InstancePoolManager,
) -> ProgrammingInstance | None:
    """Decide y abre una instancia si la tarea lo requiere.

    Devuelve None si la tarea no es de programacion (el workflow sigue su
    propio camino normal), o si el pool esta lleno (el llamador decide el
    siguiente paso: encolar, reintentar, o probar otro engine_binding).
    """
    if not requires_programming(task):
        return None
    complexity = classify_complexity(task)
    profile = _PROFILE_BY_COMPLEXITY[complexity]
    instance = ProgrammingInstance(
        tenant_id=tenant_id,
        mission_id=task.get("mission_id", ""),
        api_slot=api_slot,
        engine_binding=engine_binding,
        parent_workflow_id=workflow_id,
        profile=profile,
        idempotency_key=task.get("task_id"),
    )
    try:
        return pool.create_instance(instance)
    except ConcurrencyCapExceeded:
        return None
