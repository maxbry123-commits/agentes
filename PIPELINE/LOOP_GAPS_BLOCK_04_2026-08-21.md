# LOOP GAPS BLOCK 04 — PLAN DE CIERRE Y ESTADO FORENSE

Fecha: 2026-08-21
Repo: maxbry123-commits/agentes
Rol: equipo de programación

## 0. Guía leída antes de este bloque

Fuentes verificadas:
- `AGENTS.md`
- `PIPELINE/00_METODO_TRABAJO_Y_ARQUITECTURA.md`
- `PIPELINE/ADVANCED_ENGINEERING_STANDARD_V3.md`
- `PIPELINE/FORENSIC_CODE_AUDIT.md`
- `PIPELINE/64_RECOVERY_PATCH_GAPS_WORDFLOW_2026-08-21.md`
- `PIPELINE/GAPS_PROGRAMMING_WORDFLOW.md`
- `PIPELINE/WORDFLOW_PROGRAMMING_FORENSIC_MAP.md`
- `PIPELINE/WORDFLOW_PROGRAMMING_MASTER.md`
- `PIPELINE/FORENSE_PASADA_01_STRUCTURE.md`
- `PIPELINE/FORENSE_PASADA_02_CONNECTIVITY.md`
- `PIPELINE/FORENSE_PASADA_03_BEHAVIOR.md`
- `PIPELINE/FORENSE_PASADA_04_CIERRE.md`
- `PIPELINE/56_METODO_COPY_MOVE_REUSE_INDEX.md`
- `PIPELINE/59_PATCH_GIT_01.md`
- `PIPELINE/58_CROSS_REPOSITORY_TRANSFER.md`
- `PIPELINE/60_REUSE_FIRST.md`

Regla ejecutable:
`CONTEXT/HANDOFF → COPY-FIRST → IMPLEMENT(COPY|ADAPT|GENERATE) → WIRE → LOCAL_VERIFY → PUBLISH → REMOTE_VERIFY → FORENSIC_4_PASS → VERDICT → DONE|REPAIR_REQUIRED`

## 1. ESTADO REAL — NO FINGIR CIERRE

### RESUELTO / PASS de auditoría

- T02: especificación C100 localizada y cruzada. C100 sigue `NO`; T49 sigue bloqueado. Auditoría de especificación PASS, resolución DONE NO.
- T01: contrato fail-closed de `RouterHTTPGateway` cubierto por `test_router_http_gateway.py`; commit `360bd903da1ba591feda0226af413ffcb5af6b06`; remote read-back PASS. Implementación del hot path NO DONE.
- Reception: `kernel/reception/convert.py` YA invoca `input_compiler`, `task_classifier`, `locate_phase` y `attach_plugin`; la evidencia actual contradice el mapa forense histórico que decía que input_compiler no estaba invocado. Este gap debe reclasificarse como `DOCUMENTATION_FORENSIC_DRIFT` y verificarse con test real antes de cerrar.
- KernelExtMotor: YA tiene dispatch `ingest/convert/reception` hacia `kernel.reception.convert.ingest`.
- `VerdictAuthority`, `ForensicProgrammingEnforcer`, QualityDAG, COPY-FIRST, EvidenceVerifier y ContextManifest existen.
- `InstanceStore/PersistentRegistry` demuestra persistencia de estado de instancia, pero NO demuestra persistencia de GapRegistry.

### PENDIENTE / OPEN

- T01: cablear el hot path `consult_path_gateway()` a RouterHTTP/factory sin romper el contrato actual; ajustar tests y verificar producción.
- T02: C100/T49 sigue BLOCKED por evidencia de producción/vendor/engines/git apply; no inventar PASS.
- T03: state machine global persistente de gaps.
- T04: GapRegistry persistente.
- T05: FourPassController global repo-wide o demostración formal de equivalencia.
- T06: recepción documental completa: auto-discovery/versionado/provenance y handoff seguro; parte del runtime ya existe.
- T07: DOC→REQ→CODE→TEST→EVIDENCE automático y mismatch detector.
- T08: connectivity completa y consumidores reales del output.
- T09: audit history append-only global.
- T10: auditoría y cierre fail-closed de todos los callers/configuraciones; no asumir que un archivo aislado basta.
- X-Ray histórico: duplicados de homes, catálogos `pending_mount`, paths fantasma y consumidores desconocidos siguen pendientes de reconciliación.

