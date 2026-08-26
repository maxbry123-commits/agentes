# CHECKPOINT + PARCHE DE RECUPERACIÓN — G1–G7 / OPENCLAW → WORDFLOW

**Fecha:** 2026-08-26
**Repositorio:** `maxbry123-commits/agentes`
**Rama:** `main`
**Autoridad:** GitHub = truth
**Modo:** LOOP / FAIL-CLOSED / NO_FAKE_PASS

---

## 0. PROPÓSITO

Este checkpoint congela el estado recuperable antes de continuar el ciclo de resolución de G1–G7. No declara PASS por documentación. Cada cierre requiere evidencia real en `main`.

## 1. PLAN CANÓNICO

`PIPELINE/PLAN_YAIWES_AGENTE_WORDFLOW.md`

https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/PLAN_YAIWES_AGENTE_WORDFLOW.md

**SHA del plan leído:** `91f6aac5b33a997af170849961c2b565b8663cae`

Reglas del plan relevantes:
- GitHub = única verdad.
- PASS solo con evidencia.
- FAIL-CLOSED.
- Refactoria obligatoria para cambios de código.
- `code_path_runner.py` no se toca sin paridad de tests.
- No inventar adapters, schemas, p01–p12 ni cuerpos de agentes.

## 2. GUÍA OBLIGATORIA DE PLUGINS

`Método de trabajo/GUIA_REGISTRO_PLUGINS_Y_CABLEADO.md`

https://github.com/maxbry123-commits/agentes/blob/main/M%C3%A9todo%20de%20trabajo/GUIA_REGISTRO_PLUGINS_Y_CABLEADO.md

Regla operativa:
1. Crear/preparar el mecanismo plugin de conexión junto con el archivo cuando corresponda.
2. Validar.
3. Registrar.
4. Dejar estable el archivo registrado.
5. Las conexiones futuras se hacen por plugin/contrato/adapter/cable.
6. No editar posteriormente el archivo original solamente para añadir una conexión.

Esta regla se aplica a los pasos 2, 3 y 4 y a los gaps donde exista cableado/conexión.

## 3. PARCHE DE RECUPERACIÓN — PUNTO DE RESTAURACIÓN

### Estado base

Checkpoint anterior:
`PIPELINE/checkpoints/CHECKPOINT_LOOP_2026-08-26_OPENCLAW_GAPS.md`

SHA del blob de ese checkpoint al ser leído:
`f0a192c5df4196dc4c63b06a4e52032b0de02db2`

Commit que creó el checkpoint anterior:
`a004805a61f9d225a3b48213c33e47681da44091`

### Regla de restauración

Si cualquier cambio posterior rompe un componente:

1. NO editar el archivo roto directamente para recuperar.
2. Identificar el último commit de `main` que contiene el estado válido.
3. Recuperar desde `Refactoria/<GAP>/source/` cuando exista.
4. Comparar `source/` contra `new/` y contra el destino canónico.
5. Ejecutar tests antes de volver a integrar.
6. Crear checkpoint nuevo después de la recuperación.
7. Mantener las copias `source/` como evidencia.

### Regla de rollback

No ejecutar `reset`, `clean`, eliminación de source ni reemplazo destructivo como mecanismo de recuperación sin una evidencia y autorización compatibles con el plan. La recuperación debe ser trazable a un commit/SHA y a una copia source.

---

## 4. PARCHE ESPECÍFICO OPENCLAW → WORDFLOW

Estado: **CABLEADO VERIFICADO PREVIAMENTE; NO CONFUNDIR CON CIERRE DE G1–G7.**

Ruta conceptual verificada:

`Wordflow → OpenClawEngine.reason() → IntelligenceGateway → OpenClawHTTPGateway → POST /v1/chat/completions → OpenClaw Gateway`

Reglas de recuperación:
- No introducir Hermes.
- No reemplazar `EnginePort.reason` por un cuerpo inventado.
- LLM debe continuar pasando por `IntelligenceGateway`.
- No editar el hot path para resolver una conexión.
- Si el cable falla, corregir el plugin/adapter/contrato, no modificar el archivo estable solamente para conectarlo.

---

## 5. HOT PATH — PROTECCIÓN

Archivo protegido:

`extensions/wordflow/engine/code_path_runner.py`

Regla:
- SOLO LECTURA durante esta tarea.
- No reescribir.
- No apagar.
- No reemplazar.
- Antes de cada cierre: comparar estado actual contra el estado base y confirmar que no fue modificado.
- La verificación debe aparecer en el RESULT del gap correspondiente.

---

## 6. PROMPT DE GAPS QUE ESTE LOOP ESTÁ RESOLVIENDO

# CHAT B — TASK: Cerrar gaps G1–G7 (YAIWES / wordflow) — NIVEL SAAS AVANZADO

