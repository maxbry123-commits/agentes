# ✅ NOTA X-RAY — Claude 11

**Fuente:** `Readme arquitectura Yaiwes/Claude instrucciones Yaiwes/11_catalogo_105_algoritmos_deterministas.md`
**Blob SHA fuente:** `42511c2ed12c3405fc63b9d2e479aff3e6a473f0`
**Estado:** AUDITADO / PROPUESTA, no integrado.

## 4 pasadas
1. **Literal/método:** catálogo de 105 algoritmos/capacidades deterministas para reducir uso de LLM en búsqueda, análisis, lógica, decisión, cierre, persistencia, verificación y optimización.
2. **Código que falta / cómo conseguirlo:** el documento indica librerías conocidas para muchos algoritmos; son candidatos, no implementaciones demostradas dentro del kernel.
3. **Integración:** usar la misma ficha con `ejecucion.kind: code`; `expert-panel-router` podría seleccionar capacidad determinista en vez de llamar a LLM.
4. **Cruce YAIWES:** refuerza kernel 0% LLM y decision-on-demand; integrar los 105 de golpe sería sobreingeniería. Cada algoritmo debe responder a un gap real, pasar ficha, destino, test y evidencia.

## 6 lentes
Literal PASS · Arquitectura ALINEADO · Código CATÁLOGO_NO_IMPLEMENTACIÓN · Integración SELECTIVA · Seguridad depende de librería/capacidad · Cierre por gap real y test.

**Conclusión:** regla para Wordflow: `DETERMINISTA SI RESUELVE → LLM SOLO SI JUSTIFICADO`; no convertir el catálogo en backlog obligatorio completo.
