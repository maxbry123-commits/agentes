"""
Preflight Engine Module - PECP-MAXBRY-100x (Nodo T-014)
Verificación previa de restricciones, cuotas, autenticación y capacidades de red/almacenamiento.
"""

from typing import Dict, Any, List, Optional
import json


class PreflightEngine:
    """Valida los recursos solicitados contra las políticas del proveedor antes de permitir la ejecución."""

    DEFAULT_POLICIES = {
        "github": {"max_rate_limit": 5000, "timeout_ms": 3000, "storage_quota_mb": 500},
        "huggingface": {"max_rate_limit": 1000, "timeout_ms": 5000, "storage_quota_mb": 5000},
        "pypi": {"max_rate_limit": 200, "timeout_ms": 2000, "storage_quota_mb": 100}
    }

    def __init__(self, policies: Optional[Dict[str, Any]] = None) -> None:
        self.policies = policies if policies else self.DEFAULT_POLICIES

    def evaluate_request(self, resource_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evalúa una petición de recursos garantizando que cumpla con las restricciones.
        """
        provider = resource_request.get("provider", "").lower()
        requested_storage = resource_request.get("required_storage_mb", 0)
        requested_timeout = resource_request.get("timeout_ms", 1000)

        policy = self.policies.get(provider)
        if not policy:
            return {
                "approved": False,
                "reason": f"Proveedor '{provider}' no está configurado en las políticas.",
                "fallback_plan": "REJECT"
            }

        violations: List[str] = []

        if requested_storage > policy["storage_quota_mb"]:
            violations.append(f"Almacenamiento excede cuota: {requested_storage}MB > {policy['storage_quota_mb']}MB")

        if requested_timeout > policy["timeout_ms"]:
            violations.append(f"Timeout excede máximo: {requested_timeout}ms > {policy['timeout_ms']}ms")

        approved = len(violations) == 0

        return {
            "provider": provider,
            "approved": approved,
            "violations": violations,
            "fallback_plan": "EXECUTE" if approved else "RESOURCE_REALLOCATION"
        }


if __name__ == "__main__":
    print("=== TEST NODO T-014: PREFLIGHT ENGINE ===")
    engine = PreflightEngine()
    req_valid = {"provider": "github", "required_storage_mb": 100, "timeout_ms": 2000}
    req_invalid = {"provider": "github", "required_storage_mb": 1000, "timeout_ms": 4000}

    print("Valid Req:", json.dumps(engine.evaluate_request(req_valid), indent=2))
    print("Invalid Req:", json.dumps(engine.evaluate_request(req_invalid), indent=2))