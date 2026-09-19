"""
router_modelos.py - Decide QUE proveedor y QUE modelo de LLM usar para una
consulta. Determinista: nunca es el LLM quien se elige a si mismo.
Reglas fijas por tipo de tarea + disponibilidad real de keys en el entorno.

Proveedores de TEST (nunca produccion): Cerebras y Groq.
Produccion futura: Router Inteligente Universal (repo
router-universal-router-inteligente-) sera el unico proveedor de API key.

CATALOGO GROQ VERIFICADO (GitHub Action run, GET /models real,
2026-09-19T04:14Z): esta cuenta tiene habilitados solo 13 modelos, y
NINGUNO de los pedidos originalmente (llama-3.3-70b-versatile,
qwen/qwen3-32b, moonshotai/kimi-k2-instruct) esta en ese catalogo ->
daban HTTP 404. El unico probado con PASS real (HTTP 200 + contenido) es
openai/gpt-oss-120b. Catalogo completo disponible:
whisper-large-v3, openai/gpt-oss-20b, groq/compound,
meta-llama/llama-prompt-guard-2-86m, canopylabs/orpheus-arabic-saudi,
allam-2-7b, openai/gpt-oss-safeguard-20b, openai/gpt-oss-120b,
canopylabs/orpheus-v1-english, qwen/qwen3.8-27b,
meta-llama/llama-prompt-guard-2-22m, groq/compound-mini,
whisper-large-v3-turbo.

GROQ_API_KEY_1 quedo marcada INVALIDA (HTTP 401 real, dos corridas
consecutivas). Las keys 2 a 7 son validas. Se rota solo sobre las
validas hasta que el Director confirme/reemplace la key 1.

Groq: 1 sola API key sirve para TODOS los modelos del catalogo; lo
unico que cambia entre modelos es el campo "model" del payload.
"""
import os
import itertools

KEY_INVALIDA_CONOCIDA = {"GROQ_API_KEY_1"}  # HTTP 401 real, confirmado 2 veces

PROVEEDORES_DISPONIBLES = {
    "cerebras": {
        "keys_env": [f"CEREBRAS_API_KEY_{i}" for i in range(1, 7)],
        "url": "https://api.cerebras.ai/v1/chat/completions",
        "modelo_default": "llama3.3-70b",
        "uso": "alto_volumen",
    },
    "groq": {
        "keys_env": [f"GROQ_API_KEY_{i}" for i in range(1, 8) if f"GROQ_API_KEY_{i}" not in KEY_INVALIDA_CONOCIDA],
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "modelo_default": "openai/gpt-oss-120b",
        "uso": "test_multi_modelo",
    },
}

# Catalogo real de la cuenta (ver GET /models, evidencia en
# tests/evidencia_runs/). Tabla determinista tipo_tarea -> modelo,
# nunca decidida por el LLM. Usa SOLO ids confirmados en catalogo real.
CATALOGO_GROQ_VERIFICADO = [
    "whisper-large-v3",
    "openai/gpt-oss-20b",
    "groq/compound",
    "meta-llama/llama-prompt-guard-2-86m",
    "canopylabs/orpheus-arabic-saudi",
    "allam-2-7b",
    "openai/gpt-oss-safeguard-20b",
    "openai/gpt-oss-120b",
    "canopylabs/orpheus-v1-english",
    "qwen/qwen3.8-27b",
    "meta-llama/llama-prompt-guard-2-22m",
    "groq/compound-mini",
    "whisper-large-v3-turbo",
]

TAREA_A_MODELO_GROQ = {
    "codigo": "openai/gpt-oss-120b",
    "diseno_arquitectura": "openai/gpt-oss-120b",
    "razonamiento": "openai/gpt-oss-120b",
    "evaluar_componente": "openai/gpt-oss-120b",
    "investigar_gap": "groq/compound",  # tiene tool-use/search integrado
    "investigacion": "groq/compound",
    "chat_rapido": "openai/gpt-oss-20b",  # mas chico/rapido
}
MODELO_GROQ_DEFAULT = "openai/gpt-oss-120b"


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
        modelo = TAREA_A_MODELO_GROQ.get(tipo_tarea, MODELO_GROQ_DEFAULT)
        if modelo not in CATALOGO_GROQ_VERIFICADO:
            # fail-closed: nunca pedir a ciegas un modelo no verificado
            return MODELO_GROQ_DEFAULT
        return modelo
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
