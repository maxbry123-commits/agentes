# G4 · CAPA DE CONTROL — FUNDACIÓN (5A) — Documento 1/4
**Bloques B1 (Manifest) + B2 (State) · UOOS Parte 1**
Fuente: `SALIDA_1_CAPA_CONTROL_PARTE_1.md`, secciones 1-8 (líneas 1-380), literal

**Nota de ritmo:** este grupo tiene 4.660 líneas de fuente repartidas en 3 partes — el bloque de fuente más grande de las 19 salidas. Se construye en varios turnos para no perder fidelidad. Este documento cubre solo las secciones 1-8 (identidad hasta flujo de ejecución); las secciones 9-16 de Parte 1, más Partes 2 y 3, van en los siguientes documentos.

**Corrección aplicada:** la fuente dice "reemplazar Dagu" / "Dagu ejecuta" en varios puntos — se preserva literal en las citas de abajo (es el INPUT BLOCK exacto), pero donde el propio proyecto ya decidió el motor (Decisión 01, Documento 00: Temporal, no Dagu), la nota se hace explícita en cada punto donde aplica.

---

## B1 · PROJECT_MANIFEST

```yaml
salida: G4 - Capa de Control · Fundación (CC1+CC2 parcial+CC4, primera parte)
serie: 4 de 19
modo: A  # el INPUT BLOCK ya es la especificación completa, dada literal por el Director
regla_del_documento_fuente: >
  "Todo lo que dijo el Director va literal, entre bloques marcados
  INPUT BLOCK. Nada se resume, nada se filtra, nada se reinterpreta."
identidad:
  nombre: "OpenClaw Control Plane Lightweight Layer"
  ubicacion: "antes de OpenClaw"
  tipo: "capa Python/YAML de control"
  no_es: [kernel, orquestador, scheduler, "motor DAG", "memoria inteligente"]
  clasificacion_propia: >
    "Execution Knowledge Layer (EKL) — Sistema Determinista de Conocimiento
    Operativo. Su función no es recordar conversaciones, sino gobernar la
    ejecución mediante conocimiento estructurado."
objetivo_real: >
  Un tool como calculadora científica: no necesita IA para dar el mismo
  resultado 100% siempre. No analiza, no piensa, solo ejecuta pasos de
  su sistema interno. 90% code / 10% LLM cuando se requiere.
depende_de: [G1, G3]
grupos_que_dependen_de_este: [G5, G6, G7, G8, G9, G10, G11, G12, G13, G14]
```

## B2 · state.json

```yaml
grupo: G4
documento_actual: 1 de 4 (de un total de más de 4 — ver nota de ritmo)
estado: en_construcción
avance_fuente:
  parte_1_secciones_1_a_8: leído y construido (este documento)
  parte_1_secciones_9_a_16: pendiente
  parte_2_completa: pendiente
  parte_3_completa: pendiente
  capa_de_control_1_indice_html: leído completo en checkpoint previo
```

---

## Prohibiciones duras (literal)

```
FORBIDDEN:
- crear kernel              - reemplazar OpenClaw
- crear scheduler           - reemplazar Dagu ⚠️ ver nota
- crear queue                - ejecutar procesos pesados
- crear agent loop

El código NO puede:
ejecutar comandos del sistema directamente · crear procesos ·
administrar colas · crear DAG propio · reemplazar Dagu ⚠️ · modificar OpenClaw

rules:
  no_kernel: true
  no_orchestrator: true
  no_scheduler: true
  no_memory_engine: true

Implementación pequeña: Python + YAML. Sin base propia. Sin loops
infinitos. Sin procesos residentes pesados. Sin ejecutar comandos.
Sin tocar OpenClaw internamente.

"Todo esto son capas externas sin kernel, son adiciones, extensiones
que deben poder funcionar en cualquier agente y orquestador sin
rediseñar el kernel o tocar el código del agente."
```
⚠️ **Nota de corrección:** las 2 menciones a "reemplazar Dagu" son literales del INPUT BLOCK original — la prohibición en sí sigue siendo válida (la Capa de Control no reemplaza al motor de workflow, sea cual sea), pero el motor real ya no es Dagu sino **Temporal** (Decisión 01). Se preserva la cita exacta por regla de literalidad; se aplica la sustitución conceptual, no textual.

## Función — qué sí hace (literal)

