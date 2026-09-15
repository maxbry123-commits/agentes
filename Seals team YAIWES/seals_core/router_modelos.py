"""
router_modelos.py - Decide QUE proveedor de LLM usar para una consulta.
Determinista: nunca es el LLM quien elige el LLM. Reglas fijas por tipo
de tarea y disponibilidad. Hoy: solo Cerebras (6 keys). Espacio ya listo
para modelos locales cuando el Director los entregue.
"""
import os
import itertools

PROVEEDORES_DISPONIBLES = {
    "cerebras": {
        "keys_env": [f"CEREBRAS_API_KEY_{i}" for i in range(1, 7)],
        "url": "https://api.cerebras.ai/v1/chat/completions",
        "modelo": "llama3.3-70b",
        "uso": "alto_volumen",
    },
}

_ciclos = {
    nombre: itertools.cycle([os.environ.get(k) for k in cfg["keys_env"] if os.environ.get(k)])
    for nombre, cfg in PROVEEDORES_DISPONIBLES.items()
}


def elegir_proveedor(tipo_tarea: str) -> str:
    if tipo_tarea in ("evaluar_componente", "investigar_gap"):
        return "cerebras"
    return "cerebras"


def siguiente_key(proveedor: str):
    ciclo = _ciclos.get(proveedor)
    if ciclo is None:
        return None
    return next(ciclo)


def ask_council(tipo_tarea: str, contexto: dict, pregunta: str, n_consultas: int = 1):
    from consultor_experto import consultar_experto_cerebras

    proveedor = elegir_proveedor(tipo_tarea)
    respuestas = []
    for _ in range(n_consultas):
        respuestas.append(consultar_experto_cerebras(contexto, pregunta))
    return respuestas
