# 🏈 16-Autonomous-Pentest-Agent — YAIWES Persistence Architecture v2.0

## Swarm agent team Navy seals YAIWES

**Nueva versión:** `YAIWES-PERSISTENCE-v2.0`  
**Componente base:** `16-Autonomous-Pentest-Agent`  
**Fuente upstream:** `deltaRed1a/autonomous-pentest-agent`  
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

`📂coda workflow persistencias/🏈 cancha deportiva de fútbol/🏈 16-Autonomous-Pentest-Agent/`

## Cableado Swarm v3

**Equipo:** Swarm agent team Navy seals YAIWES  
**Cadena:** `yaiwes-navy-seals-persistence-chain-v3`  
**Posición:** `16/24`  
**Anterior:** `🏈 15-Pentdem`  
**Siguiente:** `🏈 17-AI-Red-Team-Agent`

`🏈 15-Pentdem → 🏈 16-Autonomous-Pentest-Agent → 🏈 17-AI-Red-Team-Agent`

Contrato de handoff: `yaiwes.task-state.v2`. Este eslabón recibe estado de tarea, guarda checkpoint/evidencia mediante el adapter YAIWES y entrega el estado al siguiente eslabón. El runner maestro solo carga los adapters YAIWES generados; no invoca automáticamente el código upstream.
