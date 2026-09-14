# Investigación técnica — Agentes Meta 2026 para Core Kernel YAIWES

**Fecha de auditoría:** 2026-09-13 / verificación de publicación 2026-09-14  
**Destino YAIWES:** `Core kernel Yaiwes/`  
**Estado de descarga/extracción:** `VERIFICADO / PUBLICADO`  

---

# 0. Resumen ejecutivo

Esta investigación separa con precisión cuatro conceptos que suelen confundirse:

1. **Muse Code** — agente/harness de programación de Meta. El runtime completo de `muse` no está publicado íntegramente como un único repositorio abierto, pero Meta publica el SDK, el protocolo MSP y recetas oficiales suficientes para reconstruir gran parte de su arquitectura operativa.
2. **Muse Glimmer Agent** — agente de referencia ejecutable publicado por Meta alrededor de Muse Glimmer. Incluye loop, parser ATEM, registro de herramientas, ejecución y realimentación de resultados.
3. **MetaCua** — agente autónomo de computer-use para macOS que observa la pantalla y actúa con mouse/teclado reales.
4. **Agentes/recetas agentic adicionales del Meta Model Cookbook 2026** — GitHub Repo Agent, computer-use en Linux con Cua + MCP, multi-agent product studio y patrones de agentes verificables.

## PUNTOS MÁS RELEVANTES

> **PUNTO CLAVE 1 — Muse Code no confía en la memoria del agente.** Usa sesiones, eventos, cursores, `commandId`, reconciliación, approvals y recuperación.

> **PUNTO CLAVE 2 — Muse Glimmer demuestra que el kernel agentic mínimo puede ser pequeño:** `modelo → parse → tool → resultado → modelo otra vez`.

> **PUNTO CLAVE 3 — MetaCua usa un loop de percepción-acción real:** `screenshot → razonar → click/type → screenshot → corregir`.

> **PUNTO CLAVE 4 — El GitHub Repo Agent mete el agente dentro de GitHub Actions**, con disparadores por issue/PR/comando y seguridad diferenciada para forks.

> **PUNTO CLAVE 5 — El computer-use Linux separa el agente del host mediante Cua + Docker + MCP**, evitando que el modelo toque directamente la máquina principal.

> **PUNTO CLAVE 6 — El patrón multi-agent coordina varios perfiles especializados mediante estado compartido/Kanban**, en lugar de dejar chats independientes sin coordinación.

> **PUNTO CLAVE 7 — Para YAIWES, lo más reutilizable no es un modelo concreto sino el patrón de runtime:** `EventStore + StateFold + PendingCommandSet + Sheriff + Claims + MCP/API`.

---

# 1. Fuentes oficiales auditadas

Se utilizaron únicamente repositorios oficiales de la organización `meta-models`:

- `https://github.com/meta-models/muse-code-sdk`
- `https://github.com/meta-models/meta-oss-cookbook`
- `https://github.com/meta-models/meta-model-cookbook`

No se consideran forks de terceros como fuentes autoritativas.

Los repositorios fueron descargados con commits fijados para reproducibilidad:

| Fuente | Commit fijado | Destino YAIWES |
|---|---|---|
| `meta-models/muse-code-sdk` | `fbce769ccb75ab971d00e01a00fe076de4c773fc` | `Meta-Muse-Code-SDK-2026/` |
| `meta-models/meta-oss-cookbook` | `499ad7422c2175cf47dbad5df37c4c8f6c11f924` | `Meta-Muse-Glimmer-Agent-2026/` |
| `meta-models/meta-model-cookbook` | `fb440d68f9f1eb735faca57092b0729ad6195d96` | `Meta-Agent-Cookbook-2026/` |

Cada destino contiene:

```text
code/
_archives/
DOWNLOAD_EXTRACT_MANIFEST.json
```

El manifest conserva fuente, commit, hashes, número de archivos y prueba de reconstrucción/extracción.

---

