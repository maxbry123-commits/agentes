Sí. El problema se resuelve no intentando meter los 20–100 GB dentro de la ventana de contexto, sino haciendo que el agente funcione como una memoria externa jerárquica de la LLM.


ff

SALIDA 3 — INTEGRACIÓN FINAL DEL WORKFLOW + MEMORY/AUDIT ORCHESTRATOR
Esta salida cierra las dos anteriores: define qué debe programarse en el Workflow, qué debe programarse en el Memory/Audit Orchestrator, el contrato entre ambos, el ciclo completo y las reglas que deben quedar congeladas antes de escribir código.

FRONTERA DEFINITIVA
WORKFLOW
Pregunta:
¿Qué debemos hacer?
Controla:
¿Qué hacemos ahora?
MEMORY/AUDIT
Pregunta:
¿Qué información necesitamos?
Controla:
¿Qué información recuperamos, conservamos y validamos?
SANDBOX
Controla:
¿Dónde ejecutamos esta unidad y con qué estado?
LLM
Hace:
Razonar y procesar la unidad asignada.
CONSOLIDATOR
Hace:
Integrar las piezas.
AUDITOR
Hace:
Comprobar si las piezas son confiables y completas.
CHECKPOINT
Hace:
Permitir continuar, recuperar o retroceder.
63. PRINCIPIO FINAL
LLM
= COGNITIVE PROCESSOR

WORKFLOW
= EXECUTION CONTROL

MEMORY ORCHESTRATOR
= EXTERNAL COGNITIVE MEMORY

AUDITOR
= VERIFICATION

SANDBOX
= ISOLATED WORKSPACE

CHECKPOINT
= RECOVERY

CONSOLIDATOR
= GLOBAL INTEGRATION

ROUTER
= RESOURCE SELECTION

POLICY
= AUTHORITY

STATE MACHINE
= DETERMINISTIC TRANSITIONS
Y la regla raíz:
THE MODEL THINKS.
THE RUNTIME CONTROLS.
THE MEMORY REMEMBERS.
THE RETRIEVER FINDS.
THE AUDITOR QUESTIONS.
THE CONSOLIDATOR CONNECTS.
THE CHECKPOINT RECOVERS.
THE POLICY AUTHORIZES.
THE JUDGE VALIDATES.
64. ORDEN DE PROGRAMACIÓN
No recomiendo comenzar programando la interfaz.
El orden correcto para construir el sistema sería:
01. CORE STATE MODEL
02. EVENT MODEL
03. TASK MODEL
04. TASK CONTRACT
05. STATE MACHINE
06. CHECKPOINT ENGINE
07. POLICY ENGINE
08. MEMORY CONTRACT
09. RETRIEVAL CONTRACT
10. CONTEXT FABRIC
11. SANDBOX CONTRACT
12. WORKER CONTRACT
13. OUTPUT SCHEMA
14. AUDIT ENGINE
15. CONSOLIDATOR
16. ROUTER
17. CONTINUOUS LOOP
18. RECOVERY
19. RESOURCE BRAIN
20. GLOBAL INTEGRATION
21. FIVE-PASS BUILD AUDITOR
22. API
23. UI
La UI debe ser la última capa, porque el comportamiento real debe existir independientemente de la interfaz.
65. CRITERIO DE ÉXITO DEL SISTEMA
El sistema estará realmente terminado cuando una LLM pequeña pueda recibir:
20 MILLONES DE CONTEXTO TOTAL
sin recibir los 20M simultáneamente y pueda:
LEER
 ↓
SEGMENTAR
 ↓
INVESTIGAR
 ↓
RAZONAR
 ↓
RESOLVER
 ↓
GUARDAR
 ↓
CONSOLIDAR
 ↓
RECUPERAR
 ↓
CONTINUAR
 ↓
INTEGRAR
 ↓
AUDITAR
 ↓
REPARAR
 ↓
FINALIZAR
sin perder:
objetivo;
instrucciones originales;
decisiones;
evidencia;
dependencias;
resultados anteriores;
estado;
trazabilidad.
Y, sobre todo:
una solución parcial no se considera automáticamente una solución global.
La integración global, cobertura y validación son fases obligatorias.

### Resultado de las 3 salidas

Con esto quedan separadas las tres capas que no conviene mezclar:

**Workflow/Runtime**
→ transforma el problema en trabajo ejecutable.

**Memory/Audit Orchestrator**
→ transforma almacenamiento masivo en contexto relevante, verificable y recuperable.

**Sandbox + LLM**
→ ejecuta unidades cognitivas aisladas y devuelve cambios candidatos.

Y el **Consolidator** es el puente que evita precisamente el problema que señalaste: que el modelo sea capaz de resolver 100 fragmentos individualmente pero sea incapaz de construir correctamente **el proyecto completo**.



# SALIDA 3
## BLOQUE 3/3 — CONTRATO WORKFLOW ↔ MEMORY/AUDIT

# 45. INTERFAZ CONCEPTUAL

WORKFLOW
    │
    │ GET_CONTEXT
    ▼
MEMORY/AUDIT
    │
    ├── RETRIEVE
    ├── RERANK
    ├── AUDIT
    ├── RELATE
    └── BUILD_CONTEXT
    │
    ▼
CONTEXT PACK
    │
    ▼
WORKFLOW
    │
    ▼
SANDBOX
    │
    ▼
LLM
    │
    ▼
STATE DELTA
    │
    ▼
MEMORY/AUDIT
    │
    ├── VALIDATE
    ├── STORE
    ├── AUDIT
    └── CONSOLIDATE
    │
    ▼
WORKFLOW

---

# 46. OPERACIONES PRINCIPALES

El Workflow debe poder solicitar:

GET_CONTEXT
GET_MEMORY
GET_EVIDENCE
GET_STATE
GET_HISTORY
GET_ARTIFACT
GET_RELATIONS
AUDIT_MEMORY

Y enviar:

SAVE_STATE_DELTA
SAVE_ARTIFACT
SAVE_CLAIM
SAVE_EVIDENCE
SAVE_CONSOLIDATION
CREATE_CHECKPOINT

---

# 47. REGLA DE ESCRITURA

La LLM no escribe directamente en memoria canónica.

Siempre:

LLM
 ↓
OUTPUT
 ↓
NORMALIZER
 ↓
SCHEMA VALIDATION
 ↓
AUDIT
 ↓
STATE DELTA
 ↓
MEMORY UPDATE

Esto evita que una alucinación se convierta inmediatamente en memoria permanente.

---

# 48. REGLA DE LECTURA

La LLM tampoco decide libremente qué memoria utilizar.

El Runtime solicita:

CONTEXT FOR TASK X

Memory Orchestrator construye:

CONTEXT PACK

La LLM procesa:

CONTEXT PACK

---

# 49. CONTINUOUS COGNITIVE LOOP

El ciclo completo queda:

MASTER INPUT
 ↓
QUESTION ENGINE
 ↓
GOALS
 ↓
REQUIREMENTS
 ↓
PLAN
 ↓
TASK DAG
 ↓
TASK FUNNEL
 ↓
TASK CONTRACT
 ↓
MEMORY RETRIEVAL
 ↓
CONTEXT FABRIC
 ↓
SANDBOX
 ↓
LLM
 ↓
OUTPUT
 ↓
SCHEMA VALIDATION
 ↓
AUDIT
 ↓
STATE DELTA
 ↓
CONSOLIDATION
 ↓
MEMORY UPDATE
 ↓
CHECKPOINT
 ↓
COVERAGE CHECK
 ↓
NEXT TASK
 ↓
REPEAT

---

# 50. EL SISTEMA DEBE PODER CONTINUAR SIN NUEVO INPUT HUMANO

Si:

- existen tareas;
- existe autorización;
- existe contexto;
- existe progreso;
- no existe conflicto crítico;

entonces:

CONTINUE LOOP

No esperar:

USER → NUEVO PROMPT

para cada subtarea.

---

# 51. AUTO-PREGUNTAS

Durante la ejecución pueden generarse:

- preguntas de investigación;
- preguntas de validación;
- preguntas de integración;
- preguntas de contradicción;
- preguntas de dependencia.

Estas preguntas se convierten en tareas.

Ejemplo:

TASK A
 ↓
QUESTION Q1
 ↓
RESEARCH TASK R1
 ↓
ANSWER
 ↓
UPDATE TASK A

---

# 52. AUTO-RESEARCH

Cuando falta conocimiento:

UNKNOWN
 ↓
RESEARCH TASK
 ↓
RESOURCE ROUTER
 ↓
WORKER
 ↓
EVIDENCE
 ↓
AUDIT
 ↓
MEMORY
 ↓
ORIGINAL TASK

El sistema no debe inventar para llenar el vacío.

---

# 53. CONSOLIDACIÓN EN EMBUDO

El sistema debe consolidar progresivamente:

WORK UNIT
 ↓
TASK RESULT
 ↓
TASK CONSOLIDATION
 ↓
PHASE CONSOLIDATION
 ↓
PROJECT CONSOLIDATION
 ↓
FINAL CONSOLIDATION

Esto evita el problema:

"cada segmento funciona, pero nadie puede unirlos."

---

# 54. INTEGRATION CHECK

Antes de considerar terminado un proyecto:

Cada:

REQUIREMENT

debe apuntar a:

TASK
 ↓
ARTIFACT
 ↓
EVIDENCE
 ↓
VALIDATION

Si existe:

REQUIREMENT
 ↓
NO IMPLEMENTATION

entonces:

INCOMPLETE

---

# 55. CROSS-CHECK

Debe existir una comprobación bidireccional:

TOP-DOWN:

GOALS
 ↓
REQUIREMENTS
 ↓
TASKS
 ↓
ARTIFACTS

BOTTOM-UP:

ARTIFACTS
 ↓
TASKS
 ↓
REQUIREMENTS
 ↓
GOALS

Después comparar ambos.

---

# 56. FINAL JUDGE

El Judge debe decidir:

PASS
FAIL
REPAIR
ESCALATE
HUMAN_REQUIRED

No debe aceptar:

"la LLM dice que terminó".

Debe comprobar el estado objetivo.

---

# 57. FINAL AUDIT

Antes de producir la salida final:

AUDIT 1
→ REQUIREMENTS

AUDIT 2
→ EVIDENCE

AUDIT 3
→ CONTRADICTIONS

AUDIT 4
→ COVERAGE

AUDIT 5
→ TRACEABILITY

Después:

GLOBAL CONSOLIDATION

y finalmente:

FINAL OUTPUT

---

# 58. REGLA CONTRA ALUCINACIÓN

La arquitectura no debe intentar resolver alucinaciones solamente mediante prompts.

Debe reducirlas estructuralmente:

SOURCE
+
EVIDENCE
+
RETRIEVAL
+
SCHEMA
+
STATE
+
AUDIT
+
CROSS-CHECK
+
TRACEABILITY

La LLM puede equivocarse.

El sistema debe detectar el error antes de convertirlo en estado canónico.

---

# 59. REGLA CONTRA PÉRDIDA DE CONTEXTO

No intentar conservar todo dentro de la ventana.

Conservar externamente:

MASTER INPUT
+
MEMORY
+
STATE
+
ARTIFACTS
+
EVIDENCE
+
CONSOLIDATION
+
CHECKPOINTS
+
HISTORY

Y recuperar dinámicamente:

RELEVANT CONTEXT

---

# 60. REGLA CONTRA FRAGMENTACIÓN

La solución al problema:

"cada segmento funciona pero el proyecto completo falla"

es:

LOCAL RESULTS
 ↓
LOCAL CONSOLIDATION
 ↓
GLOBAL STATE
 ↓
INTEGRATION MAP
 ↓
GLOBAL CONSOLIDATION
 ↓
CROSS-CHECK
 ↓
FINAL VALIDATION

No basta con guardar resúmenes.

Debe existir una estructura global de relaciones.

---

# 61. ARQUITECTURA FINAL

                    USER
                     │
                     ▼
                MASTER INPUT
                     │
                     ▼
            ┌─────────────────┐
            │    WORKFLOW     │
            │                 │
            │ Goals           │
            │ Requirements    │
            │ Planner         │
            │ Task DAG        │
            │ Task Funnel     │
            │ Runtime         │
            │ Policy          │
            │ Router          │
            └────────┬────────┘
                     │
                     ▼
            MEMORY REQUEST
                     │
                     ▼
       ┌──────────────────────────┐
       │ MEMORY/AUDIT ORCHESTRATOR│
       │                          │
       │ Memory                   │
       │ Retrieval                │
       │ Tags                     │
       │ Graph                    │
       │ Evidence                │
       │ Audit                    │
       │ Context Fabric           │
       │ Resource Brain            │
       │ History                  │
       └────────────┬─────────────┘
                    │
                    ▼
              CONTEXT PACK
                    │
                    ▼
                 SANDBOX
                    │
                    ▼
                   LLM
                    │
                    ▼
              STATE DELTA
                    │
                    ▼
          AUDIT + VALIDATION
                    │
                    ▼
              CONSOLIDATOR
                    │
              ┌─────┴─────┐
              ▼           ▼
           MEMORY      CHECKPOINT
              │           │
              └─────┬─────┘
                    ▼
               NEXT TASK
                    │
                    ▼
                 LOOP

# SALIDA 3
## BLOQUE 2/3 — MEMORY/AUDIT ORCHESTRATOR

# 24. RESPONSABILIDAD

El Memory/Audit Orchestrator administra el conocimiento externo necesario para que una LLM limitada pueda trabajar sobre proyectos mucho mayores que su ventana.

Debe administrar:

RAW DATA
MEMORY
EVIDENCE
INDEXES
TAGS
GRAPH
ARTIFACTS
HISTORY
CONSOLIDATIONS
CHECKPOINT REFERENCES
AUDIT

---

# 25. NO ES UNA BASE DE DATOS SIMPLE

Debe funcionar como:

MEMORY FABRIC
+
RETRIEVAL ENGINE
+
EVIDENCE GRAPH
+
CONTEXT FABRIC
+
AUDIT ENGINE

---

# 26. MEMORY LAYERS

L0 — RAW SOURCE

Fuente original.

L1 — WORKING MEMORY

Información de la ventana actual.

L2 — TASK MEMORY

Información de la tarea.

L3 — PROJECT MEMORY

Estado global del proyecto.

L4 — LONG-TERM KNOWLEDGE

Información reutilizable.

---

# 27. RAW SOURCE

Nunca eliminar la fuente original debido a una síntesis.

Debe poder recuperarse:

SOURCE
VERSION
HASH
LOCATION
PROVENANCE

---

# 28. CHUNKING

El sistema debe dividir información considerando:

- semántica;
- estructura;
- sección;
- entidad;
- dependencia;
- código;
- función;
- clase;
- requisito.

No solamente tamaño.

---

# 29. TAGGING

Cada objeto puede tener:

PROJECT
TOPIC
TASK
GOAL
REQUIREMENT
ENTITY
SOURCE
EVIDENCE
STATUS
PRIORITY
VERSION
DEPENDENCY

Y relaciones:

SUPPORTS
CONTRADICTS
DEPENDS_ON
DERIVED_FROM
IMPLEMENTS
VALIDATES
SUPERSEDES
RELATED_TO

---

# 30. RETRIEVAL

Debe existir Retrieval híbrido:

LEXICAL
+
SEMANTIC
+
TAG
+
GRAPH
+
ENTITY
+
TEMPORAL
+
TASK
+
EVIDENCE
+
HISTORY

Después:

RETRIEVE
 ↓
RERANK
 ↓
FILTER
 ↓
CONTEXT PACK

---

# 31. CONTEXT FABRIC

No debe devolver documentos indiscriminadamente.

Debe construir:

MINIMAL SUFFICIENT CONTEXT

Debe contener solamente lo necesario para ejecutar la unidad actual.

---

# 32. CONTEXT BUDGET

Debe conocer:

MODEL LIMIT
SYSTEM TOKENS
TASK TOKENS
OUTPUT RESERVE
PINNED TOKENS
MEMORY BUDGET
SAFETY MARGIN

Y nunca superar el límite.

---

# 33. MEMORY COMPACTION

Cuando la información crece:

WINDOW
 ↓
EXTRACT
 ↓
VALIDATE
 ↓
CONSOLIDATE
 ↓
STORE
 ↓
INDEX

La fuente original permanece.

La síntesis es una capa derivada.

---

# 34. CONSOLIDATION

Debe existir:

LOCAL CONSOLIDATION

y:

GLOBAL CONSOLIDATION

La consolidación global debe integrar:

facts
decisions
evidence
requirements
artifacts
dependencies
contradictions
task state

No solamente texto resumido.

---

# 35. CLAIM SYSTEM

Cada afirmación relevante debe poder tener:

CLAIM
SOURCE
EVIDENCE
CONFIDENCE
STATUS
PROVENANCE

Estados:

UNVERIFIED
SUPPORTED
CONFLICTED
VALIDATED
REJECTED
SUPERSEDED

---

# 36. EVIDENCE GRAPH

Debe representar:

CLAIM
 ↓
SOURCE
 ↓
EVIDENCE

y:

CLAIM
 ↓
SUPPORTS
 ↓
REQUIREMENT

o:

CLAIM A
 ↓
CONTRADICTS
 ↓
CLAIM B

---

# 37. MEMORY AUDIT

Debe ejecutarse continuamente.

Debe detectar:

- duplicados;
- contradicciones;
- información obsoleta;
- claims sin evidencia;
- referencias rotas;
- memoria huérfana;
- estados inconsistentes;
- artefactos sin procedencia.

---

# 38. MEMORY VERSIONING

Cada cambio importante debe producir una nueva versión.

No sobrescribir silenciosamente.

Debe poder reconstruirse:

VERSION N
 ↓
VERSION N+1
 ↓
VERSION N+2

---

# 39. HISTORY

Debe conservar eventos:

INPUT_RECEIVED
DOCUMENT_INGESTED
MEMORY_CREATED
MEMORY_UPDATED
RETRIEVAL_EXECUTED
CLAIM_CREATED
AUDIT_EXECUTED
CONFLICT_FOUND
CONSOLIDATION_CREATED
CHECKPOINT_CREATED
ROLLBACK_EXECUTED

---

# 40. TRACEABILITY

Cada elemento crítico debe responder:

¿De dónde salió?

¿Quién lo produjo?

¿Con qué versión?

¿En qué tarea?

¿Con qué evidencia?

¿En qué checkpoint?

¿Fue validado?

---

# 41. RESOURCE BRAIN

El Orchestrator debe mantener un catálogo de recursos:

MODELS
APIS
TOOLS
DATASETS
INDEXES
SKILLS
WORKERS
SANDBOXES
SERVICES

Estados:

DISCOVERED
REGISTERED
CONFIGURED
REACHABLE
HEALTHY
AUTHORIZED
AVAILABLE
DEGRADED
UNAVAILABLE

---

# 42. RESOURCE ROUTING

El Router puede consultar:

CAPABILITY
HEALTH
AUTHORIZATION
CONTEXT LIMIT
LATENCY
COST
SPECIALIZATION
POLICY

Pero la decisión final de ejecución pertenece al Runtime.

---

# 43. MEMORY RESPONSE

El resultado de Memory Orchestrator no debe ser una respuesta conversacional.

Debe ser:

CONTEXT PACK

con:

- relevant memory;
- evidence;
- relations;
- current state;
- consolidation;
- open questions;
- provenance;
- confidence;
- context budget.

---

# 44. REGLA FUNDAMENTAL

MEMORY ORCHESTRATOR

NO decide:

- objetivo;
- política global;
- estrategia final;
- finalización;
- autorización.

Entrega información estructurada al Runtime.


# SALIDA 3 — WORKFLOW + MEMORY/AUDIT ORCHESTRATOR
## BLOQUE 1/3 — WORKFLOW

# 1. RESPONSABILIDAD DEL WORKFLOW

El Workflow es el cerebro determinista de ejecución.

No almacena todo el conocimiento del proyecto.

No razona por sí mismo.

No sustituye a la LLM.

Su función es convertir:

MASTER INPUT
    ↓
GOALS
    ↓
REQUIREMENTS
    ↓
PLAN
    ↓
TASK GRAPH
    ↓
EXECUTION
    ↓
VALIDATION
    ↓
CONSOLIDATION
    ↓
FINAL OUTPUT

Debe controlar todo el ciclo.

---

# 2. MASTER INPUT

El Master Input original debe ser:

- inmutable;
- versionado;
- trazable;
- siempre recuperable.

Debe conservarse literalmente.

No debe ser resumido como sustituto del original.

El sistema puede crear derivados, pero nunca reemplazar:

MASTER INPUT ORIGINAL

---

# 3. QUESTION ENGINE

Antes de ejecutar una tarea compleja debe existir una fase de interrogación estructurada.

El sistema debe generar preguntas para descubrir:

- qué se quiere conseguir;
- cuál es el objetivo;
- qué restricciones existen;
- qué información falta;
- qué debe investigarse;
- qué dependencias existen;
- qué riesgos existen;
- qué resultado se considera correcto;
- qué puede bloquear la ejecución.

Las preguntas no deben ser solamente preguntas para el usuario.

Deben ser también preguntas internas de planificación.

---

# 4. GOAL ENGINE

Las preguntas producen:

- objetivos;
- subobjetivos;
- criterios de éxito;
- criterios de fracaso.

Debe existir:

GOAL TREE

Ejemplo:

GOAL
 ├── GOAL A
 │    ├── TASK A1
 │    └── TASK A2
 │
 ├── GOAL B
 │    ├── TASK B1
 │    └── TASK B2
 │
 └── GOAL C

---

# 5. REQUIREMENT ENGINE

Cada objetivo debe convertirse en requisitos verificables.

Cada requirement necesita:

- ID;
- descripción;
- prioridad;
- origen;
- dependencia;
- criterio de cumplimiento;
- estado;
- tareas asociadas.

Estados:

DISCOVERED
PLANNED
IN_PROGRESS
SATISFIED
FAILED
BLOCKED
SUPERSEDED

---

# 6. PLAN ENGINE

El Planner no debe generar simplemente un texto de planificación.

Debe producir un objeto estructurado:

PLAN

que contenga:

- goals;
- requirements;
- phases;
- tasks;
- dependencies;
- resources;
- validation;
- checkpoints;
- recovery;
- expected artifacts.

---

# 7. TASK DAG

La tarea debe representarse como DAG cuando sea posible.

TASK A
 ├── TASK B
 ├── TASK C
 │     └── TASK E
 └── TASK D

TASK E no puede comenzar hasta que las dependencias requeridas estén satisfechas.

Pero el DAG debe poder modificarse.

Nueva información puede producir:

NEW REQUIREMENT
    ↓
NEW TASK
    ↓
NEW DEPENDENCY
    ↓
UPDATED DAG

---

# 8. TASK CONTRACT

Cada tarea debe tener un contrato.

Debe definir:

- input;
- contexto requerido;
- objetivo;
- restricciones;
- herramientas;
- worker;
- output schema;
- validadores;
- criterio de éxito;
- retry;
- timeout;
- escalamiento.

La LLM recibe el contrato.

No decide el contrato.

---

# 9. TASK FUNNEL

El Workflow debe convertir una tarea grande en unidades progresivamente pequeñas:

PROJECT
 ↓
PHASE
 ↓
GOAL
 ↓
TASK
 ↓
SUBTASK
 ↓
WORK UNIT
 ↓
LLM CALL

La unidad enviada a la LLM debe ser suficientemente pequeña para que pueda razonar correctamente.

---

# 10. CONTEXT REQUEST

Antes de cada Work Unit:

WORKFLOW
    ↓
REQUEST CONTEXT
    ↓
MEMORY ORCHESTRATOR
    ↓
CONTEXT PACK
    ↓
WORK UNIT

El Workflow indica:

- qué tarea está ejecutando;
- qué información necesita;
- qué objetivo persigue;
- qué evidencia necesita.

Memory Orchestrator recupera la información.

---

# 11. INPUT BLOCK

El Runtime construye un Input Block estructurado.

Debe contener:

MASTER INPUT
CURRENT GOAL
CURRENT TASK
TASK CONTRACT
RELEVANT CONTEXT
EVIDENCE
CURRENT STATE
CURRENT CONSOLIDATION
OPEN QUESTIONS
CONSTRAINTS
OUTPUT SCHEMA

La LLM recibe esto.

---

# 12. PINNED INPUT

Debe existir una sección de información que acompañe cada ventana.

PINNED:

- instrucciones críticas;
- objetivo principal;
- restricciones;
- requisitos críticos;
- decisiones importantes;
- políticas.

Esto evita que la segmentación destruya el enfoque.

---

# 13. CARRY FORWARD

Cada ventana debe producir:

CARRY_FORWARD_STATE

Debe contener:

- objetivo actual;
- tarea actual;
- hechos descubiertos;
- decisiones;
- errores;
- preguntas abiertas;
- dependencias;
- progreso;
- siguiente acción;
- consolidación actual.

El siguiente Input Block recibe este estado.

---

# 14. LLM OUTPUT

La salida no debe ser considerada automáticamente como verdad.

Debe pasar por:

LLM OUTPUT
 ↓
NORMALIZER
 ↓
SCHEMA VALIDATION
 ↓
AUDIT
 ↓
STATE DELTA
 ↓
CONSOLIDATION

---

# 15. STATE DELTA

La LLM propone cambios.

No modifica directamente el estado global.

Debe producir:

STATE DELTA

Ejemplo:

- fact_added;
- decision_added;
- task_completed;
- task_created;
- issue_detected;
- evidence_added;
- contradiction_detected.

El Runtime decide si aplica el delta.

---

# 16. CONTINUOUS EXECUTION LOOP

Mientras existan tareas ejecutables:

GET NEXT TASK
 ↓
GET CONTEXT
 ↓
CREATE SANDBOX
 ↓
EXECUTE
 ↓
VALIDATE
 ↓
UPDATE STATE
 ↓
CHECKPOINT
 ↓
CONSOLIDATE
 ↓
NEXT TASK

El sistema continúa automáticamente.

---

# 17. STOP CONDITIONS

Debe detenerse cuando:

- no existen tareas;
- existe conflicto crítico;
- falta autorización;
- existe violación de policy;
- no existe progreso;
- se alcanzan límites;
- existe fallo repetitivo;
- se necesita intervención humana.

No debe detenerse simplemente porque una LLM terminó una respuesta.

---

# 18. RETRY

Un retry no debe repetir ciegamente el mismo prompt.

Debe registrar:

ATTEMPT 1
 ↓
FAILURE ANALYSIS
 ↓
STRATEGY CHANGE
 ↓
ATTEMPT 2

Si continúa:

ATTEMPT 3
 ↓
ESCALATE

---

# 19. CHECKPOINT

Después de cada unidad significativa:

STATE
TASK STATE
MEMORY VERSION
ARTIFACTS
CONSOLIDATION
AUDIT
NEXT ACTION

→ CHECKPOINT

Esto permite continuar después de errores.

---

# 20. ROLLBACK

Si un estado es inválido:

CURRENT
 ↓
INVALID
 ↓
FIND LAST VALID CHECKPOINT
 ↓
ROLLBACK
 ↓
REPAIR / BRANCH
 ↓
CONTINUE

Nunca:

ERROR
 ↓
START FROM ZERO

---

# 21. BRANCHING

Si existen varias estrategias:

PLAN A
PLAN B
PLAN C

pueden ejecutarse aisladamente.

Después:

COMPARE
 ↓
AUDIT
 ↓
JUDGE
 ↓
SELECT VALIDATED BRANCH

---

# 22. CONVERGENCE

Cada ciclo debe medir:

- progreso;
- cobertura;
- errores;
- contradicciones;
- tareas pendientes;
- incertidumbre.

Si existe progreso:

CONTINUE

Si no existe progreso:

CHANGE STRATEGY

Si existe fallo persistente:

ESCALATE

---

# 23. FINALIZATION

La tarea no termina cuando existe una respuesta.

Debe pasar:

TASK COMPLETION
 ↓
COVERAGE AUDIT
 ↓
CONTRADICTION AUDIT
 ↓
REQUIREMENT AUDIT
 ↓
GLOBAL CONSOLIDATION
 ↓
FINAL VALIDATION
 ↓
FINAL OUTPUT


hhhSALIDA 2 — ORQUESTADOR AUDITOR DE MEMORIA

En esta salida voy a separar qué debe vivir dentro del Orquestador de Memoria/Auditor, qué debe quedar en el Workflow y cómo se conectan ambos, sin mezclar responsabilidades.

La regla central es:

> Workflow decide qué trabajo ejecutar. Memory/Audit Orchestrator decide qué información recuperar, cómo conservarla, cómo auditarla y qué contexto estructurado entregar al Workflow/Runtime.



1. Qué debe ser el Orquestador de Memoria/Auditor

No debe ser simplemente una base de datos con búsqueda.

Debe funcionar como una Memory & Evidence Fabric:

MEMORY/AUDIT ORCHESTRATOR
                              │
       ┌──────────────────────┼──────────────────────┐
       │                      │                      │
   INGESTION              MEMORY                  AUDIT
       │                      │                      │
   documentos             estado                claims
   mensajes               hechos                evidencia
   código                  decisiones            conflictos
   outputs                 artefactos             cobertura
   eventos                 historial              consistencia
       │                      │                      │
       └──────────────────────┼──────────────────────┘
                              │
                       CONTEXT FABRIC
                              │
                       CONTEXT PACK
                              │
                         WORKFLOW


---

2. Las 12 funciones principales

El Orquestador debe tener como mínimo:

01. INGESTION
02. NORMALIZATION
03. CHUNKING
04. INDEXING
05. TAGGING
06. RETRIEVAL
07. RERANKING
08. MEMORY STATE
09. EVIDENCE GRAPH
10. AUDIT
11. CONSOLIDATION
12. CONTEXT FABRICATION

Pero deben existir además mecanismos transversales:

VERSIONING
CHECKPOINTING
TRACEABILITY
PROVENANCE
DEDUPLICATION
CONFLICT MANAGEMENT
STALE-DATA DETECTION
ACCESS CONTROL
RESOURCE HEALTH
REPAIR


---

3. INGESTION

Todo material que entra debe convertirse en objetos manejables.

Ejemplos:

USER INPUT
DOCUMENT
PDF
MARKDOWN
CODE
CHAT
API RESPONSE
LLM OUTPUT
RESEARCH RESULT
ARTIFACT
EVENT
CHECKPOINT

Cada elemento recibe un identificador estable.

No debe depender exclusivamente del nombre del archivo.


---

4. NORMALIZATION

Antes de indexar:

RAW
 ↓
NORMALIZE
 ↓
IDENTIFY
 ↓
CLASSIFY
 ↓
VERSION
 ↓
INDEX

Debe conservarse siempre el original.

Nunca reemplazar silenciosamente la fuente original por una versión resumida.


---

5. CHUNKING INTELIGENTE

No utilizar solamente:

cada N tokens

El chunking debe considerar:

estructura
semántica
secciones
dependencias
entidades
código
funciones
clases
tablas
requisitos
relaciones

Un documento puede convertirse en:

DOCUMENT
 ├── SECTION
 │    ├── SUBSECTION
 │    │    ├── CLAIM
 │    │    ├── EVIDENCE
 │    │    └── RELATION
 │    └── ...
 └── ...

Esto permite recuperar unidades pequeñas sin perder su procedencia.


---

6. TAG ENGINE

El sistema que propusiste de Tags debe convertirse en un componente formal.

Cada objeto puede tener:

