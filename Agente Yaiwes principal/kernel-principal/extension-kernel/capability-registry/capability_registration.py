"""
Registro de code-programming-engine e instance-pool como capacidades
montadas del kernel, siguiendo el MISMO formato que ya usa
extensions/wordflow/component_catalog.json y connect_catalog.json
(verificado en la auditoria del repo: catalog_version 1.1.0 / version 1.7.0,
legend WIRED/STUB/PARTIAL/GAP/LOCATE_ONLY/WIRED_NO_PASS/WIRED_DENY/DRY_RUN).

Este modulo NO ejecuta nada: solo declara como debe verse la entrada en
esos catalogos para que extension-kernel sepa que el motor existe, sin
contenerlo. Grok: usar append_entries() sobre los catalogos reales, no
sobreescribir el archivo entero.
"""

import json


COMPONENT_ENTRY_CODE_ENGINE = {
    "id": "code_programming_engine",
    "path": "code-programming-engine/",
    "kind": "engine",
    "status": "materialized",
    "capabilities": [
        "quality_bar",
        "goal_lock",
        "cognitive_wire",
        "forensic_enforcement",
        "instance_pool_binding",
    ],
}

COMPONENT_ENTRY_INSTANCE_POOL = {
    "id": "code_programming_instance_pool",
    "path": "code-programming-engine/instance_pool.py",
    "kind": "service",
    "status": "materialized",
    "capabilities": [
        "tenant_isolation",
        "concurrency_cap",
        "handle_lifecycle",
        "idempotency_dedup",
    ],
}

CONNECT_ENTRY_CLASSIFIER_TO_ENGINE = {
    "id": "CONN.classifier_to_programming_engine",
    "from": "task_classifier",
    "to": "code_programming_engine",
    "status": "WIRED",
    "note": "clasifica tarea; si requiere code, abre instancia en el pool",
}

CONNECT_ENTRY_ENGINE_TO_GATEWAY = {
    "id": "CONN.engine_to_intelligence_gateway",
    "from": "code_programming_engine",
    "to": "intelligence_gateway",
    "status": "WIRED_DENY",
    "note": "el motor consulta el gateway; vendor_call solo vive en adapter-layer",
}


def append_entries(catalog_path: str, entries: list[dict]) -> None:
    """Anade entradas nuevas a un catalogo JSON existente sin pisar lo demas.

    catalog_path: ruta a component_catalog.json o connect_catalog.json.
    entries: lista de dicts a anadir bajo 'components' o 'connections'.
    Es idempotente: si el id ya existe, no lo duplica.
    """
    with open(catalog_path, "r", encoding="utf-8") as handle:
        catalog = json.load(handle)
    key = "components" if "component" in catalog_path else "connections"
    existing_ids = {item["id"] for item in catalog.get(key, [])}
    for entry in entries:
        if entry["id"] not in existing_ids:
            catalog.setdefault(key, []).append(entry)
    with open(catalog_path, "w", encoding="utf-8") as handle:
        json.dump(catalog, handle, indent=2, ensure_ascii=False)