# 2. MUSE CODE — agente/harness de programación

## 2.1 Qué es realmente

Muse Code no es simplemente un LLM con un prompt largo. Es un **harness de programación y ejecución** alrededor de modelos Muse. La parte pública muestra una arquitectura de sesiones que separa claramente:

```text
MODEL
  │
  ▼
MUSE HOST / SERVE
  │
  ▼
MSP — Muse Session Protocol
  │
  ▼
SDK / CLIENT
  │
  ├─ Session
  ├─ SessionFold
  ├─ PendingCommandSet
  ├─ TurnSubmitter
  ├─ ApprovalRouter
  ├─ GapFiller
  ├─ TurnHandle
  └─ Host-death / durability
```

El SDK público no pretende ser el servidor autoritativo. Consume eventos del host y deriva una visión coherente de la sesión.

## 2.2 Session

`Session` es el agregado principal del cliente. Representa una conversación/trabajo vivo y compone:

- estado derivado;
- commands pendientes;
- turns;
- approvals;
- recovery de eventos perdidos;
- estado de caída del host;
- conexión opcional al runtime.

Flujo simplificado:

```text
session/start
    ↓
Session creada
    ↓
turn/start
    ↓
trabajo del agente
    ↓
eventos MSP
    ↓
Session.apply(event)
    ↓
fold + routing + pending reconciliation
```

### PUNTO RELEVANTE

**El cliente no debería marcar un nodo como DONE porque un agente lo dijo. Debe derivar DONE de un evento autoritativo.**

Aplicación YAIWES:

```text
NODE_COMPLETED event
      ↓
CrazyWallFold.apply()
      ↓
state = DONE
```

---

## 2.3 SessionFold — estado derivado

`SessionFold` mantiene la vista cliente de:

- items;
- turns;
- session state;
- approvals pendientes;
- user input pendiente;
- resultados/terminales observados.

Patrón:

```text
EVENT 1
EVENT 2
EVENT 3
   ↓
REDUCER / FOLD
   ↓
CURRENT STATE
```

### Por qué importa

Esto reduce estados inventados y divergentes. Si dos clientes reciben los mismos eventos en el mismo orden, deben derivar el mismo estado.

### Adaptación YAIWES

```text
Crazy Wall JSON actual
        ↓ migrar hacia
append-only events
        ↓
CrazyWallFold
        ↓
read-only current state
```

---

## 2.4 PendingCommandSet — operación enviada ≠ operación confirmada

Muse conserva un conjunto explícito de comandos todavía no reconciliados.

Estados conceptuales:

```text
CREATED
  ↓
SUBMITTED
  ↓
ACKED / REJECTED / RECLAIMED
  ↓
RETIRED
```

Mientras un side effect no está reconciliado, no debe convertirse mágicamente en PASS.

### PUNTO RELEVANTE

**Este patrón resuelve una de las causas más frecuentes de duplicados:** conexión rota después de ejecutar pero antes de recibir respuesta.

Para YAIWES es especialmente útil en:

- `git commit`;
- `git push`;
- escritura de archivos;
- llamadas MCP;
- APIs externas;
- deploys;
- claims/releases de nodos.

---

## 2.5 `commandId` e idempotencia

MSP usa identidad de comando. Un retry correcto reutiliza la misma identidad lógica.

```text
COMMAND
  commandId = UUIDv7
  payloadHash = SHA256(payload)
        │
        ├─ intento 1 falla transport
        │
        └─ intento 2 usa MISMO commandId + MISMO payload
```

### Regla YAIWES propuesta

```json
{
  "command_id": "019...",
  "node_id": "N17",
  "agent_id": "SOL-7",
  "operation": "github.push",
  "payload_hash": "sha256:...",
  "attempt": 2,
  "status": "PENDING"
}
```

> **PUNTO RELEVANTE:** `retry` no debe significar `crear otra operación`. Debe significar `reconciliar/repetir la misma operación lógica`.

