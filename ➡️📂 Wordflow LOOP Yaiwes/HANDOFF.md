# HANDOFF — Wordflow LOOP Yaiwes — AGENT FLEET

Contrato: `tel.workflow/v4`  
Modo: `FAIL_CLOSED_EXECUTION_LOOP`  
Raíz única autorizada de escritura: `➡️📂 Wordflow LOOP Yaiwes/`  
Estado: `READY_FOR_REAL_AGENT_TEST`.

## STEP1 ✅
El índice quedó canónico dentro del Wordflow:
`➡️📂 Wordflow LOOP Yaiwes/➡️📂 readme indice agentes.md`.
La copia que yo había escrito en `maxbry123-commits/Agentes-motores-Wordflow-YAIWES` fue retirada en el commit `a17e1572b9df41954597fc8c66b390c47800d081`; ese repo queda como fuente de lectura/trazabilidad.

## STEP2 ✅
18 bindings / Council12=12. Rutas canónicas actuales:
- Adapter: `➡️📂 Wordflow LOOP Yaiwes/wordflow_loop/wordflow_loop/agent_fleet/agent_fleet_adapter.py`
- Registry: `➡️📂 Wordflow LOOP Yaiwes/wordflow_loop/wordflow_loop/agent_fleet/agent_fleet_registry.json`
- Health: `➡️📂 Wordflow LOOP Yaiwes/wordflow_loop/wordflow_loop/agent_fleet/agent_fleet_health.json`
- Ready manifest: `➡️📂 Wordflow LOOP Yaiwes/wordflow_loop/wordflow_loop/agent_fleet/AGENT_FLEET_READY_FOR_TEST.json`
- Plugin registration local: `➡️📂 Wordflow LOOP Yaiwes/wordflow_loop/wordflow_loop/agent_fleet/agent_fleet_plugin_registration.json`
- Ficha: `➡️📂 Wordflow LOOP Yaiwes/wordflow_loop/contracts/ficha.agent_fleet.v2.json`

El registry preexistente fuera del Wordflow fue restaurado al blob previo `ce40e9afd13fdbea22609fe57807566770dfc1b0`; no conserva el binding agent_fleet escrito por este bloque.

Fleet: OpenCode, OpenHands, Claude Code, MiMo Code, Codex, SmolAgents, Hermes, OpenClaw, Aider, Muse/Glimmer, Kimi, Qwen, Cline, Goose, Agent-Zero, OpenDev, Research Agent Lab, MiroThinker.

## STEP3 HISTÓRICO ✅
Run `34406268016`; job `102649876845`; head `05ce5fc43a599da1ae9e80f485450d52aede07a1`; `completed/success`.
La evidencia histórica fue movida a:
`➡️📂 Wordflow LOOP Yaiwes/wordflow_loop/evidence/STEP3_AGENT_FLEET_VERIFY.json`.
El YAML histórico fue movido fuera de `.github/workflows` a:
`➡️📂 Wordflow LOOP Yaiwes/wordflow_loop/workflows/wordflow-agent-fleet-step3.yml`.
Por tanto no queda activo como GitHub Action desde esa copia archivada.

## ROUTER MVP
Ruta canónica única:
`➡️📂 Wordflow LOOP Yaiwes/wordflow_loop/wordflow_loop/model_api_router_mvp.py`.
Prioridad: Kimi → MiniMax → DeepSeek V4 Pro → DeepSeek V4 Flash → GLM 5 → Muse/Glimmer → Qwen 3.8 → GPT-OSS; disponibilidad primero, failover de API/key y luego siguiente familia.

## MIGRACIÓN DE ALCANCE
Commit principal: `2a73aba061db7dfba2b37bf6637babb2e73c4b0d`.
Manifiesto: `➡️📂 Wordflow LOOP Yaiwes/wordflow_loop/evidence/SCOPE_MIGRATION_2026-09-09.json`.
Rutas externas creadas por este bloque: retiradas. Archivos preexistentes externos modificados por el bloque: restaurados.

## GAPs HONESTOS
Hermes, Muse/Glimmer y Goose siguen `EXTERNAL_NOT_VENDORED`. Los runtimes externos requieren API/MCP/command real para poder afirmar ejecución remota. No se afirma PASS_REAL de esos runtimes hasta probarlos.

## REGLA
No escribir ni modificar para este Wordflow fuera de `maxbry123-commits/agentes/➡️📂 Wordflow LOOP Yaiwes/`. No existe Paso 4 en el bloque anterior.
