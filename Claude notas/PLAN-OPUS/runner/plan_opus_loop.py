"""PLAN OPUS - loop de trabajo de los 5 agentes (paso 0 del Director).

Lee el DAG (PROMPT-DSL-DAG-PLAN-OPUS.yaml), mete sus nodos en la cola durable de Fables
(SQLiteDurableStore, coda workflow persistencias - no se reinventa) y por cada nodo listo:

  ask_consul (cascada del router, consenso) -> ejecuta -> audita -> repara -> re-audita
  -> evidencia sha256 + read-back -> bitacora Crazy Wall -> memoria del agente

Claves: solo por credential_ref del grupo, resueltas desde el banco cifrado (vault.py del
router). Nunca se imprimen ni se escriben. Sin banco: BANDERA B-001 y se sigue.
Nodo bloqueado: BANDERA, se sigue, y al final se vuelve en bucle. R08: 20 intentos max.
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import gzip
import hashlib
import importlib.util
import json
import os
import re
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
PLAN = HERE.parent                                   # Claude notas/PLAN-OPUS
REPO = PLAN.parent.parent
CODA = REPO / "\U0001f4c2coda workflow persistencias" / "Fables enchufe universal"
DAG_FILE = PLAN / "PROMPT-DSL-DAG-PLAN-OPUS.yaml"
BITACORA = PLAN / "CRAZY-WALL-BITACORA-PLAN-OPUS.json"
STATE_DB = PLAN / "estado" / "plan_opus_queue.db"
EVID = PLAN / "evidencia"
ROUTER_RAW = "https://raw.githubusercontent.com/maxbry123-commits/router-universal-router-inteligente-/main/"
NVIDIA = "https://integrate.api.nvidia.com/v1"
MAX_ATTEMPTS = 20                                    # R08 gap ladder
AGENT_TIMEOUT = int(os.environ.get("PLAN_OPUS_AGENT_TIMEOUT", "1500"))

sys.path.insert(0, str(CODA))
from yaiwes_coda_persistence_v8 import SQLiteDurableStore  # noqa: E402  (motor de Fables)


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


# ---------------------------------------------------------------- bitacora (solo anadir)
def bitacora_append(entry: dict) -> str:
    data = json.loads(BITACORA.read_text(encoding="utf-8"))
    entry = {"id": f"E-{len(data['entradas']) + 1:04d}", "fecha": now(), **entry}
    data["entradas"].append(entry)
    BITACORA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return entry["id"]


def last_entry(nodo: str) -> dict | None:
    rows = [e for e in json.loads(BITACORA.read_text(encoding="utf-8"))["entradas"] if e.get("nodo") == nodo]
    return rows[-1] if rows else None


def bandera(node: dict, grupo: dict, agente: str, motivo: str) -> None:
    prev = last_entry(node["id"])
    if prev and prev.get("estado") == "BANDERA" and prev.get("bandera_motivo") == motivo:
        return                                       # no repetir la misma bandera cada hora
    bitacora_append({"objetivo": str(node["objetivo"]), "nodo": node["id"], "agente": agente,
                     "grupo_credential_ref": grupo["credential_ref"], "modelo": None, "ask_consul": None,
                     "accion": node["salida"], "estado": "BANDERA",
                     "evidencia": {"rutas": [], "sha": [], "run_id": os.environ.get("GITHUB_RUN_ID"), "sha256": None},
                     "bandera_motivo": motivo, "revision_claude": None})


def memoria_agente(agente: str, linea: str) -> None:
    p = PLAN / "agentes" / f"README-AGENTE-{agente}.md"
    if p.exists():
        with p.open("a", encoding="utf-8") as fh:
            fh.write(f"- {now()}: {linea}\n")


# ---------------------------------------------------------------- claves por banco
def _download(name: str, url: str) -> Path:
    dst = Path(tempfile.gettempdir()) / name
    if not dst.exists():
        urllib.request.urlretrieve(url, dst)  # noqa: S310 - repo publico del router
    return dst


def resolve_key(credential_ref: str) -> str | None:
    """Abre el banco solo en memoria y devuelve la clave del grupo. None si no hay banco."""
    bank_b64, passphrase = os.environ.get("RIU_TEAM_BANK_B64"), os.environ.get("RIU_TEAM_BANK_PASSPHRASE")
    bank_file = os.environ.get("RIU_TEAM_BANK_FILE")
    if not passphrase or not (bank_b64 or bank_file):
        return None
    vault_py = _download("riu_vault.py", ROUTER_RAW + "Chat%20Mvp/secret_bank/vault.py")
    spec = importlib.util.spec_from_file_location("riu_vault", vault_py)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    raw = Path(bank_file).read_bytes() if bank_file else bank_b64.encode()
    if not raw.startswith(b"SQLite format 3"):
        raw = gzip.decompress(base64.b64decode(raw.strip()))
    tmp = Path(tempfile.mkdtemp()) / "bank.db"
    tmp.write_bytes(raw)
    try:
        return mod.Vault(tmp).unlock(passphrase).get_secret(credential_ref)
    finally:
        tmp.unlink(missing_ok=True)


def chat(key: str, model: str, prompt: str, max_tokens: int = 900, timeout: float = 90) -> str:
    body = {"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens}
    req = urllib.request.Request(NVIDIA + "/chat/completions", data=json.dumps(body).encode(), method="POST",
                                 headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310
        data = json.loads(r.read().decode())
    return ((data.get("choices") or [{}])[0].get("message") or {}).get("content") or ""


# ---------------------------------------------------------------- ask consul
def ask_consul(key: str, router: dict, node: dict, handoff: str) -> dict:
    goal_in = f"Nodo {node['id']} objetivo {node['objetivo']}: {node['salida']}"
    goal_out = f"Entrega verificable: {node.get('archivo') or 'cambio en repo con test'}; PASS solo con evidencia real."
    q = (f"{handoff[:3500]}\n\nGOAL DE ENTRADA: {goal_in}\nGOAL DE SALIDA: {goal_out}\n"
         "Analiza la arquitectura ANTES de ejecutar. Responde SOLO JSON: "
         '{"enfoque": "...", "pasos": ["..."], "riesgos": ["..."], "acceptance": ["..."]}')
    votos = []
    for model in router["cascada_ask_consul"]:
        if "huggingface" in model:
            continue                                  # adicional por HF: sin token HF en este entorno
        try:
            votos.append({"modelo": model, "respuesta": chat(key, model, q, timeout=60)[:3000]})
        except Exception as exc:  # noqa: BLE001 - un modelo caido no para el consenso
            votos.append({"modelo": model, "error": type(exc).__name__})
    ok = [v for v in votos if "respuesta" in v]
    decision = None
    if len(ok) >= 2:
        merge = ("Eres Ask Consul. Estas son propuestas de varios modelos para la misma tarea:\n"
                 + json.dumps(ok, ensure_ascii=False)[:9000]
                 + "\nDevuelve la DECISION POR CONSENSO en maximo 15 lineas: enfoque, pasos numerados, acceptance.")
        decision = chat(key, router["modelo_agentes"], merge, max_tokens=700)
    return {"goal_entrada": goal_in, "goal_salida": goal_out,
            "modelos_consultados": [{k: v for k, v in x.items() if k != "respuesta"} for x in votos],
            "decision_consenso": decision}


# ---------------------------------------------------------------- agentes
def _llm_proxy(key: str, model: str) -> subprocess.Popen:
    """LiteLLM expone formato Anthropic para que Claude Code use el modelo del router."""
    cfg = Path(tempfile.mkdtemp()) / "litellm.yaml"
    cfg.write_text(yaml.safe_dump({"model_list": [{"model_name": "*", "litellm_params": {
        "model": "openai/" + model, "api_base": NVIDIA, "api_key": "os.environ/NVIDIA_API_KEY"}}]}))
    proc = subprocess.Popen(["litellm", "--config", str(cfg), "--port", "4000"],
                            env={**os.environ, "NVIDIA_API_KEY": key},
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(60):
        try:
            socket.create_connection(("127.0.0.1", 4000), timeout=1).close()
            return proc
        except OSError:
            time.sleep(1)
    proc.kill()
    raise RuntimeError("litellm proxy no arranco")


def run_agent(agente: str, prompt: str, key: str, model: str, log: Path) -> int:
    env = {**os.environ, "NVIDIA_API_KEY": key}
    for k in ("RIU_TEAM_BANK_B64", "RIU_TEAM_BANK_PASSPHRASE"):
        env.pop(k, None)                              # el agente nunca ve el banco
    # SALVAGUARDAS: ningun agente corre con las protecciones apagadas. Solo leen/editan
    # archivos y corren tests; sin shell libre ni red propia. Todo cambio termina en un PR
    # que aprueba el Director (ver workflow), nunca directo en main.
    proxy = None
    if agente == "claude_code":
        proxy = _llm_proxy(key, model)
        env.update(ANTHROPIC_BASE_URL="http://127.0.0.1:4000", ANTHROPIC_AUTH_TOKEN="local",
                   ANTHROPIC_MODEL=model, ANTHROPIC_SMALL_FAST_MODEL=model)
        cmd = ["claude", "-p", prompt, "--permission-mode", "acceptEdits", "--allowedTools",
               "Read,Edit,Write,Glob,Grep,Bash(python -m pytest:*),Bash(pytest:*),Bash(git status:*),Bash(git diff:*)"]
    elif agente == "codex":
        home = Path.home() / ".codex"
        home.mkdir(exist_ok=True)
        (home / "config.toml").write_text(
            f'model = "{model}"\nmodel_provider = "nvidia"\n\n[model_providers.nvidia]\n'
            f'name = "NVIDIA"\nbase_url = "{NVIDIA}"\nenv_key = "NVIDIA_API_KEY"\nwire_api = "chat"\n')
        cmd = ["codex", "exec", "--skip-git-repo-check", "--sandbox", "workspace-write", prompt]
    elif agente in ("opencode", "meta_code"):
        cfg = Path.home() / ".config" / "opencode"
        cfg.mkdir(parents=True, exist_ok=True)
        (cfg / "opencode.json").write_text(json.dumps({
            "$schema": "https://opencode.ai/config.json",
            "permission": {"edit": "allow", "webfetch": "deny",
                           "bash": {"*": "deny", "python -m pytest*": "allow", "pytest*": "allow",
                                    "git status*": "allow", "git diff*": "allow"}},
            "provider": {"nvidia": {"npm": "@ai-sdk/openai-compatible", "name": "NVIDIA",
                                    "options": {"baseURL": NVIDIA, "apiKey": "{env:NVIDIA_API_KEY}"},
                                    "models": {model: {}}}}}))
        cmd = ["opencode", "run", "-m", f"nvidia/{model}", prompt]
    elif agente == "openhands":
        # runtime docker (por defecto): los comandos de OpenHands corren dentro de un contenedor aislado
        env.update(LLM_MODEL="openai/" + model, LLM_BASE_URL=NVIDIA, LLM_API_KEY=key,
                   SANDBOX_VOLUMES=f"{REPO}:/workspace:rw")
        cmd = [sys.executable, "-m", "openhands.core.main", "-t", prompt]
    else:
        raise ValueError(agente)
    try:
        with log.open("w", encoding="utf-8") as fh:
            r = subprocess.run(cmd, cwd=REPO, env=env, stdout=fh, stderr=subprocess.STDOUT,
                               timeout=AGENT_TIMEOUT, check=False)
        code = r.returncode
    except FileNotFoundError:
        log.write_text(f"agente {agente} no instalado ({cmd[0]})\n")
        code = 127
    except subprocess.TimeoutExpired:
        with log.open("a", encoding="utf-8") as fh:
            fh.write(f"\nTIMEOUT {AGENT_TIMEOUT}s\n")
        code = 124
    finally:
        if proxy:
            proxy.kill()
    text = log.read_text(encoding="utf-8", errors="replace")
    log.write_text(text.replace(key, "***"), encoding="utf-8")   # la clave nunca queda en evidencia
    return code


def veredicto(log: Path) -> str:
    m = re.findall(r"VEREDICTO:\s*(OK|GAP)", log.read_text(encoding="utf-8", errors="replace"))
    return m[-1] if m else "SIN_VEREDICTO"


# ---------------------------------------------------------------- un nodo
def rol_prompt(system: str, node: dict, agente: str, rol: str, decision: str | None, extra: str = "") -> str:
    base = (f"{system}\nTu nombre: {agente}. Tu rol en este nodo: {rol}.\n"
            f"Nodo {node['id']} (objetivo {node['objetivo']}): {node['salida']}.\n")
    if node.get("archivo"):
        base += f"Archivo de salida obligatorio: {node['archivo']}\n"
    if node.get("plantilla"):
        base += f"Plantilla a seguir: {node['plantilla']}\n"
    for orden in node.get("ordenes_centro", []):
        base += f"ORDEN DEL CENTRO DE CONTROL (manda sobre lo anterior): {orden}\n"
    base += f"DECISION ASK CONSUL:\n{decision}\n{extra}\n"
    if rol == "audita":
        base += ("Revisa lo entregado: existe de verdad (ruta+sha), test real, R01 R02 R03, acceptance literal. "
                 "Una linea por hallazgo OK o GAP. Ultima linea obligatoria: 'VEREDICTO: OK' o 'VEREDICTO: GAP'.")
    if rol == "repara":
        base += "Repara los GAP del informe del auditor, sin codigo desde cero, max 500 LOC, sin borrar archivos."
    return base


def run_node(node: dict, grupo: dict, router: dict, system: str, handoff: str, key: str) -> str:
    run_dir = EVID / f"{node['id']}-{time.strftime('%Y%m%dT%H%M%S')}"
    run_dir.mkdir(parents=True, exist_ok=True)
    model = router["modelo_agentes"]
    if os.environ.get("PLAN_OPUS_NO_SPARSE") != "1":
        for ruta in node.get("rutas", grupo.get("rutas", [])):
            subprocess.run(["git", "sparse-checkout", "add", ruta], cwd=REPO, check=False)
    consul = ask_consul(key, router, node, handoff)
    (run_dir / "ask_consul.json").write_text(json.dumps(consul, ensure_ascii=False, indent=2))
    base = {"objetivo": str(node["objetivo"]), "nodo": node["id"], "grupo_credential_ref": grupo["credential_ref"],
            "modelo": model, "ask_consul": consul}
    if not consul["decision_consenso"]:
        bandera(node, grupo, "ask_consul", "sin consenso: menos de 2 modelos respondieron")
        return "BANDERA"
    bitacora_append({**base, "agente": node["ejecuta"], "accion": node["salida"], "estado": "PLANEADO",
                     "evidencia": {"rutas": [], "sha": [], "run_id": os.environ.get("GITHUB_RUN_ID"), "sha256": None},
                     "bandera_motivo": None, "revision_claude": None})
    logs = []
    ex = run_dir / f"1-ejecuta-{node['ejecuta']}.log"
    rc = run_agent(node["ejecuta"], rol_prompt(system, node, node["ejecuta"], "ejecuta", consul["decision_consenso"]),
                   key, model, ex)
    logs.append(ex)
    au = run_dir / f"2-audita-{node['audita']}.log"
    run_agent(node["audita"], rol_prompt(system, node, node["audita"], "audita", consul["decision_consenso"]),
              key, model, au)
    logs.append(au)
    v = veredicto(au)
    reparador = node.get("repara") or node["audita"]          # Obj 1: Codex audita y repara
    if v != "OK":
        rp = run_dir / f"3-repara-{reparador}.log"
        run_agent(reparador, rol_prompt(system, node, reparador, "repara", consul["decision_consenso"],
                                        "INFORME DEL AUDITOR:\n" + au.read_text(errors="replace")[-6000:]),
                  key, model, rp)
        au2 = run_dir / f"4-reaudita-{node['audita']}.log"
        run_agent(node["audita"], rol_prompt(system, node, node["audita"], "audita", consul["decision_consenso"]),
                  key, model, au2)
        logs += [rp, au2]
        v = veredicto(au2)
    salida = [REPO / a for a in ([node["archivo"]] if isinstance(node.get("archivo"), str) else node.get("archivo", []))]
    if salida:
        archivos_ok = all(p.is_file() and p.stat().st_size > 0 for p in salida)
    else:                                              # R04: sin archivo declarado, exige cambio real de codigo
        st = subprocess.run(["git", "-c", "core.quotepath=off", "status", "--porcelain"], cwd=REPO, capture_output=True, text=True, check=False)
        rutas = node.get("rutas", grupo.get("rutas", []))
        cambios = [ln[3:].strip('"') for ln in st.stdout.splitlines()
                   if "__pycache__" not in ln and not ln.endswith(".pyc")
                   and any(ln[3:].strip('"').startswith(r) for r in rutas)]
        (run_dir / "CAMBIOS.txt").write_text("\n".join(cambios) + "\n", encoding="utf-8")
        salida = [REPO / c.strip('"') for c in cambios if (REPO / c.strip('"')).is_file()]
        archivos_ok = bool(salida)
    estado = "PASS" if (rc == 0 and v == "OK" and archivos_ok) else "GAP"
    evid = logs + [p for p in salida if p.is_file()]
    manifest = {str(p.relative_to(REPO)): sha256_file(p) for p in evid}   # read-back: se relee cada archivo
    (run_dir / "EVIDENCIA.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    bitacora_append({**base, "agente": node["ejecuta"], "accion": node["salida"], "estado": estado,
                     "evidencia": {"rutas": list(manifest), "sha": [], "run_id": os.environ.get("GITHUB_RUN_ID"),
                                   "sha256": sha256_file(run_dir / "EVIDENCIA.json")},
                     "bandera_motivo": None if estado == "PASS" else
                     f"rc_ejecutor={rc} veredicto={v} archivos_salida_ok={archivos_ok}",
                     "revision_claude": None})
    for ag in {node["ejecuta"], node["audita"], reparador}:
        memoria_agente(ag, f"nodo {node['id']} -> {estado} (evidencia {run_dir.name})")
    return estado


# ---------------------------------------------------------------- centro de control
CONTROL = PLAN / "CENTRO-DE-CONTROL.yaml"


def aplicar_centro_de_control(nodes: dict, store: SQLiteDurableStore) -> set[str]:
    """Aplica las ordenes PENDIENTE que dejaron Sonnet / Sol / el Director. Devuelve nodos pausados."""
    if not CONTROL.exists():
        return set()
    ctl = yaml.safe_load(CONTROL.read_text(encoding="utf-8")) or {}
    ordenes = ctl.get("ordenes") or []
    for o in ordenes:
        if o.get("estado") != "PENDIENTE":
            continue
        tipo, nid = o.get("tipo"), o.get("nodo")
        resultado = "APLICADA"
        if tipo == "NUEVO_NODO" and isinstance(o.get("nodo_def"), dict):
            nodes[o["nodo_def"]["id"]] = o["nodo_def"]
            nid = o["nodo_def"]["id"]
            store.enqueue(nid, o["nodo_def"], priority=int(o["nodo_def"]["objetivo"]))
        elif nid not in nodes:
            resultado = "RECHAZADA: nodo no existe"
        elif tipo in ("REACTIVAR", "INSTRUCCION"):
            if tipo == "INSTRUCCION":
                nodes[nid].setdefault("ordenes_centro", []).append(o.get("texto", ""))
            store.enqueue(nid, nodes[nid], priority=int(nodes[nid]["objetivo"]))
            conn = store._connect()
            try:
                conn.execute("UPDATE queue_items SET status='QUEUED', attempts=0, lease_owner=NULL, "
                             "lease_until=NULL, payload_json=? WHERE task_id=?",
                             (json.dumps(nodes[nid], ensure_ascii=False), nid))
            finally:
                conn.close()
        elif tipo not in ("PAUSAR", "REVISION"):
            resultado = f"RECHAZADA: tipo desconocido {tipo}"
        o["estado"], o["aplicada"] = resultado, now()
        bitacora_append({"objetivo": str(nodes.get(nid, {}).get("objetivo", "")), "nodo": nid or "centro",
                         "agente": "centro_control", "grupo_credential_ref": None, "modelo": None,
                         "ask_consul": None, "accion": f"orden {o.get('id')} {tipo} de {o.get('autor')}: {o.get('texto', '')}",
                         "estado": resultado, "evidencia": {"rutas": [], "sha": [], "run_id": os.environ.get("GITHUB_RUN_ID"), "sha256": None},
                         "bandera_motivo": None,
                         "revision_claude": o.get("texto") if tipo == "REVISION" else None})
    CONTROL.write_text(yaml.safe_dump(ctl, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return {o["nodo"] for o in ordenes if o.get("tipo") == "PAUSAR" and o.get("estado") == "APLICADA"
            and not any(x.get("tipo") == "REACTIVAR" and x.get("nodo") == o["nodo"] and x.get("aplicada", "") > o.get("aplicada", "")
                        for x in ordenes)}


# ---------------------------------------------------------------- loop
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--grupo", default="all", help="G1..G4 o all")
    ap.add_argument("--max-nodos", type=int, default=1, help="nodos a ejecutar por grupo en esta vuelta")
    args = ap.parse_args()

    dag = yaml.safe_load(DAG_FILE.read_text(encoding="utf-8"))
    handoff = (PLAN / "HANDOFF-PLAN-OPUS.md").read_text(encoding="utf-8")
    nodes = {n["id"]: n for n in dag["nodos"]}
    store = SQLiteDurableStore(STATE_DB)

    for n in nodes.values():                                    # sembrar la cola durable
        st = store.queue_state(n["id"])
        if st and (st["status"] == "DONE" or st["attempts"] >= MAX_ATTEMPTS):
            continue
        store.enqueue(n["id"], n, priority=int(n["objetivo"]))
        if n.get("estado") == "HECHO" and store.queue_state(n["id"])["status"] != "DONE":
            store.claim("seed", allowed_task_ids=[n["id"]])
            store.finish_queue(n["id"], True)

    pausados = aplicar_centro_de_control(nodes, store)

    def done(nid: str) -> bool:
        st = store.queue_state(nid)
        return bool(st and st["status"] == "DONE")

    grupos = dag["grupos"] if args.grupo == "all" else {args.grupo: dag["grupos"][args.grupo]}
    resumen = {}
    for vuelta in (1, 2):                                        # vuelta 2 = bucle de revision de banderas
        for gid, grupo in grupos.items():
            hechos = resumen.setdefault(gid, [])
            if len(hechos) >= args.max_nodos:
                continue
            candidatos = [n for n in nodes.values()
                          if n["grupo"] == gid and not done(n["id"]) and n["id"] not in pausados]
            listos = [n for n in candidatos if all(done(d) for d in n.get("depende", []))]
            for n in candidatos:
                if n not in listos:
                    faltan = [d for d in n.get("depende", []) if not done(d)]
                    bandera(n, grupo, n["ejecuta"], f"dependencia pendiente: {', '.join(faltan)}")
            if not listos:
                continue
            key = resolve_key(grupo["credential_ref"])
            if not key:
                for n in listos:
                    bandera(n, grupo, n["ejecuta"], "B-001: banco NVIDIA o contrasena no disponibles en este entorno")
                continue
            print(f"::add-mask::{key}")
            for n in listos[: args.max_nodos - len(hechos)]:
                job = store.claim(f"{gid}-{os.getpid()}", allowed_task_ids=[n["id"]], lease_seconds=AGENT_TIMEOUT * 5)
                if not job:
                    continue
                try:
                    estado = run_node(n, grupo, dag["router"], dag["prompt_sistema"], handoff, key)
                except Exception as exc:  # noqa: BLE001 - un nodo roto no para el loop
                    bandera(n, grupo, n["ejecuta"], f"error del runner: {type(exc).__name__}: {str(exc)[:200]}")
                    estado = "BANDERA"
                store.finish_queue(n["id"], estado == "PASS", None if estado == "PASS" else estado)
                hechos.append(f"{n['id']}={estado}")
    print(json.dumps({"fecha": now(), "resumen": resumen}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
