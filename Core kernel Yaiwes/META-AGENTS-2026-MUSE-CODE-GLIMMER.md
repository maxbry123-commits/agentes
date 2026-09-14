# Meta Agents 2026 — Muse Code, Muse Glimmer y agentes publicados por Meta

Fecha de auditoría: 2026-09-13
Destino YAIWES: `Core kernel Yaiwes/`

## 1. Alcance

Este documento separa tres capas que no deben confundirse:

1. **Muse Code**: agente/harness de programación de Meta. Su runtime completo no está publicado íntegramente; Meta sí publica el SDK, el protocolo MSP y recetas oficiales que muestran sesiones, approvals, subagentes, recuperación y auditoría.
2. **Muse Glimmer**: modelo agentic open-weight acompañado por un **agente de referencia ejecutable** (`agent_loop.py`, `response_parser.py`, `run_agent.py`) que implementa planificar → llamar herramientas → ejecutar → devolver observación → autocorregir.
3. **Meta Model Cookbook 2026**: repositorio oficial que contiene implementaciones y recetas de agentes adicionales, entre ellas `metacua` (computer-use agent macOS), GitHub repo agent, patrones multi-agent y recetas completas de Muse Code.

Fuentes oficiales utilizadas:

- https://github.com/meta-models/muse-code-sdk
- https://github.com/meta-models/meta-oss-cookbook
- https://github.com/meta-models/meta-model-cookbook

No se incluyen forks de terceros ni repositorios que sólo mencionen Meta/Muse.

---

## 2. Muse Code — cómo funciona el agente

### 2.1 Separación de responsabilidades

Muse Code no debe entenderse como un único `while` alrededor de un LLM. La arquitectura observable en el SDK/MSP separa:

- **host `muse serve`**: autoridad de ejecución y sesiones;
- **Muse Session Protocol (MSP)**: protocolo tipado entre cliente y host;
- **SDK**: cliente event-driven que inicia/reanuda sesiones, envía turns, responde approvals y reconstruye estado;
- **SessionFold**: reduce eventos de servidor a una vista consistente de items, turns, session state, approvals y user input;
- **PendingCommandSet**: registra comandos todavía no reconciliados;
- **TurnSubmitter**: envía `turn/start` y conserva el contrato de replay con el mismo `commandId`;
- **ApprovalRouter**: transporta decisiones de autorización usando choices creados por el servidor;
- **GapFiller**: recupera eventos perdidos mediante `view/gap` + `view/page`;
- **TurnHandle**: representa un turno y permite observar items/deltas hasta su terminación;
- **host-death logic**: diferencia sesiones durables, ephemeral y valores desconocidos.

### 2.2 Flujo lógico

```text
usuario/cliente
    ↓
MuseClient
    ↓
session/start | session/resume
    ↓
Session
    ↓
turn/start
    ↓
Muse host
    ↓
modelo/agente decide acciones
    ↓
approval / herramienta / shell / edición / subagente
    ↓
eventos MSP
    ↓
Session.apply(event)
    ↓
SessionFold + PendingCommandSet
    ↓
TurnHandle / estado observable
```

### 2.3 Estado derivado, no inventado

El SDK público declara explícitamente que no es la autoridad durable. Su estado se deriva de eventos emitidos por el servidor. Esto evita que el cliente marque arbitrariamente una acción como terminada.

Principio reutilizable para YAIWES:

```text
EVENTOS AUTORITATIVOS → FOLD/REDUCER → ESTADO
```

En lugar de permitir:

```text
agent.status = DONE
```

usar:

```text
NODE_COMPLETED(event)
   ↓
StateFold.apply(event)
   ↓
status = DONE
```

### 2.4 Idempotencia y PendingCommandSet

Muse Code usa `commandId` para distinguir una operación lógica de sus reintentos. Si se pierde la conexión, un retry correcto reutiliza la misma identidad de comando en vez de crear una operación nueva.

