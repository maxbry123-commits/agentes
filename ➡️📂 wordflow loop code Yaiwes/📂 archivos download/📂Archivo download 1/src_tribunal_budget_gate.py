"""
LLM Budget Gate Module - PECP-MAXBRY-100x (Nodo T-008)
Validación estricta de ratio de consumo de tokens LLM.
"""

from typing import Dict, Any


class LLMBudgetGate:
    """Valida que el consumo de tokens de LLM no supere la cuota del 10%."""

    MAX_RATIO: float = 0.10  # 10% máximo permitido

    def evaluate(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evalúa el ratio: tokens_llm / tokens_total <= 0.10
        """
        llm_tokens: int = metrics.get("tokens_llm", 0)
        total_tokens: int = metrics.get("tokens_total", 1)

        if total_tokens <= 0:
            total_tokens = 1

        ratio: float = round(llm_tokens / total_tokens, 4)
        passed: bool = ratio <= self.MAX_RATIO

        return {
            "gate": "LLM_BUDGET_GATE",
            "passed": passed,
            "ratio": ratio,
            "max_ratio_allowed": self.MAX_RATIO,
            "tokens_llm": llm_tokens,
            "tokens_total": total_tokens
        }


if __name__ == "__main__":
    gate = LLMBudgetGate()
    print("Test OK Budget:", gate.evaluate({"tokens_llm": 50, "tokens_total": 1000}))
    print("Test Exceed Budget:", gate.evaluate({"tokens_llm": 200, "tokens_total": 1000}))
