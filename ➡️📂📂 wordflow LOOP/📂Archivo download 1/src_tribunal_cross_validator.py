"""
Cross Validator Module - PECP-MAXBRY-100x (Nodo T-008)
Validación de consistencia lógica cruzada entre múltiples métricas y evidencias.
"""

from typing import Dict, Any, List


class CrossValidator:
    """Verifica la consistencia entre las evidencias entregadas."""

    def validate(self, evidence: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compara campos clave para confirmar consistencia lógica.
        """
        issues: List[str] = []

        # 1. Verificación de hash y estado
        if evidence.get("constitutional_pass") and not evidence.get("llm_budget_ok"):
            issues.append("Constitutional PASS marcado con LLM Budget FAIL")

        # 2. Verificación de score vs pasa
        score: int = evidence.get("score_tribunal", 0)
        if score < 70 and evidence.get("status") == "PASS":
            issues.append(f"Score {score} < 70 no permite estado PASS")

        is_consistent: bool = len(issues) == 0

        return {
            "gate": "CROSS_VALIDATOR",
            "consistent": is_consistent,
            "issues_found": issues
        }


if __name__ == "__main__":
    validator = CrossValidator()
    print("Consistent Test:", validator.validate({"score_tribunal": 85, "status": "PASS", "constitutional_pass": True, "llm_budget_ok": True}))
    print("Inconsistent Test:", validator.validate({"score_tribunal": 50, "status": "PASS", "constitutional_pass": True, "llm_budget_ok": False}))
