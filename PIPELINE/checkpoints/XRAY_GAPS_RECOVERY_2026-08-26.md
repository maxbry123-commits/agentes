# XRAY FORENSE — G1–G7 — CHECKPOINT + PARCHE DE RECUPERACIÓN

Fecha: 2026-08-26
Repositorio de verdad: `maxbry123-commits/agentes`
Rama: `main`
Política: FAIL-CLOSED / NO_INVENTAR / NO_FAKE_PASS / NO_APAGAR_MONOLITO

## 1. Objetivo

Auditar de nuevo G1–G7 contra evidencia actualmente visible en `main`, identificar exactamente qué falta para cada acceptance y dejar un parche de recuperación operativo. Este checkpoint NO convierte UNKNOWN/OPEN en PASS.

## 2. Fuentes canónicas revisadas

- `PIPELINE/PASO3_ORGANIZACION_CODIGO_REAL_YAIWES.md`
- `PIPELINE/checkpoints/GAP_REGISTER_2026-08-26.md`
- `PIPELINE/checkpoints/S10_LOOP_FINAL_2026-08-26.md`
- `PIPELINE/checkpoints/OPENCLAW_CABLE_CI_PASS.md`
- `PIPELINE/CI_LAST_RESULT.md`
- `.github/workflows/verify-gap-indexes.yml`
- `Refactoria/G1/new/build_programming_symbol_index.py`
- `Refactoria/G3/new/build_test_assert_index.py`

## 3. Estado forense actual

| Gap | Estado | Evidencia actual | Falta exacta para PASS |
|---|---|---|---|
| G1 | OPEN | Existe exportador determinista que reutiliza `build_symbol_index()` y genera MD/JSON en el destino canónico | Una ejecución CI real posterior al cambio debe generar los artefactos y éstos deben leerse de vuelta desde `main`; debe comprobarse que el índice no está vacío y contiene símbolos del runner/pipeline. |
| G2 | OPEN / PARCIAL | Existe mapa C-19 y contratos derivados de fuentes reales ya identificadas | Falta cerrar la lista de stages realmente nombrados por `code_path_runner.py`/`programming_pipeline.py` y disponer de un schema JSON válido por cada stage existente; stages ausentes deben permanecer como residual OPEN. No crear 19 schemas por número. |
| G3 | OPEN | Existe scanner AST determinista para `extensions/wordflow/tests` y `extensions/wordflow_kernel/tests` | Una ejecución CI real debe producir `TEST_ASSERT_INDEX.md/.json`, verificar que `file_count >= 1` y que todos los archivos indexados tienen `parse=PASS`, y leer el resultado desde `main`. |
| G4 | OPEN | `PIPELINE/CI_LAST_RESULT.md` es histórico y real; no corresponde necesariamente al cable loop actual | Falta un artifact/trace-history correspondiente a una ejecución actual del workflow/cable. Si no se puede obtener, crear solo runbook determinista y conservar OPEN. No fabricar logs. |
| G5 | OPEN/BLOCKER-T-GAP | PASO3 afirma que existe una rama histórica `programming-modular-v1` con p01…p12, pero no se encontró evidencia verificable en la búsqueda actual de `main` para el conjunto completo | Debe verificarse la rama/refs y localizar los 12 fuentes reales. Si no están accesibles, registrar BLOCKER-T-GAP con refs/paths buscados y NO generar 12 módulos. Si aparecen, aislar source, construir wire real y ejecutar pruebas de paridad contra `code_path_runner.py`. |
| G6 | CLOSED en alcance OpenClaw | `OPENCLAW_CABLE_CI_PASS.md` registra workflow/test/commit y el cable OpenClaw HTTP | Mantener cerrado solo para el adapter OpenClaw comprobado. Para otros adapters del catálogo no existe evidencia suficiente y no deben declararse cerrados por extensión. |
| G7 | CLOSED en alcance de ruta OpenClaw | `OPENCLAW_CABLE_CI_PASS.md` registra PASS de `test_openclaw_http.py`; Hermes está excluido | Mantener cerrado solo para la ruta OpenClaw comprobada. No afirmar que existe un body Hermes ni un body nativo adicional sin source real. |

## 4. Auditoría de G1

Fuente nueva: `Refactoria/G1/new/build_programming_symbol_index.py`.

Comprobaciones del código:
- importa `build_symbol_index` desde `extensions.wordflow.standards.symbol_index`;
- roots reales: `extensions/wordflow/engine` y `extensions/wordflow/standards`;
- salida canónica: `agente-yaiwes/control-governance/symbol-index-wiring-graph/`;
- produce MD y JSON;
- no modifica `code_path_runner.py`.

### Recuperación G1

