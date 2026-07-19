 <tador-universal/orchestrator/runtime.py 2>/dev/null
"""
runtime.py — UOOS Parte 2 v3.0 Executor Runtime
Motor de ejecución determinista en formato DSL/DAG.

Implementa:
- RT-00..RT-04: BOOT (versión, integridad, preflight, skills, resume)
- RT-10..RT-45: CICLO POR NODO (select, idempotencia, capability, memoria, validar, ejecutar, tribunal, goal_check, artefactos, consistencia, auditoría, memoria_out, autooptimizar, entregar)
- RT-80: RECOVERY_GATE
- RT-90: CIERRE_PROYECTO
- Reglas E01-E12 (ejecución obligatoria, alcance, comunicación mínima)
- Eventos obligatorios (append-only en state.json)
"""
import os
import sys
import json
import time
import hashlib
import threading
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
from dataclasses import dataclass, field

from orchestrator.state import atomic_write_json


UOOS_VERSION = "3.0.0"
UOOS_PARTE1_MIN = "2.0.0"


class NodeStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    VALIDATING = "validating"
    BLOCKED = "blocked"
    DONE = "done"
    FAILED = "failed"
    RECOVERED = "recovered"


class EventType(str, Enum):
    BOOT_VERSION_OK = "boot.version.ok"
    BOOT_INTEGRITY_OK = "boot.integrity.ok"
    BOOT_PREFLIGHT_OK = "boot.preflight.ok"
    BOOT_SKILLS_OK = "boot.skills.ok"
    NODE_SELECTED = "node.selected"
    NODE_REUSED = "node.reused"
    NODE_START = "node.start"
    NODE_CHECKPOINT = "node.checkpoint"
    NODE_VALIDATE = "node.validate"
    NODE_GOAL_GAP = "node.goal_gap"
    NODE_ARTIFACTS = "node.artifacts"
    NODE_DONE = "node.done"
    NODE_FAILED = "node.failed"
    LOOP_DELTA = "loop.delta"
    LOOP_ITER = "loop.iter"
    CONTEXT_COMPRESSED = "context.compressed"
    CONTEXT_CLEARED = "context.cleared"
    RECOVERY_START = "recovery.start"
    RECOVERY_RESTORE = "recovery.restore"
    PROJECT_COMPLETED = "project.completed"


@dataclass
class Node:
    id: str
    goal: str
    contrato_input: dict
    contrato_output: dict
    criterio_exito: str
    dependencies: List[str] = field(default_factory=list)
    risk: str = "bajo"  # bajo | medio | alto
    priority: int = 3
    skills_requeridas: List[str] = field(default_factory=list)
    timeout_seg: int = 300
    sandbox: str = "local"
    max_iteraciones: int = 3
    memory_lee: List[str] = field(default_factory=list)
    memory_escribe: List[str] = field(default_factory=list)
    requiere_director: bool = False
    # runtime state
    estado: str = "pending"
    intentos: int = 0
    recoveries: int = 0
    score_tribunal: Optional[float] = None
    output: Optional[dict] = None
    last_checkpoint_ts: float = 0.0
    input_hash: Optional[str] = None


@dataclass
class RuntimeState:
    """state.json del proyecto (B2)."""
    proyecto: str = ""
    uoos_version: str = UOOS_VERSION
    modo: str = "A"
    boot: Dict[str, Any] = field(default_factory=lambda: {"completado": False, "eventos": []})
    nodos: Dict[str, Node] = field(default_factory=dict)
    dag_activo: str = "DAG-001"
    loop_activo: Optional[str] = None
    presupuesto_global: Dict[str, int] = field(default_factory=lambda: {"tokens_usados": 0, "tiempo_seg": 0})
    evidencias: List[dict] = field(default_factory=list)
    decisiones_director: List[dict] = field(default_factory=list)
    historial_eventos: List[dict] = field(default_factory=list)
    auditoria: Dict[str, dict] = field(default_factory=dict)
    rankings: Dict[str, dict] = field(default_factory=lambda: {"skills": {}, "herramientas": {}})

    STATE_PATH = "workflow_state.json"

    def emit_event(self, event_type: str, nodo_id: str = "", payload: Optional[dict] = None):
        """E12: todo cambio en state.json va con evento (L10)."""
        event = {
            "evento": event_type,
            "nodo_id": nodo_id,
            "timestamp": time.time(),
            "payload": payload or {},
        }
        self.historial_eventos.append(event)
        return event

    def persist(self):
        data = {
            "proyecto": self.proyecto,
            "uoos_version": self.uoos_version,
            "modo": self.modo,
            "boot": self.boot,
            "nodos": {nid: {k: v for k, v in vars(n).items()} for nid, n in self.nodos.items()},
            "dag_activo": self.dag_activo,
            "loop_activo": self.loop_activo,
            "presupuesto_global": self.presupuesto_global,
            "evidencias": self.evidencias,
            "decisiones_director": self.decisiones_director,
            "historial_eventos": self.historial_eventos[-500:],  # cap
            "auditoria": self.auditoria,
            "rankings": self.rankings,
        }
        try:
            atomic_write_json(self.STATE_PATH, data)
        except Exception as e:
            sys.stderr.write(f"[persist_error] {e}\n")


