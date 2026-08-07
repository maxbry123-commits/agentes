from dataclasses import dataclass
from typing import Literal

RiskLevel = Literal["normal", "sheriff_check", "quarantine"]


@dataclass(frozen=True)
class ContractDecision:
    contracts: tuple[str, ...]
    risk_score: int
    risk_level: RiskLevel
    allowed: bool
    reason: str


class ContractRouter:
    """Selector determinista de contratos (SOURCE: SALIDA_1_CAPA_CONTROL_PARTE_3 §42).

    INPUT → Classifier → Threat Analyzer → Contract Compiler → Sheriff
    El LLM nunca selecciona contratos.
    """

    # risk weights
    DATA = {"public": 0, "internal": 2, "secret": 5}
    OP = {"read": 1, "write": 3, "delete": 5}
    EXT = {"none": 0, "api": 3, "unknown": 5}

    def classify(
        self,
        operation: str,
        data_sensitivity: str = "internal",
        external: str = "none",
    ) -> ContractDecision:
        score = (
            self.DATA.get(data_sensitivity, 2)
            + self.OP.get(operation, 3)
            + self.EXT.get(external, 0)
        )

        if score <= 3:
            level: RiskLevel = "normal"
            contracts = ("C_BASIC",)
            allowed = True
        elif score <= 7:
            level = "sheriff_check"
            contracts = ("C_BASIC", "C_SHERIFF")
            allowed = True
        else:
            level = "quarantine"
            contracts = ("C_QUARANTINE",)
            allowed = False

        return ContractDecision(
            contracts=contracts,
            risk_score=score,
            risk_level=level,
            allowed=allowed,
            reason=f"op={operation} data={data_sensitivity} ext={external} → {level}",
        )
