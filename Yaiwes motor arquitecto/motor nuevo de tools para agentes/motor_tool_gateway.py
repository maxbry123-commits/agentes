#!/usr/bin/env python3
"""Motor Tool Gateway: convierte los motores Yaiwes en tools nativos para agentes.
Modos: --emit-tools | --call TOOL --args-json/--args-file | --workflow PLAN --state STATE | --stdio
Stdlib only. Sin credenciales en codigo. Fail-closed. Recuperacion por ledger + reanudacion Range."""
from __future__ import annotations
import argparse, hashlib, json, os, pathlib, re, subprocess, sys, time, urllib.error, urllib.parse, urllib.request

SCHEMA = "yaiwes.tools.gateway.v1"
BASE = pathlib.Path(__file__).resolve().parent
ROOT = BASE.parent
MOTORS = {
    "extract": ROOT / "\u27a1\ufe0f\U0001f4c2 Motor de extracci\u00f3n zip/motor_1_extract_only.py",
    "queue": ROOT / "\U0001f4c2Motor descarga de componentes y extracci\u00f3n de zip/motor_2_queue_download_extract.py",
    "copy": ROOT / "\u27a1\ufe0f\U0001f4c2motor de copiar archivos/motor_3_copy_batches.py",
    "copy_root": ROOT / "\u27a1\ufe0f\U0001f4c2motor de copiar archivos/motor_copy_root_to_repo.py",
    "move": ROOT / "\u27a1\ufe0f\U0001f4c2motor de moves archivos/motor_4_move_batches.py",
}
MIB = 1024 * 1024
GITHUB_HARD_LIMIT = 100 * MIB
PART_DEFAULT = 12 * MIB
HTTP_TIMEOUT = float(os.getenv("FETCH_TIMEOUT_SECONDS", "60"))
MIN_INTERVAL = float(os.getenv("GITHUB_MIN_INTERVAL_SECONDS", "1.0"))
MAX_RETRIES = int(os.getenv("TOOL_MAX_RETRIES", "3"))
STEP_TIMEOUT = int(os.getenv("STEP_TIMEOUT_SECONDS", "3600"))
_last_http = [0.0]

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(MIB), b""): h.update(b)
    return h.hexdigest()

def atomic_json(p, obj):
    p = pathlib.Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, p)

def pace():
    wait = MIN_INTERVAL - (time.time() - _last_http[0])
    if wait > 0: time.sleep(wait)
    _last_http[0] = time.time()

def retry_wait(attempt, headers=None):
    if headers:
        ra = headers.get("Retry-After")
        if ra and str(ra).isdigit(): return min(600, max(1, int(ra)))
        reset = headers.get("X-RateLimit-Reset")
        if reset and str(reset).isdigit(): return min(600, max(1, int(reset) - int(time.time())))
    return min(120, 5 * (2 ** (attempt - 1)))

def is_rate_text(t):
    t = (t or "").lower()
    return any(k in t for k in ("rate_limit", "rate limit", "secondary rate", "429", "too many requests"))

def split_file(path, parts_dir, part_bytes, source_url=""):
    path = pathlib.Path(path); parts_dir = pathlib.Path(parts_dir)
    part_bytes = max(1, min(95 * MIB, int(part_bytes)))
    parts_dir.mkdir(parents=True, exist_ok=True)
    parts = []; total = 0
    with path.open("rb") as f:
        i = 1
        while True:
            b = f.read(part_bytes)
            if not b: break
            p = parts_dir / f"{path.name}.part-{i:04d}"; p.write_bytes(b)
            parts.append({"name": p.name, "bytes": len(b), "sha256": sha256_file(p)}); total += len(b); i += 1
    man = {"schema": SCHEMA, "source_url": source_url, "filename": path.name, "bytes": total,
           "sha256": sha256_file(path), "part_bytes": part_bytes, "parts": parts}
    atomic_json(parts_dir / "manifest.json", man)
    return man

def reassemble(parts_dir, man, out):
    parts_dir = pathlib.Path(parts_dir); out = pathlib.Path(out)
    with out.open("wb") as w:
        for row in man["parts"]:
            p = parts_dir / row["name"]
            if sha256_file(p) != row["sha256"]: raise RuntimeError("PART_HASH_MISMATCH:" + row["name"])
            with p.open("rb") as r:
                for b in iter(lambda: r.read(MIB), b""): w.write(b)
    if sha256_file(out) != man["sha256"]: raise RuntimeError("REASSEMBLY_HASH_MISMATCH")

