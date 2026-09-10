# ➡️📂 README arquitectura Wordflow LOOP Yaiwes

Contrato: `tel.workflow/v4` · modo `FAIL_CLOSED_EXECUTION_LOOP`.  
Raíz única autorizada de escritura: `maxbry123-commits/agentes/➡️📂 Wordflow LOOP Yaiwes/`.  
Arquitectura: modular, determinista por defecto, no monolítica.

## Flujo
`documentos → requisitos → Task Contract/Ficha → agent_fleet_plugin_registration → AgentFleetAdapter → registry → binding ID/slot/rol → router disponibilidad/prioridad → transporte API/MCP/command → agente → evidencia → STATE/CHECKPOINT`.

## Fleet
18 agentes · Council12=12. Routing determinista por ID/rol. Sin runtime configurado, `fail_closed`.

## Router MVP
Ruta: `➡️📂 Wordflow LOOP Yaiwes/wordflow_loop/wordflow_loop/model_api_router_mvp.py`.
Prioridad global: Kimi → MiniMax → DeepSeek V4 Pro → DeepSeek V4 Flash → GLM 5 → Muse/Glimmer → Qwen 3.8 → GPT-OSS. Dentro de una prioridad rota por rutas/API; si fallan, baja a la siguiente familia. `dispatch_parallel()` distribuye agentes en paralelo.

## CIERRE FINAL 3 PASOS — 2026-09-10
1. **Estructura/rutas PASS:** todos los artefactos de este bloque viven dentro de `➡️📂 Wordflow LOOP Yaiwes/`.
2. **Tests PASS_LOCAL:** fleet 18, IDs únicos, Council12, routing por rol, fail-closed 18/18, prioridad/failover del router, fallback Kimi→MiniMax y parallel dispatch 3/3.
3. **Persistencia/watchdog PASS:** evidence final persistida y Watchdog horario activo con alcance exclusivo a la raíz autorizada.

Evidence final: `➡️📂 Wordflow LOOP Yaiwes/wordflow_loop/evidence/FINAL_3STEP_CLOSURE_TEST_2026-09-10.json` · commit `6c4b10a49fa8de3bd85348f15bd5f5fa461d128c`.

## Estado verificable
`LOCAL_TESTS_PASS_AUTH_PROVIDER_TEST_PENDING`.
No se afirma autenticación real de NVIDIA/Cerebras/Groq ni ejecución remota de los agentes hasta disponer de un canal saliente autenticado seguro. Esa parte permanece evidence-gated.

## Persistencia
- STATE: `➡️📂 Wordflow LOOP Yaiwes/Crazy Wall Orquestador/STATE.json`
- CHECKPOINT: `➡️📂 Wordflow LOOP Yaiwes/Crazy Wall Orquestador/CHECKPOINT.json`
- PLAN: `➡️📂 Wordflow LOOP Yaiwes/Crazy Wall Orquestador/PLAN-LOOP-30-TAREAS.md`
- RECOVERY: `➡️📂 Wordflow LOOP Yaiwes/Crazy Wall Orquestador/RECOVERY-PATCH.md`
- BITÁCORA: `➡️📂 Wordflow LOOP Yaiwes/Crazy Wall Orquestador/BITACORA-CRAZY-WALL.md`
- HANDOFF: `➡️📂 Wordflow LOOP Yaiwes/HANDOFF.md`

## Regla final
No escribir ni modificar nada para este Wordflow fuera de `➡️📂 Wordflow LOOP Yaiwes/`. Próxima fase válida: únicamente prueba externa autenticada, cuando exista canal seguro, para alcanzar `PASS_REAL_EXTERNAL`.
