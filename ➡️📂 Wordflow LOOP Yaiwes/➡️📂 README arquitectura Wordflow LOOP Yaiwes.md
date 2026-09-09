# ➡️📂 README arquitectura Wordflow LOOP Yaiwes

Contrato: `tel.workflow/v4` · modo `FAIL_CLOSED_EXECUTION_LOOP`.  
Arquitectura: modular, determinista por defecto, no monolítica.  
Parche actual: `STEP1 → STEP2 → STEP3 = VERIFIED_CLOSED`.

## Flujo
`documentos → requisitos → Task Contract/Ficha → Capability Registry → AgentFleetAdapter determinista → binding por ID/slot/rol → transporte configurado → agente → evidencia → STATE/CHECKPOINT`.

Kernel/control = `0% LLM`; el routing del fleet no usa decisión LLM.

## Fundación LOOP — no rehacer
- LOOP5: LangGraph, Temporal Python SDK, Prefect, Hatchet Python SDK, redun.
- MOVE `26d0860ef23c3285ee60c63a5c9121fa45bb0ed1`.
- runtime Universal Plug wiring `da290e6200c9e82154ed917ce6bbc6194d423da3`.
- programming trigger run `34179064259`: PASS_REAL 3/3 + idempotencia/fail-closed.
- T16 Ficha run `34075371938`: PASS 4/4.

## Paso 1 — índice ✅
Repo motor: `maxbry123-commits/Agentes-motores-Wordflow-YAIWES`.  
Índice: `➡️📂 readme indice agentes.md`; commit `ba9596c5716f34926e23186330609d4238bd8ccd`.

## Paso 2 — cableado ✅
Arquitectura reutilizada, sin bus paralelo:
`Ficha v2 → agent_fleet_adapter.py → agent_fleet_registry.json → wordflow_loop_plugin_registry.json → agent_fleet_health.json`.

Evidencia:
- adapter `1567d025656466df2c816ee4f52f404cbaca2e5a`, blob `3e88678073c895899ab05dac0dd1c0ecee3c817e`;
- registry inicial `f2e99e193286043d8cd2ed5bd5310b5ea9b42c7c`;
- Ficha `c21c632a09d27098157d39b80e0ebd29fd72dad1`;
- health inicial `ff4f60a69bad684acb60e2239ffe72c2f6b0e20d`;
- Universal Plug inicial `973a9ab800ea91ff0503efbd933428a693fdee50`.

Fleet 18: OpenCode, OpenHands, Claude Code, MiMo Code, Codex, SmolAgents, Hermes, OpenClaw, Aider, Muse/Glimmer, Kimi, Qwen, Cline, Goose, Agent-Zero, OpenDev, Research Agent Lab, MiroThinker.

Council12: Claude Code, OpenClaw, Hermes, Codex, Aider, OpenCode, OpenHands, MiMo, Muse/Glimmer, Kimi, SmolAgents, Qwen.

Adicionales: Agent-Zero=fallback worker; OpenDev=fallback coder; Research Agent Lab=research; MiroThinker=reasoning/reviewer.

## Paso 3 — test ✅
Workflow `.github/workflows/wordflow-agent-fleet-step3.yml`.

Run `34406268016` · job `102649876845` · head `05ce5fc43a599da1ae9e80f485450d52aede07a1` · `completed/success`.

Stdout:
`WORDFLOW_AGENT_FLEET_STEP3=PASS`  
`fleet_count=18`  
`council12=12`  
`runtimes_unconfigured_fail_closed=18`  
`prior_programming_trigger=PASS_REAL_3_3`.

Evidence commit `7a7b1a6af381dbdb4882d3d744ef392161dffdff`.

Promoción final:
- registry fleet `f2f978a18cbeaeac8c99d35993a66a68bfdcef7f`;
- health `e05946c349ef79d26e036e8f2fb5ee15f77775e0`;
- Universal Plug `08b42de1136917ef0adc712155c583188c6b9085`;
- `yaiwes.runtime.agent_fleet=ACTIVE`;
- capability registry `active_count=12`.

## Evidencia honesta / GAP
Hermes, Muse/Glimmer y Goose: source físico exacto no localizado en el índice del motor repo. Los 18 runtimes externos no estaban configurados en Actions; el sistema demostró routing + wiring + fail-closed. **No se afirma ejecución remota de esos runtimes.**

## Enlaces
- Índice: https://github.com/maxbry123-commits/Agentes-motores-Wordflow-YAIWES/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20readme%20indice%20agentes.md
- Adapter: https://github.com/maxbry123-commits/agentes/blob/main/Agente%20Yaiwes%20principal/execution-engine-pool/agent-bindings/agent_fleet_adapter.py
- Registry: https://github.com/maxbry123-commits/agentes/blob/main/Agente%20Yaiwes%20principal/execution-engine-pool/agent-bindings/agent_fleet_registry.json
- Health: https://github.com/maxbry123-commits/agentes/blob/main/Agente%20Yaiwes%20principal/execution-engine-pool/agent-bindings/agent_fleet_health.json
- Ficha: https://github.com/maxbry123-commits/agentes/blob/main/Agente%20Yaiwes%20principal/kernel-principal/extension-kernel/capability-registry/wordflow-loop-contracts/ficha.agent_fleet.v2.json
- Plug registry: https://github.com/maxbry123-commits/agentes/blob/main/Agente%20Yaiwes%20principal/kernel-principal/extension-kernel/capability-registry/wordflow_loop_plugin_registry.json
- Evidence: https://github.com/maxbry123-commits/agentes/blob/main/Agente%20Yaiwes%20principal/kernel-principal/extension-kernel/capability-registry/wordflow-loop-evidence/STEP3_AGENT_FLEET_VERIFY.json
- Run: https://github.com/maxbry123-commits/agentes/actions/runs/34406268016

## Estado
El bloque exacto de 3 pasos está `VERIFIED_CLOSED`. HF continúa `EN_CURSO` por separado hasta señal del Director. No se crea Paso 4.