ROLE: Senior Software Engineer / Implementer
Repo: `maxbry123-commits/agentes` · branch `main`
ESTÁNDAR: PRODUCTION / ADVANCED — PROHIBIDO MVP, stubs fingidos, PASS sin evidencia.

### REGLAS ABSOLUTAS
- REUSE > PATCH > ADAPT > GENERATE.
- NO inventar APIs, engines, p01–p12 ni bodies OpenClaw/Hermes si no hay source en repo.
- NO tocar ni apagar `extensions/wordflow/engine/code_path_runner.py`.
- NO duplicar `goal_lock`, `cognitive_loop`, `evidence_packet`.
- TASK total ≤ 2000 LOC estimadas; cada bloque de código ≤ 500 LOC.
- YAML/JSON para contratos; NO DSL inventado.
- FAIL-CLOSED: UNKNOWN / sin evidencia → no PASS.
- GitHub = truth.

### REFACTORÍA OBLIGATORIA
Para cualquier archivo modificado/generado a partir de existente:

1. Aislar en:
   - `despliegue/refactoria/<gap_id>/source/`
   - `Refactoria/<gap_id>/source/`
2. Implementar en:
   - `Refactoria/<gap_id>/new/`
3. Verificación cruzada ×3:
   - diff source vs new;
   - tests contra new;
   - checklist + evidencia.
4. Solo con las tres verificaciones PASS integrar al destino canónico.
5. Nunca borrar `Refactoria/*/source/` en este task.

### G1 — SYMBOL_INDEX_PROGRAMMING.md
Reutilizar `build_symbol_index()`.
Roots reales: engine + standards.
Destino: `agente-yaiwes/control-governance/symbol-index-wiring-graph/`.
Acceptance: export no vacío, símbolos del runner/pipeline, reproducible.

### G2 — SCHEMAS STAGE C-19
Leer `code_path_runner` + `programming_pipeline`.
Crear schemas JSON solo para stages que el código realmente nombra.
Destino: `agente-yaiwes/code-programming-engine/schema-contracts-io/`.
No inventar 19 stages.
Stages ausentes = residual OPEN.

### G3 — TEST→ASSERT INDEX
Escanear tests relevantes bajo `wordflow_kernel/tests` y tests de wordflow.
Destino: `agente-yaiwes/code-programming-engine/module-tests/`.
Acceptance: cada test file listado; asserts contados/citados; reproducible.

### G4 — CI LOG REAL
Destino: `agente-yaiwes/observability/trace-history/`.
Preparar captura determinista de workflow existente.
Si no hay log real: OPEN + runbook exacto.
NO fabricar log.

### G5 — p01→p12 E2E
Buscar `p01_* … p12_*` en repo/branches.
Si no existe source real: OPEN/BLOCKER y diseño de extracción solamente.
Si existe: cablear vía Refactoria y probar paridad con `code_path_runner`.

### G6 — ADAPTERS REALES
Inventariar gateway real.
Implementar adapter solo si existe source/SDK real.
Si no: contrato/interface + ficha v2 + OPEN; wire point hacia `intelligence_gateway`.

### G7 — OPENCLAW/HERMES BODY
Source = stubs actuales.
Implementar body real solo con source adquirido real.
Sin source: mejorar contrato/tests del stub y mantener OPEN para body real.
`EnginePort.reason` debe continuar y LLM debe pasar por `IntelligenceGateway`.
Hermes está excluido de esta ejecución por instrucción del Director.

### DESTINOS
- G1 → `control-governance/symbol-index-wiring-graph/`
- G2 → `code-programming-engine/schema-contracts-io/`
- G3 → `code-programming-engine/module-tests/`
- G4 → `observability/trace-history/`
- G5 → `code-programming-engine/code-path-execution/`
- G6 → `execution-engine-pool/adapter-layer/`
- G7 → `execution-engine-pool/auxiliary-role-agents/`

### OUTPUT POR GAP
`/TASK-GAPS/`
- `01_CODE/`
- `02_FILE_MANIFEST.json`
- `03_TEST_REPORT.md`
- `04_CONTRACT_REPORT.md`
- `05_DEPENDENCY_REPORT.md`
- `06_QUALITY_REPORT.md`
- `07_TRACEABILITY.json`
- `08_EVIDENCE_PACKET.json`
- `09_RESULT.md`

`Refactoria/<gap_id>/source/` y `Refactoria/<gap_id>/new/` deben existir para todo cambio.

### QUALITY BAR
- correctness;
- contracts;
- unit + integración por gap CLOSED;
- determinismo;
- seguridad sin secretos;
- observabilidad;
- no fake PASS.

### DEFINITION OF DONE
- `code_path_runner.py` intacto y verificado tres veces en RESULT.
- G1/G3 CLOSED solo con artifacts reales o BLOCKER.
- G2 CLOSED parcial solo con stages reales + residual OPEN.
- G4/G5/G6/G7 CLOSED solo con evidencia real; si no, OPEN.
- Evidence packet completo.
- Sin reescritura del kernel/hot path.

