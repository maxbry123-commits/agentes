# TAREA ACTUAL — Equipo de Programación — Auditoría agentes + X-Ray

**Fecha:** 2026-08-21
**Repositorio:** `maxbry123-commits/agentes`
**Estado del bloque:** PLAN VALIDADO / IMPLEMENTACIÓN DE GAPS NO INICIADA
**Método:** `PIPELINE/00_METODO_TRABAJO_Y_ARQUITECTURA.md`
**Recovery patch:** `PIPELINE/64_RECOVERY_PATCH_GAPS_WORDFLOW_2026-08-21.md`

## Objetivo
Auditar el repositorio `agentes`, realizar forense X-Ray del Wordflow de programación de code, cruzar documentación contra código real y preparar una tarea independiente para cada gap real antes de modificar código.

## Auditoría completada

- `GAPS_PROGRAMMING_WORDFLOW.md`: G-W1..G-W14 + R4 cerrados; residuales VENDOR/P1 y T49/BLOCK.
- `WORDFLOW_PROGRAMMING_FORENSIC_MAP.md`: identifica además ausencias/NOT VERIFIED en lifecycle global, persistencia de GapRegistry, FourPass global, reception auto-load, trazabilidad completa y audit history.
- `code_path_runner.py`: actualmente consulta `MockIntelligenceGateway` con `PATH_GATEWAY_DENY`; por ello la existencia de `RouterHTTPGateway` no equivale a VENDOR cerrado.
- `router_http.py`: existe cliente HTTP fail-closed para `ROUTER_URL`; necesita verificación/cableado real al hot path.
- `gap_registry.py`: lifecycle local existe, pero `_gaps` es memoria del objeto; no demuestra persistencia global.
- `forensic_core.py`: `run_four_passes()` existe dentro del enforcer; esto no demuestra un FourPassController global sobre todo el repo.
- `VerdictAuthority`: permanece como única autoridad de PASS.
- T49/C100: no se encontró una fuente primaria `PIPELINE/T49_C100.md`; se clasifica BLOCKED FOR SPECIFICATION y no se inventa el contrato.

## Bloque de resolución — 10 tareas

1. T01 VENDOR / Router real — **PLANNED**
2. T02 T49 / Claim C100 — **PLANNED / BLOCKED FOR SPECIFICATION** hasta encontrar fuente primaria
3. T03 State machine global persistente — **PLANNED**
4. T04 GapRegistry persistente — **PLANNED**
5. T05 FourPassController/global four-pass — **PLANNED**
6. T06 Auto-carga segura `reception/` + handoff — **PLANNED**
7. T07 DOC→REQUIREMENT→CODE→TEST→EVIDENCE — **PLANNED**
8. T08 Connectivity full chain — **PLANNED**
9. T09 Audit history append-only — **PLANNED**
10. T10 Fail-closed production/callers/post-verify — **PLANNED**

Cada tarea está descrita con alcance, entradas, salidas, 12 pasos, acceptance y verificaciones en `PIPELINE/64_RECOVERY_PATCH_GAPS_WORDFLOW_2026-08-21.md`.

## Gate obligatorio de cada tarea

`PLANNED → READY → BUILD → LOCAL_VERIFY_PASS → PUBLISHED → REMOTE_VERIFY_PASS → FORENSIC_PASS → DONE`

Fallo: `REPAIR_REQUIRED`; nunca avanzar por afirmación del agente.

## Ask Council — 12 pasos

1. Fuente primaria del gap.
2. Contrato existente reutilizable.
3. Código real que prueba el estado.
4. Documentación vs runtime.
5. Cambio mínimo.
6. Autoridad que debe ejecutar/verificar.
7. Dependencias.
8. Riesgo de integridad/seguridad.
9. Test que puede falsar PASS.
10. Evidencia remota.
11. Forense X-Ray requerido.
12. Condición exacta PASS→DONE.

## Estado de esta salida

**Auditoría documental:** PASS.
**Verificación cruzada documentación↔código:** PASS como clasificación.
**Código modificado:** NO.
**Gaps cerrados:** 0.
**Plan persistido:** PASS.
**Implementación:** PENDIENTE.
