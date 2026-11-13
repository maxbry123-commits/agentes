# ✅ NOTA X-RAY — Claude 10

**Fuente:** `Readme arquitectura Yaiwes/Claude instrucciones Yaiwes/10_plantilla_modulos_razonamiento.md`
**Blob SHA fuente:** `be4f61d138bd12e8ad39ab932d0a5fe6a2511e8d`
**Estado:** AUDITADO / PROPUESTA, no integrado.

## 4 pasadas
1. **Literal/método:** un módulo de razonamiento entra solo si pasa 4 pruebas: independencia en 3 dominios, no redundancia, instrucción accionable y costo declarado.
2. **Código que falta / cómo conseguirlo:** reutilizar `expert-panel-router`, `decision-on-demand`, Multi-API y Judge; agregar únicamente contenido/ficha y el delta de validación necesario.
3. **Integración:** un módulo por archivo, registry/slot, SELECT→ADAPT→ejecución→RANK; no crear otra capa del kernel.
4. **Cruce YAIWES:** `ficha_contract_v2.py` actual no demuestra el bloque `cognicion` ni `validar_cognicion()` descritos por Claude; por tanto esa extensión es PROPUESTA y requiere schema+validator+tests antes de usarla.

## 6 lentes
Literal PASS · Arquitectura ALINEADO · Código EXTENSIÓN NO DEMOSTRADA · Integración REUSA PIEZAS · Seguridad/costo declarados · Cierre 4/4 pruebas + tests.

**Conclusión:** buena regla de admisión para el Wordflow, pero no marcar la categoría cognitiva como implementada hasta verificar el contrato real.