def fetch_resumable(url, dest_dir, filename=None, part_bytes=PART_DEFAULT, expected_sha256=None, max_retries=MAX_RETRIES):
    dest_dir = pathlib.Path(dest_dir).expanduser(); dest_dir.mkdir(parents=True, exist_ok=True)
    name = filename or urllib.parse.urlsplit(url).path.rstrip("/").split("/")[-1] or "download.bin"
    if not re.fullmatch(r"[A-Za-z0-9._-]{1,120}", name): raise RuntimeError("FETCH_FILENAME_GAP:" + name)
    dest = dest_dir / name; partial = dest_dir / (name + ".partial")
    total = None; attempt = 0
    while attempt < max_retries:
        attempt += 1
        start = partial.stat().st_size if partial.exists() else 0
        headers = {"User-Agent": "YaiwesToolGateway/1.0"}
        if start: headers["Range"] = f"bytes={start}-"
        try:
            pace()
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=HTTP_TIMEOUT) as r:
                if getattr(r, "status", 200) == 200 and start: start = 0
                cr = r.headers.get("Content-Range")
                if cr and cr.rsplit("/", 1)[-1].isdigit(): total = int(cr.rsplit("/", 1)[-1])
                cl = r.headers.get("Content-Length")
                if total is None and cl is not None: total = start + int(cl)
                with partial.open("ab" if start else "wb") as w:
                    while True:
                        b = r.read(MIB)
                        if not b: break
                        w.write(b)
            size = partial.stat().st_size
            if total is not None and size < total: raise IOError(f"incomplete:{size}/{total}")
            break
        except urllib.error.HTTPError as e:
            if e.code == 416 and partial.exists(): break
            if attempt >= max_retries: raise RuntimeError(f"FETCH_HTTP_GAP:{e.code}")
            time.sleep(retry_wait(attempt, e.headers))
        except Exception as e:
            if attempt >= max_retries: raise RuntimeError(f"FETCH_IO_GAP:{type(e).__name__}:{e}")
            time.sleep(retry_wait(attempt))
    if not partial.exists(): raise RuntimeError("FETCH_EMPTY_GAP")
    if expected_sha256 and sha256_file(partial) != expected_sha256:
        partial.unlink(missing_ok=True); raise RuntimeError("FETCH_HASH_MISMATCH")
    os.replace(partial, dest)
    size = dest.stat().st_size
    if size > GITHUB_HARD_LIMIT and int(part_bytes) >= size: raise RuntimeError("GITHUB_FILE_LIMIT_GAP")
    parts_dir = dest_dir / (name + ".parts")
    man = split_file(dest, parts_dir, part_bytes, url)
    rebuilt = dest_dir / (name + ".reassembled")
    reassemble(parts_dir, man, rebuilt); rebuilt.unlink()
    return {"schema": SCHEMA, "tool": "motores_fetch_resumable", "verdict": "VERIFIED_CLOSED",
            "file": str(dest), "bytes": size, "sha256": man["sha256"], "parts": len(man["parts"]),
            "manifest": str(parts_dir / "manifest.json")}

