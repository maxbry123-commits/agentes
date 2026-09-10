# PLAN DE PROGRAMACIÓN — WORDFLOW LOOP YAIWES — AGENTES

Contrato `tel.workflow/v4` · `FAIL_CLOSED_EXECUTION_LOOP`.
Raíz única de escritura: `maxbry123-commits/agentes/➡️📂 Wordflow LOOP Yaiwes/`.

## ESTADO
Índice ✅ · cableado 18 agentes ✅ · Council12=12 ✅ · STEP3 histórico ✅ · preparación para test real `READY_FOR_REAL_AGENT_TEST`.

## RUTAS CANÓNICAS
`Task Contract/Ficha → agent_fleet_plugin_registration → AgentFleetAdapter → agent_fleet_registry → health → runtime API/MCP/command → evidencia`.

Todo el material de este bloque vive bajo:
- `➡️📂 Wordflow LOOP Yaiwes/wordflow_loop/wordflow_loop/agent_fleet/`
- `➡️📂 Wordflow LOOP Yaiwes/wordflow_loop/contracts/`
- `➡️📂 Wordflow LOOP Yaiwes/wordflow_loop/evidence/`
- router: `➡️📂 Wordflow LOOP Yaiwes/wordflow_loop/wordflow_loop/model_api_router_mvp.py`.

## FLEET
OpenCode=writer/executor; OpenHands=review/repair; Claude Code+MiMo=flow/wiring review; Codex=auditor/debug; SmolAgents=auditor/council; OpenClaw=coordinator/auditor; Aider=editor/council; Kimi/Qwen/Muse-Glimmer=Council; Hermes=worker/auditor; Cline=coder auxiliar; Goose=research auxiliar; Agent-Zero=fallback worker; OpenDev=fallback coder; Research Agent Lab=research; MiroThinker=reasoning/reviewer.

## ROUTER MODELOS
Prioridad: Kimi → MiniMax → DeepSeek V4 Pro → DeepSeek V4 Flash → GLM 5 → Muse/Glimmer → Qwen 3.8 → GPT-OSS. Availability-first; intenta API/key alternativa antes de cambiar de familia y permite despacho paralelo.

## EVIDENCIA
STEP3 histórico: run `34406268016`, job `102649876845`, head `05ce5fc43a599da1ae9e80f485450d52aede07a1`, success. Evidencia actual en `➡️📂 Wordflow LOOP Yaiwes/wordflow_loop/evidence/STEP3_AGENT_FLEET_VERIFY.json`.

## MIGRACIÓN
Commit principal `2a73aba061db7dfba2b37bf6637babb2e73c4b0d`; limpieza del índice externo `a17e1572b9df41954597fc8c66b390c47800d081`; registry preexistente externo restaurado al blob `ce40e9afd13fdbea22609fe57807566770dfc1b0`.

## LÍMITE
Hermes, Muse/Glimmer y Goose siguen `EXTERNAL_NOT_VENDORED`. Ningún runtime externo se declara PASS_REAL sin ejecución real demostrada. No escribir fuera de la raíz autorizada.
