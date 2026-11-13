"""
SDPA v2.0 + FABLES — Universal Plugin Bus v2 Integrated
Capa 10: Plugin Orchestrator con contrato de fichas v2.0

YAIWES G-018 security adaptation.
Original user-upload SHA-256: 5e4595a86bfd68a3c1fde70ba614ce7b9ec6ea4d6c867912e836cca33c626fc3
Dynamic candidate execution was replaced by AST-only inspection.
"""
from __future__ import annotations

import ast
import hashlib
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Set, Tuple

from runtime.src.uek.ficha_contract_v2 import (
    FichaContract, dict_to_ficha, ficha_to_dict, validar, Veredicto,
    Perfil, PresupuestoNivel, Telemetria, Evidencia, Failover, Salud,
    Trazas, Activacion, NIVELES,
)


class PluginStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    FAILED = "FAILED"
    EXPERIMENTAL = "EXPERIMENTAL"
    DEPRECATED = "DEPRECATED"


class ViolationSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"


class EvidenceLevel(str, Enum):
    L1 = "L1_static"
    L2 = "L2_build"
    L3 = "L3_runtime"
    L4 = "L4_feature"


@dataclass(frozen=True)
class ExportedSymbol:
    name: str
    kind: Literal["function", "class", "variable", "constant"]
    signature: str
    doc: str = ""
    is_async: bool = False


@dataclass
class EventDefinition:
    name: str
    direction: Literal["emit", "subscribe"]
    payload_schema: str = "Any"


@dataclass
class EventBinding:
    event_name: str
    handler: Optional[str]
    direction: Literal["emit", "subscribe"]


@dataclass
class ContractViolation:
    field: str
    message: str
    severity: ViolationSeverity
    suggestion: str = ""


@dataclass
class InterfaceContract:
    plugin_id: str
    exports: List[ExportedSymbol] = field(default_factory=list)
    entry_points: List[str] = field(default_factory=list)
    events: List[EventDefinition] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    type_mappings: Dict[str, str] = field(default_factory=dict)
    version: str = "1.0.0"
    fingerprint: str = ""


@dataclass
class NativeInterface:
    wrapper_code: str
    import_path: str
    event_bindings: List[EventBinding] = field(default_factory=list)
    documentation: str = ""


@dataclass
class PluginRegistration:
    plugin_id: str
    status: PluginStatus
    registered_at: datetime
    registered_by: str
    interface_contract: InterfaceContract
    native_interface: NativeInterface
    slot_number: int
    version_history: List[str] = field(default_factory=list)
    merkle_hash: str = ""
    ficha: Optional[FichaContract] = None


@dataclass
class HotSwapResult:
    success: bool
    previous_plugin_id: Optional[str]
    swap_time_ms: float
    fallback_available: bool
    shadow_tests_passed: bool
    message: str = ""


@dataclass
class ContractValidation:
    valid: bool
    violations: List[ContractViolation] = field(default_factory=list)
    compatibility_score: float = 0.0


@dataclass
class ComponentCandidate:
    source_code: str
    language: Literal["python", "rust", "go", "javascript", "wasm"]
    file_paths: List[str] = field(default_factory=list)
    checksum: str = ""


@dataclass
class TargetConventions:
    language: Literal["python", "rust", "go", "javascript"]
    naming_style: Literal["snake_case", "camelCase", "PascalCase"]
    async_style: Literal["async", "sync", "mixed"]
    type_system: Literal["strict", "gradual", "dynamic"]
    max_line_length: int = 88


@dataclass
class ShadowInstance:
    plugin_id: str
    candidate: ComponentCandidate
    slot: int
    loaded_at: datetime
    test_results: List[bool] = field(default_factory=list)


class PluginBusError(Exception):
    pass


class ManifestValidationError(PluginBusError):
    pass


class TribunalNotApprovedError(PluginBusError):
    pass


class HotSwapTimeoutError(PluginBusError):
    pass


class FichaValidationError(PluginBusError):
    pass


class BudgetExceededError(PluginBusError):
    pass


