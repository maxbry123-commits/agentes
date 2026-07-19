 <universal/orchestrator/conector_chat.py 2>/dev/null
"""
conector_chat.py — Conector HTTP + MCP para que cualquier chat/Mavis se conecte.

Endpoints:
- POST /api/mensaje  → recibe {mensaje, objetivo, user} → orquesta → responde
- POST /api/ejecutar → recibe {objetivo, tareas, metas} → ejecuta DSL completo
- GET  /api/estado  → devuelve estado del orquestador
- GET  /api/tareas  → lista las 5 carpetas de tareas
- POST /api/tarea/<n> → ejecuta tarea N
- GET  /mcp/tools    → expone tools para clientes MCP
- POST /mcp/call    body={name, arguments} → ejecuta tool

Uso:
  python -m orchestrator.conector_chat --port 9090
"""
import os
import sys
import json
import time
import logging
import threading
from typing import Optional, Dict, Any, List
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

# logging básico
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger("orquestador")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import signal
signal.signal(signal.SIGPIPE, signal.SIG_IGN)

try:
    from orchestrator.runtime import (
        RuntimeExecutor, RuntimeState, Node, NodeStatus, UOOS_VERSION
    )
    from orchestrator.router_apis import get_router
    log.info("Imports OK")
except Exception as e:
    log.error(f"Error importando módulos: {e}")
    raise


class OrquestadorActivo:
    def __init__(self):
        self.state: Optional[RuntimeState] = None
        self.executor: Optional[RuntimeExecutor] = None
        self.router = None
        self.historial: list = []
        self.lock = threading.Lock()

    def inicializar(self, n_nodos: int = 5):
        with self.lock:
            if self.state is not None:
                return self.state
            self.state = RuntimeState(proyecto="orquestador-activo", modo="A")
            for i in range(1, n_nodos + 1):
                nid = f"T-{i:03d}"
                node = Node(
                    id=nid,
                    goal=f"objetivo verificable del nodo {i}",
                    contrato_input={},
                    contrato_output={"criterio_exito": "status==ok"},
                    criterio_exito="status==ok",
                    dependencies=[f"T-{i-1:03d}"] if i > 1 else [],
                    risk="bajo",
                    priority=1,
                    skills_requeridas=[],
                    timeout_seg=60,
                )
                self.state.nodos[nid] = node
            self.executor = RuntimeExecutor(self.state)
            self.router = get_router()
            log.info(f"Inicializado: {n_nodos} nodos, "
                    f"APIs: {[a.name for a in self.router.apis]}")
        return self.state

    def ejecutar_objetivo(self, objetivo: str, metas=None, tareas=None) -> dict:
        try:
            with self.lock:
                if self.state is None:
                    self.inicializar(5)
                if self.state.nodos:
                    first_id = sorted(self.state.nodos.keys())[0]
                    self.state.nodos[first_id].goal = objetivo
                boot = self.executor.boot()
                ejecutados = []
                while True:
                    nodo = self.executor.rt_10_select()
                    if nodo is None:
                        break
                    try:
                        result = self._ejecutar_nodo_real(nodo, objetivo)
                    except Exception as e:
                        result = {"status": "error", "error": str(e)[:200]}
                    ejecutados.append({"id": nodo.id, "goal": nodo.goal, "result": result})
                cierre = self.executor.rt_90_cierre()
                respuesta = {
                    "timestamp": time.time(),
                    "objetivo": objetivo,
                    "boot": boot,
                    "ejecutados": ejecutados,
                    "cierre": cierre,
                    "router_status": self.router.status(),
                }
                self.historial.append(respuesta)
                return respuesta
        except Exception as e:
            return {"status": "error", "error": str(e)[:500]}

    def ejecutar_objetivo_async(self, objetivo: str, metas=None, tareas=None) -> str:
        import uuid
        task_id = str(uuid.uuid4())[:8]
        _task_results[task_id] = {"status": "processing"}
        def _run():
            try:
                res = self.ejecutar_objetivo(objetivo, metas=metas, tareas=tareas)
                _task_results[task_id] = {"status": "done", "result": res}
            except Exception as e:
                _task_results[task_id] = {"status": "error", "error": str(e)[:500]}
        t = threading.Thread(target=_run, daemon=True)
        t.start()
        return task_id

    def _ejecutar_nodo_real(self, nodo, objetivo: str) -> dict:
        prompt = f"Objetivo: {objetivo}\nTarea: {nodo.goal}\nID: {nodo.id}"
        system = "Eres un agente worker del orquestador."
        try:
            result = self.router.call(prompt, system=system, max_tokens=2000)
            return result
        except Exception as e:
            return {"status": "error", "error": str(e)[:200]}

    def estado(self) -> dict:
        try:
            if self.state is None:
                self.inicializar(5)
            return {
                "uoos_version": UOOS_VERSION,
                "nodos_total": len(self.state.nodos),
                "nodos_estados": {nid: n.estado for nid, n in self.state.nodos.items()},
                "router": self.router.status() if self.router else {},
                "historial_len": len(self.historial),
            }
        except Exception as e:
            return {"status": "error", "error": str(e)[:500]}


_orq = OrquestadorActivo()
_task_results: dict = {}
_task_counter = [0]


class ChatHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        log.info(f"HTTP {args[0]}")

    def _send_json(self, data, status=200):
        try:
            body = json.dumps(data, indent=2, default=str).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except BrokenPipeError:
            pass
        except Exception as e:
            log.error(f"send_error: {e}")

    def _read_body(self) -> dict:
        try:
            length = int(self.headers.get("Content-Length", 0))
            if length == 0:
                return {}
            raw = self.rfile.read(length)
            return json.loads(raw.decode("utf-8"))
        except Exception as e:
            log.error(f"read_error: {e}")
            return {}

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        try:
            path = urlparse(self.path).path
            if path in ("/", "/index"):
                self._send_json({
                    "name": "Orquestador Universal",
                    "version": UOOS_VERSION,
                    "status": "running",
                    "endpoints": [
                        "GET  /api/estado",
                        "GET  /api/tareas",
                        "POST /api/mensaje  body={objetivo, user}",
                        "POST /api/ejecutar body={objetivo, metas, tareas}",
                        "POST /api/tarea/N  body={descripcion}",
                        "GET  /mcp/tools",
                        "POST /mcp/call    body={name, arguments}",
                    ],
                })
            elif path == "/api/estado":
                self._send_json(_orq.estado())
            elif path == "/api/tareas":
                base = "/opt/orquestador-universal/tareas"
                tareas = []
                for i in range(1, 6):
                    d = f"{base}/tarea_{i}"
                    tareas.append({"id": i, "path": d, "existe": os.path.isdir(d)})
                self._send_json({"tareas": tareas, "base": base})
            elif path == "/api/historial":
                self._send_json({"historial": _orq.historial[-10:]})
            elif path.startswith("/api/task/"):
                tid = path.split("/")[-1]
                if tid in _task_results:
                    self._send_json(_task_results[tid])
                else:
                    self._send_json({"error": "task_not_found", "task_id": tid}, 404)
            elif path == "/mcp/tools":
                self._send_json({
                    "tools": [
                        {"name": "ejecutar_objetivo",
                         "description": "Ejecuta un objetivo en el orquestador",
                         "input_schema": {
                             "type": "object",
                             "properties": {
                                 "objetivo": {"type": "string"},
                                 "metas": {"type": "array", "items": {"type": "string"}},
                             },
                             "required": ["objetivo"],
                         }},
                        {"name": "estado_orquestador",
                         "description": "Estado del orquestador",
                         "input_schema": {"type": "object", "properties": {}}},
                    ]
                })
            elif path == "/health":
                self._send_json({"status": "ok", "ts": time.time()})
            else:
                self._send_json({"error": "not_found", "path": path}, 404)
        except Exception as e:
            log.error(f"GET error: {e}")
            self._send_json({"error": str(e)[:500]}, 500)

    def do_POST(self):
        try:
            path = urlparse(self.path).path
            body = self._read_body()
            if path == "/api/mensaje":
                objetivo = body.get("objetivo") or body.get("mensaje", "")
                user = body.get("user", "anon")
                if not objetivo:
                    self._send_json({"error": "missing objetivo"}, 400)
                    return
                task_id = _orq.ejecutar_objetivo_async(objetivo, metas=body.get("metas"))
                self._send_json({
                    "user": user,
                    "objetivo": objetivo,
                    "respuesta": f"Objetivo recibido y en procesamiento. task_id={task_id}",
                    "task_id": task_id,
                    "status_url": f"/api/tarea/{task_id}",
                })
            elif path == "/api/ejecutar":
                objetivo = body.get("objetivo", "")
                if not objetivo:
                    self._send_json({"error": "missing objetivo"}, 400)
                    return
                result = _orq.ejecutar_objetivo(objetivo,
                    metas=body.get("metas"), tareas=body.get("tareas"))
                self._send_json({"status": "ok", "result": result})
            elif path.startswith("/api/tarea/"):
                try:
                    n = int(path.split("/")[-1])
                except ValueError:
                    self._send_json({"error": "tarea_invalida"}, 400)
                    return
                descripcion = body.get("descripcion", "")
                base = f"/opt/orquestador-universal/tareas/tarea_{n}"
                os.makedirs(base, exist_ok=True)
                with open(f"{base}/descripcion.txt", "w") as f:
                    f.write(descripcion + "\n")
                task_id = _orq.ejecutar_objetivo_async(f"Tarea {n}: {descripcion}")
                with open(f"{base}/task_id.txt", "w") as f:
                    f.write(task_id + chr(10))
                self._send_json({"status": "accepted", "tarea": n, "task_id": task_id})
            elif path == "/mcp/call":
                tool = body.get("name")
                args = body.get("arguments", {})
                if tool == "ejecutar_objetivo":
                    task_id = _orq.ejecutar_objetivo_async(
                        args.get("objetivo", ""), metas=args.get("metas"))
                    self._send_json({"status": "accepted", "task_id": task_id})
                elif tool == "estado_orquestador":
                    self._send_json({"status": "ok", "content": _orq.estado()})
                else:
                    self._send_json({"error": f"unknown tool: {tool}"}, 400)
            else:
                self._send_json({"error": "not_found", "path": path}, 404)
        except Exception as e:
            log.error(f"POST error: {e}")
            self._send_json({"error": str(e)[:500]}, 500)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Conector HTTP del Orquestador")
    parser.add_argument("--port", type=int, default=9090, help="Puerto HTTP")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host")
    args = parser.parse_args()

    log.info(f"Iniciando orquestador en http://{args.host}:{args.port}")
    try:
        # pre-inicializar para detectar errores temprano
        _orq.inicializar(5)
        log.info("Pre-inicialización OK")
        server = ThreadingHTTPServer((args.host, args.port), ChatHandler)
        server.daemon_threads = True
        log.info(f"Servidor HTTP escuchando en {args.host}:{args.port}")
        server.serve_forever()
    except KeyboardInterrupt:
        log.info("Detenido por usuario")
    except Exception as e:
        log.error(f"Error fatal: {e}")
        raise


if __name__ == "__main__":
    main()
root@vmi3428294:~# echo 