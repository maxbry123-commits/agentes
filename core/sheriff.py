 <tador-universal/orchestrator/sheriff.py 2>/dev/null
"""
sheriff.py — 6 gates + Validador + Verificador.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Callable, Any, Optional


class Verdict(str, Enum):
    GO = "GO"
    NO_GO = "NO_GO"


@dataclass
class SheriffVerdict:
    verdict: Verdict
    reason: str = ""


class Validador:
    """Contrato JSON: required_fields + type_map."""

    def validate(self, output: dict, required_fields: List[str],
                 type_map: Optional[Dict[str, type]] = None) -> dict:
        if not isinstance(output, dict):
            return {"valid": False, "missing": ["<output_not_dict>"],
                    "type_errors": []}
        missing = [f for f in required_fields if f not in output]
        type_errors = []
        if type_map:
            for field, expected_type in type_map.items():
                if field in output and not isinstance(output[field], expected_type):
                    type_errors.append(
                        f"{field}: expected {expected_type.__name__}, "
                        f"got {type(output[field]).__name__}")
        return {
            "valid": not missing and not type_errors,
            "missing": missing,
            "type_errors": type_errors,
        }


class Verificador:
    """Ejecuta tests/lint/diff dentro del sandbox. Devuelve {pass, errors[], coverage}."""

    def __init__(self, sandbox=None):
        self.sandbox = sandbox

    def run(self, command: str, timeout: int = 120) -> dict:
        if not self.sandbox:
            return {"pass": False, "errors": ["sandbox_not_attached"],
                    "coverage": 0.0, "duration_s": 0.0}
        result = self.sandbox.exec(command, timeout=timeout)
        passed = result["exit_code"] == 0
        errors = [] if passed else [result["stderr"] or result["stdout"]][-2000:]
        return {
            "pass": passed,
            "errors": errors,
            "coverage": 0.0,
            "duration_s": result["duration_s"],
        }


class Sheriff:
    """6 gates: completitud, coherencia, formato, sandbox_isolation, repairs_ok, approval."""

    GATE_NAMES = ["completitud", "coherencia", "formato",
                  "sandbox_isolation", "repairs_ok", "approval"]

    def __init__(self, sentinel=None):
        self.sentinel = sentinel
        self.gates: Dict[str, Callable] = {
            "completitud":       self._check_completitud,
            "coherencia":        self._check_coherencia,
            "formato":           self._check_formato,
            "sandbox_isolation": self._check_sandbox_isolation,
            "repairs_ok":        self._check_repairs_ok,
            "approval":          self._check_approval,
        }
        self.validador = Validador()
        self.verificador = Verificador()

    def validate(self, output: dict, gate: str, state, node_repair_max: int = 2) -> SheriffVerdict:
        if gate not in self.gates:
            return SheriffVerdict(Verdict.NO_GO, f"Gate '{gate}' no definido")
        return self.gates[gate](output, state, node_repair_max)

    def _check_completitud(self, output, state, _rm) -> SheriffVerdict:
        if not isinstance(output, dict):
            return SheriffVerdict(Verdict.NO_GO, "Output no es dict")
        status = output.get("status")
        if status is None:
            return SheriffVerdict(Verdict.NO_GO, "Falta campo 'status'")
        if status not in ("ok", "completed", "success"):
            return SheriffVerdict(Verdict.NO_GO, f"status='{status}' no válido")
        return SheriffVerdict(Verdict.GO, "completitud_ok")

    def _check_coherencia(self, output, state, _rm) -> SheriffVerdict:
        if not isinstance(output, dict):
            return SheriffVerdict(Verdict.NO_GO, "Output no es dict")
        for k, t in (("tasks", list), ("teams_created", dict),
                     ("document_index", list), ("checks", list),
                     ("simulations", dict)):
            if k in output and not isinstance(output[k], t):
                return SheriffVerdict(Verdict.NO_GO, f"'{k}' debe ser {t.__name__}")
        return SheriffVerdict(Verdict.GO, "coherencia_ok")

    def _check_formato(self, output, state, _rm) -> SheriffVerdict:
        if not isinstance(output, dict):
            return SheriffVerdict(Verdict.NO_GO, "Output no es dict")
        required = output.get("required_fields", [])
        if not isinstance(required, list):
            return SheriffVerdict(Verdict.NO_GO, "'required_fields' debe ser lista")
        missing = [f for f in required if f not in output]
        if missing:
            return SheriffVerdict(Verdict.NO_GO, f"Campos faltantes: {missing}")
        return SheriffVerdict(Verdict.GO, "formato_ok")

    def _check_sandbox_isolation(self, output, state, _rm) -> SheriffVerdict:
        expected_sb = output.get("expected_sandbox_id")
        actual_sb = output.get("sandbox_id")
        if expected_sb and actual_sb and expected_sb != actual_sb:
            return SheriffVerdict(
                Verdict.NO_GO,
                f"Sandbox mismatch: expected={expected_sb} got={actual_sb}")
        return SheriffVerdict(Verdict.GO, "sandbox_isolation_ok")

    def _check_repairs_ok(self, output, state, node_repair_max) -> SheriffVerdict:
        node_id = state.current_node
        if not node_id:
            return SheriffVerdict(Verdict.GO, "no_node_id")
        repair_count = state.repair_counts.get(node_id, 0)
        if repair_count >= node_repair_max:
            return SheriffVerdict(
                Verdict.NO_GO,
                f"repair_count={repair_count} >= max={node_repair_max}")
        return SheriffVerdict(Verdict.GO, f"repairs_ok ({repair_count}/{node_repair_max})")

    def _check_approval(self, output, state, _rm) -> SheriffVerdict:
        node_id = state.current_node
        if not node_id:
            return SheriffVerdict(Verdict.NO_GO, "current_node es None")
        if node_id not in state.approvals:
            return SheriffVerdict(Verdict.NO_GO, f"Sin aprobación para {node_id}")
        if state.approvals[node_id] != "GO":
            return SheriffVerdict(
                Verdict.NO_GO,
                f"Aprobación='{state.approvals[node_id]}' para {node_id}")
        return SheriffVerdict(Verdict.GO, f"approval_ok para {node_id}")
root@vmi3428294:~# echo 