Aplicación YAIWES:

```json
{
  "command_id": "uuidv7",
  "node_id": "N17",
  "agent_id": "SOL-7",
  "operation": "github.commit",
  "payload_hash": "sha256:...",
  "attempt": 2,
  "status": "PENDING"
}
```

Regla:

```text
retry = mismo commandId + mismo payload
```

Esto reduce duplicados en commit, push, MCP, APIs y escrituras de filesystem.

### 2.5 Cola y steering

MSP incluye operaciones como:

- `turn/start`
- `turn/steer`
- `turn/interrupt`
- `turn/cancel`
- `turn/unqueue`
- `session/start`
- `session/resume`
- `session/fork`
- `session/read`
- `session/list`

`turn/start` puede expresar disposiciones de cola/steer/replace cuando ya existe trabajo corriendo. La concurrencia vive en el runtime, no en una promesa del prompt.

### 2.6 Recovery de gaps

Cuando hay pérdida de delivery aparece `view/gap`. El SDK pausa la vista corriente, recorre páginas faltantes con `view/page`, inserta el prefijo perdido en orden de cursor y después libera la cola de eventos live retenidos.

Patrón:

```text
cursor 100
   ↓
se detecta gap 101..108
   ↓
CURRENT=false
   ↓
pausar acciones dependientes
   ↓
view/page
   ↓
fold 101..108
   ↓
reanudar live tail
```

Para Crazy Wall esto significa que una revisión perdida debe congelar CLAIM/EXECUTE hasta reconciliar el estado.

### 2.7 Durabilidad y caída del host

El SDK distingue:

- `durable`
- `ephemeral`
- valor desconocido

Un valor desconocido no obtiene garantías por inferencia: se trata conservadoramente. Una desconexión no equivale automáticamente a `FAILED` ni `SUCCEEDED`; una sesión durable puede reanudarse y obtener los terminales reales después.

### 2.8 Approvals fail-closed

MSP expone modos cerrados de approval como:

- `allowAll`
- `promptUnmatched`
- `onRequest`
- `denyUnmatched`

Las choices válidas las crea el servidor. El cliente selecciona una de ellas; no debe poder inventar permisos nuevos.

### 2.9 Subagentes

MSP incluye primitivas dedicadas para lifecycle de subagentes, incluyendo follow-up task, interrupt, stop, resume, reopen, close y readResult. Esto prueba que el árbol padre/hijo forma parte del protocolo y no es sólo prompting.

Patrón YAIWES recomendado:

```text
SWARM ROOT
 ├─ child/session → N17
 ├─ child/session → N18
 └─ child/session → N19
```

Cada child debería registrar como mínimo `parentId`, `childId`, `sessionId`, `taskId`, `claimId` y `resultId`.

---

## 3. Muse Glimmer — agente de referencia ejecutable

### 3.1 Componentes

El agente de referencia publicado por Meta vive en `meta-oss-cookbook/agentic-fundamentals/` y contiene:

- `agent_loop.py`
- `response_parser.py`
- `run_agent.py`

### 3.2 Loop

El loop implementa:

```text
USER TASK
   ↓
MODEL GENERATION
   ↓
MuseGlimmerATEMParser
   ↓
¿tool calls?
   ├─ NO → final answer
   └─ SÍ
       ↓
     ToolRegistry.call()
       ↓
     resultado real
       ↓
     append tool observation
       ↓
     MODEL GENERATION otra vez
```

La capacidad agentic no depende de un DAG gigante: surge de generación + protocolo de tool calls + ejecución + realimentación + autocorrección.

### 3.3 ToolRegistry

Las herramientas se registran con nombre, descripción, JSON schema y función Python. El agente pasa los schemas al chat template y luego despacha la función seleccionada.

Ventaja: extremadamente simple y extensible.

Límite: el reference loop no sustituye un Sheriff. El registro de una función concede capacidad de ejecución; por eso YAIWES debe interponer policy, schema validation y autorización antes del side effect.