---

## 2.6 Cola, steering, interrupt y cancelación

El protocolo incorpora primitivas como:

```text
turn/start
turn/steer
turn/interrupt
turn/cancel
turn/unqueue
session/start
session/resume
session/fork
session/read
session/list
```

Esto mueve la concurrencia fuera del prompt y la convierte en semántica del runtime.

### YAIWES

La cola 1×1 no debe depender de una instrucción textual. Debe estar implementada por el kernel:

```text
QUEUE
  ↓
CLAIM
  ↓
IN_PROGRESS
  ↓
COMPLETE / RELEASE
```

---

## 2.7 `view/gap` + `view/page` — recuperación de eventos perdidos

Muse trata un gap de eventos como una condición formal.

```text
cursor A
  ↓
se detecta delivery gap
  ↓
CURRENT = false
  ↓
retener live tail
  ↓
view/page(after,next)
  ↓
recuperar estado faltante
  ↓
splice en orden
  ↓
reanudar stream
```

### PUNTO RELEVANTE

**Gap no significa “seguir con lo que recuerdo”. Significa detener acciones dependientes y reconciliar.**

Para YAIWES:

```text
agent revision < CrazyWall revision
        ↓
STALE
        ↓
NO CLAIM / NO EXECUTE
        ↓
REFRESH + RECONCILE
```

---

## 2.8 Durable vs ephemeral

El SDK diferencia sesiones:

- `durable`;
- `ephemeral`;
- unknown/open-enum.

Un valor desconocido no obtiene garantías por optimismo.

### PUNTO RELEVANTE

**UNKNOWN no debe convertirse a SUCCESS ni FAILURE.**

Estados YAIWES recomendados:

```text
SUCCEEDED
FAILED
UNKNOWN_NEEDS_RECONCILIATION
```

---

## 2.9 Approvals

MSP define modos como:

```text
allowAll
promptUnmatched
onRequest
denyUnmatched
```

Las opciones válidas de una approval son emitidas por el servidor y el cliente selecciona una opción existente.

### PUNTO RELEVANTE

Esto evita que el agente se auto-conceda una capacidad inexistente.

Aplicación Sheriff:

```text
Agent proposal
     ↓
Sheriff creates allowed choices
     ↓
choiceId
     ↓
agent/operator selects
     ↓
execution
```

---

## 2.10 Subagentes

MSP incluye lifecycle explícito para subagentes:

```text
subagent/followupTask
subagent/interrupt
subagent/stop
subagent/resume
subagent/reopen
subagent/close
subagent/readResult
```

Eso implica un árbol de ownership:

```text
PARENT SESSION
   ├─ CHILD A
   ├─ CHILD B
   └─ CHILD C
```

Cada child debería tener identidad, estado y resultado trazables.

### Adaptación YAIWES

```text
parentId
childId
sessionId
taskId
claimId
resultId
```

---

## 2.11 Audit log, deterministic replay y crash recovery

Las recetas públicas de Muse Code documentan patrones de:

- log append-only;
- replay determinista;
- recuperación después de muerte del host;
- staged approvals;
- sandbox containment;
- goal tracking;
- loop/cron;
- subagent fanout.

### PUNTO RELEVANTE

**Un log de auditoría útil debe servir también para reconstruir y repetir determinísticamente una sesión, no sólo para mirar qué ocurrió.**

---

## 2.12 Qué NO está abierto completamente

No debe confundirse `muse-code-sdk` con todo el runtime interno de Muse Code.

Público/verificable:

- SDK;
- MSP/schema;
- SessionFold;
- PendingCommandSet;
- cliente/connection;
- recipes;
- protocolos de approvals/recovery/subagents.

No se debe afirmar sin evidencia que todo el kernel de `muse serve` esté publicado en ese repo.

---

# 3. MUSE GLIMMER AGENT — kernel agentic de referencia

## 3.1 Componentes centrales