class ContractGenerator:
    def generate(self, candidate: ComponentCandidate) -> InterfaceContract:
        exports = self._extract_exports(candidate)
        return InterfaceContract(
            plugin_id="",
            exports=exports,
            entry_points=candidate.file_paths[:1] or ["__init__.py"],
            events=self._extract_events(candidate),
            dependencies=self._extract_deps(candidate),
            fingerprint=hashlib.sha256(candidate.source_code.encode()).hexdigest()[:16],
        )

    def _extract_exports(self, c: ComponentCandidate) -> List[ExportedSymbol]:
        """Extract public symbols without executing candidate code."""
        if c.language != "python":
            return [ExportedSymbol("main", "function", "(*args, **kwargs) -> Any", "", False)]
        try:
            tree = ast.parse(c.source_code)
        except SyntaxError:
            return [ExportedSymbol("unknown", "function", "(*args, **kwargs) -> Any", "", False)]

        syms: List[ExportedSymbol] = []
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_"):
                args = ast.unparse(node.args) if hasattr(ast, "unparse") else "*args, **kwargs"
                syms.append(
                    ExportedSymbol(
                        node.name,
                        "function",
                        f"({args})",
                        ast.get_docstring(node) or "",
                        isinstance(node, ast.AsyncFunctionDef),
                    )
                )
            elif isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
                syms.append(ExportedSymbol(node.name, "class", "()", ast.get_docstring(node) or "", False))
        return syms

    def _extract_events(self, c: ComponentCandidate) -> List[EventDefinition]:
        return [
            EventDefinition(f"evt_{p[:-1]}", "emit")
            for p in ["emit(", "dispatch(", "trigger(", "notify(", "publish("]
            if p in c.source_code
        ]

    def _extract_deps(self, c: ComponentCandidate) -> List[str]:
        deps: List[str] = []
        if c.language == "python":
            try:
                tree = ast.parse(c.source_code)
            except SyntaxError:
                return deps
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        dep = alias.name.split(".")[0]
                        if dep not in deps:
                            deps.append(dep)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    dep = node.module.split(".")[0]
                    if dep not in deps:
                        deps.append(dep)
        return deps


class AdapterFactory:
    def create(self, candidate: ComponentCandidate, conventions: TargetConventions, contract: InterfaceContract) -> str:
        return self._style(candidate, conventions, contract) if candidate.language == conventions.language else self._bridge(candidate, contract)

    def _style(self, c: ComponentCandidate, conv: TargetConventions, contract: InterfaceContract) -> str:
        lines = [f"# Adapter for {contract.plugin_id}", "from typing import Any", ""]
        for sym in contract.exports:
            an = self._adapt_name(sym.name, conv.naming_style)
            if sym.is_async and conv.async_style == "sync":
                lines.append(f"def {an}{sym.signature}:")
                lines.append(f"    return __import__('asyncio').run(_orig_{sym.name}{sym.signature})")
            else:
                lines.append(f"{an} = _orig_{sym.name}")
        return "\n".join(lines)

    def _bridge(self, c: ComponentCandidate, contract: InterfaceContract) -> str:
        src = c.language
        if src in ("rust", "go", "c"):
            return self._ffi(contract)
        if src == "javascript":
            return self._grpc(contract)
        if src == "wasm":
            return self._wasm(contract)
        return "# Fallback\nfrom typing import Any\ndef _invoke(*args, **kwargs) -> Any:\n    raise NotImplementedError\n"

    def _ffi(self, contract: InterfaceContract) -> str:
        return "import ctypes\nfrom typing import Any\n" + "\n".join(
            f"def {s.name}{s.signature}:\n    return _lib.{s.name}(*args)" for s in contract.exports
        )

    def _grpc(self, contract: InterfaceContract) -> str:
        return "import grpc\nfrom typing import Any\n_channel = grpc.insecure_channel('localhost:50051')\n" + "\n".join(
            f"def {s.name}{s.signature}:\n    return _stub.{s.name}(*args)" for s in contract.exports
        )

    def _wasm(self, contract: InterfaceContract) -> str:
        return "import wasmtime\nfrom typing import Any\n_engine = wasmtime.Engine()\n" + "\n".join(
            f"def {s.name}{s.signature}:\n    return _instance.exports(_store)['{s.name}'](*args)" for s in contract.exports
        )

    def _adapt_name(self, name: str, style: str) -> str:
        if style == "snake_case":
            r: List[str] = []
            for i, ch in enumerate(name):
                if i > 0 and ch.isupper():
                    r.append("_")
                r.append(ch.lower())
            return "".join(r)
        if style == "camelCase":
            p = name.split("_")
            return p[0].lower() + "".join(x.capitalize() for x in p[1:])
        if style == "PascalCase":
            return "".join(p.capitalize() for p in name.split("_"))
        return name