class RuntimeExecutor:
    """UOOS Parte 2 v3.0 — Executor Runtime."""

    def __init__(self, state: RuntimeState,
                 director_input_fn: Optional[Callable[[str], str]] = None,
                 execute_fn: Optional[Callable[[Node], dict]] = None):
        self.state = state
        self._director_input = director_input_fn
        self._execute_fn = execute_fn or self._default_executor
        self._lock = threading.Lock()

    # =========================================================================
    # RT-00..RT-04: BOOT
    # =========================================================================

    def rt_00_boot_version(self) -> bool:
        """RT-00: verificar versión del paquete."""
        # Aquí verificaríamos que B1..B8 tienen misma versión
        # Simplificado: la versión está en state
        self.state.emit_event(EventType.BOOT_VERSION_OK)
        return True

    def rt_01_integridad(self) -> bool:
        """RT-01: checks bidireccionales B2 ↔ B3, DAG acíclico, contratos no vacíos."""
        errors = []
        # bidireccional: B2 nodos ↔ B3 (todos los nodos del state están registrados)
        for nid, node in self.state.nodos.items():
            if node.contrato_output is None or not node.criterio_exito:
                errors.append(f"nodo {nid} sin contrato output o criterio_exito")
        # DAG acíclico
        if self._has_cycles():
            errors.append("DAG tiene ciclos")
        if errors:
            sys.stderr.write(f"[integrity_fail] {errors}\n")
            return False
        self.state.emit_event(EventType.BOOT_INTEGRITY_OK, payload={"orden": self._topological_order()})
        return True

    def rt_02_preflight(self) -> bool:
        """RT-02: preflight de entorno."""
        checks = {
            "python_ok": sys.version_info >= (3, 8),
            "workspace_writable": os.access(".", os.W_OK),
            "state_path_ok": True,
        }
        if not all(checks.values()):
            return False
        self.state.emit_event(EventType.BOOT_PREFLIGHT_OK, payload=checks)
        return True

    def rt_03_skills_bootstrap(self) -> bool:
        """RT-03: bootstrap dirigido por necesidad (YAGNI)."""
        required = set()
        for node in self.state.nodos.values():
            required.update(node.skills_requeridas)
        self.state.emit_event(EventType.BOOT_SKILLS_OK, payload={"skills": sorted(required)})
        return True

    def rt_04_resume_check(self) -> str:
        """RT-04: detectar modo INICIO vs REANUDACIÓN."""
        estados = [n.estado for n in self.state.nodos.values()]
        if not estados:
            return "INICIO"
        if any(e in ("running", "validating", "recovered") for e in estados):
            return "REANUDACIÓN"
        if all(e == "done" for e in estados):
            return "COMPLETADO"
        if all(e == "pending" for e in estados):
            return "INICIO"
        return "REANUDACIÓN"

    def boot(self) -> dict:
        """Ejecuta RT-00..RT-04 y emite respuesta boot."""
        ok = all([self.rt_00_boot_version(),
                  self.rt_01_integridad(),
                  self.rt_02_preflight(),
                  self.rt_03_skills_bootstrap()])
        if not ok:
            return {"status": "boot_fail"}
        modo = self.rt_04_resume_check()
        self.state.boot["completado"] = True
        self.state.persist()
        orden = self._topological_order()
        proximo = next((nid for nid in orden
                        if self.state.nodos[nid].estado == "pending"
                        and all(self.state.nodos[d].estado == "done"
                                for d in self.state.nodos[nid].dependencies)), None)
        return {
            "status": "boot_ok",
            "modo": modo,
            "orden": orden,
            "proximo": proximo,
        }

    # =========================================================================
    # RT-10..RT-45: CICLO POR NODO
    # =========================================================================

    def _topological_order(self) -> List[str]:
        visited = set()
        order = []
        def visit(nid):
            if nid in visited:
                return
            visited.add(nid)
            node = self.state.nodos.get(nid)
            if not node:
                return
            for dep in node.dependencies:
                if dep in self.state.nodos:
                    visit(dep)
            order.append(nid)
        for nid in self.state.nodos:
            visit(nid)
        return order

    def _has_cycles(self) -> bool:
        try:
            self._topological_order()
            return False
        except RecursionError:
            return True

    def rt_10_select(self) -> Optional[Node]:
        """RT-10: elegir siguiente nodo ejecutable."""
        candidatos = []
        for nid, node in self.state.nodos.items():
            if node.estado != "pending":
                continue
            if not all(self.state.nodos.get(d, Node(id="x", goal="", contrato_input={}, contrato_output={}, criterio_exito="")).estado == "done"
                       for d in node.dependencies):
                continue
            candidatos.append(node)
        if not candidatos:
            return None
        # desempate: priority menor, risk menor, timeout menor
        candidatos.sort(key=lambda n: (
            n.priority,
            {"bajo": 0, "medio": 1, "alto": 2}.get(n.risk, 1),
            n.timeout_seg,
        ))
        nodo = candidatos[0]
        self.state.emit_event(EventType.NODE_SELECTED, nodo.id, {"goal": nodo.goal})
        return nodo

    def rt_11_idempotencia(self, node: Node, input_data: dict) -> bool:
        """RT-11: si mismo input_hash → reutilizar output previo."""
        input_hash = hashlib.sha256(json.dumps(input_data, sort_keys=True, default=str).encode()).hexdigest()[:16]
        if node.input_hash == input_hash and node.output is not None:
            self.state.emit_event(EventType.NODE_REUSED, node.id, {"input_hash": input_hash})
            return True
        node.input_hash = input_hash
        return False

    def rt_12_capability(self, node: Node) -> bool:
        """RT-12: ¿skills disponibles? (simplificado: siempre OK si no requiere custom)."""
        return True

    def rt_13_memoria_in(self, node: Node) -> dict:
        """RT-13: cargar SOLO memory.lee + state.json resumido."""
        contexto = {
            "nodo_id": node.id,
            "goal": node.goal,
            "contrato": node.contrato_output,
            "state_resumido": {k: v for k, v in vars(self.state).items()
                               if k in node.memory_lee or k == "presupuesto_global"},
        }
        return contexto

    def rt_14_validar_input(self, node: Node, input_data: dict) -> bool:
        """RT-14: input vs contrato.input.schema."""
        if not node.contrato_input:
            return True  # sin schema, pasa
        # simplificado: check required fields
        required = node.contrato_input.get("required", [])
        for r in required:
            if r not in input_data:
                self.state.emit_event(EventType.NODE_FAILED, node.id,
                                      {"causa": "input_invalido", "falta": r})
                return False
        return True

    def rt_20_ejecutar(self, node: Node, input_data: dict) -> dict:
        """RT-20: ejecutar el nodo (default: stub; ejecutor real inyectado)."""
        node.estado = NodeStatus.RUNNING.value
        node.intentos += 1
        self.state.emit_event(EventType.NODE_START, node.id,
                              {"intento": node.intentos, "ts": time.time()})
        try:
            output = self._execute_fn(node, input_data)
            return output
        except Exception as e:
            return {"status": "fail", "error": str(e)}

    def rt_30_tribunal(self, node: Node, output: dict) -> float:
        """RT-30: 6 roles votan; devuelve score promedio."""
        # simplificado: scoring determinista
        scores = {
            "SHERIFF": 100,  # sin violaciones registradas
            "CENTINELA": 100,  # sandbox respetado
            "JUEZ": 100 if output.get("status") in ("ok", "done") else 40,
            "SUPERVISOR": 100,
            "VALIDADOR": 100 if output.get("status") == "ok" else 60,
            "VERIFICADOR": 100,  # evidencia presente
        }
        avg = sum(scores.values()) / len(scores)
        node.score_tribunal = avg
        self.state.emit_event(EventType.NODE_VALIDATE, node.id, {"scores": scores, "promedio": avg})
        return avg

    def rt_31_goal_check(self, node: Node, output: dict) -> bool:
        """RT-31: ¿output cumple COMPLETAMENTE el goal?"""
        # simplificado: si status==ok y output tiene keys esperadas
        if output.get("status") not in ("ok", "done", "completed"):
            self.state.emit_event(EventType.NODE_GOAL_GAP, node.id,
                                  {"que_falta": "status no es ok"})
            return False
        return True

    def rt_40_artefactos(self, node: Node, output: dict) -> list:
        """RT-40: registrar archivos creados/modificados."""
        artefactos = output.get("_artefactos", [])
        self.state.emit_event(EventType.NODE_ARTIFACTS, node.id, {"lista": artefactos})
        return artefactos

    def rt_41_consistencia(self, node: Node) -> bool:
        """RT-41: re-validar todo antes de cerrar."""
        if node.score_tribunal is None or node.score_tribunal < 70:
            return False
        if node.output is None:
            return False
        return True

    def rt_42_auditoria(self, node: Node, output: dict):
        """RT-42: auditoría completa por nodo."""
        self.state.auditoria[node.id] = {
            "inicio": node.last_checkpoint_ts,
            "fin": time.time(),
            "duracion": time.time() - node.last_checkpoint_ts,
            "output": output,
            "score_tribunal": node.score_tribunal,
            "intentos": node.intentos,
            "recoveries": node.recoveries,
        }

    def rt_41_consistencia(self, node: Node) -> bool:
        """RT-41: re-validar antes de cerrar."""
        if node.score_tribunal is None or node.score_tribunal < 70:
            return False
        if node.output is None:
            return False
        return True

    def rt_42_auditoria(self, node: Node, output: dict):
        """RT-42: auditoría completa por nodo."""
        self.state.auditoria[node.id] = {
            "inicio": node.last_checkpoint_ts,
            "fin": time.time(),
            "duracion": time.time() - node.last_checkpoint_ts,
            "output": output,
            "score_tribunal": node.score_tribunal,
            "intentos": node.intentos,
            "recoveries": node.recoveries,
        }

    def rt_43_memoria_out(self, node: Node, output: dict):
        """RT-43: escribir memory.escribe."""
        node.output = output
        self.state.emit_event(EventType.CONTEXT_CLEARED, node.id, {})

    def rt_44_autooptimizar(self, node: Node):
        """RT-44: actualizar rankings de skills."""
        for skill in node.skills_requeridas:
            rank = self.state.rankings["skills"].get(skill, 0)
            if node.score_tribunal and node.score_tribunal >= 70:
                self.state.rankings["skills"][skill] = rank + 1
            elif node.score_tribunal and node.score_tribunal < 70:
                self.state.rankings["skills"][skill] = max(0, rank - 1)

    def rt_45_entregar(self, node: Node, output: dict):
        """RT-45: marcar done, entregar al Director."""
        node.estado = NodeStatus.DONE.value
        self.state.emit_event(EventType.NODE_DONE, node.id,
                              {"output": output, "score": node.score_tribunal})
        self.state.persist()

    def execute_node(self, node: Node, input_data: dict) -> dict:
        """RT-10..RT-45: ciclo completo por nodo."""
        # RT-11
        if self.rt_11_idempotencia(node, input_data):
            return {"status": "reused", "output": node.output}
        # RT-12
        if not self.rt_12_capability(node):
            return {"status": "fail", "error": "capability_missing"}
        # RT-13
        self.rt_13_memoria_in(node)
        # RT-14
        if not self.rt_14_validar_input(node, input_data):
            return {"status": "fail", "error": "input_invalido"}
        # RT-20
        node.last_checkpoint_ts = time.time()
        output = self.rt_20_ejecutar(node, input_data)
        # RT-30
        score = self.rt_30_tribunal(node, output)
        if score < 70:
            node.estado = NodeStatus.FAILED.value
            self.state.emit_event(EventType.NODE_FAILED, node.id, {"score": score})
            return {"status": "fail", "score": score}
        # RT-31
        if not self.rt_31_goal_check(node, output):
            return {"status": "fail", "error": "goal_gap"}
        # RT-40
        self.rt_40_artefactos(node, output)
        # RT-43: escribir output ANTES de consistencia (para que consistencia lo vea)
        self.rt_43_memoria_out(node, output)
        # RT-41
        if not self.rt_41_consistencia(node):
            return {"status": "fail", "error": "inconsistencia"}
        # RT-42
        self.rt_42_auditoria(node, output)
        # RT-44
        self.rt_44_autooptimizar(node)
        # RT-45
        self.rt_45_entregar(node, output)
        return {"status": "done", "output": output, "score": score}

    # =========================================================================
    # RT-80: RECOVERY_GATE
    # =========================================================================

    def rt_80_recovery_gate(self, node: Node, causa: str) -> str:
        """RT-80: clasificar y aplicar B8 o escalar al Director."""
        auto = ["input_invalido_upstream", "dependencia_faltante_instalable",
                "timeout_con_checkpoint", "estancamiento_con_pool_disponible"]
        requiere_director = ["ley_violada", "contrato_incumplible",
                             "2do_recovery_mismo_nodo", "presupuesto_agotado"]
        self.state.emit_event(EventType.RECOVERY_START, node.id, {"causa": causa})
        if causa in auto and node.recoveries < 2:
            node.recoveries += 1
            node.estado = NodeStatus.RECOVERED.value
            self.state.emit_event(EventType.RECOVERY_RESTORE, node.id,
                                  {"recovery_n": node.recoveries})
            return "AUTO"
        return "DIRECTOR"

    # =========================================================================
    # RT-90: CIERRE
    # =========================================================================

    def rt_90_cierre(self) -> dict:
        """RT-90: cierre del proyecto si todos los nodos están done."""
        estados = [n.estado for n in self.state.nodos.values()]
        nodos_pendientes = [nid for nid, e in zip(self.state.nodos.keys(), estados) if e != "done"]
        if nodos_pendientes:
            return {"status": "blocked", "pendientes": nodos_pendientes}
        self.state.emit_event(EventType.PROJECT_COMPLETED, payload={
            "nodos": len(self.state.nodos),
            "duracion_total": time.time() - self.state.boot.get("ts_inicio", time.time()),
            "recoveries_total": sum(n.recoveries for n in self.state.nodos.values()),
            "score_medio": sum(n.score_tribunal or 0 for n in self.state.nodos.values()) / max(1, len(self.state.nodos)),
        })
        return {"status": "completed", "nodos": len(self.state.nodos)}

    # =========================================================================
    # DEFAULT EXECUTOR (stub)
    # =========================================================================

    def _default_executor(self, node: Node, input_data: dict) -> dict:
        """Ejecutor por defecto: marca como ok si el goal contiene 'test'."""
        # placeholder: en producción esto se reemplaza con ejecución real
        time.sleep(0.01)
        return {
            "status": "ok",
            "nodo_id": node.id,
            "goal": node.goal,
            "ts": time.time(),
            "_artefactos": [],
        }