def run_motor(key, env_map, timeout=STEP_TIMEOUT):
    path = MOTORS[key]
    if not path.is_file(): raise RuntimeError("MOTOR_PATH_GAP:" + str(path))
    env = dict(os.environ)
    env.update({k: str(v) for k, v in env_map.items() if v is not None and v != ""})
    p = subprocess.run([sys.executable, str(path)], env=env, text=True,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
    payload = None
    for line in reversed([x.strip() for x in p.stdout.splitlines() if x.strip()]):
        try:
            o = json.loads(line)
            if isinstance(o, dict): payload = o; break
        except json.JSONDecodeError: pass
    if payload is None: raise RuntimeError("MOTOR_NO_JSON_OUTPUT:" + (p.stdout or "")[-1500:])
    return payload

def _s(t="string"): return {"type": t}
TOOLS = {
 "motores_extract_zip": {"description": "Extrae ZIP (fragmentado o no) con CRC, guardas de ruta y read-back.",
  "input_schema": {"type":"object","additionalProperties":False,"required":["archive_input","dest_dir"],
   "properties":{"archive_input":_s(),"dest_dir":_s(),"state_file":_s(),"batch_size":_s("integer")}},
  "motor":"extract","env":{"archive_input":"ARCHIVE_INPUT","dest_dir":"DEST_DIR","state_file":"STATE_FILE","batch_size":"BATCH_SIZE"}},
 "motores_download_queue": {"description": "Descarga en cola un lote de componentes (repo/subcarpeta), parte en trozos, extrae y verifica; publicacion opcional.",
  "input_schema": {"type":"object","additionalProperties":False,"required":["state_file"],
   "properties":{"queue":_s("array"),"queue_file":_s(),"state_file":_s(),"dest_repo":_s(),"dest_branch":_s(),"dest_root":_s(),"index_path":_s(),"max_retries":_s("integer"),"max_items_per_run":_s("integer")}},
  "motor":"queue"},
 "motores_copy_batches": {"description": "Copia lotes de archivos o raices completas con SHA-256, reanudacion y politica de colision.",
  "input_schema": {"type":"object","additionalProperties":False,"required":["source_dir","dest_dir"],
   "properties":{"source_dir":_s(),"dest_dir":_s(),"state_file":_s(),"batch_size":_s("integer"),"collision_policy":_s(),"max_batches":_s("integer")}},
  "motor":"copy","env":{"source_dir":"SOURCE_DIR","dest_dir":"DEST_DIR","state_file":"STATE_FILE","batch_size":"BATCH_SIZE","collision_policy":"COLLISION_POLICY","max_batches":"MAX_BATCHES"}},
 "motores_move_batches": {"description": "Mueve lotes de archivos o raices completas con verificacion antes/despues y reanudacion.",
  "input_schema": {"type":"object","additionalProperties":False,"required":["source_dir","dest_dir"],
   "properties":{"source_dir":_s(),"dest_dir":_s(),"state_file":_s(),"batch_size":_s("integer"),"collision_policy":_s(),"max_batches":_s("integer")}},
  "motor":"move","env":{"source_dir":"SOURCE_DIR","dest_dir":"DEST_DIR","state_file":"STATE_FILE","batch_size":"BATCH_SIZE","collision_policy":"COLLISION_POLICY","max_batches":"MAX_BATCHES"}},
 "motores_copy_root": {"description": "Copia la raiz canonica completa de motores+skill a otro repo validando allowlist y lock de blobs.",
  "input_schema": {"type":"object","additionalProperties":False,"required":["source_root","dest_root","dest_repo_name"],
   "properties":{"source_root":_s(),"dest_root":_s(),"dest_repo_name":_s(),"batch_size":_s("integer")}},
  "motor":"copy_root","env":{"source_root":"SOURCE_ROOT","dest_root":"DEST_ROOT","dest_repo_name":"DEST_REPO_NAME","batch_size":"BATCH_SIZE"}},
 "motores_fetch_resumable": {"description": "Descarga un archivo grande con reanudacion Range, lo divide en partes <=95MiB (limites GitHub), manifiesto SHA-256 y verificacion de reensamblado.",
  "input_schema": {"type":"object","additionalProperties":False,"required":["url","dest_dir"],
   "properties":{"url":_s(),"dest_dir":_s(),"filename":_s(),"part_bytes_mib":_s("integer"),"expected_sha256":_s()}},
  "motor":None},
 "motores_workflow": {"description": "Ejecuta un plan DAG de tools con ledger de recuperacion, reintentos, cooldown por rate-limit y reanudacion.",
  "input_schema": {"type":"object","additionalProperties":False,"required":["plan_file","state_file"],
   "properties":{"plan_file":_s(),"state_file":_s(),"wait":_s("boolean")}},
  "motor":None},
}

def validate_args(tool, args):
    if tool not in TOOLS: raise RuntimeError("UNKNOWN_TOOL:" + str(tool))
    s = TOOLS[tool]["input_schema"]
    if not isinstance(args, dict): raise RuntimeError("ARGS_TYPE_GAP")
    for k in s.get("required", []):
        if k not in args: raise RuntimeError("ARGS_REQUIRED_GAP:" + k)
    checks = {"string": lambda v: isinstance(v, str), "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
              "number": lambda v: isinstance(v, (int, float)), "boolean": lambda v: isinstance(v, bool),
              "array": lambda v: isinstance(v, list), "object": lambda v: isinstance(v, dict)}
    for k, v in args.items():
        if k not in s["properties"]: raise RuntimeError("ARGS_UNKNOWN_GAP:" + k)
        t = s["properties"][k].get("type")
        if t in checks and not checks[t](v): raise RuntimeError("ARGS_TYPE_GAP:" + k)

def dispatch(tool, args):
    validate_args(tool, args)
    spec = TOOLS[tool]
    if tool == "motores_fetch_resumable":
        return fetch_resumable(args["url"], args["dest_dir"], args.get("filename"),
                               int(args.get("part_bytes_mib", 12)) * MIB, args.get("expected_sha256"))
    if tool == "motores_workflow":
        return run_workflow(pathlib.Path(args["plan_file"]), pathlib.Path(args["state_file"]), bool(args.get("wait", False)))
    if tool == "motores_download_queue":
        state_file = pathlib.Path(args["state_file"]).expanduser()
        qf = args.get("queue_file")
        if not qf:
            if not args.get("queue"): raise RuntimeError("ARGS_REQUIRED_GAP:queue|queue_file")
            qf = state_file.parent / "queue.resolved.json"; atomic_json(qf, {"queue": args["queue"]})
        env = {"QUEUE_FILE": qf, "STATE_FILE": state_file, "DEST_REPO": args.get("dest_repo"),
               "DEST_BRANCH": args.get("dest_branch"), "DEST_ROOT": args.get("dest_root"),
               "INDEX_PATH": args.get("index_path"), "MAX_RETRIES": args.get("max_retries"),
               "MAX_ITEMS_PER_RUN": args.get("max_items_per_run")}
        return run_motor("queue", env)
    return run_motor(spec["motor"], {env_k: args.get(a) for a, env_k in spec["env"].items()})

def validate_plan(plan):
    if plan.get("schema") != "yaiwes.tools.workflow.v1": raise RuntimeError("WORKFLOW_SCHEMA_GAP")
    steps = plan.get("steps", [])
    ids = [s.get("id") for s in steps]
    if not steps or len(ids) != len(set(ids)) or any(not i for i in ids): raise RuntimeError("WORKFLOW_IDS_GAP")
    idset = set(ids)
    for s in steps:
        if s.get("tool") not in TOOLS or s["tool"] == "motores_workflow": raise RuntimeError("WORKFLOW_TOOL_GAP:" + str(s.get("tool")))
        if any(n not in idset for n in s.get("needs", [])): raise RuntimeError("WORKFLOW_NEEDS_GAP:" + s["id"])
    done = set()
    while True:
        ready = [s["id"] for s in steps if s["id"] not in done and all(n in done for n in s.get("needs", []))]
        if not ready: break
        done.update(ready)
    if len(done) != len(steps): raise RuntimeError("WORKFLOW_CYCLE_GAP")

def plan_sha(plan): return hashlib.sha256(json.dumps(plan, sort_keys=True, ensure_ascii=False).encode()).hexdigest()

def load_ledger(plan, state_file):
    sha = plan_sha(plan)
    if state_file.exists():
        led = json.loads(state_file.read_text())
        if led.get("plan_sha256") != sha: raise RuntimeError("WORKFLOW_PLAN_CHANGED_GAP")
    else:
        led = {"schema": SCHEMA, "plan_sha256": sha, "steps": {}}
    for s in plan["steps"]:
        st = led["steps"].setdefault(s["id"], {"status": "PENDING", "attempts": 0})
        if st["status"] == "RUNNING": st["status"] = "PENDING"
    return led

def run_workflow(plan_file, state_file, wait=False):
    plan = json.loads(pathlib.Path(plan_file).read_text())
    validate_plan(plan)
    led = load_ledger(plan, state_file)
    steps = {s["id"]: s for s in plan["steps"]}
    while True:
        ready = [s for s in plan["steps"] if led["steps"][s["id"]]["status"] in ("PENDING", "RETRY_PENDING")
                 and all(led["steps"][n]["status"] == "DONE" for n in s.get("needs", []))
                 and led["steps"][s["id"]].get("next_retry_at", 0) <= time.time()]
        if not ready: break
        for s in sorted(ready, key=lambda x: x["id"]):
            st = led["steps"][s["id"]]; maxr = int(s.get("max_retries", MAX_RETRIES))
            st["attempts"] += 1; st["status"] = "RUNNING"; atomic_json(state_file, led)
            try:
                res = dispatch(s["tool"], s.get("args", {}))
                if res.get("verdict") != "VERIFIED_CLOSED": raise RuntimeError("STEP_NOT_CLOSED:" + json.dumps(res, ensure_ascii=False)[-1200:])
                st["status"] = "DONE"; st["result"] = res; st.pop("error", None); st.pop("next_retry_at", None)
            except Exception as e:
                st["error"] = str(e)[-1500:]
                if st["attempts"] >= maxr: st["status"] = "FAILED"
                else:
                    st["status"] = "RETRY_PENDING"
                    delay = retry_wait(st["attempts"]) * (4 if is_rate_text(st["error"]) else 1)
                    if wait: time.sleep(delay)
                    else: st["next_retry_at"] = int(time.time() + delay)
            atomic_json(state_file, led)
    for s in plan["steps"]:
        st = led["steps"][s["id"]]
        if st["status"] in ("PENDING", "RETRY_PENDING") and any(led["steps"][n]["status"] == "FAILED" for n in s.get("needs", [])):
            st["status"] = "BLOCKED"; atomic_json(state_file, led)
    ok = all(led["steps"][i]["status"] == "DONE" for i in steps)
    return {"schema": SCHEMA, "tool": "motores_workflow", "verdict": "VERIFIED_CLOSED" if ok else "GAPS_PENDING",
            "state_file": str(state_file), "steps": {i: led["steps"][i]["status"] for i in steps}}

def stdio_loop():
    for line in sys.stdin:
        line = line.strip()
        if not line: continue
        req = {}
        try:
            req = json.loads(line)
            if req.get("method") == "tools/list":
                resp = {"id": req.get("id"), "ok": True, "result": emit_tools_obj()}
            else:
                resp = {"id": req.get("id"), "ok": True, "result": dispatch(req["tool"], req.get("args", {}))}
        except Exception as e:
            resp = {"id": req.get("id"), "ok": False, "error": str(e)[-1500:]}
        print(json.dumps(resp, ensure_ascii=False, sort_keys=True), flush=True)

def emit_tools_obj():
    return {"schema": SCHEMA, "tools": [{"name": n, "description": t["description"], "input_schema": t["input_schema"]} for n, t in TOOLS.items()]}

def main():
    p = argparse.ArgumentParser(description="Yaiwes Motor Tool Gateway")
    p.add_argument("--emit-tools", action="store_true")
    p.add_argument("--call"); p.add_argument("--args-json", default="{}"); p.add_argument("--args-file")
    p.add_argument("--workflow"); p.add_argument("--state"); p.add_argument("--wait", action="store_true")
    p.add_argument("--stdio", action="store_true")
    a = p.parse_args()
    try:
        if a.emit_tools: print(json.dumps(emit_tools_obj(), ensure_ascii=False, indent=2, sort_keys=True)); return
        if a.stdio: stdio_loop(); return
        if a.workflow:
            if not a.state: raise RuntimeError("ARGS_REQUIRED_GAP:state")
            res = run_workflow(pathlib.Path(a.workflow), pathlib.Path(a.state), a.wait)
        elif a.call:
            args = json.loads(pathlib.Path(a.args_file).read_text()) if a.args_file else json.loads(a.args_json)
            res = dispatch(a.call, args)
        else: raise RuntimeError("MODE_GAP: use --emit-tools|--call|--workflow|--stdio")
        print(json.dumps(res, ensure_ascii=False, sort_keys=True))
        if res.get("verdict") != "VERIFIED_CLOSED": raise SystemExit(1)
    except SystemExit: raise
    except Exception as e:
        print(json.dumps({"schema": SCHEMA, "verdict": "GAP", "detail": str(e)[-1500:]}, ensure_ascii=False, sort_keys=True))
        raise SystemExit(1)

if __name__ == "__main__": main()
