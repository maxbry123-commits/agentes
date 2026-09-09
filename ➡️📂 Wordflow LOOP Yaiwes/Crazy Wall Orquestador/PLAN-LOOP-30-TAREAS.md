# PLAN LOOP — Wordflow LOOP Yaiwes

Contrato: `tel.workflow/v4` · modo `FAIL_CLOSED_EXECUTION_LOOP` · cola `1×1`.

## PARCHE ACTIVO DEL DIRECTOR — EXACTAMENTE 3 PASOS
Este bloque controla la ejecución actual y no crea un Paso 4.

| Paso | Tarea | Estado | Restricciones |
|---|---|---|---|
| 1 | Ubicar agentes/componentes en `maxbry123-commits/Agentes-motores-Wordflow-YAIWES` y crear `➡️📂 readme indice agentes.md` | PENDIENTE | Solo inventario/nombres/rol general; no revisar código; no tests |
| 2 | Mostrar agentes adicionales útiles y cablear solo los necesarios 1×1 mediante Enchufe Universal | PENDIENTE | Sin tests; actualizar README arquitectura + Crazy Wall/STATE/CHECKPOINT/PLAN/RECOVERY/BITACORA/HANDOFF; entregar enlaces visibles |
| 3 | Ejecutar test final del Wordflow LOOP mediante workflow/trigger real | PENDIENTE | Solo después del cierre material del Paso 2 |

**Nodo actual:** `STEP1_AGENT_INDEX`.

**Prohibido:** investigar OSS nuevos, re-descargar LOOP5, rehacer MOVE/runtime wiring ya verificado, tests en Paso 1/2, arquitectura paralela, `force git`, falso PASS.

## FUNDACIÓN YA VERIFICADA — NO REHACER
- LOOP5: LangGraph, Temporal Python SDK, Prefect, Hatchet Python SDK, redun.
- MOVE estructura final: commit `26d0860ef23c3285ee60c63a5c9121fa45bb0ed1`.
- Wiring runtime por Enchufe Universal: commit `da290e6200c9e82154ed917ce6bbc6194d423da3`.
- Trigger programación: commit `ebac5c5b10d03d5e828e8fae266af88eb7b9b3d3`, run `34179064259`, `PASS_REAL`, 3/3 casos, `registry_active=11`, `engine_binding=yaiwes.loop.loop_engineer`.
- Ficha Contract v2 T16: run `34075371938`, `YAIWES_T16_CANONICAL_VERIFY=PASS 4/4`.

## MAPEO AL BACKLOG HISTÓRICO PLAN30
El PLAN30 se conserva para trazabilidad. No se inflan estados por este parche documental.

| # | Objetivo | Tarea | Estado histórico verificado |
|---|---|---|---|
| 01 | O02 | Reconciliar anclas/objetivo/roles | VERIFIED_CLOSED |
| 02 | O02 | Consolidar inventario de código candidato | VERIFIED_CLOSED |
| 03 | O02 | Verificar runner 1x1 | VERIFIED_CLOSED |
| 04 | O02 | Verificar pause/resume | VERIFIED_CLOSED |
| 05 | O02 | Verificar identidad/reinyección | VERIFIED_CLOSED |
| 06 | O02 | Verificar input_hash/node/attempt/checkpoint | VERIFIED_CLOSED |
| 07 | O02 | Verificar strategy/failure-memory | VERIFIED_CLOSED |
| 08 | O02 | Mapear candidatos a destino | VERIFIED_CLOSED |
| 09 | O02 | Manifiesto provenance/compatibilidad | VERIFIED_CLOSED |
| 10 | O03 | Reusar módulo cola 1x1 | VERIFIED_CLOSED |
| 11 | O03 | Reusar módulo pause/resume | VERIFIED_CLOSED |
| 12 | O03 | Reusar módulo identidad/checkpoint | VERIFIED_CLOSED |
| 13 | O03 | Reusar módulo input_hash/node_state | VERIFIED_CLOSED |
| 14 | O03 | Reusar strategy/failure-memory | VERIFIED_CLOSED |
| 15 | O03 | Patches quirúrgicos necesarios | VERIFIED_CLOSED |
| 16 | O04 | Crear/ajustar Ficha/contrato de módulos integrados | VERIFIED_CLOSED |
| 17 | O04 | Cablear adapters/plugins a registry | ESTADO HISTÓRICO EN_CURSO; evidencia posterior de runtime wiring existe y no debe rehacerse |
| 18 | O04 | Health/evidence hooks fail-closed | PENDIENTE histórico |
| 19 | O05 | 5 pasadas docs↔arquitectura↔code↔contratos↔tests | PENDIENTE histórico |
| 20 | O06 | Contratos de tareas de agentes | PENDIENTE; absorbido por Paso 2 cuando aplique |
| 21 | O07 | Cablear OpenCode | PENDIENTE; Paso 2 |
| 22 | O07 | Cablear OpenHands | PENDIENTE; Paso 2 |
| 23 | O07 | Cablear Claude Code + Mimo Code | PENDIENTE; Paso 2 |
| 24 | O07 | Auditores + Council12 + embudo | PENDIENTE; Paso 2 |
| 25 | O08 | HF/3 procesadores con health real | EN CURSO EXTERNO SEGÚN DIRECTOR; esperar señal de listo |
| 26 | O09 | Graphiti/Grapify/SQL/HF storage | PENDIENTE histórico; no ejecutar dentro del parche de 3 pasos salvo instrucción nueva |
| 27 | O10 | APIs/modelos por secret_ref | PENDIENTE histórico; no ejecutar dentro del parche de 3 pasos salvo instrucción nueva |
| 28 | O11 | Tests unit/integración/E2E | Paso 3 para el bloque actual |
| 29 | O11 | Checks inestables hasta 10x + recovery | Solo si el test del Paso 3 lo requiere |
| 30 | O11 | Auditoría final + verify_final | Cierre del Paso 3 si existe evidencia suficiente |

## LISTA DE AGENTES OBJETIVO DEL DIRECTOR
OpenCode · OpenHands · Claude Code · MiMo Code · Codex/Codex CLI · Cline · Kimi K Code CLI · Hermes · OpenClaw · Aider · Muse/Glimmer Code · Smolagents/Smolange · Qwen Code CLI/GLM Code · Goose.

Esta lista es objetivo para localizar/cablear; `nombre/carpeta presente ≠ binding integrado`.

## REGLA DE RECUPERACIÓN
`HANDOFF → guía v4 → README arquitectura → STATE → CHECKPOINT → PLAN → RECOVERY → BITACORA → HEAD real → retomar primer Paso 1/2/3 sin evidencia`.

## SIGUIENTE DELTA EXACTO
`STEP1_AGENT_INDEX`: revisar únicamente el inventario del repo `Agentes-motores-Wordflow-YAIWES` y crear `➡️📂 readme indice agentes.md`; no leer código y no ejecutar tests.
