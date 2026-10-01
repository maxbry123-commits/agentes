RESOLUCION DE 3 PENDIENTES - 2026-09-17

## 1. FORMATO DEL TEMPLATE PARA LA BIBLIOTECA RAG (resuelto por Claude)

Mismo patron que la ficha del Enchufe Universal (ya real, ya probado).
Formato: archivo YAML por template, en
wordflow_loop/wordflow_loop/templates/nombre.yaml

Campos: template_id, nombre, lenguaje, categoria (backend/frontend/infra),
fuente (origen REUSE_EXISTING o GENERATED_AND_SAVED, source_url con commit
pin, source_commit, generado_por si aplica), codigo (bloque real), usado_en
(lista de proyectos/nodos), veces_reusado (contador), ultima_verificacion
(fecha del ultimo test que confirmo que sigue funcionando).

Regla: cada vez que reuse_selector.py genera codigo nuevo (GENERATE, la
ultima opcion), ese resultado se guarda como template nuevo - la
biblioteca crece sola con el uso.

## 2. PROMPT PARA FUSIONAR LOS 2 CRAZY WALL (resuelto, listo para Sol)

SOL GPT - COMPARACION Y FUSION CRAZY WALL - AGENTE YAIWES
repo: maxbry123-commits/agentes | branch: main | modo: FAIL_CLOSED_STRICT_3_STEPS

FUENTES:
Crazy Wall principal: raiz del repo, Bitacora stated JSON Craxy wall.json
Crazy Wall Orquestador: wordflow loop code Yaiwes/Crazy Wall Orquestador/

OBJETIVO: NO fusionar todavia. Comparar TASK-NODES.json (Orquestador)
contra los nodos del principal - identificar node_id repetidos con
estados distintos (conflicto real) vs conjuntos separados sin conflicto.

PASOS: 1 ANALYZE listar node_id de ambos, marcar interseccion. 2 EXECUTE
escribir tabla comparativa en Claude notas/COMPARACION-2-CRAZY-WALL.md
(node_id, existe_en_principal, existe_en_orquestador, estado_A, estado_B,
conflicto_real). 3 VALIDATE confirmar 100% de nodos cubiertos.

REGLA DURA: prohibido borrar o sobrescribir cualquiera de los 2 archivos
originales. Solo generar la tabla comparativa.
INICIA AHORA.

## 3. CLASIFICACION DE OMNIROUTE/ORCA/OMARCHY/ANYDOC (resuelto por Claude)

Categoria nueva: PENDIENTE DE VERIFICACION POR SOL AL DESCARGAR - Sol
puede confirmar si existen y su repo real al mismo tiempo que los
descarga. Ver prompt de descarga en archivo separado, sin Crazy Wall por
instruccion del Director (Crazy Wall solo para tareas importantes).
