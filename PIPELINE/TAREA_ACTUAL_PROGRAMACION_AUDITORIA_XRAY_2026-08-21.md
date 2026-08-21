# TAREA ACTUAL — Equipo de Programación — Auditoría agentes + X-Ray

**Fecha:** 2026-08-21
**Repositorio:** `maxbry123-commits/agentes`
**Estado del bloque:** EN PROGRESO
**Método:** PIPELINE/00_METODO_TRABAJO_Y_ARQUITECTURA.md

## Objetivo
Auditar el repositorio `agentes`, realizar forense X-Ray del Wordflow de programación de code, localizar el documento que contiene la lista de gaps/documentos relevantes y dejar trazabilidad persistente.

## Bloque de 10 tareas

1. **T1 — Intake y método:** leer README, README_METHOD y PIPELINE rector. Estado: TERMINADA.
2. **T2 — Inventario raíz:** auditar estructura principal, PIPELINE, engine, standards, CI y reglas. Estado: TERMINADA.
3. **T3 — Localizar mapa de gaps:** localizar GAPS_PROGRAMMING_WORDFLOW y documentos de puntos ausentes. Estado: TERMINADA.
4. **T4 — X-Ray arquitectura real:** contrastar arquitectura documentada con paths reales. Estado: TERMINADA.
5. **T5 — X-Ray ejecución:** reconstruir run_code_path y sus gates/enforcement. Estado: TERMINADA.
6. **T6 — X-Ray conectividad:** revisar DECLARED→REGISTERED→RESOLVED→INVOKED→EXECUTED→OUTPUT→BEHAVIOR. Estado: TERMINADA.
7. **T7 — X-Ray lifecycle:** revisar GapRegistry, OPEN→FIXED→VERIFIED→CLOSED y persistencia. Estado: TERMINADA documental; persistencia global queda NOT VERIFIED.
8. **T8 — X-Ray trazabilidad:** contrastar DOC→REQUIREMENT→CODE→TEST→EVIDENCE. Estado: TERMINADA documental; automatización completa queda ABSENT/PARTIAL.
9. **T9 — Clasificar gaps reales:** separar cerrados, residuales abiertos y ausencias/NOT VERIFIED. Estado: TERMINADA.
10. **T10 — Actualizar memoria PIPELINE:** registrar evidencia, pendientes y siguiente salida. Estado: EN PROGRESO hasta completar el registro forense final.

## 12 pasos de entrada/salida por tarea

1. Identificar TASK_ID.
2. Leer método rector.
3. Leer contexto y handoff.
4. Identificar fuentes.
5. Definir alcance.
6. Inventariar entradas.
7. Ejecutar auditoría determinista.
8. Registrar evidencia.
9. Comparar documentación vs código.
10. Clasificar REAL/PARTIAL/ABSENT/UNKNOWN.
11. Ejecutar verificación cruzada.
12. Registrar salida y estado en PIPELINE.

## Ask Council — 12 pasos

1. ¿Cuál es la fuente primaria?
2. ¿Qué exige el método?
3. ¿Qué existe realmente?
4. ¿Qué está documentado solamente?
5. ¿Qué está verificado?
6. ¿Qué está ausente?
7. ¿Qué contradicciones existen?
8. ¿Qué evidencia reproducible existe?
9. ¿Qué no puede afirmarse?
10. ¿Cuál es el riesgo técnico?
11. ¿Cuál es la acción mínima segura?
12. ¿Cuál es el siguiente gate de verificación?

## Hallazgos X-Ray actuales

### A. Gaps explícitos
`PIPELINE/GAPS_PROGRAMMING_WORDFLOW.md` registra G-W1..G-W14 como cerrados y R4 cerró G-W14b, G-W13b y G-W3b. Quedan residuales: `VENDOR` (P1, ROUTER_URL + engines reales) y `T49` (BLOCK, Claim C100). No se publica PASS fingido.

### B. Arquitectura REAL
El mapa forense identifica `run_code_path`, quality_bar, goal_lock, cognitive_loop, evidence packet, programming pipeline, pre/post gates, COPY-FIRST, AST symbols, forensic contract, VerdictAuthority, smoke tests, WiringGraph, scope/requirements y mission edges como componentes reales/documentados según cada caso.

### C. Ausencias/NOT VERIFIED
El mapa forense declara como AUSENTE/NOT VERIFIED: state machine global persistente OPEN→FIXED→VERIFIED→CLOSED, GapRegistry runtime completo, FourPassController global independiente y auto-carga de `reception/` en `run_code_path`.

### D. Trazabilidad
DOC→REQUIREMENT es ABSENT en runtime; REQUIREMENT→CODE y CODE→TEST son PARTIAL; TEST→EVIDENCE es PARTIAL. No existe detector automático completo de todos los mismatches documentales/código/tests/evidence.

### E. Conectividad
La conectividad está declarada como REAL/PARTIAL según etapa. El documento advierte explícitamente: IMPORTABLE ≠ FUNCTIONALLY CONNECTED.

### F. Persistencia
Instance state y sidecars/capacidades de artefactos existen; audit history append-only no está verificado y Gap DB está ausente.

## Documento clave de gaps
`PIPELINE/GAPS_PROGRAMMING_WORDFLOW.md`

## Documento clave de forense
`PIPELINE/WORDFLOW_PROGRAMMING_FORENSIC_MAP.md`

## Documento maestro
`PIPELINE/WORDFLOW_PROGRAMMING_MASTER.md`

## Siguiente salida
Completar T10 con el registro forense final, localizar cualquier archivo adicional de lista/gaps que sea más específico que GAPS_PROGRAMMING_WORDFLOW, y preparar la matriz de gaps priorizada antes de tocar código.
