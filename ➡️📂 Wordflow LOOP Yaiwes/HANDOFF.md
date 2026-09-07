# HANDOFF — Wordflow LOOP Yaiwes

## ABRIR PRIMERO

Este archivo es el punto de entrada operativo para cualquier GPT/Codex/agente que continúe el proyecto.

Contrato: `tel.workflow/v3`  
Modo: `FAIL_CLOSED_LOOP`  
Estado global: `ACTIVE_LOOP`  
Nodo actual: `PLAN30_T16_FICHA_CONTRACTS`  
Progreso PLAN30 verificado: `15/30 = 50%`.

## OBJETIVO FINAL

`documentos/proyectos YAIWES → requisitos trazables → tareas de programación → código → Ficha/contrato → adapter/plugin → registry → ejecución/repair → auditoría/tests → STATE/CHECKPOINT/evidence → E2E verificable`.

No confundir el LOOP con el objetivo final: el LOOP es el motor persistente que mantiene el trabajo hasta cierre real.

## ORDEN DE LECTURA OBLIGATORIO

1. Este `HANDOFF.md`.
2. `➡️📂 README arquitectura Wordflow LOOP Yaiwes.md` — arquitectura/plan actual.
3. `➡️📂 readme wordflow loop Yaiwes.md` — ledger histórico/literal y recuperación; no reemplazar.
4. `Crazy Wall Orquestador/TRAZABILIDAD-PROYECTO-WORDFLOW-YAIWES.md` — source→SHA→destino→evidencia y T01→T30.
5. `Crazy Wall Orquestador/STATE.json`.
6. `Crazy Wall Orquestador/CHECKPOINT.json`.
7. `Crazy Wall Orquestador/RECOVERY-PATCH.md`.
8. `Crazy Wall Orquestador/BITACORA-CRAZY-WALL.md`.
9. `Crazy Wall Orquestador/PLAN-LOOP-30-TAREAS.md`.
10. Evidencia exacta del nodo activo.

Si hay divergencia entre anclas: `GAP`; reconciliar antes de mutar.

## CADENA OBLIGATORIA DEL LOOP

`INPUT literal → GOALS12/12 → prioridades → plan → cola1×1 → delta autorizado → verify/refute → GAP? research ≥10 vías/hasta20 soluciones → StrategyDelta distinto → retry/continue safe task → auditor instrucciones×3 → Council12 → output goals12 → 3 refutaciones → cross-check → CODA → verify_final → persistencia`.

Prioridad: `REUSE > COPY/MOVE > PATCH QUIRÚRGICO > ADAPTER > GENERATE`.

No PASS por presencia. Cierre exige ruta + SHA/diff + test/log + URL/evidence.

## ESTADO O01–O11

- O01 LOOP/watchdog/checkpoint/STATE/recovery: `VERIFIED_CLOSED`.
- O02 investigación de código: `VERIFIED_CLOSED`.
- O03 copy/reuse por SHA: `VERIFIED_CLOSED`.
- O04 Ficha→adapter/plugin→registry→health→evidence: `IN_PROGRESS_T16`.
- O05 verificación documental 5 pasadas: `PENDING`.
- O06 task contracts agentes: `PENDING`.
- O07 integración agentes/council: `PENDING`.
- O08 HF/3 procesadores: `PENDING`.
- O09 Graphiti/Grapify/SQL/HF storage: `PENDING`.
- O10 APIs/modelos por secret_ref: `PENDING`.
- O11 tests/auditoría/E2E: `PENDING`.

## PLAN T01→T30

T01–T15 = `VERIFIED_CLOSED`.  
T16 = `EN_CURSO`.  
T17–T30 = `PENDIENTE`.

Plan completo y evidencia por tarea:
https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20Wordflow%20LOOP%20Yaiwes/Crazy%20Wall%20Orquestador/TRAZABILIDAD-PROYECTO-WORDFLOW-YAIWES.md

## COMPONENTES INTEGRADOS Y PROVENANCE

### C01 serial dispatch 1×1
- Fuente: `Agentes-motores-Wordflow-YAIWES/Loop Engineer/Loop-Engineer/loop/runner.py`
- Blob origen: `daa32a5d6dfeb0d21a975b8a5b8384d68a8aa08e`
- URL: https://github.com/maxbry123-commits/Agentes-motores-Wordflow-YAIWES/blob/main/Loop%20Engineer/Loop-Engineer/loop/runner.py
- Destino: `Agente Yaiwes principal/execution-orchestration/deterministic-execution/serial_dispatch.py`
- Blob destino: `77017b70239cedcce26f1df4a076272572f0927b`.

### C02 pause/resume
- Fuente: `Agentes-motores-Wordflow-YAIWES/Loop Engineer/Loop-Engineer/loop/runcontrol.py`
- Blob: `2c6aff845c97b600d4b3851b5ee9a6e0ee23defb`
- URL: https://github.com/maxbry123-commits/Agentes-motores-Wordflow-YAIWES/blob/main/Loop%20Engineer/Loop-Engineer/loop/runcontrol.py
- Destino: `Agente Yaiwes principal/state-events-durability/checkpoint-recovery/run_control_adapter.py`
- Blob destino: `aa4f62571044d873e3969bc7f747bfc83e3047a6`.

