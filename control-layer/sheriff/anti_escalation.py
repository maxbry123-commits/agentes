from pathlib import Path
from typing import Any
import yaml


def load_anti_escalation(path: str | Path = "config/anti_escalation.yaml") -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def check_anti_escalation(proposed_action: str, rules: dict[str, Any] | None = None) -> tuple[bool, str]:
    """Verifica R21-R30 contra una acción propuesta.

    SOURCE: SALIDA_1_CAPA_CONTROL_PARTE_2 §20
    """
    if rules is None:
        rules = load_anti_escalation()

    blocked = {
        "create_phase": "R21",
        "create_task": "R22",
        "modify_mission": "R23",
        "unregistered_node": "R24",
        "discover_component": "R25",
        "change_dag": "R26",
        "modify_architecture": "R27",
        "change_protected_config": "R28",
        "out_of_scope": "R29",
        "outside_registry": "R30",
    }

    if proposed_action in blocked:
        rule_id = blocked[proposed_action]
        return False, f"Blocked by {rule_id}: {rules['rules'][rule_id]['name']}"

    return True, "OK"
