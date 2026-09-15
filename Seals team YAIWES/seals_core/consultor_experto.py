"""
consultor_experto.py - El 5-10% LLM del pipeline SELECT->ADAPT->IMPLEMENT.
El 90% deterministico (ejecutor.py) decide CUANDO llamar esto.
Usa Cerebras para volumen alto, NUNCA Claude aqui (presupuesto).
Las API keys SIEMPRE vienen de variables de entorno, nunca hardcodeadas.
"""
import os
import itertools
import requests

_KEYS_ENV = [f"CEREBRAS_API_KEY_{i}" for i in range(1, 7)]
_CEREBRAS_KEYS = [os.environ.get(k) for k in _KEYS_ENV]
_key_cycle = itertools.cycle([k for k in _CEREBRAS_KEYS if k])


def consultar_experto_cerebras(contexto: dict, pregunta: str) -> str:
    keys_disponibles = [k for k in _CEREBRAS_KEYS if k]
    if not keys_disponibles:
        return "ERROR: no hay CEREBRAS_API_KEY_1..6 configuradas como variables de entorno"

    key = next(_key_cycle)
    try:
        resp = requests.post(
            "https://api.cerebras.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}"},
            json={
                "model": "llama3.3-70b",
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
        return f"ERROR_CEREBRAS: {e}"
