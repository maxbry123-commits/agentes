# G2 · RESEARCH ENGINE — Documento 3/4
**Bloques B5 (Sandbox — stub) + B6 (Validación Sheriff) · UOOS Parte 1**
Fuente: `arquitectura_Wordflow.md`, Salida 6/13, líneas 4254-4278 + 4435-4456, literal

---

## B5 · Sandbox Manager (Protocol — solo la abstracción, no la implementación)

El Sandbox queda abstraído desde esta salida, para no atar el Workflow a una tecnología concreta:

```python
class SandboxProvider(Protocol):

    def create(self, request):
        ...

    def execute(self, sandbox_id, command):
        ...

    def destroy(self, sandbox_id):
        ...
```

```
Sandbox Manager
       │
       ├── Docker
       ├── gVisor
       ├── Firecracker
       └── otro provider
```

El Workflow no depende de ninguna implementación concreta. **La implementación real (Sandbox Pool, Broker, Resource Governor de 11 componentes, Watchdog) es G12-G13** — aquí solo se fija el contrato.

---

## B6 · Contrato Sheriff para Research — validación

```
RESEARCH
│
├── ≥20 findings
├── fuentes registradas
├── evidencia
├── repositorio identificado
├── versión identificada
├── commit identificable
├── licencia registrada
└── mirror verificable
        │
        ▼
      SHERIFF
        │
   ┌────┴────┐
   ▼         ▼
 DENY       ALLOW
```

Ningún resultado de investigación pasa a la fase de construcción sin cumplir los 8 requisitos de arriba, verificados por el Sheriff — no por criterio del agente ni del LLM.

---

*Siguiente: Documento 4/4 — B7 (Memory stub + trazabilidad + preview de Hermes) + B8 (recuperación del Sandbox efímero).*