class HotSwapManager:
    MAX_SWAP_MS: float = 100.0

    def __init__(self) -> None:
        self._shadows: Dict[str, ShadowInstance] = {}
        self._lock = threading.RLock()

    def shadow_load(self, plugin_id: str, candidate: ComponentCandidate, slot: int) -> ShadowInstance:
        with self._lock:
            s = ShadowInstance(plugin_id, candidate, slot, datetime.utcnow())
            self._shadows[plugin_id] = s
            return s

    def run_shadow_tests(self, shadow: ShadowInstance) -> bool:
        if not self._test_safe(shadow):
            return False
        return self._test_import(shadow) and self._test_symbols(shadow)

    def atomic_swap(self, old_slot: int, new_slot: int, registry: "PluginRegistry") -> HotSwapResult:
        start = time.perf_counter()
        with self._lock:
            old = registry.get_by_slot(old_slot)
            new = registry.get_by_slot(new_slot)
            if new is None:
                return HotSwapResult(False, old.plugin_id if old else None, (time.perf_counter() - start) * 1000, old is not None, False, "Shadow not found")
            registry._slots[old_slot], registry._slots[new_slot] = new, old
            new.slot_number = old_slot
            if old:
                old.slot_number = new_slot
            elapsed = (time.perf_counter() - start) * 1000
            if elapsed > self.MAX_SWAP_MS:
                raise HotSwapTimeoutError(f"{elapsed:.2f}ms > {self.MAX_SWAP_MS}ms")
            return HotSwapResult(True, old.plugin_id if old else None, elapsed, old is not None, True, "Atomic swap OK")

    def _test_import(self, s: ShadowInstance) -> bool:
        """Syntax-check only; never import/execute candidate source."""
        if s.candidate.language != "python":
            return True
        try:
            ast.parse(s.candidate.source_code)
            return True
        except SyntaxError:
            return False

    def _test_symbols(self, s: ShadowInstance) -> bool:
        return bool(s.candidate.source_code.strip())

    def _test_safe(self, s: ShadowInstance) -> bool:
        if s.candidate.language != "python":
            return True
        try:
            tree = ast.parse(s.candidate.source_code)
        except SyntaxError:
            return False
        forbidden_names = {"eval", "exec", "compile", "__import__"}
        forbidden_attrs = {
            ("os", "system"),
            ("subprocess", "call"),
            ("subprocess", "run"),
            ("subprocess", "Popen"),
        }
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in forbidden_names:
                    return False
                if (
                    isinstance(node.func, ast.Attribute)
                    and isinstance(node.func.value, ast.Name)
                    and (node.func.value.id, node.func.attr) in forbidden_attrs
                ):
                    return False
        return True