PROJECT
TASK
MODULE
ENTITY
TOPIC
REQUIREMENT
GOAL
EVIDENCE
STATUS
PRIORITY
VERSION
DATE
SOURCE
DEPENDENCY
CONFIDENCE

Pero además:

supports
contradicts
depends_on
derived_from
implements
validates
supersedes
related_to

Los Tags sirven para reducir brutalmente el espacio de búsqueda.


---

7. BÚSQUEDA MULTICAPA

No depender de un solo buscador.

El Retrieval Engine debe combinar:

LEXICAL SEARCH
+
SEMANTIC SEARCH
+
TAG SEARCH
+
ENTITY SEARCH
+
GRAPH SEARCH
+
TEMPORAL SEARCH
+
TASK SEARCH
+
EVIDENCE SEARCH
+
HISTORY SEARCH

Después:

CANDIDATES
 ↓
RERANK
 ↓
FILTER
 ↓
CONTEXT PACK

Esto es mucho más robusto que simplemente hacer RAG.


---

8. MEMORY STATE

La memoria debe distinguir diferentes tipos de información.

RAW
FACT
EVIDENCE
DECISION
INFERENCE
HYPOTHESIS
ASSUMPTION
REQUIREMENT
TASK
RESULT
UNKNOWN
CONFLICT
REJECTED
SUPERSEDED

Esto es crítico para reducir alucinaciones.

Por ejemplo:

"X funciona así"

no debería almacenarse automáticamente como:

FACT

Puede comenzar como:

CLAIM
STATUS = UNVERIFIED

Después el Auditor determina su estado.


---

9. EVIDENCE GRAPH

Cada afirmación importante debe poder apuntar hacia su origen.

CLAIM
  │
  ├── derived_from → SOURCE
  │
  ├── supported_by → EVIDENCE
  │
  ├── related_to → CLAIM
  │
  └── affects → TASK

Esto permite contestar:

> ¿De dónde salió esta conclusión?



sin depender de que la LLM lo recuerde.


---

10. AUDITOR DE MEMORIA

Debe realizar auditorías continuas.

No solamente al final.

Debe buscar:

DUPLICATES
CONTRADICTIONS
STALE INFORMATION
UNVERIFIED CLAIMS
ORPHAN MEMORY
BROKEN REFERENCES
INVALID RELATIONS
MISSING EVIDENCE
INCONSISTENT STATE

Y generar:

MEMORY_AUDIT_RESULT

con estados como:

VALID
UNVERIFIED
CONFLICT
STALE
ORPHAN
INVALID
REVIEW_REQUIRED


---

11. CONSOLIDACIÓN DE MEMORIA

Aquí está una diferencia importante.

Consolidar no significa resumir.

El sistema debe conservar:

SOURCE MATERIAL
      ↓
ATOMIC FACTS
      ↓
RELATIONS
      ↓
LOCAL CONSOLIDATION
      ↓
MODULE CONSOLIDATION
      ↓
GLOBAL CONSOLIDATION

La síntesis es una capa derivada.

Nunca debe destruir la fuente.


---

12. CONTEXT FABRIC

Esta es probablemente una de las partes más importantes del sistema.

El Memory Orchestrator no debería entregar simplemente:

top_k documents

Debe construir:

CONTEXT PACK

para la tarea concreta.

Ejemplo:

CURRENT TASK
+
TASK REQUIREMENTS
+
RELEVANT FACTS
+
RELEVANT EVIDENCE
+
RELEVANT DECISIONS
+
CURRENT STATE
+
CURRENT CONSOLIDATION
+
OPEN QUESTIONS
+
CONSTRAINTS
+
REQUIRED OUTPUT SCHEMA

El resultado debe respetar el límite de contexto de la LLM.


---

13. CONTEXT BUDGETER

Debe existir un componente que conozca:

MODEL_CONTEXT_LIMIT
RESERVED_OUTPUT
SYSTEM_CONTEXT
TASK_CONTEXT
MEMORY_CONTEXT
SAFETY_MARGIN

Y calcule:

AVAILABLE_CONTEXT

Por ejemplo conceptualmente:

TOTAL
-
SYSTEM
-
TASK
-
OUTPUT_RESERVE
-
SAFETY_MARGIN
=
MEMORY_BUDGET

La memoria no debe llenar arbitrariamente la ventana.


---

14. CONTEXT PRIORITY

Si no cabe todo:

P0 = instrucciones críticas
P1 = tarea actual
P2 = requisitos
P3 = estado actual
P4 = evidencia directa
P5 = decisiones
P6 = consolidación
P7 = contexto relacionado
P8 = información secundaria

El Context Fabric elimina o posterga P8 antes de sacrificar P0–P4.


---

15. MEMORY COMPACTION

Cuando una sesión se hace demasiado grande:

OLD WINDOW
 ↓
EXTRACT
 ↓
VALIDATE
 ↓
CONSOLIDATE
 ↓
STORE
 ↓
INDEX

Después la siguiente ventana recibe:

MASTER INPUT
+
CURRENT STATE
+
CONSOLIDATION
+
RELEVANT RETRIEVED MEMORY

No recibe necesariamente todo el historial.


---

16. EL "ARRASTRE" QUE PROPUSISTE

Debe formalizarse como:

CARRY FORWARD STATE

Cada ventana genera:

CARRY_FORWARD

que contiene únicamente:

CURRENT OBJECTIVE
CURRENT TASK
DECISIONS
FACTS
OPEN QUESTIONS
DEPENDENCIES
ERRORS
NEXT ACTION
CURRENT CONSOLIDATION

La siguiente ventana recibe ese estado.

Así se obtiene el efecto de:

> leer página → tomar notas → continuar → actualizar notas → leer siguiente página.



Pero de forma estructurada.


---

17. PUSH-PIN

También incorporaría tu concepto de "push/pin".

Debe existir:

PINNED_CONTEXT

Información que nunca debe desaparecer durante determinada tarea.

Por ejemplo:

MASTER REQUIREMENT
CRITICAL CONSTRAINT
USER INSTRUCTION
SAFETY POLICY
CURRENT GOAL
KEY DECISION

Mientras que:

EPHEMERAL_CONTEXT

puede ser sustituido.


---

18. MEMORY LAYERS

Propongo cinco niveles:

L0 — RAW
L1 — WORKING MEMORY
L2 — TASK MEMORY
L3 — PROJECT MEMORY
L4 — LONG-TERM KNOWLEDGE

L0 RAW

Fuente original.

L1 WORKING

Ventana actual.

L2 TASK

Información necesaria para completar la tarea.

L3 PROJECT

Estado global del proyecto.

L4 LONG-TERM

Conocimiento persistente reutilizable.


---

19. HISTORIAL

Todo cambio importante debe producir:

EVENT

Ejemplo:

TASK_CREATED
TASK_STARTED
MEMORY_RETRIEVED
LLM_EXECUTED
OUTPUT_RECEIVED
AUDIT_FAILED
REPAIR_CREATED
CHECKPOINT_CREATED
STATE_UPDATED
TASK_COMPLETED

Esto permite reconstruir lo sucedido.


---

20. CONEXIÓN CON CHECKPOINTS

El Memory Orchestrator no debe guardar únicamente archivos.

Debe relacionarse con:

CHECKPOINT
   │
   ├── STATE
   ├── MEMORY VERSION
   ├── TASK VERSION
   ├── ARTIFACT VERSION
   ├── CONSOLIDATION VERSION
   └── AUDIT VERSION

Entonces un rollback puede recuperar el estado cognitivo completo.


---

21. CONEXIÓN CON WORKFLOW

La interfaz conceptual debe ser:

WORKFLOW
   │
   │ request_context()
   ▼
MEMORY ORCHESTRATOR
   │
   ├── retrieve
   ├── rerank
   ├── audit
   ├── assemble
   └── validate
   │
   ▼
CONTEXT PACK
   │
   ▼
WORKFLOW
   │
   ▼
LLM
   │
   ▼
STATE DELTA
   │
   ▼
MEMORY ORCHESTRATOR

El ciclo se repite.


---

22. CONEXIÓN CON EL CONSOLIDATOR

Después de cada unidad:

LLM OUTPUT
 ↓
NORMALIZER
 ↓
AUDIT
 ↓
STATE DELTA
 ↓
CONSOLIDATOR
 ↓
MEMORY

El Consolidator no debe inventar información faltante.

Si dos resultados dicen:

A = X
A = Y

debe registrar:

CONFLICT

y crear una tarea de resolución.


---

23. CONEXIÓN CON SENTINEL / SHERIFF / JUDGE

SENTINEL

Observa.

detect anomaly

SHERIFF

Ejecuta control.

pause
retry
rollback
branch
block

JUDGE

Evalúa resultado.

PASS
FAIL
REPAIR
ESCALATE

El Memory Orchestrator conserva todas esas decisiones.


---

24. QUÉ NO DEBE HACER EL MEMORY ORCHESTRATOR

No debe:

decidir el objetivo global;
crear arbitrariamente tareas;
controlar el loop principal;
autorizar acciones peligrosas;
decidir qué modelo debe ganar;
modificar instrucciones del usuario;
convertir hipótesis en hechos;
borrar conflictos silenciosamente.

Eso pertenece al Runtime/Workflow/Policy/Audit según corresponda.


---

25. CONTRATO ENTRE AMBOS SISTEMAS

El Workflow debe poder solicitar:

GET_CONTEXT
GET_MEMORY
GET_EVIDENCE
GET_ARTIFACTS
GET_STATE
GET_HISTORY
GET_RELEVANT_RELATIONS
AUDIT_MEMORY
SAVE_STATE
SAVE_ARTIFACT
SAVE_CONSOLIDATION
CREATE_CHECKPOINT

El Memory Orchestrator debe responder con objetos estructurados, no con texto libre únicamente.


---

26. CICLO COMPLETO

USER
 ↓
MASTER INPUT
 ↓
WORKFLOW
 ↓
QUESTIONS
 ↓
GOALS
 ↓
PLAN
 ↓
TASK
 ↓
MEMORY REQUEST
 ↓
RETRIEVAL
 ↓
AUDIT MEMORY
 ↓
CONTEXT FABRIC
 ↓
SANDBOX
 ↓
LLM
 ↓
STATE DELTA
 ↓
AUDIT OUTPUT
 ↓
CONSOLIDATION
 ↓
MEMORY UPDATE
 ↓
CHECKPOINT
 ↓
NEXT TASK
 ↓
REPEAT


---

27. EL PRINCIPIO MÁS IMPORTANTE

El sistema debe conseguir que una LLM de:

120K

o:

250K

pueda trabajar sobre:

1M
5M
20M
100M+

sin convertir mágicamente su ventana en 100M.

La capacidad adicional proviene de:

EXTERNAL MEMORY
+
RETRIEVAL
+
TASK DECOMPOSITION
+
STATE
+
CHECKPOINTS
+
CONSOLIDATION
+
AUDIT
+
CONTEXT FABRICATION

La LLM nunca necesita "recordar" los 20M.

El Runtime y la Memory Fabric hacen que pueda acceder nuevamente a cualquier pieza cuando la necesita.


---

28. DIFERENCIA ENTRE "RECORDAR" Y "PODER PROCESAR"

Este es un principio que conviene congelar en la arquitectura:

MEMORY
≠
CONTEXT WINDOW

y:

CONTEXT WINDOW
≠
TOTAL COGNITIVE WORKSPACE

El Workspace total puede ser:

MEMORY
+
INDEX
+
GRAPH
+
ARTIFACTS
+
TASK STATE
+
CHECKPOINTS
+
CONTEXT PACK
+
CURRENT LLM WINDOW

La ventana de la LLM es solamente el área de procesamiento activo.


---

29. RESULTADO FINAL DEL ORQUESTADOR DE MEMORIA/AUDITOR

Debe convertirse en:

MEMORY
      +
RETRIEVAL
      +
EVIDENCE
      +
GRAPH
      +
AUDIT
      +
CONTEXT FABRIC
      +
STATE HISTORY
      +
CHECKPOINT REFERENCES
      +
TRACEABILITY

Y entregar al Workflow:

"ESTE ES EL CONTEXTO MÍNIMO,
RELEVANTE,
VERIFICADO,
TRAZABLE
Y SUFICIENTE
PARA EJECUTAR LA SIGUIENTE UNIDAD."

Ese es el punto donde tu idea deja de ser simplemente "darle memoria a una LLM pequeña" y pasa a convertirse en un sistema externo de memoria cognitiva + ejecución incremental + consolidación verificable.





# SALIDA 1 — CONSOLIDADO MAESTRO DE PROGRAMACIÓN
## BLOQUE 3/3 — WORKFLOW, MEMORY/AUDIT ORCHESTRATOR Y AUDITORÍA PRE-BUILD

# 34. WORKFLOW

El Workflow debe ser responsable de:

- recibir Master Input;
- generar preguntas;
- definir objetivos;
- definir requisitos;
- construir el plan;
- construir Task DAG;
- administrar Task Funnel;
- crear Task Contracts;
- seleccionar Work Units;
- preparar Context Packs;
- despachar tareas;
- seleccionar Workers;
- crear Sandboxes;
- controlar loops;
- crear checkpoints;
- ejecutar recuperación;
- ejecutar retries;
- crear branches;
- medir convergencia;
- escalar;
- solicitar consolidación;
- ejecutar validación final.

El Workflow NO debe convertirse en una memoria gigante.

Debe controlar la ejecución.

---

# 35. MEMORY/AUDIT ORCHESTRATOR

El Memory/Audit Orchestrator debe encargarse de:

INGESTION
HASH / IDEMPOTENCY
OCR
PERSISTENCE
DOCUMENT REGISTRY
VERSIONING
TAGS
SEARCH
HYBRID RETRIEVAL
GRAPH
EVIDENCE
CLAIMS
MEMORY CONSOLIDATION
MEMORY AUDIT
CONTEXT PREPARATION
MEMORY COMPACTION
HISTORY
CHECKPOINT STORAGE
RESOURCE REGISTRY
RESOURCE HEALTH
RESOURCE AUTHORIZATION
TRACEABILITY

Debe ser una infraestructura cognitiva.

No debe ser el dueño de toda la ejecución.

---

# 36. SEPARACIÓN ENTRE WORKFLOW Y MEMORY

MAXBRY ORCHESTRATOR
        │
        ├── WORKFLOW
        ├── TASK ENGINE
        ├── POLICY ENGINE
        ├── STATE MACHINE
        ├── ROUTER
        └── CONSOLIDATOR
                │
                ▼
       MEMORY/AUDIT ORCHESTRATOR
                │
        ├── MEMORY
        ├── RETRIEVAL
        ├── AUDIT
        ├── RESOURCE BRAIN
        ├── EVIDENCE
        ├── GRAPH
        └── CONTEXT FABRIC

El Workflow decide:

QUÉ HACER

El Memory Orchestrator decide:

QUÉ INFORMACIÓN RELEVANTE RECUPERAR

El Sandbox proporciona:

DÓNDE Y CON QUÉ ESTADO EJECUTAR

El Auditor determina:

SI EL RESULTADO ES VÁLIDO

El Consolidator determina:

CÓMO INTEGRAR LAS PIEZAS

---

# 37. RESOURCE BRAIN

Debe existir un registro de recursos/capacidades.

Puede descubrir:

- modelos;
- APIs;
- herramientas;
- memoria;
- índices;
- datasets;
- skills;
- agentes;
- OCR;
- analizadores;
- sandboxes;
- proveedores.

Estados:

DISCOVERED
REGISTERED
CONFIGURED
REACHABLE
HEALTHY
AUTHORIZED
AVAILABLE
DEGRADED
UNAVAILABLE

Regla:

REGISTERED ≠ AVAILABLE

AVAILABLE ≠ AUTHORIZED

Un recurso no puede utilizarse solamente porque fue descubierto.

---

# 38. RESOURCE ROUTING

El Router debe considerar:

- capacidad;
- salud;
- autorización;
- coste;
- latencia;
- contexto;
- especialización;
- prioridad;
- disponibilidad;
- política.

Debe poder seleccionar:

- modelo;
- API;
- Worker;
- herramienta;
- memoria;
- sandbox.

La LLM no debe seleccionar unilateralmente el recurso que controla el proceso.

---

# 39. MEMORY COMO CONTEXT FACTORY

El Memory Orchestrator no solamente almacena.

Debe poder:

CAPTURE
 ↓
STORE
 ↓
INDEX
 ↓
TAG
 ↓
SEARCH
 ↓
RETRIEVE
 ↓
RERANK
 ↓
RELATE
 ↓
CONSOLIDATE
 ↓
VERSION
 ↓
AUDIT
 ↓
PREPARE CONTEXT

Su producto principal para el Runtime es:

CONTEXT PACK

---

# 40. RETRIEVAL HÍBRIDO

La recuperación puede combinar:

- búsqueda semántica;
- búsqueda léxica;
- BM25;
- tags;
- grafo;
- historial;
- relaciones;
- evidencia;
- recencia;
- relevancia.

La recuperación debe ser selectiva.

No devolver todo.

Debe construir:

RELEVANT CONTEXT PACK

---

# 41. TAGS Y ETIQUETAS

Cada fragmento puede recibir:

- tags semánticos;
- tags de tarea;
- tags de proyecto;
- tags de entidad;
- tags temporales;
- tags de prioridad;
- tags de evidencia;
- tags de estado;
- tags de dependencia.

Los tags no sustituyen el índice.

Funcionan como otra dimensión de recuperación.

---

# 42. MEMORY AUDIT

El Auditor de Memoria debe detectar:

- duplicados;
- información contradictoria;
- claims sin evidencia;
- información obsoleta;
- referencias rotas;
- relaciones inconsistentes;
- memoria huérfana;
- estados incompatibles;
- artefactos sin procedencia.

Debe poder marcar:

VALID
UNVERIFIED
CONFLICT
STALE
ORPHAN
INVALID
REQUIRES_REVIEW

---

# 43. TRACEABILITY

Para cualquier artefacto o recurso importante debe existir:

- origen;
- repositorio;
- versión;
- commit;
- ruta;
- hash;
- tamaño;
- licencia;
- dependencias;
- fecha;
- estado de verificación.

Si no puede verificarse:

SOURCE_NOT_RESOLVED

No inventar procedencia.

---

# 44. PRINCIPIOS DE ARQUITECTURA QUE DEBEN CONGELARSE

P01 — MODEL ≠ AGENT

P02 — CONTEXT ≠ MEMORY

P03 — MEMORY ≠ SUMMARY

P04 — TASK ≠ PROMPT

P05 — OUTPUT ≠ FINAL

P06 — FAILURE ≠ RESET

P07 — CHECKPOINT ≠ SIMPLE SNAPSHOT

P08 — WORKER ≠ GLOBAL STATE

P09 — RETRIEVAL ≠ MEMORY

P10 — REGISTERED ≠ AUTHORIZED

P11 — LOOP ≠ INFINITE LOOP

P12 — LLM ≠ CONTROLLER

---

# 45. REGLA MAESTRA

La LLM procesa unidades cognitivas pequeñas.

El sistema externo:

- conserva;
- relaciona;
- verifica;
- versiona;
- recupera;
- consolida;
- controla;
- repara.

Esto permite que una LLM pequeña procese proyectos mucho mayores que su ventana de contexto sin obligarla a cargar todo simultáneamente.

---

# 46. DEFINICIÓN DE FRONTERAS

MAXBRY ORCHESTRATOR
│
├── DETERMINISTIC RUNTIME
├── WORKFLOW
├── TASK ENGINE
├── POLICY
├── STATE MACHINE
├── ROUTER
└── CONSOLIDATOR
          │
          ▼
MEMORY/AUDIT ORCHESTRATOR
│
├── MEMORY FABRIC
├── CONTEXT FABRIC
├── RETRIEVAL
├── GRAPH
├── EVIDENCE
├── AUDIT
├── RESOURCE BRAIN
└── CHECKPOINT STORAGE
          │
          ▼
SANDBOXES
          │
     ┌────┼────┐
     ▼    ▼    ▼
   LLM-A LLM-B LLM-C

FRONTERA RAÍZ:

LA LLM NUNCA DECIDE EL FLUJO DE EJECUCIÓN.

---

# 47. JSON — PROTOCOLO DE AUDITORÍA 5 PASADAS ANTES DE PROGRAMAR

{
  "document_audit_protocol": {
    "name": "FIVE_PASS_PREBUILD_AUDIT",
    "mandatory": true,

    "purpose": "Auditar todo el material disponible antes de construir para impedir que requisitos, mecanismos, restricciones, decisiones, dependencias o ideas relevantes sean descartados.",

    "passes": [

      {
        "pass": 1,
        "name": "EXTRACTION",
        "objective": "Extraer toda la información sin descartar ni evaluar prematuramente.",
        "must_capture": [
          "requirements",
          "mechanisms",
          "components",
          "constraints",
          "decisions",
          "dependencies",
          "open_questions",
          "proposals"
        ]
      },

      {
        "pass": 2,
        "name": "CLASSIFICATION",
        "objective": "Clasificar cada elemento según su naturaleza y estado.",
        "categories": [
          "fact",
          "requirement",
          "decision",
          "proposal",
          "hypothesis",
          "evidence",
          "dependency",
          "conflict",
          "unknown",
          "constraint"
        ]
      },

      {
        "pass": 3,
        "name": "CROSS_REFERENCE",
        "objective": "Comparar todas las fuentes y localizar relaciones, duplicados, contradicciones y conceptos equivalentes.",
        "must_detect": [
          "duplicates",
          "contradictions",
          "dependencies",
          "merged_concepts",
          "missing_links"
        ]
      },

      {
        "pass": 4,
        "name": "ARCHITECTURAL_MAPPING",
        "objective": "Asignar cada requisito y mecanismo al componente responsable.",
        "components": [
          "workflow",
          "runtime",
          "memory_orchestrator",
          "audit",
          "sandbox",
          "router",
          "consolidator",
          "policy_engine",
          "state_machine",
          "llm"
        ],
        "must_define": [
          "ownership",
          "interfaces",
          "data_flow",
          "state_flow"
        ]
      },

      {
        "pass": 5,
        "name": "PREBUILD_GAP_AUDIT",
        "objective": "Comparar nuevamente la arquitectura consolidada contra todas las fuentes originales antes de permitir programación.",
        "must_generate": [
          "coverage_matrix",
          "missing_requirements",
          "unresolved_conflicts",
          "implementation_dependencies",
          "final_build_checklist"
        ]
      }
    ],

    "hard_rules": [
      "No descartar información durante la extracción.",
      "No eliminar contradicciones; registrarlas.",
      "No convertir hipótesis en hechos.",
      "No convertir propuestas en requisitos sin decisión.",
      "No fusionar conceptos ambiguos sin trazabilidad.",
      "Cada requisito debe tener propietario.",
      "Cada componente debe tener responsabilidad definida.",
      "Cada requisito debe tener trazabilidad hacia su fuente.",
      "Toda decisión debe conservar procedencia y versión.",
      "Ningún requisito crítico puede desaparecer durante la consolidación."
    ],

    "build_gate": {
      "required": true,
      "block_build_if": [
        "audit_incomplete",
        "critical_requirement_missing",
        "critical_conflict_unresolved",
        "component_ownership_missing",
        "workflow_boundary_missing",
        "memory_boundary_missing",
        "state_machine_missing",
        "validation_rules_missing",
        "checkpoint_strategy_missing",
        "recovery_strategy_missing"
      ],
      "failure_action": "BLOCK_BUILD"
    }
  }
}

---

# 48. CRITERIO FINAL PARA COMENZAR PROGRAMACIÓN

NO comenzar programación simplemente porque exista una arquitectura aparentemente completa.

Primero debe existir:

FIVE-PASS AUDIT
+
COVERAGE MATRIX
+
COMPONENT OWNERSHIP
+
WORKFLOW BOUNDARIES
+
MEMORY BOUNDARIES
+
STATE MACHINE
+
POLICY
+
CHECKPOINTS
+
RECOVERY
+
VALIDATION
+
AUDIT
+
CONSOLIDATION

Después:

BUILD.

---

# 49. RESULTADO DE LA SALIDA 1

La arquitectura consolidada queda resumida así:

LLM
= razonamiento

WORKFLOW
= planificación y ejecución

RUNTIME
= control determinista

MEMORY ORCHESTRATOR
= memoria + recuperación + contexto

SANDBOX
= aislamiento + persistencia

CHECKPOINT ENGINE
= recuperación

TASK ENGINE
= descomposición

ROUTER
= selección de recursos

CONSOLIDATOR
= integración

AUDITOR
= verificación

SENTINEL
= detección

SHERIFF
= intervención

JUDGE
= decisión de validación

POLICY
= reglas

STATE MACHINE
= transiciones

RESOURCE BRAIN
= capacidades y recursos

La regla raíz:

LA LLM PROCESA.
EL SISTEMA CONTROLA.


# SALIDA 1 — CONSOLIDADO MAESTRO DE PROGRAMACIÓN
## BLOQUE 2/3 — SANDBOX, ESTADO, CHECKPOINTS, AUDITORÍA Y CONSOLIDACIÓN

# 13. SANDBOX

Cada unidad de trabajo debe ejecutarse dentro de un Sandbox aislado.

El Sandbox debe mantener:

- policy;
- permisos;
- estado;
- memoria;
- cache;
- event log;
- checkpoints;
- branches;
- artifacts;
- evidence;
- checklist;
- audit;
- consolidation.

El Sandbox debe ser:

- aislado;
- persistente;
- versionado;
- recuperable;
- auditable;
- reanudable.

---

# 14. MEMORIA VS CACHE

MEMORIA:

- persistente;
- recuperable;
- versionada;
- parte del conocimiento del trabajo.

CACHE:

- temporal;
- optimización;
- puede purgarse;
- nunca debe ser la única fuente de verdad.

No se deben mezclar.

---

# 15. CHECKPOINTS

Un checkpoint debe conservar:

- estado;
- versión del plan;
- versión de memoria;
- estado de tareas;
- versiones de artefactos;
- evidencia;
- decisiones;
- checklist;
- validación;
- siguiente acción;
- relaciones relevantes.

Ejemplo conceptual:

CP-041 ✓
CP-042 ✓
CP-043 ✗

Ante un fallo:

CP-043
 ↓
detectar estado inválido
 ↓
rollback a CP-042
 ↓
repair / fork
 ↓
nuevo checkpoint
 ↓
continuar

Un error no debe obligar a comenzar desde cero.

---

# 16. VERSIONADO

Debe existir versionado independiente para:

- estado;
- tareas;
- plan;
- memoria;
- artefactos;
- evidencia;
- consolidación;
- configuración;
- policy.

El sistema debe poder reconstruir:

qué ocurrió;
qué cambió;
qué versión estaba activa;
qué decisión produjo el cambio;
qué evidencia justificaba el cambio.

---

# 17. BRANCHING

El sistema debe permitir varias estrategias simultáneas.

PLAN V1
 ├── SANDBOX A
 ├── SANDBOX B
 └── SANDBOX C

Cada sandbox puede utilizar:

- modelo diferente;
- API diferente;
- estrategia diferente;
- herramientas diferentes;
- contexto diferente.

Después:

A → PASS
B → PASS
C → FAIL

El sistema conserva las ramas.

Solo una rama validada puede convertirse en estado canónico.

---

# 18. TASK FUNNEL

El Workflow debe implementar:

MASTER REQUEST
 ↓
QUESTIONS
 ↓
GOALS
 ↓
REQUIREMENTS
 ↓
TASKS
 ↓
SUBTASKS
 ↓
WORK UNITS
 ↓
SANDBOX
 ↓
ARTIFACT
 ↓
VERIFICATION
 ↓
CONSOLIDATION
 ↓
GLOBAL TASKS
 ↓
FINAL

Pero también debe permitir:

DISCOVERY
 ↓
NEW REQUIREMENT
 ↓
NEW TASK
 ↓
TASK FUNNEL

Por tanto el DAG puede evolucionar durante la ejecución.

---

# 19. CONTINUOUS LOOP

El sistema puede continuar automáticamente mientras:

- existan tareas autorizadas;
- no exista conflicto crítico;
- no exista duda bloqueante;
- exista progreso;
- las políticas lo permitan;
- los recursos estén disponibles;
- la validación continúe siendo satisfactoria.

Debe detenerse o escalar cuando:

- exista conflicto crítico;
- falte autorización;
- exista ambigüedad crítica;
- se viole una policy;
- no exista progreso;
- se repita el mismo error;
- se alcance un límite;
- se requiera intervención humana.

LOOP CONTINUO ≠ LOOP INFINITO.

---

# 20. CONVERGENCE ENGINE

Cada ciclo debe medir:

- progreso;
- cobertura;
- errores;
- incertidumbre;
- contradicciones;
- tareas pendientes.

Si:

progreso ↑
errores ↓
cobertura ↑
incertidumbre ↓

→ CONTINUAR

Si:

progreso ≈ 0
mismo error repetido
contradicciones ↑

→ CAMBIAR ESTRATEGIA

Si continúa fallando:

→ ESCALATE

---

# 21. SENTINEL

Debe detectar:

- desviación del objetivo;
- pérdida de enfoque;
- policy violation;
- output inválido;
- loops;
- falta de evidencia;
- scope drift;
- tareas estancadas.

No decide por la LLM.

Supervisa el proceso.

---

# 22. SHERIFF

Puede ejecutar acciones de control:

- bloquear;
- pausar;
- rechazar;
- reintentar;
- rollback;
- crear branch;
- cambiar estrategia;
- escalar.

Debe actuar mediante reglas deterministas.

---

# 23. JUDGE

Debe evaluar:

PASS
FAIL
REPAIR
ESCALATE
HUMAN_REQUIRED

El Judge no debe aceptar una salida simplemente porque la LLM declare:

"tarea completada".

Debe comprobar criterios objetivos.

---

# 24. WATCHDOG

Debe vigilar:

- tiempo;
- loops;
- repetición;
- consumo;
- retries;
- falta de progreso;
- workers bloqueados;
- sandboxes congelados.

Debe impedir que el sistema quede ejecutándose indefinidamente sin producir avance.

---

# 25. AUDITOR

El Auditor debe comprobar:

- cobertura;
- requisitos;
- evidencia;
- contradicciones;
- dependencias;
- consistencia;
- omisiones;
- trazabilidad;
- cumplimiento del plan.

---

# 26. CROSS-EXAMINATION

La auditoría puede dividirse en perspectivas independientes:

AUDITOR A → OMISIONES
AUDITOR B → CONTRADICCIONES
AUDITOR C → EVIDENCIA
AUDITOR D → REQUISITOS
AUDITOR E → DEPENDENCIAS
AUDITOR F → SCOPE

Después:

AUDIT RESULTS
 ↓
CONSOLIDATOR
 ↓
REPAIR TASKS

---

# 27. COVERAGE MATRIX

Cada requisito debe poder relacionarse con:

REQUIREMENT
 ↓
TASK
 ↓
ARTIFACT
 ↓
EVIDENCE
 ↓
VALIDATION

Si falta una conexión:

REQUIREMENT
 ↓
NO ARTIFACT

entonces:

MISSING COVERAGE

El sistema debe crear una tarea de reparación.

---

# 28. BOTTOM-UP + TOP-DOWN

BOTTOM-UP:

SOURCE
 ↓
SEGMENTS
 ↓
MODULES
 ↓
SYSTEM

TOP-DOWN:

GOAL
 ↓
REQUIREMENTS
 ↓
EXPECTED MODULES
 ↓
EXPECTED SYSTEM

