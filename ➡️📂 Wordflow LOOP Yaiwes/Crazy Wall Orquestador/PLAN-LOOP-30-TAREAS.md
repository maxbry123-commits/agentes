# PLAN LOOP — 30 TAREAS — Wordflow LOOP Yaiwes

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP` · cola `1x1`.
Objetivo final: convertir documentos/proyectos YAIWES en requisitos trazables, tareas de programación, código ejecutable modular integrado en el microkernel YAIWES, plugins/cableado, tests, reparación, auditoría, persistencia, recovery y evidencia E2E.

## Cola maestra 30 tareas

| # | Objetivo | Tarea | Dependencia | Evidencia mínima de cierre | Estado inicial |
|---|---|---|---|---|---|
| 01 | O02 | Reconciliar HANDOFF + README Wordflow + README arquitectura + STATE + CHECKPOINT + RECOVERY + Crazy Wall contra el objetivo real y roles actuales de agentes | O01 | rutas+SHA+cross-check | EN_CURSO |
| 02 | O02 | Consolidar inventario de código candidato ya localizado para cola 1x1, resume/checkpoint, input_hash y estrategia distinta | 01 | repo+ruta+blob SHA+función | PENDIENTE |
| 03 | O02 | Verificar `Loop Engineer/loop/runner.py` como candidato canónico de cola 1x1 | 02 | read-back+SHA+símbolos | PENDIENTE |
| 04 | O02 | Verificar `Loop Engineer/loop/runcontrol.py` para pause/resume event-sourced | 02 | read-back+SHA+símbolos | PENDIENTE |
| 05 | O02 | Verificar candidato de identidad/reinyección con checkpoint provenance | 02 | read-back+SHA+tests | PENDIENTE |
| 06 | O02 | Verificar candidato de `input_hash + node_id + attempt + checkpoint` | 02 | read-back+SHA+tests | PENDIENTE |
| 07 | O02 | Verificar candidato de memoria de estrategias fallidas y delta distinto | 02 | read-back+SHA+test repetición | PENDIENTE |
| 08 | O02 | Mapear cada candidato a capa destino exacta del Wordflow/Yaiwes sin monolito | 03-07 | source→dest manifest | PENDIENTE |
| 09 | O02 | Crear manifiesto de provenance/compatibilidad/imports/dependencias para candidatos seleccionados | 08 | manifest+SHA+decisión REUSE/COPY/PATCH/ADAPTER | PENDIENTE |
| 10 | O03 | Copiar/reusar módulo 1x1 seleccionado por SHA al destino modular | 09 | source SHA+dest SHA/read-back | PENDIENTE |
| 11 | O03 | Copiar/reusar módulo pause/resume seleccionado por SHA | 09 | source SHA+dest SHA/read-back | PENDIENTE |
| 12 | O03 | Copiar/reusar módulo identidad/checkpoint seleccionado por SHA | 09 | source SHA+dest SHA/read-back | PENDIENTE |
| 13 | O03 | Copiar/reusar módulo `input_hash/node_state` seleccionado por SHA | 09 | source SHA+dest SHA/read-back | PENDIENTE |
| 14 | O03 | Copiar/reusar módulo strategy/failure-memory seleccionado por SHA | 09 | source SHA+dest SHA/read-back | PENDIENTE |
| 15 | O03 | Aplicar solo patches quirúrgicos de imports/rutas/contratos necesarios | 10-14 | diff mínimo+tests | PENDIENTE |
| 16 | O04 | Crear/ajustar Ficha/contrato de cada módulo integrado | 15 | Ficha/schema validado | PENDIENTE |
| 17 | O04 | Cablear adapters/plugins separados hacia Universal Plugin/Capability Registry | 16 | registry entry+adapter test | PENDIENTE |
| 18 | O04 | Añadir health/evidence hooks y fail-closed al cableado | 17 | health test+evidence record | PENDIENTE |
| 19 | O05 | Ejecutar 5 pasadas documentos↔arquitectura↔código↔contratos↔tests y registrar GAPs | 18 | informe 5 pasadas+GAP ledger | PENDIENTE |
| 20 | O06 | Crear contratos de tareas de agentes: ID, objetivo, contexto, rutas, deps, LOC, tests, evidence | 19 | task contracts verificables | PENDIENTE |
| 21 | O07 | Localizar y cablear OpenCode como escritor/ejecutor de código | 20 | source/binding/health/test | PENDIENTE |
| 22 | O07 | Localizar y cablear OpenHands como revisor/reparador | 20 | source/binding/health/test | PENDIENTE |
| 23 | O07 | Localizar y cablear Claude Code + Mimo Code para flujo, ejecución y wiring review | 20 | bindings+health+review test | PENDIENTE |
| 24 | O07 | Cablear auditores Claude Code, Mimo Code, Codex, Smolange, Hermes, OpenClaw y Council12; embudo→OpenHands+OpenCode | 21-23 | registry+consensus contract+test | PENDIENTE |
| 25 | O08 | Auditar y conectar HF/3 procesadores solo con autorización/health real | 24 | secret_ref/health/run evidence | PENDIENTE |
| 26 | O09 | Integrar Graphiti/Grapify/SQL/HF storage mediante contratos/adapters separados | 24 | storage health+CRUD test | PENDIENTE |
| 27 | O10 | Integrar modelos/APIs solo por `secret_ref`, budget, timeout, fallback y health | 24 | no secret leak+health/fallback tests | PENDIENTE |
| 28 | O11 | Ejecutar tests unitarios/integración/E2E del pipeline documento→code→plugin→verify | 25-27 | logs+tests+artifacts | PENDIENTE |
| 29 | O11 | Repetir checks reales inestables hasta 10x, verificar recovery/crash/idempotencia/no duplicate effects | 28 | stable_across_runs+recovery evidence | PENDIENTE |
| 30 | O11 | Auditoría final Council/3 refutaciones/cross-check/verify_final; cerrar o generar siguiente lote 30 únicamente de GAPs reales restantes | 29 | VERIFIED_CLOSED o GAP/INCONCLUSIVE con evidencia | PENDIENTE |

## Reglas de ejecución por tarea
`INPUT literal → GOALS 12/12 → prioridades → plan → cola1x1 → execute delta → verify/refute → GAP? research 10 vías/hasta 20 soluciones → StrategyDelta distinto → Council12 → auditor instrucciones×3 → 12 goals salida → 3 refutaciones → cross-check → CODA → verify_final → persistir STATE/CHECKPOINT/BITACORA/PLAN/RECOVERY`.

No se permite marcar `PASS` por mera presencia de archivo. Cierre requiere ruta, SHA/diff, test/log/URL y evidencia falsificable.