class PluginRegistry:
    MAX_HISTORY: int = 3

    def __init__(self) -> None:
        self._plugins: Dict[str, PluginRegistration] = {}
        self._slots: Dict[int, PluginRegistration] = {}
        self._next_slot: int = 1
        self._lock = threading.RLock()
        self._merkle: List[str] = []

    def register(self, plugin_id: str, contract: InterfaceContract, native: NativeInterface, registered_by: str, ficha: Optional[FichaContract] = None) -> PluginRegistration:
        with self._lock:
            if plugin_id in self._plugins and self._plugins[plugin_id].status == PluginStatus.ACTIVE:
                raise PluginBusError(f"{plugin_id} already active")
            slot = self._next_slot
            self._next_slot += 1
            reg = PluginRegistration(plugin_id, PluginStatus.ACTIVE, datetime.utcnow(), registered_by, contract, native, slot, ficha=ficha)
            self._plugins[plugin_id] = reg
            self._slots[slot] = reg
            self._update_merkle()
            return reg

    def update_history(self, pid: str, ver: str) -> None:
        with self._lock:
            r = self._plugins.get(pid)
            if r:
                r.version_history.append(ver)
                if len(r.version_history) > self.MAX_HISTORY:
                    r.version_history.pop(0)
                self._update_merkle()

    def deactivate(self, pid: str) -> None:
        with self._lock:
            r = self._plugins.get(pid)
            if r:
                r.status = PluginStatus.INACTIVE
                self._update_merkle()

    def mark_failed(self, pid: str) -> None:
        with self._lock:
            r = self._plugins.get(pid)
            if r:
                r.status = PluginStatus.FAILED
                self._update_merkle()

    def get(self, pid: str) -> Optional[PluginRegistration]:
        return self._plugins.get(pid)

    def get_by_slot(self, slot: int) -> Optional[PluginRegistration]:
        return self._slots.get(slot)

    def list_active(self) -> List[PluginRegistration]:
        return [p for p in self._plugins.values() if p.status == PluginStatus.ACTIVE]

    def has_active_deps(self, pid: str) -> bool:
        return any(pid in p.interface_contract.dependencies for p in self.list_active() if p.plugin_id != pid)

    def _update_merkle(self) -> None:
        rows = [f"{pid}:{reg.status}:{reg.version_history}" for pid, reg in sorted(self._plugins.items())]
        digest = hashlib.sha256("\n".join(rows).encode()).hexdigest()
        self._merkle.append(digest)


class CostGovernor:
    def __init__(self) -> None:
        self._used_tokens: int = 0
        self._used_ms: int = 0
        self._used_cost: float = 0.0

    def check_budget(self, nivel: str, presupuesto: PresupuestoNivel) -> bool:
        if presupuesto.max_tokens and self._used_tokens > presupuesto.max_tokens:
            return False
        if presupuesto.max_ms and self._used_ms > presupuesto.max_ms:
            return False
        if presupuesto.max_costo_usd and self._used_cost > presupuesto.max_costo_usd:
            return False
        return True


class TelemetryEmitter:
    def __init__(self) -> None:
        self._spans: List[Dict[str, Any]] = []

    def emit_span(self, name: str, plugin_id: str, duration_ms: float) -> None:
        self._spans.append({"type": "span", "name": name, "plugin_id": plugin_id, "duration_ms": duration_ms, "ts": datetime.utcnow().isoformat()})

    def emit_metric(self, plugin_id: str, metric: str, value: Any) -> None:
        self._spans.append({"type": "metric", "plugin_id": plugin_id, "metric": metric, "value": value, "ts": datetime.utcnow().isoformat()})

    def get_spans(self) -> List[Dict[str, Any]]:
        return list(self._spans)


class EvidenceCollector:
    def __init__(self) -> None:
        self._records: Dict[str, List[Dict[str, Any]]] = {}

    def collect(self, plugin_id: str, level: EvidenceLevel, data: Any) -> None:
        self._records.setdefault(plugin_id, []).append({"level": level.value, "data": data})

    def get(self, plugin_id: str) -> List[Dict[str, Any]]:
        return list(self._records.get(plugin_id, []))


class HealthMonitor:
    def __init__(self) -> None:
        self._heartbeats: Dict[str, datetime] = {}
        self._lock = threading.RLock()

    def heartbeat(self, plugin_id: str) -> None:
        with self._lock:
            self._heartbeats[plugin_id] = datetime.utcnow()

    def is_healthy(self, plugin_id: str, interval_s: int = 30) -> bool:
        with self._lock:
            last = self._heartbeats.get(plugin_id)
            return last is not None and (datetime.utcnow() - last).total_seconds() < interval_s

    def check_all(self, registry: PluginRegistry, default_interval: int = 30) -> Dict[str, bool]:
        return {
            p.plugin_id: self.is_healthy(p.plugin_id, p.ficha.salud.heartbeat_interval_s if p.ficha else default_interval)
            for p in registry.list_active()
        }


class FailoverManager:
    def __init__(self) -> None:
        self._chains: Dict[str, List[str]] = {}
        self._lock = threading.RLock()

    def register_chain(self, plugin_id: str, chain: List[str]) -> None:
        with self._lock:
            self._chains[plugin_id] = chain

    def get_fallback(self, plugin_id: str, registry: PluginRegistry) -> Optional[str]:
        with self._lock:
            for fallback in self._chains.get(plugin_id, []):
                r = registry.get(fallback)
                if r and r.status == PluginStatus.ACTIVE:
                    return fallback
            return None