Después:

TOP-DOWN
    ↕
BOTTOM-UP

Esto permite detectar:

- requisitos faltantes;
- módulos faltantes;
- inconsistencias;
- piezas que no contribuyen al objetivo.

---

# 29. SÍNTESIS JERÁRQUICA

No esperar hasta tener cientos de documentos.

Ejemplo:

10 segmentos
 ↓
SYNTHESIS A

10 segmentos
 ↓
SYNTHESIS B

SYNTHESIS A + B
 ↓
MODULE

MODULE A + MODULE B
 ↓
SYSTEM

SYSTEM
 ↓
GLOBAL SYNTHESIS

La síntesis debe ser incremental y versionada.

---

# 30. CONSOLIDATOR

El Consolidator debe integrar:

- artefactos;
- facts;
- evidence;
- decisiones;
- requisitos;
- dependencias;
- tareas;
- resultados;
- contradicciones;
- validaciones.

Debe producir:

GLOBAL STATE
GLOBAL CONSOLIDATION
INTEGRATION MAP
COVERAGE STATE
OPEN ISSUES
NEXT TASKS

No debe limitarse a producir un resumen textual.

---

# 31. GLOBAL INTEGRATION STATE

Debe representar las relaciones entre las piezas:

A
 ↓ depends_on
B

B
 ↓ supports
C

C
 ↓ contradicts
D

D
 ↓ affects
TASK-18

TASK-18
 ↓ satisfies
REQUIREMENT-07

El sistema conserva estas relaciones externamente.

La LLM no necesita recordar todas simultáneamente.

---

# 32. REGLAS DE VALIDACIÓN

NO VALIDATION
→ NO STATE UPDATE

NO EVIDENCE
→ CLAIM ≠ VERIFIED FACT

PENDING CRITICAL TASK
→ NOT COMPLETE

UNRESOLVED CRITICAL CONTRADICTION
→ NOT COMPLETE

INVALID SCHEMA
→ REJECT OUTPUT

POLICY VIOLATION
→ BLOCK

NO CHECKPOINT
→ NO LONG-RUNNING CONTINUATION

---

# 33. MULTI-API / MULTI-MODEL

Las múltiples APIs deben funcionar como Workers especializados.

Ejemplos:

WORKER A → investigación
WORKER B → análisis
WORKER C → implementación
WORKER D → contradicciones
WORKER E → verificación
WORKER F → síntesis

Cada Worker debe utilizar:

- contrato común;
- schema común;
- política común;
- estado local;
- memoria local;
- checkpoint local.

Después:

WORKERS
 ↓
NORMALIZER
 ↓
CONSOLIDATOR

Nunca fusionar directamente outputs incompatibles.

ggg# SALIDA 1 — CONSOLIDADO MAESTRO DE PROGRAMACIÓN
## BLOQUE 1/3 — ARQUITECTURA, CONTEXTO, MEMORIA Y EJECUCIÓN

## 1. DEFINICIÓN DEL SISTEMA

El sistema no debe considerarse simplemente un agente con memoria.

Debe implementarse como un:

CONTINUOUS COGNITIVE EXECUTION ENGINE (CCEE)

Runtime determinista de ejecución cognitiva capaz de permitir que una LLM con contexto limitado procese proyectos que exceden ampliamente su ventana mediante:

- segmentación;
- recuperación selectiva;
- tareas persistentes;
- memoria externa;
- sandboxes aislados;
- procesamiento por ventanas;
- memoria de trabajo;
- consolidación incremental;
- consolidación global;
- ejecución paralela;
- validación;
- checkpoints;
- rollback;
- branching;
- reparación;
- escalamiento;
- loop continuo.

PRINCIPIO FUNDAMENTAL:

La LLM no controla el sistema.

La LLM es el procesador cognitivo.

El Agent Runtime controla la ejecución.

---

# 2. SEPARACIÓN DE RESPONSABILIDADES

## LLM

Responsable de:

- interpretar;
- razonar;
- analizar;
- clasificar;
- comparar;
- generar resultados;
- proponer conclusiones;
- proponer acciones.

## AGENT RUNTIME

Responsable de:

- ejecutar;
- programar;
- enrutar;
- recuperar;
- administrar estado;
- administrar tareas;
- crear contextos;
- crear checkpoints;
- recuperar estados;
- controlar loops;
- ejecutar retries;
- crear branches;
- administrar sandboxes;
- consolidar;
- finalizar.

## MEMORY ORCHESTRATOR

Responsable de:

- persistencia;
- indexación;
- búsqueda;
- recuperación;
- tags;
- relaciones;
- grafo;
- evidencia;
- historial;
- memoria;
- preparación de contexto;
- compactación;
- auditoría de memoria.

## POLICY ENGINE

Responsable de:

- permisos;
- restricciones;
- reglas;
- autorización;
- bloqueo;
- escalamiento.

## AUDITOR

Responsable de:

- cobertura;
- contradicciones;
- evidencia;
- cumplimiento;
- omisiones;
- consistencia;
- desviaciones.

## CONSOLIDATOR

Responsable de:

- unir resultados parciales;
- relacionar artefactos;
- resolver dependencias;
- construir estado global;
- mantener coherencia entre segmentos.

## CHECKPOINT ENGINE

Responsable de:

- persistir estados;
- versionar;
- recuperar;
- rollback;
- branching;
- replay.

---

# 3. ARQUITECTURA PRINCIPAL

MASTER INPUT
    ↓
DETERMINISTIC CORE
    ↓
QUESTION ENGINE
    ↓
GOALS
    ↓
REQUIREMENTS
    ↓
PLAN
    ↓
TASK DAG
    ↓
TASK FUNNEL
    ↓
TASK DISPATCHER
    ↓
SANDBOXES
    ↓
LLM WORKERS
    ↓
STRUCTURED OUTPUT
    ↓
NORMALIZER
    ↓
ARTIFACT REGISTRY
    ↓
LOCAL CONSOLIDATION
    ↓
GLOBAL CONSOLIDATION
    ↓
AUDIT
    ↓
SENTINEL / SHERIFF / JUDGE
    ↓
VALIDATION
    ↓
PASS / REPAIR / ESCALATE
    ↓
CHECKPOINT
    ↓
NEXT WINDOW
    ↓
CONTINUOUS LOOP
    ↓
FINAL VALIDATION
    ↓
FINAL OUTPUT

---

# 4. CONTEXTO DE 20 MILLONES

Nunca se debe intentar:

20M CONTEXT → LLM

Debe hacerse:

20M
 ↓
INGESTION
 ↓
SEGMENTATION
 ↓
INDEXING
 ↓
TAGS
 ↓
GRAPH
 ↓
ARTIFACTS
 ↓
TASK ROUTING
 ↓
RETRIEVAL
 ↓
CONTEXT PACK
 ↓
LLM
 ↓
STATE DELTA
 ↓
CONSOLIDATION

La LLM solo recibe la información necesaria para la unidad cognitiva actual.

---

# 5. CONTEXT FABRIC

Debe existir una fábrica de contexto que construya dinámicamente el contexto que recibe cada ventana.

Debe combinar:

- Master Input;
- objetivo actual;
- tarea actual;
- requisitos;
- contexto relevante;
- evidencia;
- decisiones;
- estado actual;
- consolidación anterior;
- preguntas abiertas;
- restricciones;
- schema de salida;
- información recuperada mediante búsqueda.

La fábrica de contexto debe evitar introducir información irrelevante solamente para aumentar el contexto.

---

# 6. INPUT BLOCK

Cada llamada a la LLM debe recibir un Input Block generado por el Runtime.

Debe contener:

MASTER INPUT
CURRENT GOAL
CURRENT TASK
TASK CONTRACT
RELEVANT CONTEXT
RELEVANT EVIDENCE
CURRENT STATE
CURRENT CONSOLIDATION
OPEN QUESTIONS
POLICY
OUTPUT SCHEMA

El MASTER INPUT original debe ser inmutable.

La LLM no puede modificarlo.

---

# 7. TASK CONTRACT

Cada tarea debe definir:

- identificador;
- objetivo;
- propósito;
- entradas;
- contexto permitido;
- evidencia requerida;
- restricciones;
- herramientas permitidas;
- criterio de éxito;
- criterio de fallo;
- schema esperado;
- dependencia;
- prioridad;
- timeout;
- política de retry;
- política de escalamiento.

La tarea no debe depender de un prompt gigante.

---

# 8. STATE DELTA

La LLM no debe reescribir todo el estado global.

Debe devolver únicamente cambios candidatos:

- nuevos hechos;
- nuevas decisiones;
- preguntas resueltas;
- nuevas preguntas;
- nuevas dependencias;
- nuevas contradicciones;
- tareas completadas;
- artefactos creados;
- recomendaciones.

El Runtime determina:

OLD STATE
+
VALIDATED STATE DELTA
=
NEW STATE

La LLM propone.

El Runtime valida y aplica.

---

# 9. BOLA DE NIEVE CONTROLADA

Cada ventana debe producir:

PROCESS
 ↓
VALIDATE
 ↓
STATE DELTA
 ↓
UPDATE STATE
 ↓
CONSOLIDATION

La siguiente ventana recibe:

MASTER INPUT
+
CURRENT TASK
+
CURRENT CONSOLIDATION
+
RELEVANT ARTIFACTS
+
RELEVANT EVIDENCE
+
OPEN QUESTIONS
+
NEXT ACTION

No necesita cargar todo el proyecto.

---

# 10. CONSOLIDACIÓN LOCAL Y GLOBAL

Cada sandbox debe producir:

LOCAL CONSOLIDATION

Después:

LOCAL CONSOLIDATION A
LOCAL CONSOLIDATION B
LOCAL CONSOLIDATION C
LOCAL CONSOLIDATION D
        ↓
GLOBAL CONSOLIDATOR
        ↓
GLOBAL CONSOLIDATION

La consolidación debe ser incremental.

No esperar a que todo el proyecto esté terminado.

---

# 11. CLASIFICACIÓN DE INFORMACIÓN

Toda afirmación importante debe poder clasificarse como:

FACT
EVIDENCE
OBSERVATION
INFERENCE
HYPOTHESIS
DECISION
REQUIREMENT
ASSUMPTION
UNKNOWN
CONTRADICTION
REJECTED
INVALIDATED

Regla:

INFERENCE ≠ FACT

hasta que exista evidencia y validación suficiente.

---

# 12. PRINCIPIO DE CONTROL

La regla raíz del sistema es:

LA LLM NUNCA CONTROLA EL SISTEMA QUE CONTROLA A LA LLM.

El Runtime controla:

- loop;
- contexto;
- memoria;
- tareas;
- estado;
- recuperación;
- herramientas;
- routing;
- policy;
- checkpoints;
- validación;
- finalización.

La LLM procesa únicamente la unidad cognitiva que el Runtime le asigna.

La idea fundamental sería:

LLM pequeña = razonador
Agente = memoria + recuperación + compresión + navegación + control

Arquitectura

┌──────────────────────┐
                    │      LLM pequeña     │
                    │  120k / 250k tokens  │
                    │                      │
                    │   RAZONA / DECIDE    │
                    └──────────┬───────────┘
                               │
                    contexto de trabajo
                               │
                    ┌──────────▼───────────┐
                    │       AGENTE        │
                    │ Context Manager      │
                    │ Memory Manager       │
                    │ Retrieval            │
                    │ Summarizer           │
                    │ Planner              │
                    │ State Manager        │
                    └───────┬───────┬──────┘
                            │       │
             ┌──────────────┘       └──────────────┐
             ▼                                     ▼
      Memoria inmediata                      Memoria externa
       120k–250k                              20–100 GB
             │                                     │
       ┌─────▼─────┐                    ┌──────────▼─────────┐
       │ Working   │                    │ documentos         │
       │ Context   │                    │ código             │
       │           │                    │ conversaciones     │
       │ estado    │                    │ datos              │
       │ actual    │                    │ embeddings         │
       └───────────┘                    │ índices            │
                                        └────────────────────┘

La clave es que el contexto no es una sola cosa.

1. Divide la información en niveles

Yo utilizaría al menos 5 niveles:

Nivel	Contenido	Tamaño

L0	Contexto actual	pequeño
L1	Memoria de trabajo	decenas de miles de tokens
L2	Resúmenes jerárquicos	cientos de miles/millones
L3	Memoria episódica/semántica	GB
L4	Archivo bruto	20–100 GB


La LLM normalmente trabaja únicamente con L0 + L1.

Cuando necesita algo que no está ahí, el agente recupera información de L2–L4.


---

2. No dividiría simplemente en chunks

Aquí está una diferencia importante.

El método ingenuo sería:

100 GB
 ↓
chunks de 8K
 ↓
buscar chunks
 ↓
LLM

Eso funciona, pero pierde contexto global.

Yo haría chunking jerárquico:

PROYECTO
   │
   ├── Módulo A
   │      ├── archivo 1
   │      │     ├── chunk 1
   │      │     ├── chunk 2
   │      │     └── chunk 3
   │      └── archivo 2
   │
   ├── Módulo B
   │
   └── Módulo C

Y además:

chunk
 ↓
resumen del chunk
 ↓
resumen del archivo
 ↓
resumen del módulo
 ↓
resumen del proyecto

Así puedes preguntarle a la LLM:

> "¿Qué está ocurriendo en el módulo de autenticación?"



sin cargar todos los archivos.


---

3. La información importante tiene que tener un índice

El agente mantiene algo parecido a:

ID
├── ubicación
├── tipo
├── tema
├── entidades
├── relaciones
├── resumen
├── embedding
├── dependencias
├── timestamp
├── versión
└── prioridad

Por ejemplo:

MEM-82917

tipo: código
proyecto: YAIWES
módulo: router
archivo: engine_router.py
función: route_model()

resumen:
"Selecciona el backend de inferencia..."

depende_de:
  - provider_registry
  - capability_bus

relacionado_con:
  - model_selector
  - fallback_manager

La LLM no necesita saber dónde está físicamente la información.

El agente sí.


---

4. El agente funciona como un "sistema operativo de memoria"

Esta es probablemente la forma más útil de verlo.

La LLM dice:

NECESITO:
información sobre cómo funciona
el fallback del router.

El agente interpreta la necesidad.

Hace:

QUERY
 ↓
índice semántico
 ↓
índice estructural
 ↓
metadata
 ↓
dependencias
 ↓
recuperación

Encuentra:

router.py
fallback.py
provider_registry.py
config.yaml
tests/test_fallback.py

Y no entrega todo.

Primero entrega:

Resumen:
El router intenta Provider A.
Si falla:
    → Provider B
    → Provider C
    → local model

Archivos relevantes:
...

La LLM decide:

> Necesito ver fallback.py.



Entonces el agente carga solamente esa parte.


---

5. Aquí aparece algo todavía más importante: "contexto virtual"

Puedes hacer que la LLM tenga la sensación de que dispone de muchísimo más contexto del que realmente cabe en su ventana.

Por ejemplo:

CONTEXTO VIRTUAL
────────────────────────

Proyecto: YAIWES

Estado:
  tarea actual = implementar router

Objetivos:
  G1...
  G2...
  G3...

Decisiones previas:
  D1...
  D2...

Archivos relevantes:
  router.py
  fallback.py

Memorias relevantes:
  M183
  M927
  M1821

Información recuperada:
  [actual]

Información disponible bajo demanda:
  [20 GB]

La LLM solamente ve una vista materializada del universo de información.


---

6. Para 100 GB utilizaría recuperación en varias etapas

No haría:

100 GB → embedding search → LLM

Haría:

100 GB
   ↓
Filtro estructural
   ↓
filtro temporal
   ↓
filtro por proyecto
   ↓
filtro por entidad
   ↓
búsqueda semántica
   ↓
reranking
   ↓
resúmenes
   ↓
chunks originales
   ↓
LLM

Por ejemplo, si la pregunta es:

> "¿Dónde se implementa el sistema de recuperación?"



El agente podría reducir:

100 GB
 ↓
12 GB relacionados con YAIWES
 ↓
800 MB relacionados con memoria
 ↓
40 MB relacionados con retrieval
 ↓
2 MB candidatos
 ↓
300 KB relevantes
 ↓
50 KB enviados a la LLM

La LLM nunca ve los 100 GB.


---

7. Pero hay un problema: mantener coherencia global

Este es el problema realmente difícil.

Supongamos:

Archivo A dice:

timeout = 30 segundos

pero:

Archivo B dice:

timeout = 60 segundos

Si simplemente recuperas chunks, la LLM puede equivocarse.

Por eso necesitas una memoria de estado canónico.

Algo como:

FACTS

router.timeout
    value: 60
    source: config.yaml
    confidence: 0.98
    version: 17

router.fallback
    A → B → C
    source: fallback.py
    version: 21

El agente mantiene estas estructuras actualizadas.


---

8. Y agregaría "eventos" para conservar continuidad

En lugar de guardar solamente conversaciones, guardaría eventos:

EVENT 001
Usuario decidió usar Xata.

EVENT 002
Se descartó Qdrant.

EVENT 003
Router debe ser único.

EVENT 004
HF ↔ HF directo está prohibido.

EVENT 005
Se aprobó arquitectura X.

Entonces el agente puede reconstruir:

estado actual
       ↑
eventos
       ↑
decisiones
       ↑
historial

Esto es muchísimo más fiable que intentar conservar una conversación gigantesca.


---

9. Incluso puedes hacer "compresión progresiva"

Supongamos una conversación de 10 millones de tokens.

No conservas todo en el contexto.

Haces:

10M tokens
    ↓
100 episodios
    ↓
100 resúmenes
    ↓
20 temas
    ↓
5 decisiones principales
    ↓
estado actual

Pero no eliminas el original.

Lo mandas a memoria externa.

Por eso:

COMPRIMIDO = navegación rápida
ORIGINAL   = fuente de verdad

Esta distinción es fundamental.


---

10. La LLM puede pedir memoria iterativamente

En lugar de una sola llamada:

memoria → LLM → respuesta

el agente puede hacer:

LLM
 ↓
"Necesito X"
 ↓
AGENTE
 ↓
recupera X
 ↓
LLM
 ↓
"Ahora necesito Y"
 ↓
AGENTE
 ↓
recupera Y
 ↓
LLM
 ↓
razona
 ↓
"Necesito comprobar Z"
 ↓
AGENTE
 ↓
Z
 ↓
LLM
 ↓
respuesta

Eso convierte a la LLM en un razonador con memoria externa navegable.


---

11. Y hay una técnica todavía más potente

Separaría:

Memoria

¿Qué sé?

Estado

¿En qué punto estoy?

Objetivos

¿Qué estoy intentando conseguir?

Evidencia

¿Por qué creo esto?

Plan

¿Qué debo hacer después?

Contexto

¿Qué necesito mostrarle a la LLM ahora?

Esto evita el error típico de utilizar una única base vectorial como si fuera "memoria".


---

12. Para tu escenario concreto

Con una LLM de 120k–250k tokens y un agente con 20–100 GB, yo diseñaría:

SMALL LLM
                    │
              ┌─────▼─────┐
              │ Controller│
              └─────┬─────┘
                    │
       ┌────────────┼────────────┐
       ▼            ▼            ▼
   Context       Memory        State
   Manager       Manager       Manager
       │            │            │
       └────────────┼────────────┘
                    │
             Retrieval Engine
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
     Vector       Graph       Keyword
      Index       Index        Index
        │           │           │
        └───────────┼───────────┘
                    ▼
              Reranker
                    │
             Context Builder
                    │
                    ▼
              120k–250k
                    │
                    ▼
                   LLM

La regla sería:

Nunca preguntes "¿cómo meto 100 GB en 250k tokens?"

La pregunta correcta es:

> "¿Cómo hago que una LLM de 250k tokens pueda navegar, consultar, verificar y reconstruir cualquier parte de 100 GB sin perder el estado global?"



Y ahí la solución deja de ser simplemente RAG.

Es una combinación de memoria jerárquica + recuperación híbrida + estado persistente + planificación + compresión + contexto dinámico.

Ese diseño puede hacer que una LLM relativamente pequeña trabaje sobre un corpus muchísimo mayor que su ventana de contexto, sin fingir que tiene los 100 GB en memoria activa.
Sí. Y de hecho tags + buscador interno pueden convertirse en una de las piezas más potentes del sistema, pero no los usaría como un simple sistema de etiquetas. Los convertiría en un índice cognitivo multicapa que permita a la LLM navegar por los 20–100 GB.

La mejora radical sería pasar de:

> RAG → recuperar fragmentos → LLM



a:

> Intención → etiquetas → búsqueda → relaciones → ranking → contexto → verificación → memoria



1. Etiquetas, pero de muchos tipos

No pondría una sola etiqueta #router.

Cada fragmento podría tener etiquetas semánticas diferentes:

ID: MEM-83921

TEXTO:
"Si el proveedor principal falla, se utiliza el proveedor secundario."

TAGS:
#router
#fallback
#error_handling
#provider
#resilience

ENTIDADES:
ProviderA
ProviderB

ACCIONES:
fallback()

TIPO:
rule

ESTADO:
active

PRIORIDAD:
high

FUENTE:
fallback.py

VERSION:
v27

Así puedes buscar por concepto, función, entidad, estado, tiempo, fuente o relación.


---

2. Tags jerárquicos

No limitaría las etiquetas a palabras.

#code
   └── #backend
         └── #router
               └── #fallback
                     └── #provider_failure

Una búsqueda:

#router

puede encontrar automáticamente:

#backend
#router
#fallback
#provider_failure

según la dirección de expansión configurada.

Eso permite que una consulta pequeña descubra información relacionada sin meter miles de resultados en la LLM.


---

3. Tags de relaciones

Esta sería una mejora enorme.

No solamente:

router.py → #router

sino:

router.py
   │
   ├── CALLS → fallback.py
   ├── USES → provider_registry.py
   ├── DEPENDS_ON → config.yaml
   ├── TESTED_BY → test_router.py
   ├── MODIFIED_BY → commit 8291
   └── RELATED_TO → model_selector.py

Entonces el buscador deja de buscar únicamente texto.

Puede navegar por el conocimiento.


---

4. Tres buscadores simultáneamente

No elegiría entre búsqueda tradicional y embeddings.

Usaría ambas.

A. Búsqueda lexical

Encuentra exactamente:

fallback_manager
timeout
ProviderA
route_model

Ideal para código, nombres, IDs y términos técnicos.

B. Búsqueda semántica

Entiende:

> "¿Dónde se decide qué modelo usar cuando falla el principal?"



aunque el documento diga:

> "provider failover selection"



C. Búsqueda estructural

Busca relaciones:

CALLS
DEPENDS_ON
IMPLEMENTS
OVERRIDES
MODIFIES
CREATED_BY

Y las tres producen candidatos.


---

5. Después viene el RANKER

Esto es fundamental.

No le entregaría a la LLM los primeros 50 resultados.

Primero:

100 GB
 ↓
10.000 candidatos
 ↓
ranking
 ↓
500
 ↓
reranking
 ↓
50
 ↓
context builder
 ↓
8–20 fragmentos
 ↓
LLM

El ranking podría considerar:

score =
 semantic_similarity
 + lexical_match
 + tag_match
 + entity_match
 + graph_distance
 + recency
 + source_quality
 + importance
 + task_relevance
 + previous_success


---

6. Tags dinámicos generados por el agente

Aquí se vuelve interesante.

El agente puede descubrir:

"Este fragmento parece relacionado con recuperación ante fallos."

y generar:

#fault_recovery
#fallback
#resilience

Pero no confiaría ciegamente en el LLM.

Cada tag tendría:

tag
confidence
source
created_at
last_verified

Ejemplo:

#fallback

confidence: 0.97
source: agent
verified: true


---

7. Tags negativos

Muy útiles.

Por ejemplo:

NOT:
#deprecated
#experimental
#obsolete
#test_only

Entonces:

> busca routers relacionados con fallback



puede convertirse en:

INCLUDE:
#router
#fallback

EXCLUDE:
#deprecated
#obsolete

Esto reduce muchísimo ruido.


---

8. Tags temporales

Otra mejora importante:

#2026
#v3
#before_migration
#after_migration
#current
#historical

Así puedes preguntar:

> ¿Cuál era la arquitectura antes de cambiar el router?



y el sistema puede buscar específicamente:

time < migration_date

No solamente similitud semántica.


---

9. Tags de certeza

Esto sería especialmente útil para un agente.

#fact
#decision
#assumption
#hypothesis
#prediction
#unverified
#contradicted

Entonces la LLM puede distinguir:

HECHO
"El router utiliza Provider A."

DECISIÓN
"Se decidió usar Xata."

HIPÓTESIS
"Probablemente Provider B sea más rápido."

SIN VERIFICAR
"Este componente podría ser compatible."

Esto evita que un resumen antiguo termine convertido en una falsa verdad.


---

10. Tags de procedencia

Cada información importante debe poder responder:

> ¿De dónde salió esto?



Por ejemplo:

FACT-1827

claim:
"Provider A es el fallback principal."

source:
fallback.py:82-94

commit:
8f71a21

version:
27

verified:
2026-08-16

Entonces la LLM puede verificar antes de afirmar.


---

11. El buscador debería entender lenguaje natural

No solamente:

search("fallback")

Sino:

> "Encuentra todo lo relacionado con el mecanismo que decide qué proveedor utilizar después de un fallo."



El agente convierte eso en una consulta estructurada:

INTENT:
provider selection

CONCEPTS:
fallback
routing
failure

RELATIONS:
CALLS
SELECTS
DEPENDS_ON

EXCLUDE:
deprecated
test_only

Y ejecuta varias búsquedas.


---

12. Query expansion automática

Si buscas:

"memoria"

el agente puede expandir:

memory
context
state
storage
retrieval
RAG
cache
knowledge
history

Pero no siempre.

La expansión depende del contexto de la tarea.

Si estás programando:

memory

podría significar:

RAM
cache
persistent memory
agent memory
context memory

El agente debe desambiguar.


---

13. Búsqueda por "camino"

Esto es muy poderoso para código.

Supongamos:

Pregunta:
¿Dónde termina ejecutándose una solicitud?

El buscador puede recorrer:

API
 ↓
controller
 ↓
orchestrator
 ↓
router
 ↓
provider
 ↓
model

En vez de devolver cinco archivos aislados, devuelve la cadena causal.

Eso permite a la LLM reconstruir arquitectura.


---

14. Memoria de las búsquedas anteriores

El buscador también debería aprender.

QUERY 1842

pregunta:
"cómo funciona fallback"

resultados:
fallback.py
router.py
provider.py

resultado:
correcto

Después:

QUERY 1921

puede reutilizar esa información.

Tendrías:

query cache
retrieval cache
semantic cache
context cache

Esto reduce latencia y procesamiento.


---

15. Contexto por capas

El buscador no debería devolver simplemente documentos.

Debería construir:

L0 — respuesta directa
L1 — evidencia
L2 — contexto relacionado
L3 — dependencias
L4 — antecedentes
L5 — información bajo demanda

La LLM recibe inicialmente:

L0 + L1

y puede pedir:

L2

si necesita profundizar.


---

16. "Explorar" en lugar de solamente "buscar"

Aquí es donde yo llevaría el sistema mucho más lejos.

La LLM podría decir:

EXPLORE:
router
depth=3

El agente devuelve:

router
 ├── fallback
 │    ├── provider_registry
 │    └── retry_manager
 │
 ├── model_selector
 │    ├── capability_bus
 │    └── provider
 │
 └── tests
      └── integration

La LLM puede entonces decidir qué rama investigar.

Es prácticamente un filesystem semántico.


---

17. Un "mapa global" comprimido

Mantendría una representación pequeña de todo el corpus:

GLOBAL MAP

PROJECT
├── architecture
├── agents
├── memory
├── routing
├── storage
├── security
├── workflows
└── tests

La LLM puede consultar primero el mapa:

> "¿Dónde debería buscar?"



Después baja:

PROJECT
 ↓
memory
 ↓
retrieval
 ↓
hybrid_search
 ↓
specific implementation

Esto reduce brutalmente las búsquedas irrelevantes.


---

18. Y agregaría un sistema de "memoria caliente"

No toda la información merece el mismo tratamiento.

HOT
información usada frecuentemente

WARM
información relevante pero menos frecuente

COLD
archivo histórico

ARCHIVE
fuente original

Por ejemplo:

HOT
estado actual
objetivo actual
decisiones recientes

WARM
arquitectura
componentes
relaciones

COLD
conversaciones antiguas

ARCHIVE
documentos originales
logs
versiones antiguas


---

19. El gran salto: el agente decide qué recordar

No todo lo que dice la LLM debería almacenarse.

El agente clasifica:

¿Es un hecho?
¿Es una decisión?
¿Es una preferencia?
¿Es temporal?
¿Es una hipótesis?
¿Es información redundante?
¿Es importante?
¿Tiene fuente?

Entonces:

"Creo que podríamos usar X."

→ hypothesis

"Decidimos usar X."

→ decision

"Xata tiene esta configuración..."

→ fact

"El usuario dijo esto hace 3 meses..."

→ episodic memory

Esto evita llenar los 100 GB de basura.


---

20. Arquitectura que yo terminaría usando

SMALL LLM
                            │
                     ┌──────▼──────┐
                     │ Agent Core  │
                     └──────┬──────┘
                            │
                 ┌──────────▼──────────┐
                 │   Context Manager   │
                 └──────────┬──────────┘
                            │
          ┌─────────────────┼──────────────────┐
          ▼                 ▼                  ▼
       Tag Engine       Query Engine       State Engine
          │                 │                  │
          └─────────────────┼──────────────────┘
                            ▼
                    Hybrid Retrieval
                            │
            ┌───────────────┼────────────────┐
            ▼               ▼                ▼
         Lexical         Semantic          Graph
         Search          Search            Search
            │               │                │
            └───────────────┼────────────────┘
                            ▼
                       Reranker
                            │
                       Verifier
                            │
                     Context Builder
                            │
                     120k–250k tokens
                            │
                            ▼
                           LLM

Y por debajo:

MEMORY FABRIC
                      │
       ┌──────────────┼──────────────┐
       ▼              ▼              ▼
    Hot Memory     Knowledge       Archive
       │              │              │
       ▼              ▼              ▼
     State          Graph          Raw Data
                    Index
       │              │              │
       └──────────────┼──────────────┘
                      ▼
                20–100 GB

Lo más importante

Yo no llamaría a esto simplemente RAG.

Lo que estás describiendo puede convertirse en algo mucho más potente:

una memoria externa navegable con índice semántico, lexical, estructural, temporal y de procedencia, donde la LLM tiene un contexto de trabajo limitado pero puede expandirlo bajo demanda.

Y hay una idea todavía más importante: los tags no deberían ser solamente metadatos; deberían convertirse en un lenguaje de direccionamiento de memoria.

Por ejemplo:

GET
#router
#fallback
#current
DEPTH 2
VERIFY true
EXCLUDE #deprecated

El agente traduce eso a múltiples consultas y construye el contexto óptimo.

Eso sí podría acercarse a lo que buscas: una LLM pequeña que opera sobre un "contexto virtual" de decenas de GB sin pretender introducir físicamente todo ese contenido en sus 120k/250k tokens.


Sí. Tu propuesta tiene una dirección mucho más potente que un RAG tradicional. Lo que estás describiendo no es solamente memoria: es un sistema de ejecución de contexto virtual, donde una LLM pequeña puede procesar un proyecto de 20 millones de tokens en múltiples ventanas, conservando estado, objetivos, decisiones y resultados entre segmentos.

