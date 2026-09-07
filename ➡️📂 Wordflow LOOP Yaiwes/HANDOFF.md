# HANDOFF — Wordflow LOOP Yaiwes

## ABRIR PRIMERO
Punto de entrada operativo para GPT/Codex/agentes que continúen el proyecto.

Contrato: `tel.workflow/v3`  
Modo: `FAIL_CLOSED_LOOP`  
Estado global: `ACTIVE_LOOP`  
Nodo actual: `PLAN30_T16_FICHA_CONTRACTS`  
Progreso verificado PLAN30: `15/30 = 50%`.

## OBJETIVO FINAL
`documentos/proyectos YAIWES → requisitos trazables → tareas de programación → código → Ficha/contrato → adapter/plugin → registry → ejecución/repair → auditoría/tests → STATE/CHECKPOINT/evidence → E2E verificable`.

El LOOP es el motor persistente; no es el objetivo final.

## ORDEN DE LECTURA OBLIGATORIO
1. Este `HANDOFF.md`.
2. `➡️📂 README arquitectura Wordflow LOOP Yaiwes.md`.
3. `➡️📂 readme wordflow loop Yaiwes.md` histórico/literal.
4. `Crazy Wall Orquestador/TRAZABILIDAD-PROYECTO-WORDFLOW-YAIWES.md` — X-Ray completo + 5 pasadas chat.
5. `Crazy Wall Orquestador/STATE.json`.
6. `Crazy Wall Orquestador/CHECKPOINT.json`.
7. `Crazy Wall Orquestador/RECOVERY-PATCH.md`.
8. `Crazy Wall Orquestador/BITACORA-CRAZY-WALL.md`.
9. `Crazy Wall Orquestador/PLAN-LOOP-30-TAREAS.md`.
10. evidencia exacta del nodo activo.

Divergencia = `GAP`; reconciliar antes de mutar.

## RESULTADO AUDITORÍA FORENSE X-RAY — 5 PASADAS CHAT
### P1 objetivos/continuidad
- O01–O11 exactos preservados.
- T01–T30 preservados.
- Regla nueva fijada desde instrucción del Director: T30 solo cierra proyecto si no queda GAP. Si queda trabajo, generar siguiente lote de 30 (`T31–T60`, etc.) desde evidencia real pendiente y continuar LOOP.

### P2 contrato LOOP operacional
`INPUT literal sin reinterpretar → GOALS12 → 2 prioridades → plan → cola1×1 → delta → verify/refute+análisis → fallo=LOOP → auditor instrucciones×3 → GAP research≥10 vías/hasta20 soluciones → StrategyDelta distinto → comunidad secundaria → Council12 → research intensiva12 cuando aplique → 6 causas → ejecutar solución → verificar INPUT+LOOP → 3 refutaciones → cross-check global → CODA/checklist → verify_final → reinyección si falla`.

FLAG `🚩`: no PASS; persistir GAP y solo seguir otra tarea segura sin romper dependencias.

### P3 watchdog/salida/persistencia
Cada corrida debe actualizar lista global de tareas y emitir 10 líneas:
1 avance %, 2 nodo, 3 cerradas, 4 en curso, 5 pendientes, 6 GAP/flags, 7 evidencia, 8 cambios, 9 siguiente 1×1, 10 mini resumen + estado.
Estados: `VERIFIED_CLOSED | CLOSED_UNVERIFIED | INCONCLUSIVE | ACTIVE_LOOP`.

### P4 fuentes/adquisición
Orden: chat/historial → local Wordflow → repo `agentes` → `Agentes-motores-Wordflow-YAIWES` → router-universal → osquestador-auditor → GitHub/docs oficiales → comunidad secundaria.
Antes de programar: repo+ruta+URL+commit/blob SHA+comportamiento+destino+decisión.
Skill adquisición obligatorio cuando falte OSS:
https://github.com/maxbry123-commits/agentes/tree/c789e5fe635e220230ffc759d86dc3bbb8e261d4/skills/skills%20Github%20acci%C3%B3n
No LFS; no reactivar workflows viejos; validar destino; `verify_final`.

### P5 anti-alucinación/omisiones
Antes de avanzar: ¿inventé? ¿seguí INPUT literal? ¿revisé verdad? ¿sigo plan? ¿verify/refute pasó?
Si se pierde rumbo: reconstruir `HANDOFF+README+STATE+CHECKPOINT+RECOVERY+BITACORA` y retomar último checkpoint válido.

Omisiones ahora registradas como backlog global:
- 105 capacidades/algoritmos deterministas: no asumir wiring/registry/runtime sin evidencia.
- OpenMythos/capa persistencia: auditar integración real.
- PluginBus dinámico: aislamiento/guards/tests antes de declarar seguro.
- Council12: Qwen Code CLI es candidato 12.º, no integrado sin evidencia.

## ESTADO O01–O11
- O01 `VERIFIED_CLOSED` — LOOP/watchdog/checkpoint/STATE/recovery.
- O02 `VERIFIED_CLOSED` — investigación de código.
- O03 `VERIFIED_CLOSED` — copy/reuse por SHA.
- O04 `IN_PROGRESS_T16` — Ficha→adapter/plugin→registry→health→evidence.
- O05–O11 `PENDING`.

## PLAN T01→T30
T01–T15 `VERIFIED_CLOSED`.  
T16 `EN_CURSO`.  
T17–T30 `PENDIENTE`.

