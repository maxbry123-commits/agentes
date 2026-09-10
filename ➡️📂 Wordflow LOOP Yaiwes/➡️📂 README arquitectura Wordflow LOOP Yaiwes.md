# ➡️📂 README arquitectura Wordflow LOOP Yaiwes

Contrato: `tel.workflow/v4` · modo `FAIL_CLOSED_EXECUTION_LOOP`.  
Raíz única autorizada de escritura: `maxbry123-commits/agentes/➡️📂 Wordflow LOOP Yaiwes/`.  
Arquitectura: modular, determinista por defecto, no monolítica.

## Flujo
`documentos → requisitos → Task Contract/Ficha → agent_fleet_plugin_registration → AgentFleetAdapter → registry → binding ID/slot/rol → transporte API/MCP/command → agente → evidencia → STATE/CHECKPOINT`.

Kernel/control = `0% LLM`; el routing del fleet no usa decisión LLM.

## Fundación LOOP — no rehacer
Se conserva su evidencia histórica: LOOP5, MOVE `26d0860ef23c3285ee60c63a5c9121fa45bb0ed1`, runtime wiring `da290e6200c9e82154ed917ce6bbc6194d423da3`, programming trigger run `34179064259` PASS_REAL 3/3 y Ficha T16 run `34075371938` PASS 4/4.

## Paso 1 — índice ✅
Índice canónico actual:
`➡️📂 Wordflow LOOP Yaiwes/➡️📂 readme indice agentes.md`.
El repo `maxbry123-commits/Agentes-motores-Wordflow-YAIWES` queda como fuente de lectura; la copia escrita allí fue retirada en `a17e1572b9df41954597fc8c66b390c47800d081`.

## Paso 2 — cableado ✅
Rutas canónicas actuales, todas dentro del Wordflow:
- `wordflow_loop/wordflow_loop/agent_fleet/agent_fleet_adapter.py`
- `wordflow_loop/wordflow_loop/agent_fleet/agent_fleet_registry.json`
- `wordflow_loop/wordflow_loop/agent_fleet/agent_fleet_health.json`
- `wordflow_loop/wordflow_loop/agent_fleet/AGENT_FLEET_READY_FOR_TEST.json`
- `wordflow_loop/wordflow_loop/agent_fleet/agent_fleet_plugin_registration.json`
- `wordflow_loop/contracts/ficha.agent_fleet.v2.json`

Fleet 18: OpenCode, OpenHands, Claude Code, MiMo Code, Codex, SmolAgents, Hermes, OpenClaw, Aider, Muse/Glimmer, Kimi, Qwen, Cline, Goose, Agent-Zero, OpenDev, Research Agent Lab, MiroThinker. Council12=12.

El registry preexistente fuera del Wordflow fue restaurado a su blob anterior `ce40e9afd13fdbea22609fe57807566770dfc1b0`; el registro del fleet vive ahora solo dentro de la raíz autorizada.

## Paso 3 — evidencia histórica ✅
Run `34406268016` · job `102649876845` · head `05ce5fc43a599da1ae9e80f485450d52aede07a1` · `completed/success`.

Evidencia movida a:
`➡️📂 Wordflow LOOP Yaiwes/wordflow_loop/evidence/STEP3_AGENT_FLEET_VERIFY.json`.

YAML histórico movido a:
`➡️📂 Wordflow LOOP Yaiwes/wordflow_loop/workflows/wordflow-agent-fleet-step3.yml`.
Al no estar en `.github/workflows`, esa copia no queda activa como GitHub Action.

## Router MVP
`➡️📂 Wordflow LOOP Yaiwes/wordflow_loop/wordflow_loop/model_api_router_mvp.py`.
Orden global: Kimi → MiniMax → DeepSeek V4 Pro → DeepSeek V4 Flash → GLM 5 → Muse/Glimmer → Qwen 3.8 → GPT-OSS. Hace availability probe, intenta API/key alternativa de la misma familia, pasa al siguiente modelo y despacha agentes en paralelo.

## Migración de alcance
Commit: `2a73aba061db7dfba2b37bf6637babb2e73c4b0d`.
Manifiesto: `➡️📂 Wordflow LOOP Yaiwes/wordflow_loop/evidence/SCOPE_MIGRATION_2026-09-09.json`.

## GAP honesto
Hermes, Muse/Glimmer y Goose siguen `EXTERNAL_NOT_VENDORED`. Los runtimes externos requieren valores reales de API/MCP/command para afirmar ejecución remota. No se inventan endpoints ni PASS_REAL.

## Regla de continuidad
Todo artefacto nuevo o modificación de este Wordflow debe permanecer dentro de `➡️📂 Wordflow LOOP Yaiwes/`. Lecturas externas pueden usarse como fuentes; no se escribirá fuera sin autorización explícita.