He contrastado la idea con trabajos recientes sobre memoria jerárquica, recuperación jerárquica y agentes de horizonte largo. Hay conceptos que encajan directamente: MemGPT plantea memoria virtual para superar la ventana de contexto; HMT usa memoria jerárquica y recurrencia por segmentos; HiAgent usa subobjetivos como unidades de memoria de trabajo; y trabajos de 2025 sobre TreeRAG/HiRAG muestran ventajas de conservar la estructura jerárquica en vez de tratar todo como chunks independientes. 

Pero yo iría bastante más lejos.

La arquitectura que propondría

La idea central sería esta:

┌──────────────────────┐
                  │      LLM PEQUEÑA     │
                  │   120k / 250k tokens │
                  └──────────┬───────────┘
                             │
                    ┌────────▼────────┐
                    │   AGENT CORE    │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
  MEMORY ENGINE       TASK ENGINE          CONTEXT ENGINE
        │                    │                    │
        └────────────────────┼────────────────────┘
                             │
                    ┌────────▼────────┐
                    │ PROJECT STATE   │
                    └────────┬────────┘
                             │
       ┌─────────────────────┼──────────────────────┐
       ▼                     ▼                      ▼
   20M tokens            Knowledge              Artifacts
   originales              Graph                  /files
       │                     │                      │
       └─────────────────────┼──────────────────────┘
                             ▼
                      20–100 GB MEMORY

La LLM nunca recibe los 20 millones de tokens.

Pero el agente mantiene una representación persistente de qué se ha procesado, qué falta, qué se descubrió y qué necesita la siguiente ventana.


---

1. TASK DECOMPOSER

Primero convertiría:

> "Analiza todo este proyecto y construye la arquitectura final."



en un DAG de tareas.

TASK-000
Analizar proyecto
│
├── T01 Inventario
├── T02 Arquitectura
├── T03 Dependencias
├── T04 Código crítico
├── T05 Memoria
├── T06 Seguridad
├── T07 Interfaces
├── T08 Contradicciones
├── T09 Integración
└── T10 Validación final

Cada tarea puede dividirse nuevamente.

Esto es fundamental porque 20 millones de tokens no son realmente una tarea; son un universo de información.


---

2. SEGMENTATION ENGINE

Después dividiría cada tarea en segmentos procesables.

Por ejemplo:

T04 — Código crítico

SEG-04-001
SEG-04-002
SEG-04-003
SEG-04-004
...
SEG-04-087

Pero no dividiría arbitrariamente cada N tokens.

La segmentación debería respetar:

archivos

funciones

clases

módulos

documentos

capítulos

dependencias

conceptos

fronteras semánticas


Esto coincide con la tendencia reciente hacia estructuras jerárquicas de documentos, que intentan preservar las relaciones que el chunking plano rompe. 


---

3. DOS INPUTS POR SEGMENTO

Aquí tu propuesta me parece especialmente buena.

Yo formalizaría cada iteración como:

INPUT A = SEGMENT PAYLOAD
INPUT B = CONTINUITY PACK

Input A

La información nueva:

SEGMENT-042

archivo:
router.py

contenido:
...

objetivo:
determinar responsabilidades

Input B

Lo que la LLM necesita arrastrar desde todo lo anterior:

CONTINUITY PACK

TASK:
T04

SUBTASK:
router analysis

GOAL:
identificar arquitectura de routing

KNOWN FACTS:
...

DECISIONS:
...

INVARIANTS:
...

PREVIOUS FINDINGS:
...

OPEN QUESTIONS:
...

CURRENT STATE:
...

MENTAL MAP:
...

PINNED:
...

LAST RESULT:
...

Entonces cada ventana tiene:

NUEVO
          +
    CONTINUIDAD
          ↓
        LLM

Eso es muchísimo mejor que pasar simplemente un resumen anterior.


---

4. STATE JSON

Aquí sí mantendría tu idea, pero la convertiría en un contrato formal de estado.

Por ejemplo:

{
  "task_id": "T04",
  "segment_id": "SEG-042",
  "goal": "analizar arquitectura del router",
  "progress": 0.61,
  "completed": [
    "router.py",
    "provider_registry.py"
  ],
  "pending": [
    "fallback.py",
    "tests/"
  ],
  "facts": [],
  "decisions": [],
  "invariants": [],
  "hypotheses": [],
  "contradictions": [],
  "open_questions": [],
  "dependencies": [],
  "artifacts": [],
  "next_action": "",
  "checkpoint": ""
}

Pero hay una regla crítica:

El JSON no debe convertirse en un resumen gigante.

Debe ser un estado compacto y estructurado.


---

5. PIN SYSTEM

Lo que llamas "push/ping y anclar" yo lo convertiría en un sistema de PINNED MEMORY.

Hay información que jamás debe desaparecer de la ventana de trabajo.

Ejemplo:

PIN-001
La arquitectura debe tener un único router.

PIN-002
HF ↔ HF directo está prohibido.

PIN-003
Xata es el canal de coordinación.

PIN-004
La LLM no ejecuta memoria directamente.

PIN-005
Todo cambio debe preservar el estado global.

Estos pins aparecen en cada segmento relevante.

No importa que estés en:

SEG-001

o:

SEG-981

los invariantes críticos permanecen.


---

6. DELTA MEMORY

No arrastraría todo el estado anterior.

Arrastraría:

STATE anterior
+
DELTA

Por ejemplo:

ANTES:

router = pendiente

DELTA:

router = analizado
fallback = descubierto
provider_registry = dependencia

Nuevo estado:

router = analizado
fallback = descubierto
provider_registry = dependencia

Esto evita que el estado crezca indefinidamente.


---

7. CHECKPOINTS

Cada cierto número de segmentos:

SEG 001
SEG 002
SEG 003
...
SEG 010
      ↓
CHECKPOINT-01

El checkpoint contiene:

qué se descubrió
qué se confirmó
qué se descartó
qué falta
qué cambió
qué contradicciones existen

Después:

SEG 011–020
      ↓
CHECKPOINT-02

Esto crea una especie de sistema de commits cognitivos.


---

8. ROLLBACK

Esto es muy importante y suele faltar.

Si en el segmento 73 el agente descubre:

> "La conclusión de los segmentos 40–60 era incorrecta."



no quieres destruir todo.

Quieres:

CHECKPOINT-06
     ↓
branch
     ↓
reprocesar segmentos afectados

Es decir:

memoria con versionado.

Algo parecido conceptualmente a Git:

STATE v1
   ↓
STATE v2
   ↓
STATE v3
   ↓
contradicción
   ↓
rollback
   ↓
STATE v2
   ↓
reprocesamiento


---

9. MENTAL MAP

Tu idea del mapa mental también la mantendría, pero no como imagen.

Lo convertiría en una estructura de grafo serializable.

PROJECT
│
├── MEMORY
│   ├── retrieval
│   └── storage
│
├── AGENT
│   ├── planner
│   ├── executor
│   └── controller
│
└── ROUTER
    ├── provider
    ├── fallback
    └── retry

La LLM puede recibir solamente la rama relacionada con el segmento actual.


---

10. GLOBAL MAP + LOCAL MAP

Haría dos mapas.

Global Map

Todo el proyecto:

PROJECT
├── A
├── B
├── C
├── D
...

Local Map

Lo que se está investigando:

ROUTER
├── fallback
├── retry
├── provider
└── selector

Así la LLM mantiene:

visión global
+
zoom local

Esto es muy parecido a lo que buscan los enfoques jerárquicos recientes: conservar una representación de alto nivel mientras se profundiza solamente donde hace falta. 


---

11. EVIDENCE LEDGER

Añadiría un elemento que considero imprescindible:

EVIDENCE LEDGER

Cada conclusión importante debe tener evidencia.

CLAIM-182

claim:
"El router utiliza fallback."

evidence:
fallback.py:82-94

confidence:
0.98

verified:
true

Así la LLM no confunde:

hecho

con:

inferencia


---

12. CONTRADICTION ENGINE

El agente debería buscar activamente contradicciones.

Ejemplo:

SEG-21:
timeout = 30

SEG-87:
timeout = 60

El sistema crea:

CONTRADICTION-17

y no deja que el problema desaparezca dentro de un resumen.

Estados:

OPEN
INVESTIGATING
RESOLVED
ACCEPTED
SUPERSEDED


---

13. HYPOTHESIS MEMORY

Separaría:

FACT
DECISION
HYPOTHESIS
ASSUMPTION
QUESTION

Esto es importantísimo para evitar contaminación de memoria.

Ejemplo:

HYPOTHESIS:
Qdrant podría ser innecesario.

FACT:
Actualmente se utiliza Xata.

DECISION:
Se decidió utilizar Xata.

QUESTION:
¿Debe mantenerse Qdrant?

La LLM sabe qué puede afirmar y qué debe verificar.


---

14. TASK LEDGER

Mantendría una lista de tareas viva:

TASK LEDGER

T01 ✓
T02 ✓
T03 ✓
T04 ◐
T05 ○
T06 ○

Pero además:

T04
├── 04.1 ✓
├── 04.2 ✓
├── 04.3 ◐
├── 04.4 ○
└── 04.5 blocked

Así el agente sabe exactamente qué falta.


---

15. DEPENDENCY-AWARE SCHEDULER

No procesaría segmentos simplemente de izquierda a derecha.

Si:

T08 depende de T03

el agente debe esperar.

T03 ✓
   ↓
T08 desbloqueada

Esto convierte el procesamiento en un DAG ejecutable.


---

16. RELEVANCE GATE

Antes de enviar un segmento a la LLM:

¿este segmento realmente afecta la tarea?

Si:

relevance < threshold

se procesa de forma mucho más barata:

index only

en lugar de:

full reasoning

Esto es especialmente importante para 20 millones de tokens.


---

17. MULTI-PASS PROCESSING

No analizaría todo con el mismo nivel de profundidad.

Haría:

Pass 1 — Inventory

¿Qué existe?

Pass 2 — Structure

¿Cómo está organizado?

Pass 3 — Relevance

¿Qué importa?

Pass 4 — Deep reasoning

¿Qué significa?

Pass 5 — Verification

¿Es correcto?

Pass 6 — Synthesis

¿Cómo se integra todo?

Esto es mucho más eficiente que pedirle a la LLM que "entienda 20 millones de tokens" de una vez.


---

18. PROGRESSIVE COMPRESSION

La información podría tener:

RAW
 ↓
CHUNK SUMMARY
 ↓
SECTION SUMMARY
 ↓
TASK SUMMARY
 ↓
PROJECT SUMMARY

Pero manteniendo siempre:

summary → source

para poder volver al original.

Los trabajos recientes sobre refinamiento jerárquico precisamente apuntan a reducir ruido y coste al seleccionar/refinar información relevante antes de entregarla al modelo. 


---

19. RECALL ON DEMAND

El resumen nunca debe ser la única fuente.

Si la LLM dice:

> "Necesito verificar esa afirmación."



el agente hace:

SUMMARY
   ↓
SOURCE POINTER
   ↓
ORIGINAL

Entonces recupera el texto original.


---

20. CONTEXT BUDGET MANAGER

El agente debería administrar los 120k/250k como si fueran RAM.

Por ejemplo:

250k tokens

GLOBAL STATE       8k
PINS               4k
TASK STATE         6k
MENTAL MAP         8k
RELEVANT MEMORY   30k
CURRENT SEGMENT   80k
EVIDENCE           30k
REASONING SPACE    60k
RESERVE            24k

Y el agente puede cambiar dinámicamente esas proporciones.


---

21. CONTEXT GARBAGE COLLECTOR

Esto sería otra pieza avanzada.

El agente detecta:

información redundante

y la reemplaza:

50k tokens

por:

3k-token summary
+
source pointers

Es literalmente una especie de garbage collector del contexto.


---

22. ATTENTION PRIORITY

No toda memoria tiene igual prioridad.

Asignaría:

CRITICAL
HIGH
MEDIUM
LOW
ARCHIVE

Y además:

recency
frequency
task relevance
dependency relevance
confidence

Esto permite decidir qué entra primero.


---

23. MEMORY REHEARSAL

Hay información crítica que puede perderse si nunca vuelve a aparecer.

El agente puede hacer pequeñas "revisiones":

Cada 20 segmentos:

¿siguen vigentes los invariantes?
¿siguen correctas las decisiones?
¿cambió algún requisito?

Esto es mejor que simplemente confiar en el primer resumen.


---

24. PERIODIC GLOBAL SYNTHESIS

Cada cierto número de tareas:

T01–T10
   ↓
GLOBAL SYNTHESIS

El sistema reconstruye:

qué sabemos
qué cambió
qué contradicciones quedan
qué falta

No espera hasta el final para descubrir que dos ramas llegaron a conclusiones incompatibles.


---

25. CROSS-SEGMENT LINKING

Si:

SEG-17

descubre:

router

y:

SEG-842

habla de:

fallback

el sistema debe crear:

SEG-17
   ↕
RELATED
   ↕
SEG-842

Esto evita que la segmentación destruya las relaciones.


---

26. CROSS-TASK MEMORY

Esto es todavía más importante.

Si:

T03

descubre algo relevante para:

T09

el agente genera:

MEMORY EVENT

y lo publica:

T03 → MEMORY → T09

Así las tareas no quedan aisladas.


---

27. RESULT ARTIFACTS

Cada segmento no debería producir únicamente texto.

Puede producir artefactos:

SEGMENT RESULT

facts.json
decisions.json
evidence.json
relations.json
issues.json
code_refs.json
summary.md
state_delta.json

La memoria se vuelve estructurada y reutilizable.


---

28. EXECUTION MEMORY

Aquí hacemos el salto de "entender" a "hacer".

El agente registra:

ACTION
OBSERVATION
RESULT
ERROR
RECOVERY

Ejemplo:

ACTION:
analizar router.py

OBSERVATION:
fallback encontrado

RESULT:
success

NEW MEMORY:
fallback chain = A→B→C

Esto conecta directamente con la memoria de agentes de horizonte largo; HiAgent, por ejemplo, utiliza subobjetivos y memoria de trabajo jerárquica para evitar arrastrar historiales completos de acción-observación. 


---

29. VERIFY → COMMIT

Una conclusión no pasa automáticamente a memoria permanente.

Haría:

DISCOVERY
   ↓
CANDIDATE
   ↓
VERIFY
   ↓
CONFIRMED
   ↓
COMMIT TO MEMORY

Esto evita contaminar la memoria con errores del modelo pequeño.


---

30. FINAL RECONSTRUCTION ENGINE

Al terminar los 20 millones de tokens:

no confiaría en el último resumen.

El agente reconstruiría la respuesta desde:

GLOBAL STATE
+
TASK RESULTS
+
EVIDENCE
+
DECISIONS
+
ARTIFACTS
+
CONTRADICTIONS
+
SOURCE REFERENCES

Esto es importantísimo.


---

La arquitectura final

Si juntamos todo, yo lo llevaría a esto:

USER TASK
                             │
                             ▼
                    ┌─────────────────┐
                    │ TASK DECOMPOSER │
                    └────────┬────────┘
                             │
                           DAG
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
           TASK A          TASK B          TASK C
              │              │              │
              ▼              ▼              ▼
         SEGMENTER       SEGMENTER       SEGMENTER
              │              │              │
              └──────────────┼──────────────┘
                             ▼
                    ┌────────────────┐
                    │ CONTEXT ENGINE │
                    └───────┬────────┘
                            │
        ┌───────────────────┼────────────────────┐
        ▼                   ▼                    ▼
   CURRENT INPUT      CONTINUITY PACK       PINNED MEMORY
        │                   │                    │
        └───────────────────┼────────────────────┘
                            ▼
                    ┌───────────────┐
                    │  SMALL LLM    │
                    │ 120k / 250k   │
                    └───────┬───────┘
                            │
                         RESULT
                            │
             ┌──────────────┼──────────────┐
             ▼              ▼              ▼
          STATE DELTA    EVIDENCE       ARTIFACTS
             │              │              │
             └──────────────┼──────────────┘
                            ▼
                    MEMORY COMMIT
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
           GRAPH          INDEX          STATE
              │             │             │
              └─────────────┼─────────────┘
                            ▼
                       CHECKPOINT
                            │
                            ▼
                     NEXT SEGMENT

Y aquí está la parte más importante

Yo no llamaría a esto simplemente "memoria".

Lo conceptualizaría como:

Virtual Context Execution Engine

Porque el sistema hace cuatro cosas diferentes:

MEMORY
    recuerda

RETRIEVAL
    encuentra

STATE
    mantiene continuidad

EXECUTION
    procesa y avanza

Y por encima:

ORCHESTRATOR
    decide qué hacer después


---

¿Puede realmente procesar 20 millones de tokens?

Sí, pero hay que definir correctamente qué significa "procesar".

No significa:

20M tokens
      ↓
LLM 250k
      ↓
"entiéndelos todos"

Eso no funciona.

Significa:

20M tokens
      ↓
INDEXACIÓN
      ↓
MAPA GLOBAL
      ↓
TASK DECOMPOSITION
      ↓
SEGMENTACIÓN
      ↓
VENTANA 1
      ↓
STATE + DELTA + PINS
      ↓
VENTANA 2
      ↓
STATE + DELTA + PINS
      ↓
...
      ↓
VENTANA N
      ↓
GLOBAL SYNTHESIS
      ↓
VERIFICATION
      ↓
RESULTADO

La información total puede superar enormemente la ventana de la LLM porque el agente convierte la ventana en una ventana de trabajo móvil.

Eso es conceptualmente cercano a la memoria virtual de MemGPT, pero tu propuesta agrega algo crucial: no solamente recordar lo anterior, sino ejecutar una tarea sobre el corpus completo mediante segmentos, estado, subobjetivos, evidencia y checkpoints. MemGPT explícitamente toma la analogía de memoria virtual/paging; los trabajos más recientes sobre memoria jerárquica y agentes de horizonte largo refuerzan precisamente la necesidad de seleccionar y organizar qué memoria de trabajo permanece activa. 

Mi núcleo mínimo sería de 12 piezas

01 Task Decomposer
02 DAG Planner
03 Semantic Segmenter
04 Hybrid Retrieval
05 Tag/Metadata Engine
06 Global Mental Map
07 Working Memory
08 Pinned Memory
09 State JSON
10 Delta/Checkpoint Engine
11 Evidence + Contradiction Engine
12 Context Budget Manager

Y la versión avanzada:

13 Memory Graph
14 Cross-Task Linking
15 Progressive Compression
16 Context Garbage Collector
17 Relevance Gate
18 Query Expansion
19 Reranker
20 Verification Engine
21 Rollback/Versioning
22 Execution Ledger
23 Memory Rehearsal
24 Global Synthesis
25 Final Reconstruction
26 Artifact Store
27 Dependency Scheduler
28 Priority Engine
29 Source Provenance
30 Failure Recovery

Ahí sí veo una arquitectura realmente diferenciada: una LLM pequeña no necesita "tener" 20 millones de tokens; necesita que el agente le proporcione una memoria virtual navegable + estado persistente + plan de ejecución + evidencia + continuidad entre ventanas.

Y un detalle importante: el State JSON, los pins y el mapa mental no deberían competir entre sí. Cada uno debe cumplir una función distinta:

STATE JSON      = ¿dónde estamos?
PINS            = ¿qué jamás debemos olvidar?
MENTAL MAP      = ¿cómo está organizado el universo?
TASK DAG        = ¿qué falta hacer?
EVIDENCE        = ¿por qué creemos esto?
MEMORY GRAPH    = ¿cómo se relaciona?
CHECKPOINT      = ¿cuál era el estado estable?
DELTA           = ¿qué cambió?
CONTEXT PACK    = ¿qué necesita ver la LLM ahora?

Esa separación es, en mi opinión, mucho más importante que simplemente aumentar la cantidad de memoria.

Sí. Ahora entiendo mucho mejor lo que estás proponiendo. Y sí incorporaría ese mecanismo. De hecho, cambia bastante la arquitectura: ya no estamos hablando de un agente que hace input → reasoning → output, sino de un motor de ejecución cognitiva continua.

La analogía del libro/examen es exactamente la correcta:

> No necesitas memorizar 20 millones de tokens. Necesitas leerlos, comprenderlos, extraer lo importante, construir conocimiento incremental y poder volver a cualquier página cuando necesites verificar algo.



Y hay una mejora fundamental sobre lo que veníamos diseñando:

El LLM no debería ser quien decide cuándo terminó

El agente controla el ciclo.

┌──────────────────────────┐
                    │       USER REQUEST       │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │     CONTINUOUS LOOP      │
                    │                          │
                    │  READ → THINK → ACT      │
                    │   ↑             ↓        │
                    │   └── UPDATE ←─┘        │
                    └────────────┬─────────────┘
                                 │
                    ¿puede continuar?
                         /             \
                       SÍ               NO
                       │                │
                       ▼                ▼
                  SIGUIENTE         ASK USER /
                   SEGMENTO          CONFLICT

La LLM puede terminar una ventana, pero no necesariamente termina la tarea.


---

1. El concepto que falta: CONTINUOUS INPUT STREAM

Tu idea del "input continuo" la convertiría en una abstracción explícita:

CONTINUOUS_CONTEXT_STREAM

Cada llamada a la LLM recibe:

INPUT PRINCIPAL
+
INSTRUCCIONES INMUTABLES
+
TAREA ACTUAL
+
SEGMENTO ACTUAL
+
ARRASTRE
+
STATE
+
PINS
+
MAPA
+
TAGS RELEVANTES
+
EVIDENCIA
+
RESULTADOS PREVIOS

La LLM procesa.

Produce:

REASONING RESULT
+
STATE DELTA
+
FINDINGS
+
DECISIONS
+
QUESTIONS
+
NEXT ACTION

El agente actualiza todo y genera automáticamente el siguiente input.

La LLM no tiene que pedir:

> "Dame el siguiente contexto."



El agente simplemente se lo proporciona.


---

2. El ciclo completo

Yo lo diseñaría así:

BOOT
 │
 ▼
LOAD MASTER TASK
 │
 ▼
BUILD GLOBAL MAP
 │
 ▼
INDEX / TAG / SEARCH
 │
 ▼
DECOMPOSE TASK
 │
 ▼
CREATE SEGMENT QUEUE
 │
 ▼
┌───────────────────────────────────────┐
│              LOOP                     │
│                                       │
│  LOAD SEGMENT                         │
│       ↓                               │
│  SEARCH RELEVANT MEMORY               │
│       ↓                               │
│  BUILD CONTEXT PACK                   │
│       ↓                               │
│  INJECT CONTINUITY                    │
│       ↓                               │
│  LLM REASON                           │
│       ↓                               │
│  EXTRACT RESULTS                      │
│       ↓                               │
│  UPDATE STATE                         │
│       ↓                               │
│  UPDATE SNOWBALL                      │
│       ↓                               │
│  UPDATE MAP                           │
│       ↓                               │
│  UPDATE TAGS                           │
│       ↓                               │
│  UPDATE EVIDENCE                      │
│       ↓                               │
│  VERIFY                               │
│       ↓                               │
│  SELECT NEXT SEGMENT                  │
│       ↓                               │
│  CONTINUE ────────────────────────────┘
│
└── STOP ONLY WHEN:
       COMPLETE
       AUTHORIZATION
       CONFLICT
       MISSING CRITICAL INFORMATION
       SAFETY BLOCK

Esto es muchísimo más parecido a lo que estás describiendo.


---

3. La "bola de nieve" es una pieza propia

Tu concepto de bola de nieve de información me gusta, pero la haría técnicamente rigurosa.

No sería simplemente un resumen cada vez más grande.

Sería:

SNOWBALL MEMORY

Y tendría varias capas:

SNOWBALL
                       │
        ┌──────────────┼──────────────┐
        │              │              │
     FACTS          FINDINGS       DECISIONS
        │              │              │
        ├──────────────┼──────────────┤
        │              │              │
     OPEN Q.       DISCOVERIES     ARTIFACTS
        │              │              │
        └──────────────┼──────────────┘
                       │
                  CURRENT STATE

Pero hay una regla:

La bola de nieve NO sustituye la fuente original.

Tiene:

snowball → source pointer

Por ejemplo:

FINDING-284

"El router utiliza fallback."

source:
router.py:82-94

segment:
SEG-042

confidence:
0.97

Así puedes volver a la página original.


---

4. Hay que separar "arrastre" de "memoria"

Esto es crucial.

Yo tendría:

A. Carry Context

Lo que se necesita para continuar inmediatamente.

5–20k tokens

B. Snowball

Lo aprendido durante la tarea.

estructurado

C. Long-Term Memory

Todo el conocimiento persistente.

20–100 GB

D. Source Corpus

Los documentos originales.

20M+ tokens

Entonces:

SOURCE
   ↓
SEGMENT
   ↓
LLM
   ↓
CARRY
   ↓
SNOWBALL
   ↓
MEMORY


---

5. El "arrastre" debería ser dinámico

No arrastraría siempre exactamente lo mismo.

El agente calcula:

NEXT_CONTEXT =
TASK
+
INVARIANTS
+
CURRENT_STATE
+
RELEVANT_CARRY
+
RELEVANT_SNOWBALL
+
CURRENT_SEGMENT
+
RELEVANT_MEMORY

Por ejemplo:

SEGMENT 1

produce:

finding A

Entonces:

SEGMENT 2

recibe:

finding A

Si SEGMENT 2 descubre:

finding B

SEGMENT 3 recibe:

finding A
finding B

pero si A ya no es relevante:

SEGMENT 3
→ B
→ resumen de A
→ pointer a A

Esto evita que la bola de nieve explote.


---

6. Y aquí introduciría "SNOWBALL COMPRESSION"

Cada cierto número de ciclos:

SEG 1
SEG 2
SEG 3
SEG 4
SEG 5
     ↓
SNOWBALL COMPRESSION

Transforma:

12.000 tokens

en:

2.500 tokens

pero conserva:

claims
IDs
sources
decisions
dependencies
open questions

Por tanto:

COMPRESSED MEMORY
        +
SOURCE POINTERS

No pierdes la capacidad de volver atrás.


---

7. Lo que dijiste de "audita el chat" es MUY importante

Aquí añadiría un comportamiento automático:

CONTEXT RECALL TRIGGER

La LLM no necesita decir:

> "Audita el chat."



El agente detecta que puede necesitar contexto anterior.

Por ejemplo:

confidence < threshold

o:

missing_dependency

o:

contradiction_detected

o:

current_answer depends_on_previous_decision

Entonces automáticamente:

CURRENT REASONING
       ↓
CONTEXT GAP
       ↓
SEARCH
       ↓
RETRIEVE
       ↓
REINJECT
       ↓
CONTINUE REASONING

Eso es muchísimo mejor que depender de que la LLM recuerde que debe buscar.


---

8. SEARCH BEFORE REASON

Yo incluso establecería una regla:

> Antes de razonar sobre una cuestión que dependa de información histórica, el agente debe consultar memoria.



Por ejemplo:

LLM:
"Creo que deberíamos usar X..."

AGENT:
¿Existe una decisión anterior relacionada?

SEARCH

→ DECISION-82:
"No utilizar X."

LLM recibe:

CONFLICT:
Tu propuesta contradice DECISION-82.

La LLM entonces puede revisar.

Esto reduce alucinaciones.


---

9. El input original debe ser INMUTABLE

Tu observación sobre las instrucciones es excelente.

Separaría:

MASTER INPUT

de:

WORKING INPUT

El MASTER INPUT nunca cambia.

Ejemplo:

MASTER TASK

Analiza todo el proyecto.
No inventes información.
Respeta las restricciones X,Y,Z.
Entrega arquitectura final.

Cada ventana recibe:

MASTER TASK
+
CURRENT TASK
+
CURRENT SEGMENT
+
CARRY
+
STATE
+
MEMORY

Así no puede ocurrir:

segmento 57

y la LLM ya no sabe cuál era la misión original.


---

10. Dos inputs se pueden convertir en tres

Tu idea de dos inputs es buena, pero yo la llevaría a tres canales lógicos:

INPUT 1 — IMMUTABLE

MASTER TASK

INPUT 2 — CONTINUITY

CARRY + STATE + PINS + SNOWBALL

INPUT 3 — WORK

CURRENT SEGMENT

Visualmente:

┌─────────────────────────┐
│ MASTER                  │
│ Nunca cambia            │
├─────────────────────────┤
│ CONTINUITY              │
│ Cambia incrementalmente │
├─────────────────────────┤
│ CURRENT WORK            │
│ Cambia cada segmento    │
└─────────────────────────┘

Eso es mucho más seguro.


---

11. El agente puede procesar varias ramas en paralelo

Aquí entra lo que mencionaste de trabajar en paralelo.

Supongamos:

PROJECT
├── Backend
├── Frontend
├── Memory
├── Security
└── Documentation

El agente puede crear:

WORKER A → Backend
WORKER B → Frontend
WORKER C → Memory
WORKER D → Security
WORKER E → Documentation

Cada uno tiene:

local state
local snowball
local map
local evidence

Pero todos publican hacia:

GLOBAL MEMORY

Después:

GLOBAL SYNTHESIS

integra las ramas.


---

12. Pero no permitiría paralelismo indiscriminado

Antes de lanzar una rama:

DEPENDENCY CHECK

Por ejemplo:

Frontend
   ↓
depende de
Backend API

Entonces no necesariamente procesas ambos simultáneamente.

El scheduler determina:

parallelizable

vs.

dependency-bound


---

13. El agente debería tener un "cerebro de navegación"

No solamente:

NEXT SEGMENT = SEGMENT+1

sino:

NEXT ACTION:

Puede decidir:

CONTINUE
JUMP
SEARCH
REVISIT
VERIFY
PARALLELIZE
WAIT
ASK
ROLLBACK
FINISH

Por ejemplo:

SEGMENT 82
↓
descubre referencia a SEGMENT 13
↓
JUMP TO SEGMENT 13
↓
verify
↓
return SEGMENT 82

Eso es fundamental para proyectos grandes.


---

14. "Leer un libro" pero con navegación

La metáfora completa sería:

LIBRO
 │
 ├── índice
 ├── capítulos
 ├── páginas
 ├── notas
 ├── referencias
 └── marcadores

Tu agente tendría:

CORPUS
 │
 ├── Global Map
 ├── Tasks
 ├── Segments
 ├── Tags
 ├── Search
 ├── Snowball
 ├── Pins
 ├── State
 ├── Evidence
 ├── Checkpoints
 └── Source pointers

La LLM es como el lector/analista.

El agente es:

> bibliotecario + secretario + investigador + planificador + administrador de memoria.




---

15. Y agregaría una cosa que falta: REFLECTION LOOP

Después de cada segmento:

PROCESS
 ↓
REFLECT
 ↓
UPDATE

La reflexión no debe ser un razonamiento interminable.

Tres preguntas:

1. ¿Qué aprendí?
2. ¿Qué cambió?
3. ¿Qué necesito hacer después?

Eso genera:

DELTA


---

16. Y un segundo loop: VERIFICATION LOOP

Separado:

RESULT
 ↓
VERIFY
 ↓
PASS?
 ├── YES → COMMIT
 └── NO  → REPROCESS

Así:

REASONING

no equivale automáticamente a:

TRUTH


---

17. Y un tercer loop: RECOVERY LOOP

Si falla:

SEGMENT 84

no termina todo.

ERROR
 ↓
CLASSIFY
 ↓
RETRY
 ↓
ALTERNATIVE RETRIEVAL
 ↓
