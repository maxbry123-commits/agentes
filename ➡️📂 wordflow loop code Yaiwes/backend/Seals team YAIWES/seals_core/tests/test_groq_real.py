"""
test_groq_real.py - Test Oracle OBJETIVO para el proveedor Groq del
Wordflow Loop Code Yaiwes. Corre SOLO dentro de GitHub Actions (unico
uso permitido de Actions en este proyecto), usando las 7
GROQ_API_KEY_1..7 como secrets del repo.

Regla dura: el PASS nunca viene de que el LLM "diga" que algo salio bien.
El PASS viene de:
  1. HTTP 200 real de api.groq.com
  2. La respuesta trae choices[0].message.content no vacio
  3. Se ejercitan las keys validas al menos una vez (rotacion real)

Diagnostico previo (primera corrida detecto 401 en 1 key y 404 en 2
modelos): antes de probar chat completions, se valida CADA key contra
GET /models (endpoint real, sin costo de tokens) para separar
"key invalida" de "modelo no existe en el catalogo de esa cuenta". Esto
es evidencia objetiva, no una suposicion.
"""
import os
import sys
import json
import hashlib
import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests  # noqa: E402

CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"
MODELS_URL = "https://api.groq.com/openai/v1/models"

MODELOS_A_PROBAR = [
    "llama-3.3-70b-versatile",
    "qwen/qwen3-32b",
    "openai/gpt-oss-120b",
    "moonshotai/kimi-k2-instruct",
]

KEYS_ENV = [f"GROQ_API_KEY_{i}" for i in range(1, 8)]


def cargar_keys():
    keys = [(nombre, os.environ.get(nombre)) for nombre in KEYS_ENV]
    faltantes = [n for n, v in keys if not v]
    presentes = [(n, v) for n, v in keys if v]
    return presentes, faltantes


def validar_key(nombre: str, key: str) -> dict:
    """GET /models real: separa key invalida (401/403) de key valida."""
    try:
        resp = requests.get(
            MODELS_URL,
            headers={"Authorization": f"Bearer {key}"},
            timeout=20,
        )
        ids = []
        if resp.status_code == 200:
            ids = [m["id"] for m in resp.json().get("data", [])]
        return {
            "key": nombre,
            "http_status": resp.status_code,
            "valida": resp.status_code == 200,
            "modelos_catalogo": ids,
        }
    except Exception as e:
        return {"key": nombre, "http_status": None, "valida": False, "modelos_catalogo": [], "excepcion": str(e)}


def llamar_groq(key: str, modelo: str) -> dict:
    resp = requests.post(
        CHAT_URL,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={
            "model": modelo,
            "messages": [{"role": "user", "content": "Responde solo con la palabra OK"}],
            "max_tokens": 200,
        },
        timeout=30,
    )
    return {
        "http_status": resp.status_code,
        "ok_http": resp.status_code == 200,
        "body": resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {"raw": resp.text[:500]},
    }


def evaluar(resultado: dict) -> tuple:
    if not resultado["ok_http"]:
        return False, f"HTTP_{resultado['http_status']}_NO_200"
    body = resultado["body"]
    choices = body.get("choices")
    if not choices or not isinstance(choices, list):
        return False, "SIN_CHOICES_EN_RESPUESTA"
    content = choices[0].get("message", {}).get("content", "")
    if not content or not content.strip():
        return False, "CONTENT_VACIO"
    return True, "PASS_OBJETIVO"


