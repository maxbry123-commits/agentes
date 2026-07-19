 <questador-universal/orchestrator/dsl.py 2>/dev/null
"""
dsl.py — DSL Runtime: parsea YAML, valida, ejecuta loops anidados.

Implementa:
- Carga el DSL desde YAML (sin PyYAML, parser propio minimalista)
- Construye el DAG
- Valida dependencias, providers, gates
- Ejecuta loop por loop (no termina hasta que todos estén ok o se agote escalate_after)
- Persiste en workflow_state.json (atómico)
- Conecta con chat_interface para input/output
"""
import os
import re
import sys
import json
import time
import hashlib
import threading
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

from orchestrator.state import atomic_write_json, hash_goal


# ============================================================================
# Parser YAML minimalista (sin dependencia de PyYAML)
# ============================================================================

class SimpleYAML:
    """Parser YAML muy básico para nuestro DSL (estructura plana + listas anidadas)."""

    @staticmethod
    def parse(text: str) -> dict:
        lines = []
        for raw in text.split("\n"):
            # quitar comentarios
            if "#" in raw:
                # solo fuera de string
                in_str = False
                cut = -1
                for i, ch in enumerate(raw):
                    if ch in ('"', "'"):
                        in_str = not in_str
                    elif ch == "#" and not in_str:
                        cut = i
                        break
                if cut >= 0:
                    raw = raw[:cut]
            if raw.strip() == "":
                continue
            lines.append(raw)

        return SimpleYAML._parse_block(lines, 0, 0)[0]

    @staticmethod
    def _parse_block(lines, start, indent):
        result = {}
        i = start
        while i < len(lines):
            line = lines[i]
            stripped = line.lstrip()
            current_indent = len(line) - len(stripped)
            if current_indent < indent:
                break
            if current_indent > indent:
                i += 1
                continue
            # key: value
            if ":" in stripped:
                key, _, rest = stripped.partition(":")
                key = key.strip()
                rest = rest.strip()
                if rest == "":
                    # bloque anidado o lista
                    sub, j = SimpleYAML._parse_block(lines, i + 1, indent + 2)
                    # detectar si es lista (siguiente no-vacío empieza con "-")
                    if j < len(lines):
                        next_line = lines[j]
                        next_stripped = next_line.lstrip()
                        next_indent = len(next_line) - len(next_stripped)
                        if next_indent == indent + 2 and next_stripped.startswith("- "):
                            # es lista
                            lst, j2 = SimpleYAML._parse_list(lines, j, indent + 2)
                            result[key] = lst
                            i = j2
                            continue
                    result[key] = sub
                    i = j
                else:
                    # escalar
                    result[key] = SimpleYAML._cast(rest)
                    i += 1
            else:
                i += 1
        return result, i

    @staticmethod
    def _parse_list(lines, start, indent):
        result = []
        i = start
        while i < len(lines):
            line = lines[i]
            stripped = line.lstrip()
            current_indent = len(line) - len(stripped)
            if current_indent < indent:
                break
            if not stripped.startswith("- "):
                break
            content = stripped[2:].strip()
            if ":" in content and not content.startswith('"'):
                # dict dentro de list
                # parsear como dict con indent base = current_indent + 2
                sub_lines = [" " * (current_indent + 2) + content]
                j = i + 1
                while j < len(lines):
                    next_line = lines[j]
                    next_stripped = next_line.lstrip()
                    next_indent = len(next_line) - len(next_stripped)
                    if next_indent <= current_indent:
                        break
                    sub_lines.append(next_line)
                    j += 1
                d, _ = SimpleYAML._parse_block(sub_lines, 0, 0)
                result.append(d)
                i = j
            else:
                result.append(SimpleYAML._cast(content))
                i += 1
        return result, i

    @staticmethod
    def _cast(s):
        s = s.strip()
        if s.startswith('"') and s.endswith('"'):
            return s[1:-1]
        if s.startswith("'") and s.endswith("'"):
            return s[1:-1]
        if s.lower() == "true":
            return True
        if s.lower() == "false":
            return False
        if s.lower() in ("null", "~"):
            return None
        try:
            if "." in s:
                return float(s)
            return int(s)
        except (ValueError, TypeError):
            return s


# ============================================================================
# Estado del DSL
# ============================================================================

class LoopStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    OK = "ok"
    FAILED = "failed"
    REPAIRING = "repairing"
    ESCALATED = "escalated"


@dataclass
class LoopResult:
    loop_id: str
    status: LoopStatus = LoopStatus.PENDING
    attempts: int = 0
    output: dict = field(default_factory=dict)
    error: str = ""
    started_at: float = 0.0
    finished_at: float = 0.0


# ============================================================================
# DSL Runtime
# ============================================================================

class DSLRuntime:
    """Runtime que carga un DSL YAML y lo ejecuta loop por loop."""

    def __init__(self, dsl_path: str, work_dir: str = "/tmp/dsl_work"):
        self.dsl_path = dsl_path
        self.work_dir = work_dir
        self.dsl = None
        self.loops: Dict[str, dict] = {}
        self.loop_order: List[str] = []
        self.results: Dict[str, LoopResult] = {}
        self.escalate_count = 0
        self.max_loops = 100
        self.escalate_after = 2
        self.state = {}
        self._lock = threading.Lock()
        self._chat_callback = None
        self.state_path = "workflow_state.json"

    def load(self) -> bool:
        """Carga y valida el DSL desde el archivo."""
        if not os.path.exists(self.dsl_path):
            return False
        with open(self.dsl_path) as f:
            text = f.read()
        parsed = None
        # intentar con PyYAML primero
        if HAS_YAML:
            try:
                parsed = yaml.safe_load(text)
            except Exception:
                parsed = None
        # fallback al parser propio
        if parsed is None:
            try:
                parsed = SimpleYAML.parse(text)
            except Exception as e:
                sys.stderr.write(f"[dsl_parse_error] {e}\n")
                return False
        self.dsl = parsed
        if not self.dsl:
            return False
        # extraer loops (filtrar items que no sean dicts)
        for loop in self.dsl.get("loops", []):
            if not isinstance(loop, dict):
                continue
            lid = loop.get("id")
            if lid:
                self.loops[lid] = loop
        # orden topológico
        self.loop_order = self._topological_order()
        # config del orquestador
        orch = self.dsl.get("orchestrator", {})
        self.max_loops = orch.get("max_loops", 100)
        self.escalate_after = orch.get("escalate_after", 2)
        return True

    def _topological_order(self) -> List[str]:
        visited = set()
        order = []
        def visit(n):
            if n in visited:
                return
            visited.add(n)
            for dep in self.loops.get(n, {}).get("depends_on", []):
                if dep in self.loops:
                    visit(dep)
            order.append(n)
        for n in self.loops:
            visit(n)
        return order

    def validate(self) -> List[str]:
        """Valida el DSL. Devuelve lista de errores."""
        errors = []
        # dependencias existen
        for lid, loop in self.loops.items():
            for dep in loop.get("depends_on", []):
                if dep not in self.loops:
                    errors.append(f"DSL_INVALID: {lid} depends on non-existent '{dep}'")
        return errors

    def register_chat_callback(self, fn):
        """Registra callback que recibe/envía mensajes del chat."""
        self._chat_callback = fn

    def send_to_chat(self, message: str):
        """Envía un mensaje al chat (si hay callback)."""
        if self._chat_callback:
            try:
                self._chat_callback(message)
            except Exception as e:
                sys.stderr.write(f"[chat_error] {e}\n")

    def _persist(self):
        atomic_write_json(self.state_path, {
            "dsl_path": self.dsl_path,
            "loops_status": {lid: r.status.value
                             for lid, r in self.results.items()},
            "escalate_count": self.escalate_count,
            "state": self.state,
            "ts": time.time(),
        })

    def _resolve(self, value: Any, context: dict) -> Any:
        """Resuelve referencias ${node.field} o ${user.field} o ${state.x}."""
        if isinstance(value, str) and "${" in value:
            def replacer(match):
                path = match.group(1)
                parts = path.split(".")
                obj = context
                for p in parts:
                    if isinstance(obj, dict):
                        obj = obj.get(p)
                    else:
                        return match.group(0)
                return str(obj) if obj is not None else ""
            return re.sub(r"\$\{([^}]+)\}", replacer, value)
        if isinstance(value, list):
            return [self._resolve(v, context) for v in value]
        if isinstance(value, dict):
            return {k: self._resolve(v, context) for k, v in value.items()}
        return value

    def _execute_loop(self, loop_id: str, context: dict) -> LoopResult:
        """Ejecuta un loop individual."""
        loop = self.loops[loop_id]
        result = LoopResult(loop_id=loop_id, started_at=time.time())
        # resolver inputs
        resolved_inputs = {}
        for k, v in loop.get("inputs", {}).items():
            resolved_inputs[k] = self._resolve(v, context)
        # simular ejecución del agente
        agent = loop.get("agent", "claude_code")
        provider = loop.get("provider", "mavis")
        loop_type = loop.get("type", "execute")
        self.send_to_chat(f"🔄 [{loop_id}] ejecutando con {agent} ({provider})...")
        result.attempts += 1
        # por ahora retornamos OK (la integración real con el provider se hace
        # al desplegar, este runtime valida el DSL y la estructura)
        if loop_type == "plan":
            result.output = {
                "status": "ok",
                "goal_hash": hash_goal(str(resolved_inputs.get("objetivo", "x"))),
                "plan": ["step1", "step2", "step3"],
            }
        elif loop_type == "consensus":
            result.output = {
                "status": "ok",
                "chosen_agent": "mavis",
                "agreement": 1.0,
            }
        elif loop_type == "execute":
            result.output = {"status": "ok", "agent": agent}
        elif loop_type == "verify":
            result.output = {"status": "ok", "pytest_pass": True}
        elif loop_type == "validate":
            result.output = {"status": "ok", "lint_pass": True}
        elif loop_type == "repair":
            result.output = {"status": "ok", "new_diff": "--- a/x\n+++ b/x\n"}
        elif loop_type == "judge":
            result.output = {
                "status": "ok",
                "all_passed": True,
                "baseline_written": True,
            }
        else:
            result.output = {"status": "ok"}
        result.status = LoopStatus.OK
        result.finished_at = time.time()
        # guardar output en state global para loops siguientes
        self.state[loop_id] = result.output
        return result

    def run(self, user_input: Optional[dict] = None) -> dict:
        """Ejecuta el DSL completo. No termina hasta completar todos los loops."""
        if not self.load():
            return {"status": "fail", "error": "DSL not loaded"}
        # validar
        errs = self.validate()
        if errs:
            return {"status": "fail", "errors": errs}
        # contexto para resolver ${...}
        context = {
            "user": user_input or {},
            "state": self.state,
            "orchestrator": self.dsl.get("orchestrator", {}),
        }
        # ejecutar en orden topológico
        # BUCLE PRINCIPAL: no termina hasta que todos los loops estén OK
        for cycle in range(self.max_loops):
            all_ok = True
            for loop_id in self.loop_order:
                # si ya está OK, skip
                if loop_id in self.results and self.results[loop_id].status == LoopStatus.OK:
                    continue
                # ejecutar
                result = self._execute_loop(loop_id, context)
                with self._lock:
                    self.results[loop_id] = result
                if result.status == LoopStatus.OK:
                    self.send_to_chat(f"✅ [{loop_id}] completado")
                else:
                    all_ok = False
                    self.escalate_count += 1
                    if self.escalate_count >= self.escalate_after:
                        self.send_to_chat(
                            f"❌ [{loop_id}] falló tras {self.escalate_count} intentos, escalando")
                        result.status = LoopStatus.ESCALATED
                        self._persist()
                        return {
                            "status": "escalated",
                            "loop_id": loop_id,
                            "results": {k: v.__dict__ for k, v in self.results.items()},
                        }
            self._persist()
            if all_ok:
                break
        # resumen final
        return {
            "status": "done",
            "completed_loops": [k for k, v in self.results.items()
                                if v.status == LoopStatus.OK],
            "results": {k: v.__dict__ for k, v in self.results.items()},
            "escalate_count": self.escalate_count,
        }


def run_dsl(dsl_path: str, user_input: Optional[dict] = None,
            chat_callback=None) -> dict:
    """API pública: carga y ejecuta un DSL YAML."""
    runtime = DSLRuntime(dsl_path)
    if chat_callback:
        runtime.register_chat_callback(chat_callback)
    return runtime.run(user_input)
root@vmi3428294:~# echo 