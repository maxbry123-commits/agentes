Falta integrar al kernel o a la extensión del kernel 


Sí. Lo llevaría mucho más lejos: el sistema no debería almacenar “roles”, prompts o métodos como texto muerto. Debe convertirlos en artefactos ejecutables, versionados y gobernados por el kernel.

La idea central sería:

> El LLM descubre y diseña; el Evolution Kernel compila; el runtime determinista ejecuta.



No convertiría todo en determinista —la generación de código, interpretación y decisiones nuevas siguen necesitando modelos—, pero todo lo que pueda quedar convertido en estructura ejecutable debe salir del prompt y pasar al runtime.

1. El concepto: Role → Engineering Capability

Hoy:

"Actúa como ingeniero Python"
        ↓
System Prompt
        ↓
LLM intenta comportarse como Python developer

Tu sistema:

"Necesito especialización Python"
        ↓
Specialty Discovery
        ↓
Research
        ↓
Official docs
        ↓
Libraries
        ↓
Examples
        ↓
Community patterns
        ↓
Benchmarks
        ↓
Capability extraction
        ↓
Role Compiler
        ↓
ENGINEER_PYTHON

Y ENGINEER_PYTHON ya no es un prompt.

Es un paquete ejecutable del kernel.


---

2. El paquete de una especialidad

Por ejemplo:

extensions/
└── specialties/
    └── python_engineering/
        ├── manifest.yaml
        ├── capability.yaml
        ├── goals.yaml
        ├── inputs.yaml
        ├── outputs.yaml
        ├── methods/
        ├── workflows/
        ├── schemas/
        ├── validators/
        ├── sheriff/
        ├── adapters/
        ├── libraries.lock
        ├── knowledge/
        ├── examples/
        ├── benchmarks/
        ├── failures/
        ├── README.md
        └── LEARNING.md

Entonces:

Python Engineer no es un prompt.

Es:

knowledge
+
libraries
+
methods
+
schemas
+
validators
+
workflows
+
tools
+
goals
+
tests
+
resource policies


---

3. El sistema crea la especialidad automáticamente

Cuando recibe:

> "Necesito un especialista en Python para backend."



El Evolution Engine genera:

SPECIALTY REQUEST
        ↓
DOMAIN ANALYZER
        ↓
RESEARCH PLAN
        ↓
SOURCE DISCOVERY
        ↓
CAPABILITY EXTRACTION
        ↓
SPECIALTY COMPILER

El investigador busca, por ejemplo:

Python
├── language
├── package ecosystem
├── backend frameworks
├── async
├── testing
├── typing
├── databases
├── security
├── packaging
├── deployment
└── debugging

Pero no instala todo.

Primero construye un Specialty Manifest.


---

4. El Specialty Manifest

Ejemplo conceptual:

specialty:
  id: python.backend.engineer
  version: 1.0

domain:
  language: python
  specialization: backend

capabilities:
  - code_generation
  - code_review
  - debugging
  - testing
  - dependency_management
  - api_design
  - database_integration

methods:
  - analyze_repository
  - design_change
  - implement
  - test
  - inspect_failure
  - repair

Después el compilador genera el resto.


---

5. Tus 12 Goals

Aquí tu idea es buena, pero yo no los trataría como simples prompts.

Los convertiría en contratos I/O especializados.

Por ejemplo, Python Backend Engineer podría tener 12 objetivos:

G01 Analyze Repository
G02 Understand Architecture
G03 Design Backend
G04 Generate Python
G05 Refactor Python
G06 Integrate Dependency
G07 Design API
G08 Design Database Layer
G09 Generate Tests
G10 Debug Failure
G11 Security Review
G12 Production Validation

Cada uno tiene:

INPUT
↓
preconditions
↓
method
↓
tools
↓
LLM operations
↓
deterministic transformations
↓
validators
↓
OUTPUT

Por ejemplo:

G10 DEBUG_FAILURE

INPUT:
  error
  stacktrace
  repository
  environment

PROCESS:
  classify error
  locate source
  inspect dependencies
  propose repair
  generate patch
  execute test

OUTPUT:
  diagnosis
  patch
  evidence
  tests
  confidence

Esto ya es un programa de trabajo, no un prompt.


---

6. Los 12 Goals necesitan contratos

Yo añadiría:

GoalContract
├── input_schema
├── output_schema
├── preconditions
├── allowed_tools
├── forbidden_tools
├── workflow
├── budget
├── timeout
├── validators
├── recovery
├── evidence
└── success_conditions

Así el agente no puede simplemente responder cualquier cosa.


---

7. Los "12 Ask Council" también deben convertirse en código

Si por ASK Council te refieres a los 12 tipos de consultas/consultas especializadas al consejo de agentes, no los dejaría como:

> "pregunta a otros agentes".



Los convertiría en Council Operations.

Ejemplo:

C01 Architecture Council
C02 Implementation Council
C03 Security Council
C04 Performance Council
C05 Dependency Council
C06 Testing Council
C07 Debugging Council
C08 Database Council
C09 API Council
C10 Maintainability Council
C11 Cost Council
C12 Final Review Council

Cada uno tiene:

question_schema
participants
routing_policy
aggregation_method
decision_schema
evidence_requirement

Entonces:

Goal
 ↓
Council operation
 ↓
parallel agents
 ↓
structured responses
 ↓
deterministic aggregation
 ↓
decision


---

8. El System Prompt desaparece como mecanismo principal

Esta es una de las partes más importantes de tu propuesta.

Hoy:

SYSTEM PROMPT

"You are an expert Python engineer..."

El problema es que el modelo puede ignorarlo, reinterpretarlo o perder consistencia.

Tu sistema:

SYSTEM PROMPT
       ↓
   ANALYZER
       ↓
   EXTRACT
       ↓
   COMPILE
       ↓

produce:

DSL
+
DAG
+
Schema
+
Sheriff
+
Capability Registry

El prompt puede seguir existiendo como contexto auxiliar, pero ya no es el mecanismo de control.


---

9. El método de trabajo también se compila

Supongamos que alguien proporciona:

> "Primero analiza el proyecto, luego diseña, después implementa, ejecuta pruebas y finalmente revisa."



Actualmente:

texto
↓
LLM intenta recordarlo

Tu sistema:

method
 ↓
Method Compiler
 ↓
DAG

Por ejemplo:

ANALYZE
   ↓
ARCHITECTURE
   ↓
IMPLEMENT
   ↓
TEST
   ↓
REVIEW
   ↓
REPAIR
   ↺

Ahora el método vive en el runtime.

No depende de que el modelo lo recuerde.


---

10. Y el formato de salida también se compila

Esto es fundamental.

No:

"Devuelve un JSON con..."

como simple instrucción.

Sino:

OutputSchema
      ↓
Schema Validator
      ↓
Sheriff
      ↓
Runtime

Ejemplo:

output:
  type: code_change

  required:
    - files
    - changes
    - tests
    - evidence

  validators:
    - files_exist
    - syntax_valid
    - tests_pass
    - no_secret_leak

El modelo puede equivocarse.

El Sheriff no acepta una salida que no cumpla el contrato.


---

11. El Sheriff se convierte en el límite entre IA y realidad

La arquitectura sería:

LLM
              │
              ▼
       GENERATE / REASON
              │
              ▼
          DSL/DAG
              │
              ▼
           SCHEMA
              │
              ▼
           SHERIFF
              │
        ┌─────┴─────┐
        │           │
      PASS         FAIL
        │           │
        ▼           ▼
     EXECUTE      REPAIR

Esto permite que los modelos sean probabilísticos pero el resultado operacional esté gobernado.


---

12. El agente se convierte en compilador de especialidades

Esta sería una de las mayores diferencias respecto a un agente tradicional:

INPUT
 ↓
UNDERSTAND
 ↓
RESEARCH
 ↓
LEARN
 ↓
DESIGN
 ↓
COMPILE
 ↓
REGISTER
 ↓
EXECUTE

Y el producto final no es:

respuesta

sino:

NEW CAPABILITY


---

13. Incluso puede crear especialidades compuestas

Esto es todavía más potente.

Por ejemplo:

Python
+
PostgreSQL
+
FastAPI
+
Docker
+
AWS

puede generar:

Python Backend Engineer

Pero:

Python
+
Pandas
+
Finance
+
Colombia

puede producir:

Financial Python Analyst — Colombia

Y:

HTML
+
CSS
+
React
+
Accessibility
+
PWA

produce:

Frontend PWA Engineer

La especialidad deja de ser una identidad ficticia.

Es una composición de capabilities.


---

14. Incluso puede especializarse por país

Aquí haría una separación estricta:

CORE SPECIALTY
      +
DOMAIN PACK
      +
JURISDICTION PACK
      +
LANGUAGE PACK
      +
PROJECT PACK

Por ejemplo:

Python Engineer
       +
Accounting
       +
Colombia
       +
Spanish

El kernel no modifica Python.

Añade:

jurisdiction/colombia
domain/accounting
language/es

Eso hace que la especialidad sea modular.


---

15. El sistema puede crear especialidades desde ejemplos

Tu idea de que las LLM aprenden patrones a partir de ejemplos también se puede incorporar.

EXAMPLES
   ↓
Example Analyzer
   ↓
Pattern Extraction
   ↓
Method Extraction
   ↓
Input/Output Extraction
   ↓
Schema Generation
   ↓
Workflow Generation

Por ejemplo, 50 ejemplos de código bien estructurado pueden producir:

coding patterns
+
anti-patterns
+
validation rules
+
generation templates