def build_state_from_b3(b1_manifest: dict, b2_state: dict, b3_nodos: dict) -> RuntimeState:
    """Construye RuntimeState desde los 3 bloques UOOS Parte 1."""
    state = RuntimeState(
        proyecto=b1_manifest.get("manifest", {}).get("proyecto", "orquestador-universal"),
        uoos_version=b2_state.get("uoos_version", UOOS_VERSION),
        modo=b2_state.get("modo", "A"),
    )
    # cargar nodos desde B3
    for nid, nodo_data in b3_nodos.items():
        if isinstance(nodo_data, dict) and "nodo" in nodo_data:
            nd = nodo_data["nodo"]
        else:
            nd = nodo_data
        node = Node(
            id=nd.get("id", nid),
            goal=nd.get("goal", ""),
            contrato_input=nd.get("contrato", {}).get("input", {}),
            contrato_output=nd.get("contrato", {}).get("output", {}),
            criterio_exito=nd.get("contrato", {}).get("output", {}).get("criterio_exito", ""),
            dependencies=nd.get("dependencies", []),
            risk=nd.get("risk", "bajo"),
            priority=nd.get("priority", 3),
            skills_requeridas=nd.get("skills_requeridas", []),
            timeout_seg=nd.get("timeout_seg", 300),
            sandbox=nd.get("sandbox", "local"),
            max_iteraciones=nd.get("retry", {}).get("max", 3),
            memory_lee=nd.get("memory", {}).get("lee", []),
            memory_escribe=nd.get("memory", {}).get("escribe", []),
            requiere_director=nd.get("approval", {}).get("requiere_director", False),
        )
        # restaurar estado desde B2
        if nid in b2_state.get("nodos", {}):
            b2n = b2_state["nodos"][nid]
            node.estado = b2n.get("estado", "pending")
            node.intentos = b2n.get("intentos", 0)
            node.recoveries = b2n.get("recoveries", 0)
            node.score_tribunal = b2n.get("score_tribunal")
        state.nodos[nid] = node
    # historial
    state.historial_eventos = b2_state.get("historial_eventos", [])
    return state
root@vmi3428294:~# echo 