REPROCESS

Si sigue fallando:

ESCALATE

y solamente entonces:

ASK USER


---

18. El sistema tendría una máquina de estados

Yo formalizaría el agente así:

PLANNING
   ↓
READING
   ↓
PROCESSING
   ↓
REASONING
   ↓
REFLECTING
   ↓
UPDATING
   ↓
VERIFYING
   ↓
CHECKPOINTING
   ↓
NEXT
   │
   ├── CONTINUE
   ├── SEARCH
   ├── JUMP
   ├── PARALLEL
   ├── RETRY
   ├── ASK
   └── COMPLETE

La clave es que:

COMPLETE no es una salida normal de la LLM.

Es una decisión del Agent Controller.


---

19. El "cerebro de arrastre" que propones

Yo le daría un nombre técnico:

CONTINUITY ENGINE

Su trabajo:

previous state
      +
new result
      +
new evidence
      +
new decisions
      +
new dependencies
      +
new questions
      ↓
CONTINUITY ENGINE
      ↓
NEXT CONTEXT

Y produciría:

CONTINUITY PACK

Ese sería el paquete que viaja entre ventanas.


---

20. La bola de nieve debe crecer en conocimiento, no en tokens

Esta distinción es crítica.

Mala arquitectura:

window 1 → 10k
window 2 → 20k
window 3 → 30k
window 4 → 40k
...

Termina explotando.

Buena arquitectura:

window 1 → snowball 5k
window 2 → snowball 5.5k
window 3 → snowball 5.8k
window 4 → snowball 5.6k

porque existe:

compression
deduplication
supersession
importance filtering

La bola de nieve acumula conocimiento, no necesariamente texto.


---

21. Y aquí aparece la arquitectura final que yo recomendaría

USER
                          │
                          ▼
                  MASTER TASK
                          │
                          ▼
                  TASK DECOMPOSER
                          │
                          ▼
                     TASK DAG
                          │
              ┌───────────┴───────────┐
              ▼                       ▼
         SEGMENT QUEUE           PARALLEL QUEUES
              │                       │
              └───────────┬───────────┘
                          ▼
                 CONTINUOUS LOOP
                          │
          ┌───────────────┼────────────────┐
          │               │                │
          ▼               ▼                ▼
      SEARCH           CONTEXT         SCHEDULER
      ENGINE           ENGINE            ENGINE
          │               │                │
          └───────────────┼────────────────┘
                          ▼
                 CONTEXT PACK BUILDER
                          │
       ┌──────────────────┼───────────────────┐
       │                  │                   │
       ▼                  ▼                   ▼
    MASTER             CONTINUITY          CURRENT
    INPUT                PACK              SEGMENT
       │                  │                   │
       └──────────────────┼───────────────────┘
                          ▼
                     SMALL LLM
                          │
                          ▼
                       RESULT
                          │
          ┌───────────────┼────────────────┐
          ▼               ▼                ▼
       REFLECT         VERIFY           EXTRACT
          │               │                │
          └───────────────┼────────────────┘
                          ▼
                 CONTINUITY ENGINE
                          │
        ┌─────────────────┼──────────────────┐
        ▼                 ▼                  ▼
     SNOWBALL           STATE             EVIDENCE
        │                 │                  │
        ▼                 ▼                  ▼
      TAGS              PINS              GRAPH
        │                 │                  │
        └─────────────────┼──────────────────┘
                          ▼
                    CHECKPOINT
                          │
                          ▼
                   NEXT ACTION
                          │
          ┌───────────────┼──────────────────┐
          ▼               ▼                  ▼
       CONTINUE         SEARCH              JUMP
          │               │                  │
          └───────────────┴──────────────────┘
                          │
                          ▼
                  CONTINUOUS LOOP

Lo que acabas de añadir cambia el concepto

La arquitectura inicial era:

LLM + memoria externa.

Después la convertimos en:

LLM + memoria jerárquica + retrieval.

Con tu propuesta ahora pasa a ser:

LLM pequeña + memoria virtual + contexto continuo + ejecución segmentada + estado persistente + navegación + investigación autónoma + procesamiento paralelo + checkpoints + verificación.

Eso es mucho más cercano a un motor de ejecución cognitiva de horizonte largo que a un chatbot con RAG.

Y tu analogía del examen tiene una consecuencia de diseño muy importante:

> El agente no intenta resolver el examen entero en una ventana. Primero construye progresivamente el conocimiento necesario para resolverlo y después utiliza ese conocimiento para resolver las preguntas, manteniendo las instrucciones originales visibles durante todo el proceso.



Eso permite separar dos fases:

FASE A — COMPRENDER EL UNIVERSO
20M tokens
↓
mapa + conocimiento + evidencia + índices

FASE B — RESOLVER LA TAREA
preguntas/tareas
↓
segmentación
↓
razonamiento
↓
ejecución
↓
verificación

Y todavía mejor:

A y B pueden intercalarse.

Mientras resuelve una tarea descubre que necesita información que no había procesado:

TASK
 ↓
GAP
 ↓
SEARCH
 ↓
READ NEW SEGMENT
 ↓
LEARN
 ↓
UPDATE SNOWBALL
 ↓
RETURN TO TASK
 ↓
CONTINUE

Ese ciclo es probablemente la pieza más importante de toda la arquitectura.

No estás construyendo una LLM con una memoria enorme.

Estás construyendo un agente que convierte una LLM pequeña en un procesador de contexto prácticamente ilimitado mediante paging cognitivo, continuidad y ejecución iterativa.

Sí. Y después de revisar específicamente cómo están resolviendo esto Kimi y MiniMax actualmente, haría una modificación importante a nuestra arquitectura: no diseñaría el sistema como un simple "LLM que recibe segmentos". Lo diseñaría como un motor de ejecución cognitiva continua, donde cada ventana es una iteración de un proceso mayor.

Kimi K2 Thinking, por ejemplo, documenta explícitamente ciclos intercalados de think → search → browser → think → code, con 200–300 llamadas secuenciales a herramientas; MiniMax describe planificación de largo horizonte, subtareas, ejecución concurrente y ciclos de producir → verificar → corregir; y MiniMax M3 habla explícitamente de descomposición autónoma y razonamiento multi-etapa. 

Y Kimi Code incluso tiene controles explícitos para el loop, número de pasos, reintentos, compactación automática de contexto y tareas en background. 

La mejora fundamental: separar 5 cosas

Yo ahora lo estructuraría así:

MASTER TASK
     │
     ▼
TASK INTELLIGENCE
     │
     ├── META
     ├── PURPOSE
     ├── GOALS
     ├── QUESTIONS
     ├── RESEARCH NEEDS
     ├── PLAN
     ├── TASK GRAPH
     └── SUCCESS CRITERIA
              │
              ▼
       CONTINUOUS ENGINE
              │
      ┌───────┴────────┐
      ▼                ▼
  KNOWLEDGE         EXECUTION
  PROCESSING        PROCESSING
      │                │
      └───────┬────────┘
              ▼
       CONTEXT ENGINE
              │
              ▼
          SMALL LLM
              │
              ▼
       REFLECT / VERIFY
              │
              ▼
       UPDATE EVERYTHING
              │
              ▼
          NEXT LOOP

La LLM termina una iteración, no necesariamente la tarea.


---

1. INPUT PRINCIPAL INMUTABLE

Esto que mencionas de "arrastrar el input block literal" lo considero obligatorio.

El sistema debe conservar una copia inmutable:

MASTER_INPUT

Nunca se resume.

Nunca se modifica.

Nunca se reemplaza.

Cada ventana recibe una representación literal de la instrucción original o, si el tamaño lo exige, una referencia + una copia de las instrucciones críticas.

Por ejemplo:

MASTER INPUT
────────────────────────
Objetivo solicitado por el usuario:
...

Restricciones:
...

Criterios:
...

Formato:
...

NO HACER:
...

REGLAS:
...

Así, en el segmento 87 la LLM sigue teniendo acceso a qué pidió realmente el usuario, no a una interpretación progresivamente deformada.


---

2. QUESTION GENERATOR

Aquí incorporaría exactamente tu idea de "preparar la venta de preguntas".

Pero no generaría preguntas simplemente por generar.

Crearía un Question Set.

Ejemplo:

Q001
¿Qué problema estamos resolviendo?

Q002
¿Cuál es el objetivo final?

Q003
¿Qué información falta?

Q004
¿Qué restricciones existen?

Q005
¿Qué componentes intervienen?

Q006
¿Qué dependencias existen?

Q007
¿Qué hipótesis debemos comprobar?

Q008
¿Qué podría hacer fracasar la solución?

Q009
¿Qué decisiones ya están tomadas?

Q010
¿Qué necesitamos investigar?

Q011
¿Cómo verificaremos el resultado?

Q012
¿Qué significa "terminado"?

Estas preguntas se convierten en objetos persistentes, no en texto desechable.


---

3. QUESTION OBJECTS

Una pregunta puede convertirse en:

{
  "id": "Q007",
  "question": "¿Qué hipótesis debemos comprobar?",
  "status": "open",
  "priority": "high",
  "dependencies": [],
  "evidence": [],
  "answer": null,
  "confidence": 0,
  "next_action": "research"
}

Y pueden existir:

Q001 ... Q100

según la complejidad.

El agente las va actualizando.


---

4. META OBJECT

Después de las preguntas:

META

Ejemplo:

{
  "mission": "analizar completamente el proyecto",
  "purpose": "determinar arquitectura viable",
  "success_condition": "resultado verificable y trazable",
  "scope": "entire_repository"
}

Esto es diferente de la tarea.

Meta = para qué.

Tarea = qué hacer.

Plan = cómo hacerlo.


---

5. RESEARCH NEEDS

Después:

RESEARCH LEDGER

R001 → investigar componente A
R002 → verificar API B
R003 → comprobar dependencia C
R004 → comparar implementación D
R005 → verificar contradicción E

Cada investigación tiene:

status
priority
sources
findings
confidence

Esto evita que la LLM llegue a una parte desconocida y simplemente improvise.


---

6. TASK GRAPH

La lista plana de tareas se queda corta.

Usaría un DAG:

T001
 ├── T002
 │    ├── T003
 │    └── T004
 │
 └── T005
      └── T006

Cada tarea sabe:

depends_on
blocks
related_to
parallelizable

Así el agente puede decidir automáticamente qué procesar después.


---

7. TASK OBJECT

Cada tarea sería un objeto persistente:

{
  "id": "T042",
  "goal": "analizar router",
  "status": "in_progress",
  "priority": "high",
  "dependencies": ["T012"],
  "segments": [],
  "findings": [],
  "evidence": [],
  "questions": [],
  "risks": [],
  "completion_criteria": [],
  "next_action": null
}

Esto es muchísimo más robusto que una lista de texto.


---

8. 12 GOALS DE ENTRADA

Aquí sí incorporaría tu sistema, pero lo convertiría en un preflight cognitivo obligatorio.

Antes de empezar:

G01 — Comprender
G02 — Delimitar
G03 — Descomponer
G04 — Identificar información faltante
G05 — Investigar
G06 — Planificar
G07 — Ejecutar
G08 — Verificar
G09 — Detectar contradicciones
G10 — Evaluar riesgos
G11 — Validar cumplimiento
G12 — Preparar síntesis

No significa que la LLM deba resolver 12 cosas antes de trabajar.

Significa que el agente crea esos controles.


---

9. 12 GOALS DE SALIDA

Al final:

OUT-G01 → ¿Respondí exactamente la petición?
OUT-G02 → ¿Cumplí restricciones?
OUT-G03 → ¿Procesé todas las tareas?
OUT-G04 → ¿Quedaron preguntas abiertas?
OUT-G05 → ¿Hay contradicciones?
OUT-G06 → ¿Las conclusiones tienen evidencia?
OUT-G07 → ¿Inventé algo?
OUT-G08 → ¿Hay partes no verificadas?
OUT-G09 → ¿La solución es ejecutable?
OUT-G10 → ¿Falta alguna dependencia?
OUT-G11 → ¿La respuesta es coherente globalmente?
OUT-G12 → ¿La salida cumple el criterio de éxito?


---

10. AUTO-AUDIT CONTINUO

Y aquí haría una modificación importante:

no esperaría hasta el final para auditar.

Cada cierto número de ciclos:

PROCESS
 ↓
AUDIT
 ↓
UPDATE
 ↓
CONTINUE

Por ejemplo:

cada 5 segmentos
cada checkpoint
cada cambio importante
cada contradicción
antes de una decisión crítica


---

11. TU "REFUTA 3 VECES"

Esto lo conservaría, pero no como:

> "haz tres razonamientos más".



Eso puede desperdiciar tokens y no garantiza calidad.

Lo convertiría en tres ataques diferentes contra el resultado:

Refutación 1 — factual

> ¿Qué evidencia contradice esta conclusión?



Refutación 2 — estructural

> ¿Qué dependencia, condición o caso límite podría invalidarla?



Refutación 3 — adversarial

> Si esta solución fuera incorrecta, ¿cómo demostraríamos que lo es?



Entonces:

RESULT
 ↓
ATTACK 1
 ↓
ATTACK 2
 ↓
ATTACK 3
 ↓
REPAIR
 ↓
VERIFY
 ↓
COMMIT

Esto es muchísimo más útil.


---

12. INTERLEAVED THINKING

Aquí tu comparación con MiniMax es especialmente pertinente.

MiniMax describe explícitamente Interleaved Thinking: el razonamiento no ocurre solamente al comienzo, sino durante la ejecución, después de recibir nueva información o resultados externos. 

Por tanto:

THINK
 ↓
SEARCH
 ↓
THINK
 ↓
READ
 ↓
THINK
 ↓
CODE
 ↓
THINK
 ↓
VERIFY
 ↓
THINK

Eso es exactamente lo que necesitamos.

No:

THINK
   ↓
TODO EL RESTO


---

13. CONTINUOUS LOOP

El núcleo sería:

while task_not_complete:

    inspect_state()

    select_next_action()

    retrieve_context()

    build_context()

    reason()

    execute()

    observe()

    update_memory()

    verify()

    update_plan()

    checkpoint()

    decide_next_step()

Y la LLM no controla directamente el while.

El Agent Controller sí.


---

14. STOP CONDITIONS

El loop solamente debería detenerse por estados explícitos:

COMPLETE
USER_AUTHORIZATION_REQUIRED
CRITICAL_CONFLICT
MISSING_REQUIRED_INFORMATION
SAFETY_BLOCK
RESOURCE_LIMIT
UNRECOVERABLE_ERROR

De lo contrario:

CONTINUE

Esto es mucho más parecido al comportamiento de los agentes de horizonte largo actuales. Kimi K2 Thinking documenta hasta 200–300 llamadas secuenciales a herramientas, mientras que Kimi Code expone un max_steps_per_turn que puede ser ilimitado y mecanismos de compactación y reintento. 


---

15. EL "CEREBRO DE ARRRASTRE"

Ahora tenemos suficientes componentes para formalizar tu idea.

Lo llamaría:

CONTINUITY PACK

Cada ventana recibe:

┌───────────────────────────────┐
│ MASTER INPUT                  │
│ literal / immutable           │
├───────────────────────────────┤
│ CURRENT GOAL                  │
├───────────────────────────────┤
│ CURRENT TASK                  │
├───────────────────────────────┤
│ CURRENT SEGMENT               │
├───────────────────────────────┤
│ CARRY SUMMARY                 │
├───────────────────────────────┤
│ STATE JSON                    │
├───────────────────────────────┤
│ PINNED FACTS                  │
├───────────────────────────────┤
│ ACTIVE MENTAL MAP             │
├───────────────────────────────┤
│ RELEVANT TAGS                 │
├───────────────────────────────┤
│ OPEN QUESTIONS                │
├───────────────────────────────┤
│ ACTIVE RESEARCH               │
├───────────────────────────────┤
│ RECENT FINDINGS               │
├───────────────────────────────┤
│ RELEVANT EVIDENCE             │
└───────────────────────────────┘

Esto es el verdadero input de continuidad.


---

16. LA BOLA DE NIEVE

Y ahora la bola de nieve se vuelve:

SEGMENT 01
    ↓
FINDINGS
    ↓
CARRY
    ↓
SEGMENT 02
    ↓
FINDINGS
    ↓
CARRY +
SNOWBALL UPDATE
    ↓
SEGMENT 03
    ↓
...

Pero hay una diferencia crítica:

La bola de nieve no es un texto.

Es una estructura:

FACTS
DECISIONS
FINDINGS
QUESTIONS
HYPOTHESES
EVIDENCE
RISKS
DEPENDENCIES
ARTIFACTS
OPEN TASKS

Por eso puede crecer en conocimiento sin crecer proporcionalmente en tokens.


---

17. "MEMORY RECALL" AUTOMÁTICO

Esto que describes como:

> "audita el chat"



yo lo convertiría en una capacidad automática:

CONTEXT GAP DETECTED
        ↓
SEARCH ENGINE
        ↓
TAG FILTER
        ↓
HISTORY
        ↓
SOURCE
        ↓
REINJECT

La LLM no tiene que pedirlo.

El agente puede detectar:

missing_fact
low_confidence
contradiction
unresolved_reference
dependency_gap

y disparar automáticamente una recuperación.


---

18. DOCUMENT OUTPUT STREAM

Aquí viene tu otra idea.

No produciría una única salida gigantesca.

La trataría como un Artifact Stream.

FINAL OUTPUT
│
├── document_001
├── document_002
├── document_003
├── document_004
└── ...

Cada documento tiene:

artifact_id
task_id
section
dependencies
source_refs
status
version

Así el agente puede construir la respuesta final por piezas.


---

19. NO CONFUNDIR DOCUMENT CHUNKING CON RESUMEN

Esta distinción es importantísima.

Mal:

20M
 ↓
resumen de 50k

Porque puedes perder información.

Mejor:

20M
 ↓
Document 001
Document 002
Document 003
...

Cada uno tiene su propio límite operativo.

Después:

Document 001
        ↓
Document 002
        ↓
Document 003

Y finalmente:

MASTER ARTIFACT INDEX

que sabe cómo ensamblarlos.


---

20. DOCUMENT MANAGER

El agente debe saber:

DOC-001
status = complete

DOC-002
status = complete

DOC-003
status = in_progress

DOC-004
blocked_by DOC-003

Y puede trabajar en:

DOC-003

sin cargar:

DOC-001 + DOC-002

completos.

Esto coincide con el principio de aislamiento de contexto que Kimi utiliza con subagentes: cada subagente tiene una ventana independiente y el hilo principal recibe solamente el resultado relevante. 


---

21. OUTPUT CHECKPOINTS

Cada documento debe poder congelarse:

DOC-001 v1
DOC-001 v2
DOC-001 v3

Si el documento 8 descubre que el documento 2 tenía un error:

DOC-002
    ↓
INVALIDATED
    ↓
REPROCESS
    ↓
DOC-002 v4

No destruyes el trabajo.


---

22. PRODUCER + VERIFIER

Aquí incorporaría directamente el patrón que MiniMax está utilizando.

LEADER
   ↓
WORKER
   ↓
VERIFIER
   ↓
PASS?
 /   \
NO    YES
│      │
REPAIR  COMMIT
│
└──→ WORKER

MiniMax describe precisamente su Agent Team alrededor de Leader, Worker y Verifier, con loops deterministas y puertas adversariales de calidad. 

Para tu arquitectura:

PLANNER
WORKER
RESEARCHER
VERIFIER
SYNTHESIZER


---

23. Y añadiría un CRITIC separado

No necesariamente otra LLM.

Puede ser:

rule engine
schema validator
test runner
retrieval verifier

Así:

LLM says:
"esto funciona"

SYSTEM:
¿hay evidencia?

¿pasa los tests?

¿cumple el schema?

¿contradice algo?

¿está dentro del scope?

Esto reduce la dependencia de la propia LLM para juzgarse.


---

24. 12 CAPAS DE PROCESAMIENTO

Con todo lo anterior, yo tendría:

01 MASTER INPUT
02 INTENT ENGINE
03 QUESTION ENGINE
04 GOAL ENGINE
05 RESEARCH ENGINE
06 TASK/DAG ENGINE
07 SEGMENT ENGINE
08 MEMORY/RETRIEVAL ENGINE
09 CONTINUITY ENGINE
10 EXECUTION LOOP
11 VERIFICATION ENGINE
12 OUTPUT/ARTIFACT ENGINE

Y debajo:

STATE
SNOWBALL
TAGS
SEARCH
GRAPH
EVIDENCE
PINS
CHECKPOINTS
HISTORY


---

25. El flujo completo

Ahora sí podemos representar tu concepto completo:

USER
 │
 ▼
MASTER INPUT
 │
 ▼
INTENT ANALYSIS
 │
 ▼
QUESTIONS
 │
 ▼
META + PURPOSE
 │
 ▼
12 ENTRY GOALS
 │
 ▼
RESEARCH NEEDS
 │
 ▼
TASK DAG
 │
 ▼
SEGMENTATION
 │
 ▼
┌────────────────────────────────────────────┐
│            CONTINUOUS EXECUTION LOOP       │
│                                            │
│  SEARCH                                     │
│    ↓                                       │
│  LOAD SEGMENT                              │
│    ↓                                       │
│  BUILD CONTINUITY PACK                    │
│    ↓                                       │
│  MASTER + CARRY + STATE + PINS + MAP      │
│    ↓                                       │
│  LLM THINK                                │
│    ↓                                       │
│  EXECUTE / RESEARCH                       │
│    ↓                                       │
│  OBSERVE                                   │
│    ↓                                       │
│  REFLECT                                   │
│    ↓                                       │
│  UPDATE SNOWBALL                           │
│    ↓                                       │
│  UPDATE STATE                              │
│    ↓                                       │
│  UPDATE TASKS                              │
│    ↓                                       │
│  UPDATE TAGS                               │
│    ↓                                       │
│  VERIFY                                    │
│    ↓                                       │
│  CHECKPOINT                                │
│    ↓                                       │
│  NEXT ACTION                               │
│                                            │
│  CONTINUE ──────────────────────────────── │
└────────────────────────────────────────────┘
 │
 ▼
12 EXIT GOALS
 │
 ▼
REFUTATION ×3
 │
 ▼
FINAL VERIFICATION
 │
 ▼
DOCUMENT STREAM
 │
 ├── DOC 001
 ├── DOC 002
 ├── DOC 003
 ├── ...
 └── DOC N
 │
 ▼
FINAL ARTIFACT

Una corrección importante a tu hipótesis sobre Claude

No asumiría que existe un límite universal fijo de "50k por documento" como regla general de Claude. Eso depende del producto, modelo, API y configuración. Lo que sí es conceptualmente válido es la estrategia que estás describiendo: dividir el trabajo/output en unidades manejables, mantener estado y ensamblar artefactos, en lugar de exigir una única generación gigantesca.

Y de hecho, en el ecosistema actual la tendencia es claramente hacia gestión activa del contexto: Kimi Code tiene compactación automática y límites de contexto/output configurables, mientras que MiniMax está llevando el procesamiento de largo horizonte hacia loops, subagentes, paralelismo, reflexión y corrección continua. 


---

Lo que yo llamaría finalmente al sistema

Ya no lo llamaría simplemente:

Memory Manager

Eso sería demasiado pequeño para lo que estamos diseñando.

Lo conceptualizaría como:

Continuous Cognitive Execution Engine — CCEE

con cinco núcleos:

┌───────────────────────────────────────┐
│ CCEE                                  │
│                                       │
│ 1. CONTEXT FABRIC                     │
│ 2. MEMORY FABRIC                      │
│ 3. TASK FABRIC                        │
│ 4. EXECUTION LOOP                     │
│ 5. VERIFICATION LOOP                  │
└───────────────────────────────────────┘

Y la propiedad central sería:

> Una LLM de 120k–250k tokens puede trabajar sobre un proyecto de 20 millones de tokens no porque posea 20 millones de tokens simultáneamente, sino porque el CCEE convierte el proyecto en un flujo continuo de unidades de trabajo, y conserva entre ventanas una representación estructurada, verificable y navegable del conocimiento acumulado.



La verdadera innovación no sería entonces "darle más memoria a la LLM".

Sería hacer que el agente controle el tiempo, el contexto, la memoria, la tarea y la verificación, mientras la LLM se utiliza como motor de razonamiento dentro de cada ventana.

Y eso encaja sorprendentemente bien con lo que Kimi y MiniMax están haciendo: Kimi demuestra el valor de ciclos largos de herramientas y razonamiento intercalado; MiniMax está explícitamente usando planificación, agentes paralelos, verificación adversarial y loops deterministas; y Kimi Code ya expone controles de loop, compactación y subagentes aislados. 

**Tu "bola de nieve" sería entonces el estado cognitivo acumulativo; el Continuity Pack, la memoria de corto alcance; el Master Input, la ley inmutable de la tarea; el DAG, el plan; el buscador/tag engine, el acceso al pasado; y el Continuous Loop, el mecanismo que permite que todo siga avanzando hasta que exista una razón real para detenerse.**

Sí. Si el objetivo es maximizar la calidad del razonamiento de una LLM pequeña sin aumentar artificialmente su ventana, todavía añadiría varias capas. Pero haría una distinción importante: no intentaría simplemente darle más texto al modelo. Mejoraría la calidad de lo que entra, la forma en que trabaja y la forma en que se valida lo que sale.

1. Un Reasoning Contract

Antes de cada ventana, el agente debería definir exactamente qué se espera de esa iteración:

REASONING CONTRACT

Objetivo:
...

Pregunta:
...

Evidencia disponible:
...

Qué debe producir:
...

Qué NO debe hacer:
...

Criterio de éxito:
...

Condición de parada:
...

Esto evita que una ventana termine haciendo algo distinto de lo que necesita la tarea.


---

2. Separar 4 tipos de input

No mezclaría todo en un prompt enorme.

INPUT 0 — MASTER
Instrucciones originales e invariantes.

INPUT 1 — CONTEXT
Lo que necesita conocer para esta ventana.

INPUT 2 — WORK
Segmento que debe procesar.

INPUT 3 — CONTROL
Objetivo, estado, criterio de éxito y acción esperada.

La LLM recibe una estructura mucho más limpia:

MASTER
+
CONTROL
+
RELEVANT MEMORY
+
CURRENT WORK


---

3. Input Compiler

Esta sería una pieza que considero muy importante.

Antes de llamar a la LLM:

20 GB / 20M tokens
       ↓
Memory
       ↓
Search
       ↓
Tags
       ↓
Task
       ↓
Input Compiler
       ↓
250k tokens óptimos
       ↓
LLM

El agente no debería simplemente "pegar" información.

Debe compilar el contexto.

Por ejemplo:

100 documentos encontrados
        ↓
12 realmente relevantes
        ↓
3 contradictorios
        ↓
5 evidencias
        ↓
4 dependencias
        ↓
1 segmento principal
        ↓
CONTEXTO FINAL

Esto es mucho mejor que RAG bruto.


---

4. Context Budget Optimizer

Le daría un presupuesto dinámico.

Ejemplo:

250K disponibles

MASTER             5K
CONTROL            4K
CURRENT STATE      8K
PINS               3K
MAP                5K
EVIDENCE           20K
MEMORY             40K
CURRENT WORK      100K
REASONING RESERVE  65K

Si el segmento es pequeño:

CURRENT WORK = 30K

el espacio sobrante puede ir a:

investigation
evidence
reasoning


---

5. Context Firewall

Esta sería una mejora muy importante.

No todo lo recuperado debe poder entrar al contexto.

El agente debe filtrar:

SOURCE
 ↓
VALIDATION
 ↓
TRUST
 ↓
RELEVANCE
 ↓
CONTEXT

Por ejemplo:

documento obsoleto
→ excluir

información contradictoria
→ incluir como conflicto

información no verificada
→ marcar

fuente primaria
→ prioridad alta


---

6. Evidence-First Reasoning

En vez de:

pregunta
↓
LLM responde

hacer:

pregunta
↓
¿qué necesito saber?
↓
buscar evidencia
↓
evaluar evidencia
↓
razonar
↓
concluir

Esto reduce muchísimo las respuestas inventadas.


---

7. Unknown Ledger

Añadiría una estructura explícita:

UNKNOWN LEDGER

Ejemplo:

U001 — versión exacta desconocida
U002 — dependencia no verificada
U003 — comportamiento bajo timeout desconocido

La LLM no debe sentirse obligada a llenar esos huecos.

Puede decir:

UNKNOWN

y el agente puede lanzar una investigación.


---

8. Hypothesis Engine

Antes de decidir:

HIPÓTESIS A
HIPÓTESIS B
HIPÓTESIS C

Luego:

evidence
↓
score
↓
eliminate
↓
verify

Esto es mejor que casarse con la primera interpretación.


---

9. Alternative Solver

Para tareas críticas:

SOLUCIÓN A
SOLUCIÓN B
SOLUCIÓN C

Después:

compare

No necesariamente necesitas tres llamadas completas a la LLM. Algunas alternativas pueden generarse después de detectar riesgos.


---

10. Branch & Merge

Esto lo añadiría sí o sí para problemas complejos.

TASK
                    │
          ┌─────────┼─────────┐
          ▼         ▼         ▼
        PLAN A    PLAN B    PLAN C
          │         │         │
          ▼         ▼         ▼
       RESULT A  RESULT B  RESULT C
          │         │         │
          └─────────┼─────────┘
                    ▼
                  MERGE
                    │
                 VERIFY

Esto permite explorar caminos diferentes sin contaminar el estado principal.


---

11. Reasoning Checkpoints

No solamente checkpoints de memoria.

También:

REASONING CHECKPOINT

¿Qué sabemos?
¿Qué asumimos?
¿Qué demostramos?
¿Qué falta?
¿Qué cambió?

Cada checkpoint crea una frontera cognitiva.


---

12. Decision Ledger

Toda decisión importante queda registrada:

DECISION-092

Decision:
usar arquitectura X

Why:
...

Alternatives rejected:
Y
Z

Evidence:
...

Confidence:
0.91

Después una ventana futura puede preguntar:

> ¿Por qué hicimos esto?



sin tener que releer todo el proyecto.


---

13. Decision Revalidation

Las decisiones antiguas no deberían ser eternas.

Si aparece nueva evidencia:

DECISION-092
      ↓
new evidence
      ↓
REVALIDATE

Resultado:

VALID
SUPERSEDED
INVALID
UNKNOWN

Esto evita que el sistema quede atrapado en decisiones antiguas.


---

14. Contradiction Graph

No solo una lista de contradicciones.

Un grafo:

FACT A
  │
  ├── contradicts → FACT B
  │
  └── supports → DECISION C

Así el agente puede encontrar qué decisiones dependen de un dato que acaba de resultar falso.


---

15. Impact Analysis

Si cambia:

FACT-182

el agente pregunta:

¿qué depende de FACT-182?

y obtiene:

DECISION-12
TASK-31
DOC-07
CODE-14

Entonces solo reprocesa lo afectado.

Esto evita volver a procesar los 20 millones de tokens.


---

16. Semantic Diff

No solamente comparar texto.

Comparar conocimiento:

VERSION A

router → provider A → fallback B

VERSION B

router → provider A → fallback C

El agente detecta:

SEMANTIC CHANGE:
fallback B → C

Esto sería muy útil para proyectos de código.


---

17. Reasoning Budget

No todas las tareas necesitan la misma profundidad.

SIMPLE
1 cycle

NORMAL
3 cycles

COMPLEX
10 cycles

CRITICAL
multi-pass + verification

