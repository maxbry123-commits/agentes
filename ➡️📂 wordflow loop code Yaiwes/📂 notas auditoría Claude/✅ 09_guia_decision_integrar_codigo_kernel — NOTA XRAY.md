# ✅ NOTA X-RAY — Claude 09

**Fuente:** `Readme arquitectura Yaiwes/Claude instrucciones Yaiwes/09_guia_decision_integrar_codigo_kernel.md`
**Blob SHA fuente:** `a7b0da54bee75dec7321731e524cd2248ee3ba0d`
**Estado:** AUDITADO / PROPUESTA, no integrado.

## 4 pasadas
1. **Literal/método:** intake de código = analizar sin ejecutar → llenar ficha → validar → integrar intacto o adaptar → slot nuevo/shadow test → entregar original+ficha+adaptador.
2. **Código que falta / cómo conseguirlo:** antes de escribir, decidir si el bloque puede entrar intacto, necesita adaptador o debe rechazarse; desconocidos críticos se marcan `[NO_DETERMINABLE]`, nunca se inventan.
3. **Integración:** preservar original, adaptador separado, registry por slots, shadow-test/swap para reemplazos; encaja directamente con el método REUSE/ADAPT de YAIWES.
4. **Cruce con código real dentro de la raíz:** `UniversalPluginBus.enchufar`, `ContractGenerator.generate`, `AdapterFactory.create` y `PluginRegistry` SÍ existen en `Skills de trabajo/...universal_plugin_bus_v2_integrated.py`; el validador de 36 invariantes está dentro de `ficha_contract_v2.py` como `validar()`, no se demostró un `validator_v2.py` separado. Hallazgo crítico: `ContractGenerator._extract_exports()` y `HotSwapManager._test_import()` usan `exec(candidate.source_code, ...)`, contradiciendo la regla de Claude “nunca ejecutes el código todavía”.

## 6 lentes
Literal PASS · Arquitectura ALINEADO · Código SÍ LOCALIZADO con corrección de nombres · Integración ÚTIL · Seguridad GAP_CRÍTICO por `exec()` pre-sandbox · Cierre NO APTO hasta corregir/probar intake seguro.

**Conclusión:** conservar ficha+adaptador+slot, pero sustituir inspección ejecutable por análisis estático/AST o sandbox real antes de tratar el Enchufe como intake seguro.
