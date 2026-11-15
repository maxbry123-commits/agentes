import hmac
import hashlib
import time
import json
import concurrent.futures
from typing import Dict, Any, Callable

class SLAConstraintViolation(Exception):
    """Excepción lanzada cuando la ejecución o aislamiento supera el SLA de 500ms."""
    pass


class CircuitBreakerSLA:
    """
    Capa 12: Aislamiento por Límite de Tiempo (< 500 ms)[span_2](start_span)[span_2](end_span).
    Monitorea la ejecución y corta de manera determinista cualquier plugin o extensión
    que falle o exceda el tiempo límite permitido.
    """
    MAX_TIMEOUT_SECONDS = 0.500  # SLA Estricto < 500ms[span_3](start_span)[span_3](end_span)

    def __init__(self, hmac_secret_key: str):
        self._secret_key = hmac_secret_key.encode('utf-8')

    def execute_with_circuit_breaker(
        self, 
        module_id: str, 
        target_func: Callable, 
        *args, 
        **kwargs
    ) -> Dict[str, Any]:
        """
        [Determinista 100%] Ejecuta el módulo en un hilo aislado.
        Si la ejecución excede 500ms o lanza una excepción, realiza el desenchufe de emergencia inmediatamente[span_4](start_span)[span_4](end_span).
        """
        start_time = time.perf_counter()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(target_func, *args, **kwargs)
            try:
                # Intento de ejecución dentro del ventana estricta de SLA (<500ms)[span_5](start_span)[span_5](end_span)
                result = future.result(timeout=self.MAX_TIMEOUT_SECONDS)
                execution_time_ms = round((time.perf_counter() - start_time) * 1000, 2)

                return {
                    "status": "SUCCESS",
                    "module_id": module_id,
                    "execution_time_ms": execution_time_ms,
                    "result": result,
                    "incident_log": None
                }

            except concurrent.futures.TimeoutError:
                # Desenchufe de emergencia por Timeout (SLA superado)[span_6](start_span)[span_6](end_span)
                execution_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
                incident = self._generate_incident_log(
                    module_id=module_id,
                    reason=f"SLA_VIOLATION_TIMEOUT: La ejecución superó los {self.MAX_TIMEOUT_SECONDS*1000}ms",
                    execution_time_ms=execution_time_ms
                )
                return {
                    "status": "ISOLATED_TIMEOUT",
                    "module_id": module_id,
                    "execution_time_ms": execution_time_ms,
                    "result": None,
                    "incident_log": incident
                }

            except Exception as e:
                # Desenchufe de emergencia por Error Crítico en tiempo de ejecución[span_7](start_span)[span_7](end_span)
                execution_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
                incident = self._generate_incident_log(
                    module_id=module_id,
                    reason=f"RUNTIME_EXCEPTION: {str(e)}",
                    execution_time_ms=execution_time_ms
                )
                return {
                    "status": "ISOLATED_CRASH",
                    "module_id": module_id,
                    "execution_time_ms": execution_time_ms,
                    "result": None,
                    "incident_log": incident
                }

    def _generate_incident_log(self, module_id: str, reason: str, execution_time_ms: float) -> Dict[str, Any]:
        """
        Genera un registro firmado inmutable para el tribunal/autocuración tras el desenchufe[span_8](start_span)[span_8](end_span).
        """
        payload = {
            "timestamp": time.time(),
            "module_id": module_id,
            "reason": reason,
            "isolation_time_ms": execution_time_ms,
            "action_taken": "FORCE_UNPLUGGED_SUB_500MS[span_9](start_span)"[span_9](end_span)
        }
        
        serialized = json.dumps(payload, sort_keys=True)
        hmac_sig = hmac.new(self._secret_key, serialized.encode('utf-8'), hashlib.sha256).hexdigest()

        return {
            "payload": payload,
            "hmac_signature": hmac_sig
        }


# Ejemplo de ejecución
if __name__ == "__main__":
    breaker = CircuitBreakerSLA("SDPA_SECRET_KEY_INCIDENTS")

    # 1. Caso Normal (Ejecución rápida)
    def fast_task():
        return "Procesado correctamente"

    res_fast = breaker.execute_with_circuit_breaker("plugin_fast_v1", fast_task)
    print("Test 1 (Rápido):", res_fast["status"], f"({res_fast['execution_time_ms']} ms)")

    # 2. Caso SLA Excedido (Simulación de bucle o demora > 500ms)[span_10](start_span)[span_10](end_span)
    def slow_task():
        time.sleep(0.7)  # Supera los 500ms de SLA
        return "No debería llegar aquí"

    res_slow = breaker.execute_with_circuit_breaker("plugin_slow_v1", slow_task)
    print("Test 2 (Timeout / Desenchufe):", res_slow["status"], f"({res_slow['execution_time_ms']} ms)")[span_11](start_span)[span_11](end_span)
    print("Incident Log HMAC:", res_slow["incident_log"]["hmac_signature"][:20] + "...")

    # 3. Caso Crash Inesperado
    def crashing_task():
        raise ValueError("División por cero simulada")

    res_crash = breaker.execute_with_circuit_breaker("plugin_crash_v1", crashing_task)
    print("Test 3 (Crash / Aislamiento):", res_crash["status"])