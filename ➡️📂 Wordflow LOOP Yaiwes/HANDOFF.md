# HANDOFF — Wordflow LOOP Yaiwes — RECOVERY PATCH AGENTES 3 PASOS

Contrato: `tel.workflow/v4`  
Modo: `FAIL_CLOSED_EXECUTION_LOOP`  
Estado: `ACTIVE_3STEP_AGENT_INTEGRATION`  
Nodo actual: `STEP3_AGENT_FLEET_VERIFY`  
Cola: `1×1`  

> Este HANDOFF sustituye como punto de entrada operativo al snapshot anterior. El contenido histórico anterior permanece recuperable por blob `364688dddb7192e75fd8c82dca70d73f1f41b826`. No degradar evidencia posterior ni reabrir trabajo ya verificado.

## OBJETIVO ACTIVO DEL DIRECTOR — EXACTAMENTE 3 PASOS

### PASO 1 — ÍNDICE DE AGENTES — CERRADO
- Repo fuente: `maxbry123-commits/Agentes-motores-Wordflow-YAIWES`.
- Índice: `➡️📂 readme indice agentes.md`.
- Commit reconciliado: `ba9596c5716f34926e23186330609d4238bd8ccd`.
- Regla respetada: nombres/rutas/metadata; no test en STEP1.

### PASO 2 — LISTA ADICIONAL + CABLEADO 1×1 SIN TESTS — CERRADO FÍSICAMENTE
- Adapter determinista: `Agente Yaiwes principal/execution-engine-pool/agent-bindings/agent_fleet_adapter.py`; blob `3e88678073c895899ab05dac0dd1c0ecee3c817e`; commit `1567d025656466df2c816ee4f52f404cbaca2e5a`.
- Registry fleet: `agent_fleet_registry.json`; commit `f2e99e193286043d8cd2ed5bd5310b5ea9b42c7c`.
- Ficha v2: `wordflow-loop-contracts/ficha.agent_fleet.v2.json`; commit `c21c632a09d27098157d39b80e0ebd29fd72dad1`.
- Health descriptor sin tests: `agent_fleet_health.json`; commit `ff4f60a69bad684acb60e2239ffe72c2f6b0e20d`.
- Universal Plug registry: `wordflow_loop_plugin_registry.json`; commit `973a9ab800ea91ff0503efbd933428a693fdee50`.
- Fleet: 18 bindings; Council12 canónico + Cline + Goose + 4 adicionales seleccionados (`Agent-Zero`, `OpenDev`, `Research Agent Lab`, `MiroThinker`).
- Estado del plugin fleet: `WIRED_UNTESTED`; no se infló `ACTIVE` antes de STEP3.
- Fuentes físicas localizadas para OpenCode, OpenHands, Claude Code, MiMo, Codex, SmolAgents, OpenClaw, Aider, Kimi, Qwen y Cline.
- Hermes, Muse/Glimmer y Goose: binding lógico/fail-closed materializado, pero `SOURCE_NOT_LOCATED_IN_REPO_ROOT_INDEX`; no se declara source integration.

### PASO 3 — TEST FINAL WORDFLOW LOOP — ACTIVO
- Workflow: `.github/workflows/wordflow-agent-fleet-step3.yml`.
- Trigger commit: `79e0a5d29313ff5620b136cf19c1e71eab776505`.
- Run: `34405553218`.
- Verifica: registry 18/18, IDs únicos, Council12, routing determinista por rol, fail-closed de runtime no configurado, conexión `yaiwes.runtime.agent_fleet` al registry Universal Plug y preservación del trigger de programación real 3/3.
- No se declara PASS hasta `completed/success` + logs/job.

## PROHIBICIONES DEL PARCHE ACTUAL
- No crear Paso 4.
- No investigar componentes OSS nuevos.
- No volver a descargar los 5 LOOP.
- No reabrir el MOVE/wiring/runtime ya probado.
- No ejecutar tests durante Paso 1 ni Paso 2.
- No modificar proyectos ajenos al alcance Wordflow/agentes.
- No sobreingeniería ni arquitectura paralela.
- `NO_FORCE_GIT`.

## FUNDACIÓN YA VERIFICADA — NO REHACER
1. **5 LOOP OSS adquiridos:** LangGraph, Temporal Python SDK, Prefect, Hatchet Python SDK y redun.
2. **MOVE a estructura final:** commit `26d0860ef23c3285ee60c63a5c9121fa45bb0ed1`.
3. **Wiring del runtime por Enchufe Universal:** commit `da290e6200c9e82154ed917ce6bbc6194d423da3`.
4. **Trigger de programación real:** evidencia `Agente Yaiwes principal/kernel-principal/extension-kernel/capability-registry/wordflow-loop-evidence/STEP3_PROGRAMMING_TRIGGER.json`, commit `ebac5c5b10d03d5e828e8fae266af88eb7b9b3d3`, run `34179064259`, `status=PASS_REAL`, `registry_active=11`, `engine_binding=yaiwes.loop.loop_engineer`, casos `sum/normalize/classify` = `3/3 completed`, idempotencia PASS y fail-closed de perfil inválido PASS.
5. **Ficha Contract v2 T16:** run `34075371938`, resultado `YAIWES_T16_CANONICAL_VERIFY=PASS 4/4`.