class UniversalPluginBus:
    def __init__(self) -> None:
        self.contract_generator = ContractGenerator()
        self.adapter_factory = AdapterFactory()
        self.hot_swap = HotSwapManager()
        self.registry = PluginRegistry()
        self.cost_governor = CostGovernor()
        self.telemetry = TelemetryEmitter()
        self.evidence = EvidenceCollector()
        self.health = HealthMonitor()
        self.failover = FailoverManager()
        self._tribunal_approvals: Set[str] = set()
        self._event_bus: List[Dict[str, Any]] = []
        self._lock = threading.RLock()

    def add_tribunal_approval(self, case_id: str) -> None:
        with self._lock:
            self._tribunal_approvals.add(case_id)

    def is_tribunal_approved(self, case_id: str) -> bool:
        with self._lock:
            return case_id in self._tribunal_approvals

    def enchufar(self, manifest: Dict[str, Any], candidate: ComponentCandidate, conventions: TargetConventions, registered_by: str = "tribunal") -> PluginRegistration:
        """Enchufa un plugin validando Ficha v2.0 without executing candidate code."""
        t0 = time.perf_counter()
        veredicto = validar(manifest)
        if not veredicto.valido:
            self.evidence.collect(manifest.get("artifact_id", "unknown"), EvidenceLevel.L1, f"Ficha invalida: {veredicto.errores}")
            raise FichaValidationError(f"Ficha v2.0 invalida: {veredicto.errores}")
        ficha = dict_to_ficha(veredicto.ficha_normalizada or {})

        if not self.is_tribunal_approved(manifest.get("tribunal_case_id", "")):
            raise TribunalNotApprovedError(manifest.get("tribunal_case_id", ""))
        pid = ficha.artifact_id
        if self.registry.get(pid) and self.registry.get(pid).status == PluginStatus.ACTIVE:
            raise PluginBusError(f"{pid} already active")

        shadow = self.hot_swap.shadow_load(pid, candidate, self.registry._next_slot)
        if not self.hot_swap.run_shadow_tests(shadow):
            raise PluginBusError("STATIC_SHADOW_VALIDATION_FAILED")

        presupuesto = ficha.presupuesto.get("n0", PresupuestoNivel())
        if not self.cost_governor.check_budget("n0", presupuesto):
            raise BudgetExceededError(f"Presupuesto n0 excedido para {pid}")

        contract = self.contract_generator.generate(candidate)
        contract.plugin_id = pid
        val = self.verify_contract(contract, conventions)
        if not val.valid:
            raise PluginBusError(f"Contract invalid: {val.violations}")
        adapter = self.adapter_factory.create(candidate, conventions, contract)
        native = NativeInterface(
            wrapper_code=f"# Native for {pid}\n{adapter}\n",
            import_path=f"sdpa.plugins.{pid}",
            event_bindings=[EventBinding(evt.name, None, evt.direction) for evt in contract.events],
            documentation="\n".join([f"- `{s.name}`: {s.kind}" for s in contract.exports]),
        )

        reg = self.registry.register(pid, contract, native, registered_by, ficha=ficha)
        self.registry.update_history(pid, ficha.version)
        if ficha.failover.sustituible_por:
            self.failover.register_chain(pid, ficha.failover.sustituible_por)
        self.evidence.collect(pid, EvidenceLevel.L2, {"contract": contract.fingerprint, "adapter_len": len(adapter)})
        self.telemetry.emit_span("enchufar", pid, (time.perf_counter() - t0) * 1000)
        self.telemetry.emit_metric(pid, "registry_size", len(self.registry._plugins))
        self._emit_event("kernel.v2.plugin.enchufed", {"plugin_id": pid, "version": ficha.version, "categoria": ficha.categoria, "etapa": ficha.etapa})
        return reg

    def verify_contract(self, contract: InterfaceContract, conventions: TargetConventions) -> ContractValidation:
        violations: List[ContractViolation] = []
        score = 1.0
        if not contract.exports:
            violations.append(ContractViolation("exports", "No exports", ViolationSeverity.CRITICAL, "Expose at least one symbol"))
            score -= 0.5
        for sym in contract.exports:
            if conventions.naming_style == "snake_case" and any(ch.isupper() for ch in sym.name):
                violations.append(ContractViolation(f"export.{sym.name}", "Not snake_case", ViolationSeverity.WARNING, f"Rename to {sym.name.lower()}"))
                score -= 0.05
            if conventions.async_style == "sync" and sym.is_async:
                violations.append(ContractViolation(f"export.{sym.name}", "Async in sync", ViolationSeverity.CRITICAL, "Wrap adapter"))
                score -= 0.2
        return ContractValidation(not any(v.severity == ViolationSeverity.CRITICAL for v in violations), violations, max(0.0, score))

    def get_plugin_profile(self, plugin_id: str, nivel: str) -> Optional[Perfil]:
        reg = self.registry.get(plugin_id)
        return reg.ficha.perfiles.get(nivel) if reg and reg.ficha else None

    def check_plugin_health(self, plugin_id: str) -> bool:
        reg = self.registry.get(plugin_id)
        interval = reg.ficha.salud.heartbeat_interval_s if reg and reg.ficha else 30
        return self.health.is_healthy(plugin_id, interval)

    def trigger_plugin(self, plugin_id: str, event_type: str, payload: Dict[str, Any]) -> bool:
        reg = self.registry.get(plugin_id)
        if not reg or not reg.ficha:
            return False
        act = reg.ficha.activacion
        if event_type in act.eventos:
            return True
        if any(ww in str(payload) for ww in act.wake_words):
            return True
        return False

    def desenchufar(self, plugin_id: str, reason: str) -> HotSwapResult:
        reg = self.registry.get(plugin_id)
        if reg is None:
            return HotSwapResult(False, None, 0.0, False, False, f"{plugin_id} not found")
        if self.registry.has_active_deps(plugin_id):
            reg.status = PluginStatus.DEPRECATED
            self._emit_event("kernel.v2.plugin.deprecated", {"plugin_id": plugin_id, "reason": reason})
            return HotSwapResult(False, plugin_id, 0.0, True, False, f"Deps active; DEPRECATED: {reason}")
        t0 = time.perf_counter()
        self.registry.deactivate(plugin_id)
        self.evidence.collect(plugin_id, EvidenceLevel.L3, f"Desenchufed: {reason}")
        elapsed = (time.perf_counter() - t0) * 1000
        self._emit_event("kernel.v2.plugin.desenchufed", {"plugin_id": plugin_id, "reason": reason})
        return HotSwapResult(True, plugin_id, elapsed, True, True, f"Desenchufed: {reason}")

    def upgrade(self, plugin_id: str, manifest: Dict[str, Any], candidate: ComponentCandidate, conventions: TargetConventions) -> HotSwapResult:
        old = self.registry.get(plugin_id)
        if old is None:
            raise PluginBusError(f"{plugin_id} not found")
        veredicto = validar(manifest)
        if not veredicto.valido:
            raise FichaValidationError(str(veredicto.errores))
        shadow = self.hot_swap.shadow_load(plugin_id + ".shadow", candidate, self.registry._next_slot)
        if not self.hot_swap.run_shadow_tests(shadow):
            return HotSwapResult(False, plugin_id, 0.0, True, False, "Shadow validation failed")
        contract = self.contract_generator.generate(candidate)
        contract.plugin_id = plugin_id + ".shadow"
        native = NativeInterface(self.adapter_factory.create(candidate, conventions, contract), f"sdpa.plugins.{plugin_id}.shadow")
        new_ficha = dict_to_ficha(veredicto.ficha_normalizada or {})
        shadow_reg = self.registry.register(plugin_id + ".shadow", contract, native, "upgrade", ficha=new_ficha)
        return self.hot_swap.atomic_swap(old.slot_number, shadow_reg.slot_number, self.registry)

    def _emit_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        self._event_bus.append({"type": event_type, "payload": payload, "timestamp": datetime.utcnow().isoformat()})


