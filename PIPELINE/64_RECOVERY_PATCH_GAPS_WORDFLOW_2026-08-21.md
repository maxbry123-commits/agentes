# RECOVERY PATCH — GAPS WORDFLOW PROGRAMMING — 2026-08-21

**Repo:** `maxbry123-commits/agentes`
**Rol:** Equipo de programación
**Estado:** PLAN VALIDADO / IMPLEMENTACIÓN AÚN NO INICIADA
**Autoridad:** `PIPELINE/00_METODO_TRABAJO_Y_ARQUITECTURA.md`
**Fuentes primarias:** `GAPS_PROGRAMMING_WORDFLOW.md`, `WORDFLOW_PROGRAMMING_FORENSIC_MAP.md`, `WORDFLOW_PROGRAMMING_MASTER.md`, código real bajo `extensions/wordflow*`.

## 0. Regla de recuperación

Este archivo es un mapa ejecutable de recuperación. Si se pierde contexto, leer en este orden:

`README → PIPELINE/00 → 56 → 59 → 58 → 57 → 60 → LISTA/GAPS → este parche → completion records → código → tests`.

No declarar PASS/DONE por afirmación del agente. Cada tarea requiere evidencia, commit, lectura remota y auditoría forense. Si una verificación falla: `REPAIR_REQUIRED`, no avanzar.

## 1. Auditoría cruzada que originó el plan

### Gap residual VENDOR — P1
**Documento:** `PIPELINE/GAPS_PROGRAMMING_WORDFLOW.md`.

**Código cruzado:** `extensions/wordflow_kernel/gateway/router_http.py` sí implementa `RouterHTTPGateway`, usa `ROUTER_URL`, soporta `ROUTER_TOKEN_REF`/`ROUTER_TOKEN` y fail-closed si falta URL; `gateway/__init__.py` lo exporta. Sin embargo, `extensions/wordflow/engine/code_path_runner.py` ejecuta actualmente `MockIntelligenceGateway(fixed_text="PATH_GATEWAY_DENY")` dentro de `consult_path_gateway()`. Por tanto, la existencia del cliente HTTP no demuestra que el hot path use Router/engines reales. Estado forense: **PARTIAL / NOT VERIFIED**, no PASS.

### Gap residual T49 — BLOCK / Claim C100
El documento de gaps lo marca BLOCK. No se encontró un archivo `PIPELINE/T49_C100.md`; por tanto no se inventa su definición. El cierre exige primero localizar la fuente exacta de C100 y luego reproducir el claim contra código/tests/evidence. Estado: **BLOCKED FOR SPECIFICATION**, no PASS.

### Gap L1 — State machine global persistente
El código `GapRegistry` sí implementa transiciones locales `OPEN→FIXED→VERIFIED→CLOSED` y prohíbe saltos inválidos, pero almacena `_gaps` solamente en memoria del objeto. El mapa forense declara persistencia global NOT VERIFIED. Estado: **PARTIAL**.

### Gap L2 — GapRegistry runtime/persistencia
`GapRegistry` existe y se usa desde `run_code_path`, pero no existe en la evidencia revisada una base/almacén persistente de gaps. Estado: **PARTIAL runtime / ABSENT persistence**.

### Gap L3 — FourPassController global
`forensic_core.py` sí tiene `run_four_passes()` con STRUCTURE/CONNECTIVITY/BEHAVIOR/FORENSIC_CLOSURE dentro del enforcer, pero el mapa forense indica que no hay cuatro runners independientes sobre todo el árbol. Estado: **PARTIAL**, no debe cerrarse fingiendo que el enforcer local equivale a un controller global.

### Gap L4 — Auto-carga `reception/`
El mapa forense declara auto-discovery de `reception/` ABSENT en `run_code_path`. El runner recibe `raw_input` y parámetros explícitos; no se ha demostrado carga automática de documentos `reception/`. Estado: **ABSENT/NOT VERIFIED**.

### Gap L5 — DOC→REQUIREMENT
El mapa declara ABSENT en runtime. El master usa requisitos/medidas, pero no se ha demostrado un parser/runtime que convierta documentos en requirements trazables. Estado: **ABSENT**.

### Gap L6 — REQUIREMENT→CODE / CODE→TEST / TEST→EVIDENCE
El mapa declara PARTIAL. Hay `scope_measure`, smoke y evidence packets, pero no un detector automático completo de mismatches entre los cuatro niveles. Estado: **PARTIAL**.

### Gap L7 — Conectividad funcional completa
La cadena `DECLARED→REGISTERED→RESOLVED→INVOKED→EXECUTED→OUTPUT_CONSUMED→BEHAVIOR_VERIFIED` está definida y parte está medida; `OUTPUT_CONSUMED` y callers completos permanecen UNKNOWN/PARTIAL. Estado: **PARTIAL/UNKNOWN**.