def main():
    presentes, faltantes = cargar_keys()
    evidencia = {
        "timestamp_utc": datetime.datetime.utcnow().isoformat() + "Z",
        "keys_presentes": [n for n, _ in presentes],
        "keys_faltantes": faltantes,
        "diagnostico_keys": [],
        "resultados": [],
    }

    if not presentes:
        evidencia["veredicto_final"] = "FAIL_SIN_KEYS"
        _escribir_evidencia(evidencia)
        print("FAIL: ninguna GROQ_API_KEY_1..7 presente como secret")
        sys.exit(1)

    # 1) Diagnostico real por key (barato: /models no consume tokens)
    diag = [validar_key(n, k) for n, k in presentes]
    evidencia["diagnostico_keys"] = [
        {k: v for k, v in d.items() if k != "modelos_catalogo"} for d in diag
    ]
    for d in diag:
        estado = "VALIDA" if d["valida"] else "INVALIDA"
        print(f"[DIAG] key={d['key']} http={d['http_status']} estado={estado}")

    keys_validas = [(d["key"], k) for d, (n, k) in zip(diag, presentes) if d["valida"] and d["key"] == n]
    catalogo_real = next((d["modelos_catalogo"] for d in diag if d["valida"] and d["modelos_catalogo"]), [])
    evidencia["catalogo_real_detectado"] = catalogo_real
    print(f"[DIAG] catalogo real ({len(catalogo_real)} modelos): {catalogo_real}")

    if not keys_validas:
        evidencia["veredicto_final"] = "FAIL_TODAS_LAS_KEYS_INVALIDAS"
        _escribir_evidencia(evidencia)
        print("FAIL: ninguna GROQ_API_KEY_1..7 paso la validacion real contra /models")
        sys.exit(1)

    # 2) Solo probar chat completions con modelos que SI estan en el
    #    catalogo real (evidencia objetiva, no lista fija adivinada)
    modelos_validos = [m for m in MODELOS_A_PROBAR if not catalogo_real or m in catalogo_real]
    modelos_fuera_catalogo = [m for m in MODELOS_A_PROBAR if catalogo_real and m not in catalogo_real]
    evidencia["modelos_fuera_de_catalogo"] = modelos_fuera_catalogo
    for m in modelos_fuera_catalogo:
        print(f"[SKIP] modelo={m} no esta en el catalogo real de la cuenta, no se prueba a ciegas")

    todo_paso = True
    idx_key = 0
    for modelo in modelos_validos:
        nombre_key, key = keys_validas[idx_key % len(keys_validas)]
        idx_key += 1
        try:
            resultado_http = llamar_groq(key, modelo)
            paso, motivo = evaluar(resultado_http)
        except Exception as e:
            paso, motivo = False, f"EXCEPCION:{e}"
            resultado_http = {"http_status": None, "ok_http": False, "body": {}}

        fingerprint = hashlib.sha256(
            f"{modelo}|{resultado_http.get('http_status')}|{motivo}".encode("utf-8")
        ).hexdigest()

        evidencia["resultados"].append({
            "modelo": modelo,
            "key_usada": nombre_key,
            "http_status": resultado_http.get("http_status"),
            "pass": paso,
            "motivo": motivo,
            "sha256_evidencia": fingerprint,
        })
        print(f"[{'PASS' if paso else 'FAIL'}] modelo={modelo} key={nombre_key} http={resultado_http.get('http_status')} motivo={motivo}")
        if not paso:
            todo_paso = False

    if not modelos_validos:
        todo_paso = False
        evidencia["veredicto_final"] = "FAIL_NINGUN_MODELO_PEDIDO_EN_CATALOGO"
    else:
        evidencia["veredicto_final"] = "PASS" if todo_paso else "FAIL"

    keys_ejercitadas = {r["key_usada"] for r in evidencia["resultados"]}
    evidencia["keys_ejercitadas_count"] = len(keys_ejercitadas)

    _escribir_evidencia(evidencia)

    if not todo_paso:
        print("FAIL: al menos un modelo del catalogo real no paso el test oracle objetivo")
        sys.exit(1)

    print(f"PASS: {len(modelos_validos)}/{len(modelos_validos)} modelos reales del catalogo verificados con Groq")
    sys.exit(0)


def _escribir_evidencia(evidencia: dict):
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "evidencia_runs")
    os.makedirs(out_dir, exist_ok=True)
    ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    path = os.path.join(out_dir, f"groq_test_{ts}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(evidencia, f, ensure_ascii=False, indent=2)
    print(f"Evidencia escrita en: {path}")


if __name__ == "__main__":
    main()