Pero los ejemplos no se convierten automáticamente en verdad.

Se etiquetan:

observed
official
community
verified


---

16. La evolución real sería entonces

USER TASK
                  │
                  ▼
           CAPABILITY GAP
                  │
       ┌──────────┴──────────┐
       ▼                     ▼
  USE EXISTING          EVOLVE
  CAPABILITIES             │
                           ▼
                     RESEARCH
                           │
                     LEARN EXAMPLES
                           │
                     STUDY SOFTWARE
                           │
                     STUDY METHODS
                           │
                     STUDY SKILLS
                           │
                     STUDY LIBRARIES
                           │
                           ▼
                    SPECIALTY MODEL
                           │
                           ▼
                     ROLE COMPILER
                           │
             ┌─────────────┼──────────────┐
             ▼             ▼              ▼
            GOALS        COUNCILS       METHODS
             │             │              │
             └─────────────┼──────────────┘
                           ▼
                     DSL COMPILER
                           │
                     ┌─────┼─────┐
                     ▼     ▼     ▼
                    DAG  SCHEMA SHERIFF
                     │     │     │
                     └─────┼─────┘
                           ▼
                    NATIVE EXTENSION
                           │
                           ▼
                       EXECUTE
                           │
                           ▼
                       OBSERVE
                           │
                           ▼
                       LEARN

17. Y aquí está la mejora de fondo

Yo no lo llamaría simplemente Role System.

Lo llamaría algo como:

Specialty Compiler / Capability Compiler

Porque realmente hace esto:

> Convierte conocimiento especializado, software, documentación, ejemplos, skills, métodos de trabajo y experiencia en capacidades ejecutables del kernel.



El flujo sería:

PROMPT
  ↓
KNOWLEDGE
  ↓
METHOD
  ↓
CAPABILITY
  ↓
DSL
  ↓
DAG
  ↓
SCHEMA
  ↓
SHERIFF
  ↓
EXECUTABLE CODE
  ↓
NATIVE KERNEL EXTENSION

Y después el propio sistema puede mejorar esa extensión.

La arquitectura resultante tiene una propiedad muy importante: el modelo no necesita recordar cómo ser un ingeniero Python, contador, investigador o arquitecto de software en cada conversación. El conocimiento operativo que vale la pena conservar queda convertido en estructuras persistentes y ejecutables; el modelo se utiliza para descubrir, razonar y generar lo nuevo.

Eso es considerablemente más robusto que intentar solucionar el problema mediante un system prompt cada vez más grande.

Exactamente. Yo lo diseñaría como un compilador de métodos y políticas, no como un sistema que almacena prompts.

La diferencia fundamental es:

ANTES
System Prompt → LLM intenta obedecer

NUEVO SISTEMA
System Prompt / método / ejemplos
            ↓
      Analyzer
            ↓
   Method Extraction
            ↓
   Policy Extraction
            ↓
      DSL Compiler
            ↓
        DAG + Schema
            ↓
        Sheriff Rules
            ↓
       Code Generator
            ↓
  Kernel Extension
            ↓
       EXECUTABLE

Y después esa extensión puede editarse a sí misma mediante el mismo compilador.


---

1. El prompt es solamente materia prima

Si encuentra:

> "Primero analiza el problema, después revisa dependencias, luego implementa, ejecuta pruebas y si falla corrige."



No guardaría eso como:

system_prompt.md

Lo transforma en:

METHOD
├── analyze
├── dependency_scan
├── implement
├── validate
└── repair

Y después:

METHOD
   ↓
DSL
   ↓
DAG
   ↓
CODE

El prompt original puede conservarse como fuente/evidencia, pero deja de ser el mecanismo de ejecución.


---

2. El Schema define qué entra y qué sale

Ejemplo conceptual:

GOAL: repair_code

INPUT
├── repository
├── error
├── logs
├── environment
└── constraints

PROCESS
├── inspect
├── diagnose
├── patch
├── validate
└── repair_if_failed

OUTPUT
├── diagnosis
├── patch
├── changed_files
├── validation
└── evidence

El compilador produce un contrato formal:

InputSchema
OutputSchema
Preconditions
Postconditions

El agente ya no puede simplemente decir:

> "Creo que está reparado."



Tiene que producir una salida que satisfaga el esquema.


---

3. El Sheriff es la parte estricta

El Sheriff no es otro prompt.

Es código ejecutable.

Por ejemplo:

Sheriff
 ├── validate_input()
 ├── validate_output()
 ├── validate_files()
 ├── validate_dependencies()
 ├── validate_policy()
 ├── validate_budget()
 ├── validate_side_effects()
 └── validate_success()

Entonces:

LLM
 ↓
genera propuesta
 ↓
Schema
 ↓
Sheriff
 ↓
PASS → ejecutar
FAIL → reparar

El modelo puede ser probabilístico.

El control operacional no.


---

4. El método de trabajo también se convierte en código

Por ejemplo:

ANALYZE
   ↓
PLAN
   ↓
IMPLEMENT
   ↓
TEST
   ↓
REVIEW
   ↓
REPAIR
      │
      └──── FAIL ──→ IMPLEMENT

El compilador puede convertirlo en:

WorkflowDefinition
      ↓
DAGDefinition
      ↓
RuntimeExecutor

El runtime ejecuta los nodos.

Por tanto, el modelo no tiene que recordar el método.

El kernel ya lo tiene.


---

5. Pero hay una segunda capacidad todavía más importante: editarlo

Aquí está la parte que creo que debes añadir explícitamente.

No solamente:

Prompt → Compiler → Extension

sino:

Existing Extension
       ↓
Extension Analyzer
       ↓
Understand current behavior
       ↓
Change Request
       ↓
Patch Compiler
       ↓
New Version

Ejemplo:

La extensión originalmente tiene:

ANALYZE
→ CODE
→ TEST

Después aprende que antes de programar necesita analizar arquitectura.

Puede recibir:

ADD:
architecture_review
BEFORE:
code_generation

El sistema no reescribe todo.

Hace:

Extension v1
    ↓
AST / DSL representation
    ↓
Patch
    ↓
Extension v2

Resultado:

ANALYZE
 ↓
ARCHITECTURE_REVIEW
 ↓
CODE
 ↓
TEST


---

6. Esto requiere una representación intermedia

Yo añadiría un IR — Intermediate Representation.

Sería el corazón del sistema.

Prompt
Method
Skill
Documentation
Examples
Software
Agent
Dataset
        ↓
   Knowledge IR
        ↓
 Capability IR
        ↓
 Workflow IR
        ↓
 Policy IR
        ↓
 Executable Extension

Así no dependes de que un LLM transforme directamente lenguaje natural → código.

El sistema primero crea una representación estructurada.


---

7. El IR permite editar sin destruir

Ejemplo:

workflow:
  id: python_backend
  version: 4

nodes:
  - analyze
  - architecture
  - implement
  - test
  - review

edges:
  - analyze -> architecture
  - architecture -> implement
  - implement -> test
  - test -> review

Si necesita añadir seguridad:

review

se puede modificar estructuralmente:

test
 ↓
security_review
 ↓
review

No necesitas regenerar toda la extensión.


---

8. El Sheriff también debe evolucionar

Esto es todavía más importante.

No solo:

Workflow v1 → Workflow v2

sino:

Workflow
Schema
Sheriff

deben evolucionar juntos.

Ejemplo:

La extensión aprende que una API nunca debe aceptar una contraseña en logs.

El sistema puede crear:

Policy:
NO_SECRET_IN_LOGS

y convertirla en:

Sheriff Rule

Después:

if secret_detected_in_log:
    reject()

Eso ya es una regla ejecutable, no una instrucción al LLM.


---

9. El agente aprende a construir Sheriffs

Aquí está la evolución interesante.

Puede estudiar:

documentación
+
código existente
+
errores
+
issues
+
ejemplos
+
prácticas de ingeniería

y detectar:

Invariant
Constraint
Precondition
Postcondition
Failure condition
Security rule
Quality rule

Entonces:

Knowledge
 ↓
Rule Extraction
 ↓
Rule DSL
 ↓
Sheriff Compiler
 ↓
Executable Validator

Por ejemplo:

"Esta operación debe ser idempotente."

↓

invariant:
  operation.idempotent == true

↓

Sheriff:
validate_idempotency()


---

10. El sistema aprende a modificar sus propios métodos

Supongamos que después de 100 ejecuciones detecta:

implement → test

produce demasiados errores.

El sistema analiza trazabilidad:

failure_analysis
       ↓
pattern detected
       ↓
missing architecture validation
       ↓
proposed improvement

Propone:

implement

cambiarlo por:

architecture
→ implementation

Pero la modificación se hace sobre la representación estructurada:

Workflow IR

no sobre un prompt gigante.


---

11. Tres niveles de evolución

Yo implementaría:

Nivel 1 — Paramétrica

Cambia:

timeouts
budgets
model
parallelism
thresholds

Sin cambiar el código.

Nivel 2 — Estructural

Cambia:

DAG
schemas
methods
policies
validators

Nivel 3 — Código

Cuando realmente hace falta:

new adapter
new capability
new executor
new parser
new integration

genera código real.

Esto reduce muchísimo el riesgo.


---

12. Y el resultado final

Una especialidad ya compilada podría verse conceptualmente así:

extensions/
└── python_backend/
    │
    ├── capability.py
    ├── runtime.py
    ├── methods.dsl
    ├── workflow.dag
    ├── schemas/
    ├── sheriff/
    │   ├── input.py
    │   ├── output.py
    │   ├── security.py
    │   └── quality.py
    │
    ├── adapters/
    ├── libraries.lock
    ├── knowledge/
    ├── examples/
    ├── benchmarks/
    └── evolution/
        ├── history.json
        ├── patches/
        └── decisions/

