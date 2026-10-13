from dataclasses import dataclass
from typing import Any, Literal

RiskLevel = Literal["normal", "sheriff_check", "quarantine"]


@dataclass(frozen=True)
class ContractDecision:
    contracts: tuple[str, ...]
    risk_score: int
    risk_level: RiskLevel
    allowed: bool
    reason: str
    enchufe_ok: bool = True


class ContractRouter:
    """Selector determinista de contratos + ENCHUFE gate.

    SOURCE: SALIDA_1_CAPA_CONTROL_PARTE_3 §42 + ENCHUFE UNIVERSAL v2.0
    INPUT → Classifier → Threat Analyzer → Contract Compiler → Sheriff
    El LLM nunca selecciona contratos.
    """

    DATA = {"public": 0, "internal": 2, "secret": 5}
    OP = {"read": 1, "write": 3, "delete": 5}
    EXT = {"none": 0, "api": 3, "unknown": 5}

    def classify(
        self,
        operation: str,
        data_sensitivity: str = "internal",
        external: str = "none",
        ficha: dict[str, Any] | None = None,
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

        enchufe_ok = True
        if ficha is not None:
            try:
                from enchufe.validator_v2 import validar
                veredicto = validar(ficha)
                enchufe_ok = veredicto.valido
                if not enchufe_ok:
                    allowed = False
                    level = "quarantine"
            except Exception:
                enchufe_ok = False
                allowed = False

        return ContractDecision(
            contracts=contracts,
            risk_score=score,
            risk_level=level,
            allowed=allowed,
            reason=f"op={operation} data={data_sensitivity} ext={external} → {level}",
            enchufe_ok=enchufe_ok,
        )
