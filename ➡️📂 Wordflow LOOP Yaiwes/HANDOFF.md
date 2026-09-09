# HANDOFF — Wordflow LOOP Yaiwes — RECOVERY PATCH AGENTES 3 PASOS

Contrato: `tel.workflow/v4`  
Modo: `FAIL_CLOSED_EXECUTION_LOOP`  
Estado: `ACTIVE_3STEP_AGENT_INTEGRATION`  
Nodo actual: `STEP1_AGENT_INDEX`  
Cola: `1×1`  

> Este HANDOFF sustituye como punto de entrada operativo al snapshot anterior. El contenido histórico anterior permanece recuperable por blob `364688dddb7192e75fd8c82dca70d73f1f41b826`. No degradar evidencia posterior ni reabrir trabajo ya verificado.

## OBJETIVO ACTIVO DEL DIRECTOR — EXACTAMENTE 3 PASOS

### PASO 1 — ÍNDICE DE AGENTES
- Repo fuente: `maxbry123-commits/Agentes-motores-Wordflow-YAIWES`.
- Ubicar los agentes/componentes existentes sin revisar su código.
- Crear en `main` el archivo `➡️📂 readme indice agentes.md`.
- Registrar nombre y rol/función general.
- No cablear todavía.
- No ejecutar tests.

### PASO 2 — LISTA ADICIONAL + CABLEADO 1×1 SIN TESTS
- Mostrar al Director una lista adicional de agentes del repo que puedan mejorar Wordflow LOOP.
- Cablear únicamente los agentes necesarios, uno por uno.
- Carril: `Task Contract/Ficha → adapter/plugin → registry/binding → health descriptor`.
- Reutilizar el Enchufe Universal existente; no crear otro bus.
- Actualizar después del cableado: README arquitectura, STATE, CHECKPOINT, PLAN, RECOVERY, BITÁCORA y este HANDOFF.
- Entregar enlaces visibles de todo lo cableado y de los documentos actualizados.
- **Prohibido ejecutar tests en este paso.**

### PASO 3 — TEST FINAL WORDFLOW LOOP
- Solo después de completar todo el cableado del Paso 2.
- Ejecutar el test del Wordflow LOOP mediante workflow/trigger real.
- Verificar bindings, ejecución, fail-closed, evidencia y flujo de programación.
- Cerrar únicamente con run/job/status/conclusion/SHA/log/evidence.

## PROHIBICIONES DEL PARCHE ACTUAL
- No crear Paso 4.
- No investigar componentes OSS nuevos.
- No volver a descargar los 5 LOOP.
- No reabrir el MOVE/wiring/runtime ya probado.
- No analizar código de los agentes durante Paso 1.
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

## LISTA OBJETIVO DE AGENTES ENTREGADA POR EL DIRECTOR
Esta lista es objetivo del Paso 1/2; **presencia o nombre ≠ binding verificado**:
1. OpenCode
2. OpenHands
3. Claude Code
4. MiMo Code
5. Codex / Codex CLI
6. Cline
7. Kimi K Code CLI
8. Hermes
9. OpenClaw
10. Aider
11. Muse / Glimmer Code
12. Smolagents / Smolange
13. Qwen Code CLI / GLM Code
14. Goose

## ROLES BASE YA DEFINIDOS
- OpenCode: writer/executor.
- OpenHands: review/repair.
- Claude Code + MiMo Code: flujo/ejecución/wiring review.
- Auditores base: Claude Code, MiMo Code, Codex, Smolange, Hermes, OpenClaw.
- Council adicional: Aider, Muse/Glimmer, Kimi; Qwen/GLM sujeto a presencia/capacidad real.
- Cline y Goose: deben clasificarse por función durante el índice, sin inspección de código en Paso 1.

## HUGGING FACE
Estado informado por el Director: `EN_CURSO` fuera de este parche. No tocar ni probar HF hasta que el Director indique que está listo y entregue la orden/destino para prueba.

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
9. Retomar **exactamente** desde el primer paso de `STEP1 → STEP2 → STEP3` que no tenga evidencia material.

## QUÉ FALTA PARA TERMINAR — MICRO RESUMEN
- **Ahora:** Paso 1, crear el índice real de agentes en `Agentes-motores-Wordflow-YAIWES`.
- **Después:** Paso 2, cablear 1×1 los agentes necesarios, sin tests, y persistir enlaces/evidencia de wiring.
- **Final:** Paso 3, workflow/trigger de test global del Wordflow LOOP.
- **HF:** esperar a que el Director lo declare listo; no bloquear ni alterar este bloque mientras tanto.

## ENLACES CANÓNICOS
- Arquitectura: https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20Wordflow%20LOOP%20Yaiwes/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20README%20arquitectura%20Wordflow%20LOOP%20Yaiwes.md
- Guía v4: https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20Wordflow%20LOOP%20Yaiwes/GUIA-MAESTRA-EJECUCION-LOOP-V4-WORDFLOW-YAIWES.md
- STATE: https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20Wordflow%20LOOP%20Yaiwes/Crazy%20Wall%20Orquestador/STATE.json
- CHECKPOINT: https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20Wordflow%20LOOP%20Yaiwes/Crazy%20Wall%20Orquestador/CHECKPOINT.json
- PLAN: https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20Wordflow%20LOOP%20Yaiwes/Crazy%20Wall%20Orquestador/PLAN-LOOP-30-TAREAS.md
- RECOVERY: https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20Wordflow%20LOOP%20Yaiwes/Crazy%20Wall%20Orquestador/RECOVERY-PATCH.md
- BITÁCORA: https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20Wordflow%20LOOP%20Yaiwes/Crazy%20Wall%20Orquestador/BITACORA-CRAZY-WALL.md

Regla final: `archivo presente ≠ agente integrado`; el Paso 2 solo termina cuando cada binding requerido quede materializado y documentado. Los tests se reservan exclusivamente para el Paso 3.