Eso sí es una especialidad instalada en el kernel.

No:

"You are a Python expert..."

sino:

PythonBackendCapability
        +
PythonWorkflow
        +
PythonSchemas
        +
PythonSheriff
        +
PythonAdapters
        +
PythonMethods


---

13. La arquitectura que recomiendo

La pieza nueva que falta en tu diseño es:

┌─────────────────────┐
              │  KNOWLEDGE SOURCES  │
              │ prompts / skills /  │
              │ repos / examples /  │
              │ docs / experience   │
              └──────────┬──────────┘
                         ↓
                ┌────────────────┐
                │ LEARNING ENGINE │
                └───────┬────────┘
                        ↓
                 ┌──────────────┐
                 │   IR / AST   │
                 └──────┬───────┘
                        ↓
             ┌─────────────────────┐
             │ SPECIALTY COMPILER  │
             └──────────┬──────────┘
                        ↓
          ┌─────────────┼─────────────┐
          ↓             ↓             ↓
       METHODS         DAG         SCHEMAS
          │             │             │
          └─────────────┼─────────────┘
                        ↓
                 SHERIFF COMPILER
                        ↓
                 EXECUTABLE CODE
                        ↓
                KERNEL EXTENSION
                        │
                        ▼
                    RUNTIME
                        │
                        ▼
                   EXPERIENCE
                        │
                        ▼
                 LEARNING ENGINE
                        │
                        └──────→ PATCH
                                  ↓
                             NEW VERSION

La regla fundamental

El LLM puede enseñar al sistema cómo construir una capacidad, pero la capacidad que queda instalada no depende del LLM para existir.

El LLM puede:

interpretar;

investigar;

proponer;

generar código;

descubrir patrones;

diseñar nuevas reglas.


El kernel convierte eso en:

DSL

DAG

Schema

Sheriff

validators

adapters

runtime code

versiones

patches


Y cuando aprende algo nuevo, edita la extensión existente mediante un patch estructurado, en lugar de volver a crear un prompt.

Ese mecanismo es el que convertiría realmente tu sistema de un agente basado en prompts a un sistema operativo de capacidades evolutivas.



Sí. Y con tu objetivo concreto, no estudiaría estos agentes para copiar su arquitectura, sino para hacer reverse engineering funcional: descubrir qué decisiones, invariantes, estados, protocolos y mecanismos repetibles tienen, y convertirlos en primitivas deterministas de tu kernel.

He revisado las superficies actuales de OpenClaw, Hermes y MiMo Code, y hay una conclusión importante: hay bastante más que extraer que el simple agent loop. OpenClaw separa tools, skills y plugins; Hermes tiene registry de tools, toolsets, memoria, plugins, skills, delegación y ejecución; MiMo Code añade memoria persistente, checkpoints, subagentes, goals y mecanismos de evolución. 

1. Primero: qué NO debes copiar

No intentaría copiar:

OpenClaw completo
Hermes completo
Claude Code completo
MiMo Code completo

Ni tampoco:

agent loop
+
prompt
+
tools

Tu objetivo debe ser:

SOURCE AGENT
     ↓
ARCHITECTURE MINING
     ↓
BEHAVIOR / INVARIANT EXTRACTION
     ↓
ABSTRACTION
     ↓
YOUR DSL
     ↓
YOUR DAG
     ↓
YOUR SCHEMA
     ↓
YOUR SHERIFF
     ↓
YOUR RUNTIME CODE

Es decir:

estudiar la implementación → extraer el principio → reimplementarlo con tus contratos.

Eso además evita acoplar tu kernel a decisiones internas de esos proyectos.


---

2. Qué debes buscar exactamente

Yo dividiría el estudio de cada repositorio en 12 mapas.

Mapa 1 — Execution Loop

Busca:

run()
run_agent()
agent_loop
iteration
turn
step
execute
dispatch
continue
stop

No quieres copiar el loop.

Quieres descubrir:

¿Cuándo empieza una iteración?
¿Qué estado conserva?
¿Qué produce cada iteración?
¿Qué provoca otra iteración?
¿Qué condiciones terminan?
¿Qué errores reintenta?

Hermes, por ejemplo, tiene actualmente una separación explícita del runner en módulos bajo agent/, y su run_agent.py concentra el ciclo de conversación, ejecución de herramientas, recuperación y manejo de historial. 

Eso se transforma en:

IterationState
IterationInput
IterationOutput
TerminationCondition
RecoveryPolicy


---

3. Mapa 2 — Tool Registry

Este es uno de los componentes que sí deberías estudiar profundamente.

Hermes actualmente utiliza un registry donde cada herramienta registra:

schema
handler
metadata

y model_tools.py construye la superficie pública a partir de ese registry. 

Esto es casi exactamente el patrón que necesitas.

Tu versión:

CapabilityRegistry

con:

Capability
├── id
├── version
├── input_schema
├── output_schema
├── executor
├── prerequisites
├── resource_cost
├── permissions
├── lifecycle
└── sheriff

Entonces una capability deja de ser:

prompt:
"puedes utilizar PostgreSQL"

y pasa a ser:

postgres.query
postgres.migrate
postgres.inspect
postgres.validate

con código real.


---

4. Mapa 3 — Tool Schema

Busca en los agentes:

name
description
input_schema
parameters
required
validation
result
error

Tu objetivo es descubrir:

> ¿Cómo describe el agente una operación antes de ejecutarla?



Después conviertes eso en tu DSL:

capability:
  id: file.patch

  input:
    schema: PatchRequest

  output:
    schema: PatchResult

  executor:
    module: kernel.file_patch

  sheriff:
    pre:
      - path_allowed
      - workspace_exists

    post:
      - patch_applied
      - file_valid


---

5. Mapa 4 — Permissions / Safety

Este es especialmente importante de Claude Code y OpenClaw.

La investigación de 2026 sobre Claude Code identifica como piezas centrales el sistema de permisos, compaction, MCP/plugins/skills/hooks, subagentes y almacenamiento de sesiones. 

No copies sus permisos.

Extrae la idea abstracta:

ACTION
 ↓
POLICY
 ↓
ALLOW / DENY / ASK

Y conviértelo en:

SheriffPolicy

Ejemplo:

file.write
 ├── workspace_allowed?
 ├── path_allowed?
 ├── extension_allowed?
 ├── secret_scan?
 └── budget_allowed?

Eso sí es determinista.


---

6. Mapa 5 — Context Management

Busca:

context
compaction
summarization
history
session
checkpoint
memory
snapshot
restore

MiMo Code es particularmente interesante aquí porque su arquitectura está orientada a tareas largas, memoria persistente y evolución. El repositorio oficial describe memoria persistente y trabajo continuado sobre el proyecto. 

No copies su implementación.

Extrae:

ContextLifecycle

con estados:

HOT
 ↓
WARM
 ↓
COMPACT
 ↓
ARCHIVE
 ↓
RESTORE

Y esto puede ser casi completamente determinista.


---

7. Mapa 6 — Memory

Hermes es especialmente útil aquí.

Tiene un MemoryManager como punto de integración y una interfaz MemoryProvider con lifecycle definido:

initialize
prefetch
sync_turn
get_tool_schemas
handle_tool_call
shutdown



Esto es excelente material para convertir en:

MemoryProviderContract

y luego:

MemoryScheduler
MemoryCache
MemoryIndex
MemoryWritePolicy
MemoryReadPolicy

La memoria deja de ser:

> "recuerda esto."



y pasa a ser:

memory.write()
memory.query()
memory.promote()
memory.supersede()
memory.archive()


---

8. Mapa 7 — Skills

Aquí OpenClaw y Hermes son muy interesantes por razones distintas.

OpenClaw trata skills como paquetes de instrucciones y los filtra según entorno, configuración, disponibilidad y permisos. Los plugins también pueden aportar tools, skills, hooks y otros recursos. 

Hermes, por su parte, distingue explícitamente cuándo una capacidad debe ser skill, tool, plugin o MCP. 

Tu sistema debería estudiar esa lógica para crear:

CapabilityClassifier

que determine:

knowledge
        ↓
method
        ↓
skill
        ↓
adapter
        ↓
tool
        ↓
core capability

Esto encaja directamente con tu Evolution Engine.


---

9. Mapa 8 — Plugins

Aquí debes estudiar:

discovery
registration
manifest
lifecycle
hooks
enable
disable
dependencies
configuration

Hermes tiene una arquitectura de plugins con discovery, lifecycle hooks, tools, skills y archivos de datos. 

OpenClaw también considera plugin como una superficie que puede añadir tools, skills, providers, hooks y otros recursos de runtime. 

Tu versión:

UniversalPluginAdapter

debería convertir:

plugin
 ↓
manifest parser
 ↓
capability extraction
 ↓
dependency map
 ↓
lifecycle extraction
 ↓
adapter generation
 ↓
kernel extension


---

10. Mapa 9 — Subagents / Delegation

Busca:

spawn
delegate
subagent
child
background
cancel
timeout
result
parent
context

Hermes tiene delegate_task, incluyendo ejecución en background y retorno posterior del resultado al flujo principal. 

No copies el sistema.

Extrae:

Task
ChildTask
ParentTask
Dependency
Result
Cancellation

Y conviértelo en:

DAG node

Por ejemplo:

ARCHITECTURE
      │
 ┌────┼────┐
 ▼    ▼    ▼
DB   API  SECURITY
 │    │    │
 └────┼────┘
      ▼
 CONSOLIDATE


---

11. Mapa 10 — Goal / Completion

Esto es algo que yo pondría muy alto en tu estudio de MiMo Code.

Busca:

goal
objective
success
completion
verify
done
stop
checkpoint

MiMo Code declara explícitamente mecanismos de goals y evolución del agente; además, análisis comunitarios de su arquitectura destacan un verificador independiente del objetivo y checkpoints de memoria. 

Tu sistema:

GoalContract

debería tener:

goal
inputs
required_state
success_conditions
failure_conditions
verification
terminal_states

Así:

"terminé"

no tiene ningún significado especial.

Solo:

Sheriff.verify_goal() == PASS

significa terminado.


---

12. Mapa 11 — Recovery

Busca:

retry
backoff
fallback
repair
recover
resume
checkpoint
rollback
failure

Esto debe convertirse en:

RecoveryPolicy

Ejemplo:

FAIL
 ↓
classify_failure()
 ↓
┌─────────────┬──────────────┬───────────────┐
│ transient   │ tool_error   │ code_failure  │
▼             ▼              ▼
retry         repair_tool    repair_code

Y cada rama puede ser un DAG.


---

13. Mapa 12 — Observability / Trace

Busca:

event
trace
session
task_id
run_id
tool_call
result
error
metrics

Todo debe convertirse en:

EventBus

con eventos estructurados:

TASK_CREATED
TASK_STARTED
CAPABILITY_SELECTED
MODEL_SELECTED
TOOL_STARTED
TOOL_COMPLETED
VALIDATION_FAILED
REPAIR_STARTED
TASK_COMPLETED

Esto será esencial para que tu sistema pueda aprender de su propia ejecución.


---

14. La pieza más importante: Behavior Mining

No analizaría archivos uno por uno manualmente sin estructura.

Crearía un scanner determinista.

repo
 ↓
AST Scanner
 ↓
Symbol Index
 ↓
Call Graph
 ↓
Import Graph
 ↓
State Graph
 ↓
Event Graph
 ↓
Capability Graph
 ↓
Behavior Report

Para Python:

ast
inspect
importlib

Para TypeScript:

TypeScript compiler API
ts-morph

Y para cualquier repositorio:

tree-sitter

El scanner busca automáticamente:

classes
functions
interfaces
registries
handlers
events
schemas
state machines
queues
executors
validators
retry logic
permission checks
plugins
hooks
storage


---

15. No extraigas "código"; extrae invariantes

Esto es fundamental.

Supongamos que Hermes tiene:

if not tool_available:
    return ...

No copies esa condición.

Pregúntale al analizador:

> ¿Qué propiedad del sistema garantiza esta condición?



Puede descubrir:

Capability must not be exposed when prerequisite unavailable.

Eso se convierte en:

INVARIANT:
capability.available == true

Y luego:

Sheriff:
assert_capability_available()

Eso es mucho más potente.


---

16. El pipeline que yo construiría

SOURCE REPOSITORY
       │
       ▼
┌────────────────────┐
│ SOURCE INGESTOR     │
└─────────┬──────────┘
          ▼
┌────────────────────┐
│ AST / SYMBOL INDEX  │
└─────────┬──────────┘
          ▼
┌────────────────────┐
│ BEHAVIOR MINER      │
└─────────┬──────────┘
          ▼
┌────────────────────┐
│ CAPABILITY MINER    │
└─────────┬──────────┘
          ▼
┌────────────────────┐
│ INVARIANT MINER     │
└─────────┬──────────┘
          ▼
┌────────────────────┐
│ WORKFLOW MINER      │
└─────────┬──────────┘
          ▼
┌────────────────────┐
│ POLICY MINER        │
└─────────┬──────────┘
          ▼
       KERNEL IR
          │
    ┌─────┼─────┐
    ▼     ▼     ▼
   DSL   DAG   SCHEMA
    │     │     │
    └─────┼─────┘
          ▼
    SHERIFF COMPILER
          │
          ▼
   EXECUTABLE MODULE
          │
          ▼
    KERNEL EXTENSION


---

17. El 10% LLM debe estar aquí

No intentaría hacer 100% determinista la interpretación semántica.

El reparto que propones sí es razonable:

90% determinista

repo scanning
AST
symbols
dependency graph
call graph
registries
schemas
state
events
DAG
validation
permissions
resource limits
cache
storage
execution
recovery
versioning
patch application

~10% LLM

¿Qué significa esta función?
¿Qué capability representa?
¿Qué invariant parece estar protegiendo?
¿Qué dos componentes equivalen semánticamente?
¿Qué método se puede abstraer?
¿Cómo traducir una lógica ambigua al IR?

Pero incluso aquí pondría una regla:

> El LLM propone una interpretación; el compilador solo acepta estructuras que encajen en el IR.




---

18. El Kernel IR es la pieza central

Yo diseñaría aproximadamente:

KernelIR
├── capabilities
├── operations
├── workflows
├── goals
├── schemas
├── policies
├── invariants
├── events
├── resources
├── adapters
├── memory
├── recovery
└── provenance

Y cada elemento tiene:

source
version
confidence
evidence
dependencies
generated_by

Así sabes exactamente:

> "Esta capacidad salió de qué parte de Hermes, qué comportamiento detectamos y cómo fue transformada."




---

19. Qué buscar específicamente en cada agente

Fuente	Estudiaría principalmente

OpenClaw	tools, skills, plugins, hooks, capability discovery, permissions, session/gateway
Hermes	tool registry, toolsets, memory, plugins, skills, delegation, Kanban, recovery
Claude Code	permission architecture, context lifecycle, hooks, subagents, MCP, session persistence
MiMo Code	goals, checkpoints, persistent memory, subagents, long-horizon execution, evolution


OpenClaw documenta explícitamente la separación entre tools, skills y plugins; Hermes tiene una superficie de herramientas mucho más estructurada y un sistema de plugins/memoria; MiMo Code es especialmente interesante para tu componente de evolución. 


---

20. Lo que yo NO convertiría en determinista

Hay que poner un límite.

No convertiría:

"¿Cuál es la mejor arquitectura?"

en una regla fija.

Ni:

"¿Cómo reparar este algoritmo?"

Ni:

"¿Qué librería nueva debería usar?"

Eso sigue siendo trabajo de modelos.

Pero sí convertiría:

qué herramientas puede usar
qué archivos puede modificar
qué esquema debe devolver
qué condiciones debe cumplir
qué presupuesto tiene
qué estados existen
qué eventos produce
qué significa PASS
qué significa FAIL
qué puede reintentarse
qué debe escalarse
qué debe bloquearse
cómo se registra
cómo se recupera

en código.


---

21. Resultado final que buscaría

No terminarías con:

OpenClaw + Hermes + Claude Code + MiMo

Terminarías con:

NCT KERNEL
│
├── Capability Engine
├── Workflow Engine
├── Goal Engine
├── Schema Engine
├── Sheriff Engine
├── Policy Engine
├── Resource Governor
├── Memory Engine
├── Event Engine
├── Recovery Engine
├── Plugin Engine
├── Evolution Engine
└── Model Router

Y cada una de esas piezas tendría principios extraídos de varios sistemas, no copias.

Por ejemplo:

Hermes Tool Registry
        +
OpenClaw Plugin Model
        +
MiMo Goal System
        +
Claude Permission Model
        ↓
NCT Capability Kernel

Eso es exactamente el tipo de fusión por abstracción que estás describiendo.

La primera fase que haría

Antes de escribir el compilador, haría un Kernel Archaeology Engine v0.1.

Su única misión sería:

CLONE REPO
↓
PIN COMMIT
↓
SCAN
↓
INDEX
↓
MAP
↓
EXTRACT
↓
CLASSIFY
↓
GENERATE REPORT

Y produciría cuatro documentos por repositorio:

01_ARCHITECTURE_MAP.md
02_CAPABILITY_MAP.md
03_BEHAVIOR_INVARIANT_MAP.md
04_CONVERSION_MAP.md

El cuarto sería el más importante:

SOURCE BEHAVIOR
        ↓
NCT CAPABILITY
        ↓
NCT DSL
        ↓
NCT DAG
        ↓
NCT SCHEMA
        ↓
NCT SHERIFF
        ↓
NCT CODE

No empezaría modificando OpenClaw, Hermes, Claude Code o MiMo. Primero haría que tu sistema pueda leerlos como material de ingeniería, construir el mapa semántico y producir una propuesta de conversión reproducible. Después sí se implementa el compilador.

Además, para Claude Code hay una consideración especial: el estudio académico de 2026 analiza su arquitectura públicamente disponible y señala que gran parte de su valor está precisamente en los sistemas alrededor del loop —permisos, compaction, extensibilidad, subagentes y sesiones—, que es justamente el material que te interesa abstraer, no el loop en sí. 

Sí. Pero haría una distinción importante: no intentaría convertir literalmente los prompts del kernel en DSL. Los usaría como materia prima para extraer reglas, decisiones, contratos e invariantes. El prompt es una representación blanda; el DSL/DAG/Sheriff sería la representación ejecutable.

Arquitectura de conversión