Pendientes exactos:
- T16 validar Ficha Contract v2 exacto 4/4.
- T17 registry/adapters/plugins.
- T18 health/evidence/fail-closed.
- T19 5 pasadas docs↔arquitectura↔code↔contracts↔tests.
- T20 task contracts agentes.
- T21 OpenCode.
- T22 OpenHands.
- T23 Claude Code + Mimo Code.
- T24 auditores + Council12 + embudo.
- T25 HF/3 processors.
- T26 Graphiti/Grapify/SQL/HF storage.
- T27 APIs/modelos secret_ref/health/budget/timeout/fallback.
- T28 unit/integration/E2E.
- T29 stability ×10 + recovery/idempotencia/no duplicate effects.
- T30 auditoría final + verify_final + cierre o generación del siguiente lote30.

## COMPONENTES INTEGRADOS
### C01 serial dispatch 1×1
Fuente `Agentes-motores-Wordflow-YAIWES/Loop Engineer/Loop-Engineer/loop/runner.py`, blob `daa32a5d6dfeb0d21a975b8a5b8384d68a8aa08e` → destino `serial_dispatch.py`, blob `77017b70239cedcce26f1df4a076272572f0927b`.

### C02 pause/resume
Fuente `runcontrol.py`, blob `2c6aff845c97b600d4b3851b5ee9a6e0ee23defb` → `run_control_adapter.py`, blob `aa4f62571044d873e3969bc7f747bfc83e3047a6`.

### C03/C04 resume identity/input_hash
Elspeth commit `720d441336434d227c2a00caaac100db48a07d5c`; identity blob `98b791e350e3a2829fb2c2977cc0fbc25beb4321`, audit blob `c89a5d9d2354ae549845aeab9a90cc3ab14f853e` → `resume_identity.py` blob `dc440bd180194d6cef2bf1b38b1ef1b85138ef0b`.

### C05 StrategyDelta
indexer-core commit `efcfcb20f09117504b00f682ada1bfff2b04b649`; `rules.py` blob `7704a6bd73d8b073df88651bbaf232f1f3dbfd6b` → `strategy_delta_guard.py` blob `46efd22bd7b5ac3c22cc5ca084788d46b4b5b16b`.

Test T10–T15: `test_plan30_loop_runtime.py` blob `e1b1e3a4e4ca79e5dee00d5676a6038c6426bc31`, commit `3b7f0cec153ef03656f76dcd693c17fe061f7a78`, resultado `5 passed in 0.06s`.

Trazabilidad SELECTED/REFERENCE/REJECTED completa:
https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20Wordflow%20LOOP%20Yaiwes/Crazy%20Wall%20Orquestador/TRAZABILIDAD-PROYECTO-WORDFLOW-YAIWES.md

## T16 ACTUAL — FICHA CONTRACT V2
Validador:
https://github.com/maxbry123-commits/agentes/blob/37bef3a8a8f6dadca067638b8ea0c32995fc1d63/skills/research-download-chain/assets/plugin-bus/ficha_contract_v2.py
Commit `37bef3a8a8f6dadca067638b8ea0c32995fc1d63`; blob `b27f14b4d64f77bccf53a893c49b6f20bd58e745`.

Fichas:
- serial_dispatch `bc885059ed0a97f73aad02572853d1b0a4f8117d`
- run_control `7fdb64b7a21fe51c278dcc907b09eb800f2a2770`
- resume_identity `4ce82a32faa939177dd22603f097402e9b9e6ed9`
- strategy_delta `44aeb5cb48db6d42499bc940e47e912942d7fd40`

GAP: ejecutar validador exacto 4/4 + stdout/veredicto + cross-check; T17 bloqueado hasta cierre.

## ROLES AGENTES / COUNCIL
- OpenCode writer/executor.
- OpenHands review/repair.
- Claude Code + Mimo Code flow/execution/wiring review.
- Auditores: Claude Code, Mimo Code, Codex, Smolange, Hermes, OpenClaw.
- Council adicional: Aider, Muse/Glimmer Code, Kimi K Code CLI.
- Qwen Code CLI: candidato 12.º pendiente evidencia.
- Embudo: OpenHands + OpenCode.

Presencia ≠ integración/binding.

## AUTORIZACIONES
Plugins externos autorizados actualmente: GitHub y Hugging Face. No añadir otros sin autorización literal posterior.
Kernel/control: 0% LLM. LLM solo donde decisión/razonamiento no sea resoluble determinísticamente.

## CONTINUIDAD POST-T30
Si T30 encuentra cualquier O01–O11/GAP/E2E abierto:
1. consolidar GAP ledger;
2. deduplicar trabajo ya cerrado;
3. generar siguiente lote de 30 tareas numeradas consecutivamente;
4. persistir PLAN/STATE/CHECKPOINT/BITACORA/RECOVERY;
5. continuar LOOP hasta `VERIFIED_CLOSED` global.

## ENLACES
README arquitectura:
https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20Wordflow%20LOOP%20Yaiwes/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20README%20arquitectura%20Wordflow%20LOOP%20Yaiwes.md

Trazabilidad:
https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20Wordflow%20LOOP%20Yaiwes/Crazy%20Wall%20Orquestador/TRAZABILIDAD-PROYECTO-WORDFLOW-YAIWES.md

HANDOFF:
https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20Wordflow%20LOOP%20Yaiwes/HANDOFF.md

## CIERRE
No cerrar hasta demostrar:
`documento → requisito → task contract → engine/agente → código → repair → Ficha/plugin/registry → ejecución real → auditoría → test independiente → STATE/CHECKPOINT/evidence → output`.

Si falta evidencia: `GAP/INCONCLUSIVE`; estado actual `ACTIVE_LOOP`.