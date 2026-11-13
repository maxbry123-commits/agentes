# G2 · RESEARCH ENGINE — Documento 4/4
**Bloques B7 (Plan/Memoria/Trazabilidad) + B8 (Recuperación del Sandbox) · UOOS Parte 1**
Fuente: `arquitectura_Wordflow.md`, Salida 6/13, líneas 4283-4483, literal

---

## B7 · Conexión con memoria, trazabilidad, preview de Hermes

El Workflow no se acopla a Graphiti directamente — se define un Protocol:

```python
class MemoryProvider(Protocol):

    def store(self, record):
        ...

    def query(self, query):
        ...

    def link(self, source, target):
        ...
```
Implementable con Graphiti, GraphRAG, Vector DB, Graph DB, PostgreSQL, u otro sistema. **La implementación completa de 4 capas es G16.**

Qué se registra — cada investigación genera una cadena de relaciones trazable:
```
Workflow → Research → Source → Repository → Version → Commit →
Mirror → Architecture Decision → Agent Execution → Validation
```
Esto permite reconstruir por qué se tomó una decisión.

Preview de Hermes (todavía no ejecuta agentes en esta salida — su rol completo es G17):
```
SENTINELA · JUEZ · SUPERVISOR · VALIDADOR · VERIFICADOR
```
Recibe: Research, Architecture, Execution, Validation, Documents, Changes. Puede generar: `Hermes Finding → Change Proposal → DAG Patch → Sheriff`.

Documento nuevo — flujo de bajo impacto sin reconstruir todo:
```
nuevo documento → Document Detector → Impact Analysis → ¿afecta arquitectura?
  NO → continue
  SÍ → Council → DAG Patch
```

**Resultado acumulado hasta esta salida** (tal como lo resume la fuente):
- Salida 1: State / Events / Contracts
- Salida 2: DAG / Sheriff / Policies / DAG Patch
- Salida 3: Goals / Council / Ask Preview / Long Loop
- Salida 4: Checkpoint / Recovery / Watchdog / Resume
- Salida 5: Agent Registry / Universal Harness / Routes
- Salida 6 (esta): Research / Repositories / Mirrors / Skills / Context / Sandbox / Memory Adapter

*Nota de trazabilidad: esta numeración "Salida 1-6" es la de la fuente `arquitectura_Wordflow.md` (13 salidas), distinta de la numeración G1-G19 de este proyecto — ver tabla de equivalencias en `CHECKPOINT-ESTADO.md`.*

---

## B8 · Recuperación — el Sandbox es efímero, la información no

```
Sandbox
   │
   ├── source · temp · build · artifacts
          │
          ▼
       checkpoint
          │
          ▼
    persistent storage
```

Si el Sandbox desaparece: `nuevo Sandbox → restore checkpoint → restore repository mirror → restore context → continue`. No se pierde la investigación ya hecha.

---

*G2 completo — 4/4 documentos. Siguiente en el orden confirmado: G3 — DAG y Motor de Grafos.*