### Gap L8 — Audit history append-only / memoria de auditoría
El mapa declara NOT VERIFIED. Instance store, sidecars y PolicySnapshot no equivalen a un audit history append-only global. Estado: **NOT VERIFIED**.

### Gap L9 — `enforce_post_verify=False`
El mapa documenta riesgo de bypass cuando el post verify puede desactivarse. El cierre debe comprobar que ningún perfil de producción pueda saltar el veredicto obligatorio y que los tests demuestren fail-closed. Estado: **RISK / NOT CLOSED**.

### Gap L10 — Context/handoff default
La arquitectura documenta que los parámetros del runner tienen defaults seguros en la versión actual, pero el mapa histórico señala riesgo de defaults True en ciertos callers/configuraciones. La tarea debe verificar todos los callers reales y configuración, no asumir por el archivo aislado. Estado: **NEEDS CROSS-CALLER AUDIT**.

## 2. Bloque de 10 tareas — una tarea por gap/categoría

### T01 — VENDOR / Router real
**Objetivo:** demostrar y, si corresponde, cablear el único gateway RouterHTTP al hot path sin crear una segunda autoridad.

**Entrada:** `router_http.py`, `intelligence.py`, `code_path_runner.py`, configuración/CI.
**Salida:** código cableado + tests de router real/fail-closed + evidencia de provider.
**12 pasos:** intake → método → callers → gateway contract → config → tests actuales → diseñar mínimo cambio → implementar COPY/ADAPT → local verify → commit → remote read-back → forensic audit.
**Acceptance:** `ROUTER_URL` configurado usa RouterHTTP; ausencia/unreachable produce DENY/ERROR fail-closed; mock solo en dev/test explícito; ningún vendor directo; `VerdictAuthority` sigue siendo autoridad.
**Verificaciones mínimas:** import, unit tests, fake HTTP contract test, fail-closed test, no-secret scan, remote read-back, diff audit, forensic code audit.
**Estado:** PLANNED — no PASS todavía.

### T02 — T49 / Claim C100
**Objetivo:** localizar la especificación primaria de C100 y cerrar el claim solamente con evidencia reproducible.

**Regla:** si no existe definición primaria, `BLOCKED`; nunca inventar C100.
**12 pasos:** localizar fuentes → identificar owner → leer contrato → mapear código → mapear tests → definir evidencia → reproducir claim → clasificar REAL/PARTIAL/ABSENT → implementar si existe fix definido → verificar → commit → forensic closure.
**Acceptance:** C100 tiene fuente primaria, código, test y evidence o queda explícitamente BLOCKED con causa.
**Verificaciones:** búsqueda repo, referencias cruzadas, test reproducible, evidence packet, remote read-back, revisión de diff y VerdictAuthority.
**Estado:** PLANNED/BLOCKED FOR SPEC si no aparece fuente.

### T03 — State machine global persistente
**Objetivo:** convertir lifecycle local en estado persistente con ownership único.

**12 pasos:** identificar store → contrato de estados → schema → transiciones → atomicidad → concurrencia → recovery → migration → tests → local verify → remote verify → forensic audit.
**Acceptance:** OPEN→FIXED→VERIFIED→CLOSED persistente; saltos inválidos bloqueados; CLOSED terminal; restart conserva estado; no segunda autoridad.
**Verificaciones:** transition matrix completa, restart test, corruption/error-path test, concurrent update test, persistence read-back, forensic audit.
**Estado:** PLANNED.

### T04 — GapRegistry persistente
**Objetivo:** persistir `gap_id`, lifecycle, revisions, evidence y verification.

**12 pasos:** inventario del registry actual → store autorizado → schema → repository/service → write path → read path → lifecycle integration → counters → migration → tests → remote verify → forensic audit.
**Acceptance:** gaps sobreviven reinicio; cada transición deja revision/evidence; `new_gaps_after_fix` es auditable; no se confunde con simples counters.
**Verificaciones:** CRUD/lifecycle, restart, malformed record, duplicate gap_id, concurrent write, remote read-back.
**Estado:** PLANNED.

### T05 — FourPassController global
**Objetivo:** determinar si se requiere un controller global real y, si sí, implementarlo sin duplicar `ForensicProgrammingEnforcer`.

**12 pasos:** definir alcance → inventariar `run_four_passes` → callers → repo-wide scope → pass contracts → dependency order → reuse existing enforcer → implementation → tests → cross-tree audit → remote verify → forensic closure.
**Acceptance:** four passes independientes o evidencia formal de que el enforcer existente satisface el contrato; nunca cerrar por nombre de clase.
**Verificaciones:** pass N blocking, all-four required, repo-wide coverage, no duplicate authority, CI test.
**Estado:** PLANNED.

### T06 — Auto-carga `reception/` + document handoff
**Objetivo:** resolver el gap documental sin introducir lectura implícita insegura.