PROMPT / SYSTEM INSTRUCTION
          │
          ▼
   PROMPT EXTRACTOR
          │
          ├── reglas
          ├── restricciones
          ├── objetivos
          ├── condiciones
          ├── herramientas
          ├── formato de salida
          ├── criterios de éxito
          └── comportamiento de recuperación
          │
          ▼
    SEMANTIC NORMALIZER
          │
          ▼
       KERNEL IR
          │
     ┌────┼────┐
     ▼    ▼    ▼
    DSL   DAG  SCHEMA
     │    │    │
     └────┼────┘
          ▼
       SHERIFF
          │
          ▼
   EXECUTABLE CODE

1. Primero extraería el prompt en unidades

Por ejemplo, un prompt podría decir:

> Analiza el problema, revisa los archivos relevantes, modifica únicamente los archivos necesarios, ejecuta pruebas y verifica que no hayas roto funcionalidades existentes.



No lo dejaría como prompt.

Lo convertiría en:

goal:
  id: modify_project
  objective: produce_valid_change

constraints:
  - only_relevant_files
  - preserve_existing_behavior

required_actions:
  - inspect_project
  - identify_targets
  - modify
  - test
  - verify

Eso ya es mucho más útil.


---

2. Después separaría 7 tipos de información

El extractor debería clasificar cada fragmento del prompt como:

GOAL
CONSTRAINT
PRECONDITION
ACTION
DECISION
OUTPUT
INVARIANT

Ejemplo:

"Antes de modificar código, revisa las dependencias."

→ PRECONDITION

"Modifica solamente los archivos necesarios."

→ CONSTRAINT

"Ejecuta las pruebas."

→ ACTION

"No continúes si las pruebas críticas fallan."

→ DECISION + INVARIANT

"Entrega un resumen de los cambios."

→ OUTPUT

Esta clasificación debería ser principalmente determinista mediante reglas + parser, y usar LLM solo cuando haya ambigüedad semántica.


---

3. Crear un Prompt-to-Kernel IR

Esta sería una pieza central de tu sistema.

Por ejemplo:

instruction:
  id: code_change

goal:
  type: modification
  success: project_valid

preconditions:
  - workspace_exists
  - repository_indexed

actions:
  - inspect
  - plan
  - patch
  - test
  - verify

constraints:
  files:
    mode: minimal_change

invariants:
  - no_unrelated_files_modified
  - existing_tests_preserved

outputs:
  - patch
  - test_report
  - verification_report

El prompt original podría desaparecer después de esta compilación.


---

4. El DSL representa el comportamiento

El DSL debe responder:

> ¿Qué puede hacer el kernel y bajo qué condiciones?



Ejemplo:

capability: safe_code_change

requires:
  - repository
  - workspace

steps:

  - id: inspect
    action: repository.inspect

  - id: analyze
    action: code.analyze
    depends_on: [inspect]

  - id: patch
    action: code.patch
    depends_on: [analyze]

  - id: test
    action: test.run
    depends_on: [patch]

  - id: verify
    action: code.verify
    depends_on: [test]

Aquí ya no necesitas decirle al agente:

> "primero inspecciona..."



El DAG lo impone.


---

5. El DAG elimina la parte repetitiva del razonamiento

El LLM no debería decidir cada vez:

¿Ahora inspecciono?
¿Ahora pruebo?
¿Ahora verifico?

Eso lo sabe el DAG.

INSPECT
   ↓
ANALYZE
   ↓
PATCH
   ↓
TEST
   ↓
VERIFY

El LLM solamente interviene cuando existe una decisión realmente semántica:

ANALYZE
   ↓
¿qué cambio debe hacerse?

Después vuelve al DAG.

Eso reduce muchísimo el uso del modelo.


---

6. El Schema define el contrato

Cada nodo debería tener un schema estricto.

input:
  repository: RepositoryRef
  target: FileSet
  objective: Goal

output:
  patch: Patch
  changed_files: FileSet
  diagnostics: Diagnostics

Así el siguiente nodo no recibe:

> "Aquí tienes lo que encontré..."



Recibe una estructura conocida.

AnalyzeResult
       ↓
PatchRequest
       ↓
PatchResult
       ↓
TestResult

Esto es mucho más determinista.


---

7. Sheriff = la parte que realmente reemplaza al prompt

Aquí está la mayor oportunidad.

Un prompt dice:

> "No hagas cambios peligrosos."



El Sheriff debería decir:

BEFORE PATCH:

✓ workspace permitido
✓ archivo permitido
✓ extensión permitida
✓ tamaño permitido
✓ no secret detected
✓ budget disponible
✓ capability autorizada

→ ALLOW

Y después:

AFTER PATCH:

✓ syntax valid
✓ schema valid
✓ tests valid
✓ diff within policy
✓ no forbidden files changed

→ PROMOTE

El LLM puede sugerir el cambio.

El Sheriff decide si puede ejecutarse.


---

8. Convertiría los "system prompts" en políticas

Ejemplo:

Prompt:

"Never expose credentials."

No conservaría eso como prompt.

Lo transformaría:

policy:
  id: secret_protection

rules:
  - deny_secret_output
  - deny_secret_prompt_injection
  - deny_secret_logging
  - deny_secret_artifact

Y código:

SecretScanner
CredentialBroker
OutputFilter
AuditLogger

Ahora la regla existe aunque cambies de modelo.


---

9. Los prompts de especialización también se compilan

Esto encaja directamente con tu idea anterior de crear especialidades reales.

Ejemplo:

"Actúa como ingeniero Python senior..."

No quiero guardar eso.

El sistema debería extraer:

Python
typing
pytest
ruff
mypy
packaging
asyncio
FastAPI
security

Luego investigar qué herramientas/librerías necesita realmente.

Después:

PythonEngineer
│
├── capabilities
├── libraries
├── validators
├── workflows
├── schemas
├── goals
├── test policies
└── sheriff policies

El resultado sería un runtime especializado, no un personaje definido por un prompt.


---

10. Incluso los "formatos de respuesta" se pueden compilar

Prompt:

> "Responde siempre con análisis, cambios, pruebas y riesgos."



Se convierte:

output_schema:
  type: EngineeringReport

  required:
    - analysis
    - changes
    - tests
    - risks

El modelo puede generar el contenido.

Pero el Schema determina:

¿faltó tests?
→ INVALID

¿faltó risks?
→ INVALID


---

11. Haría un compilador de prompts

Lo llamaría, por ejemplo:

PROMPT2KERNEL

Pipeline:

Prompt
 ↓
Parser
 ↓
Instruction Extractor
 ↓
Semantic Classifier
 ↓
Conflict Detector
 ↓
Invariant Extractor
 ↓
Capability Mapper
 ↓
Kernel IR
 ↓
DSL Compiler
 ↓
DAG Compiler
 ↓
Schema Compiler
 ↓
Sheriff Compiler
 ↓
Code Generator

El LLM solo aparece aquí:

Semantic Classifier
        +
Invariant Extraction
        +
Ambiguous Mapping

Todo lo demás puede ser determinista.


---

12. Añadiría una etapa que considero crítica: Prompt Conflict Resolver

Cuando estudies OpenClaw, Hermes, Claude Code, MiMo, etc., vas a encontrar instrucciones contradictorias.

Ejemplo:

Prompt A:
"Always ask before changing files."

Prompt B:
"Automatically repair compilation errors."

No puedes simplemente fusionarlos.

El sistema debe convertirlos en políticas:

normal_change → policy.ask
automatic_repair → policy.auto_repair
critical_change → policy.ask

Y establecer prioridad:

SAFETY
  >
SYSTEM POLICY
  >
PROJECT POLICY
  >
TASK POLICY
  >
MODEL SUGGESTION

Eso debe ser determinista.


---

13. Y añadiría aprendizaje de ejemplos

Aquí tu idea es especialmente potente.

Puedes darle al extractor:

PROMPT
+
10 ejecuciones exitosas
+
3 ejecuciones fallidas
+
diffs
+
tests
+
resultados

Y producir:

Behavior Pattern

Por ejemplo:

Observed:

inspect → patch → test → repair → test

success rate: 91%

failure pattern:
patch without dependency inspection

new invariant:
dependency_inspection_required

Entonces el sistema puede proponer:

invariant:
  id: dependency_inspection_required

El Director decide si incorporarlo.

Eso es aprendizaje operacional, no fine-tuning.


---

14. La arquitectura final

Yo la dejaría así:

EXTERNAL AGENTS
        OpenClaw / Hermes / Claude / MiMo
                         │
                         ▼
                SOURCE ANALYZER
                         │
                         ▼
                 PROMPT MINER
                         │
             ┌───────────┴──────────┐
             ▼                      ▼
       CODE BEHAVIOR          PROMPT BEHAVIOR
             │                      │
             └───────────┬──────────┘
                         ▼
                    KERNEL IR
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
         DSL             DAG          SCHEMA
          │              │              │
          └──────────────┼──────────────┘
                         ▼
                      SHERIFF
                         │
                         ▼
                  CODE GENERATOR
                         │
                         ▼
                KERNEL EXTENSION
                         │
                         ▼
              CAPABILITY REGISTRY

Y después:

NEW EXECUTION
     ↓
observe
     ↓
compare expected/actual
     ↓
detect improvement
     ↓
generate candidate
     ↓
Director approval
     ↓
compile
     ↓
register

La regla fundamental

El prompt no desaparece porque lo "reescribamos mejor". Desaparece porque lo compilamos.

El LLM puede seguir existiendo para producir contenido, resolver problemas ambiguos y proponer soluciones. Pero:

intención → contrato → DAG → schema → Sheriff → código

es la ruta que convierte una instrucción blanda en una capacidad persistente, editable, versionada y ejecutable del kernel.

