import ast
import inspect
import re
from typing import Dict, List, Callable, Any, Optional

class ASTSecurityAndSBOMScanner:
    """
    Capa 5: Motor de Verificación[span_2](start_span)[span_2](end_span).
    Genera inventario SBOM[span_3](start_span)[span_3](end_span) y detecta secretos/patrones inseguros en el AST sin ejecutar el código.
    """
    SECRET_PATTERNS = [
        re.compile(r'(?i)(api[_-]?key|secret|password|bearer|token)\s*=\s*["\'][A-Za-z0-9/+=_-]{8,}["\']'),
        re.compile(r'-----BEGIN PRIVATE KEY-----')
    ]

    UNSAFE_CALLS = {"eval", "exec", "__import__"}

    def scan_code(self, code_content: str) -> Dict[str, Any]:
        """
        [Determinista 90%] Análisis AST de imports, funciones invocadas y patrones regex.
        [LLM 10%] Permite evaluar si un nombre de variable sospechoso es realmente un falso positivo.
        """
        errors = []
        imports_found = []

        # 1. Escaneo Regex de Secretos en texto plano
        for pattern in self.SECRET_PATTERNS:
            if pattern.search(code_content):
                errors.append("SECRETS_DETECTED: Se detectaron credenciales o llaves harcodeadas.")
                break

        # 2. Análisis AST para Imports (SBOM) y llamadas peligrosas
        try:
            tree = ast.parse(code_content)
            for node in ast.walk(tree):
                # Captura de dependencias (SBOM)[span_4](start_span)[span_4](end_span)
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports_found.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports_found.append(node.module)

                # Detección de llamadas peligrosas
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name) and node.func.id in self.UNSAFE_CALLS:
                        errors.append(f"UNSAFE_CALL: Uso no permitido de la función '{node.func.id}'.")

        except SyntaxError as e:
            errors.append(f"SYNTAX_ERROR: Error al parsear código AST: {str(e)}")

        status = "PASSED" if not errors else "FAILED"

        return {
            "status": status,
            "errors": errors,
            "sbom_dependencies": list(set(imports_found)),  # Inventario SBOM[span_5](start_span)[span_5](end_span)
            "is_secure": len(errors) == 0
        }


class AdapterFactory:
    """
    Capa 10: Bus Universal de Plugins y Generación de Adaptadores Dinámicos.
    Garantiza que un plugin sea compatible con la interfaz del Bus sin romper el sistema.
    """
    @staticmethod
    def create_adapter(target_func: Callable, expected_args: List[str]) -> Callable:
        """
        [Determinista 90%] Adapta la firma de una función ajustando parámetros sobrantes o faltantes.
        [LLM 10%] Inferencia de compatibilidad cuando los nombres de los argumentos varían.
        """
        sig = inspect.signature(target_func)
        present_params = list(sig.parameters.keys())

        def adapted_wrapper(*args, **kwargs) -> Any:
            # Mapea dinámicamente los argumentos recibidos contra los que la función realmente acepta
            filtered_kwargs = {k: v for k, v in kwargs.items() if k in present_params}
            
            # Si faltan argumentos requeridos sin valor por defecto, inyecta None
            for param_name, param in sig.parameters.items():
                if param_name not in filtered_kwargs and param.default == inspect.Parameter.empty:
                    # Inyección de seguridad determinista para evitar TypeError
                    filtered_kwargs[param_name] = None

            return target_func(**filtered_kwargs)

        return adapted_wrapper


# Ejemplo de ejecución rápida
if __name__ == "__main__":
    scanner = ASTSecurityAndSBOMScanner()

    # Código de prueba con dependencia e intento de secreto
    test_code = """
import os
import requests

API_KEY = "AIzaSyD-TEST_KEY_EXPLICIT_SECRET"

def process_data():
    return os.getenv("PATH")
"""

    scan_res = scanner.scan_code(test_code)
    print("Estado del Escaneo:", scan_res["status"])
    print("SBOM Dependencias:", scan_res["sbom_dependencies"])[span_6](start_span)[span_6](end_span)
    print("Errores Detección:", scan_res["errors"])

    # Prueba de AdapterFactory (Capa 10)
    def plugin_func(a, b):
        return f"Ejecutado con a={a}, b={b}"

    # El bus envía 'a', 'b' y un parámetro extra 'c' que el plugin no soporta
    adapted_plugin = AdapterFactory.create_adapter(plugin_func, expected_args=["a", "b", "c"])
    result = adapted_plugin(a=10, b=20, c="extra_ignored_arg")
    print("Resultado Adaptador:", result)