## 2. T01 — PLAN DE CIERRE

Objetivo: eliminar MockIntelligenceGateway del hot path de producción y conservar mock solo como dependencia explícita de tests/dev.

Fuente existente: `extensions/wordflow_kernel/gateway/router_http.py` y `build_gateway_from_env()`.

10 vías si aparece un gap:
1. inyección directa RouterHTTP;
2. factory `build_gateway_from_env()`;
3. adaptador de `GatewayResponse`;
4. parámetro gateway para test;
5. ROUTER_URL obligatorio en prod;
6. mock solo dev/test explícito;
7. contrato HTTP determinista;
8. test anti-instanciación Mock en hot path;
9. evidencia source/SHA/diff;
10. cuatro pasadas + VerdictAuthority.

Acceptance: Router real con URL; URL ausente/unreachable fail-closed; no vendor directo; tests actualizados; remote read-back; forense PASS.

## 3. T02 — PLAN DE CIERRE

Objetivo: desbloquear C100 solo con evidencia reproducible.

10 vías:
1. localizar engine real;
2. localizar runner de producción;
3. localizar vendor adapter autorizado;
4. ejecutar prueba real;
5. capturar evidence packet;
6. verificar Router→engine;
7. verificar git apply;
8. verificar no-fake path;
9. repetir 4-pass;
10. si falta cualquier pieza, mantener BLOCKED.

No se permite convertir documentación en evidencia de producción.

## 4. T03 — STATE MACHINE PERSISTENTE

Reutilización prioritaria: `InstanceStore` como patrón, pero no copiar su semántica sin revisar ownership.

10 vías:
1. GapStore basado en JSON atómico;
2. SQLite;
3. repository append-only;
4. sidecar por gap;
5. store dentro InstanceStore con namespace;
6. event log;
7. journal + snapshot;
8. git-backed state;
9. durable KV;
10. adapt existing persistent store si ya existe.

Acceptance: restart conserva estado; OPEN→FIXED→VERIFIED→CLOSED; saltos inválidos; CLOSED terminal; concurrencia y corrupción probadas.

## 5. T04 — GAPREGISTRY PERSISTENTE

GapRegistry actual es memoria de proceso. No crear segunda autoridad: separar lifecycle authority de storage.

10 vías:
1. repository/service sobre GapStore;
2. SQLite;
3. JSON journal;
4. append-only event store;
5. instance namespace;
6. git evidence record;
7. content-addressed records;
8. durable KV;
9. sidecar por misión;
10. reutilizar persistence existente si X-Ray encuentra uno.

Acceptance: gap_id único, revision/evidence por transición, restart, duplicate, corruption, concurrent write.

## 6. T05 — FOUR PASS GLOBAL

Primero demostrar si `ForensicProgrammingEnforcer.run_four_passes()` puede ampliarse por scope antes de crear controller.

10 vías:
1. controller que recorra repo;
2. adapt existing enforcer con scope;
3. orchestration wrapper;
4. pass registry;
5. CI-driven four pass;
6. graph-driven pass;
7. tree snapshot pass;
8. artifact-based pass;
9. reuse forensic reports;
10. document equivalence si no requiere controller nuevo.

Acceptance: STRUCTURE/CONNECTIVITY/BEHAVIOR/FORENSIC_CLOSURE independientes y bloqueantes.

## 7. T06 — RECEPTION/HANDOFF

La implementación actual ya contiene compile/classify/locate/plugin. El trabajo restante es provenance/discovery/versioning/consumer.

10 vías:
1. manifest de reception;
2. discovery allowlist;
3. version resolver;
4. stale-doc detector;
5. provenance hash;
6. ContextManifest injection;
7. path traversal guard;
8. secret scan;
9. deterministic ordering;
10. E2E reception→compile→phase→plugin→consumer.

Acceptance: ningún documento no autorizado entra al contexto; provenance completa; obsolete detectado; output consumido.

