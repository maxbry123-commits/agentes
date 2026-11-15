# ✅ NOTA X-RAY — Claude 04

**Fuente:** `Readme arquitectura Yaiwes/Claude instrucciones Yaiwes/04_hoja_de_ruta_observabilidad_cierre.md`
**Blob SHA fuente:** `32be9479220130a4d709f8f58a2f0add9f977dac`
**Estado:** AUDITADO / PROPUESTA, no integrado.

## 4 pasadas
1. **Literal/método:** instrumentar trazas, mission/trace/ledger, durabilidad, retry/circuit breaker/watchdog, contract tests, Merkle, E2E, SBOM/secret scan y auditoría final.
2. **Código que falta / cómo conseguirlo:** reutilizar checkpoint/durability cuando exista y seleccionar librería real solo para gaps comprobados; no aceptar fake/stub como cierre.
3. **Integración:** observabilidad y recovery deben envolver el flujo real; el test E2E cubre reception→mission→decision→execution→evidence→closure sin mocks críticos.
4. **Cruce YAIWES:** coincide con el criterio canónico `code + wiring + test + evidence`; es fase de cierre, no sustituto del camino mínimo.

## 6 lentes
Literal PASS · Arquitectura ALINEADO · Código PARCIAL · Integración POST-E2E · Seguridad secret scan/contratos · Cierre FAIL-CLOSED.

**Conclusión:** una carpeta, stub o documentación no cierra ninguna capacidad; cada cierre debe ser falsificable y reproducible.