### C03/C04 resume identity + input_hash
- Patrón: `dta-au/elspeth` commit `720d441336434d227c2a00caaac100db48a07d5c`.
- `identity.py` blob `98b791e350e3a2829fb2c2977cc0fbc25beb4321`.
- `audit.py` blob `c89a5d9d2354ae549845aeab9a90cc3ab14f853e`.
- Destino: `resume_identity.py` blob `dc440bd180194d6cef2bf1b38b1ef1b85138ef0b`.

### C05 StrategyDelta
- Patrón: `Alex-v-p/indexer-core` commit `efcfcb20f09117504b00f682ada1bfff2b04b649`.
- `rules.py` blob `7704a6bd73d8b073df88651bbaf232f1f3dbfd6b`.
- Destino: `control-governance/strategy_delta_guard.py` blob `46efd22bd7b5ac3c22cc5ca084788d46b4b5b16b`.

### Test lote T10–T15
- `Agente Yaiwes principal/tests/test_plan30_loop_runtime.py`
- Blob `e1b1e3a4e4ca79e5dee00d5676a6038c6426bc31`.
- Commit `3b7f0cec153ef03656f76dcd693c17fe061f7a78`.
- Resultado registrado: `5 passed in 0.06s`.

La trazabilidad forense también incluye Loop Engineer supporting files, Elspeth transform/node-state/tests y Supreme-Agent models/feedback/planner/test con decisión SELECTED/REFERENCE/REJECTED.

## T16 ACTUAL — FICHA CONTRACT V2

Validador canónico:
https://github.com/maxbry123-commits/agentes/blob/37bef3a8a8f6dadca067638b8ea0c32995fc1d63/skills/research-download-chain/assets/plugin-bus/ficha_contract_v2.py

Commit `37bef3a8a8f6dadca067638b8ea0c32995fc1d63`; blob `b27f14b4d64f77bccf53a893c49b6f20bd58e745`.

Fichas materializadas:
- serial_dispatch `bc885059ed0a97f73aad02572853d1b0a4f8117d`
- run_control `7fdb64b7a21fe51c278dcc907b09eb800f2a2770`
- resume_identity `4ce82a32faa939177dd22603f097402e9b9e6ed9`
- strategy_delta `44aeb5cb48db6d42499bc940e47e912942d7fd40`

GAP: falta ejecutar el validador canónico exacto contra 4/4 Fichas, registrar stdout/veredicto y cross-check de paths. No abrir T17 antes de ese cierre.

## T17→T30 — CONTINUIDAD

17. adapters/plugins → registry.
18. health/evidence/fail-closed.
19. verificación 5 pasadas docs↔arquitectura↔code↔contracts↔tests.
20. contratos de tareas de agentes.
21. OpenCode writer/executor.
22. OpenHands review/repair.
23. Claude Code + Mimo Code flow/wiring review.
24. auditores + Council12 + embudo OpenHands/OpenCode.
25. HF/3 procesadores.
26. Graphiti/Grapify/SQL/HF storage.
27. APIs/modelos por `secret_ref`.
28. unit/integration/E2E tests.
29. stability checks hasta 10× + recovery/idempotencia.
30. auditoría final + 3 refutaciones + cross-check + `verify_final`.

## ROLES DE AGENTES

- OpenCode: escritor/ejecutor principal.
- OpenHands: reviewer/repair.
- Claude Code + Mimo Code: review de flujo/ejecución/wiring.
- Auditores independientes: Claude Code, Mimo Code, Codex, Smolange, Hermes, OpenClaw.
- Council objetivo adicional: Aider, Muse/Glimmer Code, Kimi K Code CLI y 12.º agente solo si existe evidencia/autorización.
- Embudo final: OpenHands + OpenCode.

No afirmar integración por mera existencia del agente.

## ADQUISICIÓN OSS

Skill autorizado cuando realmente falte descargar/extraer un componente:
https://github.com/maxbry123-commits/agentes/tree/c789e5fe635e220230ffc759d86dc3bbb8e261d4/skills/skills%20Github%20acci%C3%B3n

Prohibido LFS; no reactivar workflows antiguos; validar destino y `verify_final`.

## ENLACES CANÓNICOS

README arquitectura actual:
https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20Wordflow%20LOOP%20Yaiwes/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20README%20arquitectura%20Wordflow%20LOOP%20Yaiwes.md

Trazabilidad completa:
https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20Wordflow%20LOOP%20Yaiwes/Crazy%20Wall%20Orquestador/TRAZABILIDAD-PROYECTO-WORDFLOW-YAIWES.md

HANDOFF:
https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20Wordflow%20LOOP%20Yaiwes/HANDOFF.md

STATE:
https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20Wordflow%20LOOP%20Yaiwes/Crazy%20Wall%20Orquestador/STATE.json

## REGLA DE CIERRE

No cerrar el proyecto hasta demostrar el E2E completo:
`documento → requisito → task contract → engine/agente → código → repair → Ficha/plugin/registry → ejecución real → auditoría → test independiente → STATE/CHECKPOINT/evidence → output`.

Si falta evidencia: `GAP/INCONCLUSIVE`, nunca falso PASS.