# PLAN LOOP — Wordflow LOOP Yaiwes

Contrato: `tel.workflow/v4` · modo `FAIL_CLOSED_EXECUTION_LOOP` · cola `1×1`.

## PARCHE ACTIVO DEL DIRECTOR — EXACTAMENTE 3 PASOS
Este bloque controla la ejecución actual y no crea un Paso 4.

| Paso | Tarea | Estado | Evidencia |
|---|---|---|---|
| 1 | Ubicar agentes/componentes y crear `➡️📂 readme indice agentes.md` | VERIFIED_CLOSED | motor repo commit `ba9596c5716f34926e23186330609d4238bd8ccd` |
| 2 | Mostrar agentes adicionales útiles y cablear solo los necesarios 1×1 mediante Enchufe Universal, sin tests | WIRED_UNTESTED | adapter `1567d025…`; registry `f2e99e19…`; Ficha `c21c632a…`; health `ff4f60a6…`; Universal Plug `973a9ab8…` |
| 3 | Ejecutar test final del Wordflow LOOP mediante workflow/trigger real | IN_PROGRESS | workflow `.github/workflows/wordflow-agent-fleet-step3.yml`; run `34405553218`; head `79e0a5d29313ff5620b136cf19c1e71eab776505` |

**Nodo actual:** `STEP3_AGENT_FLEET_VERIFY`.

**Prohibido:** investigar OSS nuevos, re-descargar LOOP5, rehacer MOVE/runtime wiring ya verificado, tests en Paso 1/2, arquitectura paralela, `force git`, falso PASS.

## PASO 2 — FLEET CABLEADO
Fleet registry: `Agente Yaiwes principal/execution-engine-pool/agent-bindings/agent_fleet_registry.json`.

18 bindings:
1. OpenCode
2. OpenHands
3. Claude Code
4. MiMo Code
5. Codex
6. SmolAgents
7. Hermes
8. OpenClaw
9. Aider
10. Muse/Glimmer
11. Kimi K Code
12. Qwen Code
13. Cline
14. Goose
15. Agent-Zero
16. OpenDev
17. Research Agent Lab
18. MiroThinker

Council12 canónico: Claude Code, OpenClaw, Hermes, Codex, Aider, OpenCode, OpenHands, MiMo Code, Muse/Glimmer, Kimi, SmolAgents, Qwen.

Adicionales seleccionados porque cubren huecos concretos sin duplicar Council: Agent-Zero=`fallback_worker`, OpenDev=`fallback_coder`, Research Agent Lab=`research`, MiroThinker=`reasoning/reviewer`.

GAP de procedencia física que no invalida el binding fail-closed pero impide afirmar source integration: Hermes, Muse/Glimmer y Goose no fueron localizados como fuente exacta en el índice del repo motor.

## FUNDACIÓN YA VERIFICADA — NO REHACER
- LOOP5: LangGraph, Temporal Python SDK, Prefect, Hatchet Python SDK, redun.
- MOVE estructura final: commit `26d0860ef23c3285ee60c63a5c9121fa45bb0ed1`.
- Wiring runtime por Enchufe Universal: commit `da290e6200c9e82154ed917ce6bbc6194d423da3`.
- Trigger programación: commit `ebac5c5b10d03d5e828e8fae266af88eb7b9b3d3`, run `34179064259`, `PASS_REAL`, 3/3 casos, `registry_active=11`, `engine_binding=yaiwes.loop.loop_engineer`.
- Ficha Contract v2 T16: run `34075371938`, `YAIWES_T16_CANONICAL_VERIFY=PASS 4/4`.

## MAPEO AL BACKLOG HISTÓRICO PLAN30
El PLAN30 se conserva para trazabilidad; el parche actual no borra historial.

| # | Objetivo | Tarea | Estado reconciliado |
|---|---|---|---|
| 01–16 | O02–O04 | trabajo histórico verificado | VERIFIED_CLOSED |
| 17 | O04 | adapters/plugins→registry | evidencia posterior de runtime wiring existe; NO REHACER |
| 18 | O04 | health/evidence hooks | cubierto parcialmente por runtime y fleet; cierre global pendiente de STEP3 |
| 19 | O05 | verificación documental | fuera del bloque actual salvo persistencia requerida |
| 20 | O06 | contratos tareas agentes | Ficha/registry fleet materializado en STEP2 |
| 21 | O07 | OpenCode | WIRED_UNTESTED STEP2 |
| 22 | O07 | OpenHands | WIRED_UNTESTED STEP2 |
| 23 | O07 | Claude Code + Mimo Code | WIRED_UNTESTED STEP2 |
| 24 | O07 | auditores + Council12 | WIRED_UNTESTED STEP2 |
| 25 | O08 | HF/3 processors | EN CURSO EXTERNO; esperar Director |
| 26–27 | O09–O10 | storage/APIs | fuera del bloque actual |
| 28 | O11 | tests | STEP3 activo run `34405553218` |
| 29 | O11 | estabilidad/recovery | solo reparar fallo que surja en STEP3 |
| 30 | O11 | verify_final | cerrar solo con evidencia STEP3 |

## STEP3 — CRITERIO DE CIERRE
El run debe demostrar:
- registry fleet 18/18;
- IDs únicos;
- Council12 12/12;
- routing determinista por slots/roles;
- fail-closed cuando un runtime externo no está configurado;
- `yaiwes.runtime.agent_fleet` conectado una sola vez al Universal Plug registry;
- preservar evidencia del trigger real de programación 3/3.

No se exige fingir disponibilidad de CLIs/APIs externas ausentes en GitHub Actions. `WIRED + FAIL_CLOSED` puede pasar integración; `runtime externo ejecutado` solo se afirma si existe configuración y evidencia real.

## REGLA DE RECUPERACIÓN
`HANDOFF → guía v4 → README arquitectura → STATE → CHECKPOINT → PLAN → RECOVERY → BITACORA → HEAD real → run 34405553218`.

## SIGUIENTE DELTA EXACTO
Verificar run `34405553218`; si falla, reparar únicamente el fallo de STEP3 y relanzar; si success, persistir evidence y promover `yaiwes.runtime.agent_fleet` de `WIRED_UNTESTED` a `ACTIVE`.