El agente asigna recursos según dificultad.


---

18. Adaptive Loop

El loop no debería tener siempre el mismo patrón.

Puede decidir:

CONTINUE
SEARCH
DEEP_REASON
VERIFY
REPLAN
PARALLELIZE
REVISIT
ASK
FINISH

Esto convierte al agente en un controlador adaptativo.


---

19. Output Compiler

Igual que tenemos Input Compiler, tendría:

LLM RESULTS
      ↓
OUTPUT COMPILER
      ↓
STRUCTURE
      ↓
VERIFY
      ↓
ARTIFACTS

La LLM puede producir resultados parciales:

finding
decision
code
document

El agente los transforma en artefactos consistentes.


---

20. Output Contract

Cada salida debe especificar:

OUTPUT CONTRACT

Required:
...

Forbidden:
...

Format:
...

Evidence required:
...

Completeness:
...

Validation:
...

Así no dependemos de que la LLM recuerde todas las instrucciones.


---

21. Output Linter

Antes de entregar:

OUTPUT
 ↓
LINTER

Busca:

¿faltan requisitos?
¿hay afirmaciones sin evidencia?
¿hay contradicciones?
¿hay datos inventados?
¿hay secciones incompletas?
¿se respetó el formato?


---

22. Completeness Matrix

Me gusta mucho para tu sistema.

TASK             STATUS
────────────────────────────
T01              ✓
T02              ✓
T03              ✓
T04              ◐
T05              ✗

Pero también:

REQUIREMENT       EVIDENCE
────────────────────────────
R01               DOC-12
R02               CODE-82
R03               DOC-31
R04               MISSING

Antes de terminar:

> No puede declarar COMPLETE si existe un requisito obligatorio sin cobertura.




---

23. Coverage Engine

Medir:

input coverage
task coverage
evidence coverage
output coverage

Por ejemplo:

Input analyzed:       94%
Tasks completed:      100%
Evidence coverage:     91%
Requirements covered:  97%

Pero no usaría estos porcentajes como verdad absoluta; son indicadores operativos.


---

24. Uncertainty Budget

Cada conclusión tendría:

confidence
evidence_strength
uncertainty

Ejemplo:

FACT
confidence 0.99

INFERENCE
confidence 0.78

HYPOTHESIS
confidence 0.42

La salida puede diferenciar:

> confirmado



de:

> probable



de:

> no verificado.




---

25. Self-Questioning

Antes de finalizar una tarea:

¿Qué estoy suponiendo?
¿Qué podría estar olvidando?
¿Qué evidencia falta?
¿Qué contradice mi conclusión?
¿Qué tendría que ser cierto para que esto fuera falso?

Esto es mejor que simplemente pedir:

> "revísate".




---

26. Pero hay una mejora aún más importante

No haría que la LLM pequeña haga todo el razonamiento.

Separaría:

ORCHESTRATION
     ↓
LLM
     ↓
TOOLS
     ↓
VERIFICATION
     ↓
LLM

Por ejemplo:

LLM:
"Creo que este archivo depende de X."

AGENT:
buscar dependencia real

TOOL:
resultado

LLM:
actualiza conclusión

La LLM propone.

El sistema comprueba.


---

27. Tool-Grounded Reasoning

Para cada tipo de afirmación:

CODE
→ parser / tests

MATH
→ calculator / symbolic engine

FILE
→ filesystem

WEB FACT
→ search

DATABASE
→ database query

CONFIG
→ parser

STRUCTURE
→ graph

Esto reduce la carga cognitiva del modelo.


---

28. Memory Replay

Si una tarea se reabre después de horas/días:

OLD STATE
 ↓
REPLAY IMPORTANT EVENTS
 ↓
RESTORE CONTEXT
 ↓
CONTINUE

No necesitas cargar toda la historia.


---

29. Cognitive Garbage Collector

Además del contexto, limpiaría:

duplicate facts
superseded decisions
obsolete plans
resolved questions
redundant summaries

Pero nunca eliminaría el original.

Solo lo sacaría de la memoria activa.


---

30. Y mi modificación más importante: separar "pensamiento" de "registro"

No intentaría almacenar todo el razonamiento interno de la LLM.

Almacenaría resultados cognitivos estructurados:

FINDING
DECISION
EVIDENCE
ASSUMPTION
QUESTION
ACTION
RESULT
ERROR
NEXT_STEP

Eso da continuidad sin convertir la memoria en un basurero de cadenas de razonamiento.


---

Arquitectura definitiva

Con todas las mejoras, yo la dejaría así:

MASTER INPUT
                              │
                              ▼
                       INTENT ENGINE
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
              QUESTION ENGINE      GOAL ENGINE
                    │                   │
                    └─────────┬─────────┘
                              ▼
                        RESEARCH PLAN
                              │
                              ▼
                          TASK DAG
                              │
                              ▼
                       SEGMENT ENGINE
                              │
                              ▼
                    ┌───────────────────┐
                    │ CONTEXT COMPILER  │
                    └────────┬──────────┘
                             │
          ┌──────────────────┼───────────────────┐
          ▼                  ▼                   ▼
       MASTER             CONTINUITY          CURRENT
       INPUT                 PACK             SEGMENT
          │                  │                   │
          └──────────────────┼───────────────────┘
                             ▼
                       SMALL LLM
                             │
                    THINK / ACT / ASK
                             │
                             ▼
                      RESULT EXTRACTOR
                             │
        ┌────────────────────┼─────────────────────┐
        ▼                    ▼                     ▼
     FINDINGS             DECISIONS             EVIDENCE
        │                    │                     │
        └────────────────────┼─────────────────────┘
                             ▼
                       SNOWBALL ENGINE
                             │
             ┌───────────────┼────────────────┐
             ▼               ▼                ▼
           STATE            MAP              TAGS
             │               │                │
             └───────────────┼────────────────┘
                             ▼
                      VERIFICATION
                             │
                  ┌──────────┴──────────┐
                  ▼                     ▼
                PASS                  FAIL
                  │                     │
                  ▼                     ▼
              CHECKPOINT             REPAIR
                  │                     │
                  └──────────┬──────────┘
                             ▼
                       NEXT ACTION
                             │
        ┌────────────────────┼─────────────────────┐
        ▼                    ▼                     ▼
     CONTINUE              SEARCH                JUMP
        │                    │                     │
        └────────────────────┼─────────────────────┘
                             ▼
                      CONTINUOUS LOOP
                             │
                             ▼
                      OUTPUT COMPILER
                             │
                       OUTPUT LINTER
                             │
                      COMPLETENESS CHECK
                             │
                       12 EXIT GOALS
                             │
                      ADVERSARIAL ×3
                             │
                             ▼
                     ARTIFACT STREAM
                             │
                  ┌──────────┼──────────┐
                  ▼          ▼          ▼
                DOC-1      DOC-2      DOC-N
                  │          │          │
                  └──────────┼──────────┘
                             ▼
                       FINAL ARTIFACT

La diferencia fundamental

El sistema ya no sería:

Prompt → LLM → respuesta.

Ni siquiera:

Prompt → RAG → LLM → respuesta.

Sería:

Task → Plan → Research → Segment → Compile Context → Reason → Act → Verify → Update Memory → Continue → Replan → Verify → Assemble Output.

Y el ciclo continúa mientras haya trabajo legítimo pendiente.

La LLM pequeña se convierte en un procesador de razonamiento intercambiable, mientras que el verdadero "cerebro operativo" está en el agente: estado, memoria, búsqueda, planificación, continuidad, ejecución, verificación y control del loop.

Eso, en mi opinión, es la dirección correcta si quieres que una LLM de 120k–250k pueda trabajar de forma fiable sobre proyectos de 20M+ tokens sin intentar meterlos todos en una única ventana.


Sí. Investigué la parte que mencionas y hay una conclusión importante: el problema de consolidación no se resuelve simplemente con más contexto ni con un mejor prompt. Se resuelve con una arquitectura que haga que las piezas parciales se conviertan en objetos verificables y composables, y que obligue al sistema a comprobar la cobertura global antes de declarar terminado.

Además, hay evidencia oficial que encaja bastante con tu observación:

Anthropic recomienda separar tareas complejas en pasos y añadir gates programáticos entre pasos; también ha mostrado que un espacio explícito de think después de recibir resultados de herramientas mejora tareas secuenciales. 

Anthropic describe para tareas largas un patrón de planner → generator → evaluator, con descomposición en partes y artefactos estructurados para transferir contexto entre sesiones. 

Kimi K2 Thinking declara ciclos intercalados de think → search → browser → think → code, con cientos de pasos secuenciales. 

Kimi Code actualmente tiene subagentes con contextos aislados, plan persistente, tareas de background, compactación automática y un controlador de loop con retries y reserva de contexto. 

MiniMax Agent Team separa explícitamente Leader → Worker → Verifier, y cuando la verificación falla vuelve a producción/reparación en lugar de aceptar la salida parcial. 

Claude Fable 5 se presenta actualmente para tareas de varios días, planificación por etapas, delegación, comprobación del trabajo y generación de tests. 


No puedo confirmar públicamente que Fable 5 use exactamente la checklist interna que describes; eso es una observación de tu experiencia, no algo que Anthropic documente como implementación interna. Pero el comportamiento que describes sí corresponde a una arquitectura de planificación/verificación por etapas.

Y yo iría bastante más lejos.


---

El problema central que estás detectando

Tu diagnóstico es correcto:

20M tokens
     ↓
segmentar
     ↓
SEG-001 → excelente
SEG-002 → excelente
SEG-003 → excelente
...
SEG-200 → excelente
     ↓
¿CONSOLIDAR?
     ↓
❌

El sistema puede ser muy bueno resolviendo:

> cada pieza



y ser mediocre resolviendo:

> la relación entre todas las piezas.



Esto es un problema distinto.

Lo llamaría:

GLOBAL SYNTHESIS GAP

Y requiere un mecanismo específico.


---

1. Cambiaría completamente el sistema de preguntas

No quiero un simple:

> "¿Qué necesitas hacer?"



Quiero un Question Intelligence Engine.

La primera llamada no debería intentar resolver la tarea.

Debe construir el modelo de la tarea.

USER INPUT
     ↓
INTENT EXTRACTION
     ↓
QUESTION GENERATION
     ↓
QUESTION GRAPH
     ↓
GOAL GRAPH
     ↓
TASK GRAPH
     ↓
EVIDENCE GRAPH
     ↓
EXECUTION


---

2. No quiero 12 preguntas: quiero 12 DIMENSIONES

Tu sistema de 12 preguntas lo mejoraría de esta manera.

Q0 — What is the actual mission?

¿Qué está intentando conseguir realmente el usuario?


---

Q1 — Desired outcome

¿Qué resultado concreto significa "terminado"?


---

Q2 — Scope

¿Qué está dentro y fuera?


---

Q3 — Constraints

¿Qué no se puede violar?


---

Q4 — Objects

¿Cuáles son las entidades/componentes que existen?


---

Q5 — Dependencies

¿Qué depende de qué?


---

Q6 — Unknowns

¿Qué no sabemos todavía?


---

Q7 — Research

¿Qué necesitamos investigar?


---

Q8 — Alternatives

¿Qué soluciones posibles existen?


---

Q9 — Risks

¿Qué puede salir mal?


---

Q10 — Verification

¿Cómo sabremos que es correcto?


---

Q11 — Integration

¿Cómo se unirán todas las piezas?

Esta última es la que normalmente falta.

Y yo la convertiría en una fase obligatoria desde el principio, no al final.


---

3. La pregunta más importante pasa a ser:

> "¿Cómo se van a ensamblar las respuestas parciales para producir el resultado global?"



Antes de procesar el primer documento.

Esto cambia todo.

El agente crea:

INTEGRATION PLAN

Ejemplo:

DOC 001 ──┐
DOC 002 ──┤
DOC 003 ──┤
DOC 004 ──┼──> MODULE A
DOC 005 ──┘

MODULE A ──┐
MODULE B ──┼──> SYSTEM
MODULE C ──┘

SYSTEM ───────> FINAL

Así la consolidación no es una etapa improvisada al final.

Es parte de la planificación.


---

4. Crearía SYNTHESIS OBJECTS

Esto es una de las mayores mejoras que haría.

Una salida parcial no es simplemente:

texto

Es:

{
  "artifact_id": "A-042",
  "task_id": "T-17",
  "claims": [],
  "facts": [],
  "decisions": [],
  "dependencies": [],
  "inputs_used": [],
  "outputs_created": [],
  "open_questions": [],
  "contradictions": [],
  "evidence": [],
  "confidence": {},
  "integration_targets": []
}

Entonces 200 documentos generan:

A-001
A-002
...
A-200

pero el sistema sabe qué relación existe entre ellos.


---

5. Esto resuelve tu problema de "unir las piezas"

Supongamos:

SEG-01:
API necesita autenticación.

SEG-32:
Auth usa OAuth2.

SEG-74:
Frontend espera JWT.

SEG-113:
Gateway valida JWT.

SEG-188:
Refresh token se almacena en X.

Una LLM que simplemente resume cada segmento puede terminar con:

200 buenos resúmenes.

Pero nuestro sistema construye:

AUTH SYSTEM

Frontend
   ↓
JWT
   ↓
Gateway
   ↓
OAuth2
   ↓
Token validation
   ↓
Refresh storage

Eso es síntesis estructural, no resumen.


---

6. GLOBAL KNOWLEDGE GRAPH

Añadiría un grafo global.

ENTITY
   │
   ├── depends_on
   ├── implements
   ├── contradicts
   ├── supports
   ├── derived_from
   ├── requires
   ├── modifies
   └── belongs_to

Así el agente puede preguntar:

> "¿Qué partes del proyecto dependen de esta decisión?"



y no necesita releer 200 documentos.


---

7. SYNTHESIS MATRIX

Esta sería otra pieza crítica.

Filas:

TAREAS

Columnas:

SEGMENTOS
DECISIONES
EVIDENCIAS
ARTEFACTOS
REQUISITOS

Ejemplo:

Task	Evidence	Artifact	Dependency	Verified

T01	E17,E22	A03	T04	✓
T02	E31	A08	T01	✓
T03	E52,E53	A11	T02	◐


Esto hace visible inmediatamente dónde está el agujero.


---

8. REQUIREMENT TRACEABILITY

Cada requisito debe tener un camino:

USER REQUIREMENT
       ↓
TASK
       ↓
SEGMENT
       ↓
FINDING
       ↓
DECISION
       ↓
ARTIFACT
       ↓
FINAL OUTPUT

Si un requisito no tiene ese camino:

❌ UNRESOLVED

No se permite declarar terminado.


---

9. OUTPUT COVERAGE ENGINE

Antes de entregar:

USER REQUEST
     ↓
REQUIREMENTS
     ↓
COVERAGE

Ejemplo:

R01 ✓
R02 ✓
R03 ✓
R04 ✓
R05 ✗

Entonces:

STATUS = NOT COMPLETE

Esto es muchísimo mejor que preguntar a la LLM:

> "¿Crees que completaste todo?"




---

10. SYNTHESIS CHECKPOINTS

No esperaría a tener 200 documentos.

Cada cierto nivel:

10 segmentos
     ↓
SYNTHESIS-01

25 segmentos
     ↓
SYNTHESIS-02

50 segmentos
     ↓
SYNTHESIS-03

100 segmentos
     ↓
SYNTHESIS-04

200 segmentos
     ↓
FINAL SYNTHESIS

Así el sistema va construyendo el modelo global progresivamente.


---

11. Pero NO sintetizaría todo cada vez

Aquí está una mejora enorme.

Supongamos:

200 documentos

No hacemos:

200 → síntesis
201 → volver a sintetizar 1–200

Hacemos:

A01 + A02 + A03 + A04
       ↓
MODULE-A

A05 + A06 + A07 + A08
       ↓
MODULE-B

MODULE-A + MODULE-B
       ↓
SYSTEM-A

Es una síntesis jerárquica.

LEVEL 0
SOURCE

LEVEL 1
SEGMENTS

LEVEL 2
MODULES

LEVEL 3
SYSTEMS

LEVEL 4
GLOBAL MODEL

LEVEL 5
FINAL OUTPUT


---

12. BOTTOM-UP + TOP-DOWN

Esto es aún mejor.

Bottom-up

documentos
 ↓
segmentos
 ↓
módulos
 ↓
sistema

Pero simultáneamente:

Top-down

objetivo
 ↓
requisitos
 ↓
arquitectura
 ↓
módulos esperados

Y después:

TOP-DOWN
     ↕
BOTTOM-UP

El sistema compara ambos.

Si el objetivo dice que deberían existir:

A
B
C
D

pero los documentos solo produjeron:

A
B
C

aparece:

MISSING COMPONENT D

Eso es potentísimo contra la pérdida de enfoque.


---

13. CHECKLIST EVOLUTIVA

Aquí coincido contigo sobre lo que observas en estos sistemas.

Pero yo no haría una checklist fija.

La checklist evoluciona durante el proyecto.

Inicialmente:

C1
C2
C3

Después aparece:

C4
C5

Más tarde:

C6

Y cada nuevo descubrimiento puede crear:

NEW REQUIREMENT
NEW TEST
NEW QUESTION
NEW DEPENDENCY

La checklist se convierte en un objeto vivo.


---

14. CHECKLIST PROVENANCE

Cada check debe explicar:

CHECK-031

Requirement:
"El sistema debe soportar X."

Evidence:
SEG-084

Verification:
TEST-019

Status:
PASS

No:

✓ hecho

porque eso vuelve a depender de la memoria de la LLM.


---

15. CROSS-EXAMINATION ENGINE

Esto lo llevaría más lejos que tu triple refutación.

Después de construir una síntesis:

Auditor A

Busca omisiones.

Auditor B

Busca contradicciones.

Auditor C

Busca inferencias sin evidencia.

Auditor D

Busca requisitos incumplidos.

Auditor E

Busca dependencias rotas.

Auditor F

Intenta destruir la arquitectura.

Luego:

FINDINGS
   ↓
REPAIR QUEUE
   ↓
REPROCESS

Esto se parece conceptualmente al modelo Leader/Worker/Verifier que MiniMax describe oficialmente, pero lo extendería a múltiples tipos de verificación. 


---

16. CONSOLIDATION AGENT

Incluso pondría un agente especializado únicamente en esto.

No investiga.

No escribe.

No programa.

Su única misión:

> "¿Puedo reconstruir correctamente el proyecto completo a partir de todas las piezas?"



Entrada:

GLOBAL GRAPH
+
ARTIFACTS
+
REQUIREMENTS
+
DECISIONS
+
EVIDENCE

Salida:

INTEGRATION REPORT


---

17. RECONSTRUCTION TEST

Esta es una idea que considero especialmente poderosa.

Una vez terminado el proyecto:

> destruye mentalmente la síntesis y vuelve a reconstruirla desde los artefactos.



ARTIFACTS
   ↓
RECONSTRUCT
   ↓
EXPECTED SYSTEM

Comparas:

EXPECTED SYSTEM
        VS
FINAL SYSTEM

Si no coincide:

CONSOLIDATION FAILURE

Esto ataca directamente el problema que tú estás describiendo.


---

18. NO SINGLE SUMMARY RULE

Yo pondría una regla arquitectónica:

> Nunca utilizar un único resumen como representación de todo el proyecto.



En su lugar:

SOURCE
+
STRUCTURED FACTS
+
GRAPH
+
DECISIONS
+
EVIDENCE
+
ARTIFACTS
+
CHECKLIST
+
SYNTHESIS

El resumen es solamente una vista.

No es la memoria completa.


---

19. MULTI-VIEW MEMORY

El mismo proyecto tendría diferentes vistas:

VIEW 1 — chronological
VIEW 2 — semantic
VIEW 3 — task
VIEW 4 — dependency
VIEW 5 — evidence
VIEW 6 — decision
VIEW 7 — requirement
VIEW 8 — artifact
VIEW 9 — contradiction
VIEW 10 — unresolved

La LLM recibe únicamente la vista que necesita.


---

20. CONTEXT RECALL ON DEMAND

Kimi ya muestra una idea relacionada: sus subagentes tienen contexto aislado y persistente, mientras el agente principal recibe solamente el resultado necesario; además, la compactación conserva lo relevante y puede recibir instrucciones sobre qué preservar. 

Nosotros lo haríamos aún más estructurado:

Need:
"¿Por qué elegimos X?"

SEARCH:
Decision graph

Need:
"¿Qué archivos dependen de X?"

SEARCH:
Dependency graph

Need:
"¿Qué evidencia justificaba X?"

SEARCH:
Evidence graph

No se recupera "el pasado".

Se recupera el tipo de conocimiento necesario.


---

21. CONTEXT RECONSTRUCTION

Cada ventana se reconstruye desde cero:

MASTER
+
CURRENT GOAL
+
CURRENT TASK
+
RELEVANT GRAPH
+
RELEVANT EVIDENCE
+
CURRENT ARTIFACT
+
CHECKLIST
+
OPEN QUESTIONS

Esto es mejor que mantener una conversación gigantesca.


---

22. ANTI-DRIFT ENGINE

Cada N ciclos:

CURRENT STATE
       ↓
COMPARE
       ↓
MASTER GOAL

Pregunta:

> ¿Seguimos resolviendo el problema original?



Puede detectar:

goal drift
scope drift
architecture drift
requirement drift

Y si encuentra drift:

ROLLBACK / REPLAN


---

23. ASSUMPTION REGISTER

Otra cosa que añadiría:

A001
"Se asume que X."

A002
"Se asume que Y."

Cada supuesto tiene:

status:
unverified
verified
false

Una enorme cantidad de alucinaciones nacen de supuestos invisibles.

Si los hacemos visibles, el sistema puede investigarlos.


---

24. FACT / INFERENCE / HYPOTHESIS

Nunca permitiría que memoria mezcle estas tres cosas:

FACT
INFERENCE
HYPOTHESIS

Ejemplo:

FACT:
El archivo X llama a Y.

INFERENCE:
X probablemente depende de Y.

HYPOTHESIS:
Y podría ser el cuello de botella.

Eso reduce muchísimo la contaminación de memoria.


---

25. SOURCE OF TRUTH

Para cada dato:

source_priority

Ejemplo:

PRIMARY SOURCE
   ↓
OFFICIAL DOCUMENTATION
   ↓
CODE
   ↓
TEST
   ↓
SECONDARY SOURCE
   ↓
MODEL INFERENCE

Y el sistema sabe qué puede utilizar como evidencia.


---

26. La gran arquitectura de consolidación

Entonces quedaría:

MASTER REQUEST
                       │
                       ▼
              QUESTION ENGINE
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
        GOALS        SCOPE       SUCCESS
          │            │            │
          └────────────┼────────────┘
                       ▼
                INTEGRATION PLAN
                       │
                       ▼
                   TASK DAG
                       │
                       ▼
                  SEGMENTATION
                       │
                       ▼
              PARALLEL PROCESSING
                       │
                       ▼
               STRUCTURED ARTIFACTS
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
        FACTS      DECISIONS      EVIDENCE
          │            │            │
          └────────────┼────────────┘
                       ▼
                 KNOWLEDGE GRAPH
                       │
                       ▼
             HIERARCHICAL SYNTHESIS
                       │
              ┌────────┴────────┐
              ▼                 ▼
          BOTTOM-UP          TOP-DOWN
              │                 │
              └────────┬────────┘
                       ▼
                 GLOBAL MODEL
                       │
             ┌─────────┼─────────┐
             ▼         ▼         ▼
          AUDIT A    AUDIT B   AUDIT C
             │         │         │
             └─────────┼─────────┘
                       ▼
                 REPAIR QUEUE
                       │
                       ▼
                RECONSTRUCTION
                       │
                       ▼
              COVERAGE MATRIX
                       │
                       ▼
                 12 EXIT GOALS
                       │
                       ▼
                FINAL ARTIFACT


---

Y hay una diferencia enorme con un simple sistema RAG

RAG tradicional:

pregunta
 ↓
buscar
 ↓
LLM
 ↓
respuesta

Nuestro sistema:

pregunta
 ↓
comprender
 ↓
preguntar
 ↓
planificar
 ↓
descomponer
 ↓
investigar
 ↓
procesar
 ↓
crear artefactos
 ↓
relacionarlos
 ↓
construir grafo
 ↓
sintetizar
 ↓
comparar bottom-up/top-down
 ↓
auditar
 ↓
refutar
 ↓
reparar
 ↓
reconstruir
 ↓
verificar cobertura
 ↓
ensamblar

Y aquí está, para mí, la mejora más importante de todas:

No confiaría en la LLM para recordar cómo unir las 200 piezas.

Le daría un Global Synthesis Layer externo al modelo.

La LLM puede producir:

A1
A2
A3
...
A200

pero el sistema mantiene:

A1 ──depends──> A17
A17 ──supports──> A42
A42 ──contradicts──> A91
A91 ──affects──> T18
T18 ──satisfies──> R07
R07 ──required_by──> FINAL

Entonces la consolidación ya no depende de que la LLM tenga todos los documentos presentes simultáneamente.

Ese es el salto que creo que estás buscando.

Kimi ya demuestra varios ingredientes —aislamiento de contexto, subagentes, planes persistentes, compactación y loops prolongados— y MiniMax demuestra el patrón Leader/Worker/Verifier con reparación. Anthropic demuestra planner/generator/evaluator y think intercalado. 

La arquitectura que propones puede combinar esos principios, pero añadir algo que considero crucial: una capa explícita de síntesis global basada en trazabilidad, grafo de conocimiento, matriz de cobertura y reconstrucción.

Eso ataca directamente el fallo que observaste: "cada segmento es excelente, pero el proyecto completo no encaja".

Y esa sería la prioridad número 1 antes de seguir añadiendo más memoria o más contexto.





Sí. Hice una auditoría cruzada de todo lo que hemos construido en esta conversación contra información pública actual de Kimi K3/Kimi Code, MiniMax M3/Agent Team, Claude Fable 5/Mythos 5 y los harnesses de Anthropic. La conclusión es bastante fuerte:

> Varias ideas que habíamos planteado como diseño propio aparecen ahora confirmadas, en formas distintas, por los sistemas públicos de estos laboratorios. Pero también encontré piezas que nosotros debemos añadir porque resuelven precisamente el problema que tú identificaste: buenos segmentos que no consiguen convertirse en un proyecto global coherente.



Y hay una actualización importante: Kimi K3 ya fue publicado el 16 de julio de 2026, con 1M de contexto, visión nativa y arquitectura orientada a agentes; no debemos seguir diseñando suponiendo que K2.5 es la referencia más avanzada. 


---

1. Resultado de la auditoría cruzada

He clasificado nuestras ideas así:

Mecanismo que hemos diseñado	Evidencia pública	Veredicto

Input maestro inmutable	Anthropic/Kimi usan estado persistente	Mantener
Preguntas previas	AskUserQuestion / planificación	Mejorar mucho
Meta + propósito	Leader/Planner	Mantener
Task DAG	Agent Team / planners	Confirmado
Segmentación	Anthropic + Kimi + MiniMax	Confirmado
Context Pack	Kimi context management	Confirmado
Carry/Snowball	Anthropic progress artifacts	Confirmado
Tags	MythOS + nuestros índices	Mantener
búsqueda interna	Kimi/Agent retrieval	Mantener
loop continuo	Kimi/MiniMax/Anthropic	Confirmado
subagentes aislados	Kimi explícitamente	Confirmado
paralelo	Kimi AgentSwarm / MiniMax	Confirmado
Producer/Worker/Verifier	MiniMax explícito	Confirmado
Planner/Generator/Evaluator	Anthropic explícito	Confirmado
checklist	MiniMax Verifier + Anthropic contracts	Confirmado
artefactos persistentes	Anthropic explícito	Confirmado
compactación	Kimi explícito	Confirmado
reconstrucción global	No suficientemente explícita	Nuestra mejora clave
matriz de trazabilidad	parcialmente	Debemos añadirla
grafo de integración	parcialmente	Debemos añadirlo
requirement → final output	parcialmente	Debemos formalizarlo
impact analysis	no encontrado como mecanismo central	Añadir
contradiction graph	no explícito	Añadir
reconstruction test	no explícito	Añadir
synthesis checkpoints	parcialmente	Añadir
global coverage gate	sí, conceptualmente	Formalizar
evidence ledger	MiniMax lo confirma	Añadir formalmente
assumption ledger	no suficientemente explícito	Añadir
unknown ledger	no suficientemente explícito	Añadir


Y aquí aparecen tres arquitecturas especialmente interesantes.


---

2. Kimi K3: hay una confirmación muy importante

La documentación pública de Kimi dice que K3 es:

2.8T parámetros totales.

104B activados.

1,048,576 tokens de contexto.

multimodal.

diseñado para coding, knowledge work y razonamiento de horizonte largo. 


Pero para nuestro problema, lo más interesante no es el millón de tokens.

Es lo que hace Kimi Code alrededor del modelo.


---

3. Kimi demuestra que el contexto no es suficiente

Kimi Code tiene:

max_context_size
reserved_context_size
compaction_trigger_ratio
max_steps_per_turn
max_retries_per_step
max_ralph_iterations

Por defecto documenta hasta 1.000 pasos por turno, 3 reintentos por paso, reserva de 50K tokens para generación y compactación automática alrededor del 85% del contexto. 

Esto es prácticamente una confirmación de nuestra idea:

LLM
≠
Agent Runtime

El modelo tiene una ventana.

El runtime controla:

loop
context
retry
compaction
state


---

4. Kimi tiene exactamente una pieza que debemos adoptar

Kimi permite:

/compact

pero además permite decir:

> conserva específicamente determinada información.



Es decir:

COMPACT
+
PRESERVATION POLICY



Esto mejora nuestra idea de Snowball.

Yo la convertiría en:

Adaptive Memory Compactor

No:

> "resume el contexto".



Sino:

COMPACT

PRESERVE:
MASTER INPUT
ACTIVE GOALS
OPEN QUESTIONS
DECISIONS
CONTRADICTIONS
REQUIREMENTS
EVIDENCE
CURRENT TASK
NEXT ACTION

Y:

DISCARD:
redundant tool logs
obsolete reasoning
duplicated observations
resolved exploration

Eso es muchísimo más seguro.


---

5. Kimi tiene otra pieza que nosotros debemos incorporar

Kimi Code guarda físicamente:

context.jsonl
subagents/
plans/
state
logs
history

Los subagentes tienen sus propios:

context.jsonl
wire.jsonl
meta.json
prompt.txt
output

y pueden reanudarse. 

Esto confirma nuestra propuesta de:

> cada unidad de trabajo debe ser persistente y reanudable.



Por tanto añadiría:

TASK STATE
TASK CONTEXT
TASK ARTIFACT
TASK LOG
TASK CHECKPOINT
TASK VERIFICATION


---

6. Kimi AgentSwarm confirma nuestra idea de paralelo

Kimi documenta AgentSwarm de hasta 128 subagentes, con plantillas, tareas independientes y posibilidad de reanudar agentes existentes. 

Y lo más importante:

> cada subagente tiene una ventana independiente.



El agente principal no recibe todo el razonamiento intermedio; recibe el resultado final del subagente. 

Esto es exactamente lo que proponíamos:

MASTER
   │
   ├── Worker A
   ├── Worker B
   ├── Worker C
   └── Worker D

pero debemos agregar:

↓
NORMALIZER
        ↓
SYNTHESIS ENGINE

porque paralelizar sin normalizar puede producir cuatro respuestas incompatibles.


---