En `meta-oss-cookbook/agentic-fundamentals/` aparecen:

```text
agent_loop.py
response_parser.py
run_agent.py
```

El loop es deliberadamente pequeño.

```text
USER
 ↓
MODEL
 ↓
RAW TURN
 ↓
ATEM PARSER
 ↓
TOOL CALL ?
 ├─ NO → FINAL
 └─ YES
      ↓
   ToolRegistry.call
      ↓
   real tool result
      ↓
   append observation
      ↓
   MODEL AGAIN
```

---

## 3.2 MuseGlimmerAgent

El agente:

1. carga tokenizer/model;
2. aplica chat template;
3. incluye schemas de tools;
4. genera;
5. parsea canales;
6. ejecuta tool calls;
7. reinserta resultados como mensajes `tool`;
8. repite hasta final o `max_steps`.

### PUNTO RELEVANTE

**La autonomía básica no necesita un framework gigantesco.** La inteligencia emerge del ciclo observación-acción-observación.

---

## 3.3 ToolRegistry

Cada tool contiene:

```text
name
description
parameters / JSON schema
callable Python
```

El modelo recibe el schema y puede seleccionar la función.

### Riesgo

El reference loop ejecuta la función registrada. Por eso registrar una herramienta equivale a conceder capacidad.

### Sheriff recomendado

```text
ATEM CALL
   ↓
schema validate
   ↓
capability check
   ↓
policy
   ↓
resource limits
   ↓
execute
```

---

## 3.4 ATEM parser

El parser separa canales:

```text
to=self     reasoning
to=tool     function invocation
to=user     final response
```

También evita interpretar como tool call una invocación que sólo aparece citada dentro del contenido final/reasoning.

### PUNTO RELEVANTE

**Separar canal de razonamiento, canal de acción y canal de usuario reduce ambigüedad operacional.**

---

## 3.5 Self-correction

Cuando una herramienta falla, el resultado/error vuelve al modelo.

```text
tool error
   ↓
observation
   ↓
model sees failure
   ↓
new plan / corrected call
```

No requiere que un controlador externo codifique todas las estrategias de recuperación.

### Riesgo

Los errores crudos pueden filtrar paths o información interna. YAIWES debería usar un `ErrorSanitizer`.

---

## 3.6 Límites del reference agent

No implementa por sí solo:

- persistencia durable;
- claims;
- DAG;
- event sourcing;
- sandbox fuerte;
- autorización avanzada;
- idempotencia cross-process;
- multi-agent ownership.

Por tanto no reemplaza al Sheriff/Crazy Wall.

---

# 4. METACUA — agente autónomo de computer-use macOS

## 4.1 Qué es

`metacua` es descrito por Meta como un **terminal-first macOS computer-use agent**. Existe implementación Python y Swift.

Su función es permitir que un modelo vea y controle un Mac:

```text
SCREENSHOT
   ↓
VISION / REASON
   ↓
ACTION
   ├─ move cursor
   ├─ click
   ├─ type
   ├─ drag
   └─ keyboard
   ↓
SCREENSHOT AGAIN
   ↓
CORRECT / CONTINUE
```

---

## 4.2 Loop perceptual

El agente no trabaja sobre una representación ideal del escritorio. Observa screenshots reales y decide sobre píxeles.

Patrón:

```text
LOOK
 ↓
THINK
 ↓
ACT
 ↓
LOOK AGAIN
```

### PUNTO RELEVANTE

Este patrón es equivalente a un agente físico/GUI: **cada acción cambia el mundo y obliga a observar otra vez antes de continuar**.

---

## 4.3 Acceso real al sistema

La documentación advierte que `metacua` puede mover mouse, escribir, hacer clicks, abrir apps, cambiar settings y ejecutar lo que decida el agente.

Eso lo convierte en un agente con side effects de alto impacto.

### PUNTO RELEVANTE PARA YAIWES

No debe cablearse directamente al kernel sin:

```text
Sheriff
approval policy
workspace/scope restrictions
screen/action audit
kill switch
rate limits
```

---

## 4.4 Permisos macOS

Necesita capacidades del SO como Screen Recording/Accessibility para observar y actuar.

Esto demuestra otro principio importante:

**capacidad declarada por el agente ≠ capacidad concedida por el sistema operativo**.

El kernel debe comprobar ambas.

---

## 4.5 Implementaciones Python y Swift

La existencia de ambas versiones muestra que la lógica puede separarse del lenguaje de implementación. Para YAIWES importa el contrato conceptual:

```text
capture screen
normalize observation
model request
parse action
dispatch native event
capture again
```

---

# 5. GITHUB REPO AGENT — agente que vive dentro de GitHub Actions

## 5.1 Qué es

Meta publica una receta denominada **Production GitHub Repo Agent**. Puede ejecutarse como GitHub Action ante:

- issue;
- pull request;
- comentario/comando como `/oc`;
- revisión automática.

Usa Muse Spark mediante Meta Model API y un harness de coding.

---

## 5.2 Arquitectura

```text
GitHub event
    ↓
GitHub Actions
    ↓
checkout / context
    ↓
Repo Agent
    ↓
Muse Spark
    ↓
repo tools
    ↓
review / comment / code operation
```

---

## 5.3 Seguridad de PRs

La receta diferencia eventos que pueden provenir de forks. Usa `pull_request` en el flujo de review para que PRs externos reciban un token restringido y no accedan a secretos/write permissions.

### PUNTO RELEVANTE

**El origen del evento debe cambiar las capacidades concedidas al agente.**

Adaptación YAIWES:

```text
trusted internal event → capability profile A
external/untrusted PR  → capability profile B (read-only)
```

---

## 5.4 Integración con comandos

El agente puede activarse desde comentarios y recibir contexto GitHub. Esto es una interfaz muy útil para un enjambre:

```text
/agent fix issue 123
/agent review
/agent explain
```

Pero el backend debe mapear cada comando a una capability explícita.

---

# 6. COMPUTER-USE LINUX — OpenCode + Muse Spark + Cua + MCP

## 6.1 Qué es

Meta publica una receta donde un agente controla un escritorio Linux real dentro de un sandbox desechable.

Arquitectura:

```text
OpenCode
   ↓
Muse Spark
   ↓
MCP
   ↓
Cua bridge
   ↓
Docker desktop sandbox
   ↓
screenshot/click/type/shell
```

---

## 6.2 Look-act-look

El agente ejecuta:

```text
screenshot
 ↓
reason over pixels
 ↓
mouse/keyboard action
 ↓
screenshot
 ↓
update belief
```

La receta muestra que puede encontrar una aplicación, abrirla y jugar Minesweeper a partir de screenshots.

---

## 6.3 Aislamiento

A diferencia de MetaCua macOS, este agente opera un desktop dentro de Docker/Cua.

### PUNTO RELEVANTE

**El modelo nunca necesita acceso directo al host.** El sandbox se convierte en una frontera real.

Para YAIWES esto es preferible para tareas de GUI no confiables.

---

## 6.4 MCP como bus de capacidades

El bridge MCP expone tools como:

```text
screenshot
left_click
right_click
type_text
press_key
run_command
```

Esto encaja exactamente con la regla YAIWES de comunicación mediante MCP/API.

---

## 6.5 Delegación a subagentes

La receta documenta que, para no superar límites de imágenes, un orquestador delegó el tablero a subagentes cortos. Cada uno:

- toma nuevas capturas;
- ejecuta un número limitado de acciones;
- resume el estado en texto;
- termina;
- el orquestador lanza el siguiente.

### PUNTO RELEVANTE

Esto es un patrón muy valioso para YAIWES:

```text
long visual task
    ↓
segment into bounded child sessions
    ↓
child returns compact textual state
    ↓
next child continues
```

