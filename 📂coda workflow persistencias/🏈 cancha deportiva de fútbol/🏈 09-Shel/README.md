# 🏈 09-Shel — YAIWES Persistence Architecture v2.0

## Swarm agent team Navy seals YAIWES

**Nueva versión:** `YAIWES-PERSISTENCE-v2.0`  
**Componente base:** `09-Shel`  
**Fuente upstream:** `shri7-lab/Shel`  
**Rol nuevo:** eslabón seguro de persistencia de tareas dentro de CODA YAIWES.

### Arquitectura nueva

`INPUT → NORMALIZE → CLAIM → CHECKPOINT → SAFE_TASK → VERIFY → EVIDENCE → RELEASE/NEXT`

El código upstream se conserva dentro de `code/` para trazabilidad. El enlace YAIWES nuevo no ejecuta automáticamente código externo: usa `code/coda_persistence/yaiwes_persistence_adapter.py` para estado, checkpoints, reintentos controlados, evidencia y liberación de tareas.

### Contrato universal / Fables

El cableado adopta el sistema suministrado por el usuario: ficha universal con identidad/versionado, `consume/expone`, ejecución, sandbox, límites, evidencia, salud, failover y trazas. El autoensamblaje solo se permite entre entradas/salidas compatibles y validadas.

### Frontera de ejecución

- Descubrimiento estático; no `exec`/`eval` del código upstream.
- Sin shell ni red desde el adapter de persistencia.
- Sin credenciales ni acciones irreversibles desde este eslabón.
- Código upstream preservado como referencia/análisis.
- El runtime nuevo ejecutable es exclusivamente el adapter de persistencia verificado.

### Estado del eslabón

`PENDING → CLAIMED → CHECKPOINTED → VERIFIED → RELEASED`

### Documentación y evidencia

`📂coda workflow persistencias/🏈 cancha deportiva de fútbol/🏈 09-Shel/`


## Cableado maestro — Persistence Mesh v2.1

**Equipo:** Swarm agent team Navy seals YAIWES  
**Versión de malla:** `YAIWES-PERSISTENCE-MESH-v2.1`

`🏈 08-Redcell → 🏈 09-Shel → 🏈 10-Pentest-Swarm-AI`

Este eslabón participa en una malla circular de 24 componentes para handoff de **estado, checkpoint, evidencia y liberación de tarea**. El handoff no ejecuta código upstream ni habilita red, shell o acciones externas. Si un eslabón no valida, la malla falla cerrada y el estado permanece recuperable desde el último checkpoint verificado.

**Contrato de salida:** `CHECKPOINTED|VERIFIED|RELEASED`  
**Contrato de entrada:** `task_id + checkpoint + evidence`  
**Failover:** siguiente eslabón únicamente después de validación del registro y del adapter.
