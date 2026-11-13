# Candidatos complementarios — evaluación previa a instalación

Estado: propuesta técnica. Ningún componente de esta lista está autorizado automáticamente.

## 1. Inspect AI + Inspect Sandboxing

- Fuente: https://github.com/UKGovernmentBEIS/inspect_ai
- Sandbox: https://github.com/UKGovernmentBEIS/aisi-sandboxing
- Aporte: evaluación reproducible de agentes y ejecución de código no confiable mediante backends aislados.
- Destino recomendado: `source-evolution-workflow/evaluation-sandbox/`.
- Decisión: **recomendado** para reforzar Guardian y Judge. Antes de copiar, comprobar si ya existe en el inventario de componentes; si existe, reubicar/cablear sin redescarga.

## 2. Microsoft Agent Lightning

- Fuente: https://github.com/microsoft/agent-lightning
- Arquitectura: Trainer + API Gateway + Rollout Controller.
- Aporte: convierte trayectorias reales de agentes en datos de entrenamiento y optimización.
- Destino recomendado: pool externo de aprendizaje, nunca dentro del microkernel.
- Decisión: **diferido**. Requiere presupuesto de GPU, política de datos, evaluación de privacidad y autorización separada.

## 3. LangMem

- Fuente: https://github.com/langchain-ai/langmem
- Aporte: extracción de memoria, consolidación y optimización de comportamiento.
- Decisión: **no instalar ahora**; se solapa con MemOS. Solo adoptar si una prueba comparativa demuestra una capacidad faltante.

## 4. OpenPipe ART

- Fuente: https://github.com/OpenPipe/ART
- Aporte: entrenamiento por refuerzo para agentes mediante GRPO.
- Decisión: **diferido** por cómputo y por solapamiento con Agent Lightning/SIA. Debe vivir fuera del kernel.

## 5. AnyIO

- Fuente/documentación: https://anyio.readthedocs.io/
- Aporte: concurrencia estructurada portable entre asyncio y Trio, con cancel scopes.
- Decisión: **no instalar por ahora**. El microkernel usa `asyncio` estándar y captura fallos por carril; añadir AnyIO sin una necesidad multi-backend aumentaría dependencias sin capacidad nueva.

## Resultado

La incorporación con mejor relación valor/riesgo es Inspect AI/Sandboxing, pero primero debe pasar deduplicación contra el inventario existente y autorización del Director. Los otros candidatos permanecen como opciones de pool o evaluación, no como dependencias del kernel.
