# ✅ NOTA X-RAY — Claude 02

**Fuente:** `Readme arquitectura Yaiwes/Claude instrucciones Yaiwes/02_hoja_de_ruta_razonamiento_gobernanza.md`
**Blob SHA fuente:** `3d4d9d0e63bfc282a1863be90648e7a6e3f06808`
**Estado:** AUDITADO / PROPUESTA, no integrado.

## 4 pasadas
1. **Literal/método:** tareas 16–35: schema-first, complejidad→plantilla, contratos cerrados, timeout/idempotencia/concurrencia, gobernanza, forensic log y tests.
2. **Código que falta / cómo conseguirlo:** comprobar antes de crear; `decision_on_demand.py` y `expert_panel_router.py` ya existen dentro de `Claude instrucciones Yaiwes`, por tanto son candidatos a validar/cablear, no huecos automáticamente.
3. **Integración:** decisión y routing deben entrar por contratos, config y tests; no hardcodear capacidad ni saltarse validator/policy.
4. **Cruce YAIWES:** corresponde a `reasoning-kernel`, `definition-registry`, `execution-orchestration` y `control-governance`; es posterior al camino E2E mínimo definido por Claude 08.

## 6 lentes
Literal PASS · Arquitectura ALINEADO · Código PARCIAL/CANDIDATOS EXISTENTES · Integración CONTRATO-FIRST · Seguridad FAIL-CLOSED · Cierre requiere tests/evidencia.

**Conclusión:** no empezar escribiendo todo 16–35; inventariar equivalentes, reutilizar lo existente y crear únicamente el delta probado que cierre el flujo.
