"""
Vectorized Tribunal Engine - PECP-MAXBRY-100x (Nodo T-008)
Orquestador paralelo del tribunal de 6 roles, validación constitucional y de presupuesto.
"""

from typing import Dict, Any, List
import json
from src.tribunal.budget_gate import LLMBudgetGate
from src.tribunal.cross_validator import CrossValidator
from src.tribunal.constitutional import ConstitutionalApprove


class VectorizedTribunal:
    """Orquestador de los 6 roles del Tribunal y compuertas de decisión."""

    def __init__(self) -> None:
        self.budget_gate = LLMBudgetGate()
        self.cross_validator = CrossValidator()
        self.constitutional = ConstitutionalApprove()

    def _evaluate_roles(self, package: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluación de los 6 roles en paralelo/secuencial determinista."""
        # 1. SHERIFF & CENTINELA (Veto gates)
        sheriff_veto = package.get("violates_e_rules", False)
        centinela_veto = package.get("sandbox_escape", False) or package.get("secret_leak", False)

        if sheriff_veto or centinela_veto:
            return {"veto": True, "reason": "SHERIFF_OR_CENTINELA_VETO", "score": 0}

        # 2. JUEZ, SUPERVISOR, VALIDADOR, VERIFICADOR (Scores 0-100)
        juez_score = package.get("juez_score", 90)
        supervisor_score = package.get("supervisor_score", 95)
        validador_score = package.get("validador_score", 85)
        verificador_score = package.get("verificador_score", 90)

        avg_score = int((juez_score + supervisor_score + validador_score + verificador_score) / 4)
        approved_roles = sum(1 for s in [juez_score, supervisor_score, validador_score, verificador_score] if s >= 70)

        return {
            "veto": False,
            "score": avg_score,
            "approved_roles_count": approved_roles
        }

    def evaluate_package(self, package: Dict[str, Any]) -> Dict[str, Any]:
        """
        Criterio PASA:
        score >= 70 AND 4/6 aprueban AND Cross consistent AND LLM-Budget OK AND Constitutional PASS
        """
        roles_eval = self._evaluate_roles(package)
        budget_eval = self.budget_gate.evaluate(package.get("metrics", {}))
        constitutional_eval = self.constitutional.evaluate(package)
        
        cross_eval = self.cross_validator.validate({
            "score_tribunal": roles_eval["score"],
            "status": "PASS" if not roles_eval["veto"] else "FAIL",
            "constitutional_pass": constitutional_eval["constitutional_pass"],
            "llm_budget_ok": budget_eval["passed"]
        })

        # Evaluación de regla general
        passed = (
            not roles_eval["veto"]
            and roles_eval["score"] >= 70
            and roles_eval["approved_roles_count"] >= 4
            and budget_eval["passed"]
            and constitutional_eval["constitutional_pass"]
            and cross_eval["consistent"]
        )

        decision = "PASS" if passed else "FAIL"

        return {
            "nodo_id": "T-008",
            "decision": decision,
            "score_tribunal": roles_eval["score"],
            "constitutional_pass": constitutional_eval["constitutional_pass"],
            "llm_budget_ok": budget_eval["passed"],
            "cross_consistent": cross_eval["consistent"],
            "details": {
                "roles": roles_eval,
                "budget": budget_eval,
                "constitutional": constitutional_eval,
                "cross_validation": cross_eval
            }
        }


if __name__ == "__main__":
    print("=== TEST NODO T-008: VECTORIZED TRIBUNAL ===")
    tribunal = VectorizedTribunal()
    pkg = {
        "juez_score": 90,
        "supervisor_score": 92,
        "validador_score": 88,
        "verificador_score": 95,
        "metrics": {"tokens_llm": 40, "tokens_total": 1000}
    }
    verdict = tribunal.evaluate_package(pkg)
    print(json.dumps(verdict, indent=2))