### BLOCKER
Si falta source para G5/G6/G7: `BLOCKER-T-GAP.md` con problem/source/impact/recommended_action. No sustituir BLOCKER por código inventado.

---

## 7. MATRIZ DE ESTADO EN ESTE CHECKPOINT

| Gap | Estado checkpoint | Qué falta para CLOSED | Recuperación |
|---|---|---|---|
| G1 | OPEN | ejecución CI real + artifact reproducible | restaurar source/new y volver a ejecutar workflow |
| G2 | OPEN | derivar y validar schemas solo de stages reales | conservar source y regenerar solo desde código existente |
| G3 | OPEN | ejecución CI real + artifact reproducible | restaurar source/new y volver a ejecutar workflow |
| G4 | OPEN | log/trace real de Actions | runbook; no fabricar log |
| G5 | OPEN/BLOCKER si no hay source | evidencia de p01–p12 reales + E2E/paridad | no fabricar módulos; usar BLOCKER-T-GAP |
| G6 | CLOSED solo donde exista adapter real verificable | cualquier extensión requiere source/SDK | recuperar desde source y contrato |
| G7 | CLOSED para cable OpenClaw verificado; body real no inventado | evidencia de body real si se pretende cerrar esa parte | mantener stub/contrato si no existe source |

**Importante:** `OPEN`, `BLOCKED` y `CLOSED` son estados de evidencia; no se convierten por redacción.

---

## 8. CHECKPOINT POR TAREA TERMINADA

Cada cierre futuro debe crear un archivo nuevo en `PIPELINE/checkpoints/` que contenga obligatoriamente:

1. GAP ID.
2. Objetivo.
3. Commit SHA.
4. SHA/blob de cada archivo crítico leído/modificado.
5. Lista exacta de archivos tocados.
6. `source/` y `new/` de Refactoria.
7. Resultado del diff.
8. Tests ejecutados y resultado.
9. Artifact/log real, si aplica.
10. Contrato/schema.
11. Dependencias.
12. Verificación del hot path.
13. Evidencia del plugin/cable si aplica.
14. Estado `CLOSED | OPEN | BLOCKED`.
15. Motivo si no es CLOSED.
16. Parche de recuperación específico del gap.
17. Enlace al plan.
18. Enlace a la guía.
19. Copia del prompt del gap resuelto.
20. Commit del propio checkpoint.

---

## 9. PARCHE DE RECUPERACIÓN POR GAP

### G1
Si falla export: conservar source de `symbol_index.py`, revertir solo la integración G1 al último commit válido y volver a generar el índice desde `build_symbol_index()`.

### G2
Si un schema contradice el runner: NO modificar el runner para hacerlo coincidir. Eliminar/revertir el schema derivado incorrectamente, releer el stage real y regenerar únicamente el contrato permitido.

### G3
Si el índice test→assert falla: conservar source del escáner, restaurar el último índice válido y volver a ejecutar sobre los tests existentes. No inventar tests.

### G4
Si no existe log: mantener `OPEN`, conservar runbook y esperar una ejecución real. No convertir una instrucción en evidencia.

### G5
Si no existen p01–p12: crear `BLOCKER-T-GAP.md`; no generar 12 módulos ficticios. Si aparecen posteriormente, iniciar nueva Refactoria desde source real.

### G6
Si un adapter rompe contrato: restaurar `source/`, retirar únicamente el adapter/cable defectuoso y volver a validar contra el contrato real. No modificar el componente estable para ocultar el fallo.

### G7
Si OpenClaw falla: restaurar el cable/adapter desde su source y verificar `EnginePort.reason` + `IntelligenceGateway`. Hermes permanece excluido.

---

## 10. CRITERIO DE CONTINUACIÓN DEL LOOP

El siguiente ciclo solo puede declarar un gap CLOSED cuando su acceptance tenga evidencia real.

Orden operativo:

`G1 → evidencia CI → G3 → evidencia CI → G2 → G4 → G5 → G6/G7 residual → auditoría final`

Después de cada CLOSED:

`cambio → tests → verificación cruzada → checkpoint → siguiente gap`

No se pausa el trabajo por un gap que pueda resolverse con evidencia disponible. Si una puerta depende de un recurso externo que no existe, se documenta como OPEN/BLOCKER y se continúa con el siguiente gap independiente sin inventar evidencia.

---

## 11. FIRMA DE ESTADO

Este documento es un **checkpoint operativo y parche de recuperación**, no una declaración de PASS global.

`NO_INVENTAR = TRUE`
`FAIL_CLOSED = TRUE`
`NO_FAKE_PASS = TRUE`
`HOT_PATH_PROTECTED = TRUE`
`HERMES_EXCLUDED = TRUE`
`PLUGIN_METHOD_REQUIRED = TRUE`
`DEPLOYMENT_REMOTE_APPLY = NOT_CLAIMED`
