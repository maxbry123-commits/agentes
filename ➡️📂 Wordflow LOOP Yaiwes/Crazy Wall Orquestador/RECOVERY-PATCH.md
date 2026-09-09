# RECOVERY PATCH — Wordflow LOOP Yaiwes — AGENTES 3 PASOS

Contrato `tel.workflow/v4` · modo `FAIL_CLOSED_EXECUTION_LOOP`.

## ANCLA ACTUAL
- Estado: `ACTIVE_3STEP_AGENT_INTEGRATION`.
- Checkpoint: `WFLOOP-AGENTS-3STEP-0003-ACTIVE`.
- Nodo actual: `STEP3_AGENT_FLEET_VERIFY`.
- Cola: `1×1`.
- Recovery anterior preservado por blob `8890665047339496a2558f78b5df68454c0ebe9f`.

## ESTADO DE LOS 3 PASOS
1. **Paso 1 — VERIFIED_CLOSED.** Índice `➡️📂 readme indice agentes.md` en motor repo; commit `ba9596c5716f34926e23186330609d4238bd8ccd`.
2. **Paso 2 — WIRED_UNTESTED.** 18 bindings materializados sin tests mediante adapter determinista + registry + Ficha v2 + health descriptor + Universal Plug registry.
3. **Paso 3 — IN_PROGRESS.** Workflow `.github/workflows/wordflow-agent-fleet-step3.yml`; run `34405553218`; trigger head `79e0a5d29313ff5620b136cf19c1e71eab776505`.

## EVIDENCIA STEP2
- Adapter: `Agente Yaiwes principal/execution-engine-pool/agent-bindings/agent_fleet_adapter.py`; blob `3e88678073c895899ab05dac0dd1c0ecee3c817e`; commit `1567d025656466df2c816ee4f52f404cbaca2e5a`.
- Registry: `agent_fleet_registry.json`; commit `f2e99e193286043d8cd2ed5bd5310b5ea9b42c7c`.
- Ficha: `wordflow-loop-contracts/ficha.agent_fleet.v2.json`; commit `c21c632a09d27098157d39b80e0ebd29fd72dad1`.
- Health descriptor: `agent_fleet_health.json`; commit `ff4f60a69bad684acb60e2239ffe72c2f6b0e20d`.
- Universal Plug registry: `wordflow_loop_plugin_registry.json`; commit `973a9ab800ea91ff0503efbd933428a693fdee50`.
- Plugin `yaiwes.runtime.agent_fleet`: `WIRED_UNTESTED`, slot 12; no falso ACTIVE antes del test.

## FLEET
OpenCode, OpenHands, Claude Code, MiMo Code, Codex, SmolAgents, Hermes, OpenClaw, Aider, Muse/Glimmer, Kimi K Code, Qwen Code, Cline, Goose, Agent-Zero, OpenDev, Research Agent Lab, MiroThinker.

Council12 canónico: Claude Code, OpenClaw, Hermes, Codex, Aider, OpenCode, OpenHands, MiMo Code, Muse/Glimmer, Kimi, SmolAgents, Qwen.

## GAP HONESTO
- Hermes: source exacto no localizado en el índice del motor repo.
- Muse/Glimmer: source exacto no localizado.
- Goose: source exacto no localizado.
- Sus bindings permanecen fail-closed; no declarar integración de source ni runtime externo sin evidencia.

## NO HACER
- No Paso 4.
- No investigar OSS nuevos.
- No re-descargar LOOP5.
- No reabrir MOVE/wiring runtime ya verificado.
- No tests en Paso 1/2.
- No arquitectura paralela.
- No `force git`.
- No falso PASS.

## EVIDENCIA CERRADA QUE NO SE DEBE REPETIR
- LOOP5 adquirido: LangGraph, Temporal Python SDK, Prefect, Hatchet Python SDK, redun.
- MOVE final: commit `26d0860ef23c3285ee60c63a5c9121fa45bb0ed1`.
- Wiring runtime/Enchufe Universal: commit `da290e6200c9e82154ed917ce6bbc6194d423da3`.
- Trigger programación: commit `ebac5c5b10d03d5e828e8fae266af88eb7b9b3d3`, run `34179064259`, `PASS_REAL`, casos 3/3, idempotencia PASS, fail-closed PASS.
- T16 Ficha Contract v2: run `34075371938`, PASS 4/4.

## REANUDACIÓN EXACTA
1. Abrir `➡️📂 Wordflow LOOP Yaiwes/HANDOFF.md`.
2. Leer STATE + CHECKPOINT + PLAN + este RECOVERY + BITÁCORA + README arquitectura.
3. Refrescar HEAD.
4. Consultar exclusivamente run `34405553218`.
5. Si falla: leer job/log, reparar únicamente ese fallo y relanzar STEP3.
6. Si success: guardar evidence JSON, promover `yaiwes.runtime.agent_fleet` a `ACTIVE`, actualizar health/STATE/CHECKPOINT/PLAN/RECOVERY/BITÁCORA/HANDOFF/README.
7. No afirmar ejecución real de un agente externo cuyo command/url no esté configurado.

## HF
Hugging Face sigue `EN_CURSO` fuera de estos 3 pasos. Esperar señal del Director.

## MICRO RESUMEN
`STEP1 ✅ → STEP2 WIRED ✅ sin tests → STEP3 run 34405553218 en verificación → PASS/evidence o reparación única del fallo`.