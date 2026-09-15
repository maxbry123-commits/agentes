# CLAUDE NOTAS - memoria.md
Fuente unica y autoritativa de la memoria del orquestador. Reemplaza la
dispersion anterior en "Claude readme/" (que se mantiene sin borrar, como
historial). Desde este commit, todo se anota AQUI primero.

## Estado del ecosistema (7 proyectos, verificado)
1. Agente Yaiwes = repo agentes (activo)
2. Osquestador Maxbry = repo Orquestador-Maxbry- (en pausa)
3. Router Inteligente Universal = repo router-universal-router-inteligente- (activo, en construccion Cognitive Control Plane)
4. UI Yaiwes = repo nct-hub (hipotesis, sin confirmar)
5. Fabrica de UI = repo frontend (activo)
6. Osquestador auditor + memoria (Fables) = repo osquestador-auditor (en pausa)
7. NCT = repo nct-core (en pausa)

Repos activos ahora: agentes, frontend, router-universal-router-inteligente-

## Inventario oficial del repo agentes
Core kernel Yaiwes/CORE-KERNEL-COMPONENT-INVENTORY.json - 229 componentes,
34/35 nodos del Crazy Wall principal cerrados, 1 GAP activo (N33 BullMQ,
escalado, ver Claude readme/Escalacion GAP N33 BullMQ.md).

## Plan de adquisicion de componentes
Ver Claude readme/PLAN-ADQUISICION-COMPONENTES.md - Fase 1 (28 aprobados,
enviados a Sol via manifest RESEARCH_DOWNLOAD_MANIFEST.jsonl), Fase 2 (21
en reserva).

## Agente Seals Team (creado 2026-09-15)
Ubicacion: Seals team YAIWES/
Estado: codigo completo, pendiente de prueba real (falta que el Director
ponga las 6 API keys de Cerebras en GitHub Secrets).
Arquitectura: DAG determinista (dag_schema.yaml), 95% codigo puro / 5% LLM
via Cerebras para volumen, Claude solo para verificacion final de bajo
volumen. Extraido quirurgicamente de Muse-Agent y MUSE-KnowledgeXLab (ver
Seals team YAIWES/_fuentes_extraidas/EXTRACTION_EVIDENCE_MUSE.json).
Pendiente de decision: Meta-Muse-Code-SDK-2026 y Meta-Agent-Cookbook-2026
(Sol los descargo completos, fuera del alcance pedido - pausados sin usar).

## Regla dura de este archivo
Cada instruccion nueva del Director se anota AQUI, textual, con fecha,
antes de ejecutar nada. No se resume. No se reinterpreta. Se ejecuta
despues de anotar, sin preguntar de vuelta salvo ambiguedad real que
bloquee por completo el trabajo.

## Ultima instruccion registrada (2026-09-15, verbatim)
"Termina todo el code, dejalo listo solo falta hacer las pruebas. Pones
los archivos handoff con todo lo que el modelo va a trabajar. Planifica,
no improvises, luego ejecutas, no preguntes. Audita el chat, revisa mis
instrucciones. Luego yo pongo las claves en GitHub secret para que hagas
las pruebas."

Accion tomada en respuesta: completar verificador.py y watchdog.py con
codigo real (no placeholders), actualizar Handoff, crear este archivo.