def _valid_test_manifest(case_id: str = "CASE-001", artifact_id: str = "sdpa.plugins.test") -> Dict[str, Any]:
    return {
        "artifact_id": artifact_id,
        "version": "1.0.0",
        "estado": "active",
        "contract_hash": "sha256:" + "a" * 64,
        "tribunal_case_id": case_id,
        "contrato": {
            "rol": "transform",
            "consume": {"datatype": {"family": "text", "type": "string", "version": 1}},
            "expone": {"datatype": {"family": "text", "type": "string", "version": 1}},
        },
        "ejecucion": {"kind": "code", "transport": "importlib", "runtime_type": "compute", "idempotente": True},
        "seguridad": {"sandbox": "process", "limites": {"timeout_ms": 5000}},
        "firma": {"gpg_key_id": "ABC123"},
        "categoria": "pipeline",
        "etapa": "P",
        "perfiles": {"n0": {"habilitada": True, "iteraciones": 1, "simulaciones": 0, "criticas": 0, "muestras_k": 1}},
        "presupuesto": {"n0": {"max_tokens": 10000, "max_ms": 5000, "max_costo_usd": 0.1}},
        "telemetria": {"metricas": ["tiempo", "errores"], "span_otel": True},
        "evidencia": {"produce": ["L2_build", "L3_runtime"], "destino": "runtime/evidence/"},
        "failover": {"sustituible_por": [], "compensacion": ""},
        "salud": {"metodo": "ping", "heartbeat_interval_s": 30},
        "activacion": {"eventos": ["kernel.v2.plugin.enchufed"]},
    }


