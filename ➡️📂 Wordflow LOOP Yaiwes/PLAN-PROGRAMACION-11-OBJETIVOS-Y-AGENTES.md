# PLAN DE PROGRAMACIÓN — WORDFLOW LOOP YAIWES — 11 OBJETIVOS + AGENTES

Contrato operativo: `tel.workflow/v4`  
Modo: `FAIL_CLOSED_EXECUTION_LOOP`  
Estado actual: `ACTIVE_3STEP_AGENT_INTEGRATION`  
Historial anterior preservado por blob `fda6e95055765f6f588bff319e60abcae833c4c2`.

## OBJETIVO FINAL
`documentos/proyectos YAIWES → requisitos → task contracts → código/agentes → Ficha/adapter/plugin → registry/binding → ejecución/repair → auditoría/tests → STATE/CHECKPOINT/evidence → salida E2E verificable`.

El LOOP mantiene el trabajo persistente; no sustituye el producto final.

## PARCHE ACTIVO DEL DIRECTOR — SOLO 3 PASOS

### PASO 1 — ÍNDICE
- Repo: `maxbry123-commits/Agentes-motores-Wordflow-YAIWES`.
- Ubicar agentes/componentes existentes sin revisar código.
- Crear `➡️📂 readme indice agentes.md` en `main`.
- Registrar nombre y función/rol general.
- Sin cableado y sin tests.

### PASO 2 — LISTA ADICIONAL + CABLEADO 1×1
- Mostrar otros agentes del repo que puedan mejorar Wordflow LOOP.
- Elegir únicamente los necesarios.
- Cablear 1×1 mediante `Task Contract/Ficha → adapter/plugin → registry/binding → health descriptor`.
- Reusar Enchufe Universal existente; no crear bus paralelo.
- Sin tests.
- Actualizar README arquitectura + STATE + CHECKPOINT + PLAN + RECOVERY + BITÁCORA + HANDOFF y entregar enlaces visibles.

### PASO 3 — TEST FINAL
- Solo después de completar Paso 2.
- Ejecutar workflow/trigger del Wordflow LOOP y pruebas finales reales.
- Cierre con run/job/status/conclusion/SHA/log/evidence.

## AGENTES OBJETIVO ENTREGADOS POR EL DIRECTOR
1. OpenCode — writer/executor.
2. OpenHands — review/repair.
3. Claude Code — revisión de flujo/ejecución/wiring + auditoría.
4. MiMo Code — revisión de flujo/ejecución/wiring + auditoría.
5. Codex / Codex CLI — implementación/debugging/auditoría técnica.
6. Cline — agente de programación; rol exacto se clasifica en el índice sin inspección de código.
7. Kimi K Code CLI — programación/revisión/Council.
8. Hermes — worker auxiliar + auditor.
9. OpenClaw — coordinador/worker auxiliar + auditor.
10. Aider — edición/programación de repositorio + Council.
11. Muse / Glimmer Code — programación/revisión alternativa + Council.
12. Smolagents / Smolange — auditor/revisión adicional.
13. Qwen Code CLI / GLM Code — programación/contraste; sujeto a presencia real.
14. Goose — agente investigador/auxiliar; clasificar en índice.

Presencia de carpeta/nombre ≠ integración. Binding solo se declara materializado después del Paso 2.

## 11 OBJETIVOS CANÓNICOS
1. Investigar/localizar código cuando el Director lo autorice.
2. Copiar/reutilizar código faltante con trazabilidad.
3. Cablear mediante Ficha/adapter/plugin/registry/health/evidence.
4. Verificar documentación↔arquitectura↔code↔contracts↔tests.
5. Convertir GAPs reales en trabajo programable.
6. Crear contratos de tareas de agentes.
7. Integrar/cablear agentes de programación/auditoría.
8. Integrar HF/3 procesadores cuando el Director lo entregue listo.
9. Integrar memoria/storage autorizado cuando corresponda.
10. Integrar modelos por `secret_ref` cuando corresponda.
11. Ejecutar tests/auditoría/cierre E2E.

El parche actual **no autoriza ejecutar otros objetivos fuera de los 3 pasos**.

## FUNDACIÓN YA VERIFICADA — NO REHACER
- 5 LOOP OSS: LangGraph, Temporal Python SDK, Prefect, Hatchet Python SDK, redun.
- MOVE final commit `26d0860ef23c3285ee60c63a5c9121fa45bb0ed1`.
- Wiring runtime commit `da290e6200c9e82154ed917ce6bbc6194d423da3`.
- Trigger real commit `ebac5c5b10d03d5e828e8fae266af88eb7b9b3d3`, run `34179064259`, 3/3 programación PASS, idempotencia PASS, fail-closed PASS.
- Ficha Contract v2 T16 run `34075371938`, PASS 4/4.

## HF
Estado indicado por el Director: `EN CURSO`. No tocar/probar hasta que el Director indique que está listo.

## PROHIBICIONES
`NO_STEP_4 · NO_NEW_OSS_RESEARCH · NO_REDOWNLOAD_LOOP5 · NO_CODE_REVIEW_STEP1 · NO_TEST_STEP1_STEP2 · NO_PARALLEL_ARCHITECTURE · NO_FORCE_GIT · NO_FALSE_PASS`.

## SIGUIENTE ACCIÓN
`STEP1_AGENT_INDEX`: crear el índice real de agentes del repo `Agentes-motores-Wordflow-YAIWES`, sin revisar su código y sin tests.
