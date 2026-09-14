# CODE GRAPH — Wordflow LOOP Yaiwes

Contrato único: `tel.workflow/v4`.

Esta raíz es el workspace canónico del grafo de programación. **No es un segundo orquestador**. El grafo representa y serializa el proceso que ya ejecutan el Task Graph y `DAGEngine` existentes.

## Nodos permitidos
`source_file | requirement | capability | task | placement | agent | sandbox | test | evidence | deployment | gap | checkpoint | state`

## Aristas permitidas
`extracts | requires | implements | depends_on | placed_at | owned_by | reviewed_by | executes_in | validated_by | produces | promotes_to | tracks | checkpoint_of | state_of`

## Reglas
1. El contrato debe ser `tel.workflow/v4`.
2. Serialización JSON canónica: claves ordenadas, sin espacios variables.
3. IDs únicos; sin self-edge; endpoints deben existir; duplicados fallan cerrado.
4. `depends_on` solo puede proyectarse entre nodos `task`.
5. La proyección de tareas alimenta el manifest existente de `runtime/src/core/dag_engine.py`.
6. `director_tasks` y `generated_tasks` continúan separados en `runtime/src/core/code_task_graph.py`.
7. Estado, checkpoints y evidencia siguen persistiendo en Crazy Wall; esta raíz no crea una fuente de verdad paralela.
8. Todo código candidato sigue: sandbox → reviewer independiente → deployment determinista.

Implementación: `runtime/src/core/code_graph_workspace.py`.
Tests: `runtime/tests/test_code_graph_workspace.py`.
