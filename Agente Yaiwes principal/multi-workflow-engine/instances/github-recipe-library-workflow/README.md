# YAIWES GitHub Recipe Library Workflow

Workflow determinista para reutilizar código y plantillas existentes antes de generar código nuevo.

## Flujo de cuatro pasos
1. **DISCOVER**: consulta catálogos/registries públicos priorizados; GitHub Code Search es el fallback secundario.
2. **SELECT**: deduplica, fija commit, licencia, procedencia y puntúa compatibilidad/seguridad.
3. **ACQUIRE_ADAPT**: descarga a staging, conserva el original y conecta mediante Adapter → Registry → BUS → Schema. El LLM solo puede elegir o proponer cambios quirúrgicos, máximo 5%.
4. **VERIFY_REPLICATE**: Sheriff, validación, sandbox, pruebas, hashes, rollback y réplica reproducible.

Ningún recurso sin licencia confirmada puede ejecutarse. Ningún archivo existente se sobrescribe. Toda incorporación requiere autorización del Director.