## 8. T07 — TRAZABILIDAD

10 vías:
1. requirement IDs en docs;
2. parser literal;
3. symbol map AST;
4. test-name mapping;
5. evidence packet anchors;
6. mismatch detector;
7. graph database local;
8. JSON trace matrix;
9. CI trace gate;
10. reuse `scope_measure` + `WiringGraph` + EvidenceVerifier.

Acceptance: DOC_ONLY, CODE_ONLY, DOC_CODE_MISMATCH, CODE_TEST_MISMATCH, TEST_EVIDENCE_MISMATCH detectables.

## 9. T08 — CONNECTIVITY

10 vías:
1. WiringGraph static;
2. AST caller graph;
3. runtime trace;
4. invocation counters;
5. output consumer registry;
6. E2E fixture;
7. catalog reconciliation;
8. orphan detector;
9. required-path detector;
10. CI connectivity gate.

Acceptance: DECLARED→REGISTERED→RESOLVED→INVOKED→EXECUTED→OUTPUT_CONSUMED→BEHAVIOR_VERIFIED.

## 10. T09 — AUDIT HISTORY

10 vías:
1. append-only JSONL;
2. SQLite event table;
3. hash chain;
4. Git completion records;
5. content-addressed evidence;
6. immutable object store;
7. instance event log;
8. journal + snapshot;
9. signed event envelope;
10. reuse engine EvidencePacket chain.

Acceptance: no mutation, ordering, restart, tamper detection, remote reproducibility.

## 11. T10 — FAIL CLOSED

10 vías:
1. search every caller;
2. search every config profile;
3. remove/lock production bypass;
4. default false for context/handoff;
5. require ContextManifest;
6. require handoff artifact;
7. forbid skip→pass;
8. test missing-core;
9. test missing-evidence;
10. CI gate + VerdictAuthority.

Acceptance: no production route can disable REQUIRED post-verify; PASS only VerdictAuthority; missing context/handoff BLOCK.

## 12. 12 GOALS DEL BLOQUE

1. Mantener GitHub como verdad.
2. Leer método antes de code.
3. COPY-FIRST antes de generar.
4. Reutilizar autoridades existentes.
5. Un gap = una tarea.
6. Un commit = una intención.
7. Tests antes del cierre.
8. Remote read-back obligatorio.
9. X-Ray cuatro pasadas.
10. VerdictAuthority decide PASS.
11. Si falla, REPAIR_REQUIRED.
12. No declarar DONE por documentación.

## 13. ASK COUNCIL 12 PASOS

1. ¿Qué gap exacto se está cerrando?
2. ¿Cuál es la fuente primaria?
3. ¿Existe código reutilizable?
4. ¿Cuál es la autoridad única?
5. ¿Qué callers dependen del contrato?
6. ¿Cuál es el cambio mínimo?
7. ¿Qué puede romperse?
8. ¿Qué test lo falsifica?
9. ¿Qué evidencia remota lo prueba?
10. ¿Qué X-Ray debe pasar?
11. ¿Qué estado debe quedar en PIPELINE?
12. ¿VerdictAuthority permite DONE o exige REPAIR/BLOCK?

## 14. GATE DE CADA TAREA

`PLANNED → READY → BUILD → LOCAL_VERIFY_PASS → PUBLISHED → REMOTE_VERIFY_PASS → FORENSIC_PASS → DONE`

Fallo: `REPAIR_REQUIRED`.

## 15. RECOVERY / SIGUIENTE LOOP

No reiniciar T02 ni el test T01 ya publicados.

Orden siguiente:
1. T01 wiring + tests.
2. T06/T08 aprovechando que reception ya tiene compile/classify/phase/plugin.
3. T10 callers/configuración.
4. T03/T04 persistencia con ownership único.
5. T05 controller/equivalence.
6. T07 trazabilidad.
7. T09 audit history.
8. T02 solo cuando exista evidencia de producción real.

Estado del bloque: `PLANNING_COMPLETE / IMPLEMENTATION_IN_PROGRESS / NOT_DONE`.

No se declara C100, V1 100%, T01 ni el bloque como DONE sin las verificaciones indicadas.