Reduce crecimiento de contexto y mantiene checkpoints naturales.

---

# 7. MULTI-AGENT PRODUCT STUDIO — coordinación de agentes especializados

Meta publica una receta de orquestación con cuatro perfiles Hermes:

```text
Product Manager
Backend Engineer
Frontend Engineer
Technical Writer
```

Coordinan mediante un Kanban compartido.

Arquitectura conceptual:

```text
              SHARED PROJECT STATE
                     │
      ┌──────────────┼──────────────┐
      │              │              │
     PM           Backend        Frontend
      │              │              │
      └────────── shared board ─────┤
                                    │
                              Tech Writer
```

### PUNTO RELEVANTE

**La coordinación se hace a través de estado externo compartido, no confiando en que cada agente recuerde lo que hicieron los demás.**

Esto es análogo a Crazy Wall.

---

# 8. PATRONES AGENTIC DEL META MODEL COOKBOOK

Además de agentes completos, Meta publica patrones reutilizables.

## 8.1 Basic agent loop

```text
plan
 ↓
action
 ↓
observation
 ↓
plan again
```

## 8.2 Tool calling

El agente convierte intención en una llamada estructurada y espera resultado real.

## 8.3 Self-correction

Los resultados de tools/tests vuelven al modelo para corregir la acción.

## 8.4 Validated in-place edits

La edición de código debe validarse y no tratarse como correcta sólo porque el patch fue escrito.

## 8.5 Browser-verified coding

Un coding agent modifica una web y usa navegador/Playwright MCP para comprobar visualmente su propio trabajo.

### PUNTO RELEVANTE

**Generar código y verificar código deben ser pasos diferentes.**

Para YAIWES:

```text
GENERATE
 ↓
EXECUTE
 ↓
TEST
 ↓
EXTERNAL VERIFY
 ↓
PASS
```

---

# 9. COMPARACIÓN DIRECTA

| Sistema | Función principal | Estado | Tools | Persistencia/recovery | Multi-agent | Sandbox |
|---|---|---|---|---|---|---|
| Muse Code | coding harness/runtime | Session/MSP | shell/code/tools | fuerte | sí | recetas de containment |
| Muse Glimmer Agent | reference autonomous tool loop | lista `messages` | ToolRegistry/ATEM | básica | no nativo en loop | depende del integrador |
| MetaCua | control GUI macOS | sesión local | screen/mouse/keyboard | local | no principal | host real, alto riesgo |
| GitHub Repo Agent | automatización de repo | GitHub event/run | GitHub + coding tools | GitHub Actions | configurable | permisos GitHub |
| Linux Computer Use | GUI agent sandboxed | OpenCode/task | Cua MCP | por sesión | sí, child tasks | Cua + Docker |
| Multi-Agent Product Studio | equipo especializado | Kanban compartido | por rol | shared state | sí | depende harness |

---

# 10. QUÉ COPIAR A YAIWES

## Prioridad A — copiar patrón casi directamente

### 1. Event-sourced state

```text
EventStore → StateFold → CurrentState
```

### 2. PendingCommandSet

No cerrar side effects hasta reconciliarlos.

### 3. `commandId` idempotente

Mismo comando lógico = misma identidad.

### 4. Cursor/revision

Un agente stale no debe ejecutar.

### 5. Gap recovery

Pausar y reconciliar antes de continuar.

### 6. Approval choices server/Sheriff-minted

El agente nunca crea permisos.

### 7. Parent/child lifecycle

Cada subagente debe tener ownership y resultado trazable.

---

# 11. QUÉ NO COPIAR CIEGAMENTE

1. **Muse Glimmer `ToolRegistry.call()` directamente en producción** — necesita Sheriff antes del side effect.
2. **MetaCua sobre host real sin sandbox/approval** — demasiado poder operativo.
3. **Dependencia exclusiva del cliente SDK para durability** — YAIWES necesita autoridad durable propia.
4. **Errores crudos de tools** — sanitizar antes de devolver al modelo.
5. **Estado guardado sólo en contexto LLM** — no es fuente autoritativa.

