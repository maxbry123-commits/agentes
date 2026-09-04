import hmac
import hashlib
import json
import uuid
from typing import Dict, List, Tuple

class TribunalHMACManager:
    """
    Gestor del Tribunal Multi-Agente (Capa 9).
    Maneja el consenso ponderado, poder de veto estricto y la firma criptográfica HMAC.
    """
    
    # Pesos deterministas de la evaluación del Tribunal (Suma = 1.0)
    AGENT_WEIGHTS = {
        "ArchitectureAgent": 0.20,
        "SecurityAgent": 0.25,     # Tiene VETO
        "PerformanceAgent": 0.15,
        "TestingAgent": 0.15,
        "CompatibilityAgent": 0.15,
        "EthicsAgent": 0.10        # Tiene VETO
    }

    VETO_POWER_AGENTS = {"SecurityAgent", "EthicsAgent"}

    def __init__(self, secret_key: str):
        self._secret_key = secret_key.encode('utf-8')

    def create_case_id(self, artifact_hash: str) -> str:
        """Genera un UUID único para el expediente vinculado al hash Merkle del código."""
        short_hash = artifact_hash[:8]
        return f"TC-CASE-{uuid.uuid4().hex[:8].upper()}-{short_hash}"

    def evaluate_and_sign_case(
        self, 
        artifact_hash: str, 
        agent_scores: Dict[str, float], 
        agent_vetoes: Dict[str, bool],
        llm_ethical_reasoning: str = ""
    ) -> Dict:
        """
        [Determinista 90%] Evalúa los scores ponderados, valida vetos y firma con HMAC SHA-256.
        [LLM 10%] Acepta argumentos de la evaluación cualitativa de Ethics/Architecture.
        """
        case_id = self.create_case_id(artifact_hash)
        
        # 1. Chequeo Determinista de Vetos
        veto_triggered = False
        veto_reasons = []
        for agent in self.VETO_POWER_AGENTS:
            if agent_vetoes.get(agent, False):
                veto_triggered = True
                veto_reasons.append(f"Veto ejercido por {agent}")

        # 2. Cómputo de Score Ponderado (Determinista)
        total_score = 0.0
        for agent, weight in self.AGENT_WEIGHTS.items():
            score = agent_scores.get(agent, 0.0)
            total_score += score * weight

        # 3. Determinación de Veredicto
        if veto_triggered:
            verdict = "REJECTED_VETO"
        elif total_score >= 0.85:
            verdict = "APPROVED"
        elif total_score >= 0.70:
            verdict = "CONDITIONAL_APPROVAL"
        else:
            verdict = "REJECTED_LOW_SCORE"

        # 4. Estructura Inmutable del Caso
        case_data = {
            "tribunal_case_id": case_id,
            "artifact_hash": artifact_hash,
            "weighted_score": round(total_score, 4),
            "verdict": verdict,
            "veto_triggered": veto_triggered,
            "veto_details": veto_reasons,
            "agent_scores": agent_scores,
            "ethical_reasoning_summary": llm_ethical_reasoning[:250]  # 10% LLM Input
        }

        # 5. Generación de Firma Criptográfica HMAC SHA-256
        serialized_payload = json.dumps(case_data, sort_keys=True)
        hmac_signature = hmac.new(
            self._secret_key,
            serialized_payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        return {
            "case_file": case_data,
            "hmac_signature": hmac_signature
        }

    def verify_case_signature(self, case_file: Dict, signature_to_verify: str) -> bool:
        """Verifica que un expediente de caso no haya sido alterado en el bus."""
        serialized_payload = json.dumps(case_file, sort_keys=True)
        expected_signature = hmac.new(
            self._secret_key,
            serialized_payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature_to_verify)


# Ejemplo de ejecución
if __name__ == "__main__":
    secret = "SDPA_SECRET_KEY_2026_TRIBUNAL"
    manager = TribunalHMACManager(secret)

    # Simulación de Votación
    scores = {
        "ArchitectureAgent": 0.90,
        "SecurityAgent": 0.95,
        "PerformanceAgent": 0.80,
        "TestingAgent": 0.85,
        "CompatibilityAgent": 0.90,
        "EthicsAgent": 0.88
    }
    vetoes = {"SecurityAgent": False, "EthicsAgent": False}

    res = manager.evaluate_and_sign_case(
        artifact_hash="a3f8e12b4c5d6e7f8a9b0c1d2e3f4a5b",
        agent_scores=scores,
        agent_vetoes=vetoes,
        llm_ethical_reasoning="El módulo cumple con las directrices de privacidad de datos."
    )

    print("Case ID:", res["case_file"]["tribunal_case_id"])
    print("Veredicto:", res["case_file"]["verdict"])
    print("Firma HMAC:", res["hmac_signature"][:20] + "...")
    print("¿Firma Válida?:", manager.verify_case_signature(res["case_file"], res["hmac_signature"]))