Y eso encaja mucho mejor con tu objetivo de que el sistema pueda estudiar OpenClaw/Hermes/Claude Code/MiMo y absorber patrones sin convertirse en una copia de ninguno de ellos.



Sí. Si tu criterio es “qué arquitectura consigue que un LLM mantenga la cordura operativa” —no qué modelo tiene más conocimiento—, mi respuesta cambia bastante.

Mi elección: Claude Code como referencia arquitectónica

No porque el modelo Claude sea necesariamente el mejor, sino porque Claude Code tiene una de las arquitecturas más estudiables para convertir un LLM probabilístico en un sistema relativamente disciplinado.

Un análisis técnico de 2026 de su código identifica que el while del agente es relativamente sencillo; gran parte de la ingeniería importante está alrededor: permisos, gestión/compaction de contexto, MCP/plugins/skills/hooks, subagentes aislados y almacenamiento persistente de sesiones. 

Eso coincide exactamente con lo que tú estás intentando construir.

Mi ranking para tu objetivo

Sistema	Coherencia operativa	Planificación	Control	Qué extraería

Claude Code	★★★★★	★★★★★	★★★★★	arquitectura de control
MiMo Code	★★★★★	★★★★★	★★★★☆	goals, memoria, checkpoints
OpenHands	★★★★☆	★★★★☆	★★★★☆	ejecución/verificación
Hermes	★★★★☆	★★★★☆	★★★★☆	registry, tools, memoria, plugins
OpenClaw	★★★★☆	★★★★☆	★★★★☆	extensibilidad/capabilities
SolAgent	★★★★☆	★★★★☆	★★★★★	loops de verificación especializados


Esto no significa que uno sea "más inteligente" globalmente. Estoy clasificando la arquitectura alrededor del LLM.


---

Pero hay algo todavía más interesante

Para tu proyecto no escogería uno.

Construiría un meta-agente de control tomando lo mejor de varios:

NCT KERNEL
                      │
        ┌─────────────┼─────────────┐
        │             │             │
   Claude Code      MiMo         Hermes
   CONTROL          GOALS        TOOLS
        │             │             │
        └─────────────┼─────────────┘
                      │
                 OpenClaw
                 EXTENSIONS
                      │
                 OpenHands
                 EXECUTION
                      │
                  SHERIFF
                      │
               DETERMINISTIC
                  RUNTIME

Y ahí es donde tu idea de 90% código / 10% LLM empieza a tener mucho sentido.


---

Lo que realmente quieres construir

No quieres:

LLM
 ↓
prompt enorme
 ↓
respuesta

Quieres:

LLM
 ↓
INTENT
 ↓
KERNEL
 ↓
PLAN
 ↓
DAG
 ↓
EXECUTION
 ↓
OBSERVATION
 ↓
VERIFICATION
 ↓
RECOVERY
 ↓
GOAL

El modelo no controla directamente el sistema.

El kernel controla al modelo.


---

La característica que más copiaría conceptualmente de Claude Code

No sería su prompt.

Sería esta filosofía:

> El modelo propone; el runtime controla.



El análisis de Claude Code identifica precisamente que el sistema tiene mecanismos externos al loop para permisos, contexto, extensibilidad y aislamiento. 

Eso es mucho más importante para evitar que el modelo:

se desvíe
olvide el objetivo
invente herramientas
repita errores
modifique cosas innecesarias
pierda contexto


---

Y añadiría MiMo

Aquí MiMo Code me parece especialmente relevante para tu proyecto.

Porque tu objetivo no es solamente:

> "haz esta tarea".



Es:

> "mantén una misión durante mucho tiempo y continúa evolucionando sin perder el objetivo".



Ahí necesitas:

GOAL
 ↓
SUBGOALS
 ↓
CHECKPOINT
 ↓
MEMORY
 ↓
STATE
 ↓
RESUME

No simplemente conversación.


---

Y Hermes para convertir capacidades en infraestructura

Hermes tiene una arquitectura interesante alrededor de:

Tool Registry
Toolsets
Memory
Plugins
Skills
Delegation
Workers

Eso es exactamente material que puedes convertir en tu:

Capability Registry

en lugar de dejar que cada LLM tenga que "recordar" qué puede hacer.


---

OpenHands aporta otra cosa

OpenHands está evolucionando hacia una arquitectura donde varios agentes pueden ejecutarse en paralelo, cada uno aislado en su propio worktree, y donde el sistema puede conectarse a diferentes agentes/modelos. 

Eso te interesa para tu arquitectura de grupos.

Pero nuevamente:

no copiaría OpenHands completo.

Extraería:

parallel execution
workspace isolation
verification
agent interchangeability


---

Hay un quinto patrón muy interesante: SolAgent

Aunque es específico para Solidity, su arquitectura demuestra algo que encaja perfectamente con tu idea:

LLM
 ↓
GENERATE
 ↓
COMPILER
 ↓
STATIC ANALYZER
 ↓
REPAIR
 ↓
VERIFY

Su sistema utiliza un dual-loop: un loop interno de corrección funcional mediante compilación y uno externo de análisis de seguridad. En sus experimentos reporta una mejora considerable frente a LLMs y otros agentes en su dominio. 

La idea es más importante que Solidity.

Tu kernel podría tener:

PLAN
 ↓
EXECUTE
 ↓
VERIFY
 ↓
FAIL?
 ├── NO → CONTINUE
 └── YES
       ↓
    CLASSIFY
       ↓
    REPAIR
       ↓
    VERIFY

Eso es exactamente lo que ayuda a mantener al modelo en el problema en lugar de dejarlo improvisar.


---

La combinación que yo haría

Para tu NCT Kernel:

CLAUDE CODE
    ↓
CONTROL / PERMISSIONS / CONTEXT
         +
MiMo
    ↓
GOALS / CHECKPOINTS / LONG-HORIZON
         +
HERMES
    ↓
TOOLS / MEMORY / PLUGINS / DELEGATION
         +
OPENCLAW
    ↓
CAPABILITY / EXTENSIONS
         +
OPENHANDS
    ↓
PARALLEL EXECUTION / ISOLATION
         +
SOLAGENT
    ↓
VERIFY → REPAIR → VERIFY
         +
TU WORDLFLOW
    ↓
DAG + SCHEMA + SHERIFF

Y finalmente:

LLM
              │
              ▼
        ┌────────────┐
        │ NCT KERNEL │
        └──────┬─────┘
               │
      ┌────────┴────────┐
      ▼                 ▼
   DETERMINISTIC      LLM
      90%              10%
      │                 │
      ├─ DAG            ├─ reasoning
      ├─ schema         ├─ ambiguity
      ├─ state          ├─ design
      ├─ policy         └─ synthesis
      ├─ memory
      ├─ scheduler
      ├─ verifier
      ├─ recovery
      └─ sheriff

Esto es superior a simplemente ponerle un mejor system prompt

Porque el prompt puede decir:

> "No pierdas el objetivo."



Pero tu kernel puede detectar objetivamente que lo perdió.

Puede comparar:

CURRENT_STATE
      vs
GOAL_STATE

Puede detectar:

goal drift
context drift
repeated action
tool loop
budget exhaustion
contradictory plan
failed verification
irrelevant modification

Y automáticamente:

PAUSE
 ↓
REPLAN
 ↓
RESTORE CHECKPOINT
 ↓
CONTINUE

Ese es, en mi opinión, el salto que estás buscando.

No intentaría crear un "LLM más inteligente". Intentaría crear un runtime que haga que incluso un LLM mediocre tenga que comportarse como un agente disciplinado.

Y después puedes conectar Opus/Fable 5, DeepSeek, Seed-Coder, Nemotron, Gemma, etc. El modelo cambia; la disciplina del sistema permanece. Esto también encaja con la evidencia reciente: incluso los modelos más capaces pueden comportarse de forma no prevista bajo ciertos entornos, por lo que la contención y los controles externos siguen siendo necesarios. 

Sí. Si tienes el código fuente/binario distribuido en GitHub de los agentes que quieres estudiar, lo haría de forma mucho más determinista y barata que pedirle a un LLM que "analice todo".

La regla central sería:

> El código que ya es código no se reescribe innecesariamente. Los prompts, reglas, políticas y métodos de trabajo se extraen, se estructuran y se compilan a DSL + DAG + Schema + Sheriff.



Y el LLM solo entra cuando el extractor no puede determinar semánticamente qué significa algo.


---

1. Pipeline que usaría

GitHub
  │
  ▼
Source Downloader
  │
  ├── commit SHA
  ├── manifest
  └── hash
  │
  ▼
Static Analyzer
  │
  ├── código
  ├── prompts
  ├── schemas
  ├── tools
  ├── plugins
  ├── skills
  ├── workflows
  ├── policies
  └── state machines
  │
  ▼
CLASSIFIER
  │
  ├───────────────┐
  │               │
  ▼               ▼
CODE            BEHAVIOR
  │               │
  │          ┌────┴─────┐
  │          │          │
  ▼          ▼          ▼
KEEP       PROMPT     POLICY
AS-IS        │          │
             ▼          ▼
           DSL/DAG    SHERIFF

Esto evita enviar el repositorio completo a un LLM.


---

2. Primero: descargar y congelar el source

El sistema debe obtener:

repository
commit SHA
tag
submodules
dependencies
hashes

Por ejemplo:

sources/
  hermes/
    commit.json
    source/
    manifest.json

commit.json:

{
  "repository": "...",
  "commit": "abc123...",
  "sha256": "...",
  "timestamp": "..."
}

Así siempre puedes reproducir la extracción.


---

3. Después haces una extracción 100% determinista