### 3.4 Parser ATEM y canales

Glimmer usa canales con destinatarios:

- `to=self`: reasoning
- `to=<tool>`: tool call
- `to=user`: respuesta final

El parser extrae `reasoning`, `tool_calls` y `final_content`. También evita tratar una invocación simplemente citada dentro del canal de usuario como una llamada real.

### 3.5 Diferencia con Muse Code

Muse Glimmer reference agent aporta principalmente:

```text
reason → choose tool → execute → observe → self-correct
```

Muse Code aporta una capa de sistema más amplia:

```text
sessions + queues + approvals + audit + recovery + subagents + protocol
```

Por tanto son complementarios, no duplicados.

---

## 4. Otros agentes/código agentic publicado por Meta en 2026

La organización oficial `meta-models` publica actualmente tres repositorios públicos relevantes y no duplicados:

1. `meta-models/muse-code-sdk`
2. `meta-models/meta-oss-cookbook`
3. `meta-models/meta-model-cookbook`

El tercero contiene código agentic adicional que no conviene descargar por separado porque ya quedará incluido una sola vez en el repositorio completo:

- **metacua**: agente de computer-use para macOS basado en ciclo screenshot → decisión → acción → nueva observación;
- **GitHub repo agent**: bot autónomo de GitHub Actions para triage/review/fix workflows;
- **computer-use Linux/Cua**;
- **multi-agent product studio**;
- patrones de basic agent loop, tool use, context management y validated edits;
- recetas completas de Muse Code: audit log, replay, approvals, containment, subagent fanout, goal tracking y loop/cron.

Se descargan los repos fuente completos para no fragmentar dependencias y para conservar pruebas, manifests, ejemplos y documentación oficial.

---

## 5. Destinos YAIWES

El motor de descarga/extracción publica cada fuente en:

```text
Core kernel Yaiwes/
├── Meta-Muse-Code-SDK-2026/
│   ├── code/
│   ├── _archives/
│   └── DOWNLOAD_EXTRACT_MANIFEST.json
├── Meta-Muse-Glimmer-Agent-2026/
│   ├── code/
│   ├── _archives/
│   └── DOWNLOAD_EXTRACT_MANIFEST.json
└── Meta-Agent-Cookbook-2026/
    ├── code/
    ├── _archives/
    └── DOWNLOAD_EXTRACT_MANIFEST.json
```

Cada manifest debe contener commit fuente, hashes, número de archivos, hash del árbol extraído y prueba de reconstrucción/extracción.

---

## 6. Regla de integración con Core Kernel YAIWES

Estos repos se incorporan como **fuentes vendorizadas/auditables**, no como código automáticamente confiable en producción.

Antes de cablearlos al runtime:

```text
SOURCE VERIFIED
 → LICENSE REVIEW
 → INVENTORY
 → SECURITY/SIDE-EFFECT REVIEW
 → SHERIFF ADAPTER
 → TESTS
 → PASS
 → ENABLE
```

Los pesos grandes del modelo Muse Glimmer no se copian al repositorio Git porque son artefactos de modelo y pueden usar distribución/Hugging Face/LFS. Aquí se conserva el código de agente, integración y recetas oficiales; los pesos deben resolverse mediante un model store separado.

---

## 7. Conclusión

Muse Code enseña principalmente cómo construir un runtime confiable alrededor de un agente: sesiones autoritativas, folds, commands pendientes, idempotencia, recovery, approvals y subagentes.

Muse Glimmer enseña el kernel agentic mínimo: generar, parsear, llamar tools, devolver observaciones y autocorregir.

Para YAIWES la combinación adecuada es:

```text
Muse-style Session/Event Kernel
        +
Crazy Wall / Sheriff
        +
Glimmer-style agent loop
        +
MCP/API adapters
        =
YAIWES agent runtime verificable
```
