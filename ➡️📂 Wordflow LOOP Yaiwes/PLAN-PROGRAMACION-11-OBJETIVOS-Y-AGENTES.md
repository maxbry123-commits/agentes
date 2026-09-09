# PLAN DE PROGRAMACIÓN — WORDFLOW LOOP YAIWES — 11 OBJETIVOS + AGENTES

Contrato operativo: `tel.workflow/v4`  
Modo: `FAIL_CLOSED_EXECUTION_LOOP`  
Estado actual: `ACTIVE_3STEP_AGENT_INTEGRATION / STEP3_AGENT_FLEET_VERIFY`  
Historial anterior preservado por blob `478ad801e6da336c0b486f211e8749fc154957e9`.

## OBJETIVO FINAL
`documentos/proyectos YAIWES → requisitos → task contracts → código/agentes → Ficha/adapter/plugin → registry/binding → ejecución/repair → auditoría/tests → STATE/CHECKPOINT/evidence → salida E2E verificable`.

## PARCHE ACTIVO — SOLO 3 PASOS
### PASO 1 — VERIFIED_CLOSED
Índice del repo motor creado/reconciliado en `➡️📂 readme indice agentes.md`; commit `ba9596c5716f34926e23186330609d4238bd8ccd`.

### PASO 2 — WIRED_UNTESTED
Cableado 1×1 sin tests por la arquitectura existente:
`Ficha v2 → AgentFleetAdapter → agent_fleet_registry → Universal Plug registry → health descriptor`.

Evidencia:
- adapter commit `1567d025656466df2c816ee4f52f404cbaca2e5a`, blob `3e88678073c895899ab05dac0dd1c0ecee3c817e`;
- registry 18 agentes commit `f2e99e193286043d8cd2ed5bd5310b5ea9b42c7c`;
- Ficha v2 commit `c21c632a09d27098157d39b80e0ebd29fd72dad1`;
- health descriptor commit `ff4f60a69bad684acb60e2239ffe72c2f6b0e20d`, `tests_executed=false`;
- Universal Plug registry commit `973a9ab800ea91ff0503efbd933428a693fdee50`.

### PASO 3 — IN_PROGRESS
Workflow `.github/workflows/wordflow-agent-fleet-step3.yml`, run `34405553218`, head `79e0a5d29313ff5620b136cf19c1e71eab776505`.

Criterio: 18 IDs únicos, Council12 12/12, routing determinista, fail-closed, health descriptors, registro único en Universal Plug y preservación de trigger programación PASS_REAL 3/3.

## FLEET 18
1. OpenCode — writer/executor/final reviewer.
2. OpenHands — review/repair/final reviewer.
3. Claude Code — flow/wiring review + auditor.
4. MiMo Code — flow/wiring review + auditor.
5. Codex — auditor/debug/code review.
6. SmolAgents — auditor/council.
7. Hermes — auditor/worker.
8. OpenClaw — auditor/coordinator/gateway.
9. Aider — editor/council.
10. Muse/Glimmer Code — council/reviewer.
11. Kimi K Code — council/reviewer.
12. Qwen Code — council/reviewer.
13. Cline — coder auxiliar.
14. Goose — research auxiliar.
15. Agent-Zero — fallback worker.
16. OpenDev — fallback coder.
17. Research Agent Lab — research.
18. MiroThinker — reasoning/reviewer.

## COUNCIL12
Claude Code · OpenClaw · Hermes · Codex · Aider · OpenCode · OpenHands · MiMo Code · Muse/Glimmer · Kimi · SmolAgents · Qwen.

## ADICIONALES SELECCIONADOS
- Agent-Zero: fallback worker.
- OpenDev: fallback coder.
- Research Agent Lab: research.
- MiroThinker: reasoning/reviewer.

No se añaden más dentro de este parche: el Council ya cubre consenso y estos cuatro llenan funciones concretas sin ampliar el alcance.

## GAP DE SOURCE / RUNTIME
- Hermes: source exacto no localizado en el índice del repo motor.
- Muse/Glimmer: source exacto no localizado.
- Goose: source exacto no localizado.
- Los tres conservan slot lógico fail-closed; no declarar integración física de source.
- Los transportes externos usan solo variables de entorno; si no están configurados, STEP3 exige fallo cerrado y no inventa ejecución.

## 11 OBJETIVOS CANÓNICOS
1. Investigar/localizar código cuando el Director lo autorice.
2. Copiar/reutilizar código faltante con trazabilidad.
3. Cablear mediante Ficha/adapter/plugin/registry/health/evidence.
4. Verificar documentación↔arquitectura↔code↔contracts↔tests.
5. Convertir GAPs reales en trabajo programable.
6. Crear contratos de tareas de agentes.
7. Integrar/cablear agentes de programación/auditoría.
8. Integrar HF/3 procesadores cuando el Director lo entregue listo.
9. Integrar memoria/storage autorizado cuando corresponda.
10. Integrar modelos por `secret_ref` cuando corresponda.
11. Ejecutar tests/auditoría/cierre E2E.

El parche actual no autoriza ejecutar trabajo fuera de STEP1–STEP3.

## FUNDACIÓN YA VERIFICADA — NO REHACER
- 5 LOOP OSS: LangGraph, Temporal Python SDK, Prefect, Hatchet Python SDK, redun.
- MOVE final `26d0860ef23c3285ee60c63a5c9121fa45bb0ed1`.
- Wiring runtime `da290e6200c9e82154ed917ce6bbc6194d423da3`.
- Trigger real `ebac5c5b10d03d5e828e8fae266af88eb7b9b3d3`, run `34179064259`, 3/3 PASS_REAL, idempotencia PASS, fail-closed PASS.
- Ficha Contract v2 T16 run `34075371938`, PASS 4/4.

## HF
`EN_CURSO` según Director; no tocar/probar hasta nueva señal.

## PROHIBICIONES
`NO_STEP_4 · NO_NEW_OSS_RESEARCH · NO_REDOWNLOAD_LOOP5 · NO_TEST_STEP1_STEP2 · NO_PARALLEL_ARCHITECTURE · NO_FORCE_GIT · NO_FALSE_PASS`.

## SIGUIENTE ACCIÓN
Verificar run `34405553218`; reparar únicamente un fallo de STEP3 si aparece; si PASS, persistir evidencia y promover `yaiwes.runtime.agent_fleet` a `ACTIVE`.