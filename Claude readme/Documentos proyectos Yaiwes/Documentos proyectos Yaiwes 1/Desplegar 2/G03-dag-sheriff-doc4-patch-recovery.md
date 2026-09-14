# G3 · DAG Y SHERIFF DETERMINISTA — Documento 4/4
**Bloques B7 (Origen de cambios + contrato estricto) + B8 (DAG Patch) · UOOS Parte 1**
Fuente: `arquitectura_Wordflow.md`, Salida 2/13, líneas 1104-1425, literal

---

## B7 · Quién puede proponer un cambio, y por dónde pasa

Un patch podrá venir de: OpenClaw, Hermes, Architecture Council, nuevo documento, usuario, Research Engine, Validator, Recovery Engine. Pero todos pasan por la misma frontera, sin excepción:

```
Change Proposal → Impact Analysis → DAG Patch → DAG Validator → Sheriff → Apply
```

Contrato estricto: nadie puede "cambiar el DAG directamente". La única operación válida es:

```
ChangeProposal → DAGPatch → Validation → Sheriff → Apply
```

Esto es una de las piezas que hace que el sistema sea controlable.

**Resultado acumulado hasta esta salida:**
```
WORKFLOW CORE → DAG → DAG VALIDATOR → SHERIFF → POLICY ENGINE → APPROVED DAG → future execution
```
Y en paralelo: `nuevo documento → Change Proposal → DAG Patch → Validator → Sheriff → actualización incremental`.

Deja preparada la base para G6 (Long Loop + Goals + Council + planificación determinista) sin modificar nada de lo construido aquí.

---

## B8 · DAG Patch — modificar sin reconstruir

```python
# dag_patch.py
from dataclasses import dataclass
from typing import Mapping

from .contracts import NodeDefinition
from .dag import DAGDefinition


@dataclass(frozen=True)
class DAGPatch:
    patch_id: str
    base_version: int
    add_nodes: tuple[NodeDefinition, ...] = ()
    remove_nodes: tuple[str, ...] = ()
    replace_nodes: tuple[NodeDefinition, ...] = ()
    metadata_updates: Mapping[str, str] = ()
```

```python
from dataclasses import replace

from .dag import DAGDefinition
from .dag_patch import DAGPatch
from .errors import VersionConflictError


class DAGPatchEngine:

    def apply(self, dag: DAGDefinition, patch: DAGPatch) -> DAGDefinition:

        if patch.base_version != dag.version:
            raise VersionConflictError(
                f"Patch based on version {patch.base_version}, "
                f"current version is {dag.version}"
            )

        nodes = {node.node_id: node for node in dag.nodes}

        for node_id in patch.remove_nodes:
            nodes.pop(node_id, None)

        for node in patch.replace_nodes:
            nodes[node.node_id] = node

        for node in patch.add_nodes:
            if node.node_id in nodes:
                raise VersionConflictError(f"Node already exists: {node.node_id}")
            nodes[node.node_id] = node

        metadata = dict(dag.metadata)
        metadata.update(dict(patch.metadata_updates))

        return replace(
            dag,
            version=dag.version + 1,
            nodes=tuple(nodes.values()),
            metadata=metadata,
        )
```

Ejemplo real de modificación sin reconstruir: Hermes detecta "falta security review" en un DAG `Architecture→OpenCode→Validation`. No se reconstruye todo — se produce un patch que añade el nodo, resultando en `Architecture→OpenCode→Security Review→Validation`. El Workflow conserva: workflow_id, historial, eventos, checkpoints, resultados anteriores, memoria, evidencia. Solo cambia la parte afectada.

---

*G3 completo — 4/4 documentos. Siguiente en el orden confirmado: G4 — Capa de Control · Fundación (5A).*
