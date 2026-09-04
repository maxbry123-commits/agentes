# CHECKPOINT LOOP — 2026-08-26

## Director task
Cerrar los gaps G1–G7 bajo FAIL-CLOSED, usando el método de plugins para creación/conexión de archivos y cableado. Hermes queda ignorado. OpenClaw se materializa/cablea con Wordflow sin inventar código.

## Plan canónico
`PIPELINE/PLAN_YAIWES_AGENTE_WORDFLOW.md`

GitHub: https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/PLAN_YAIWES_AGENTE_WORDFLOW.md

Estado del plan auditado: S1–S12 registrados; los gaps técnicos G1–G7 requieren evidencia real para pasar de OPEN a CLOSED.

## Guía obligatoria
`Método de trabajo/GUIA_REGISTRO_PLUGINS_Y_CABLEADO.md`

Guía: https://github.com/maxbry123-commits/agentes/blob/main/M%C3%A9todo%20de%20trabajo/GUIA_REGISTRO_PLUGINS_Y_CABLEADO.md

Regla aplicada: un archivo/componente nuevo se crea con su mecanismo/plugin de conexión preparado; después de validado y registrado no se edita para añadir conexiones. Las conexiones futuras se realizan por plugin/contrato/adapter/cable.

## Prompt de gaps en resolución
TASK: Cerrar gaps G1–G7 (YAIWES / wordflow) — nivel SaaS avanzado.

Reglas: REUSE > PATCH > ADAPT > GENERATE; NO inventar APIs, engines, p01–p12 ni bodies OpenClaw/Hermes sin source; NO tocar extensions/wordflow/engine/code_path_runner.py; NO duplicar goal_lock, cognitive_loop, evidence_packet; YAML/JSON para contratos; FAIL-CLOSED; GitHub = truth.

Refactoria obligatoria para cambios: copiar source exacto a despliegue/refactoria/<gap>/source/ y Refactoria/<gap>/source/, implementar en Refactoria/<gap>/new/, verificar diff + tests + checklist antes de integrar; conservar source como evidencia.

G1: export AST real reutilizando build_symbol_index(); destino control-governance/symbol-index-wiring-graph/.
G2: schemas JSON únicamente para stages realmente nombrados por el código; residuales OPEN explícitos.
G3: índice test→asserts reproducible; destino code-programming-engine/module-tests/.
G4: evidencia CI real o OPEN con runbook exacto; jamás fabricar logs.
G5: p01→p12 solo si existe source real; si no, OPEN/BLOCKER y no fabricar módulos.
G6: adapters solo con source/SDK real; si no, contrato + OPEN.
G7: OpenClaw/Hermes bodies solo con source real; sin inventar agent; EnginePort.reason e IntelligenceGateway deben preservarse.

## Estado de trabajo en este checkpoint
- Método de plugins: incorporado a la fase actual.
- OpenClaw → Wordflow: cableado previamente verificado con test real según checkpoint anterior; no se debe confundir este resultado con cierre de G1–G7.
- G1: implementación preparada; workflow asociado no tiene workflow_run para los commits consultados. Por FAIL-CLOSED sigue OPEN hasta evidencia CI real.
- G3: implementación preparada; mismo bloqueo de evidencia CI; sigue OPEN.
- G2: OPEN hasta derivar schemas únicamente de stages reales y validarlos.
- G4: OPEN hasta disponer de log/trace real de Actions.
- G5: OPEN salvo evidencia de p01_* … p12_* reales y paridad E2E.
- G6: cerrado previamente solo donde exista evidencia real del adapter; no extender PASS a fuentes no verificadas.
- G7: OpenClaw cableado verificado; Hermes ignorado. No afirmar body Hermes.

## Hot path
`extensions/wordflow/engine/code_path_runner.py` es SOLO LECTURA y debe permanecer intacto. Cualquier cierre debe incluir verificación de no modificación.

## Deployment
No se afirma remote apply. `deployment_01.validation_result` permanece PENDING hasta apply externo real.

## Parches de recuperación
1. Si un cambio posterior rompe el estado: recuperar desde `Refactoria/<gap>/source/` y el último commit verificado.
2. No borrar las copias source de Refactoria.
3. No editar un archivo ya registrado para conectarlo; corregir el cable/plugin/contrato o crear una nueva versión.
4. Si falta source real para G5/G6/G7: crear/actualizar BLOCKER-T-GAP.md, no generar sustitutos.
5. Si CI no corre por el mecanismo de push, usar únicamente un disparador autorizado y verificar el run nuevo; no fabricar evidencia.

## Checkpoint rule
Cada gap terminado requiere checkpoint nuevo con: commit/SHA real, archivos tocados, tests reales, diff/refactoria, contrato, evidencia, estado CLOSED/OPEN/BLOCKED y enlace a esta guía y al plan.

## NO FAKE PASS
Este checkpoint no convierte ningún gap en PASS por documentación. PASS solo cuando la acceptance y la evidencia real estén presentes.