```
"La capa solo debe: decidir · validar · enrutar · auditar ·
detener cuando hay riesgo"

La ejecución pertenece a: Dagu⚠️→DAG · Harness→puente ·
OpenClaw→agente · Skills/MCP/API→capacidades

"Su función es ser el freno, filtro y validador de OpenClaw."
"Entrada → validar → decidir → permitir/bloquear → registrar"
```

## Ubicación en el stack (literal, motor sustituido conceptualmente)

```
USER / API / UI
       │
       ▼
DSL DAG SHERIFF CONTROL LAYER (Python + YAML)
       │
  ┌────┴────┐
  ▼         ▼
SHERIFF   TEMPORAL ⚠️ (fuente dice "DAGU")
VALIDACIÓN  EJECUCIÓN DAG
              │
              ▼
           HARNESS
              │
              ▼
           OPENCLAW
              │
        Skills / MCP / API
              │
              ▼
       LiteLLM / HF / Servicios

No va: dentro de OpenClaw · dentro del motor de workflow · dentro de LiteLLM.
Va como capa intermedia de decisión y control.

Ubicación física:
GitHub /control-layer/ → dsl/ · dag/ · schemas/ · sheriff/ · council/
VPS ⚠️ (ver Decisión 02, Documento 00: sin VPS, todo en HF)
```
⚠️ Segunda corrección: la fuente menciona "VPS" como ubicación física — Decisión 02 ya estableció que este proyecto no usa VPS. Con la arquitectura final de 5 HF (`arquitectura_final_de_hf.md`), esta Capa de Control corre específicamente en **HF1** (OpenClaw+Hermes+Supervisor), no en los HF2-5 (esos son Spaces ligeros de modelos/agentes). La ruta `/control-layer/` aplica dentro del repositorio de código en GitHub, que HF1 ejecuta — no en un VPS ni repartido entre los 5 HF.

## Distribución por lenguaje (literal)

```
YAML → define reglas DSL, políticas Sheriff, pasos DAG, roles Council, config
Python → lee YAML, ejecuta validaciones, aplica decisiones, controla flujo,
         genera auditoría, conecta con motor de workflow/OpenClaw
JSON → estado de tareas, resultados, evidencias, historial, logs estructurados

"Todo lo que valla en JSON que pueda ir en YAML y Python mejor."
```

## Arquitectura de 3 archivos (literal)

**YAML — reglas permanentes ("la constitución del sistema"):**
```yaml
dsl_version: 2.0
execution:
  mode: strict
  deterministic: true
  reasoning: false
  inference: false
  auto_fix: false
  auto_retry: false
security:
  allow_delete_outside_workspace: false
  allow_new_nodes: false
  allow_dag_changes: false
failure:
  on_assert: stop
  on_schema: reject
  on_security: reject
output:
  format: json
  schema: output_v2
```

**JSON — instrucciones de la tarea (no reglas globales, solo el flujo):**
```json
{
  "task_id": "TASK-001",
  "repo": "agentes",
  "nodes": [
    {"id": "N001", "action": "EXEC", "command": "git ls-files", "next": "N002"},
    {"id": "N002", "action": "COPY", "next": null}
  ]
}
```

**Sheriff — antes de ejecutar:** `YAML + JSON → Parser → Schema → Sheriff → Executor`. Verifica: nodos duplicados, acciones permitidas, DAG válido, ciclos prohibidos, acciones no registradas, violación de política. Si falla algo: `PROGRAM_STATUS=REJECTED`, el Executor nunca comienza.

**Tercer archivo — Registry independiente:**
```
rules.yaml    → políticas y reglas del motor
registry.json → catálogo de acciones, validadores, tipos, comandos permitidos
task.json     → la misión concreta (nodos, DAG, instrucciones)
```
Esta separación evita que una tarea pueda cambiar las reglas del sistema.

## Flujo de ejecución (literal, motor sustituido conceptualmente)

Flujo simple: `Nueva tarea → task.json → Python controller.py → Lee YAML → SHERIFF valida → APPROVED/REJECTED → [si aprobado] → Temporal⚠️ ejecuta → OpenClaw trabaja → JSON guarda evidencia`

Flujo funcional completo:
```
INPUT TASK → Goal Parser → Schema Validator → Sheriff Layer →
Council Check → DAG Builder → Temporal⚠️ → Harness → OpenClaw →
Validation → Output Goal → Audit + History
```

---

*Siguiente: Documento 2/4 — secciones 9-13 de Parte 1 (por qué el formato de prompt falla, las 12 mejoras para determinismo, los 18 problemas detectados, estructura de nodo, catálogos cerrados).*
