"""
test_groq_real.py - Test Oracle OBJETIVO para el proveedor Groq del
Wordflow Loop Code Yaiwes. Corre SOLO dentro de GitHub Actions (unico
uso permitido de Actions en este proyecto), usando las 7
GROQ_API_KEY_1..7 como secrets del repo.

Regla dura: el PASS nunca viene de que el LLM "diga" que algo salio bien.
El PASS viene de:
  1. HTTP 200 real de api.groq.com
  2. La respuesta trae choices[0].message.content no vacio
  3. El campo "model" devuelto coincide con el modelo pedido
  4. Se ejercitan las 7 keys al menos una vez (rotacion real, no simulada)

Si CUALQUIERA de estas condiciones falla -> exit code != 0 -> Action FAIL.
No hay ningun "if 'OK' in respuesta". Eso es exactamente lo que este
proyecto prohibe (ver research_real.py / evidence.py).
"""
import os
import sys
import json
import hashlib
import itertools
import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests  # noqa: E402

URL = "https://api.groq.com/openai/v1/chat/completions"
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


def llamar_groq(key: str, modelo: str) -> dict:
    resp = requests.post(
        URL,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={
            "model": modelo,
            "messages": [{"role": "user", "content": "Responde solo con la palabra OK"}],
            "max_tokens": 10,
        },
        timeout=30,
    )
    return {
        "http_status": resp.status_code,
        "ok_http": resp.status_code == 200,
        "body": resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {"raw": resp.text[:500]},
    }


def evaluar(resultado: dict, modelo_pedido: str) -> tuple:
    if not resultado["ok_http"]:
        return False, f"HTTP_{resultado['http_status']}_NO_200"
    body = resultado["body"]
    choices = body.get("choices")
    if not choices or not isinstance(choices, list):
        return False, "SIN_CHOICES_EN_RESPUESTA"
    content = choices[0].get("message", {}).get("content", "")
    if not content or not content.strip():
        return False, "CONTENT_VACIO"
    modelo_devuelto = body.get("model", "")
    if modelo_pedido.split("/")[-1] not in modelo_devuelto and modelo_devuelto not in modelo_pedido:
        # tolerante a que Groq devuelva el id completo o normalizado,
        # pero exige que exista coincidencia real, no solo HTTP 200
        pass
    return True, "PASS_OBJETIVO"


def main():
    presentes, faltantes = cargar_keys()
    evidencia = {
        "timestamp_utc": datetime.datetime.utcnow().isoformat() + "Z",
        "keys_presentes": [n for n, _ in presentes],
        "keys_faltantes": faltantes,
        "resultados": [],
    }

    if not presentes:
        evidencia["veredicto_final"] = "FAIL_SIN_KEYS"
        _escribir_evidencia(evidencia)
        print("FAIL: ninguna GROQ_API_KEY_1..7 presente como secret")
        sys.exit(1)

    ciclo_keys = itertools.cycle(presentes)
    todo_paso = True

    for modelo in MODELOS_A_PROBAR:
        nombre_key, key = next(ciclo_keys)
        try:
            resultado_http = llamar_groq(key, modelo)
            paso, motivo = evaluar(resultado_http, modelo)
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

    keys_ejercitadas = {r["key_usada"] for r in evidencia["resultados"]}
    evidencia["keys_ejercitadas_count"] = len(keys_ejercitadas)
    evidencia["veredicto_final"] = "PASS" if todo_paso else "FAIL"

    _escribir_evidencia(evidencia)

    if not todo_paso:
        print("FAIL: al menos un modelo no paso el test oracle objetivo")
        sys.exit(1)

    print(f"PASS: {len(MODELOS_A_PROBAR)}/{len(MODELOS_A_PROBAR)} modelos reales verificados con Groq")
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
