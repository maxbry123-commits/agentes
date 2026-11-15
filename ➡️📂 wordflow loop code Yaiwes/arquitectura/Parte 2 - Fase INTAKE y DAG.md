PARTE 2 - Fase INTAKE + DAG (formato Glimmer, microflujo transversal horizontal)

## 1. Capacidad
Esta fase recibe una tarea o componente nuevo, decide si ya existe algo
reusable, y construye el grafo de dependencias antes de ejecutar nada.
No ejecuta codigo todavia - solo decide el orden y el origen.

## 2. Patron - Microflujo transversal horizontal
TASK/COMPONENTE NUEVO -> INTAKE -> CLASIFICAR -> BUSCAR REUSO -> DECIDIR VIA
-> CONSTRUIR GRAFO -> DETECTAR CICLOS -> ORDEN TOPOLOGICO -> READY NODES

## 3. LOOP (detallado)
COMPONENT_INTAKE (component_intake.py)
-> EXISTING_CODE_INTAKE (busca si ya existe, existing_code_intake.py)
-> PROJECT_INTAKE_PIPELINE (arma el contexto del proyecto)
-> PLACEMENT_CLASSIFIER (decide donde va: SUB_AGENT/POOL/WORKFLOW/TOOL)
-> REUSE_SELECTOR (aplica REUSE > PATCH > ADAPT > GENERATE, en ese orden,
   nunca al reves)
-> DAG_ENGINE (construye el grafo con las dependencias reales)
-> DETECTA_CICLOS (si hay ciclo, GAP inmediato, no continua)
-> ORDEN_TOPOLOGICO (determinista, con desempate estable)
-> NODOS_READY (solo los que ya tienen sus dependencias resueltas)

Si falla:
INTAKE_FAIL -> FILE_AUDIT_CONTRACT (verifica que el archivo es legitimo)
-> SI FALLA CONTRATO -> GAP registrado -> siguiente componente independiente

## 4. Aporta
Aporta la garantia de que nunca se genera codigo nuevo si ya existe algo
reusable (REUSE_SELECTOR), y que el orden de ejecucion es siempre el mismo
para el mismo grafo de entrada (determinismo real, no aleatorio).

## 5. Usa
Usa: component_intake.py, existing_code_intake.py, project_intake_pipeline.py,
placement_classifier.py, reuse_selector.py, dag_engine.py, file_audit_contract.py,
code_task_graph.py, code_graph_workspace.py.

## 6. Reglas
- REUSE_EXISTING > PATCH > ADAPT > GENERATE > NEW_DOWNLOAD, siempre en ese orden.
- Nunca se acepta un grafo con ciclos.
- El orden topologico debe ser reproducible (mismo grafo = mismo orden).

## 7. Fallos
CICLO_DETECTADO -> GAP inmediato, no se ejecuta nada de ese subgrafo
CONTRATO_INVALIDO (file_audit_contract.py falla) -> rechazo, no intake parcial
COMPONENTE_DUPLICADO -> reuse_selector decide cual es el vigente

## 8. Test
INPUT: grafo con 5 nodos, 1 ciclo artificial -> EXPECTED: GAP en ese ciclo,
los otros 4 nodos siguen normal, orden topologico reproducible en 2 corridas
distintas con el mismo grafo.

GAP DETECTADO EN ESTA FASE: no vi ningun test file para dag_engine.py ni
reuse_selector.py en runtime/tests/ (carpeta no abierta en detalle todavia,
pendiente confirmar).
