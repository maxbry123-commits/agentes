# Evaluation Sandbox

Gate determinista del workflow de autoevolución YAIWES.

- **Inspect AI** aporta contratos y código fuente para solver, scorer y sandbox. Vive aislado en `vendor/inspect-ai`; el kernel no lo importa directamente. Su activación requiere adapter/ABI, Sheriff, autorización y prueba E2E.
- **Inspect Sandboxing Toolkit** aporta el protocolo de selección de aislamiento por herramientas, host y red. La fuente no declara licencia en el repositorio fijado, por lo que queda como referencia documental y su ejecución/copia derivada está bloqueada.
- El LLM propone o puntúa; no autoriza instalación, red, escritura, hot-swap ni PASS.
- Toda salida ejecutable pasa por pasaporte, hashes, sandbox sin red por defecto y rollback.