**12 pasos:** definir allowed roots → file discovery → ordering/versioning → provenance → ContextManifest → handoff → size/security limits → parse → evidence → tests → remote verify → forensic audit.
**Acceptance:** solo documentos autorizados; provenance completa; documentos obsoletos detectables; secretos bloqueados; no carga arbitraria.
**Verificaciones:** empty/missing reception, duplicate docs, obsolete version, malicious path, secret scan, evidence provenance.
**Estado:** PLANNED.

### T07 — DOC→REQUIREMENT→CODE→TEST→EVIDENCE
**Objetivo:** crear trazabilidad determinista mínima y detector de mismatches.

**12 pasos:** definir IDs → parser de requirements → source anchors → code mapping → test mapping → evidence mapping → mismatch classes → report → fail policy → tests → remote verify → forensic audit.
**Acceptance:** detectar DOC_ONLY, CODE_ONLY, DOC_CODE_MISMATCH, CODE_TEST_MISMATCH, TEST_EVIDENCE_MISMATCH; output auditable y fail-closed según severidad.
**Verificaciones:** fixture positivo, cada mismatch negativo, renamed symbol, missing test, stale evidence, remote report.
**Estado:** PLANNED.

### T08 — Connectivity full chain
**Objetivo:** probar funcionalmente cada eslabón, no solo importabilidad.

**12 pasos:** inventario nodes → declarations → registry → resolution → invocation → execution → output consumer → behavior → orphan detection → fixture end-to-end → remote verify → forensic audit.
**Acceptance:** cada required component tiene caller real y evidencia; orphan/never-invoked required path bloquea o queda clasificado explícitamente.
**Verificaciones:** wiring graph, dynamic call trace, E2E fixture, output-consumer assertion, orphan report, CI.
**Estado:** PLANNED.

### T09 — Audit history append-only
**Objetivo:** persistir eventos forenses y completion records sin reescritura.

**12 pasos:** event schema → append store → hash/chaining si aplica → writer authority → read API → retention → recovery → integrity test → unauthorized mutation test → remote verify → forensic audit → completion record.
**Acceptance:** historial no editable por agentes; cada evento tiene task/mission/revision/time/evidence; lectura remota reproduce la secuencia.
**Verificaciones:** append, tamper attempt, restart, duplicate event, ordering, integrity hash, remote read-back.
**Estado:** PLANNED.

### T10 — Fail-closed production / callers / post-verify
**Objetivo:** eliminar rutas que permitan ejecutar o declarar PASS saltándose gates obligatorios.

**12 pasos:** localizar callers → flags/defaults → profiles → `enforce_post_verify` → CI → tests bypass → fix → regression → scope/diff → remote verify → forensic audit → completion record.
**Acceptance:** producción no puede desactivar gates REQUIRED; skip != pass; PASS solo desde VerdictAuthority; context/handoff no se aceptan por afirmación del agente.
**Verificaciones:** prod config, dev config, bypass test, missing-core test, missing-evidence test, four-pass failure, remote CI, forensic audit.
**Estado:** PLANNED.

## 3. Ask Council — 12 pasos para CADA tarea

1. ¿Cuál es la fuente primaria del gap?
2. ¿Qué contrato existente debe reutilizarse?
3. ¿Qué código real demuestra el estado actual?
4. ¿Qué parte es solo documentación?
5. ¿Qué cambio mínimo resuelve el gap?
6. ¿Qué autoridad existente debe ejecutar/verificar?
7. ¿Qué dependencias bloquean el cambio?
8. ¿Qué riesgo de seguridad/integridad introduce?
9. ¿Qué test falsaría la afirmación de PASS?
10. ¿Qué evidencia remota probará persistencia?
11. ¿Qué forense X-Ray debe repetirse?
12. ¿Qué condición exacta permite `PASS → DONE`?

## 4. Regla de estado

Cada tarea debe evolucionar estrictamente:

`PLANNED → READY → BUILD → LOCAL_VERIFY_PASS → PUBLISHED → REMOTE_VERIFY_PASS → FORENSIC_PASS → DONE`

Cualquier fallo:

`* → REPAIR_REQUIRED → BUILD/VERIFY nuevamente`.

Nunca:

`CLAIM → PASS`.

## 5. Commit policy

Un commit por intención/gap. No mezclar T01–T10 en un mismo commit cuando se empiece la implementación. Cada commit debe registrar task_id, archivos, tests y siguiente gate.

## 6. Recuperación

Si se pierde contexto, NO usar memoria del chat como fuente primaria. Leer este parche + `PIPELINE/00` + gaps + forensic map + código + completion records. El siguiente task solo se inicia cuando el anterior tenga `DONE` real y autorización.

## 7. Estado del bloque

- Auditoría documental: **PASS**.
- Auditoría cruzada código: **PASS como clasificación**, no como cierre de gaps.
- VENDOR: **PARTIAL / OPEN**.
- T49: **BLOCKED FOR SPECIFICATION**.
- L1–L10: **PLANNED / OPEN**.
- Código modificado en esta salida: **NO**.
- PASS de implementación: **NO**.
- DONE del bloque: **NO**.
