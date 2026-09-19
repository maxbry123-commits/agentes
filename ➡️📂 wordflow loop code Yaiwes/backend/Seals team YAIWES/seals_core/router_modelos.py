"""
router_modelos.py - Decide QUE proveedor y QUE modelo de LLM usar para una
consulta. Determinista: nunca es el LLM quien se elige a si mismo.
Reglas fijas por tipo de tarea + disponibilidad real de keys en el entorno.

Proveedores de TEST (nunca produccion): Cerebras y Groq.
Produccion futura: Router Inteligente Universal (repo
router-universal-router-inteligente-) sera el unico proveedor de API key.

Groq: 1 sola API key sirve para TODOS los modelos del catalogo Groq; lo
unico que cambia entre modelos es el campo "model" del payload. Aun asi
rotamos las 7 keys entregadas para repartir rate-limit (round robin
determinista, no decidido por LLM).
"""
import os
import itertools

PROVEEDORES_DISPONIBLES = {
    "cerebras": {
        "keys_env": [f"CEREBRAS_API_KEY_{i}" for i in range(1, 7)],
        "url": "https://api.cerebras.ai/v1/chat/completions",
        "modelo_default": "llama3.3-70b",
        "uso": "alto_volumen",
    },
    "groq": {
        "keys_env": [f"GROQ_API_KEY_{i}" for i in range(1, 8)],
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "modelo_default": "llama-3.3-70b-versatile",
        "uso": "test_multi_modelo",
    },
}

# Tabla determinista tipo_tarea -> modelo Groq. Nunca decidida por el LLM.
TAREA_A_MODELO_GROQ = {
    "codigo": "qwen/qwen3-32b",
    "diseno_arquitectura": "qwen/qwen3-32b",
    "razonamiento": "openai/gpt-oss-120b",
    "evaluar_componente": "openai/gpt-oss-120b",
    "investigar_gap": "moonshotai/kimi-k2-instruct",
    "investigacion": "moonshotai/kimi-k2-instruct",
    "chat_rapido": "llama-3.3-70b-versatile",
}
MODELO_GROQ_DEFAULT = "llama-3.3-70b-versatile"


def _keys_presentes(proveedor: str) -> list:
    cfg = PROVEEDORES_DISPONIBLES[proveedor]
    return [os.environ.get(k) for k in cfg["keys_env"] if os.environ.get(k)]


_ciclos = {
    nombre: itertools.cycle(_keys_presentes(nombre) or [None])
    for nombre in PROVEEDORES_DISPONIBLES
}


def elegir_proveedor(tipo_tarea: str) -> str:
    """
    Determinista por disponibilidad real de keys en el entorno, nunca por
    preferencia del LLM. Orden fijo: cerebras primero (alto volumen) si
    tiene keys reales; si no, groq (test). Si ninguno tiene keys -> None.
    """
    if _keys_presentes("cerebras"):
        return "cerebras"
    if _keys_presentes("groq"):
        return "groq"
    return None


def elegir_modelo(proveedor: str, tipo_tarea: str) -> str:
    if proveedor == "groq":
        return TAREA_A_MODELO_GROQ.get(tipo_tarea, MODELO_GROQ_DEFAULT)
    return PROVEEDORES_DISPONIBLES.get(proveedor, {}).get("modelo_default")


def siguiente_key(proveedor: str):
    ciclo = _ciclos.get(proveedor)
    if ciclo is None:
        return None
    return next(ciclo)


def ask_council(tipo_tarea: str, contexto: dict, pregunta: str, n_consultas: int = 1):
    proveedor = elegir_proveedor(tipo_tarea)
    if proveedor is None:
        return ["ERROR_SIN_PROVEEDOR: no hay keys de Cerebras ni Groq en el entorno"]

    modelo = elegir_modelo(proveedor, tipo_tarea)
    respuestas = []
    if proveedor == "cerebras":
        from consultor_experto import consultar_experto_cerebras
        for _ in range(n_consultas):
            respuestas.append(consultar_experto_cerebras(contexto, pregunta))
    else:
        from consultor_groq import consultar_experto_groq
        for _ in range(n_consultas):
            respuestas.append(consultar_experto_groq(contexto, pregunta, modelo))
    return respuestas
