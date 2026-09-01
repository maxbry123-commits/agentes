# A3 · DAG Y SHERIFF DETERMINISTA — Documento 1/4
**Bloques B1 (Manifest) + B2 (State) · UOOS Parte 1**
Fuente: `arquitectura_Wordflow.md`, Salida 2/13, líneas 792-865, literal

**Corrección de trazabilidad:** `TRAZABILIDAD-COMPLETA.md` asociaba a este grupo `GraphMemoryProvider`/Document Graph/Impact Graph — ese contenido no existe en Salida 2, pertenece a Salida 7 y 11 de la fuente (G17-Hermes y G18-Observability de este proyecto). Esta salida es el DAG de ejecución + Sheriff + Policy Engine, sin memoria de grafos. Se corrige aquí y no se repite el error al construir G17/G18.

---

## B1 · PROJECT_MANIFEST

```yaml
salida: A3 - DSL DAG + Sheriff + Policy Engine
serie: 3 de 19
modo: A
objetivo: >
  Convertir una solicitud en una estructura de trabajo verificable.
  Todavía no ejecuta agentes.
frontera_establecida:
  control_plane: [Goals, DAG, Policies, Sheriff, State, Patches, Checkpoints]
  execution: "llega en G8 (Agent Registry + Universal Harness)"
flujo_general: >
  WORKFLOW CORE → DSL DAG → valida estructura → valida dependencias →
  valida permisos → aplica Sheriff → ejecución posterior
depende_de: [A1]
grupos_que_dependen_de_este: [G4, G5, G6, G8, G17]
```

## B2 · state.json

```yaml
grupo: A3
documento_actual: 1 de 4
estado: en_construcción
archivos_a_producir:
  - src/workflow_core/dag.py
  - src/workflow_core/sheriff.py
  - src/workflow_core/policies.py
  - src/workflow_core/dag_patch.py
  - tests/test_dag.py
  - tests/test_sheriff.py
  - tests/test_dag_patch.py

# Contrato del DAG (literal)
dag_definition:
  dag_id: str
  workflow_id: str
  version: int
  nodes: tuple[NodeDefinition, ...]
  metadata: Mapping[str, str]

nota: >
  El DAG solamente describe qué debe hacerse, qué depende de qué,
  qué rol puede hacerlo, qué prioridad tiene. No describe CÓMO el
  agente ejecuta su trabajo — eso es responsabilidad de G8 (Harness).
```

---

*Siguiente: Documento 2/4 — B3 (Sheriff/Policy contracts) + B4 (DAG Validator + Sheriff determinista).*
