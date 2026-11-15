ANEXO - GAPS y mejoras pendientes (mapa mental de Claude, 2026-09-17)
Este es el registro vivo de que falta cerrar en Wordflow Loop, con evidencia
real de esta auditoria. Se actualiza, nunca se resume.

## GAPS CONFIRMADOS CON EVIDENCIA REAL (no de memoria)

1. contracts/ (wordflow_loop/wordflow_loop/contracts/) esta VACIA - falta
   el "JSON Schema real" (punto 13 de la lista de 50 mejoras VERBATIM).
2. evidence/ (wordflow_loop/wordflow_loop/evidence/) esta VACIA - falta el
   "Evidence Manifest" (punto 18/36 de la lista de 50 mejoras).
3. DOS routers de agentes coexisten: agent_router.py (debil, runtime/src/agent/)
   y agent_fleet_adapter.py (robusto, wordflow_loop/wordflow_loop/agent_fleet/).
   Decision ya tomada de deprecar el primero, PENDIENTE DE EJECUTAR.
4. Los 7 archivos de gobernanza (sheriff/sentinel/judge/guardian/supervisor/
   validator/verifier) son sospechosamente pequenos (389-804 bytes cada uno).
   PENDIENTE: leer el contenido linea por linea antes de asumir que la
   cadena de gobernanza esta completa.
5. checkpoint.py (recovery/, 2KB) existe pero es pequeno - PENDIENTE:
   confirmar si persiste en disco/SQLite o sigue en memoria del proceso.
6. Duplicado sospechoso: source_truth_reconciler.py (4KB) y
   truth_reconciler.py (1.4KB) en runtime/src/core/ - mismo proposito,
   2 archivos. PENDIENTE: comparar y decidir cual es el vigente.
7. AGENT_FLEET_READY_FOR_TEST.json confirma textualmente: los 18 agentes
   estan registrados pero SIN prueba de runtime real.
8. La reorganizacion de raiz aprobada hace varios turnos TODAVIA NO SE
   EJECUTO - la raiz del repo sigue igual de duplicada.
9. Carpeta "Capa workflow GitHub Action" sigue existiendo pese a que el
   Director prohibio expresamente usar GitHub Actions.
10. 13 subcarpetas de wordflow_loop/wordflow_loop/ y 8 carpetas del nivel
    superior del proyecto - ver actualizacion abajo, ya revisadas.

## TAREAS DERIVADAS, EN ORDEN DE PRIORIDAD

1. Leer contenido real (no solo tamano) de los 7 archivos de gobernanza.
2. Leer contenido real de recovery/checkpoint.py.
3. Ejecutar la deprecacion de runtime/src/agent/agent_router.py.
4. Poblar contracts/ y evidence/ con los schemas ya disenados.
5. Comparar source_truth_reconciler.py vs truth_reconciler.py.
6. Ejecutar la reorganizacion de raiz ya aprobada.
7. Revisar y decidir el destino de "Capa workflow GitHub Action".
8. Disenar y correr la primera prueba real de runtime de al menos 1 agente.

## ACTUALIZACION 2026-09-17 (segunda pasada, cobertura ampliada) - GAPS 11-15

11. HALLAZGO MAYOR: las 13 subcarpetas de wordflow_loop/wordflow_loop/
    (adapters, agent_sources, code_graph, intake, plugins, prompts,
    research, skills, templates, workflows, mas contracts/ y evidence/)
    ESTAN TODAS VACIAS. Confirma que el sistema de plantillas/RAG no tiene
    ninguna infraestructura construida todavia.
12. HALLAZGO MAYOR: existe un SEGUNDO sistema de Crazy Wall completo y
    activo en "Crazy Wall Orquestador/" (40+ archivos: TASK-NODES.json 23KB,
    STATE.json 8KB, BITACORA-CRAZY-WALL.md 47KB, TRAZABILIDAD-PROYECTO-
    WORDFLOW-YAIWES.md 15.8KB, PLAN-LOOP-30-TAREAS.md, 11 archivos
    EVIDENCE-PLAN30-T17-*-REFUTATION.md), DISTINTO del "Bitacora stated
    JSON Craxy wall.json" de la raiz principal. PENDIENTE CRITICO:
    determinar si son 2 sistemas independientes o cual es el vigente.
13. "Capa de persistencia open mythos/" SI tiene codigo real:
    open_mythos_persistence_loop.py (3.6KB) - Mythos como codigo existe.
14. "Capa workflow evolucion/" tiene codigo real: evolution_engine.py
    (3.2KB), evolution_dag.yaml, evolution_contract.schema.json.
15. "Capa workflow GitHub Action/" contiene ADVERTENCIA-CODE.json y el
    motor real research_download_chain.py (7KB) - mal ubicado ahi en vez
    de en Motores/, junto a una carpeta prohibida.

## MEJORAS ANADIDAS POR INSTRUCCION DEL DIRECTOR (2026-09-17)

16. SCHEMA-refactorizacion.md creado.
17. SCHEMA-frontend-browser-verified.md creado.
18. SCHEMA-plantillas-RAG.md creado.
19. PENDIENTE: prompt para Sol investigando capacidad real de browser/
    frontend de cada uno de los 18 agentes del Fleet.

## PENDIENTE FINAL DE COBERTURA (2 carpetas de 21 sin abrir)
"archivos download/" y "notas auditoria Claude/" - no abiertas por limite
practico de turno, no por omision.

## REGLA DE ESTE ANEXO
Cada vez que se cierre un gap, se anota aqui con fecha y evidencia, nunca
se borra la linea - se marca CERRADO y se conserva el historial.