No mandas los archivos al LLM.

El extractor utiliza AST/parser.

Para Python:

AST
Tree-sitter
symbol table
imports
call graph
decorators
classes
functions
constants
strings

Para TypeScript/JavaScript:

TypeScript compiler
Tree-sitter
AST
imports
exports
call graph

Y para otros lenguajes agregas parsers.

El resultado:

extraction/
   symbols.json
   calls.json
   imports.json
   strings.json
   schemas.json
   registries.json
   prompts.json
   policies.json


---

4. Clasificador determinista

Cada elemento recibe una categoría.

CODE
PROMPT
POLICY
SCHEMA
WORKFLOW
TOOL
PLUGIN
SKILL
CONFIG
DOCUMENTATION
TEST

Por ejemplo:

def classify(node):
    if node.is_function:
        return CODE

    if node.is_json_schema:
        return SCHEMA

    if node.is_prompt_template:
        return PROMPT

    if node.registers_tool:
        return TOOL

Pero no usaría solamente reglas simples.

Crearía un Evidence Classifier.

Ejemplo:

string
 ↓
¿contiene instrucciones?
 ↓
¿se entrega al modelo?
 ↓
¿modifica comportamiento?
 ↓
¿tiene variables?

Entonces:

PROMPT_CONFIDENCE = 0.96


---

5. El código se conserva

Esto es fundamental.

Si encuentras:

def execute_tool(tool, args):
    ...

no necesitas convertirlo en DSL.

El sistema registra:

capability:
    tool.execute
implementation:
    source:function

Y lo conserva.

NCT Kernel
   │
   └── extensions/
          └── tool_execute/
                 └── runtime.py

No desperdicias tokens reconstruyendo código que ya funciona.


---

6. Pero el prompt sí cambia

Supongamos que encuentras:

Before modifying files:
1. inspect the relevant code
2. make the smallest necessary change
3. run tests
4. repair failures
5. verify the result

No lo conservaría como prompt.

El extractor lo transforma:

BEHAVIOR GRAPH

inspect
   ↓
modify
   ↓
test
   ↓
┌───────────────┐
│ test failed?  │
└───────┬───────┘
    yes │ no
        │
        ▼
      repair
        │
        ▼
       test

no → verify


---

7. Después lo compilas

DSL

workflow:
  id: safe_code_change

  policy:
    minimal_change: true
    verification_required: true

DAG

nodes:
  - inspect
  - modify
  - test
  - repair
  - verify

edges:
  - inspect -> modify
  - modify -> test
  - test.failed -> repair
  - repair -> test
  - test.passed -> verify

Schema

input:
  repository: string
  task: string

output:
  changed_files: list
  verification: VerificationResult

Sheriff

rules:
  max_repair_attempts: 3

  deny:
    - bypass_tests
    - unrelated_file_modification

  require:
    - verification

Ahora el comportamiento que antes necesitaba un bloque de prompt se ejecuta mediante código.


---

8. Esto reduce muchísimo el uso de LLM

En lugar de:

Repositorio 200.000 líneas
        ↓
LLM
        ↓
muchísimos tokens

harías:

200.000 líneas
      ↓
AST
      ↓
100% determinista
      ↓
2.000 símbolos relevantes
      ↓
200 comportamientos
      ↓
50 prompts/policies
      ↓
LLM solamente para ambigüedades

Por ejemplo:

100.000 LOC
       ↓
Parser
       ↓
0 tokens
       ↓
extracción
       ↓
LLM recibe únicamente:
20 fragmentos ambiguos

Eso es exactamente lo que quieres.


---

9. Todavía mejor: separar extracción de interpretación

Yo construiría dos motores.

Motor A — Extractor

NO LLM

Hace:

clone
parse
AST
symbols
calls
strings
schemas
registries
prompts
dependencies

Motor B — Semantic Resolver

LLM opcional

Solo recibe:

{
  "symbol": "...",
  "context": "...",
  "evidence": "...",
  "candidate_behavior": "..."
}

Y responde con JSON estricto:

{
  "type": "workflow",
  "goal": "...",
  "preconditions": [],
  "actions": [],
  "transitions": [],
  "invariants": []
}

Nunca recibe todo el repositorio.


---

10. Después unificador

Si analizas:

Claude Code
Hermes
OpenClaw
MiMo
OpenHands

puedes descubrir cinco implementaciones de:

retry

El Capability Merger detecta:

semantic_equivalence

y crea:

NCT retry.v1

Pero conserva:

adapters/
   hermes/
   openclaw/
   mimo/

Así no duplicas capacidades.


---

11. La parte más importante: no convertir todo a determinista

Hay que distinguir:

Determinizable

retry
timeout
budget
state transition
schema validation
tool permissions
file restrictions
task ordering
cache
queue
checkpoint
verification
rollback

→ código/DAG/Schema/Sheriff

No determinizable completamente

diseñar una arquitectura nueva
resolver ambigüedad
decidir entre soluciones desconocidas
generar código nuevo
interpretar requisitos ambiguos

→ LLM

Por eso tu objetivo de:

90% deterministic
10% LLM

es razonable como objetivo arquitectónico, pero no como una proporción rígida para todas las tareas.


---

12. Cómo convertiría los prompts en "código mental"

Un prompt puede contener:

GOAL
CONSTRAINT
PROCEDURE
DECISION
EXCEPTION
RECOVERY
OUTPUT FORMAT

El extractor los separa:

Prompt
 │
 ├── Goal
 ├── Preconditions
 ├── Actions
 ├── Decision rules
 ├── Constraints
 ├── Recovery
 └── Output schema

Luego:

Goal
 ↓
DAG

Constraints
 ↓
Sheriff

Input/output
 ↓
Schema

Procedure
 ↓
DSL

Decision
 ↓
Policy engine

Recovery
 ↓
State machine

Eso es muchísimo más potente que guardar el prompt.


---

13. Y puedes conservar el prompt como evidencia

No lo eliminaría.

Tendrías:

source/
   original_prompt.txt

compiled/
   workflow.dsl
   workflow.dag
   workflow.schema
   workflow.sheriff

provenance/
   mapping.json

El mapping.json podría decir:

prompt lines 12-16
        ↓
DAG nodes 3-5

prompt lines 18-20
        ↓
Sheriff rules 4-6

Entonces puedes auditar:

"¿De dónde salió esta regla?"


---

14. El compilador sería el corazón

Tu sistema tendría:

SOURCE
                       │
                       ▼
                EXTRACTION IR
                       │
                       ▼
                BEHAVIOR IR
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
         DSL          DAG        SCHEMA
          │            │            │
          └────────────┼────────────┘
                       ▼
                    SHERIFF
                       │
                       ▼
                 CODE GENERATOR
                       │
                       ▼
              NCT KERNEL EXTENSION

Y la extensión final podría contener:

extension/
├── manifest.yaml
├── capability.yaml
├── workflow.dsl
├── graph.dag
├── input.schema.json
├── output.schema.json
├── sheriff.yaml
├── runtime.py
├── adapter.py
└── provenance.json


---

15. La evolución se vuelve incremental

No vuelves a analizar todo el repositorio cada vez.

Guardas:

commit SHA

Cuando aparece una actualización:

old SHA
     ↓
new SHA
     ↓
git diff
     ↓
extract ONLY changed symbols

Eso reduce todavía más tiempo y tokens.


---

16. Y aquí aparece una ventaja enorme

Puedes hacer que el sistema estudie 10 agentes diferentes y termine con un solo kernel.

Claude Code ──┐
Hermes ───────┤
OpenClaw ─────┤
MiMo ─────────┤
OpenHands ────┤
              ▼
       Capability Merger
              ▼
          NCT Kernel

No estás copiando los agentes.

Estás haciendo:

> code archaeology → behavior extraction → normalization → compilation → native extension.



Y el resultado no depende de que el LLM recuerde el comportamiento mediante un prompt.


---

La arquitectura que finalmente programaría

01 SOURCE INGESTOR
       ↓
02 AST / STATIC ANALYZER
       ↓
03 PROMPT + POLICY EXTRACTOR
       ↓
04 BEHAVIOR GRAPH BUILDER
       ↓
05 CAPABILITY NORMALIZER
       ↓
06 SEMANTIC RESOLVER
       │
       └── LLM SOLO SI HAY AMBIGÜEDAD
       ↓
07 CAPABILITY MERGER
       ↓
08 NCT KERNEL IR
       ↓
09 DSL COMPILER
10 DAG COMPILER
11 SCHEMA COMPILER
12 SHERIFF COMPILER
       ↓
13 CODE GENERATOR
       ↓
14 EXTENSION REGISTRY
       ↓
15 NATIVE KERNEL EXTENSION

El punto clave: el LLM deja de ser el lugar donde "vive" el método de trabajo. El método queda compilado en artefactos ejecutables y verificables. El LLM queda como componente especializado para las partes que realmente requieren interpretación o generación.


Sí. La forma correcta es que Grok sea solo el primer "maestro de extracción". Después de analizar suficientes repositorios, debes convertir el procedimiento de extracción en una capacidad nativa del kernel. El agente ya no dependería de Grok para aprender a estudiar otros agentes.

La clave es separar el conocimiento de cómo analizar de la capacidad de ejecutar el análisis.

1. Lo que debes construir

Crearía una extensión nativa:

kernel/
└── extensions/
    └── evolution/
        ├── source_ingestor/
        ├── code_archaeology/
        ├── prompt_miner/
        ├── behavior_miner/
        ├── capability_miner/
        ├── semantic_resolver/
        ├── capability_merger/
        ├── ir_compiler/
        ├── extension_compiler/
        └── registry/

