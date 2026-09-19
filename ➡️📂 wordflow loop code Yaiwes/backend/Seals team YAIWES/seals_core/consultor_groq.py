"""
consultor_groq.py - El 5-10% LLM del pipeline SELECT->ADAPT->IMPLEMENT,
via Groq (proveedor de TEST, igual que Cerebras). Una sola API key de
Groq sirve para todos los modelos del catalogo: lo que cambia por
consulta es el campo "model" del payload, nunca la key. Rotamos las 7
keys entregadas por rate-limit / aislamiento, con round robin
determinista (itertools.cycle), no elegido por el LLM.

Las API keys SIEMPRE vienen de variables de entorno (GitHub Actions
secrets en el test-workflow de Wordflow), nunca hardcodeadas.
"""
import os
import itertools
import requests

_KEYS_ENV = [f"GROQ_API_KEY_{i}" for i in range(1, 8)]
_GROQ_KEYS = [os.environ.get(k) for k in _KEYS_ENV]
_key_cycle = itertools.cycle([k for k in _GROQ_KEYS if k] or [None])

_URL = "https://api.groq.com/openai/v1/chat/completions"
_MODELO_DEFAULT = "llama-3.3-70b-versatile"


def consultar_experto_groq(contexto: dict, pregunta: str, modelo: str = _MODELO_DEFAULT) -> str:
    keys_disponibles = [k for k in _GROQ_KEYS if k]
    if not keys_disponibles:
        return "ERROR: no hay GROQ_API_KEY_1..7 configuradas como variables de entorno"

    key = next(_key_cycle)
    if key is None:
        return "ERROR: no hay GROQ_API_KEY_1..7 configuradas como variables de entorno"

    try:
        resp = requests.post(
            _URL,
            headers={"Authorization": f"Bearer {key}"},
            json={
                "model": modelo,
                "messages": [
                    {
                        "role": "user",
                        "content": f"Contexto: {contexto}\nPregunta: {pregunta}\nResponde solo la decision, sin explicacion adicional.",
                    }
                ],
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"ERROR_GROQ: {e}"


def listar_modelos_habilitados() -> list:
    """Consulta real GET /models para confirmar que catalogo tiene la cuenta."""
    keys_disponibles = [k for k in _GROQ_KEYS if k]
    if not keys_disponibles:
        return []
    key = keys_disponibles[0]
    resp = requests.get(
        "https://api.groq.com/openai/v1/models",
        headers={"Authorization": f"Bearer {key}"},
        timeout=30,
    )
    resp.raise_for_status()
    return [m["id"] for m in resp.json().get("data", [])]
