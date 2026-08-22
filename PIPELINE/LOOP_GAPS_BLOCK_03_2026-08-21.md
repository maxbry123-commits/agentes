# LOOP GAPS BLOCK 03 — Guía, ejecución y verificación

Fecha: 2026-08-21
Repositorio: maxbry123-commits/agentes

## 0. GUÍA OBLIGATORIA LEÍDA ANTES DE PROGRAMAR

Fuentes internas leídas antes de esta salida:
- `AGENTS.md`
- `PIPELINE/00_METODO_TRABAJO_Y_ARQUITECTURA.md`
- `PIPELINE/ADVANCED_ENGINEERING_STANDARD_V3.md`
- `PIPELINE/FORENSIC_CODE_AUDIT.md`
- `PIPELINE/64_RECOVERY_PATCH_GAPS_WORDFLOW_2026-08-21.md`

Regla ejecutable:
`CONTEXT/HANDOFF → COPY-FIRST SCAN → IMPLEMENT(COPY|ADAPT|GENERATE) → WIRE → FORENSIC VERIFY → VERDICT AUTHORITY → CLOSED|FIX`

Regla COPY-FIRST:
`COPY/MOVE → LINK/CONNECT → PATCH → ADAPT → GENERATE LAST`.

DONE requiere INTAKE + LOCAL_VERIFY + GITHUB_PUBLISHED + REMOTE_VERIFY + FORENSIC_AUDIT_DONE. LLM no declara PASS.

## 1. PROCESO DE CODE Y VERIFICACIÓN

1. Leer contexto y handoff.
2. Localizar código existente por símbolo/path.
3. Registrar source/destination/SHA antes de copiar/adaptar.
4. Preferir reutilización antes de generar.
5. Hacer el cambio mínimo.
6. Añadir/ajustar tests del comportamiento afectado.
7. Ejecutar verificación local disponible.
8. Publicar únicamente artefacto verificado.
9. Releer GitHub después del commit.
10. Comparar SHA/tamaño/anchors y diff.
11. Ejecutar auditoría forense de 4 pasadas.
12. Solo VerdictAuthority puede cerrar PASS/DONE.

## 2. T01 — VENDOR / ROUTER

Estado: `PARTIAL / REPAIR_REQUIRED`, no DONE.

Hecho en este LOOP:
- Se confirmó que el hot path actual instancia `MockIntelligenceGateway(fixed_text="PATH_GATEWAY_DENY")`.
- Se confirmó que ya existe `RouterHTTPGateway` y que, sin `ROUTER_URL`, falla cerrado DENY.
- Se buscó código/test existente para evitar generación duplicada.
- Se creó `extensions/wordflow/tests/test_router_http_gateway.py` para cubrir el contrato fail-closed del gateway existente.
- Commit: `360bd903da1ba591feda0226af413ffcb5af6b06`.
- Remote read-back: PASS para existencia y contenido del test.
- Workflow asociado al commit: no se encontró una ejecución PR asociada; por tanto no se declara PASS de CI.

Pendiente T01:
- Cambiar el hot path de `MockIntelligenceGateway` a la autoridad `RouterHTTPGateway`/factory existente.
- Ajustar el test C-19 que actualmente espera `WIRED_DENY` del mock.
- Ejecutar tests y forense completo.
- Verificar que el vendor nunca es llamado directamente.

## 3. DIEZ VÍAS DE RESOLUCIÓN SI EL WIRING ENCUENTRA UN GAP

1. Inyección directa de `RouterHTTPGateway` en `consult_path_gateway`.
2. Reutilizar `build_gateway_from_env()` como factory única.
3. Crear una función adaptadora pequeña que preserve el contrato `GatewayResponse`.
4. Inyectar el gateway como parámetro opcional para testabilidad.
5. Usar configuración por `ROUTER_URL` y fail-closed sin fallback en producción.
6. Mantener mock únicamente como dependencia explícita de tests/dev.
7. Añadir test de contrato HTTP con servidor/mocking determinista.
8. Añadir test que falle si el hot path importa/instancia `MockIntelligenceGateway` directamente.
9. Añadir evidencia source→dest/SHA si se copia/adapta código existente.
10. Ejecutar cuatro pasadas forenses y cerrar únicamente mediante VerdictAuthority.

Estas opciones siguen el patrón de inyección de dependencias recomendado para separar la dependencia real del código bajo prueba; la comunidad de Python también usa DI para sustituir clientes reales por mocks/stubs en tests. urlDiscusión Python sobre DI y testinghttps://www.reddit.com/r/Python/comments/195ad6k/do_you_prefer_mock_or_dependency_injection_when_unit_testing_functions_in_python/

## 4. T02 — C100/T49

Estado: `BLOCKED_FOR_SPEC/PRODUCTION_EVIDENCE`.
No se inventa cierre. Requiere evidencia real de producción/engine y no solo un mock.

## 5. T03–T10

Estados: `OPEN`.
No se modifican prematuramente hasta cerrar gates de reutilización, callers y contratos.

## 6. 12 GOALS DEL LOOP

1. Preservar contexto.
2. No regenerar código existente.
3. Identificar autoridad única.
4. Resolver T01 sin segunda gateway.
5. Mantener fail-closed.
6. Cubrir comportamiento con tests.
7. Registrar evidencia.
8. Publicar solo artefactos verificados.
9. Hacer remote read-back.
10. Ejecutar X-Ray/forense.
11. No declarar PASS por afirmación LLM.
12. Dejar siguiente tarea y recuperación documentadas.

## 7. ASK COUNCIL — 12 PASOS

1. ¿Existe implementación reutilizable?
2. ¿Cuál es la fuente exacta?
3. ¿Cuál es la autoridad existente?
4. ¿Se puede copiar/adaptar en lugar de generar?
5. ¿Qué contrato no puede cambiar?
6. ¿Qué callers dependen del comportamiento actual?
7. ¿Qué tests deben cambiar?
8. ¿Qué riesgo introduce el wiring?
9. ¿Qué evidencia demuestra que funciona?
10. ¿Qué evidencia demuestra que no se llamó al vendor incorrectamente?
11. ¿Qué debe releerse en GitHub?
12. ¿VerdictAuthority permite PASS o exige FIX/BLOCK?

## 8. VERIFICACIÓN REQUERIDA

Para cada tarea de code: mínimo 7 comprobaciones y tantas adicionales como sean necesarias:
1. fuente existente;
2. SHA antes;
3. diff/cambio;
4. sintaxis/tests;
5. commit;
6. read-back remoto;
7. forense + VerdictAuthority.

Si falla una comprobación: `REPAIR_REQUIRED`, no DONE.

## 9. RECOVERY POINTER

Si se pierde contexto, leer en este orden:
`README → AGENTS.md → PIPELINE/00_METODO_TRABAJO_Y_ARQUITECTURA.md → LOOP_GAPS_BLOCK_03 → 64_RECOVERY_PATCH → GAPS → FORENSIC_MAP → código/tests`.

## ESTADO FINAL DEL BLOQUE

T01: PARTIAL / REPAIR_REQUIRED
T02: BLOCKED
T03: OPEN
T04: OPEN
T05: OPEN
T06: OPEN
T07: OPEN
T08: OPEN
T09: OPEN
T10: OPEN

No hay ninguna afirmación falsa de DONE en este bloque.