El kernel aprende:

> "Así se estudia e incorpora software."



No aprende solamente:

> "Hermes funciona de esta manera."



Eso es una diferencia importante.


---

2. Grok se usa solamente para construir la primera versión

Inicialmente:

Grok
 ↓
estudia Claude Code
Hermes
OpenClaw
MiMo
OpenHands
 ↓
descubre patrones
 ↓
nosotros los convertimos
 ↓
Evolution Engine v1

Después:

Nuevo repositorio
       ↓
NCT Evolution Engine
       ↓
lo analiza solo

Grok deja de ser necesario para el proceso normal.

Puede seguir siendo un consultor externo opcional cuando aparezca algo que el sistema no pueda interpretar.


---

3. El truco: enseñar el procedimiento, no los resultados

No guardaría:

Hermes tiene X
OpenClaw tiene Y
Claude Code tiene Z

como conocimiento principal.

Guardaría:

RECIPE:
HOW_TO_ANALYZE_AGENT

Por ejemplo:

SOURCE
 ↓
IDENTIFY_RUNTIME
 ↓
IDENTIFY_STATE
 ↓
IDENTIFY_TOOLS
 ↓
IDENTIFY_PLANNING
 ↓
IDENTIFY_MEMORY
 ↓
IDENTIFY_PROMPTS
 ↓
IDENTIFY_POLICIES
 ↓
BUILD_CALL_GRAPH
 ↓
BUILD_BEHAVIOR_GRAPH
 ↓
EXTRACT_INVARIANTS
 ↓
NORMALIZE_CAPABILITIES
 ↓
COMPILE_EXTENSION

Eso se convierte en una capability ejecutable.


---

4. Esa receta NO debería ser un prompt

Este es el punto central de tu arquitectura.

No:

system_prompt:
"Cuando estudies un agente..."

Sino:

EvolutionWorkflow

en tu DSL:

workflow: analyze_agent

steps:
  - ingest_source
  - fingerprint
  - parse
  - build_symbols
  - build_call_graph
  - detect_runtime
  - detect_tools
  - detect_memory
  - detect_prompts
  - detect_policies
  - build_behavior_graph
  - extract_invariants
  - normalize_capabilities
  - compile_extension

El kernel sabe hacerlo porque tiene el workflow, no porque un LLM recuerde un prompt.


---

5. Los extractores son plugins del kernel

Por ejemplo:

extensions/evolution/extractors/

python_ast
typescript_ast
prompt_extractor
schema_extractor
tool_extractor
plugin_extractor
workflow_extractor
policy_extractor
state_machine_extractor
dependency_extractor

Cada uno tiene una interfaz común:

extract(source) → Evidence[]

Entonces cuando encuentra Python:

Python repository
      ↓
Python AST extractor

JavaScript:

JavaScript repository
      ↓
TypeScript/JS extractor

Markdown:

Skill
      ↓
Skill extractor

JSON Schema:

Schema
      ↓
Schema extractor


---

6. Después el sistema aprende a combinar extractores

Por ejemplo descubre:

function execute_task()
+
prompt template
+
schema
+
retry handler

Entonces puede inferir:

Capability:
task_execution

Y crear:

Behavior Graph

START
 ↓
VALIDATE
 ↓
EXECUTE
 ↓
OBSERVE
 ↓
SUCCESS ─────→ END
 ↓
FAILURE
 ↓
RECOVER
 ↓
RETRY


---

7. El LLM solo entra en el punto difícil

Supongamos que el extractor encuentra:

if should_continue(context):

El parser sabe que existe una decisión.

Pero no necesariamente sabe qué significa.

Entonces:

Static Analyzer
      ↓
UNKNOWN SEMANTIC NODE
      ↓
Semantic Resolver
      ↓
LLM

El LLM recibe únicamente:

function
call graph
variables
nearby comments
related tests

No el repositorio completo.

Y devuelve:

{
  "decision": "continue_task",
  "condition": "...",
  "confidence": 0.91
}

El kernel valida eso.


---

8. Y puedes hacer que el sistema aprenda de esa resolución

Aquí aparece tu verdadera auto-evolución.

La primera vez:

UNKNOWN
 ↓
LLM
 ↓
interpretation

Se registra:

semantic_pattern:
  signature: should_continue(...)
  meaning: continuation_gate

Después aparece algo parecido:

should_continue(...)

El sistema ya sabe:

continuation_gate

Y no necesita LLM.

Esto convierte progresivamente:

LLM dependency

en:

deterministic knowledge


---

9. Crearía un Pattern Registry

kernel/
└── knowledge/
    └── evolution/
        ├── patterns/
        ├── invariants/
        ├── mappings/
        ├── transformations/
        ├── compiler_rules/
        └── examples/

Ejemplo:

pattern:
  id: retry_with_budget

detect:
  - retry_loop
  - attempt_counter
  - max_attempts

compile:
  capability: recovery.retry
  sheriff:
    max_attempts: extracted_value

Ahora el kernel reconoce automáticamente ese patrón.


---

10. Los ejemplos también se convierten en conocimiento

Esto conecta directamente con lo que dijiste anteriormente.

El sistema puede aprender de ejemplos:

SOURCE EXAMPLE
      ↓
EXTRACT
      ↓
GENERALIZE
      ↓
PATTERN
      ↓
TEST CASE
      ↓
KNOWLEDGE

Por ejemplo analiza cinco agentes:

Hermes → retry
OpenClaw → retry
MiMo → retry
OpenHands → retry
Agent X → retry

Encuentra:

common invariant:
"retry must be bounded"

Eso se convierte en:

Sheriff invariant

Ahora no es conocimiento de un agente concreto.

Es conocimiento arquitectónico del kernel.


---

11. Aquí puedes alcanzar algo mucho más potente

El sistema puede tener dos niveles:

Level 1 — Known

patrón conocido
→ determinista

Level 2 — Unknown

patrón desconocido
→ LLM
→ análisis
→ nueva regla
→ registrar

Por tanto:

UNKNOWN
   ↓
RESEARCH
   ↓
LLM
   ↓
GENERALIZE
   ↓
PATTERN
   ↓
COMPILER RULE
   ↓
DETERMINISTIC

Ese es el ciclo de aprendizaje que buscas.


---

12. Y no necesitas modificar el kernel constantemente

Yo evitaría que el sistema se reescriba directamente.

Usaría:

Kernel
   │
   └── Evolution Extension
          │
          ├── Knowledge Registry
          ├── Pattern Registry
          ├── Compiler
          └── Extension Registry

Cuando aprende algo nuevo:

new capability
      ↓
extension/
      ↓
registry

El kernel solamente carga la extensión.

Esto hace que la evolución sea mucho más segura y reversible.


---

13. El sistema finalmente aprende a estudiar cualquier cosa

Cuando recibe:

"Analiza este agente"

no necesita que Grok le diga cómo.

Ejecuta:

DISCOVER
 ↓
CLASSIFY
 ↓
EXTRACT
 ↓
UNDERSTAND
 ↓
GENERALIZE
 ↓
COMPARE
 ↓
NORMALIZE
 ↓
COMPILE
 ↓
REGISTER

Si es un agente:

Agent → Agent Capability

Si es software:

Software → Software Capability

Si es skill:

Skill → Executable Workflow

Si es plugin:

Plugin → Kernel Extension

Si es dataset:

Dataset → Knowledge Pack

Si es adapter:

Adapter → Native Adapter Capability


---

14. Y aquí está la parte que yo añadiría

Crearía un Evolution Compiler con tres memorias:

┌──────────────────────────┐
│ PROCEDURAL KNOWLEDGE     │
│ cómo analizar/incorporar │
└────────────┬─────────────┘
             │
┌────────────▼─────────────┐
│ PATTERN KNOWLEDGE        │
│ qué patrones reconoce   │
└────────────┬─────────────┘
             │
┌────────────▼─────────────┐
│ CAPABILITY KNOWLEDGE     │
│ qué capacidades posee   │
└──────────────────────────┘

Procedural

> Cómo analizar un repositorio.



Pattern

> Cómo reconocer retry, planner, tool registry, memory, etc.



Capability

> Qué puede hacer el kernel actualmente.



Esto evita mezclar conocimiento sobre agentes con conocimiento de cómo evolucionar.


---

15. Resultado final

Inicialmente:

Grok
 ↓
descubre método
 ↓
nosotros compilamos Evolution Engine

Después:

NCT KERNEL
                  │
         EVOLUTION ENGINE
                  │
       ┌──────────┼──────────┐
       ▼          ▼          ▼
   Extractor   Pattern    Compiler
       │        Registry      │
       └─────────┬────────────┘
                 ▼
          Native Extension

Y cuando aparece un nuevo agente:

GitHub
 ↓
NCT
 ↓
AST
 ↓
Code extraction
 ↓
Prompt extraction
 ↓
Behavior extraction
 ↓
Pattern matching
 ↓
Unknown?
 ├── NO → deterministic
 └── YES → LLM
              ↓
          generalize
              ↓
          save pattern
              ↓
       future = deterministic

Ese último paso es el que convierte la extracción en aprendizaje real del sistema.

Grok sería el andamio inicial. El producto final sería un Evolution Compiler autocontenido dentro de la extensión del kernel, capaz de estudiar nuevos agentes, software, plugins, skills, adapters y datasets usando principalmente código determinista y recurrir al LLM solamente cuando aparece una semántica que todavía no conoce.