## FLEET ACTUAL
1. OpenCode — writer/executor/final reviewer.
2. OpenHands — review/repair/final reviewer.
3. Claude Code CLI — flow/wiring review + auditor.
4. MiMo Code — flow/wiring review + auditor.
5. Codex — auditor/debug/code review.
6. SmolAgents — auditor/council.
7. Hermes — auditor/worker; fuente física pendiente de localizar.
8. OpenClaw — auditor/coordinator/gateway.
9. Aider — editor/council.
10. Muse/Glimmer Code — council/reviewer; fuente física pendiente de localizar.
11. Kimi K Code — council/reviewer.
12. Qwen Code — council/reviewer.
13. Cline — coder auxiliar.
14. Goose — research auxiliar; fuente física pendiente de localizar.
15. Agent-Zero — fallback worker.
16. OpenDev — fallback coder.
17. Research Agent Lab — research.
18. MiroThinker — reasoning/reviewer.

## HUGGING FACE
Estado informado por el Director: `EN_CURSO` fuera de este parche. No tocar ni probar HF hasta que el Director indique que está listo.

## RECUPERACIÓN EXACTA
Si el chat se corta:
1. Abrir este `HANDOFF.md`.
2. Leer `GUIA-MAESTRA-EJECUCION-LOOP-V4-WORDFLOW-YAIWES.md`.
3. Leer `➡️📂 README arquitectura Wordflow LOOP Yaiwes.md`.
4. Leer `Crazy Wall Orquestador/STATE.json`.
5. Leer `Crazy Wall Orquestador/CHECKPOINT.json`.
6. Leer `Crazy Wall Orquestador/PLAN-LOOP-30-TAREAS.md`.
7. Leer `Crazy Wall Orquestador/RECOVERY-PATCH.md` y `BITACORA-CRAZY-WALL.md`.
8. Refrescar HEAD real.
9. No reabrir STEP1 ni STEP2; retomar `STEP3_AGENT_FLEET_VERIFY` por run `34405553218` o su StrategyDelta de reparación si falló.

## QUÉ FALTA PARA TERMINAR — MICRO RESUMEN
- STEP1: cerrado.
- STEP2: wiring físico cerrado; persistencia documental en reconciliación.
- STEP3: esperar/verificar resultado del run `34405553218`; si falla, reparar solo el fallo y relanzar; si PASS, persistir evidencia y promover `agent_fleet` de `WIRED_UNTESTED` a `ACTIVE`.
- Runtimes externos sin configuración en Actions deben permanecer fail-closed; wiring PASS no equivale a ejecución remota de cada agente.

## ENLACES CANÓNICOS
- Índice agentes: https://github.com/maxbry123-commits/Agentes-motores-Wordflow-YAIWES/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20readme%20indice%20agentes.md
- Agent fleet adapter: https://github.com/maxbry123-commits/agentes/blob/main/Agente%20Yaiwes%20principal/execution-engine-pool/agent-bindings/agent_fleet_adapter.py
- Agent fleet registry: https://github.com/maxbry123-commits/agentes/blob/main/Agente%20Yaiwes%20principal/execution-engine-pool/agent-bindings/agent_fleet_registry.json
- Agent fleet health: https://github.com/maxbry123-commits/agentes/blob/main/Agente%20Yaiwes%20principal/execution-engine-pool/agent-bindings/agent_fleet_health.json
- Ficha fleet: https://github.com/maxbry123-commits/agentes/blob/main/Agente%20Yaiwes%20principal/kernel-principal/extension-kernel/capability-registry/wordflow-loop-contracts/ficha.agent_fleet.v2.json
- Universal Plug registry: https://github.com/maxbry123-commits/agentes/blob/main/Agente%20Yaiwes%20principal/kernel-principal/extension-kernel/capability-registry/wordflow_loop_plugin_registry.json
- STEP3 workflow: https://github.com/maxbry123-commits/agentes/blob/main/.github/workflows/wordflow-agent-fleet-step3.yml
- STEP3 run: https://github.com/maxbry123-commits/agentes/actions/runs/34405553218
- Arquitectura: https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20Wordflow%20LOOP%20Yaiwes/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20README%20arquitectura%20Wordflow%20LOOP%20Yaiwes.md
- STATE: https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20Wordflow%20LOOP%20Yaiwes/Crazy%20Wall%20Orquestador/STATE.json
- CHECKPOINT: https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20Wordflow%20LOOP%20Yaiwes/Crazy%20Wall%20Orquestador/CHECKPOINT.json
- PLAN: https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20Wordflow%20LOOP%20Yaiwes/Crazy%20Wall%20Orquestador/PLAN-LOOP-30-TAREAS.md
- RECOVERY: https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20Wordflow%20LOOP%20Yaiwes/Crazy%20Wall%20Orquestador/RECOVERY-PATCH.md
- BITÁCORA: https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20Wordflow%20LOOP%20Yaiwes/Crazy%20Wall%20Orquestador/BITACORA-CRAZY-WALL.md

Regla final: `binding materializado ≠ runtime externo probado`; STEP3 clasifica honestamente cada nivel de evidencia.