"""
Punto de decision: cuando un workflow debe abrir una instancia del motor
de programacion, y con que perfil, segun la complejidad de la tarea.
"""

from pathlib import Path
import importlib.util

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

def _workalendar_port():
    p = Path(__file__).resolve().parent / "workalendar" / "yaiwes_workalendar_port.py"
    spec = importlib.util.spec_from_file_location("n25_workalendar_port", p)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod

def working_day_gate(task: dict) -> dict:
    return _workalendar_port().working_day_gate(task)

def requires_programming(task: dict) -> bool:
    return task.get("kind") == "code"

def classify_complexity(task: dict) -> str:
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
):
    if not requires_programming(task):
        return None
    if task.get("schedule_date"):
        gate = working_day_gate(task)
        if not gate.get("allowed"):
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
