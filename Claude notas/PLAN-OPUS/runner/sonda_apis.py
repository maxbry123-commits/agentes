"""Sonda de APIs del mini router del loop (corre al inicio de cada vuelta).

Mismo metodo que seals_core/tests/test_groq_real.py (ya probado PASS 3/3), generalizado
a NVIDIA, Cerebras y Groq (los tres son compatibles OpenAI):
  1. GET /models con cada clave -> separa clave invalida (401/403) de clave valida.
  2. Del catalogo real se buscan los modelos qwen y gpt-oss (y el modelo del DAG).
  3. Chat real "Responde solo con la palabra OK" -> PASS solo con HTTP 200 + contenido.
Resultado: Claude notas/PLAN-OPUS/estado/SALUD-APIS.json. Nunca guarda una clave,
solo su nombre (variable de entorno o credential_ref).
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request

BASES = {
    "nvidia": "https://integrate.api.nvidia.com/v1",
    "cerebras": "https://api.cerebras.ai/v1",
    "groq": "https://api.groq.com/openai/v1",
}
BUSCAR = ("qwen", "gpt-oss")
MAX_MODELOS = 4


def _http(url: str, key: str, body: dict | None = None, timeout: float = 30) -> tuple[int | None, dict]:
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body else None,
                                 method="POST" if body else "GET",
                                 headers={"Authorization": "Bearer " + key, "Content-Type": "application/json",
                                          "User-Agent": "yaiwes-sonda"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310
            return r.status, json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as exc:
        return exc.code, {}
    except Exception as exc:  # noqa: BLE001 - red caida / timeout
        return None, {"error": type(exc).__name__}


def sondear_proveedor(proveedor: str, claves: list[tuple[str, str]], preferido: str | None = None) -> dict:
    base = BASES[proveedor]
    out = {"base_url": base, "claves": [], "catalogo_qwen_gptoss": [], "pruebas": [], "recomendado": None,
           "estado": "SIN_CLAVES"}
    if not claves:
        return out
    validas, catalogo = [], []
    for nombre, key in claves:
        code, data = _http(base + "/models", key, timeout=20)
        ok = code == 200
        out["claves"].append({"nombre": nombre, "http": code, "valida": ok})
        if ok:
            validas.append((nombre, key))
            catalogo = catalogo or [m.get("id", "") for m in data.get("data", [])]
    if not validas:
        out["estado"] = "CLAVES_INVALIDAS"
        return out
    elegidos = [m for m in catalogo if any(b in m.lower() for b in BUSCAR)]
    out["catalogo_qwen_gptoss"] = elegidos
    probar = ([preferido] if preferido and (not catalogo or preferido in catalogo) else []) + elegidos
    probar = list(dict.fromkeys(probar))[:MAX_MODELOS]
    for i, modelo in enumerate(probar):
        nombre, key = validas[i % len(validas)]
        t0 = time.time()
        code, data = _http(base + "/chat/completions", key, {
            "model": modelo, "max_tokens": 200,
            "messages": [{"role": "user", "content": "Responde solo con la palabra OK"}]}, timeout=60)
        texto = (((data.get("choices") or [{}])[0].get("message") or {}).get("content") or "").strip()
        paso = code == 200 and bool(texto)
        out["pruebas"].append({"modelo": modelo, "clave": nombre, "http": code, "ms": int((time.time() - t0) * 1000),
                               "pass": paso, "motivo": "PASS_OBJETIVO" if paso else f"HTTP_{code}_O_VACIO"})
    buenos = [p for p in out["pruebas"] if p["pass"]]
    out["recomendado"] = min(buenos, key=lambda p: p["ms"])["modelo"] if buenos else None
    out["claves_ok"] = [n for n, _ in validas]
    out["estado"] = "OK" if buenos else "SIN_MODELO_OK"
    return out


def sondear(fuentes: dict[str, list[tuple[str, str]]], preferidos: dict[str, str] | None = None) -> dict:
    preferidos = preferidos or {}
    return {p: sondear_proveedor(p, fuentes.get(p, []), preferidos.get(p)) for p in BASES}