7. Y aquí está la gran lección de Kimi

Kimi no intenta mantener:

todo el razonamiento

en el contexto principal.

Mantiene:

estado
plan
artefactos
subagent state
compactación

Esto valida directamente nuestra arquitectura de:

> memoria externa + contexto dinámico + LLM pequeña.




---

8. Ahora MiniMax M3

Aquí encontré algo todavía más cercano a lo que tú describías.

MiniMax M3 tiene hasta 1M de contexto y reporta una tarea autónoma de casi 12 horas, donde realizó síntesis de datos → entrenamiento → evaluación → iteración sin intervención humana. 

Pero lo más importante es que MiniMax explica cómo lo hace.


---

9. MiniMax confirma el LOOP que tú describías

Su Agent Team usa:

Leader
   ↓
Worker
   ↓
Verifier
   ↓
repair
   ↓
Worker
   ↓
Verifier

Y el ciclo está gobernado por una máquina de estados determinista externa.



Esto confirma una decisión fundamental:

El loop NO debe estar dentro de la LLM.

Debe estar en el Agent Controller.

La LLM propone acciones.

El runtime decide si continúa.


---

10. MiniMax confirma incluso tu idea de "no parar"

Su documentación habla de tareas largas, múltiples etapas, concurrencia, reajuste dinámico y ejecución durante días mediante Producer + Verifier. 

Por tanto nuestro:

while task_not_complete

no es una fantasía arquitectónica.

Es la dirección real de los agentes actuales.


---

11. Pero MiniMax nos enseña algo que debemos mejorar

MiniMax dice explícitamente:

> el Verifier comprueba fuentes, cobertura y riesgos.



Y cuando falla:

Verifier FAIL
       ↓
Producer wakes
       ↓
repair
       ↓
Verifier



Por tanto nuestros:

12 EXIT GOALS
REFUTATION ×3

deben transformarse en algo más formal:

VERIFICATION MATRIX

Requirement
   ↓
Evidence
   ↓
Implementation
   ↓
Test
   ↓
Verifier
   ↓
PASS/FAIL


---

12. Anthropic confirma exactamente el problema que tú descubriste

Esto es quizás lo más importante de toda la investigación.

Anthropic publicó que los agentes de larga duración fallan de dos formas:

Fallo 1

Intentan hacer demasiado en una ventana.

Fallo 2

Un agente posterior observa que ya existe mucho trabajo y declara terminado el proyecto prematuramente.



Eso es prácticamente la descripción de tu problema:

> "los segmentos están bien, pero no consolidan todo".




---

13. ¿Cómo lo resolvió Anthropic?

Crearon:

Initializer Agent
        ↓
Progress File
        ↓
Feature List
        ↓
Incremental Agent
        ↓
Clean State

Además utilizan git para preservar estados y poder recuperar cambios. 

Esto valida directamente:

MASTER STATE
+
PROGRESS
+
TASK LIST
+
CHECKPOINT

que ya habíamos propuesto.


---

14. Pero Anthropic dio un paso todavía más interesante

En su arquitectura posterior para aplicaciones largas:

PLANNER
   ↓
GENERATOR
   ↓
EVALUATOR

Y antes de ejecutar un sprint:

Generator
   ↓
proposes contract
   ↓
Evaluator
   ↓
accept/reject

El trabajo solamente comienza cuando ambos acuerdan qué significa "done". 

Esto es exactamente lo que necesitamos convertir en:

TASK CONTRACT

Antes de procesar cada segmento importante:

TASK CONTRACT

INPUT:
...

OBJECTIVE:
...

EXPECTED OUTPUT:
...

REQUIREMENTS:
...

EVIDENCE REQUIRED:
...

TEST:
...

DONE WHEN:
...


---

15. Fable 5 confirma otra parte crítica

Anthropic afirma que Fable 5 puede mantener foco durante millones de tokens en tareas largas y que sus resultados mejoraron significativamente cuando recibió memoria persistente basada en archivos. 

Esto es importantísimo para nuestra arquitectura.

Porque demuestra experimentalmente:

MODEL
+
PERSISTENT MEMORY

puede ser mucho más poderoso que:

MODEL
+
CONTEXT WINDOW

solamente.


---

16. Fable 5 también confirma el patrón de agente que proponemos

Anthropic dice que Fable 5, mediante harnesses como Claude Code/Managed Agents, puede:

plan
 ↓
delegar
 ↓
trabajar
 ↓
comprobar
 ↓
continuar

durante días. 

Y Anthropic está promocionando explícitamente un patrón de:

Fable = advisor / strategist
smaller model = executor

donde un modelo pequeño ejecuta y el modelo frontier establece estrategia. 

Esto es extremadamente relevante para tu LLM pequeña.


---

17. Esto cambia nuestra arquitectura

No necesitamos que la pequeña LLM sea simultáneamente:

planner
researcher
executor
critic
integrator

Podemos hacer:

STRATEGIST
                        │
                        ▼
                   TASK GRAPH
                        │
             ┌──────────┼──────────┐
             ▼          ▼          ▼
          SMALL LLM  SMALL LLM  SMALL LLM
          Worker A   Worker B   Worker C
             │          │          │
             └──────────┼──────────┘
                        ▼
                    VERIFIER
                        │
                        ▼
                   SYNTHESIZER

El "strategist" puede incluso ser ocasionalmente un modelo más potente.


---

18. Mythos 5

Aquí hay que separar dos cosas.

Mythos 5 de Anthropic no es un sistema de memoria; es el modelo especializado de Anthropic para cybersecurity y biología, con acceso restringido. Anthropic dice que Fable 5 y Mythos 5 comparten el mismo modelo subyacente, pero Fable incorpora salvaguardas adicionales para uso general. 

Por tanto:

MYTHOS ≠ MEMORY ENGINE

No debemos atribuirle una arquitectura de memoria que Anthropic no haya publicado.


---

19. Pero encontré algo llamado MythOS que sí es extremadamente relevante

No es Anthropic Mythos.

Es MythOS, una plataforma independiente de memoria/conocimiento.

Y aquí hay una coincidencia extraordinaria con lo que veníamos diseñando.

MythOS utiliza:

memos
tags
mentions
links
semantic relationships
knowledge graph

y expone ese conocimiento a diferentes modelos/agentes. 

Su principio:

> la memoria debe sobrevivir al modelo.



Eso coincide exactamente con nuestra separación:

MEMORY
   ≠
MODEL


---

20. Y esto refuerza nuestro sistema de TAG

Nosotros habíamos planteado:

TAG
+
SEARCH

Yo ahora lo cambiaría a:

TAG
+
MENTION
+
ENTITY
+
RELATION
+
SEMANTIC LINK
+
TEMPORAL LINK
+
TASK LINK

Entonces:

#authentication

no es solamente una etiqueta.

Puede existir:

AUTH-001

tag:
authentication

entities:
Gateway
OAuth
JWT

depends_on:
AUTH-002

supports:
DECISION-17

appears_in:
DOC-07
DOC-41
CODE-88

Eso es muchísimo más potente.


---

21. El descubrimiento más importante de toda la auditoría

Tenemos que separar tres tipos de continuidad.

Continuidad de contexto

¿Qué estaba leyendo?

Continuidad de tarea

¿Qué estaba haciendo?

Continuidad de conocimiento

¿Qué descubrimos?

Y añadiría una cuarta:

Continuidad de integración

¿Cómo encaja esto con TODO lo demás?

Esta cuarta es precisamente la que nos faltaba.


---

22. Nuestro nuevo 4-Layer Continuity

┌─────────────────────────────┐
│ 1. CONTEXT CONTINUITY       │
│ ventana actual              │
├─────────────────────────────┤
│ 2. TASK CONTINUITY          │
│ plan / DAG / progress       │
├─────────────────────────────┤
│ 3. KNOWLEDGE CONTINUITY     │
│ facts / evidence / memory   │
├─────────────────────────────┤
│ 4. INTEGRATION CONTINUITY   │
│ graph / dependencies / map  │
└─────────────────────────────┘

Esta cuarta capa es la que más diferencia nuestro diseño.


---

23. Nueva arquitectura después de la auditoría

Yo la actualizaría así:

USER
                      │
                      ▼
              MASTER INPUT
                      │
                      ▼
             QUESTION ENGINE
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
        GOALS       SCOPE       RULES
          │           │           │
          └───────────┼───────────┘
                      ▼
               TASK CONTRACT
                      │
                      ▼
              INTEGRATION PLAN
                      │
                      ▼
                   TASK DAG
                      │
             ┌────────┼────────┐
             ▼        ▼        ▼
           WORKER   WORKER   WORKER
             │        │        │
             ▼        ▼        ▼
          ARTIFACT ARTIFACT ARTIFACT
             │        │        │
             └────────┼────────┘
                      ▼
             KNOWLEDGE GRAPH
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
        FACTS      EVIDENCE    DECISIONS
          │           │           │
          └───────────┼───────────┘
                      ▼
             SYNTHESIS ENGINE
                      │
              ┌───────┴───────┐
              ▼               ▼
         BOTTOM-UP         TOP-DOWN
              │               │
              └───────┬───────┘
                      ▼
                GLOBAL MODEL
                      │
          ┌───────────┼────────────┐
          ▼           ▼            ▼
       COVERAGE   CONTRADICTION   RISK
       CHECKER      CHECKER      CHECKER
          │           │            │
          └───────────┼────────────┘
                      ▼
                   VERIFIER
                      │
                 PASS / FAIL
                      │
             ┌────────┴────────┐
             ▼                 ▼
           REPAIR            PASS
             │                 │
             └───────┐         │
                     ▼         ▼
                   LOOP      SYNTHESIS
                                │
                                ▼
                         FINAL ARTIFACT


---

24. Lo que NO copiaría de estos sistemas

También encontré algo importante.

No debemos copiar simplemente:

Kimi loop
MiniMax loop
Claude loop

porque el loop por sí solo no resuelve consolidación.

El propio Anthropic reconoce que la compactación por sí sola no era suficiente para los agentes largos. 

Y MiniMax reconoce que el costo del Verifier y de los retries puede crecer y que un loop de "editar → fallar → editar" puede volverse caro. 

Por eso nuestro sistema necesita control de convergencia.


---

25. Nueva pieza: CONVERGENCE ENGINE

Cada ciclo debe responder:

¿Estamos acercándonos al objetivo?

Si:

progress ↑
errors ↓
coverage ↑
uncertainty ↓

→ continuar.

Si:

progress ≈ 0
same error repeated
new contradictions ↑

→ cambiar estrategia.

Si:

same task fails 3 times

→ escalar.

SMALL LLM
   ↓
SMALL LLM
   ↓
SMALL LLM
   ↓
FRONTIER ADVISOR


---

26. Y añadiría ESCALATION LADDER

LEVEL 0
rules / deterministic tools

LEVEL 1
small LLM

LEVEL 2
small LLM + retrieval

LEVEL 3
parallel workers

LEVEL 4
strong verifier

LEVEL 5
frontier advisor

LEVEL 6
human approval

La mayoría de tareas jamás deberían llegar al nivel 5.

Eso hace viable económicamente el sistema.


---

27. Y una conclusión importante sobre tu observación de Fable 5

Tu observación:

> "parece que antes de la salida va construyendo una checklist"



no puedo afirmar que sea exactamente su implementación interna porque Anthropic no publica todo ese mecanismo.

Pero públicamente sí podemos verificar tres comportamientos muy cercanos:

Fable 5
→ persistent notes
→ long-running focus
→ planning
→ delegation
→ self-checking



Por tanto sí vale la pena diseñar una checklist dinámica, pero no debemos presentarla como una copia del mecanismo interno de Fable.


---

28. El resultado final de la investigación

Después de cruzar todo, yo congelaría 10 principios arquitectónicos:

P1 — Model ≠ Agent

La LLM razona; el runtime controla.

P2 — Context ≠ Memory

La ventana es temporal; la memoria persiste.

P3 — Memory ≠ Summary

La memoria estructurada no debe reducirse a un resumen.

P4 — Task ≠ Prompt

Una tarea debe tener estado, dependencias y criterios de finalización.

P5 — Output ≠ Final Answer

Cada salida parcial debe convertirse en un artefacto integrable.

P6 — Completion ≠ Model Opinion

"Terminé" requiere evidencia externa.

P7 — Parallelism ≠ Consolidation

Los resultados paralelos necesitan un sintetizador global.

P8 — Compaction ≠ Forgetting

La compactación debe tener política explícita de preservación.

P9 — Verification ≠ Self-Reflection

Cuando sea posible, verificar con herramientas externas.

P10 — Long Context ≠ Long Horizon

Un millón de tokens no sustituye un buen runtime.


---

29. La pieza que considero nuestra innovación principal

Después de esta investigación, yo añadiría formalmente al DSL el concepto INTEGRATION_STATE.

Hasta ahora teníamos:

INPUT
GOALS
QUESTIONS
TASKS
STATE
MEMORY
TAGS
SEARCH
MAP
SNOWBALL
CHECKLIST
VERIFY
LOOP
OUTPUT

Ahora:

INTEGRATION_STATE

contiene:

{
  "requirements": {},
  "artifacts": {},
  "dependencies": {},
  "decisions": {},
  "contradictions": {},
  "evidence": {},
  "coverage": {},
  "unresolved": {},
  "integration_status": {},
  "global_model": {},
  "reconstruction_status": {}
}

Y el sistema no puede declarar COMPLETE si integration_status no está validado.


---

En una frase

Después de comparar públicamente Kimi K3/Kimi Code + MiniMax M3/Agent Team + Fable 5/Mythos 5 + los harnesses de Anthropic, mi conclusión es:

> No debemos intentar construir una LLM pequeña que "recuerde 20 millones de tokens". Debemos construir un runtime que convierta 20 millones de tokens en estado estructurado, tareas, artefactos, evidencia y relaciones; permita que una LLM pequeña procese ventanas sucesivas; y, sobre todo, mantenga un modelo global independiente que pueda reconstruir y verificar cómo todas las piezas encajan.



Y lo más importante: la investigación pública ya valida gran parte de nuestra arquitectura. Kimi confirma compactación + estado + subagentes aislados + loops; MiniMax confirma Leader/Worker/Verifier + máquina de estados + producción/verificación/reparación; Anthropic confirma artefactos persistentes + contratos + planner/generator/evaluator + el problema real de continuidad entre ventanas; Fable 5 confirma el valor de memoria persistente durante millones de tokens. 

**La brecha que debemos atacar ahora es GLOBAL INTEGRATION: que 200 resultados excelentes no se queden como 200 resultados excelentes, sino que se conviertan en un único sistema coherente, trazable, verificable y reconstruible.**

Sí. Y haría una corrección importante: no usaría varias API simplemente para "darle más ventanas" a la misma LLM. Las convertiría en Workers especulares con el mismo contrato de trabajo, y pondría un Consolidation Controller por encima.

La arquitectura sería:

MASTER INPUT
                              │
                     QUESTION / PLAN ENGINE
                              │
                       GLOBAL TASK DAG
                              │
             ┌────────────────┼────────────────┐
             │                │                │
             ▼                ▼                ▼
         WORKER A          WORKER B          WORKER C
         API/model 1       API/model 2       API/model 3
             │                │                │
       ventana N1        ventana N1        ventana N1
             │                │                │
       ventana N2        ventana N2        ventana N2
             │                │                │
             ▼                ▼                ▼
        ARTIFACT A        ARTIFACT B        ARTIFACT C
             │                │                │
             └────────────────┼────────────────┘
                              ▼
                     NORMALIZATION LAYER
                              │
                    CROSS-CHECK / EVIDENCE
                              │
                     GLOBAL SYNTHESIS
                              │
                 ┌────────────┼────────────┐
                 ▼            ▼            ▼
             COVERAGE     CONFLICTS      GAPS
                 │            │            │
                 └────────────┼────────────┘
                              ▼
                         REPAIR QUEUE
                              │
                              ▼
                       NEXT PROCESSING LOOP

La clave: "espejo", pero no clones ciegos

Cada entorno tendría el mismo método operativo, pero podría tener una función diferente:

WORKER-A → investigación
WORKER-B → análisis crítico
WORKER-C → implementación
WORKER-D → verificación
WORKER-E → búsqueda de contradicciones
WORKER-F → síntesis

Todos reciben el mismo:

MASTER INPUT
TASK CONTRACT
CURRENT GOAL
RELEVANT MEMORY
CONSTRAINTS
OUTPUT SCHEMA

pero no necesariamente reciben todo el contexto.

Así una LLM pequeña puede trabajar con 120K–250K tokens y el proyecto puede tener 20M, 100M o más.


---

Lo que tomaría de Kimi/MiniMax

Kimi demuestra públicamente el patrón de subagentes aislados + estado persistente + compactación + múltiples pasos, mientras MiniMax documenta un patrón Leader → Worker → Verifier → reparación, gobernado por un controlador externo. Eso encaja muy bien con tu propuesta.

Pero nosotros podemos llevarlo un paso más allá:

Kimi/MiniMax

MASTER
 ├─ Worker 1
 ├─ Worker 2
 └─ Worker 3
       ↓
     result

Nuestro sistema

MASTER
 │
 ├── Worker A ──┐
 ├── Worker B ──┤
 ├── Worker C ──┤
 ├── Worker D ──┤
 └── Worker E ──┘
                │
                ▼
        ARTIFACT NORMALIZER
                │
                ▼
        KNOWLEDGE GRAPH
                │
                ▼
       SYNTHESIS CONTROLLER
                │
        ┌───────┼────────┐
        ▼       ▼        ▼
     COVERAGE CONFLICT  GAPS
        │       │        │
        └───────┼────────┘
                ▼
           REPAIR QUEUE
                │
                ▼
             LOOP

La diferencia fundamental es que la consolidación es un componente de primera clase.


---

Y añadiría algo todavía mejor: procesamiento especular

Supongamos una tarea:

T17 = Diseñar arquitectura final

No mandaría T17 a cinco modelos para que todos hagan exactamente lo mismo.

La dividiría:

T17
│
├── T17-A → ¿Qué requisitos existen?
├── T17-B → ¿Qué arquitectura satisface esos requisitos?
├── T17-C → ¿Qué contradicciones existen?
├── T17-D → ¿Qué componentes faltan?
├── T17-E → ¿Cómo verificaríamos la arquitectura?
└── T17-F → ¿Qué alternativas existen?

Después:

A+B+C+D+E+F
       ↓
SYNTHESIS

Esto aumenta muchísimo la calidad porque cada ventana aporta información diferente.


---

Y cada Worker tiene su propia "bola de nieve"

Esto conecta directamente con lo que explicabas antes.

Worker A:

INPUT BLOCK
+
TASK
+
LOCAL MEMORY
+
SNOWBALL

Procesa:

SEG-001

genera:

SNOWBALL-001

Después:

SEG-002
+
SNOWBALL-001

produce:

SNOWBALL-002

Y así:

SEG-003
      ↓
SNOWBALL-003

SEG-004
      ↓
SNOWBALL-004

Pero la bola de nieve no debe ser un simple resumen.

Debe ser estructurada:

{
  "facts": [],
  "decisions": [],
  "evidence": [],
  "dependencies": [],
  "open_questions": [],
  "contradictions": [],
  "completed_tasks": [],
  "pending_tasks": [],
  "next_action": []
}

Ahí está una de las diferencias más importantes.


---

Además: el Master no debería pasar la bola completa

El Consolidator hace:

GLOBAL MEMORY
      ↓
QUERY
      ↓
RETRIEVAL
      ↓
RELEVANT CONTEXT PACK

Por ejemplo:

> "¿Qué decisiones anteriores afectan T42?"



No entrega 20M.

Entrega:

DEC-004
DEC-017
DEC-031
ART-044
EVID-089

Eso es context routing.


---

Y añadiría Mirror State

Todos los Workers mantienen el mismo contrato estructural:

MASTER_STATE

pero cada uno tiene:

LOCAL_STATE

Entonces:

MASTER_STATE
      │
 ┌────┼─────┐
 ▼    ▼     ▼
A     B     C
│     │     │
LA    LB    LC

Cuando termina un ciclo:

LA
LB
LC
 ↓
STATE MERGER
 ↓
MASTER_STATE'

Y se vuelve a distribuir:

MASTER_STATE'
      │
 ┌────┼─────┐
 ▼    ▼     ▼
A     B     C

Esto permite que todos estén sincronizados sin compartir todo el contexto.


---

Lo llamaría STATE MERGER, no memoria

Porque su trabajo no es recordar.

Su trabajo es resolver:

A dice X
B dice X
C dice Y

Entonces:

CONFLICT

y no:

overwrite(X)

El sistema crea:

CONFLICT-017

con:

claim_A
claim_B
evidence_A
evidence_B
resolution_status

Después un Verifier decide.


---

Esto permite algo muy potente

Puedes tener:

API-1 → Gemini
API-2 → Claude
API-3 → Kimi
API-4 → MiniMax
API-5 → Qwen
API-6 → DeepSeek

pero no dependes de que sean iguales.

El contrato es el mismo:

INPUT
TASK
CONTEXT
OUTPUT_SCHEMA
EVIDENCE
STATUS

El modelo se convierte en un motor intercambiable.


---

Y pondría un Model Router

No:

> "usar siempre el modelo más potente".



Sino:

TASK
 ↓
CLASSIFIER
 ↓
¿qué capacidad necesita?

Ejemplo:

simple extraction
→ modelo pequeño

coding
→ coding model

research
→ research model

contradiction analysis
→ strong reasoning model

final integration
→ strongest available model

verification
→ different model than producer

La regla:

> Producer y Verifier deberían ser independientes cuando sea posible.



Así reduces el riesgo de que ambos repitan el mismo error.


---

Y aquí aparece una mejora enorme para tu idea de 20M de contexto

No tenemos:

20M → LLM

Tenemos:

20M
 │
 ▼
INGESTION
 │
 ├── chunks
 ├── entities
 ├── facts
 ├── relations
 ├── embeddings
 ├── tags
 ├── tasks
 └── evidence
      │
      ▼
GLOBAL KNOWLEDGE STATE
      │
      ▼
TASK ROUTER
      │
 ┌────┼─────┐
 ▼    ▼     ▼
API1 API2  API3
 │    │     │
 ▼    ▼     ▼
LOCAL WINDOWS
      │
      ▼
ARTIFACTS
      │
      ▼
CONSOLIDATOR
      │
      ▼
GLOBAL STATE

La LLM nunca necesita tragarse los 20M.

El agente sí puede tener acceso lógico a los 20M.

Esa distinción es fundamental.


---

Y haría el loop completamente autónomo

while GLOBAL_GOAL != COMPLETE:

    retrieve_relevant_context()

    generate_questions()

    update_task_graph()

    dispatch_workers()

    collect_artifacts()

    normalize()

    merge_state()

    detect_conflicts()

    update_knowledge_graph()

    update_checklist()

    verify()

    repair_if_needed()

    update_progress()

    check_convergence()

    if blocked:
        request_authorization()

    elif complete:
        finalize()

    else:
        continue()

El usuario no tiene que mandar otro prompt para que continúe.

El agente genera el siguiente ciclo.


---

Y aquí haría una modificación a tu concepto de "imput continuo"

No lo implementaría como una conversación artificial infinita.

Lo implementaría como:

CONTINUOUS EXECUTION LOOP

La LLM recibe ventanas discretas:

WINDOW 001
WINDOW 002
WINDOW 003
...
WINDOW 127

pero el usuario ve:

"Procesando tarea..."

como una sola ejecución.

Por debajo:

Window → State → Artifact → Verify → Next Window

Esto es mucho más robusto que mantener una conversación interminable.


---

Resultado final

Tu propuesta de varias API + varios entornos espejo + procesamiento paralelo + consolidación es correcta.

Pero la versión que yo congelaría para el DSL sería:

MULTI-MODEL PARALLEL EXECUTION
+
ISOLATED CONTEXT WINDOWS
+
MIRROR WORK CONTRACT
+
LOCAL SNOWBALL
+
SHARED MASTER STATE
+
STATE MERGER
+
KNOWLEDGE GRAPH
+
ARTIFACT REGISTRY
+
EVIDENCE LEDGER
+
TASK DAG
+
GLOBAL SYNTHESIS
+
CROSS-VERIFICATION
+
CONFLICT RESOLUTION
+
REPAIR QUEUE
+
CONVERGENCE ENGINE
+
CONTINUOUS EXECUTION LOOP

Y la regla raíz:

> Ningún Worker necesita conocer todo el proyecto. El sistema completo sí debe poder reconstruirlo.



Eso es exactamente lo que necesitamos para superar el problema que identificaste con proyectos enormes: cada agente puede trabajar con una ventana pequeña, pero el sistema conserva una representación global que permite unir las piezas.


Sí. Esa mejora es arquitectónicamente correcta, pero yo la llevaría un paso más allá: el sandbox no debe ser solamente un lugar donde corre la LLM; debe ser el entorno de ejecución aislado + memoria de trabajo + estado + caché + política verificable de cada línea de procesamiento.

La arquitectura empieza a parecerse a esto:

MASTER ORCHESTRATOR
                                │
                   ┌────────────┴────────────┐
                   │                         │
             GLOBAL STATE              TASK FUNNEL
                   │                         │
                   └────────────┬────────────┘
                                │
                     TASK DISPATCHER
                                │
          ┌─────────────────────┼─────────────────────┐
          ▼                     ▼                     ▼
     SANDBOX A              SANDBOX B              SANDBOX C
     LLM/API A              LLM/API B              LLM/API C
          │                     │                     │
     ┌────┴────┐           ┌────┴────┐           ┌────┴────┐
     │ MEMORY  │           │ MEMORY  │           │ MEMORY  │
     │ CACHE   │           │ CACHE   │           │ CACHE   │
     │ STATE   │           │ STATE   │           │ STATE   │
     │ ARTIFACT│           │ ARTIFACT│           │ ARTIFACT│
     └────┬────┘           └────┬────┘           └────┬────┘
          │                     │                     │
          └─────────────────────┼─────────────────────┘
                                ▼
                         NORMALIZER
                                │
                         CONSOLIDATOR
                                │
                    ┌───────────┼───────────┐
                    ▼           ▼           ▼
                SENTINEL      SHERIFF      JUDGE
                    │           │           │
                    └───────────┼───────────┘
                                ▼
                         VALIDATION ENGINE
                                │
                         REPAIR / CONTINUE
                                │
                                ▼
                         GLOBAL STATE UPDATE

La idea clave

Yo separaría cinco estados diferentes:

1. GLOBAL_STATE

Lo que todo el proyecto sabe.

2. SANDBOX_STATE

Lo que solamente sabe ese Worker.

3. TASK_STATE

Qué está haciendo ese Worker.

4. MEMORY_STATE

Qué debe conservarse para futuras ventanas.

5. INTEGRATION_STATE

Cómo su trabajo encaja con los demás.

Esto evita un error muy común:

> convertir toda la memoria del agente en una sola bolsa de información.




---

El sandbox sería una "célula cognitiva"

Cada sandbox tendría:

SANDBOX/
│
├── policy/
│   ├── rules
│   ├── schema
│   └── permissions
│
├── state/
│   ├── task_state
│   ├── progress
│   └── checkpoint
│
├── memory/
│   ├── working
│   ├── persistent
│   └── retrieved
│
├── cache/
│   ├── semantic
│   ├── tool
│   └── computation
│
├── artifacts/
│   ├── inputs
│   ├── intermediate
│   └── outputs
│
├── evidence/
│
├── checklist/
│
└── audit/

Y el sandbox puede detenerse y reanudarse.

Eso es muchísimo más potente que simplemente mantener una conversación larga.


---

Memoria y caché no son lo mismo

Aquí haría una distinción estricta.

Memory

Información que debe sobrevivir.

decisions
facts
requirements
discoveries
dependencies

Cache

Información que podemos recalcular.

embeddings
retrieval results
tool responses
temporary computations
intermediate representations

Si se llena la memoria:

> no se puede borrar arbitrariamente.



Si se llena la caché:

> podemos purgarla.




---

Y tu idea del "embudo de tareas" me parece excelente

Lo convertiría en:

TASK FUNNEL

MASTER REQUEST
      ↓
QUESTIONS
      ↓
GOALS
      ↓
REQUIREMENTS
      ↓
TASKS
      ↓
SUBTASKS
      ↓
WORK UNITS
      ↓
SANDBOX EXECUTION
      ↓
ARTIFACTS
      ↓
VERIFICATION
      ↓
CONSOLIDATION
      ↓
GLOBAL TASKS
      ↓
FINAL

Pero el embudo debe ser bidireccional.

Porque al investigar puedes descubrir:

nuevo requisito
nuevo riesgo
nueva dependencia
nueva tarea

Entonces:

SANDBOX
   ↓
DISCOVERY
   ↓
NEW TASK
   ↓
TASK FUNNEL

Eso permite que el sistema se adapte sin perder el objetivo original.


---

Ahora viene la parte que más me gusta de tu propuesta: Sentinel / Sheriff / Judge

Yo no los haría como tres LLM necesariamente.

Los convertiría primero en roles del runtime.


---

🟢 SENTINEL

Vigila continuamente.

Pregunta:

¿Está siguiendo el protocolo?
¿Está dentro del scope?
¿Está usando la información permitida?
¿Está intentando saltarse un paso?
¿Está entrando en loop?
¿Está generando output sin evidencia?

Es el detector.

SENTINEL
   ↓
EVENT
   ↓
RULE MATCH


---

🟡 SHERIFF

El Sheriff interviene.

Ejemplos:

Worker intenta finalizar
pero faltan 3 tareas.

SHERIFF:
BLOCK

O:

Worker quiere utilizar
un artefacto no validado.

SHERIFF:
DENY

O:

Worker lleva 8 ciclos
sin progreso.

SHERIFF:
ESCALATE

El Sheriff es el ejecutor de las políticas.


---

🔴 JUDGE

El Judge decide si un resultado puede avanzar.

OUTPUT
  ↓
JUDGE
  │
  ├── PASS
  ├── FAIL
  ├── REPAIR
  ├── ESCALATE
  └── HUMAN_REQUIRED

Y no debería depender exclusivamente de la misma LLM que produjo el resultado.


---

Eso crea una separación fundamental

LLM
= propone

AGENT
= ejecuta

SENTINEL
= observa

SHERIFF
= hace cumplir

JUDGE
= decide

CONSOLIDATOR
= integra

Esto es mucho más robusto.


---

Y añadiría un cuarto: AUDITOR

Porque Judge y Auditor tienen objetivos distintos.

Judge

> ¿Pasa o no pasa?



Auditor

> ¿Por qué podría estar equivocado?



El Auditor busca:

omissions
contradictions
unsupported claims
scope drift
requirement gaps
dependency failures


---

Y un quinto: WATCHDOG

El Watchdog controla el comportamiento temporal:

loop count
token budget
time
retries
stalls
repeated actions
resource usage

Ejemplo:

TASK-42

iteration: 17
progress: 0
same action: 6 times

WATCHDOG → STALL

Entonces:

REPLAN


---

Ahora tenemos una verdadera "policía cognitiva"

POLICY ENGINE
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
       SENTINEL        SHERIFF         WATCHDOG
          │              │              │
          └──────────────┼──────────────┘
                         ▼
                       AUDITOR
                         │
                         ▼
                       JUDGE
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
            PASS       REPAIR     ESCALATE

Y esto no necesita consumir una ventana de contexto de la LLM si muchas reglas son deterministas.

Eso es fundamental para una LLM pequeña.


