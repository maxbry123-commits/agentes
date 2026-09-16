# ✅ NOTA X-RAY — Claude 01

**Fuente:** `Readme arquitectura Yaiwes/Claude instrucciones Yaiwes/01_hoja_de_ruta_fundamentos_limpieza.md`
**Blob SHA fuente:** `06a2bdc456c421a191b31fdb707680a2e929dc17`
**Estado:** AUDITADO / PROPUESTA, no integrado.

## 4 pasadas
1. **Literal/método:** regla explícita: no escribir código nuevo salvo cuando la tarea lo ordena; prioriza ensamblar, cablear o envolver código existente. Tareas 1–15 construyen fachadas de las 8 primitivas y regresión.
2. **Código que falta / cómo conseguirlo:** antes de crear, comparar duplicados, reutilizar `extensions/wordflow_kernel`, generar solo CLI/contratos/wrappers/manifest/tests que realmente falten.
3. **Integración:** kernel-principal debe funcionar como fachada delegante; wrappers llaman a implementaciones existentes en vez de duplicarlas.
4. **Cruce YAIWES:** coincide con `REUSE → REFERENCIAR/COPY con SHA → ADAPT → TEST → CUTOVER` del README canónico y con la regla Lego de `PLAN_YAIWES_AGENTE_WORDFLOW.md`. Los conteos fijos del documento (p. ej. 27 tests) requieren revalidación antes de ejecutar.

## 6 lentes de auditoría
- Literal: PASS.
- Arquitectura: ALINEADO.
- Código/símbolos: REQUIERE INVENTARIO ACTUAL antes de crear wrappers.
- Integración: FACHADA/DELEGACIÓN.
- Seguridad: sin hallazgo crítico propio del documento.
- Cierre: solo PASS con regresión y evidencia real.

**Conclusión:** método reutilizable para Wordflow LOOP: `comparar → reutilizar → envolver/cablear → probar → evidenciar`; no generar sustitutos por defecto.
