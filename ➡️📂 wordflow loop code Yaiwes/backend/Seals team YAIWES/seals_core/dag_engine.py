"""
dag_engine.py - P0-01 FIX. El unico lugar que lee dag_schema.yaml. Se carga
FRESCO cada vez (no cacheado), para que editar el YAML cambie el
comportamiento real sin reiniciar nada - eso es lo que exige el criterio
de aceptacion de la auditoria 5x: "modificar una transicion del DAG debe
modificar realmente el flujo ejecutado".
"""
from pathlib import Path

import yaml

_DAG_PATH = Path(__file__).parent.parent / "dag_schema.yaml"

# Mapa: tipo de tarea (vocabulario de ejecutor.py) -> nodo del DAG que
# gobierna esa tarea (vocabulario de dag_schema.yaml). Esto es lo que
# faltaba: antes los dos vocabularios vivian separados sin conexion.
_TIPO_A_NODO = {
    "instalar_paquete": "EXECUTE",
    "verificar_existencia": "EXECUTE",
    "evaluar_componente": "RESEARCH",
    "diseno_arquitectura": "RESEARCH",
}


def cargar_dag() -> dict:
    with open(_DAG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def nodo_para_tipo(tipo: str) -> str | None:
    return _TIPO_A_NODO.get(tipo)


def obtener_nodo(dag: dict, nodo_id: str) -> dict | None:
    for paso in dag.get("steps", []):
        if paso.get("id") == nodo_id:
            return paso
    return None


def transicion_permitida(dag: dict, desde: str, hacia: str) -> bool:
    """Lee edges tal como esta AHORA en el archivo (fresco). Si alguien
    edita dag_schema.yaml y borra una transicion, esto lo refleja de
    inmediato, sin cache."""
    edges = dag.get("edges", [])
    objetivo = f"{desde}->{hacia}"
    return any(e == objetivo for e in edges)


def validar_ruta_de_tipo(tipo: str) -> tuple[bool, str]:
    """Valida que el nodo asignado a este tipo de tarea todavia existe en
    el DAG cargado fresco. Si no existe o la transicion de salida no esta
    declarada, devuelve (False, motivo) - eso se convierte en GAP, nunca
    en ejecucion silenciosa fuera del grafo declarado."""
    dag = cargar_dag()
    nodo_id = nodo_para_tipo(tipo)
    if nodo_id is None:
        return False, f"tipo_sin_nodo_dag:{tipo}"
    nodo = obtener_nodo(dag, nodo_id)
    if nodo is None:
        return False, f"nodo_no_declarado_en_dag:{nodo_id}"
    return True, nodo_id