1. Ejecutar el entrypoint en runner limpio.
2. Verificar salida no vacía.
3. Verificar `code_path_runner`, `run_code_path` y `CodePathError` en el MD.
4. Verificar JSON parseable.
5. Comparar artefacto generado con la versión registrada.
6. Solo con ejecución CI real + readback marcar CLOSED.

## 5. Auditoría de G2

El PASO3 canónico exige schemas C-19 solo para stages que el código nombra. La regla de recuperación es conservadora: derivar contratos de las firmas/estructuras reales; no inventar stages.

### Recuperación G2

1. Leer `code_path_runner.py` solo lectura.
2. Leer `programming_pipeline.py`.
3. Enumerar nombres de stages/operaciones literalmente presentes.
4. Mapear cada stage existente a un JSON Schema mínimo.
5. Validar un ejemplo construido de la entrada real de cada stage.
6. Registrar los stages inexistentes como residual OPEN.
7. Crear checkpoint G2 con lista exacta y evidencia.

## 6. Auditoría de G3

Fuente nueva: `Refactoria/G3/new/build_test_assert_index.py`.

El scanner usa AST, recorre ambos roots de tests y registra `assert` y llamadas cuyo atributo comienza con `assert`.

### Recuperación G3

1. Ejecutar en CI limpio.
2. Confirmar `file_count >= 1`.
3. Confirmar `parse=PASS` para cada archivo.
4. Confirmar MD + JSON.
5. Leer artefactos desde `main` después de la ejecución.
6. Solo entonces cerrar G3.

## 7. Auditoría de G4

El archivo histórico `PIPELINE/CI_LAST_RESULT.md` contiene PASS T01–T10B, pero el GAP_REGISTER correctamente lo considera insuficiente para demostrar el trace del loop actual.

### Recuperación G4

- Obtener run real del workflow relevante.
- Obtener job, steps y logs.
- Obtener artifact si existe.
- Registrar SHA, run ID, workflow y resultado.
- Copiar solo evidencia real a `agente-yaiwes/observability/trace-history/`.
- Si GitHub no ofrece una ejecución recuperable: `OPEN + runbook`; jamás inventar el log.

## 8. Auditoría de G5

El documento PASO3 declara una rama `programming-modular-v1` con `p01_context_gate.py` … `12_return.py` y dice que `runner.py` bridgea al legacy. Esto es una afirmación del mapa canónico, no prueba suficiente de que esos archivos estén disponibles ahora en `main`.

### Recuperación G5

1. Buscar cada nombre exacto en `main` y refs accesibles.
2. Registrar los paths/ref encontrados.
3. Si faltan uno o más, crear `BLOCKER-T-GAP.md` con source/impact/recommended_action.
4. Si aparecen todos, copiar exacto a `despliegue/refactoria/G5/source/` y `Refactoria/G5/source/`.
5. Crear nueva implementación solo en `Refactoria/G5/new/`.
6. Ejecutar paridad contra el hot path.
7. Integrar solo después de tres verificaciones PASS.

## 9. Auditoría G6/G7

La evidencia actual de OpenClaw es específica: `OPENCLAW_CABLE_CI_PASS.md` registra workflow `verify-openclaw-cable`, commit `a9cebda...`, test `extensions/wordflow_kernel/tests/test_openclaw_http.py`, ejecución GitHub Actions y origen OpenClaw Gateway `/v1/chat/completions`.

No extrapolar esta evidencia a Hermes ni a adapters no probados.

## 10. Hot path — regla de recuperación

`extensions/wordflow/engine/code_path_runner.py` permanece como fuente operativa. No se reescribe, apaga, reemplaza ni corta hasta que exista paridad de tests demostrable en el destino modular.

## 11. Regla de plugin para este ciclo

La guía de `Método de trabajo/registro de plugins/GUIA_REGISTRO_PLUGINS_Y_CABLEADO.md` es obligatoria para los cambios de este ciclo.

Todo archivo nuevo que requiera futuras conexiones debe quedar registrado/preparado con su mecanismo de plugin desde su creación. Las futuras conexiones se realizan por el plugin/contrato/cable; no se modifica el archivo estable para añadir conexiones.

## 12. Próxima secuencia de recuperación

`G1 CI/readback → G3 CI/readback → G2 stage audit → G4 trace → G5 source/ref audit → revisión final G6/G7 → X-Ray final → checkpoint final`.

## 13. Criterio de cierre

Un gap pasa a CLOSED únicamente cuando su acceptance está demostrada por artefacto, test, contrato o evidencia de fuente correspondiente. OPEN/BLOCKED permanece explícito cuando falta evidencia.

**NO_FAKE_PASS = obligatorio.**