---

# 12. ARQUITECTURA YAIWES RECOMENDADA DESPUÉS DE ESTA INVESTIGACIÓN

```text
                           YAIWES CORE
                               │
        ┌──────────────────────┼───────────────────────┐
        │                      │                       │
    EventStore            CommandStore             ClaimStore
        │                      │                       │
        └────────────┬─────────┴─────────┬─────────────┘
                     │                   │
                 StateFold           SHERIFF
                     │                   │
                     └─────────┬─────────┘
                               │
                           ORCHESTRATOR
                               │
                ┌──────────────┼──────────────┐
                │              │              │
          coding agent     visual agent    verifier
                │              │              │
                └──────────────┼──────────────┘
                               │
                           MCP / API
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                    │
     GitHub/VPS          Cua/Sandbox          filesystem/tools
```

Loop:

```text
READ CURSOR
   ↓
FOLD EVENTS
   ↓
SELECT NODE
   ↓
CLAIM
   ↓
SHERIFF
   ↓
EXECUTE VIA MCP/API
   ↓
APPEND RESULT EVENT
   ↓
VERIFY EVIDENCE
   ↓
PASS?
 ├─ NO → repair/retry same logical command
 └─ YES → complete + next node
```

---

# 13. Estado de instalación en `Core kernel Yaiwes/`

Confirmado en `main`:

```text
Core kernel Yaiwes/
├── Meta-Muse-Code-SDK-2026/
│   ├── code/
│   ├── _archives/
│   └── DOWNLOAD_EXTRACT_MANIFEST.json
│
├── Meta-Muse-Glimmer-Agent-2026/
│   ├── code/
│   ├── _archives/
│   └── DOWNLOAD_EXTRACT_MANIFEST.json
│
├── Meta-Agent-Cookbook-2026/
│   ├── code/
│   ├── _archives/
│   └── DOWNLOAD_EXTRACT_MANIFEST.json
│
└── META-AGENTS-2026-MUSE-CODE-GLIMMER.md
```

El workflow `Meta 2026 agents download + extract` terminó con conclusión `success`.

---

# 14. Conclusiones finales

## Muse Code

La enseñanza principal es **runtime reliability**: sesiones, pending commands, idempotencia, cursor/recovery, approvals y subagentes.

## Muse Glimmer Agent

La enseñanza principal es **simplicidad del loop agentic**: modelo → parser → tool → observación → autocorrección.

## MetaCua

La enseñanza principal es **perception/action feedback** y el enorme riesgo de dar control directo del host.

## GitHub Repo Agent

La enseñanza principal es **usar el contexto de seguridad del evento** para decidir permisos y ejecutar el agente dentro de CI/CD.

## Linux Computer Use

La enseñanza principal es **MCP + sandbox + screenshots** como frontera segura entre modelo y máquina.

## Multi-Agent Product Studio

La enseñanza principal es **estado externo compartido y roles especializados** para evitar enjambres sin coordinación.

---

# 15. Los 10 puntos más importantes para YAIWES

1. **Estado autoritativo fuera del LLM.**
2. **Cada side effect con `commandId`.**
3. **Retry idempotente, no duplicación.**
4. **Cursor/revision antes de CLAIM.**
5. **Gap = pausa y reconciliación.**
6. **UNKNOWN nunca se convierte automáticamente en PASS.**
7. **Approvals creadas por Sheriff/runtime, no por el agente.**
8. **Subagentes con parent/child ownership trazable.**
9. **Herramientas poderosas detrás de MCP/API + sandbox.**
10. **Generación y verificación deben ser fases diferentes.**

Estas diez reglas son la síntesis más útil de la arquitectura pública de Meta para fortalecer `Core kernel Yaiwes` sin sobreingeniería.
