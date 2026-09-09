# PLAN DE PROGRAMACIÓN — WORDFLOW LOOP YAIWES — AGENTES

Contrato `tel.workflow/v4` · `FAIL_CLOSED_EXECUTION_LOOP`.

## PARCHE EXACTO DE 3 PASOS — VERIFIED_CLOSED
1. **Índice agentes:** VERIFIED_CLOSED — motor commit `ba9596c5716f34926e23186330609d4238bd8ccd`.
2. **Cableado 1×1 sin tests:** VERIFIED_CLOSED_WIRING — 18 bindings por Ficha/adapter/registry/health/Universal Plug.
3. **Workflow/test:** VERIFIED_CLOSED — run `34406268016`, job `102649876845`, success.

## FLEET PROGRAMACIÓN/AUDITORÍA
OpenCode=writer/executor; OpenHands=review/repair; Claude Code+MiMo=flow/wiring review; Codex=auditor/debug; SmolAgents=auditor/council; OpenClaw=coordinator/auditor; Aider=editor/council; Kimi/Qwen/Muse-Glimmer=Council; Hermes=worker/auditor; Cline=coder auxiliar; Goose=research auxiliar; Agent-Zero=fallback worker; OpenDev=fallback coder; Research Agent Lab=research; MiroThinker=reasoning/reviewer.

Council12: Claude Code, OpenClaw, Hermes, Codex, Aider, OpenCode, OpenHands, MiMo Code, Muse/Glimmer, Kimi, SmolAgents, Qwen.

## CABLEADO
`Task Contract/Ficha → AgentFleetAdapter → agent_fleet_registry → Universal Plug capability registry → health/evidence`.

El routing es determinista por ID explícito o primer slot numérico con rol exacto. Ningún LLM decide la ruta del fleet.

Commits:
- adapter `1567d025656466df2c816ee4f52f404cbaca2e5a`;
- registry inicial `f2e99e193286043d8cd2ed5bd5310b5ea9b42c7c`;
- Ficha `c21c632a09d27098157d39b80e0ebd29fd72dad1`;
- health inicial `ff4f60a69bad684acb60e2239ffe72c2f6b0e20d`;
- Universal Plug wiring `973a9ab800ea91ff0503efbd933428a693fdee50`.

## TEST FINAL
Run `34406268016`; job `102649876845`; head `05ce5fc43a599da1ae9e80f485450d52aede07a1`; `completed/success`.

`WORDFLOW_AGENT_FLEET_STEP3=PASS` · `fleet_count=18` · `council12=12` · `runtimes_unconfigured_fail_closed=18` · `prior_programming_trigger=PASS_REAL_3_3`.

Evidence commit `7a7b1a6af381dbdb4882d3d744ef392161dffdff`.

Promoción final: registry fleet `f2f978a18cbeaeac8c99d35993a66a68bfdcef7f`; health `e05946c349ef79d26e036e8f2fb5ee15f77775e0`; Universal Plug `08b42de1136917ef0adc712155c583188c6b9085`; `yaiwes.runtime.agent_fleet=ACTIVE`; active_count=12.

## LÍMITE DE LA EVIDENCIA
Hermes, Muse/Glimmer y Goose tienen source físico pendiente de localizar. Los 18 transportes externos estuvieron sin configuración en Actions; el test valida integración del wiring/routing y comportamiento fail-closed, **no ejecución remota de cada agente**.

## FUNDACIÓN NO REHACER
LOOP5 + MOVE `26d0860…` + runtime wiring `da290e62…` + programming trigger run `34179064259` PASS_REAL 3/3 + T16 run `34075371938` PASS 4/4.

## HF
`EN_CURSO` según Director. Queda fuera del bloque cerrado hasta señal de listo.

No existe Paso 4. El próximo trabajo requiere nueva instrucción del Director.