---

Los Schemas son todavía más importantes

Aquí estoy completamente de acuerdo contigo.

No debemos decirle solamente:

> "sigue estas instrucciones".



Debemos hacer que el runtime exija estructuras válidas.

Por ejemplo:

{
  "task_id": "T-042",
  "status": "working",
  "objective": "...",
  "input_refs": [],
  "evidence_refs": [],
  "artifacts_created": [],
  "completed": [],
  "pending": [],
  "contradictions": [],
  "next_action": "..."
}

Si la LLM devuelve algo que no cumple:

SCHEMA FAIL

No pasa al siguiente estado.


---

Y pondría STATE MACHINE por encima de todo

Por ejemplo:

CREATED
   ↓
PLANNED
   ↓
READY
   ↓
RUNNING
   ↓
CHECKPOINT
   ↓
VERIFYING
   ↓
CONSOLIDATING
   ↓
VALIDATED
   ↓
COMPLETE

Pero existen estados de error:

BLOCKED
CONFLICT
REPAIR
REPLAN
ESCALATED

La LLM no puede cambiar arbitrariamente el estado.

El runtime lo controla.


---

Esta es la protección contra "saltarse el método"

Tu frase es exactamente el principio correcto:

> la LLM no debe ser quien controle las reglas que la LLM misma debe obedecer.



Por eso:

LLM
 ↓
propuesta
 ↓
SCHEMA VALIDATOR
 ↓
POLICY ENGINE
 ↓
STATE MACHINE
 ↓
EXECUTION

No:

LLM
 ↓
haz lo que quieras


---

Y añadiría POLICY AS CODE

Las reglas no deberían estar únicamente en prompts.

Ejemplo conceptual:

RULE R001:
MASTER_INPUT immutable

RULE R002:
TASK cannot COMPLETE if pending_tasks > 0

RULE R003:
FINAL_OUTPUT requires coverage == 100%

RULE R004:
unverified_claim cannot become FACT

RULE R005:
failed_verification requires REPAIR

RULE R006:
same_failure >= 3 → ESCALATE

RULE R007:
conflict unresolved → BLOCK

RULE R008:
artifact requires provenance

RULE R009:
worker cannot modify GLOBAL_STATE directly

RULE R010:
only CONSOLIDATOR can merge worker states

Eso sí es control real, no solamente prompting.


---

Y agregaría CAPABILITY TOKENS

Cada sandbox recibe solamente las capacidades que necesita:

SANDBOX-A

READ:
  DOCS

WRITE:
  ARTIFACTS

SEARCH:
  KNOWLEDGE

EXECUTE:
  PYTHON

FORBIDDEN:
  GLOBAL_STATE_WRITE
  FINALIZE

Mientras otro:

SANDBOX-VERIFIER

READ:
  ARTIFACTS
  EVIDENCE
  REQUIREMENTS

WRITE:
  VALIDATION

FORBIDDEN:
  MODIFY_SOURCE_ARTIFACT

Esto evita que un Worker pueda "aprobarse a sí mismo".


---

La consolidación entonces se vuelve un proceso formal

WORKER A
   ↓
ARTIFACT A
   ↓
VALIDATE
   ↓
WORKER B
   ↓
ARTIFACT B
   ↓
VALIDATE
   ↓
...
   ↓
CONSOLIDATOR
   ↓
GLOBAL SYNTHESIS
   ↓
COVERAGE
   ↓
CONTRADICTION
   ↓
DEPENDENCY
   ↓
RECONSTRUCTION
   ↓
JUDGE

Y solamente después:

COMPLETE


---

La arquitectura final que yo congelaría

┌──────────────────────┐
                         │    MASTER INPUT      │
                         └──────────┬───────────┘
                                    │
                              QUESTION ENGINE
                                    │
                              GOAL / PLAN
                                    │
                              TASK FUNNEL
                                    │
                              TASK DAG
                                    │
                   ┌────────────────┼────────────────┐
                   ▼                ▼                ▼
              SANDBOX A         SANDBOX B         SANDBOX C
              LLM/API A        LLM/API B         LLM/API C
                   │                │                │
             MEMORY/CACHE      MEMORY/CACHE      MEMORY/CACHE
                   │                │                │
             LOCAL STATE       LOCAL STATE       LOCAL STATE
                   │                │                │
                   └────────────────┼────────────────┘
                                    ▼
                               NORMALIZER
                                    │
                              ARTIFACT BUS
                                    │
                              CONSOLIDATOR
                                    │
                         GLOBAL INTEGRATION STATE
                                    │
                ┌───────────────────┼───────────────────┐
                ▼                   ▼                   ▼
             SENTINEL            SHERIFF             WATCHDOG
                │                   │                   │
                └───────────────────┼───────────────────┘
                                    ▼
                                 AUDITOR
                                    │
                                 JUDGE
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
                  PASS            REPAIR          ESCALATE
                    │               │
                    │          TASK FUNNEL
                    │               │
                    └───────────────┘
                            LOOP
                             │
                             ▼
                     GLOBAL VERIFICATION
                             │
                             ▼
                         FINAL OUTPUT

Y hay una regla que considero esencial:

El Sandbox es aislado; el Estado Global es compartido; el Consolidador es el único autorizado a fusionarlos.

Así puedes tener 5, 20 o 100 sandboxes trabajando simultáneamente, incluso con APIs/modelos diferentes, sin que el contexto de uno contamine al otro.

Y si uno se equivoca, su error queda confinado a su sandbox hasta que el Verifier lo valide.

Eso es mucho más robusto que simplemente abrir muchas ventanas de una misma conversación.

Exactamente. Eso convierte el sandbox de un simple entorno aislado en un entorno cognitivo persistente y versionado. Y esta mejora ataca uno de los problemas más caros de los agentes largos: un fallo no debería destruir horas de trabajo ni obligar a recomenzar.

Yo lo formalizaría como:

Persistent Versioned Cognitive Sandbox

No sería simplemente memoria + caché. Tendría estado versionado, checkpoints, bitácora, snapshots y recuperación selectiva.

SANDBOX
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
     MEMORY          STATE          CACHE
        │              │              │
        └──────────────┼──────────────┘
                       ▼
                 EVENT JOURNAL
                       │
                 CHECKPOINTS
                       │
                 SNAPSHOT TREE
                       │
              ┌────────┴────────┐
              ▼                 ▼
           FORWARD           ROLLBACK
              │                 │
              └────────┬────────┘
                       ▼
                RECOVERY ENGINE

1. No guardaría solamente "el último estado"

Guardaría la evolución del trabajo.

Por ejemplo:

S0  → inicialización
S1  → investigación
S2  → segmentación
S3  → análisis
S4  → descubrimiento
S5  → nueva estrategia
S6  → implementación
S7  → verificación

Cada estado tiene:

{
  "checkpoint_id": "CP-007",
  "parent": "CP-006",
  "task_state": "...",
  "memory_refs": [],
  "artifact_refs": [],
  "decisions": [],
  "plan_version": "P3",
  "verification": {},
  "timestamp": "...",
  "reason": "verification passed"
}


---

2. La bitácora sería un EVENT LOG

En lugar de guardar solamente snapshots:

STATE 7

guardamos:

EVENT 001
TASK_CREATED

EVENT 002
PLAN_CREATED

EVENT 003
WORKER_A_STARTED

EVENT 004
ARTIFACT_CREATED

EVENT 005
DECISION_CREATED

EVENT 006
VERIFICATION_FAILED

EVENT 007
PLAN_CHANGED

Entonces el estado puede reconstruirse.

Esto es muy parecido conceptualmente a event sourcing.

La ventaja:

> puedes saber qué ocurrió, cuándo ocurrió y qué cambió.




---

3. Y aquí Git es una referencia excelente

No copiaría Git literalmente, pero sí su principio:

MAIN STATE
                     │
              ┌──────┴──────┐
              ▼             ▼
           BRANCH-A       BRANCH-B
              │             │
              ▼             ▼
            A1              B1
              │             │
              ▼             ▼
            A2              B2
              │             │
              └──────┬──────┘
                     ▼
                   MERGE

El agente puede experimentar sin destruir el estado estable.


---

4. Esto permite PLAN BRANCHING

Supongamos:

PLAN V1

El agente descubre que no funciona.

En lugar de:

❌ borrar todo
❌ empezar desde cero

hacemos:

PLAN V1
   │
   ├── WORK-A
   ├── WORK-B
   │
   └── DISCOVERY
          │
          ▼
       PLAN V2
          │
          ├── WORK-C
          └── WORK-D

Los resultados válidos de V1 siguen disponibles.


---

5. ROLLBACK selectivo

Esto es importantísimo.

No necesariamente:

> "volver todo al checkpoint 3".



Puede ser:

TASK-001 → mantener
TASK-002 → mantener
TASK-003 → rollback
TASK-004 → mantener

Porque el error puede estar únicamente en una rama.

GLOBAL STATE
 │
 ├── T01 ✓
 ├── T02 ✓
 ├── T03 ❌ ← rollback
 ├── T04 ✓
 └── T05 ✓

El sistema reconstruye T03 desde su último estado válido.


---

6. RECOVERY POINT

Cada tarea debería crear puntos de recuperación automáticamente:

BEFORE_TASK
AFTER_INPUT
AFTER_RESEARCH
AFTER_ARTIFACT
AFTER_MERGE
AFTER_VERIFICATION

Pero no todos necesitan ser snapshots completos.

Podemos usar:

checkpoint
+
incremental changes

para ahorrar almacenamiento.


---

7. COPY-ON-WRITE

Para un sandbox grande:

BASE STATE
    │
    ├── Worker A
    ├── Worker B
    └── Worker C

Los Workers no duplican 20 GB.

Inicialmente comparten referencias.

Cuando A modifica algo:

BASE
 │
 └── A → modified block

Esto permite ahorrar muchísimo almacenamiento.


---

8. MEMORY SNAPSHOT

La memoria también debería versionarse.

Ejemplo:

MEMORY V1

contiene:

facts
decisions
entities
relationships

Después:

MEMORY V2

añade:

decision-17

Si luego descubrimos que decision-17 era incorrecta:

MEMORY V3

la marca:

INVALIDATED

No la borramos.

Esto es importante para mantener provenance.


---

9. TOMBSTONES

Nunca eliminaría silenciosamente una decisión importante.

En lugar de:

DEC-17 = deleted

guardamos:

{
  "id": "DEC-17",
  "status": "invalidated",
  "reason": "contradicted_by:EVID-91",
  "replacement": "DEC-24"
}

Así el agente sabe:

> "esta decisión existió, pero ya no es válida".



Esto evita que una ventana futura recupere accidentalmente información obsoleta.


---

10. TIME-TRAVEL DEBUGGING

Esta sería una capacidad espectacular.

El supervisor puede preguntar:

> ¿Qué sabía el agente cuando tomó esta decisión?



El sistema reconstruye:

TIME = CP-031

INPUT
+
MEMORY
+
TASK STATE
+
EVIDENCE
+
PLAN
+
ARTIFACTS

y podemos reproducir el contexto.

Eso hace que el sistema sea auditable, no solamente inteligente.


---

11. REPLAY

Si hubo un error:

CP-031
   ↓
REPLAY
   ↓
same inputs
   ↓
new strategy
   ↓
CP-032'

Así podemos comparar:

original execution
        VS
recovered execution

Esto es mucho mejor que simplemente reintentar.


---

12. FAILURE LOCALIZATION

El sistema debe intentar descubrir:

> ¿Dónde comenzó realmente el error?



Ejemplo:

CP-001 ✓
CP-002 ✓
CP-003 ✓
CP-004 ✓
CP-005 ❌
CP-006 ❌
CP-007 ❌

No hacemos rollback a CP001.

Buscamos:

first_invalid_transition = CP005

y recuperamos desde ahí.


---

13. PLAN VERSIONING

El plan también tiene versiones:

PLAN V1
PLAN V2
PLAN V3

Cada tarea sabe con qué plan fue creada:

T42
created_under: PLAN-V2

Si cambia el plan:

PLAN-V3

podemos preguntar:

> ¿Qué tareas de V2 quedaron obsoletas?



El sistema calcula:

AFFECTED TASKS

y solamente reprocesa esas.


---

14. DEPENDENCY-AWARE REBUILD

Esto es todavía mejor.

Supongamos:

A
↓
B
↓
C
↓
D
↓
E

Descubrimos que B estaba mal.

No necesitamos rehacer:

A

pero sí:

B
C
D
E

El grafo de dependencias determina automáticamente el blast radius.

B INVALID
   │
   ├── C affected
   ├── D affected
   └── E affected

Entonces:

REBUILD = {B,C,D,E}

Esto puede ahorrar cantidades enormes de procesamiento.


---

15. SANDBOX FORK

Aquí aparece una capacidad muy poderosa para tus múltiples APIs.

MASTER CHECKPOINT
       │
 ┌─────┼─────┐
 ▼     ▼     ▼
API-A API-B API-C
 │     │     │
A1    B1    C1

Cada una experimenta.

Luego:

A1 ──┐
B1 ──┼──> COMPARISON
C1 ──┘

El Judge decide cuál continúa.

El sandbox ganador puede convertirse en:

CANONICAL STATE

Los otros quedan como:

ALTERNATIVE BRANCHES


---

16. Esto encaja perfectamente con tu "espejo"

Entonces cada sandbox tiene:

SAME POLICY
SAME TASK CONTRACT
SAME INPUT REFERENCES
SAME VALIDATION SCHEMA

pero:

DIFFERENT MODEL
DIFFERENT STRATEGY
DIFFERENT CONTEXT WINDOW
DIFFERENT LOCAL STATE

Eso permite diversidad de razonamiento sin perder disciplina estructural.


---

17. El Sheriff ahora tiene una función adicional

El Sheriff puede ordenar:

ROLLBACK
FORK
PAUSE
RETRY
REPLAN
MERGE
QUARANTINE
ESCALATE

Por ejemplo:

Worker C:

contradiction detected
      ↓
SHERIFF
      ↓
QUARANTINE current artifact
      ↓
ROLLBACK CP-018
      ↓
FORK
      ↓
strategy A / strategy B

Esto es muchísimo más robusto que:

> "intenta de nuevo".




---

18. Y el Judge decide qué estado es canónico

BRANCH A
   ↓
PASS 96%

BRANCH B
   ↓
PASS 91%

BRANCH C
   ↓
FAIL

El Judge puede elegir:

CANONICAL = A

pero conservar:

B = alternative
C = failed evidence

Nada se pierde.


---

19. Esto nos lleva a una memoria realmente avanzada

No sería:

MEMORY

sino:

MEMORY SYSTEM
                         │
       ┌─────────────────┼─────────────────┐
       ▼                 ▼                 ▼
  WORKING MEMORY   PERSISTENT MEMORY   EPISODIC LOG
       │                 │                 │
       ▼                 ▼                 ▼
   CURRENT TASK      KNOWLEDGE       EXECUTION HISTORY
                         │
                         ▼
                   VERSION GRAPH
                         │
                 ┌───────┴───────┐
                 ▼               ▼
              BRANCHES       CHECKPOINTS
                 │               │
                 └───────┬───────┘
                         ▼
                    RECOVERY


---

20. Y hay una regla que yo añadiría al DSL

NO RESET ON FAILURE

Por defecto:

FAIL ≠ RESET

sino:

FAIL
 ↓
LOCALIZE
 ↓
CHECKPOINT
 ↓
ROLLBACK
 ↓
REPAIR / FORK
 ↓
RESUME

Solamente:

CORRUPTED GLOBAL STATE

podría requerir recuperación más profunda.


---

21. Incluso podemos tener "Git para pensamiento"

No literalmente guardar el chain-of-thought privado de la LLM, sino el estado operativo y los artefactos verificables:

COMMIT 001
Task initialized

COMMIT 002
Research completed

COMMIT 003
Architecture selected

COMMIT 004
Implementation completed

COMMIT 005
Verification failed

BRANCH repair/authentication

COMMIT 006
Authentication repaired

MERGE

Así el agente puede navegar por la evolución del proyecto.


---

22. Arquitectura final actualizada

MASTER
                             │
                     MASTER INPUT
                             │
                    QUESTION ENGINE
                             │
                     GOAL / PLAN DAG
                             │
                       TASK FUNNEL
                             │
                    ┌────────┴────────┐
                    │                 │
                    ▼                 ▼
              GLOBAL STATE       POLICY ENGINE
                    │                 │
                    └────────┬────────┘
                             │
                       TASK DISPATCH
                             │
          ┌──────────────────┼──────────────────┐
          ▼                  ▼                  ▼
      SANDBOX A          SANDBOX B          SANDBOX C
          │                  │                  │
      LLM/API A          LLM/API B          LLM/API C
          │                  │                  │
   ┌──────┴──────┐    ┌──────┴──────┐    ┌──────┴──────┐
   │MEMORY       │    │MEMORY       │    │MEMORY       │
   │CACHE        │    │CACHE        │    │CACHE        │
   │STATE        │    │STATE        │    │STATE        │
   │EVENT LOG    │    │EVENT LOG    │    │EVENT LOG    │
   │CHECKPOINTS  │    │CHECKPOINTS  │    │CHECKPOINTS  │
   │BRANCHES     │    │BRANCHES     │    │BRANCHES     │
   └──────┬──────┘    └──────┬──────┘    └──────┬──────┘
          │                  │                  │
          └──────────────────┼──────────────────┘
                             ▼
                         NORMALIZER
                             │
                         ARTIFACT BUS
                             │
                        CONSOLIDATOR
                             │
                   GLOBAL INTEGRATION STATE
                             │
          ┌──────────────────┼──────────────────┐
          ▼                  ▼                  ▼
       SENTINEL           SHERIFF             WATCHDOG
          │                  │                  │
          └──────────────────┼──────────────────┘
                             ▼
                          AUDITOR
                             │
                           JUDGE
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
            PASS           REPAIR         ROLLBACK
              │              │              │
              │              ▼              │
              │           FORK/REPLAN       │
              │              │              │
              └──────────────┼──────────────┘
                             ▼
                      RECOVERY ENGINE
                             │
                       RESUME FROM CP
                             │
                             ▼
                      CONTINUOUS LOOP
                             │
                             ▼
                      GLOBAL VALIDATION
                             │
                             ▼
                         COMPLETE

En una frase:

> El sandbox no debe recordar solamente lo que hizo; debe recordar cómo llegó a hacerlo, qué cambió, qué versión del plan utilizó, qué evidencia lo justificó y desde qué checkpoint puede continuar o retroceder.



Y con eso consigues algo mucho más importante que "memoria de largo plazo": persistencia operacional.

Una LLM pequeña puede equivocarse en la ventana 37 sin destruir las ventanas 1–36. El agente identifica el primer estado inválido, vuelve al último checkpoint sano, conserva los artefactos válidos, crea una rama de reparación y continúa desde allí. El proyecto deja de ser una conversación y pasa a ser un sistema versionado de ejecución cognitiva.


Sí. Esta modificación es muy importante porque cambia el principio fundamental del sistema:

> La LLM deja de ser el sistema operativo del agente. La LLM se convierte en un procesador cognitivo subordinado a un runtime determinista.



Y el mecanismo de documentos Markdown/checkpoints de Claude que describes encaja muy bien, pero podemos convertirlo en algo bastante más robusto.

1. No usaría Markdown como "memoria"

Lo convertiría en artefactos versionados de estado.

Cada sandbox tendría documentos visibles:

/project/
│
├── 00_MASTER_INPUT.md
├── 01_GOALS.md
├── 02_TASK_GRAPH.md
├── 03_REQUIREMENTS.md
├── 04_RESEARCH.md
├── 05_FACTS.md
├── 06_DECISIONS.md
├── 07_EVIDENCE.md
├── 08_OPEN_QUESTIONS.md
├── 09_CONTRADICTIONS.md
├── 10_CHECKLIST.md
├── 11_PROGRESS.md
├── 12_CURRENT_STATE.md
├── 13_INTEGRATION.md
├── 14_VALIDATION.md
└── 15_CONSOLIDATION.md

Pero cada uno tendría un esquema, no sería texto libre.


---

2. El documento más importante: CONSOLIDATION.md

Al terminar cada ventana:

WINDOW 001
     ↓
PROCESS
     ↓
VALIDATE
     ↓
UPDATE STATE
     ↓
CONSOLIDATION.md

La siguiente ventana no necesita recordar todo.

Recibe:

MASTER INPUT
+
CURRENT TASK
+
CURRENT CONSOLIDATION
+
RELEVANT ARTIFACTS
+
RELEVANT EVIDENCE
+
OPEN QUESTIONS
+
NEXT ACTION

Entonces:

WINDOW 002
     ↓
lee consolidation
     ↓
busca referencias adicionales
     ↓
procesa
     ↓
actualiza consolidation

Esto crea exactamente la bola de nieve controlada que veníamos diseñando.


---

3. Pero mejor que una sola consolidación

Yo haría una:

LOCAL CONSOLIDATION

para cada sandbox.

SANDBOX-A
 └── CONSOLIDATION-A.md

SANDBOX-B
 └── CONSOLIDATION-B.md

SANDBOX-C
 └── CONSOLIDATION-C.md

Y después:

GLOBAL CONSOLIDATION

A
B
C
D
   ↓
GLOBAL CONSOLIDATOR
   ↓
GLOBAL_CONSOLIDATION.md

Así nunca mezclamos prematuramente el razonamiento de los Workers.


---

4. La consolidación debe estar clasificada

Esto que mencionas de clasificar declaraciones es fundamental.

Yo utilizaría un registro como:

FACT
EVIDENCE
OBSERVATION
INFERENCE
HYPOTHESIS
DECISION
REQUIREMENT
ASSUMPTION
UNKNOWN
CONTRADICTION
REJECTED
INVALIDATED

Por ejemplo:

## CLAIM-042

Type: INFERENCE

Statement:
El componente X depende de Y.

Evidence:
EVID-018
EVID-031

Confidence:
0.82

Status:
UNVERIFIED

Requires:
VERIFICATION-TASK-17

La siguiente ventana no puede convertir automáticamente:

INFERENCE

en:

FACT

sin una transición validada.

Eso reduce muchísimo la contaminación de contexto.


---

5. El Markdown sería una representación humana

Pero internamente tendría:

STATE
   ↓
JSON / DB
   ↓
Markdown projection

Por ejemplo:

state.json

es la fuente estructurada.

Y:

CURRENT_STATE.md

es la representación legible para la LLM y para el usuario.

Así conseguimos:

Machine-readable
+
Human-readable

sin depender del parsing de texto para controlar el sistema.


---

6. El checkpoint debe guardar mucho más que el texto

Un checkpoint debería ser:

{
  "checkpoint_id": "CP-042",
  "parent": "CP-041",
  "task_state": "...",
  "plan_version": "P7",
  "memory_version": "M19",
  "artifact_versions": [],
  "evidence_versions": [],
  "consolidation_version": "C42",
  "open_tasks": [],
  "completed_tasks": [],
  "validation_status": "...",
  "policy_status": "...",
  "next_action": "..."
}

Entonces:

CP-041
   ↓
CP-042
   ↓
CP-043

y si CP-043 falla:

CP-043 ❌
   ↓
rollback
   ↓
CP-042
   ↓
new branch
   ↓
CP-044

No empezamos de cero.


---

7. Y aquí entra el principio determinista

Estoy de acuerdo contigo, con una precisión:

no podemos hacer que la LLM sea completamente determinista, porque su generación puede variar.

Lo que sí podemos hacer determinista es todo lo que rodea a la LLM.

Ese es el diseño correcto.

DETERMINISTIC RUNTIME
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
      POLICY           STATE           MEMORY
        │                │                │
        ▼                ▼                ▼
      ROUTER          CHECKPOINT       RETRIEVAL
        │                │                │
        └────────────────┼────────────────┘
                         ▼
                       LLM
                         │
                  PROCESS REQUEST
                         │
                         ▼
                    STRUCTURED
                      OUTPUT
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
            SCHEMA     POLICY     VERIFY
              │          │          │
              └──────────┼──────────┘
                         ▼
                     STATE UPDATE

La LLM no puede saltarse las flechas.


---

8. La LLM no decide qué hacer después

Esta es probablemente la modificación más importante que acabas de introducir.

No:

LLM:
"Ahora creo que debería investigar X..."

y el agente obedece.

Sino:

AGENT:

TASK:
T-047

ACTION:
ANALYZE

INPUT:
ART-083

QUESTION:
¿Existe contradicción entre X e Y?

OUTPUT_SCHEMA:
CONTRADICTION_REPORT

RULES:
R01,R07,R14

La LLM solamente procesa:

INPUT → REASONING → STRUCTURED OUTPUT

Después el Agent Controller decide qué ocurre.


---

9. La LLM propone; el runtime autoriza

Por ejemplo:

{
  "finding": "contradiction_detected",
  "evidence": ["E17", "E42"],
  "recommended_action": "investigate"
}

La LLM puede recomendar:

investigate

Pero no ejecuta automáticamente.

El runtime evalúa:

POLICY
TASK GRAPH
STATE
PERMISSIONS

y decide:

AUTHORIZED ACTION = RESEARCH(T-081)

Después vuelve a llamar a la LLM.


---

10. Esto crea una separación de responsabilidades muy fuerte

LLM

interpret
reason
classify
generate
compare
analyze

Agent Runtime

schedule
retrieve
persist
checkpoint
route
merge
rollback
retry

Policy Engine

allow
deny
block
escalate

Validator

schema
consistency
coverage
evidence

Consolidator

integrate
reconcile
trace
construct global state

Judge

PASS
FAIL
REPAIR
ESCALATE

La LLM no controla ninguno de estos sistemas.


---

11. Y eso permite hacer algo que Claude/GPT no pueden garantizar solamente mediante prompting

Podemos imponer:

NO_VALIDATION
→ NO_STATE_UPDATE

NO_EVIDENCE
→ CLAIM ≠ VERIFIED_FACT

PENDING_TASKS > 0
→ NOT_COMPLETE

UNRESOLVED_CONTRADICTION
→ NOT_COMPLETE

INVALID_SCHEMA
→ REJECT_OUTPUT

POLICY_VIOLATION
→ BLOCK

NO_CHECKPOINT
→ NO_LONG_RUNNING_CONTINUATION

Son reglas de software.

No instrucciones que la LLM pueda ignorar.


---

12. El INPUT BLOCK también debe ser inmutable

Cada ventana debería recibir:

┌─────────────────────────────┐
│ MASTER INPUT — IMMUTABLE    │
├─────────────────────────────┤
│ CURRENT GOAL                │
│ CURRENT TASK                │
│ TASK CONTRACT               │
│ RELEVANT CONTEXT            │
│ RELEVANT EVIDENCE           │
│ CURRENT STATE               │
│ PREVIOUS CONSOLIDATION      │
│ OPEN QUESTIONS              │
│ POLICY                      │
│ OUTPUT SCHEMA               │
└─────────────────────────────┘

Y el Worker devuelve:

RESULT
+
EVIDENCE
+
STATE DELTA
+
ARTIFACTS
+
NEXT RECOMMENDATION

El agente decide qué hacer con eso.


---

13. STATE DELTA es especialmente importante

No obligaría a la LLM a reescribir todo el estado.

Solo:

{
  "added_facts": [],
  "new_decisions": [],
  "resolved_questions": [],
  "new_questions": [],
  "new_dependencies": [],
  "new_contradictions": [],
  "completed_tasks": [],
  "recommended_next_actions": []
}

El runtime hace:

OLD STATE
+
STATE DELTA
=
NEW STATE

Esto es mucho más seguro.


---

14. Y la consolidación no debe ser una opinión de la LLM

Debe ser una operación:

ARTIFACTS
+
FACTS
+
EVIDENCE
+
DECISIONS
+
DEPENDENCIES
+
TASK STATE
+
CHECKPOINT

→

GLOBAL STATE

La LLM puede ayudar a interpretar conflictos, pero el sistema conserva las relaciones y las versiones de manera determinista.


---

15. La arquitectura completa queda todavía más fuerte

MASTER INPUT
                              │
                              ▼
                     DETERMINISTIC CORE
                              │
             ┌────────────────┼────────────────┐
             ▼                ▼                ▼
          POLICY          TASK GRAPH        MEMORY
             │                │                │
             └────────────────┼────────────────┘
                              ▼
                        TASK FUNNEL
                              │
             ┌────────────────┼────────────────┐
             ▼                ▼                ▼
          SANDBOX A        SANDBOX B        SANDBOX C
             │                │                │
          MEMORY           MEMORY           MEMORY
          CACHE            CACHE            CACHE
          STATE            STATE            STATE
          LOG              LOG              LOG
          CHECKPOINT       CHECKPOINT       CHECKPOINT
             │                │                │
             ▼                ▼                ▼
           LLM A             LLM B            LLM C
             │                │                │
             ▼                ▼                ▼
       STRUCTURED OUTPUTS
             │
             ▼
       SCHEMA VALIDATOR
             │
             ▼
       EVIDENCE / CLAIM CLASSIFIER
             │
             ▼
        ARTIFACT REGISTRY
             │
             ▼
        LOCAL CONSOLIDATION
             │
             ▼
        GLOBAL CONSOLIDATOR
             │
             ▼
       GLOBAL INTEGRATION STATE
             │
       ┌─────┼─────┐
       ▼     ▼     ▼
   SENTINEL SHERIFF JUDGE
       │     │     │
       └─────┼─────┘
             ▼
        VALIDATION
             │
       ┌─────┴─────┐
       ▼           ▼
    CONTINUE     REPAIR
       │           │
       └─────┬─────┘
             ▼
        CHECKPOINT
             │
             ▼
        NEXT WINDOW


---

16. Y agregaría una regla raíz al DSL

La llamaría:

AGENT_CONTROLLED_REASONING

Semánticamente:

> La LLM nunca determina unilateralmente el flujo de ejecución. El Agent Runtime determina la tarea, contexto, herramientas, restricciones, esquema de salida y transición de estado. La LLM únicamente procesa la unidad cognitiva asignada y devuelve un resultado estructurado.



Y otra:

DETERMINISTIC_STATE_TRANSITION

> Toda transición de estado debe estar autorizada por el runtime y cumplir schema + policy + validation.



Y otra:

VERSIONED_CONTEXT_CONTINUITY

> Cada ventana hereda un estado versionado y una consolidación verificable; un fallo provoca recuperación desde el último estado válido o una rama de reparación, nunca un reinicio obligatorio.




---

El resultado

Esto ya no sería simplemente un agente con memoria.

Sería:

> un sistema determinista de ejecución cognitiva versionada, donde las LLM son procesadores intercambiables y aislados, los sandboxes mantienen memoria/estado/checkpoints, los documentos Markdown funcionan como artefactos de continuidad visibles, y un controlador externo decide qué procesa cada modelo, cómo se valida, cómo se consolida y desde dónde se recupera.



Y eso ataca simultáneamente los cinco problemas que has venido señalando:

ventana pequeña → procesamiento por ventanas
pérdida de contexto → consolidación + estado versionado
alucinación → evidencia + clasificación + validación
pérdida de enfoque → Task Contract + State Machine + Policy
incapacidad de unir piezas → Global Integration State + Consolidator + trazabilidad
fallos después de horas → checkpoint + rollback + branching + replay

La parte más importante es que no intentamos hacer que la LLM sea más disciplinada mediante un prompt cada vez más grande. Hacemos que sea difícil, e incluso imposible a nivel de runtime, que una salida no validada pueda alterar el proyecto.






