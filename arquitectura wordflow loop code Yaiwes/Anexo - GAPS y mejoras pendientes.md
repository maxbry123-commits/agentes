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
   estan registrados pero SIN prueba de runtime real (tests_executed_by_
   this_closure: false, segun documentos VERBATIM ya guardados).
8. La reorganizacion de raiz aprobada hace varios turnos (fusionar Skills/
   skills, Conecciones/conectividad, etc.) TODAVIA NO SE EJECUTO - la raiz
   del repo sigue igual de duplicada.
9. Carpeta "Capa workflow GitHub Action" sigue existiendo pese a que el
   Director prohibio expresamente usar GitHub Actions - candidata a
   revisar/eliminar contenido.
10. 13 subcarpetas de wordflow_loop/wordflow_loop/ (adapters, agent_sources,
    code_graph, intake, plugins, prompts, research, skills, templates,
    workflows) y 8 carpetas del nivel superior del proyecto (Crazy Wall
    Orquestador, workspace, motores, las 4 Capas, archivos download, notas
    auditoria Claude) NO se abrieron en esta pasada - pendiente para
    cobertura 100% literal si se requiere.

## TAREAS DERIVADAS, EN ORDEN DE PRIORIDAD

1. Leer contenido real (no solo tamano) de los 7 archivos de gobernanza -
   confirmar si son stubs o implementacion real.
2. Leer contenido real de recovery/checkpoint.py - confirmar persistencia
   real vs memoria de proceso.
3. Ejecutar la deprecacion de runtime/src/agent/agent_router.py (decision
   ya tomada, falta ejecutar).
4. Poblar contracts/ y evidence/ (estan vacias) con los schemas y el
   manifest de evidencia ya disenados en los documentos VERBATIM.
5. Comparar source_truth_reconciler.py vs truth_reconciler.py, decidir cual
   se queda.
6. Ejecutar la reorganizacion de raiz ya aprobada (sigue pendiente).
7. Revisar y decidir el destino de "Capa workflow GitHub Action" (prohibido
   su uso).
8. Abrir las 13+8 carpetas restantes si se requiere cobertura 100% literal.
9. Disenar y correr la primera prueba real de runtime de al menos 1 agente
   del Fleet (AGENT_FLEET_READY_FOR_TEST.json lo marca como pendiente).

## REGLA DE ESTE ANEXO
Cada vez que se cierre un gap de esta lista, se anota aqui con fecha y
evidencia (path+sha256+resultado), nunca se borra la linea - se marca
CERRADO y se conserva el historial.
