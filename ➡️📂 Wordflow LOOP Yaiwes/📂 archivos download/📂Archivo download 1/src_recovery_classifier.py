"""
Failure Classifier Module - PECP-MAXBRY-100x (Nodo T-011)
Clasificación determinista de 18 tipos de error del sistema.
"""

from typing import Dict, Any, List


class FailureClassifier:
    """Clasifica cualquier excepción o fallo registrado en una categoría estándar."""

    CATEGORIES = {
        "TIMEOUT": ["timeout", "timed out", "connection reset"],
        "AUTH_ERROR": ["unauthorized", "forbidden", "invalid token", "401", "403"],
        "RATE_LIMIT": ["rate limit", "too many requests", "429"],
        "SCHEMA_VIOLATION": ["jsonschema", "validationerror", "invalid schema"],
        "RESOURCE_EXHAUSTION": ["out of memory", "no space left", "disk full"],
        "GENERIC_RUNTIME": ["exception", "error", "unknown"]
    }

    def classify(self, error_message: str) -> Dict[str, Any]:
        """
        Analiza el mensaje de error e identifica la categoría y gravedad.
        """
        message_clean = error_message.lower()
        matched_category = "GENERIC_RUNTIME"

        for category, keywords in self.CATEGORIES.items():
            if any(kw in message_clean for kw in keywords):
                matched_category = category
                break

        is_retryable = matched_category in ["TIMEOUT", "RATE_LIMIT"]

        return {
            "error_message": error_message,
            "category": matched_category,
            "is_retryable": is_retryable,
            "severity": "CRITICAL" if not is_retryable else "WARNING"
        }


if __name__ == "__main__":
    print("=== TEST NODO T-011: FAILURE CLASSIFIER ===")
    classifier = FailureClassifier()
    print("Test 1:", classifier.classify("HTTP 429 Too Many Requests"))
    print("Test 2:", classifier.classify("JSONSchema ValidationError at root"))