def _run_tests() -> None:
    bus = UniversalPluginBus()
    bus.add_tribunal_approval("CASE-001")
    ficha_dict = _valid_test_manifest()
    candidate = ComponentCandidate("def hello(): return 42", "python")
    conventions = TargetConventions("python", "snake_case", "sync", "gradual")

    reg = bus.enchufar(ficha_dict, candidate, conventions)
    assert reg.status == PluginStatus.ACTIVE
    assert reg.plugin_id == "sdpa.plugins.test"
    assert reg.ficha is not None
    assert reg.ficha.categoria == "pipeline"
    assert reg.ficha.etapa == "P"
    assert bus.get_plugin_profile("sdpa.plugins.test", "n0") is not None
    assert any(s["name"] == "enchufar" for s in bus.telemetry.get_spans() if s["type"] == "span")
    assert any(e["level"] == "L2_build" for e in bus.evidence.get("sdpa.plugins.test"))
    assert not bus.check_plugin_health("sdpa.plugins.test")
    bus.health.heartbeat("sdpa.plugins.test")
    assert bus.check_plugin_health("sdpa.plugins.test")
    assert bus.trigger_plugin("sdpa.plugins.test", "kernel.v2.plugin.enchufed", {})

    unsafe = bus.hot_swap.shadow_load(
        "sdpa.plugins.unsafe",
        ComponentCandidate("exec('raise RuntimeError(\"MUST_NOT_RUN\")')", "python"),
        999,
    )
    assert bus.hot_swap.run_shadow_tests(unsafe) is False

    res = bus.desenchufar("sdpa.plugins.test", "cleanup")
    assert res.success
    assert bus.registry.get("sdpa.plugins.test").status == PluginStatus.INACTIVE

    bad = dict(ficha_dict)
    bad["categoria"] = "acelerador"
    bad["etapa"] = "P"
    try:
        bus2 = UniversalPluginBus()
        bus2.add_tribunal_approval("CASE-001")
        bus2.enchufar(bad, candidate, conventions)
        raise AssertionError("Debería haber fallado")
    except FichaValidationError as ex:
        assert "V03" in str(ex)

    bus3 = UniversalPluginBus()
    bus3.add_tribunal_approval("CASE-002")
    f2 = _valid_test_manifest("CASE-002", "sdpa.plugins.upg")
    bus3.enchufar(f2, ComponentCandidate("def compute(): return 1", "python"), conventions)
    f3 = dict(f2)
    f3["version"] = "2.0.0"
    up = bus3.upgrade("sdpa.plugins.upg", f3, ComponentCandidate("def compute(): return 2", "python"), conventions)
    assert up.success
    assert up.swap_time_ms < 100.0

    print("[UniversalPluginBusV2Integrated] All tests passed.")


if __name__ == "__main__":
    _run_tests()
