Wordflow 

Sí. Hice una auditoría de lo que hemos construido en esta conversación y separé decisiones ya fijadas, componentes técnicos que añadimos después y elementos que no deben volver a aparecer.

El documento maestro se llamará:

WORKFLOW

Especificación maestra de la Control Layer, Long-Running Loops, Hermes y ejecución determinista

Este será el índice definitivo que usaré como guía para desarrollar las siguientes partes. No voy a introducir después un segundo sistema que duplique al Workflow.


---

PARTE I — FUNDAMENTOS DEL WORKFLOW

1. Propósito del sistema

1.1 Objetivo general

1.2 Principios de diseño

1.3 Determinismo

1.4 Modularidad

1.5 Agentes intercambiables

1.6 Motores de ejecución intercambiables

1.7 Memoria intercambiable

1.8 Sandbox intercambiable

1.9 Persistencia

1.10 Recuperación después de fallos

1.11 No reconstrucción del Workflow ante cambios


---

PARTE II — ARQUITECTURA MAESTRA

2. Arquitectura global

OPENCLAW
                            │
                            ▼
                     CONTROL KERNEL
                            │
                 ┌──────────┴──────────┐
                 ▼                     ▼
           GOAL ENGINE            CHANGE ENGINE
                 │                     │
                 └──────────┬──────────┘
                            ▼
                       DSL DAG
                            │
                            ▼
                    WORKFLOW ENGINE
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
           HERMES        MEMORY        RESEARCH
              │
              ▼
           SHERIFF
              │
              ▼
       UNIVERSAL HARNESS
              │
        AGENT ADAPTER
              │
              ▼
           SANDBOX
              │
              ▼
         VALIDATOR
              │
              ▼
        GITHUB / DEPLOY

3. Separación de responsabilidades

3.1 OpenClaw

3.2 Control Kernel

3.3 Workflow Engine

3.4 DSL DAG

3.5 Hermes

3.6 Universal Harness

3.7 Agent Adapter

3.8 Memory Adapter

3.9 Sandbox Adapter

3.10 GitHub Adapter

3.11 Execution Adapter


---

PARTE III — OPENCLAW

4. OpenClaw como interfaz principal

4.1 UI

4.2 Chats separados

4.3 Proyectos separados

4.4 Comunicación con Workflow

4.5 Comunicación con Hermes

4.6 Solicitud de Architecture Council

4.7 Consulta de estado

4.8 Priorización de tareas

4.9 Solicitud de investigación

4.10 Incorporación de instrucciones nuevas

5. OpenClaw → Workflow

5.1 Conversión de petición a Goal

5.2 Identificación del proyecto

5.3 Identificación del entorno

5.4 Identificación de prioridad

5.5 Creación del Change Request

5.6 Generación del DSL DAG


---

PARTE IV — CONTROL KERNEL

6. Control Kernel

6.1 Goal Engine

6.2 Policy Engine

6.3 Contract Engine

6.4 Change Engine

6.5 Agent Registry

6.6 Memory Router

6.7 Execution Router

6.8 Priority Manager

6.9 Dependency Manager

6.10 State Manager


---

PARTE V — GOALS

7. Goals de entrada

Los 10 Goals obligatorios.

7.1 Validación de entrada

7.2 Objetivo

7.3 Alcance

7.4 Restricciones

7.5 Arquitectura

7.6 Recursos

7.7 Memoria

7.8 Código fuente

7.9 Skills

7.10 Criterio de finalización

8. Goals de salida

Los 10 Goals de salida.

8.1 Objetivo cumplido

8.2 Arquitectura cumplida

8.3 Código validado

8.4 Tests

8.5 Seguridad

8.6 Documentación

8.7 Git

8.8 Deployment

8.9 Evidencia

8.10 Aprobación final


---

PARTE VI — ARCHITECTURE COUNCIL

9. Architecture Council

9.1 Council de 12 etapas

9.2 Selección de agentes

9.3 Investigación previa

9.4 Comparación de arquitecturas

9.5 Refutación

9.6 Análisis de riesgos

9.7 Decisiones

9.8 Consolidación

9.9 Architecture Document

9.10 Paso al ejecutor

10. Council Frontend

10.1 Investigación

10.2 Arquitectura

10.3 Decisiones

10.4 Entrega a Cline

11. Council Backend

11.1 Investigación

11.2 Arquitectura

11.3 Decisiones

11.4 Entrega a OpenCode


---

PARTE VII — DSL DAG SHERIFF

12. DSL DAG

12.1 Schema principal

12.2 Nodes

12.3 Edges

12.4 Dependencies

12.5 Inputs

12.6 Outputs

12.7 Conditions

12.8 Priority

12.9 Retry

12.10 Recovery

12.11 Timeout

12.12 Budget

12.13 Checkpoint

12.14 Evidence

12.15 Contracts

13. Sheriff

13.1 Sheriff de objetivos

13.2 Sheriff de arquitectura

13.3 Sheriff de investigación

13.4 Sheriff de código fuente

13.5 Sheriff de Skills

13.6 Sheriff de agentes

13.7 Sheriff de código

13.8 Sheriff de tests

13.9 Sheriff de GitHub

13.10 Sheriff de Deployment

14. Determinismo del Sheriff

14.1 Qué puede decidir el agente

14.2 Qué no puede decidir

14.3 Policies

14.4 Contratos

14.5 Validaciones

14.6 Bloqueos

14.7 Evidencia obligatoria


---

PARTE VIII — LONG-RUNNING LOOP ENGINE

15. Sistema de loops largos

15.1 Arquitectura

15.2 Iteraciones

15.3 Estados

15.4 Checkpoints

15.5 Persistencia

15.6 Reanudación

15.7 Loop dinámico

15.8 Loop paralelo

15.9 Dependencias

15.10 Subloops

15.11 Priorización

15.12 Pausas

15.13 Esperas

15.14 Condiciones de salida

16. Loop principal de 10 pasos

1. INGEST
2. UNDERSTAND
3. RESEARCH
4. ARCHITECT
5. PLAN
6. BUILD
7. TEST
8. REPAIR
9. VERIFY
10. PUBLISH

17. Recovery del Loop

17.1 Crash

17.2 Reinicio

17.3 API agotada

17.4 Timeout

17.5 Agente detenido

17.6 Sandbox perdido

17.7 Memoria temporal perdida

17.8 GitHub fallido

17.9 Recuperación desde checkpoint

17.10 Continuación automática

18. Watchdog

18.1 Detección

18.2 Estado incompleto

18.3 Reanudación

18.4 Programación de recuperación

18.5 Prevención de loops infinitos


---

PARTE IX — HERMES

19. Hermes como procesador independiente

Hermes no será simplemente otro ejecutor.

19.1 Sentinel

19.2 Sheriff

19.3 Juez

19.4 Supervisor

19.5 Validador

19.6 Verificador

19.7 Detector de desviaciones

19.8 Analizador de objetivos

19.9 Analizador de resultados

19.10 Generador de correcciones

20. Hermes durante la ejecución

Workflow
   ↓
Agente
   ↓
Resultado
   ↓
Hermes
   ↓
¿cumple?
 ┌─┴─┐
YES NO
 │   │
 ▼   ▼
next repair/change

21. Hermes → OpenClaw

21.1 Informe

21.2 Objetivos incumplidos

21.3 Errores

21.4 Tareas pendientes

21.5 Recomendaciones

21.6 Diagrama de flujo

21.7 Solicitud de nueva decisión


---

PARTE X — AGENTES INTERCAMBIABLES

22. Agent Registry

22.1 Registro

22.2 Capabilities

22.3 Selección

22.4 Fallback

22.5 Health

22.6 Cost

22.7 Priority

22.8 Disponibilidad

23. Universal Harness

prepare()
load_context()
execute()
inspect()
cancel()
cleanup()

24. Agent Adapter

Permite utilizar diferentes agentes sin modificar el núcleo.


---

PARTE XI — GRUPO BACKEND

25. Pipeline Backend

Architecture Council
        ↓
OpenCode
        ↓
OpenHands
        ↓
Codex CLI
        ↓
Claude Code CLI

25.1 OpenCode

Ejecutor principal.

25.2 OpenHands

Recuperación / problemas complejos.

25.3 Codex CLI

Reparación / verificación.

25.4 Claude Code CLI

Reparación / refactor / ejecución final.

25.5 Reglas exactas de transición


---

PARTE XII — GRUPO FRONTEND

26. Pipeline Frontend

Architecture Council
        ↓
Cline
        ↓
OpenHands
        ↓
OpenCode
        ↓
Codex CLI
        ↓
Kimi Code CLI
        ↓
Mimo Code

26.1 Cline

Ejecutor principal.

26.2 OpenHands

Recuperación / tareas complejas.

26.3 OpenCode

Reparación / refactor.

26.4 Codex CLI

Revisión.

26.5 Kimi Code CLI

Especialista frontend / recuperación.

26.6 Mimo Code

Especialista frontend / recuperación final.

26.7 Reglas exactas de transición


---

PARTE XIII — RESEARCH ENGINE

27. Investigación Open Source

27.1 Descubrimiento

27.2 Normalización

27.3 Filtrado

27.4 Seguridad

27.5 Licencia

27.6 Actividad

27.7 Arquitectura

27.8 Compatibilidad

27.9 Tests

27.10 Ranking

28. Investigación mínima

20 candidatos por sistema/categoría.

28.1 Frontend

28.2 Backend

28.3 Memoria

28.4 Sandbox

28.5 Agentes

28.6 Herramientas auxiliares

29. Repository Score

Puntuación determinista.


---

PARTE XIV — SOURCE MIRROR

30. Código fuente Open Source

30.1 Descarga

30.2 Versionado

30.3 Commit original

30.4 Hash

30.5 Licencia

30.6 Procedencia

30.7 Integridad

31. Estructura

SOURCE_MIRROR/
├── frontend/
├── backend/
├── memory/
├── sandbox/
└── agents/

El agente utilizará el código fuente espejo como referencia cuando corresponda, evitando obligarlo a reconstruir desde cero lo que ya existe.


---

PARTE XV — SKILLS

32. Skill System

32.1 Repository de Skills

32.2 Categorías

32.3 Descubrimiento

32.4 Carga

32.5 Validación

32.6 Aplicación

32.7 Versionado

32.8 Sheriff de Skills

33. Skills obligatorios

El Workflow puede bloquear la ejecución si una tarea requiere un Skill obligatorio que no fue cargado o validado.


---

PARTE XVI — MEMORIA PERSISTENTE

34. Memory Fabric

34.1 Memory Adapter

34.2 Memory Router

34.3 Context Builder

34.4 Cache

34.5 Document Store

34.6 Vector Store

34.7 Graph Store

34.8 Relational Store

35. Graphiti

35.1 Entidades

35.2 Relaciones

35.3 Eventos

35.4 Historial

35.5 Versiones

36. GraphRAG / Graphify

36.1 Recuperación

36.2 Relaciones

36.3 búsqueda contextual

36.4 combinación con documentos

37. Memoria intercambiable

MemoryAdapter
├── Graphiti
├── GraphRAG
├── Vector DB
└── otro backend


---

PARTE XVII — DOCUMENT KNOWLEDGE SYSTEM

38. Proyecto

PROJECT/
├── README.md
├── METHOD.md
├── HANDOFF.md
├── ARCHITECTURE/
├── PIPELINE/
├── DESIGN/
├── REQUIREMENTS/
├── BACKEND/
├── FRONTEND/
├── DECISIONS/
└── DOCUMENTS/

39. Document Ingestion

39.1 Nuevo documento

39.2 Limpieza

39.3 Hash

39.4 Versionado

39.5 Indexación

39.6 Relaciones

39.7 Impact Analysis

40. Knowledge Anchor

Cada tarea queda vinculada a:

Project
Documents
Architecture
Memory
Skills
Source
Git Commit

41. Execution Anchor

Permite reconstruir exactamente qué contexto utilizó una ejecución.


---

PARTE XVIII — CHANGE ENGINE

42. Cambios sin reconstruir Workflow

42.1 Nuevo documento

42.2 Nueva instrucción

42.3 Corrección

42.4 Mejora

42.5 Nuevo requisito

42.6 Cambio arquitectónico

42.7 Sugerencia de OpenClaw

42.8 Sugerencia de Hermes

43. Impact Analysis

Determina qué nodos están afectados.

44. Dynamic DAG Update

Workflow existente
       ↓
Change Request
       ↓
Impact Analysis
       ↓
nodos afectados
       ↓
nuevo DSL DAG
       ↓
Sheriff
       ↓
continúa

No se reconstruye todo el sistema.


---

PARTE XIX — SANDBOX

45. Sandbox Manager

45.1 Sandbox por grupo

45.2 Frontend

45.3 Backend

45.4 Aislamiento

45.5 Filesystem

45.6 CPU

45.7 RAM

45.8 Red

45.9 Expiración

45.10 Recuperación

46. Sandbox Adapter

Permite cambiar la tecnología sin modificar el Workflow.


---

PARTE XX — FAILURE / RECOVERY

47. Failure Contract

Failure
├── type
├── detail
├── retryable
├── evidence
└── recovery_strategy

47.1 Tipos de fallo

47.2 Evidencia

47.3 Reintento

47.4 Fallback

47.5 Reparación

47.6 Escalamiento a Hermes


---

PARTE XXI — PRIORIDAD Y PARALELISMO

48. Priority Engine

48.1 Prioridad crítica

48.2 Alta

48.3 Normal

48.4 Baja

48.5 Preemption

48.6 Dependencias

49. Parallel Execution

49.1 Fan-out

49.2 Fan-in

49.3 Tareas independientes

49.4 Recursos compartidos

49.5 Límites de concurrencia

49.6 Coordinación mediante Workflow


---

PARTE XXII — CHAIN BUDGET

50. Presupuesto global

50.1 Tokens

50.2 Coste

50.3 Tiempo

50.4 Número de agentes

50.5 Reparaciones

50.6 Investigación

50.7 Ejecuciones paralelas

El presupuesto será para toda la cadena, no únicamente para un agente.


---

PARTE XXIII — GITHUB

51. Credential Broker

51.1 GitHub App

51.2 Token temporal

51.3 Scope mínimo

51.4 Repository binding

51.5 Expiración

51.6 Rotación

52. GitHub Adapter

Sandbox
 ↓
Validate
 ↓
Sheriff
 ↓
Credential Broker
 ↓
Branch
 ↓
Commit
 ↓
Push
 ↓
PR
 ↓
CI
 ↓
Merge

53. Idempotencia

Evitar duplicaciones de:

branch

commit

push

PR

deployment


54. GitHub Sheriff

54.1 Repo correcto

54.2 Branch correcta

54.3 Archivos permitidos

54.4 Cambios autorizados

54.5 Tests

54.6 Contratos

55. Rollback

55.1 Commit

55.2 Branch

55.3 PR

55.4 Deployment


---

PARTE XXIV — DEPLOYMENT

56. Deployment Pipeline

Code
 ↓
Validation
 ↓
Sheriff
 ↓
Commit
 ↓
Push
 ↓
PR
 ↓
CI
 ↓
Merge
 ↓
Build
 ↓
Deploy
 ↓
Health Check

56.1 Deployment determinista

56.2 Deployment Sheriff

56.3 Health Check

56.4 Rollback automático


---

PARTE XXV — OBSERVABILITY

57. Event Store

Cada acción genera:

Event
Checkpoint
Evidence
Decision
Actor
Timestamp
Version

57.1 Workflow history

57.2 Agent history

57.3 Memory history

57.4 Git history

57.5 Sheriff decisions

57.6 Hermes decisions


---

PARTE XXVI — EXECUTION ADAPTER

58. Independencia del motor

El Workflow no estará construido alrededor de un único orquestador.

ExecutionAdapter
├── Temporal
├── Dagu
├── Argo
└── Local

58.1 Workflow determinista

58.2 Activities

58.3 Checkpoints

58.4 Retries

58.5 Recovery

58.6 Señales

58.7 Persistencia


---

PARTE XXVII — PROGRAMACIÓN

59. Estructura del código

control-kernel/
├── core/
├── contracts/
├── dsl/
├── sheriff/
├── workflow/
├── loops/
├── agents/
├── harness/
├── memory/
├── documents/
├── research/
├── source_mirror/
├── skills/
├── sandbox/
├── github/
├── deployment/
├── recovery/
├── observability/
├── policies/
├── workflows/
└── tests/

60. Contratos de programación

60.1 Goal

60.2 Task

60.3 Node

60.4 Failure

60.5 Checkpoint

60.6 Evidence

60.7 Agent

60.8 Memory

60.9 Document

60.10 Change Request

60.11 Git Operation

60.12 Deployment


---

PARTE XXVIII — POLICIES

61. Configuración

policies/
├── frontend.yaml
├── backend.yaml
├── research.yaml
├── memory.yaml
├── github.yaml
├── sandbox.yaml
└── deployment.yaml

Las reglas modificables estarán en configuración cuando sea posible, no enterradas en código.


---

PARTE XXIX — SEGURIDAD

62. Security Layer

62.1 Credenciales

62.2 GitHub

62.3 Sandbox

62.4 Red

62.5 Código externo

62.6 Source Mirror

62.7 Skills

62.8 Agentes

62.9 Secrets

62.10 Auditoría


---

PARTE XXX — PRUEBAS DEL WORKFLOW

63. Tests deterministas

63.1 Input

63.2 DSL

63.3 Contracts

63.4 Agent

63.5 Memory

63.6 Sandbox

63.7 GitHub

63.8 Deployment

64. Tests de recuperación

caída del agente;

caída del sandbox;

caída del servidor;

API agotada;

timeout;

reinicio;

GitHub fallido;

memoria temporal perdida;

ejecución interrumpida.


65. Tests de cambios dinámicos

documento nuevo;

requisito nuevo;

corrección;

modificación de arquitectura;

cambio de agente;

cambio de Skill;

cambio de memoria.



---

PARTE XXXI — VALIDACIÓN FINAL

66. Validation Matrix

Goals
Architecture
Research
Source
Skills
Memory
Code
Tests
Git
Deployment

67. Hermes Final Audit

Hermes comprueba:

Objetivo
   ↓
Arquitectura
   ↓
Implementación
   ↓
Validación
   ↓
Git
   ↓
Deployment

68. Final Sheriff

Solo libera el resultado cuando todos los contratos requeridos estén satisfechos.


---

PARTE XXXII — PRINCIPIOS FINALES

69. Regla de separación

LLM             = razonamiento
OpenClaw        = interfaz
Workflow        = coordinación
DSL DAG         = definición del flujo
Sheriff         = autorización
Hermes          = supervisión
Harness         = interfaz universal
Adapter         = intercambiabilidad
Memory          = conocimiento
Documents       = fuente del proyecto
Skills          = capacidades obligatorias
Sandbox         = aislamiento
Validator       = comprobación
GitHub Adapter   = publicación
Event Store     = trazabilidad
Checkpoint      = recuperación
Change Engine   = evolución

70. Regla de evolución

Agregar un agente no debe requerir reconstruir el Workflow.

Cambiar Graphiti por otro sistema de memoria no debe requerir reconstruir el Workflow.

Cambiar Docker por otro sandbox no debe requerir reconstruir el Workflow.

Cambiar Temporal por otro Execution Engine no debe requerir reconstruir el Workflow.

Agregar un documento o requisito no debe requerir reconstruir el Workflow.

Una reparación no debe destruir el estado anterior.

Un reinicio no debe obligar a comenzar el loop desde cero.


---

Resultado de la auditoría

El WORKFLOW final queda compuesto por estas capas principales:

┌─────────────────┐
                    │    OPENCLAW     │
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │ CONTROL KERNEL  │
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │    DSL / DAG    │
                    └────────┬────────┘
                             ↓
                 ┌────────────────────────┐
                 │ LONG-RUNNING LOOP      │
                 └───────────┬────────────┘
                             ↓
                        ┌─────────┐
                        │ HERMES  │
                        └────┬────┘
                             ↓
                    ┌─────────────────┐
                    │    SHERIFFS     │
                    └────────┬────────┘
                             ↓
              ┌──────────────┴──────────────┐
              ↓                             ↓
        FRONTEND GROUP                BACKEND GROUP
              ↓                             ↓
        Agent Harness                  Agent Harness
              └──────────────┬──────────────┘
                             ↓
                         SANDBOX
                             ↓
                         VALIDATOR
                             ↓
                     MEMORY / DOCUMENTS
                             ↓
                          GITHUB
                             ↓
                         DEPLOY
                             ↓
                         HERMES
                             ↓
                        OPENCLAW

Este índice es el mapa maestro. Las siguientes etapas deben desarrollar cada bloque sin cambiar su función ni introducir un segundo orquestador disfrazado de Control Layer.


WORKFLOW — Salida 1/10

Arquitectura maestra + Control Kernel

Esta primera salida fija el núcleo del sistema. Las siguientes salidas deberán conectarse a esta arquitectura, no reemplazarla.


---

1. Objetivo del WORKFLOW

El WORKFLOW será una capa de control determinista que recibe objetivos desde OpenClaw, construye y ejecuta flujos de trabajo mediante DSL DAG, controla agentes, memoria, documentos, Skills, sandbox, validación y publicación.

Su función no es programar directamente.

Su función es decidir de forma controlada:

> qué debe hacerse → en qué orden → con qué información → qué agente puede hacerlo → qué debe validar → qué ocurre si falla → cómo se reanuda → cuándo se publica.



La ejecución pesada ocurre fuera del núcleo, mediante adapters.


---

2. Principio fundamental

La arquitectura queda separada así:

OPENCLAW
   │
   │ petición / conversación
   ▼
WORKFLOW CONTROL KERNEL
   │
   ├── Goals
   ├── Policies
   ├── Contracts
   ├── Change Engine
   ├── Agent Registry
   ├── Memory Router
   ├── Execution Router
   └── Priority Manager
   │
   ▼
DSL DAG
   │
   ▼
LONG-RUNNING LOOP ENGINE
   │
   ▼
HERMES
   │
   ▼
SHERIFF / VALIDATORS
   │
   ▼
UNIVERSAL HARNESS
   │
   ▼
AGENT ADAPTER
   │
   ▼
SANDBOX
   │
   ▼
VALIDATION
   │
   ▼
GITHUB / DEPLOY

La separación es deliberada.


---

3. Qué es y qué NO es el Control Kernel

Es

El cerebro determinista de coordinación.

Controla:

objetivos;

contratos;

políticas;

Workflow;

estado;

prioridades;

dependencias;

agentes disponibles;

memoria disponible;

cambios;

recuperación;

autorización.


No es

No debe convertirse en:

otro agente;

otro LLM;

un IDE;

un compilador;

un sandbox;

una base de datos;

un sistema de memoria;

un agente ejecutor.


Esto evita que la Control Layer se convierta en un segundo sistema gigantesco.


---

4. Arquitectura interna del Control Kernel

control-kernel
│
├── Goal Engine
│
├── Policy Engine
│
├── Contract Engine
│
├── Workflow Engine
│
├── Change Engine
│
├── Agent Registry
│
├── Memory Router
│
├── Execution Router
│
├── Priority Manager
│
├── Dependency Manager
│
└── State Manager

Cada componente tiene una responsabilidad concreta.


---

5. Goal Engine

Transforma una solicitud en un objetivo formal.

Ejemplo conceptual:

OpenClaw:
"Construye el sistema de autenticación del backend."

No se envía directamente al agente.

Primero:

OpenClaw
   ↓
Goal Engine
   ↓
Goal

El Goal contiene:

goal_id
project_id
description
scope
priority
constraints
required_skills
required_documents
target_environment
success_conditions

Después se aplican los 10 Goals de entrada que desarrollaremos en la salida 2.


---

6. Policy Engine

Las reglas no deberían estar escondidas dentro del código.

Se almacenarán como políticas.

Por ejemplo:

policies/
├── frontend.yaml
├── backend.yaml
├── research.yaml
├── github.yaml
├── sandbox.yaml
└── deployment.yaml

El Workflow consulta las políticas antes de ejecutar.

Ejemplo conceptual:

¿Puede este agente modificar este repositorio?

        │
   Policy Engine
        │
    ┌───┴───┐
   YES      NO
    │        │
    ▼        ▼
 execute    BLOCK

Esto hace que las reglas puedan evolucionar sin reescribir el núcleo.


---

7. Contract Engine

Los contratos son una de las piezas centrales del determinismo.

Un nodo no solamente dice:

ejecutar agente

Dice:

INPUT
REQUIREMENTS
ALLOWED_AGENT
REQUIRED_SKILLS
REQUIRED_MEMORY
ALLOWED_REPOSITORY
OUTPUT
VALIDATION
FAILURE_POLICY

Por tanto:

Agente
   ↓
resultado
   ↓
Contract Engine
   ↓
¿cumple contrato?

Si no cumple:

Failure
   ↓
Recovery

No se continúa simplemente porque el agente haya devuelto texto.


---

8. Workflow Engine

El Workflow Engine interpreta el DSL DAG.

Ejemplo:

RESEARCH
    ↓
ARCHITECTURE
    ↓
PLAN
    ↓
BUILD
    ↓
TEST
    ↓
REPAIR
    ↓
VERIFY
    ↓
PUBLISH

Pero no tiene que ser siempre lineal.

Puede hacer:

ARCHITECTURE
          /     |      \
         /      |       \
   BACKEND   FRONTEND   SECURITY
       \        |        /
        \       |       /
             VERIFY

El DAG define las dependencias.


---

9. El Workflow no queda codificado rígidamente

Esto es importante para el sistema que quieres.

No queremos:

step1()
step2()
step3()
step4()

porque cualquier modificación obligaría a cambiar el programa.

Queremos:

Workflow Engine
      ↓
DSL
      ↓
interpreta nodos
      ↓
ejecuta

Por tanto, un cambio puede modificar el DAG sin reconstruir el motor.


---

10. Change Engine

Será una pieza fundamental.

Recibe:

nuevo documento;

nuevo requisito;

corrección;

sugerencia de OpenClaw;

sugerencia de Hermes;

cambio arquitectónico;

nuevo Skill;

cambio de dependencia.


Ejemplo:

Documento nuevo
      ↓
Change Engine
      ↓
Impact Analysis
      ↓
¿qué nodos afecta?
      ↓
genera Change Request
      ↓
actualiza DAG
      ↓
Sheriff
      ↓
continúa

No reconstruye todo.


---

11. Agent Registry

El Workflow no debe estar programado específicamente para Cline, OpenCode, Codex, etc.

Debe preguntar al Registry:

Necesito:
capability = frontend_executor

El Registry responde qué agentes disponibles pueden cumplirla.

Ejemplo:

frontend_executor
    ↓
Cline

Si Cline no está disponible:

frontend_executor
    ↓
OpenHands

La lógica de selección queda separada del agente.


---

12. Execution Router

Separa el Workflow del motor que realmente ejecuta las actividades.

Workflow
   ↓
Execution Router
   ↓
Execution Adapter

Puede existir:

TemporalAdapter
DaguAdapter
LocalAdapter
ArgoAdapter

El Workflow no necesita saber cuál está debajo.

Esto permite cambiar el motor posteriormente.


---

13. Memory Router

Los agentes tampoco deberían conectarse directamente a Graphiti.

La arquitectura será:

Agent
  ↓
Context Builder
  ↓
Memory Router
  ↓
Memory Adapter
  ↓
Graphiti / GraphRAG / Vector DB / etc.

Así podemos cambiar el sistema de memoria sin modificar los agentes.

La implementación detallada será la salida 6.


---

14. Priority Manager

Cada tarea tendrá prioridad.

Conceptualmente:

CRITICAL
HIGH
NORMAL
LOW

El Priority Manager determina qué tarea puede ejecutarse primero respetando:

dependencias;

recursos;

contratos;

estado del Workflow.


Una prioridad no puede saltarse un contrato de seguridad.


---

15. Dependency Manager

Determina qué puede ejecutarse en paralelo.

Ejemplo:

Architecture
      ↓
 ┌────┴────┐
 ↓         ↓
Backend  Frontend
 ↓         ↓
 └────┬────┘
      ↓
    Verify

Backend y Frontend pueden ejecutarse simultáneamente porque son ramas independientes.

Pero Verify espera ambas.


---

16. State Manager

El Workflow debe conocer permanentemente:

Workflow
Task
Node
Agent
Sandbox
Memory
Checkpoint
Failure
Change
Git
Deployment

El estado no debe depender exclusivamente de RAM.

Esto será fundamental para los loops largos.


---

17. Arquitectura de estado

Conceptualmente:

STATE
                   │
        ┌──────────┼──────────┐
        ▼          ▼          ▼
    Workflow     Tasks     Checkpoints
        │          │          │
        └──────────┼──────────┘
                   ▼
               Event Store

Así, después de un reinicio:

Servidor cae
     ↓
servidor vuelve
     ↓
State Manager
     ↓
último checkpoint
     ↓
Recovery
     ↓
continúa

El Long-Running Loop se desarrollará en la salida 3.


---

18. Relación con Hermes

Hermes estará separado del Control Kernel, pero conectado a él.

CONTROL KERNEL
                   │
                   ▼
              WORKFLOW
                   │
                   ▼
                HERMES
                   │
       ┌───────────┼───────────┐
       ▼           ▼           ▼
    Sentinel     Judge     Supervisor
       │           │           │
       └───────────┼───────────┘
                   ▼
              Validation
                   │
             ┌─────┴─────┐
             ▼           ▼
          ACCEPT       CHANGE
                         │
                         ▼
                    Change Engine

Hermes no sustituye al Workflow.

Hermes supervisa el cumplimiento del Workflow.


---

19. Relación con los agentes

El flujo final será:

Workflow
   ↓
selecciona capability
   ↓
Agent Registry
   ↓
Universal Harness
   ↓
Agent Adapter
   ↓
Sandbox
   ↓
Agente

El agente nunca recibe autoridad ilimitada.

Recibe:

Task
Context
Documents
Memory
Skills
Repository
Constraints

y produce:

Result
Evidence
Artifacts


---

20. El principio de autoridad

La jerarquía será:

PROJECT DOCUMENTS
       ↓
GOALS
       ↓
POLICIES
       ↓
DSL DAG
       ↓
SHERIFF CONTRACTS
       ↓
AGENT

El agente no puede redefinir unilateralmente:

el objetivo;

el repositorio;

los permisos;

los contratos;

los criterios de validación;

la política de publicación.


Puede proponer cambios.

Hermes los analiza.

El Change Engine los convierte en cambios formales.

El Sheriff los valida.


---

21. Flujo maestro de una tarea

1. OpenClaw
      ↓
2. Goal Engine
      ↓
3. Policy Engine
      ↓
4. Contract Engine
      ↓
5. Architecture Council
      ↓
6. DSL DAG
      ↓
7. Research
      ↓
8. Memory / Documents / Skills
      ↓
9. Agent Registry
      ↓
10. Harness
      ↓
11. Sandbox
      ↓
12. Agent
      ↓
13. Validator
      ↓
14. Hermes
      ↓
15. Sheriff
      ↓
16. Repair / Continue
      ↓
17. GitHub
      ↓
18. Deployment
      ↓
19. Hermes final audit
      ↓
20. OpenClaw

Los pasos 5–20 serán desarrollados individualmente en las siguientes salidas.


---

22. Regla de oro del WORKFLOW

El sistema completo debe cumplir:

CAMBIAR AGENTE
        ↓
NO REESCRIBIR WORKFLOW

CAMBIAR MEMORIA
        ↓
NO REESCRIBIR WORKFLOW

CAMBIAR SANDBOX
        ↓
NO REESCRIBIR WORKFLOW

CAMBIAR MOTOR DE EJECUCIÓN
        ↓
NO REESCRIBIR WORKFLOW

AÑADIR DOCUMENTO
        ↓
NO REESCRIBIR WORKFLOW

AÑADIR SKILL
        ↓
NO REESCRIBIR WORKFLOW

AÑADIR REQUISITO
        ↓
CHANGE ENGINE
        ↓
NO REESCRIBIR WORKFLOW

Ese principio es el que permite que el sistema pueda evolucionar durante años sin convertirse en una enorme pieza monolítica.


---

23. Resultado de esta primera capa

La arquitectura queda conceptualmente:

OPENCLAW
                            │
                            ▼
                    ┌───────────────┐
                    │ CONTROL KERNEL│
                    ├───────────────┤
                    │ Goals         │
                    │ Policies      │
                    │ Contracts     │
                    │ Workflow      │
                    │ Change        │
                    │ Agents        │
                    │ Memory        │
                    │ Execution     │
                    │ Priority      │
                    │ State         │
                    └───────┬───────┘
                            │
                            ▼
                         DSL DAG
                            │
                            ▼
                    LONG-RUNNING LOOP
                            │
                            ▼
                         HERMES
                            │
                            ▼
                        SHERIFF
                            │
                            ▼
                     UNIVERSAL HARNESS
                            │
                            ▼
                      AGENT ADAPTER
                            │
                            ▼
                         SANDBOX
                            │
                            ▼
                        VALIDATOR
                            │
                            ▼
                     GITHUB / DEPLOY

Esta es la base que queda fijada. La siguiente salida debe desarrollar Goals + Architecture Council + DSL DAG + contratos Sheriff, sin alterar esta arquitectura.

WORKFLOW — Salida 2/10

Goals + Architecture Council + DSL DAG + contratos Sheriff

Esta salida define cómo el Workflow sabe qué hacer, cómo decide el flujo y cómo impide que un agente se salga del proceso.


---

1. Cadena de control

OpenClaw
   ↓
10 INPUT GOALS
   ↓
Architecture Council
   ↓
Research
   ↓
Architecture Decision
   ↓
DSL DAG
   ↓
Sheriff Contracts
   ↓
Long-Running Loop

El LLM puede proponer decisiones, pero la ejecución queda gobernada por contratos y reglas deterministas.


---

2. Los 10 Goals de entrada

Cada tarea comienza creando un GoalSet.

G01 — OBJECTIVE
¿Qué se quiere conseguir?

G02 — SCOPE
¿Qué parte del proyecto está afectada?

G03 — REQUIREMENTS
¿Qué requisitos debe cumplir?

G04 — CONSTRAINTS
¿Qué restricciones existen?

G05 — ARCHITECTURE
¿Qué arquitectura/documentos son autoridad?

G06 — RESOURCES
¿Qué agentes, APIs, repositorios y recursos están autorizados?

G07 — MEMORY
¿Qué información persistente debe consultarse?

G08 — SOURCE
¿Qué código existente debe investigarse/reutilizarse?

G09 — SKILLS
¿Qué Skills son obligatorios?

G10 — SUCCESS
¿Cómo se determina objetivamente que terminó?

El Workflow no permite pasar a ejecución mientras falten Goals obligatorios.


---

3. Goal Contract

Conceptualmente:

GoalContract
├── goal_id
├── project_id
├── objective
├── scope
├── requirements
├── constraints
├── architecture_refs
├── resources
├── memory_refs
├── source_refs
├── required_skills
├── success_conditions
└── priority

El GoalContract se guarda con el Workflow.

Esto permite reconstruir posteriormente por qué se ejecutó una tarea.


---

4. Goals de salida

El Workflow termina solamente cuando los 10 objetivos de salida están comprobados.

O01 — OBJECTIVE
Objetivo cumplido.

O02 — ARCHITECTURE
Arquitectura respetada.

O03 — REQUIREMENTS
Requisitos satisfechos.

O04 — CODE
Código producido/modificado correctamente.

O05 — TEST
Pruebas ejecutadas.

O06 — SECURITY
Validaciones de seguridad.

O07 — DOCUMENTATION
Documentación actualizada.

O08 — GIT
Cambios publicados correctamente.

O09 — DEPLOYMENT
Deployment validado cuando corresponda.

O10 — EVIDENCE
Existe evidencia suficiente para auditar el resultado.

No son simples textos.

Cada Goal produce un estado:

PASS
FAIL
BLOCKED
NOT_REQUIRED


---

5. Architecture Council

Antes de que el ejecutor principal programe, el Workflow puede lanzar un Architecture Council.

Su función es:

> analizar el problema antes de gastar recursos importantes construyendo.



El Council recibe:

GoalSet
+
Project Documents
+
Memory
+
Research
+
Source Mirror
+
Skills


---

6. Council de 12

El Council tendrá 12 posiciones de análisis, no necesariamente 12 modelos diferentes.

Esto es importante para mantener el sistema económico.

Una misma infraestructura puede ejecutar diferentes roles.

C01 Requirements Analyst
C02 Architecture Analyst
C03 Repository Researcher
C04 Open Source Researcher
C05 Security Analyst
C06 Backend Analyst
C07 Frontend Analyst
C08 Data/Memory Analyst
C09 Testing Analyst
C10 Failure/Recovery Analyst
C11 Cost/Resource Analyst
C12 Architecture Referee

Cada posición genera una salida estructurada.


---

7. El Council no programa

El Council produce:

ArchitectureProposal

No produce directamente el código final.

Ejemplo:

ArchitectureProposal
├── objective
├── architecture
├── components
├── dependencies
├── repositories
├── risks
├── alternatives
├── rejected_options
├── implementation_order
└── validation_strategy


---

8. Investigación antes de construir

El Council activa el Research Engine.

La regla que fijaste queda:

> mínimo 20 candidatos investigados por sistema/categoría cuando la tarea requiera investigación de Open Source.



Ejemplo Backend:

20+ repositorios candidatos
       ↓
normalización
       ↓
licencia
       ↓
actividad
       ↓
compatibilidad
       ↓
arquitectura
       ↓
seguridad
       ↓
tests
       ↓
ranking

No significa descargar automáticamente los 20.

Significa investigarlos.

Los candidatos seleccionados pasan posteriormente a Source Mirror.

Eso se desarrollará en la salida 7.


---

9. DSL DAG

Una vez que el Council produce la arquitectura, el Workflow convierte la decisión en un DAG.

Ejemplo:

RESEARCH
   ↓
ARCHITECTURE
   ↓
SOURCE_PREPARATION
   ↓
SKILLS
   ↓
PLAN
   ↓
BUILD
   ↓
TEST
   ↓
VERIFY
   ↓
PUBLISH

Cada nodo posee un contrato.


---

10. Estructura conceptual de un nodo

Node
├── id
├── type
├── input
├── dependencies
├── capability
├── allowed_agents
├── required_skills
├── memory_requirements
├── source_requirements
├── sandbox_policy
├── validator
├── sheriff_policy
├── retry_policy
├── recovery_policy
├── timeout
├── budget
├── priority
└── output

Esto permite que el Workflow sea configurable sin reescribir el motor.


---

11. Ejemplo

Supongamos:

BUILD_BACKEND

El nodo podría exigir:

capability:
    backend_executor

required_skills:
    backend-development

source_required:
    true

repository:
    backend-repository

sandbox:
    backend-sandbox

validator:
    backend-validator

El agente no decide por sí mismo dónde trabajar.

El Workflow ya lo determinó.


---

12. Contracts Sheriff

El Sheriff funciona mediante contratos.

Ejemplo:

BUILD_BACKEND_CONTRACT

requiere:

INPUT:
    ArchitectureDocument
    Requirements
    SourceMirror
    Skills

ALLOWED:
    backend-repository

FORBIDDEN:
    frontend-repository

OUTPUT:
    code_changes
    evidence
    test_results

Si intenta modificar otro repositorio:

SHERIFF → BLOCK


---

13. Tipos principales de contratos

Tendremos contratos especializados:

GoalContract
ArchitectureContract
ResearchContract
SourceContract
SkillContract
AgentContract
SandboxContract
MemoryContract
BuildContract
TestContract
RepairContract
VerificationContract
GitContract
DeploymentContract

No se utilizará un único contrato gigante para todo.


---

14. Contrato de agente

El agente recibe una capacidad concreta.

AgentContract
├── agent_id
├── capability
├── task
├── allowed_repository
├── allowed_paths
├── allowed_tools
├── memory_context
├── required_skills
├── timeout
├── budget
└── output_contract

Por ejemplo:

OpenCode
    capability = backend_executor

No significa que OpenCode tenga autorización universal.

Solo tiene la autorización del nodo actual.


---

15. Contrato de memoria

El agente no solicita libremente toda la memoria.

El Workflow genera:

ContextRequest

con:

project
documents
entities
relationships
history
code_context
decisions

El Memory Adapter devuelve únicamente el contexto autorizado/relevante.

Esto evita inundar el agente con todo el historial.


---

16. Contrato de Source Mirror

Cuando la tarea exige reutilización de Open Source:

source_required = true

Entonces:

Sheriff
   ↓
¿Existe Source Mirror?
   │
  NO
   ↓
BLOCK

El agente no puede simplemente ignorar la investigación y construir desde cero.


---

17. Contrato de Skills

Igualmente:

required_skills:
    [skill-a, skill-b]

Antes de ejecutar:

Skill Resolver
      ↓
¿Skills disponibles?
   ┌──┴──┐
  YES    NO
   │      │
   ▼      ▼
execute  BLOCK

Esto hace que los Skills puedan ser obligatorios, no simples sugerencias.


---

18. Determinismo

El punto fundamental:

El LLM puede decir:

> "Creo que deberíamos usar X."



Pero no puede ejecutar X directamente.

La cadena es:

LLM
 ↓
Proposal
 ↓
Schema validation
 ↓
Policy validation
 ↓
Sheriff
 ↓
DAG
 ↓
Execution

La decisión de ejecutar pertenece al Workflow.


---

19. Contrato de transición

Cada cambio de agente también es determinista.

Ejemplo Backend:

OpenCode
   ↓
Validator
   ↓
FAIL
   ↓
Failure Classification
   ↓
¿Recovery compatible?
   ↓
OpenHands

No:

OpenCode decide llamar a OpenHands.

Sino:

Workflow decide según Failure Policy.


---

20. Failure Contract

Todo fallo tendrá estructura:

Failure
├── failure_id
├── node_id
├── type
├── severity
├── detail
├── retryable
├── evidence
├── recovery_strategy
├── affected_files
└── timestamp

Ejemplo:

type:
    TEST_FAILURE

retryable:
    true

recovery_strategy:
    REPAIR_AGENT

Hermes puede analizarlo, pero el Workflow mantiene el estado formal.


---

21. Sheriff como puerta de control

Cada transición importante pasa por Sheriff:

┌─────────────┐
                 │   PROPOSAL  │
                 └──────┬──────┘
                        ↓
                 ┌─────────────┐
                 │   CONTRACT  │
                 └──────┬──────┘
                        ↓
                 ┌─────────────┐
                 │   POLICY    │
                 └──────┬──────┘
                        ↓
                 ┌─────────────┐
                 │   SHERIFF   │
                 └──────┬──────┘
                    ┌───┴───┐
                   PASS    BLOCK
                    │
                    ▼
                 EXECUTE


---

22. DSL DAG + contratos

La combinación final:

DSL DAG
   │
   ├── estructura del proceso
   │
   └── contratos
          │
          ├── qué necesita
          ├── quién puede ejecutarlo
          ├── qué puede tocar
          ├── qué debe producir
          ├── cómo se valida
          └── qué ocurre si falla

Esto es lo que convierte el Workflow en un sistema controlado y reproducible.


---

23. Cómo queda el flujo completo

OPENCLAW
                       │
                       ▼
                 INPUT GOALS
                       │
                       ▼
              ARCHITECTURE COUNCIL
                       │
                       ▼
                  RESEARCH
                       │
                       ▼
              ARCHITECTURE PROPOSAL
                       │
                       ▼
                    DSL DAG
                       │
                       ▼
                 CONTRACTS
                       │
                       ▼
                   SHERIFF
                       │
                       ▼
                LONG LOOP ENGINE
                       │
                       ▼
                    AGENT
                       │
                       ▼
                   VALIDATOR
                       │
                       ▼
                    HERMES
                       │
                ┌──────┴──────┐
                ▼             ▼
             ACCEPT         CHANGE
                │             │
                ▼             ▼
             NEXT          CHANGE ENGINE
                              │
                              └──→ DSL DAG


---

24. Qué queda establecido después de la salida 2

Tenemos ya definidos conceptualmente:

Entrada

10 Goals

Razonamiento previo

Architecture Council de 12

Proceso

DSL DAG

Control

Contracts + Policies + Sheriff

Ejecución

Long-Running Loop

Supervisión

Hermes

Resultado

10 Output Goals

La siguiente salida debe desarrollar el componente más importante para tu requisito de procesos extensos:

Salida 3/10 — Long-Running Loop Engine

Ahí definiremos a nivel de programación los 10 pasos del loop, subloops, loops anidados, checkpoints, persistencia, recuperación después de reinicios, watchdog, API agotada, prioridades, paralelismo, pausas, reanudación y cambios dinámicos sin reconstruir el Workflow.

WORKFLOW — Salida 3/10

Long-Running Loop Engine + recuperación + ejecución paralela

Aquí definimos el motor que permite que un proceso dure horas, días o miles de pasos, se detenga, se modifique, se reinicie y continúe sin reconstruirse desde cero.

La regla principal:

> El loop es parte del modelo del WORKFLOW; el motor de ejecución que lo mantiene vivo es intercambiable.




---

1. Arquitectura

WORKFLOW
                       │
                       ▼
              LONG-RUNNING LOOP
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
      State        Scheduler     Checkpoint
      Manager        │              │
          │          ▼              │
          │       Executor          │
          │          │              │
          └──────────┼──────────────┘
                     ▼
                   HERMES
                     │
              ┌──────┴──────┐
              ▼             ▼
           CONTINUE       CHANGE
              │             │
              └──────┬──────┘
                     ▼
                 NEXT STEP


---

2. No será un while gigante

No queremos:

while not finished:
    execute()

porque si el proceso dura mucho tiempo se vuelve difícil recuperar:

estado;

errores;

contexto;

checkpoints;

cambios;

prioridades;

agentes;

presupuesto.


En su lugar, cada iteración es una unidad persistente de trabajo.

Loop
 ├── iteration 001
 ├── iteration 002
 ├── iteration 003
 ├── ...
 └── iteration N


---

3. Estado del Loop

Cada loop mantiene un LoopState.

Conceptualmente:

LoopState
├── loop_id
├── workflow_id
├── project_id
├── version
├── iteration
├── current_node
├── status
├── priority
├── active_tasks
├── completed_tasks
├── failed_tasks
├── pending_changes
├── checkpoints
├── budget
├── deadlines
└── timestamps

Estados:

CREATED
READY
RUNNING
WAITING
PAUSED
RECOVERING
BLOCKED
COMPLETED
FAILED
CANCELLED


---

4. Los 10 pasos del Loop

El loop estándar queda:

01 INGEST
      ↓
02 UNDERSTAND
      ↓
03 RESEARCH
      ↓
04 ARCHITECT
      ↓
05 PLAN
      ↓
06 BUILD
      ↓
07 TEST
      ↓
08 REPAIR
      ↓
09 VERIFY
      ↓
10 PUBLISH

Pero no significa que cada tarea tenga que ejecutar siempre los 10.

El DSL determina cuáles son necesarios.


---

5. Paso 1 — INGEST

Recibe:

Goal;

documentos;

cambios;

instrucciones;

contexto;

estado previo.


OpenClaw
   ↓
Goal
   ↓
Document Resolver
   ↓
Memory Resolver
   ↓
Context Builder

Resultado:

InputContext


---

6. Paso 2 — UNDERSTAND

El Workflow determina:

qué se pide
qué proyecto afecta
qué repositorio
qué restricciones
qué documentos son autoridad
qué Skills son obligatorios
qué recursos están autorizados

Aquí todavía no se programa.


---

7. Paso 3 — RESEARCH

Cuando corresponde:

Research Engine
       ↓
Open Source
       ↓
Candidates
       ↓
Ranking
       ↓
Source Mirror

El resultado queda anclado al Workflow.


---

8. Paso 4 — ARCHITECT

Architecture Council genera:

ArchitectureProposal

Hermes/Sheriff validan la propuesta.

Solo después se permite construir.


---

9. Paso 5 — PLAN

El plan se convierte en DAG:

Plan
 ↓
Nodes
 ↓
Dependencies
 ↓
Contracts
 ↓
Execution Graph

Ejemplo:

PLAN
           │
     ┌─────┼─────┐
     ▼     ▼     ▼
  Backend Frontend Tests
     │      │
     └──┬───┘
        ▼
      Verify


---

10. Paso 6 — BUILD

Aquí entra el grupo ejecutor correspondiente.

Backend:

OpenCode
 → OpenHands
 → Codex CLI
 → Claude Code CLI

Frontend:

Cline
 → OpenHands
 → OpenCode
 → Codex CLI
 → Kimi Code CLI
 → Mimo Code

El cambio de agente no lo decide el agente.

Lo decide la política de recuperación del Workflow.


---

11. Paso 7 — TEST

El resultado pasa por Validator.

Code
 ↓
Tests
 ↓
Static validation
 ↓
Contract validation
 ↓
Sheriff

Resultado:

PASS

o:

Failure


---

12. Paso 8 — REPAIR

Si existe un fallo:

Failure
   ↓
Failure Classifier
   ↓
Recovery Policy
   ↓
selecciona estrategia

Puede:

RETRY
REPAIR
CHANGE_AGENT
CHANGE_PLAN
REQUEST_RESEARCH
REQUEST_COUNCIL
WAIT
ESCALATE_HERMES
BLOCK

No existe un único mecanismo de reparación.


---

13. Paso 9 — VERIFY

Hermes comprueba:

Objetivo
Arquitectura
Requisitos
Código
Tests
Documentación

Y el Sheriff comprueba contratos.

Hermes
  ↓
Sheriff
  ↓
VerificationResult


---

14. Paso 10 — PUBLISH

Solo si corresponde:

Validator
 ↓
Sheriff
 ↓
GitHub Adapter
 ↓
Commit
 ↓
Push
 ↓
PR
 ↓
CI
 ↓
Deploy

La implementación completa de GitHub se desarrollará en la salida 9.


---

15. Checkpoint Engine

Este es uno de los componentes más importantes.

Después de cada unidad importante:

Node completed
      ↓
Checkpoint
      ↓
Persist State

Ejemplo:

CP-001 INGEST
CP-002 RESEARCH
CP-003 ARCHITECTURE
CP-004 PLAN
CP-005 BUILD

No es necesario guardar absolutamente todo en cada microacción.

Se definen puntos de checkpoint.


---

16. Qué contiene un Checkpoint

Checkpoint
├── checkpoint_id
├── workflow_id
├── loop_id
├── iteration
├── node
├── state_version
├── DAG_version
├── goal_version
├── active_tasks
├── completed_tasks
├── memory_anchors
├── document_versions
├── source_versions
├── skill_versions
├── agent_execution
├── sandbox_reference
├── failures
└── evidence

Así podemos reconstruir el estado.


---

17. Recuperación después de reinicio

Ejemplo:

BUILD
  ↓
agente trabajando
  ↓
SERVIDOR SE CAE

Al volver:

START
  ↓
State Manager
  ↓
último Checkpoint
  ↓
Recovery Engine
  ↓
verifica estado
  ↓
reconstruye contexto
  ↓
Sheriff
  ↓
continúa

No:

empezar desde cero


---

18. Recuperación de un agente

Si OpenCode falla:

OpenCode
   ↓
Failure
   ↓
Recovery Policy
   ↓
OpenHands

Si OpenHands falla:

OpenHands
   ↓
Failure
   ↓
Codex CLI

etc.

Pero el Workflow conserva:

qué intentó cada agente
qué modificó
qué falló
qué evidencia produjo


---

19. Recuperación de API agotada

Si una API se queda sin saldo:

Agent
 ↓
API Failure
 ↓
Failure Classifier
 ↓
WAIT / CHANGE_PROVIDER

El estado queda:

WAITING_FOR_RESOURCE

El Workflow no pierde el trabajo.

Cuando el recurso vuelva:

WATCHDOG
   ↓
detecta disponibilidad
   ↓
Recovery
   ↓
resume checkpoint


---

20. Recuperación después de la 1 AM

El mecanismo no dependerá de una hora específica.

Puede existir una política:

resume_policy:
    enabled: true
    retry_after_resource_recovery: true

Y un scheduler externo puede despertar el proceso.

Por ejemplo:

01:00
 ↓
Recovery Scheduler
 ↓
buscar workflows WAITING
 ↓
comprobar recursos
 ↓
reanudar

El Workflow conserva la lógica; el scheduler solo dispara la reanudación.


---

21. Watchdog

El Watchdog vigila:

Workflow
Loop
Agent
Sandbox
Execution Engine
Resources

Detecta:

stalled
timeout
crashed
memory_limit
resource_unavailable
heartbeat_missing

Pero el Watchdog no improvisa una solución.

Produce:

Failure / Recovery Event

y la política determina qué hacer.


---

22. Long Loop

Un Workflow puede tener:

Loop 001
  ├── Node A
  ├── Node B
  ├── Node C
  └── Loop 002
       ├── Node X
       ├── Node Y
       └── Loop 003

Por tanto permite:

loops anidados.


---

23. Subloops

Ejemplo:

MAIN LOOP
│
├── Research
│    └── Research Loop
│         ├── Search
│         ├── Evaluate
│         ├── Compare
│         └── Rank
│
├── Build
│    └── Repair Loop
│         ├── Diagnose
│         ├── Repair
│         ├── Test
│         └── Verify
│
└── Publish

Esto permite procesos profundos sin convertir todo en un único loop gigante.


---

24. Ejecución paralela

Cuando dos tareas no tienen dependencia:

PLAN
               │
        ┌──────┼──────┐
        ▼      ▼      ▼
     Backend Frontend Security
        │      │      │
        └──────┼──────┘
               ▼
             VERIFY

El Scheduler puede ejecutar las tres ramas simultáneamente.

Pero:

VERIFY

espera a que sus dependencias terminen.


---

25. Prioridades

Cada Node tiene:

priority

Ejemplo:

CRITICAL = 100
HIGH     = 75
NORMAL   = 50
LOW      = 25

El Scheduler utiliza prioridad + dependencias + recursos.

Pero:

> la prioridad nunca puede violar un contrato.



Una tarea crítica no puede saltarse:

Security
Sheriff
Required Skills
Required validation


---

26. Cambios durante el Loop

Este es uno de los puntos más importantes de tu sistema.

Supongamos:

iteration 84
BUILD

y llega:

nuevo documento

No hacemos:

reiniciar Workflow

Hacemos:

New Document
     ↓
Change Engine
     ↓
Impact Analysis
     ↓
Change Request
     ↓
DAG Version 2
     ↓
Sheriff
     ↓
Checkpoint
     ↓
continuar


---

27. Versionado del DAG

Esto permite tener:

DAG v1
DAG v2
DAG v3

El Workflow conserva qué versión utilizó cada ejecución.

Ejemplo:

CP-080 → DAG v1
CHANGE-031
CP-081 → DAG v2

Esto es fundamental para auditoría.


---

28. No destruir el historial

Nunca hacemos:

actualizar DAG
borrar anterior

Sino:

DAG v1
   ↓
Change
   ↓
DAG v2

La versión anterior permanece como evidencia.


---

29. Estado de una tarea

Cada tarea puede estar:

PENDING
READY
RUNNING
WAITING
PAUSED
RETRYING
REPAIRING
VERIFYING
COMPLETED
FAILED
BLOCKED
CANCELLED

Esto permite al sistema saber exactamente dónde quedó.


---

30. Paralelismo controlado

No significa lanzar agentes ilimitadamente.

Existe:

ConcurrencyPolicy

que controla:

max_parallel_tasks
max_agents
max_cpu
max_memory
max_api_requests
max_cost

Esto será conectado posteriormente al sistema de recursos.


---

31. ChainBudget

El presupuesto se aplica a toda la cadena.

CHAIN BUDGET
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
        TIME           COST          TOKENS
          │              │              │
          └──────────────┼──────────────┘
                         ▼
                    ALL AGENTS

Ejemplo:

Budget:
  max_time = X
  max_cost = Y
  max_tokens = Z

Si OpenCode consume parte del presupuesto:

OpenCode
 ↓
remaining budget
 ↓
OpenHands

No se concede un presupuesto independiente infinito a cada fallback.


---

32. Condiciones de salida

El loop termina únicamente cuando:

SUCCESS
FAILURE
BLOCKED
CANCELLED
BUDGET_EXCEEDED
TIMEOUT
MAX_ITERATIONS
HUMAN_APPROVAL_REQUIRED

Y existe una protección contra:

loop infinito

mediante:

máximo de iteraciones;

presupuesto;

detección de repetición;

falta de progreso;

timeout;

Sheriff.



---

33. Detección de falta de progreso

Ejemplo:

Repair 1 → mismo error
Repair 2 → mismo error
Repair 3 → mismo error

El sistema detecta:

NO_PROGRESS

y puede cambiar de estrategia:

REPAIR
   ↓
CHANGE_AGENT
   ↓
RESEARCH
   ↓
ARCHITECTURE_REVIEW
   ↓
HERMES

No se limita a repetir indefinidamente.


---

34. Arquitectura de recuperación

FAILURE
                     │
                     ▼
              Failure Classifier
                     │
              Recovery Policy
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
      RETRY        REPAIR       CHANGE
        │            │            │
        └────────────┼────────────┘
                     ▼
                  CHECKPOINT
                     │
                     ▼
                   RESUME


---

35. Independencia del motor

El Long-Running Loop no dependerá directamente de Temporal.

LOOP ENGINE
                     │
              Execution Adapter
          ┌──────────┼──────────┐
          ▼          ▼          ▼
       Temporal     Dagu       Local

Si posteriormente cambias Temporal por otro sistema:

Loop Engine
     ↓
otro Adapter

El modelo del Workflow permanece.


---

36. La regla fundamental

El Long-Running Loop será:

persistente + versionado + recuperable + paralelizable + priorizable + modificable.

Y además:

nuevo documento
nuevo requisito
nueva arquitectura
nuevo agente
nuevo Skill
nuevo método de reparación
nuevo backend de memoria

pueden incorporarse mediante el Change Engine, sin reconstruir el Workflow completo.


---

37. Resultado de la salida 3

Ya quedan definidos:

10 pasos
        ↓
Loop Engine
        ↓
Subloops
        ↓
Loops anidados
        ↓
Parallel Execution
        ↓
Priority
        ↓
Checkpoint
        ↓
Recovery
        ↓
Watchdog
        ↓
Failure Classification
        ↓
Repair / Fallback
        ↓
Dynamic Change
        ↓
DAG Versioning
        ↓
Chain Budget
        ↓
Final State

La siguiente parte será:

WORKFLOW — Salida 4/10

Hermes + Sentinel + Sheriff + Juez + Supervisor + Validador + Verificador

Ahí definiremos exactamente cómo Hermes inspecciona el objetivo, revisa arquitectura, supervisa agentes, detecta incumplimientos, genera correcciones DSL DAG y comunica el resultado a OpenClaw, sin convertirse en otro orquestador.

WORKFLOW — Salida 4/10

Hermes + Sentinel + Sheriff + Juez + Supervisor + Validador + Verificador

Esta salida fija a Hermes como sistema independiente de supervisión, no como segundo orquestador.

1. Posición de Hermes

WORKFLOW
                       │
                       ▼
                  DSL DAG
                       │
                       ▼
                   EJECUCIÓN
                       │
          ┌────────────┴────────────┐
          │                         │
          ▼                         ▼
       AGENTES                    HERMES
                                    │
              ┌─────────────────────┼─────────────────────┐
              ▼                     ▼                     ▼
          SENTINEL               JUEZ                SUPERVISOR
              │                     │                     │
              ▼                     ▼                     ▼
         DETECTA                  DECIDE              OBSERVA
              │                     │                     │
              └─────────────────────┼─────────────────────┘
                                    ▼
                               VALIDATOR
                                    │
                                    ▼
                                SHERIFF
                                    │
                         ┌──────────┴──────────┐
                         ▼                     ▼
                       PASS                  CHANGE
                                               │
                                               ▼
                                          CHANGE ENGINE
                                               │
                                               ▼
                                            DSL DAG

Hermes observa, analiza, verifica y propone acciones.

El Workflow conserva la autoridad para ejecutar esas acciones.


---

2. Hermes no ejecuta código

Hermes no debe convertirse en:

agente de programación

ni:

orquestador paralelo

Su función es:

OBSERVAR
ANALIZAR
COMPARAR
DETECTAR
VALIDAR
PROPONER
ESCALAR

La ejecución sigue perteneciendo al Workflow.


---

3. Los siete roles de Hermes

Hermes tendrá siete funciones lógicas:

1. SENTINEL
2. SHERIFF
3. JUDGE
4. SUPERVISOR
5. VALIDATOR
6. VERIFIER
7. REPORTER

No tienen que ser siete procesos independientes.

Pueden ser módulos dentro de Hermes.


---

4. Sentinel

El Sentinel observa continuamente:

Workflow
DAG
Tasks
Agents
Failures
Resources
Documents
Goals

Busca anomalías.

Ejemplos:

agente bloqueado
tarea sin progreso
contrato incumplido
documento contradictorio
agente trabajando fuera del scope
repetición
timeout
resultado incompleto

Produce:

SentinelEvent


---

5. Supervisor

El Supervisor analiza el estado general.

Pregunta:

¿El Workflow sigue avanzando hacia el objetivo?

Ejemplo:

Goal
 ↓
10 tareas
 ↓
7 completadas
 ↓
2 reparando
 ↓
1 bloqueada

Supervisor determina que el Workflow está:

PROGRESSING

Pero si:

Repair → mismo resultado
Repair → mismo resultado
Repair → mismo resultado

puede producir:

NO_PROGRESS


---

6. Verifier

El Verifier compara el resultado contra los objetivos.

Goal
 ↓
Requirements
 ↓
Implementation
 ↓
Evidence

No acepta:

> "El agente dice que está terminado."



Necesita evidencia.

Por ejemplo:

tests
files
commit
build
validation result
architecture compliance


---

7. Validator

El Validator comprueba condiciones específicas.

Ejemplo:

Backend Validator
├── syntax
├── dependencies
├── tests
├── API contract
├── security
└── architecture

Frontend:

Frontend Validator
├── build
├── routes
├── components
├── types
├── tests
└── architecture

El Validator genera un resultado estructurado.


---

8. Juez

El Juez recibe:

Goal
Architecture
Contract
Evidence
Validator
Verifier
Failures

Y determina:

PASS
FAIL
CHANGE_REQUIRED
BLOCKED
ESCALATE

El Juez no modifica el código.


---

9. Sheriff

El Sheriff hace cumplir las reglas.

Ejemplos:

¿Agente autorizado?
¿Repositorio correcto?
¿Skill obligatorio utilizado?
¿Source Mirror preparado?
¿Documento correcto?
¿Contrato cumplido?
¿Puede publicar?

Si no:

BLOCK


---

10. Diferencia entre Juez y Sheriff

Esto es importante.

Juez

Determina:

> ¿el resultado satisface el objetivo?



Sheriff

Determina:

> ¿la ejecución respetó las reglas?



Puede ocurrir:

Juez = PASS
Sheriff = BLOCK

Por ejemplo, el código funciona pero fue creado fuera del repositorio autorizado.

Entonces no puede publicarse.


---

11. Supervisor vs Sentinel

Sentinel

Detecta eventos.

"Algo está ocurriendo."

Supervisor

Interpreta el estado.

"Esto está provocando que el Workflow no avance."


---

12. Hermes recibe todo el contexto necesario

Hermes no debe recibir únicamente el último mensaje.

Su contexto será construido:

Context Builder
      │
      ├── Goal
      ├── Architecture
      ├── Documents
      ├── DAG
      ├── Memory
      ├── Skills
      ├── Agent history
      ├── Failures
      ├── Evidence
      └── Git history

Esto permite una supervisión real.


---

13. Hermes y OpenClaw

OpenClaw será la interfaz conversacional.

Ejemplo:

Usuario:
"¿Qué falta?"

OpenClaw consulta:

Hermes

Hermes responde estructuradamente:

STATUS
3 tareas completas
1 bloqueada
2 pendientes

PROBLEM
Backend authentication incomplete.

RECOMMENDATION
Architecture review required.

OpenClaw puede presentar eso al usuario.


---

14. Hermes puede generar una nueva tarea

Ejemplo:

Hermes detecta:

"La arquitectura actual no contempla
el nuevo requisito."

No modifica directamente el DAG.

Genera:

ChangeProposal


---

15. ChangeProposal

ChangeProposal
├── proposal_id
├── reason
├── source
├── affected_nodes
├── affected_documents
├── affected_goals
├── proposed_change
├── evidence
├── priority
└── required_validation

Después:

Hermes
 ↓
ChangeProposal
 ↓
Change Engine
 ↓
Impact Analysis
 ↓
DAG v2
 ↓
Sheriff
 ↓
Workflow


---

16. Esto permite incorporar documentos nuevos

Ejemplo:

PROJECT/
└── DOCUMENTS/
    └── NEW_REQUIREMENT.md

El sistema detecta:

NEW_DOCUMENT

Hermes analiza:

¿afecta objetivos?
¿afecta arquitectura?
¿afecta código?
¿afecta tests?

Después genera:

ChangeProposal

No reconstruye el Workflow.


---

17. Hermes puede recibir instrucciones de OpenClaw

Ejemplo:

OpenClaw:
"Hermes, revisa si la arquitectura actual
puede soportar WebSockets."

OpenClaw envía:

HermesRequest

Hermes consulta:

Documents
Memory
Architecture
Research
Repository

y produce:

ArchitectureAssessment

Si requiere trabajo:

ChangeProposal


---

18. Hermes → DSL DAG

Esta es una función que pediste específicamente.

Hermes no debería producir DAG arbitrario.

Debe producir una estructura validable:

Hermes
 ↓
DSL DAG Proposal
 ↓
Schema Validation
 ↓
Policy Validation
 ↓
Sheriff
 ↓
Workflow

Ejemplo conceptual:

CHANGE_ARCHITECTURE
      ↓
RESEARCH
      ↓
COUNCIL
      ↓
UPDATE_ARCHITECTURE
      ↓
REVALIDATE


---

19. El Sheriff valida el DSL

Antes de incorporarlo:

DSL
 ↓
Schema
 ↓
Policy
 ↓
Dependency validation
 ↓
Resource validation
 ↓
Sheriff

Si es válido:

ACCEPT

Si no:

REJECT


---

20. Hermes y loops

Hermes puede ordenar:

REPAIR LOOP

pero no ejecutarlo directamente.

Ejemplo:

Hermes:
"Se requieren tres fases adicionales."

        ↓

ChangeProposal

        ↓

Workflow

        ↓

DAG update

        ↓

Loop continues

Esto mantiene la separación.


---

21. Hermes puede solicitar Council

Cuando detecta una decisión arquitectónica compleja:

Hermes
 ↓
Architecture Council Request
 ↓
Council 12
 ↓
Proposal
 ↓
Hermes Review
 ↓
Sheriff
 ↓
Workflow

Esto permite que el sistema vuelva a analizar una arquitectura durante un proceso largo.


---

22. Hermes como sentinela de los dos grupos

Tendremos:

HERMES
                      │
          ┌───────────┴───────────┐
          ▼                       ▼
      FRONTEND                  BACKEND
          │                       │
       Agents                  Agents
          │                       │
       Sandbox                 Sandbox
          │                       │
       Validator              Validator
          └───────────┬───────────┘
                      ▼
                    HERMES

Hermes puede comparar ambos grupos contra el objetivo global.


---

23. Hermes no reemplaza los Validators

La separación:

AGENT
 ↓
VALIDATOR
 ↓
HERMES
 ↓
SHERIFF
 ↓
JUDGE

Cada uno tiene una función diferente.


---

24. Resultado formal de Hermes

Hermes producirá:

HermesReport
├── status
├── objective_status
├── architecture_status
├── requirements_status
├── execution_status
├── agent_status
├── validation_status
├── failures
├── missing_items
├── changes_required
├── evidence
└── recommendation


---

25. Lista de incumplimientos para OpenClaw

Cuando algo no se cumple:

Hermes
 ↓
MissingItems
 ↓
OpenClaw

Ejemplo:

FALTANTES

1. Falta validar endpoint X.
2. Falta actualizar ARCHITECTURE/API.md.
3. Falta ejecutar integración.
4. Falta verificar requisito R-17.
5. Commit aún no autorizado.

OpenClaw puede mostrarlo directamente.


---

26. Diagrama generado para OpenClaw

Hermes también puede producir una representación estructurada:

CURRENT
   ↓
BUILD
   ↓
FAIL
   ↓
REPAIR
   ↓
TEST
   ↓
PASS
   ↓
VERIFY

Si hay un problema:

BUILD
  ↓
FAIL
  ↓
RESEARCH
  ↓
ARCHITECTURE REVIEW
  ↓
REPAIR

OpenClaw puede convertir esta estructura en una visualización.


---

27. Seguridad de Hermes

Hermes tampoco tiene autoridad ilimitada.

Sus permisos serán:

READ:
    documents
    memory
    workflow
    logs
    evidence

PROPOSE:
    changes
    repairs
    architecture reviews
    DAG modifications

NO DIRECT:
    arbitrary code execution
    arbitrary repository writes
    arbitrary deployment

El Workflow decide si una propuesta se ejecuta.


---

28. Flujo completo de supervisión

AGENT
                       │
                       ▼
                   RESULT
                       │
                       ▼
                  VALIDATOR
                       │
                       ▼
                    HERMES
                       │
       ┌───────────────┼────────────────┐
       ▼               ▼                ▼
   SENTINEL        SUPERVISOR        VERIFIER
       │               │                │
       └───────────────┼────────────────┘
                       ▼
                      JUDGE
                       │
                       ▼
                    SHERIFF
                       │
                ┌──────┴──────┐
                ▼             ▼
              PASS          CHANGE
                              │
                              ▼
                        CHANGE ENGINE
                              │
                              ▼
                           DSL DAG
                              │
                              ▼
                           LOOP


---

29. Regla fundamental de Hermes

La arquitectura queda fijada así:

> Hermes puede detectar, analizar, verificar y proponer. El Workflow autoriza y ejecuta.



Esto evita que Hermes termine convirtiéndose en un segundo orquestador.


---

Estado del diseño después de la salida 4

Ya tenemos:

CONTROL KERNEL
      │
      ├── Goals
      ├── Policies
      ├── Contracts
      ├── Change Engine
      ├── Agent Registry
      ├── Memory Router
      ├── Execution Router
      └── State Manager
             │
             ▼
          DSL DAG
             │
             ▼
      LONG-RUNNING LOOP
             │
             ▼
           AGENTS
             │
             ▼
          VALIDATORS
             │
             ▼
           HERMES
        ┌────┼────┐
        ▼    ▼    ▼
    Sentinel Judge Supervisor
        │    │    │
        └────┼────┘
             ▼
          Sheriff
             │
       ┌─────┴─────┐
       ▼           ▼
     PASS        CHANGE
                   │
                   ▼
              Change Engine

La salida 5/10 será la capa de ejecución: Universal Harness + Agent Registry + adapters, incluyendo cómo hacer intercambiables Cline, OpenCode, OpenHands, Codex CLI, Claude Code CLI, Kimi Code CLI y Mimo Code sin modificar el núcleo del Workflow.



WORKFLOW — Salida 5/10

Universal Harness + Agent Registry + Agent Adapters

Esta capa resuelve uno de los problemas que señalaste: que los agentes sean intercambiables sin modificar el WORKFLOW.

La regla es:

> El WORKFLOW nunca programa contra Cline, OpenCode, OpenHands, Codex o Claude Code directamente. Programa contra una interfaz universal.




---

1. Arquitectura

WORKFLOW
                            │
                            ▼
                     AGENT REGISTRY
                            │
                            ▼
                    CAPABILITY ROUTER
                            │
                            ▼
                    UNIVERSAL HARNESS
                            │
             ┌──────────────┼──────────────┐
             ▼              ▼              ▼
        AGENT ADAPTER   AGENT ADAPTER   AGENT ADAPTER
             │              │              │
             ▼              ▼              ▼
          CLINE          OPENCODE       OPENHANDS
             │              │              │
             ▼              ▼              ▼
          SANDBOX        SANDBOX        SANDBOX

Los adapters son la pieza que absorbe las diferencias entre agentes.


---

2. Por qué necesitas un Adapter

Cada agente puede tener:

CLI diferente;

API diferente;

parámetros diferentes;

formato de salida diferente;

forma diferente de manejar archivos;

diferentes códigos de error;

diferentes capacidades.


El Workflow no debe conocer esas diferencias.

Ejemplo:

Workflow
   ↓
execute(capability="frontend_executor")

No:

Workflow
   ↓
cline --some-specific-command


---

3. Universal Harness

El Harness será el contrato común.

Conceptualmente:

UniversalHarness
├── prepare()
├── validate_input()
├── load_context()
├── load_skills()
├── load_source()
├── create_sandbox()
├── execute()
├── collect_output()
├── validate_output()
├── collect_evidence()
├── cleanup()
└── checkpoint()

El Harness no sabe cómo funciona internamente cada agente.


---

4. Flujo del Harness

Task
 ↓
prepare
 ↓
validate input
 ↓
context
 ↓
skills
 ↓
source mirror
 ↓
sandbox
 ↓
agent adapter
 ↓
execute
 ↓
collect output
 ↓
validator
 ↓
evidence
 ↓
checkpoint


---

5. Agent Registry

El Registry contiene las capacidades disponibles.

Ejemplo conceptual:

agents/
├── cline.yaml
├── opencode.yaml
├── openhands.yaml
├── codex.yaml
├── claude-code.yaml
├── kimi-code.yaml
└── mimo-code.yaml

Cada definición describe capacidades.


---

6. Capability, no nombre del agente

Esto es fundamental.

El Workflow pide:

frontend_executor

El Registry puede devolver:

Cline

Pero también:

OpenHands
OpenCode

si tienen esa capacidad.

Así puedes sustituir un agente sin modificar el DAG.


---

7. Registro conceptual

AgentDefinition
├── agent_id
├── name
├── version
├── capabilities
├── adapter
├── execution_mode
├── sandbox_profile
├── supported_inputs
├── supported_outputs
├── required_skills
├── resource_requirements
└── recovery_priority


---

8. Ejemplo Frontend

frontend_executor:
    primary: Cline

    recovery:
        - OpenHands
        - OpenCode
        - Codex
        - KimiCode
        - MimoCode

Esto coincide con el grupo que fijaste.

El Workflow no tiene que saber cómo se ejecuta Cline.


---

9. Ejemplo Backend

backend_executor:
    primary: OpenCode

    recovery:
        - OpenHands
        - Codex
        - ClaudeCode

La cadena queda configurada como política.


---

10. Cambio automático de agente

Ejemplo:

Cline
 ↓
Validator
 ↓
FAIL
 ↓
FailureClassifier
 ↓
RecoveryPolicy
 ↓
OpenHands

Si vuelve a fallar:

OpenHands
 ↓
Validator
 ↓
FAIL
 ↓
OpenCode

El cambio es determinista porque está definido en la política.


---

11. No se necesitan "3 intentos"

El sistema anterior de intentos rígidos queda sustituido por:

Failure Policy

La transición depende del tipo de fallo.

Por ejemplo:

TEST_FAILURE
    → repair

TOOL_FAILURE
    → retry

AGENT_CRASH
    → change_agent

ARCHITECTURE_FAILURE
    → architecture_review

SOURCE_MISSING
    → research

SKILL_MISSING
    → skill_resolution

Esto es mucho más robusto que:

intento 1
intento 2
intento 3


---

12. Agent Adapter

Cada agente tendrá un adapter.

adapters/
├── cline_adapter
├── opencode_adapter
├── openhands_adapter
├── codex_adapter
├── claude_code_adapter
├── kimi_code_adapter
└── mimo_code_adapter

Todos implementan el mismo contrato.


---

13. Contrato del Adapter

Conceptualmente:

AgentAdapter
├── health()
├── prepare()
├── execute()
├── stop()
├── collect_result()
└── normalize_error()

Por ejemplo:

OpenCodeAdapter

convierte la interfaz específica de OpenCode al formato universal.


---

14. Resultado normalizado

Aunque los agentes produzcan salidas diferentes:

AgentResult
├── status
├── task_id
├── agent_id
├── files_changed
├── artifacts
├── tests
├── logs_reference
├── evidence
└── failure

El resto del Workflow solo trabaja con AgentResult.


---

15. Esto permite cambiar de agente

Supongamos:

frontend_executor

hoy:

Cline

mañana:

otro agente

Solo cambias:

Agent Registry

El DAG permanece igual.

El Harness permanece igual.

Hermes permanece igual.

Sheriff permanece igual.


---

16. Agentes con UI y sin UI

Esto también resuelve tu pregunta sobre OpenClaw/Hermes y agentes con diferentes interfaces.

El Adapter puede soportar:

CLI
API
HTTP
local process
container
remote worker

Por ejemplo:

Agent Adapter
      │
      ├── CLI Adapter
      ├── HTTP Adapter
      ├── API Adapter
      └── Container Adapter

El Harness permanece idéntico.


---

17. OpenClaw

OpenClaw debe tratarse como una interfaz/origen de comandos, no como un agente ejecutor obligatorio.

Usuario
  ↓
OpenClaw
  ↓
Workflow API

Puede enviar:

Goal
CouncilRequest
StatusRequest
ResearchRequest
ChangeRequest


---

18. Hermes

Hermes funciona como componente de supervisión:

Workflow
  ↓
Hermes

y puede producir:

ChangeProposal
ArchitectureReview
VerificationResult
FailureAnalysis

El Workflow decide qué ejecutar.


---

19. Agentes independientes por grupo

Puedes mantener:

FRONTEND
│
├── Cline
├── OpenHands
├── OpenCode
├── Codex
├── Kimi Code
└── Mimo Code

y:

BACKEND
│
├── OpenCode
├── OpenHands
├── Codex
└── Claude Code

Pero no necesitas instalar dos copias del mismo agente.

El mismo Agent Adapter puede ser utilizado por ambos grupos.


---

20. Misma instancia, tareas diferentes

Conceptualmente:

OpenCode
                /        \
               /          \
        Backend Task    Frontend Task
             │                │
             ▼                ▼
        Backend Sandbox   Frontend Sandbox

El agente puede ser el mismo.

Lo que cambia es:

Task
Repository
Sandbox
Context
Skills
Permissions
Policy


---

21. Aislamiento

Aunque el agente sea compartido, las ejecuciones no deben compartir arbitrariamente el entorno de trabajo.

OpenCode
   │
   ├── Backend Sandbox
   │
   └── Frontend Sandbox

Esto evita que una tarea toque accidentalmente los archivos de otra.


---

22. Agent Pool

Para agentes reutilizables:

AgentPool
├── available
├── running
├── unavailable
├── failed
└── cooldown

El Scheduler solicita:

capability = backend_executor

El Pool encuentra una instancia disponible.


---

23. Resource-aware routing

El Registry puede considerar:

RAM
CPU
GPU
API availability
cost
latency
agent health
current workload

Ejemplo:

OpenHands
RAM requirement = high

Si no existe suficiente RAM:

OpenHands
   ↓
UNAVAILABLE
   ↓
next compatible agent

Esto conecta directamente con tu arquitectura de múltiples HF Spaces.


---

24. HF Spaces

Los agentes pesados pueden ejecutarse remotamente:

WORKFLOW
   ↓
Execution Router
   ↓
HF Worker
   ↓
Universal Harness
   ↓
Agent

Mientras el Control Kernel permanece ligero.


---

25. No necesitas mover el Workflow

Puedes tener:

HF1
Control / Memory

HF2
Frontend Agents

HF3
Backend Agents

y:

Workflow
   ↓
Execution Router

elige el entorno.


---

26. Contrato de ejecución remoto

El Workflow envía:

ExecutionRequest
├── task
├── context
├── documents
├── skills
├── source_refs
├── repository
├── sandbox_policy
├── timeout
├── budget
└── contract

El worker devuelve:

ExecutionResult
├── status
├── artifacts
├── changed_files
├── evidence
├── logs
└── failure

El Workflow no necesita saber dónde se ejecutó.


---

27. Seguridad

Cada Adapter debe operar bajo un ExecutionContract.

Agent
 ↓
Harness
 ↓
Contract
 ↓
Sandbox

El agente no recibe directamente:

GitHub token
Database credentials
Memory credentials
Deployment credentials

Esos secretos deben permanecer detrás de servicios controlados.


---

28. Agent Health

Antes de seleccionar un agente:

health()

Comprueba:

available
authenticated
compatible
resource_available
adapter_valid

Si falla:

Registry
 ↓
next candidate


---

29. El agente puede ser completamente sustituible

La arquitectura final:

WORKFLOW
                       │
                       ▼
                CAPABILITY
                       │
                       ▼
                AGENT REGISTRY
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
        Candidate A          Candidate B
             │                   │
             └─────────┬─────────┘
                       ▼
                 UNIVERSAL
                   HARNESS
                       │
                       ▼
                    SANDBOX
                       │
                       ▼
                    AGENT

Cambiar el agente no cambia el Workflow.


---

30. Regla de oro del Harness

El Harness será la frontera entre el mundo determinista y los agentes probabilísticos.

DETERMINISTA
────────────────────────
Workflow
DAG
Contracts
Policy
Sheriff
State
Budget
────────────────────────
       HARNESS
────────────────────────
Agent
LLM
CLI
API

Todo lo que está arriba tiene reglas estrictas.

Todo lo que está debajo puede ser reemplazado.


---

31. Resultado de esta salida

Queda definida la cadena:

Workflow
   ↓
Capability Router
   ↓
Agent Registry
   ↓
Universal Harness
   ↓
Agent Adapter
   ↓
Sandbox
   ↓
Agent
   ↓
Normalized Result
   ↓
Validator
   ↓
Hermes

Y los grupos que fijaste quedan:

Backend

OpenCode
   ↓
OpenHands
   ↓
Codex CLI
   ↓
Claude Code CLI

Frontend

Cline
   ↓
OpenHands
   ↓
OpenCode
   ↓
Codex CLI
   ↓
Kimi Code CLI
   ↓
Mimo Code

La diferencia importante es que ahora estas cadenas no están incrustadas en el código del Workflow: son políticas configurables del Agent Registry.


---

Siguiente: WORKFLOW — Salida 6/10

Memoria persistente + Graphiti + GraphRAG + Graphify + Vector DB + documentos del proyecto + anclajes + Context Builder + Memory Router + caché.

Ahí definiremos cómo conectar la memoria con los agentes sin permitir que cada agente acceda directamente a las bases de memoria, y cómo anclar:

PROJECT/
├── README.md
├── METHOD.md
├── HANDOFF.md
├── ARCHITECTURE/
├── PIPELINE/
├── DESIGN/
├── REQUIREMENTS/
├── BACKEND/
├── FRONTEND/
├── DECISIONS/
└── DOCUMENTS/

al sistema de memoria y al Workflow.
WORKFLOW — Salida 6/10

Memoria persistente + Graphiti + GraphRAG + Graphify + documentos + caché

Esta capa será el sistema de conocimiento persistente del WORKFLOW.

La regla arquitectónica principal se mantiene:

> Los agentes no hablan directamente con Graphiti, GraphRAG, Graphify ni las bases de datos. El WORKFLOW controla el acceso mediante un Memory Router.




---

1. Arquitectura general

OPENCLAW
                            │
                            ▼
                       WORKFLOW
                            │
                     MEMORY ROUTER
                            │
                  ┌─────────┼─────────┐
                  ▼         ▼         ▼
             CACHE       CONTEXT    MEMORY
                         BUILDER     ADAPTER
                                       │
                    ┌──────────────────┼─────────────────┐
                    ▼                  ▼                 ▼
                 GRAPHITI          GRAPHRAG          GRAPHIFY
                    │                  │                 │
                    └──────────────────┼─────────────────┘
                                       ▼
                              PERSISTENT STORAGE
                                       │
                    ┌──────────────────┼──────────────────┐
                    ▼                  ▼                  ▼
                 GRAPH DB          VECTOR DB          SQL/OBJECT

La arquitectura queda preparada para reemplazar cualquiera de esos componentes.


---

2. Memory Router

El Workflow nunca hace:

Agent → Graphiti

Hace:

Agent
 ↓
Context Request
 ↓
Memory Router
 ↓
Memory Adapter
 ↓
Graphiti / GraphRAG / Graphify / otro

Esto permite cambiar el sistema de memoria sin modificar los agentes.


---

3. Memory Adapter

El Adapter proporciona una interfaz común:

MemoryAdapter
├── search()
├── retrieve()
├── store()
├── update()
├── link()
├── get_context()
├── create_anchor()
└── health()

Puedes tener:

GraphitiAdapter
GraphRAGAdapter
GraphifyAdapter
VectorAdapter
SQLMemoryAdapter


---

4. Memoria híbrida

No recomiendo utilizar una sola base para todo.

El sistema puede dividir la información:

MEMORY
                   │
       ┌───────────┼───────────┐
       ▼           ▼           ▼
   GRAPH        VECTOR       RELATIONAL
       │           │           │
relationships   similarity    state
entities        embeddings    metadata
history         documents     transactions

Cada una resuelve un problema diferente.


---

5. Graphiti

Graphiti puede utilizarse para representar conocimiento temporal y relaciones.

Ejemplo:

PROJECT
  │
  ├── has_requirement → R-17
  ├── uses → PostgreSQL
  ├── contains → Backend
  └── depends_on → Service X

Y temporalmente:

Architecture v1
       ↓
Change
       ↓
Architecture v2

Esto es especialmente útil para saber cómo evolucionó el proyecto.


---

6. GraphRAG

GraphRAG será una estrategia de recuperación de información.

No significa que tenga que ser una base independiente obligatoria.

Su función:

Pregunta
 ↓
Search
 ↓
Graph relationships
 +
Vector similarity
 +
Documents
 ↓
Context

Esto permite responder preguntas que requieren relaciones entre documentos.


---

7. Graphify

En tu arquitectura, Graphify debe tratarse como otro adaptador o fuente de conocimiento, no como una dependencia rígida del núcleo.

Memory Router
      │
      ├── Graphiti
      ├── Graphify
      ├── GraphRAG
      └── Other

Si posteriormente cambias Graphify por otro sistema:

GraphifyAdapter
       ↓
NewMemoryAdapter

El Workflow permanece igual.


---

8. Memoria persistente

La memoria importante no puede depender de:

RAM
cache
sandbox
agente

Debe existir almacenamiento persistente.

MEMORY ENGINE
                    │
                    ▼
              PERSISTENT DB
                    │
       ┌────────────┼────────────┐
       ▼            ▼            ▼
    Graph         Vector       SQL

Si un servidor cae:

SERVER DOWN
     ↓
SERVER RESTART
     ↓
MEMORY ENGINE
     ↓
RECOVER


---

9. El caché es diferente de la memoria

No debemos confundirlos.

Memoria

Persistente:

decisiones
arquitectura
documentos
historial
relaciones
evidencia

Caché

Temporal:

contextos frecuentes
embeddings frecuentes
resultados de búsqueda
documentos recientes
respuestas repetidas

Si el caché desaparece:

NO se pierde conocimiento.


---

10. Arquitectura del caché

MEMORY ROUTER
                  │
                  ▼
                CACHE
             ┌────┴────┐
             ▼         ▼
       Context Cache Search Cache
             │         │
             └────┬────┘
                  ▼
             Persistent DB

Redis es una opción posible, pero el Workflow debe hablar con un CacheAdapter, no directamente con Redis.


---

11. Context Builder

Este componente será crítico para tu idea de contexto muy grande.

El agente no recibe 10 millones de tokens directamente.

Eso sería ineficiente aunque el modelo pudiera soportarlo.

En cambio:

10M+ información almacenada
          ↓
      Memory Search
          ↓
      Relevance
          ↓
      Context Builder
          ↓
   contexto necesario
          ↓
        AGENT

La memoria puede contener enormes cantidades de información.

El contexto enviado al modelo debe ser selectivo.


---

12. Context Request

Cuando OpenCode necesita información:

ContextRequest
├── project
├── task
├── goal
├── node
├── required_documents
├── entities
├── relationships
├── code_scope
├── memory_scope
└── token_budget

El Memory Router ejecuta la búsqueda.


---

13. Context Builder

Construye:

Context
├── system constraints
├── task
├── relevant documents
├── architecture
├── decisions
├── source references
├── previous attempts
├── failures
├── required skills
└── evidence

Y elimina información irrelevante.


---

14. Documentos del proyecto

Tu estructura queda como fuente de autoridad:

PROJECT/
│
├── README.md
├── METHOD.md
├── HANDOFF.md
│
├── ARCHITECTURE/
├── PIPELINE/
├── DESIGN/
├── REQUIREMENTS/
├── BACKEND/
├── FRONTEND/
├── DECISIONS/
└── DOCUMENTS/

No todos los documentos tienen el mismo nivel de autoridad.


---

15. Jerarquía documental

Podemos definir:

LEVEL 0
SYSTEM POLICIES

LEVEL 1
PROJECT METHOD

LEVEL 2
ARCHITECTURE

LEVEL 3
REQUIREMENTS

LEVEL 4
DESIGN

LEVEL 5
IMPLEMENTATION

LEVEL 6
DOCUMENTS / NOTES

LEVEL 7
AGENT OUTPUT

Esto evita que una nota de un agente pueda invalidar accidentalmente una decisión arquitectónica formal.


---

16. Document Anchor

Cada documento recibe un identificador estable:

document_id
project_id
path
version
hash
type
authority
created_at
updated_at

Por ejemplo:

ARCHITECTURE/API.md
version = 7
hash = ...
authority = ARCHITECTURE


---

17. Anchor

El concepto de Anchor conecta una pieza de información con el proyecto.

Ejemplo:

Goal G-17
   │
   ├── Document D-41
   ├── Architecture A-08
   ├── Decision DEC-12
   ├── Code files
   ├── Agent executions
   └── Evidence E-93

Esto permite reconstruir por qué una decisión terminó afectando determinado código.


---

18. Graphiti + documentos

Un documento no se guarda simplemente como texto.

Se pueden representar relaciones:

METHOD.md
   │
   ├── defines → Workflow Method
   │
   └── governs → Architecture

Architecture/API.md
   │
   ├── implements → Requirement R17
   └── affects → backend/auth

Eso es mucho más útil que una simple carpeta de archivos.


---

19. GitHub como memoria adicional

Como ya estableciste:

GitHub

puede funcionar como memoria histórica y fuente de auditoría, pero no debe reemplazar la base de memoria operacional.

GitHub conserva:

commits
branches
PRs
issues
documents
source
history

Mientras Memory Engine conserva:

relationships
context
events
knowledge
anchors
execution history


---

20. Repository Mirror

Los repositorios Open Source investigados tendrán una representación aislada:

SOURCE_MIRROR/
│
├── backend/
│   ├── repo-001/
│   ├── repo-002/
│   └── ...
│
└── frontend/
    ├── repo-001/
    ├── repo-002/
    └── ...

El agente trabaja con esa fuente autorizada.

No tiene que inventar una solución desde cero cuando existe código reutilizable apropiado.


---

21. Relación Source Mirror ↔ Memory

El Memory Engine almacena:

repository
commit
version
license
source_path
selected_files
reason_selected
architecture

Por tanto:

Research
   ↓
Source Mirror
   ↓
Memory Anchor
   ↓
Agent Context


---

22. Skills también quedan anclados

Cada Skill tendrá:

skill_id
name
version
source
category
rules
documents
dependencies

Y:

Task
 ↓
required_skill
 ↓
Skill Resolver
 ↓
Memory

El agente recibe el Skill obligatorio antes de ejecutar.


---

23. Historial de ejecución

Cada ejecución genera eventos:

WorkflowStarted
NodeStarted
AgentStarted
AgentCompleted
ValidationStarted
ValidationFailed
RepairStarted
AgentChanged
CheckpointCreated
DocumentChanged
WorkflowResumed
WorkflowCompleted

Estos eventos pueden almacenarse persistentemente.


---

24. Event Store

EVENT STORE
     │
     ├── Workflow events
     ├── Agent events
     ├── Memory events
     ├── Git events
     ├── Validation events
     └── Hermes events

Esto es fundamental para recuperar un Workflow largo.


---

25. Memoria + Long Loop

La integración queda:

LONG LOOP
   │
   ├── Checkpoint
   │
   ├── State
   │
   ├── Memory Anchor
   │
   └── Evidence

Si el proceso se reinicia:

Checkpoint
 ↓
Memory Anchors
 ↓
Documents
 ↓
Events
 ↓
Context Builder
 ↓
Agent

El contexto se reconstruye.


---

26. Recuperación inteligente

No queremos restaurar todo el contexto histórico.

El Recovery Engine pide:

¿Qué necesito para continuar desde Node X?

Memory Router busca:

último checkpoint
+
objetivo
+
documentos afectados
+
decisiones
+
errores anteriores
+
cambios

Eso produce un contexto compacto.


---

27. Memoria de fallos

Los fallos también se almacenan.

Ejemplo:

Failure F-104
   │
   ├── agent = OpenCode
   ├── task = auth
   ├── error = test failure
   ├── attempt = ...
   └── repair = ...

Si vuelve a aparecer un problema similar:

Memory Search
 ↓
Failure F-104
 ↓
Context
 ↓
Repair Strategy

Esto evita repetir errores.


---

28. Memoria de decisiones

También se guardan las decisiones arquitectónicas:

DEC-001
¿Por qué se eligió X?

DEC-002
¿Por qué se rechazó Y?

DEC-003
¿Qué cambió en v2?

Esto es particularmente útil para Architecture Council y Hermes.


---

29. Memoria intercambiable

La arquitectura final:

MEMORY ROUTER
                       │
        ┌──────────────┼───────────────┐
        ▼              ▼               ▼
   GraphitiAdapter GraphRAGAdapter GraphifyAdapter
        │              │               │
        └──────────────┼───────────────┘
                       ▼
                Persistent Storage

Puedes añadir:

Neo4j
Qdrant
Weaviate
PostgreSQL
otro sistema

sin modificar los agentes.


---

30. Anclaje completo

La estructura más importante queda:

PROJECT
                    │
                    ▼
                DOCUMENTS
                    │
                    ▼
                  MEMORY
                    │
        ┌───────────┼────────────┐
        ▼           ▼            ▼
      GOALS      DECISIONS     HISTORY
        │           │            │
        └───────────┼────────────┘
                    ▼
                 CONTEXT
                    │
                    ▼
                  AGENT
                    │
                    ▼
                 RESULT
                    │
                    ▼
                EVIDENCE
                    │
                    ▼
                 MEMORY

Es un ciclo de conocimiento persistente.


---

31. El principio de seguridad

Los agentes reciben:

Context

no:

DATABASE CREDENTIALS

El agente tampoco puede:

borrar memoria arbitrariamente

Las operaciones pasan por:

Memory Router
 ↓
Memory Contract
 ↓
Sheriff


---

32. Arquitectura completa hasta ahora

OPENCLAW
                            │
                            ▼
                    CONTROL KERNEL
                            │
       ┌────────────────────┼───────────────────┐
       ▼                    ▼                   ▼
     GOALS               POLICIES           CONTRACTS
       │                    │                   │
       └────────────────────┼───────────────────┘
                            ▼
                    ARCHITECTURE COUNCIL
                            │
                            ▼
                         DSL DAG
                            │
                            ▼
                   LONG-RUNNING LOOP
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
          MEMORY         AGENTS       CHECKPOINT
              │             │             │
              ▼             ▼             │
        MEMORY ROUTER    HARNESS           │
              │             │              │
      ┌───────┼───────┐     ▼              │
      ▼       ▼       ▼  SANDBOX           │
   Graphiti GraphRAG Graphify               │
      │       │       │                     │
      └───────┼───────┘                     │
              ▼                             │
         PERSISTENT DB ◄────────────────────┘


---

Resultado de la salida 6

Ahora el sistema tiene:

memoria persistente;

memoria temporal/caché separada;

Graphiti intercambiable;

GraphRAG intercambiable;

Graphify intercambiable;

documentos anclados;

Source Mirror anclado;

Skills anclados;

historial de ejecución;

memoria de fallos;

memoria de decisiones;

recuperación basada en checkpoints;

Context Builder;

Memory Router.


Y, sobre todo:

> La memoria no pertenece a ningún agente. Pertenece al sistema WORKFLOW y los agentes reciben contexto controlado.



Siguiente — Salida 7/10

Research Engine + Open Source Repository Research + Source Mirror + descarga obligatoria del código + Skills obligatorios + contratos Sheriff + cómo investigar múltiples repositorios Backend/Frontend y convertirlos en fuentes utilizables por los agentes.

WORKFLOW — Salida 7/10

Research Engine + Repository Intelligence + Source Mirror + Skills

Esta salida implementa la parte que definiste como obligatoria: antes de construir desde cero, el sistema debe investigar soluciones existentes, localizar repositorios Open Source relevantes, evaluarlos, descargarlos a un espejo aislado y entregarlos como fuente de trabajo a los agentes.

La regla será:

> Ningún agente puede comenzar una implementación cuando el Workflow determine que existe una fase de investigación obligatoria sin completar.




---

1. Arquitectura

WORKFLOW
                       │
                       ▼
                RESEARCH ENGINE
                       │
             ┌─────────┼─────────┐
             ▼         ▼         ▼
          SEARCH     ANALYZE   COMPARE
             │         │         │
             └─────────┼─────────┘
                       ▼
                 REPOSITORY
                  CANDIDATES
                       │
                       ▼
                SHERIFF CHECK
                       │
                       ▼
                 SOURCE MIRROR
                       │
                       ▼
                MEMORY ANCHOR
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
        SKILL RESOLVER      ARCHITECTURE
             │                   │
             └─────────┬─────────┘
                       ▼
                    HARNESS
                       │
                       ▼
                    AGENT


---

2. Research Engine

El Research Engine no es un agente de programación.

Es una capacidad del Workflow dedicada a:

SEARCH
DISCOVER
FILTER
COMPARE
VERIFY
MIRROR
INDEX
ANCHOR

Su salida no es código final.

Su salida es:

ResearchPackage


---

3. ResearchPackage

Cada investigación produce:

ResearchPackage
├── research_id
├── objective
├── query_set
├── candidates
├── selected_repositories
├── rejected_repositories
├── comparison
├── license_information
├── technology_stack
├── architecture_notes
├── reusable_components
├── risks
├── source_mirror_refs
├── skills
├── evidence
└── recommendation


---

4. Investigación mínima

Tu requisito de mínimo 20 investigaciones se convierte en una política configurable.

Por ejemplo:

research_policy:
    minimum_candidates: 20

No significa que obligatoriamente debamos usar 20 repositorios.

Significa:

20 candidatos investigados
        ↓
evaluación
        ↓
selección
        ↓
repositorios realmente útiles

Esto es mucho mejor que descargar 20 repositorios indiscriminadamente.


---

5. Investigación separada por grupo

Backend

BACKEND RESEARCH
├── frameworks
├── APIs
├── databases
├── authentication
├── queues
├── workers
├── orchestration
├── observability
├── testing
├── security
└── infrastructure

Frontend

FRONTEND RESEARCH
├── UI frameworks
├── components
├── state management
├── routing
├── PWA
├── accessibility
├── testing
├── animations
├── forms
├── design systems
└── performance

El Workflow decide qué categorías son relevantes para el proyecto.


---

6. Research Council

La investigación puede pasar por el Architecture Council.

Research Engine
      ↓
Candidates
      ↓
Architecture Council
      ↓
Evaluation
      ↓
Selection

El Council responde:

¿sirve?
¿es compatible?
¿qué partes podemos reutilizar?
¿qué riesgos tiene?
¿qué dependencias introduce?
¿es mejor que construirlo nosotros?


---

7. No copiar automáticamente

Encontrar un repositorio no significa incorporarlo.

Debe pasar:

DISCOVER
   ↓
VERIFY
   ↓
LICENSE
   ↓
QUALITY
   ↓
COMPATIBILITY
   ↓
SECURITY
   ↓
ARCHITECTURE
   ↓
SHERIFF

Solo después:

APPROVED


---

8. Source Mirror

Los repositorios seleccionados se descargan a un área aislada.

SOURCE_MIRROR/
│
├── BACKEND/
│   ├── research-001/
│   ├── research-002/
│   └── ...
│
└── FRONTEND/
    ├── research-001/
    ├── research-002/
    └── ...

Cada repositorio mantiene su identidad y versión.


---

9. Nunca mezclar fuentes

Cada mirror tendrá:

repo/
├── source/
├── metadata/
├── evidence/
├── analysis/
└── manifest.json

Esto permite saber:

¿de dónde salió este archivo?
¿qué commit tenía?
¿por qué se seleccionó?
¿qué licencia tiene?
¿quién lo autorizó?


---

10. Versionado obligatorio

No se guarda simplemente:

latest

Se registra:

repository
branch
commit
tag
release
hash
timestamp

Así el agente trabaja sobre una fuente reproducible.


---

11. Manifest

Cada mirror tendrá un manifiesto conceptual:

SourceManifest
├── source_id
├── repository
├── commit
├── branch
├── license
├── language
├── dependencies
├── selected_for
├── approved_by
├── research_id
└── integrity_hash


---

12. Integridad

Antes de entregar la fuente al agente:

DOWNLOAD
   ↓
HASH
   ↓
VERIFY
   ↓
REGISTER
   ↓
ANCHOR

Si la fuente cambia:

HASH MISMATCH

el Sheriff bloquea su utilización.


---

13. Source Selection

El agente no recibe necesariamente todo el repositorio.

El Workflow puede seleccionar:

repository
 ↓
relevant modules
 ↓
relevant files
 ↓
Context Builder
 ↓
Agent

Pero el mirror completo permanece disponible para estudio y trazabilidad cuando la política lo permita.


---

14. Tu requisito de estudiar el código

Aquí se conserva exactamente la idea que planteaste.

El repositorio completo puede quedar almacenado en:

SOURCE_MIRROR

para:

estudio
comparación
análisis
referencia
arquitectura

Mientras el agente recibe solamente el subconjunto necesario para su tarea.


---

15. Research Memory

La investigación se ancla en memoria:

Research R-100
       │
       ├── Candidate Repo A
       ├── Candidate Repo B
       ├── Candidate Repo C
       │
       ├── Selected Repo X
       │
       ├── Decision
       └── Evidence

Así puedes preguntar posteriormente:

> ¿Por qué utilizamos este proyecto?



Y reconstruir la decisión.


---

16. Reutilización futura

Si dentro de seis meses aparece una tarea similar:

NEW TASK
   ↓
MEMORY SEARCH
   ↓
Previous Research
   ↓
Existing Source Mirror

No necesariamente hay que repetir la investigación.

Solo se vuelve a investigar si:

version obsolete
security issue
requirements changed
compatibility changed
policy expired


---

17. Research TTL

Cada investigación puede tener una vigencia:

research_ttl

Ejemplo:

VALID
EXPIRED
INVALIDATED

Si cambia una dependencia crítica:

Research
   ↓
INVALIDATED
   ↓
Research Engine


---

18. Skills obligatorios

El Workflow tendrá un Skill Resolver.

Task
 ↓
Required Capabilities
 ↓
Skill Resolver
 ↓
Skills
 ↓
Harness
 ↓
Agent

El agente no puede avanzar si un Skill obligatorio falta.


---

19. Skill Contract

Cada Skill tiene contrato:

SkillContract
├── skill_id
├── version
├── purpose
├── prerequisites
├── allowed_tasks
├── required_tools
├── validation
└── evidence


---

20. Skill Registry

SKILLS/
│
├── backend/
├── frontend/
├── architecture/
├── testing/
├── security/
├── research/
├── github/
└── deployment/

El sistema puede incorporar nuevos Skills sin reconstruir el Workflow.


---

21. Skill dinámico

Si Hermes detecta:

TASK
requiere skill que no existe

genera:

SkillRequest

Luego:

Research
 ↓
Skill candidate
 ↓
Validation
 ↓
Sheriff
 ↓
Skill Registry

El nuevo Skill queda disponible para futuros loops.


---

22. Research Sheriff

Toda investigación pasa por Sheriff.

El Sheriff verifica:

source allowed
repository valid
license recorded
commit recorded
integrity verified
scope correct
mirror isolated
research evidence present

Si falta algo:

BLOCK


---

23. Research Contract

El contrato puede exigir:

RESEARCH_REQUIRED
MINIMUM_CANDIDATES
LICENSE_CHECK
VERSION_PINNED
SOURCE_MIRROR_REQUIRED
INTEGRITY_CHECK_REQUIRED
ARCHITECTURE_REVIEW_REQUIRED
SKILL_REVIEW_REQUIRED

Por tanto, el agente no puede saltarse la investigación simplemente porque "ya sabe cómo hacerlo".


---

24. Repository Evidence

Cada repositorio evaluado tendrá evidencia:

RepositoryEvidence
├── repository
├── version
├── license
├── activity
├── architecture
├── dependencies
├── tests
├── documentation
├── security
├── compatibility
└── recommendation


---

25. Comparación determinista

Los candidatos pueden evaluarse mediante una matriz:

Repo A   Repo B   Repo C
Architecture       8        9        6
Tests              9        7        5
Compatibility      8        9        7
Security            8        8        6
Maintenance         9        7        5
Documentation       8        9        6

El modelo puede ayudar a analizar.

Pero la política de aceptación queda determinada por reglas.


---

26. Separación modelo / decisión

El agente puede decir:

> Repo B parece mejor.



Pero el Workflow aplica:

if license_invalid:
    reject

if compatibility < threshold:
    reject

if integrity_failed:
    reject

Esto mantiene el sistema determinista.


---

27. Investigación paralela

Las investigaciones independientes pueden ejecutarse en paralelo:

RESEARCH
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
    Research A   Research B   Research C
        │            │            │
        └────────────┼────────────┘
                     ▼
                  MERGE
                     │
                  COUNCIL

Esto reduce mucho el tiempo total.


---

28. Research Checkpoint

Cada investigación crea checkpoint:

ResearchStarted
CandidateFound
CandidateEvaluated
RepositoryVerified
MirrorCreated
RepositoryApproved
ResearchCompleted

Si el proceso muere:

RESTART
   ↓
CHECKPOINT
   ↓
resume from last completed research

No empieza desde cero.


---

29. Investigación durante el loop

La investigación no tiene que existir solamente al principio.

Puede aparecer dinámicamente:

Agent
 ↓
Task
 ↓
Missing capability
 ↓
Research Request
 ↓
Research Engine
 ↓
Source Mirror
 ↓
Skill
 ↓
Agent resumes

Esto conecta directamente con tu requisito de loops adaptables.


---

30. Hermes + Research

Hermes puede detectar:

"El agente está intentando construir
una solución que podría reutilizar
una tecnología existente."

Entonces:

Hermes
 ↓
ResearchProposal
 ↓
Workflow
 ↓
Research Engine

No fuerza directamente la investigación.

La incorpora al Workflow mediante una propuesta validable.


---

31. Research + Architecture Council

Research
   ↓
20+ candidates
   ↓
Filtering
   ↓
Architecture Council
   ↓
Selected technologies
   ↓
Sheriff
   ↓
Source Mirror
   ↓
Agent

Esto convierte la investigación en parte formal del proceso arquitectónico.


---

32. Flujo completo de una tarea nueva

NEW TASK
   │
   ▼
GOAL ANALYSIS
   │
   ▼
RESEARCH REQUIRED?
   │
   ├── NO ────────────────┐
   │                      │
   └── YES                │
       │                  │
       ▼                  │
   RESEARCH               │
       │                  │
       ▼                  │
   SOURCE MIRROR          │
       │                  │
       ▼                  │
   SKILLS                 │
       │                  │
       └────────┬─────────┘
                ▼
          ARCHITECTURE
                │
                ▼
              AGENT
                │
                ▼
            VALIDATOR
                │
                ▼
             HERMES


---

33. Lo importante

Con esta capa el sistema deja de funcionar como:

problema
 ↓
LLM
 ↓
código desde cero

y pasa a:

problema
 ↓
investigación
 ↓
conocimiento existente
 ↓
repositorios
 ↓
source mirror
 ↓
skills
 ↓
arquitectura
 ↓
agente
 ↓
validación

Eso reduce la cantidad de código que los agentes tienen que inventar.


---

34. Resultado de la salida 7

Quedan integrados:

Research Engine.

Investigación Backend/Frontend.

mínimo configurable de 20 candidatos.

Repository Intelligence.

Source Mirror.

versionado por commit.

integridad mediante hash.

licencia y compatibilidad.

Architecture Council.

Research Sheriff.

Research Contract.

Skill Registry.

Skill Resolver.

Skills obligatorios.

investigación paralela.

checkpoints.

investigación dinámica durante el loop.

Hermes como detector de necesidad de investigación.

memoria de investigaciones.

reutilización de investigaciones anteriores.


Y la cadena queda:

RESEARCH
   ↓
VERIFY
   ↓
MIRROR
   ↓
ANCHOR
   ↓
SKILL
   ↓
ARCHITECTURE
   ↓
HARNESS
   ↓
AGENT

Siguiente — Salida 8/10: la parte de Long Loop Engine: los 10 pasos del loop, Architecture Council de 12, Goals de entrada/salida, prioridades, paralelismo, checkpoints, watchdog, recuperación después de reinicio/corte de API, reparación múltiple y cómo incorporar cambios/documentos nuevos sin reconstruir el Workflow.


WORKFLOW — Salida 8/10

Long Loop Engine + recuperación + prioridades + cambios dinámicos

Esta es la pieza que convierte el sistema anterior en un Workflow de ejecución prolongada, sin hacer que la Control Layer se convierta en un segundo orquestador pesado.

La idea central:

> El loop no está construido como una secuencia rígida de agentes. Está construido como un ciclo determinista de estados, contratos, checkpoints y decisiones.




---

1. Loop principal de 10 pasos

01 INPUT / GOALS
        ↓
02 RESEARCH
        ↓
03 ARCHITECTURE COUNCIL
        ↓
04 CONTEXT + SKILLS
        ↓
05 EXECUTION
        ↓
06 VALIDATION
        ↓
07 HERMES AUDIT
        ↓
08 REPAIR / CHANGE
        ↓
09 EVIDENCE + PUBLISH
        ↓
10 FINAL VERIFICATION
        │
        └──────────────► siguiente ciclo si falta algo

No significa que todos los pasos tengan que ejecutarse siempre.

El Workflow State Machine determina qué estado corresponde.


---

2. Estados del loop

WorkflowState

INPUT
RESEARCH
COUNCIL
PREPARE
EXECUTE
VALIDATE
AUDIT
REPAIR
PUBLISH
VERIFY
WAITING
PAUSED
FAILED
COMPLETED

La transición entre estados está definida por contratos.


---

3. Ejemplo de transición

EXECUTE
   │
   ▼
VALIDATE
   │
   ├── PASS ──► AUDIT
   │
   └── FAIL ──► REPAIR

Después:

REPAIR
   │
   ▼
VALIDATE

No se crea otro Workflow.

Es el mismo loop avanzando por estados.


---

4. Goals de entrada — 10

Cada Workflow recibe hasta 10 objetivos estructurados:

G01
G02
G03
G04
G05
G06
G07
G08
G09
G10

Cada Goal tiene:

Goal
├── id
├── description
├── priority
├── acceptance
├── dependencies
├── scope
└── status


---

5. Goals de salida — 10

El Workflow también produce hasta 10 resultados formales:

O01
O02
O03
O04
O05
O06
O07
O08
O09
O10

Ejemplo:

O01 = código implementado
O02 = tests
O03 = documentación
O04 = evidencia
O05 = validación

El Workflow no se considera completado solamente porque un agente terminó.

Debe satisfacer los Goals de salida correspondientes.


---

6. Architecture Council — 12

El Council tiene hasta 12 participantes o perspectivas:

C01
C02
C03
C04
C05
C06
C07
C08
C09
C10
C11
C12

No necesariamente tienen que ser 12 modelos diferentes.

Pueden ser:

agentes
roles
modelos
herramientas
analizadores

El resultado debe ser normalizado.


---

7. Council output

El Council produce:

ArchitectureDecision
├── proposal
├── alternatives
├── rejected_options
├── risks
├── dependencies
├── selected_solution
├── evidence
└── confidence

Después:

Council
 ↓
Sheriff
 ↓
ArchitectureDecision
 ↓
Workflow


---

8. Determinismo

La parte determinista no depende de que el modelo sea determinista.

El sistema fija:

STATE
INPUT
CONTRACT
POLICY
TRANSITION
CHECKPOINT

El agente puede producir diferentes respuestas.

Pero el Workflow decide:

PASS
FAIL
REPAIR
CHANGE_AGENT
RESEARCH
WAIT
ESCALATE

mediante reglas.


---

9. Priority Engine

Cada tarea tiene:

priority

Por ejemplo:

P0 = critical
P1 = high
P2 = normal
P3 = low

Pero también:

deadline
dependency
resource_cost
blocking


---

10. Prioridad dinámica

Supongamos:

Task A = P3
Task B = P2
Task C = P1

Pero Task C bloquea 7 tareas.

El Priority Engine puede calcular:

effective_priority

y convertir C en prioridad superior.

La fórmula exacta debe estar definida en política, no improvisada por un agente.


---

11. Paralelismo

Las tareas independientes pueden ejecutarse:

TASK
                │
       ┌────────┼────────┐
       ▼        ▼        ▼
      A         B        C
       │        │        │
       └────────┼────────┘
                ▼
              MERGE

Pero si:

D depende de A

entonces:

A
↓
D

El DAG determina la dependencia.


---

12. El loop no necesita rehacerse

Esta es una de las partes más importantes.

No construimos:

Workflow v1
Workflow v2
Workflow v3

por cada cambio.

Tenemos:

Workflow Engine
      │
      ▼
Current DAG
      │
      ▼
Change Engine

El Change Engine modifica el estado/configuración del DAG, no el motor.


---

13. Cambio dinámico

Si aparece:

NEW_DOCUMENT

el sistema hace:

Document Detector
        ↓
Impact Analyzer
        ↓
Change Proposal
        ↓
Hermes
        ↓
Sheriff
        ↓
DAG Patch

No reconstruye el Workflow.


---

14. DAG Patch

El cambio se representa como una operación:

ADD_NODE
REMOVE_NODE
REPLACE_NODE
MODIFY_NODE
ADD_DEPENDENCY
REMOVE_DEPENDENCY
CHANGE_PRIORITY
CHANGE_AGENT
ADD_RESEARCH
ADD_SKILL

Ejemplo:

ADD_NODE:
    security_review

Después:

validate patch

Si es válido:

apply patch


---

15. Versionado del DAG

Cada cambio genera:

DAG v1
DAG v2
DAG v3

pero el Workflow Engine sigue siendo el mismo.

Esto permite rollback.

DAG v7
 ↓
problem
 ↓
rollback
 ↓
DAG v6


---

16. Change Impact Analysis

Antes de modificar:

Change
 ↓
Impact Analyzer

Determina:

affected goals
affected nodes
affected documents
affected agents
affected skills
affected repositories
affected tests

Si el cambio no afecta una parte:

NO TOUCH

Esto evita reconstruir trabajo innecesariamente.


---

17. Nuevo documento

Ejemplo:

DOCUMENTS/
└── REQUIREMENT_NEW.md

El sistema detecta:

DocumentAdded

Después:

parse
 ↓
classify
 ↓
anchor
 ↓
compare
 ↓
impact analysis


---

18. Documento contradictorio

Si encuentra:

Architecture says X

y:

New document says Y

no cambia automáticamente.

Genera:

CONFLICT

y:

Hermes
 ↓
Architecture Council

Después se decide.


---

19. Modificación de OpenClaw

OpenClaw puede generar:

ChangeRequest

Ejemplo:

> "Agregar autenticación OAuth."



OpenClaw no modifica el DAG directamente.

Hace:

OpenClaw
 ↓
ChangeRequest
 ↓
Workflow
 ↓
Impact Analysis
 ↓
Hermes
 ↓
Sheriff
 ↓
DAG Patch


---

20. Modificación de Hermes

Hermes puede detectar:

MISSING_REQUIREMENT

y producir:

ChangeProposal

El camino es el mismo:

Hermes
 ↓
Change Engine
 ↓
Sheriff
 ↓
DAG Patch

Esto unifica todas las fuentes de cambio.


---

21. Watchdog

El Watchdog observa:

Workflow
Agent
Worker
Memory
CPU
Timeout
Heartbeat
Checkpoint

Pero no ejecuta tareas de negocio.

Su función es detectar:

STALE
TIMEOUT
CRASH
NO_HEARTBEAT
RESOURCE_LIMIT


---

22. Heartbeat

Cada tarea de larga duración mantiene:

heartbeat

Ejemplo:

Task 100
heartbeat 12:03
heartbeat 12:04
heartbeat 12:05

Si desaparece:

NO_HEARTBEAT

el Watchdog genera:

RecoveryEvent


---

23. Checkpoint

El Workflow guarda periódicamente:

Checkpoint
├── workflow_id
├── dag_version
├── current_node
├── completed_nodes
├── pending_nodes
├── active_nodes
├── goals
├── context_refs
├── memory_refs
├── agent_state
├── evidence_refs
└── timestamp


---

24. Reinicio

Si el servidor se cae:

SERVER DOWN

Después:

SERVER UP
 ↓
Recovery Engine
 ↓
latest checkpoint
 ↓
verify state
 ↓
resume

No empieza desde el paso 1.


---

25. Corte de API

Supongamos:

OpenCode
 ↓
API exhausted

El sistema clasifica:

API_QUOTA_EXHAUSTED

No significa:

TASK FAILED

Puede convertirse en:

WAITING_FOR_RESOURCE


---

26. Reanudación automática después de la 1 AM

La política puede establecer:

resume_policy:
    enabled: true
    window:
        start: "01:00"

Entonces:

API unavailable
       ↓
WAITING
       ↓
checkpoint
       ↓
01:00
       ↓
resource check
       ↓
resume

No se pierde el loop.


---

27. Si el agente muere

Agent crash
 ↓
Harness detects
 ↓
Checkpoint
 ↓
Failure classification
 ↓
Recovery policy

Puede decidir:

restart_same_agent

o:

change_agent

o:

research

o:

architecture_review


---

28. Reparaciones múltiples

No habrá un único método de reparación.

El RecoveryPolicy puede contener:

repair_same_agent
repair_new_agent
research
architecture_review
context_rebuild
skill_addition
source_reselection
rollback
human_escalation

El tipo de fallo determina cuál se utiliza.


---

29. Recovery Matrix

Ejemplo:

FAILURE              ACTION

syntax_error         repair_same_agent
test_failure         repair_same_agent
agent_crash          change_agent
missing_context      rebuild_context
missing_skill        skill_resolution
unknown_solution     research
architecture_error   council
source_problem       source_reselection
repository_error     rollback
resource_exhausted   wait/resume

Esto es mucho más robusto que una cadena fija de intentos.


---

30. Recovery no pierde información

Cada reparación mantiene:

attempt_id
failure_id
previous_agent
new_agent
context_ref
evidence
decision

Entonces:

Repair 1
 ↓
Repair 2
 ↓
Repair 3

no destruye el historial.


---

31. Long Loop real

Ejemplo:

GOAL
 ↓
RESEARCH
 ↓
COUNCIL
 ↓
EXECUTE
 ↓
VALIDATE
 ↓
FAIL
 ↓
HERMES
 ↓
RESEARCH
 ↓
SOURCE MIRROR
 ↓
SKILL
 ↓
CHANGE AGENT
 ↓
EXECUTE
 ↓
VALIDATE
 ↓
PASS
 ↓
PUBLISH
 ↓
VERIFY

Todo esto pertenece al mismo Workflow.


---

32. Workflow suspendido

Si no puede continuar:

WAITING

y conserva:

state
checkpoint
memory
documents
DAG version
priority
failure

Puede continuar posteriormente.


---

33. Nueva tarea urgente

Mientras hay tareas pendientes:

Task A P3
Task B P2
Task C P1

llega:

Task D P0

El Priority Engine puede:

pause A
pause B
execute D
resume A/B

si las dependencias y políticas permiten esa preempción.


---

34. Evitar corrupción por cambios

Un cambio nunca se aplica directamente sobre una ejecución activa sin comprobar impacto.

Change
 ↓
Impact Analysis
 ↓
Compatibility Check
 ↓
DAG Patch
 ↓
Validation
 ↓
Atomic Apply

Si falla:

rollback patch


---

35. Atomicidad

El cambio debe ser:

APPLIED

o:

NOT APPLIED

Nunca:

50% applied

Esto es esencial para no romper un Workflow largo.


---

36. Estado final del Long Loop

WORKFLOW
                       │
                       ▼
                    DAG STATE
                       │
       ┌───────────────┼────────────────┐
       ▼               ▼                ▼
   PRIORITY         CHECKPOINT       WATCHDOG
       │               │                │
       └───────────────┼────────────────┘
                       ▼
                     TASK
                       │
                       ▼
                    HARNESS
                       │
                       ▼
                    AGENT
                       │
                       ▼
                   VALIDATOR
                       │
                       ▼
                    HERMES
                       │
            ┌──────────┴──────────┐
            ▼                     ▼
          PASS                  CHANGE
                                  │
                                  ▼
                            IMPACT ANALYSIS
                                  │
                                  ▼
                              DAG PATCH
                                  │
                                  ▼
                               LOOP


---

37. Qué conseguimos con esta salida

El sistema ahora puede:

ejecutar loops extremadamente largos;

mantener checkpoints;

recuperarse de reinicios;

detectar procesos congelados;

esperar por recursos/API;

reanudar automáticamente;

cambiar de agente;

reparar con diferentes estrategias;

ejecutar tareas paralelas;

manejar prioridades;

incorporar documentos nuevos;

incorporar instrucciones de OpenClaw;

incorporar propuestas de Hermes;

añadir Skills;

añadir investigación;

modificar partes del DAG;

hacer rollback de cambios;

mantener trazabilidad;

conservar el mismo Workflow Engine.


Y la propiedad fundamental:

> No necesitas reconstruir el Workflow cuando cambia el trabajo. Cambias el estado o aplicas un DAG Patch validado.




---

Siguiente — Salida 9/10

GitHub Execution Gateway + Credential Broker + branches + commits + PR + rollback + deployment + validación + Sheriff, incluyendo cómo hacer que el Workflow haga automáticamente commit/push/PR/deploy sin entregar esas responsabilidades a los agentes.

WORKFLOW — Salida 9/10

GitHub Execution Gateway + Commit/Push + PR + Deploy + Rollback

Esta capa establece una regla importante:

> Los agentes producen cambios; el WORKFLOW controla GitHub, publicación, validación y despliegue.



Así ningún agente necesita tener permisos directos para hacer push, crear PR o desplegar.


---

1. Arquitectura

WORKFLOW
                            │
                            ▼
                    EXECUTION GATEWAY
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
           SHERIFF       VALIDATOR    CREDENTIAL
                                          BROKER
                                            │
                                            ▼
                                      GITHUB APP
                                            │
                         ┌──────────────────┼───────────────┐
                         ▼                  ▼               ▼
                       BRANCH              PR             TAG
                         │                  │               │
                         └──────────────────┼───────────────┘
                                            ▼
                                       DEPLOY GATEWAY
                                            │
                                            ▼
                                         SERVER


---

2. El agente no controla GitHub

El agente puede hacer:

CREATE / MODIFY CODE

Pero no:

git push
merge
deploy
delete branch

El flujo correcto es:

AGENT
  ↓
WORKSPACE
  ↓
VALIDATOR
  ↓
SHERIFF
  ↓
GITHUB GATEWAY
  ↓
COMMIT
  ↓
PUSH
  ↓
PR


---

3. Workspace aislado

Cada ejecución tiene su propio workspace:

/workspaces/
└── workflow-847/
    ├── source/
    ├── generated/
    ├── tests/
    ├── evidence/
    └── manifest.json

El agente trabaja exclusivamente ahí.


---

4. Repository Contract

Cada Workflow recibe explícitamente:

RepositoryContract
├── provider
├── organization
├── repository
├── allowed_branch
├── working_branch
├── allowed_paths
├── forbidden_paths
├── commit_policy
├── pull_request_policy
└── deployment_policy

Por tanto, el agente no puede decidir arbitrariamente qué repositorio modificar.


---

5. Restricción por grupo

Por ejemplo:

FRONTEND
    ↓
frontend-repository

y:

BACKEND
    ↓
backend-repository

Si un agente frontend intenta modificar:

backend/

el Sheriff bloquea la operación.


---

6. Branches

La regla:

main

nunca se toca directamente.

Se crea:

workflow/<workflow_id>/<task_id>

Ejemplo conceptual:

main
 │
 ├── workflow/847/frontend-ui
 └── workflow/847/auth-backend


---

7. Branch determinista

El nombre no lo inventa el agente.

Lo genera el Workflow:

branch_name =
workflow/{workflow_id}/{task_id}

Eso permite repetir la operación sin crear ramas aleatorias.


---

8. Idempotencia

Supongamos que el Workflow se reinicia después de crear la branch.

Al volver:

CREATE BRANCH

no se ejecuta ciegamente.

El GitHub Adapter primero consulta:

branch exists?

Si existe:

USE EXISTING BRANCH

Si no:

CREATE


---

9. Commit Gateway

El agente no decide el commit final.

El Workflow construye:

CommitRequest
├── repository
├── branch
├── files
├── message
├── workflow_id
├── task_id
└── evidence

Después:

Sheriff
 ↓
Validator
 ↓
GitHub Adapter


---

10. Commit Message

Puede utilizarse una estructura determinista:

<type>(<scope>): <description>

Ejemplo:

feat(frontend): add authentication interface

Pero el Workflow puede añadir metadata:

workflow: 847
task: F-21


---

11. GitHub App en lugar de PAT

La mejora que incorporaste anteriormente encaja aquí.

No se recomienda guardar un PAT permanente en el Workflow.

Usamos conceptualmente:

Credential Broker
        ↓
GitHub App
        ↓
installation token
        ↓
Repository

El token es:

temporal;

limitado;

asociado a la instalación;

con permisos mínimos.



---

12. Credential Broker

El Broker recibe:

CredentialRequest
├── repository
├── operation
├── workflow_id
└── required_permission

Y devuelve una credencial temporal.

El agente nunca recibe esa credencial.

Agent
  X
  │
  └── NO GitHub token

Workflow
  ↓
Credential Broker
  ↓
GitHub


---

13. Permisos mínimos

Para una operación de código:

contents
pull requests
metadata

Solo se solicitan los permisos necesarios.

Para despliegue se utiliza otra credencial separada.


---

14. Push

El proceso:

Workspace
    ↓
Detect changes
    ↓
Validate files
    ↓
Sheriff
    ↓
Credential Broker
    ↓
GitHub Adapter
    ↓
Push branch

El Workflow controla el push.


---

15. Pull Request

Después del push:

Branch
 ↓
PR Builder
 ↓
Pull Request

El PR contiene automáticamente:

workflow_id
task_id
goals
changes
tests
validation
evidence
research
agent


---

16. PR Contract

El PR puede requerir:

tests_passed = true
sheriff_approved = true
validator_passed = true
evidence_present = true

Si falta uno:

PR BLOCKED


---

17. Merge

El Workflow no debe asumir:

PR created = merge allowed

Primero:

PR
 ↓
checks
 ↓
Sheriff
 ↓
approval policy
 ↓
MERGE


---

18. Main protegido

La arquitectura conserva:

Agent
  ↓
feature branch
  ↓
PR
  ↓
validation
  ↓
merge
  ↓
main

Nunca:

Agent → main


---

19. Rollback

Cada publicación registra:

DeploymentRecord
├── workflow_id
├── commit
├── previous_commit
├── deployment_id
├── timestamp
├── validation
└── status

Si el despliegue falla:

Deployment
 ↓
Validation
 ↓
FAIL
 ↓
Rollback Policy
 ↓
previous known-good version


---

20. Known Good Version

El sistema mantiene:

KNOWN_GOOD

por repositorio.

Ejemplo:

commit A = known good
commit B = new deployment

Si B falla:

B
 ↓
FAIL
 ↓
A

No se necesita reconstruir el proyecto.


---

21. Deployment Gateway

Los agentes tampoco despliegan.

Agent
 ↓
Code
 ↓
GitHub
 ↓
Deployment Gateway
 ↓
Deploy

El Gateway recibe:

DeploymentRequest
├── repository
├── commit
├── environment
├── deployment_policy
└── workflow_id


---

22. Entornos

Se pueden definir:

development
staging
production

El Workflow decide dónde puede llegar cada tarea.

Por ejemplo:

Agent
 ↓
PR
 ↓
staging
 ↓
validation
 ↓
production


---

23. Sheriff de despliegue

Antes de desplegar:

Deployment Sheriff

comprueba:

correct repository
correct commit
tests
security
configuration
environment
approval
rollback available

Si falla:

DEPLOY BLOCKED


---

24. Deployment Validator

Después del despliegue:

DEPLOY
 ↓
HEALTH CHECK
 ↓
SMOKE TEST
 ↓
API CHECK
 ↓
APPLICATION CHECK

Resultado:

PASS

o:

FAIL


---

25. Si falla el deploy

No se manda automáticamente a un agente sin analizar el fallo.

DEPLOY FAILURE
      ↓
Failure Classifier
      │
 ┌────┼─────────────┐
 ▼    ▼             ▼
code config      infra
 │
 ▼
Repair Policy

Entonces puede decidir:

repair
rollback
retry
research
human approval


---

26. Pipeline completo

AGENT
                  │
                  ▼
               WORKSPACE
                  │
                  ▼
              VALIDATOR
                  │
                  ▼
               SHERIFF
                  │
                  ▼
             GITHUB GATEWAY
                  │
                  ▼
                BRANCH
                  │
                  ▼
                COMMIT
                  │
                  ▼
                 PUSH
                  │
                  ▼
                  PR
                  │
                  ▼
             PR VALIDATION
                  │
                  ▼
                MERGE
                  │
                  ▼
             DEPLOY GATEWAY
                  │
                  ▼
               STAGING
                  │
                  ▼
              HEALTH TEST
                  │
            ┌─────┴─────┐
            ▼           ▼
          PASS         FAIL
            │           │
            ▼           ▼
       PRODUCTION    RECOVERY
                        │
                 ┌──────┼──────┐
                 ▼      ▼      ▼
               REPAIR ROLLBACK RETRY


---

27. Evidencia

Cada etapa produce evidencia:

Evidence
├── source
├── tests
├── validator
├── sheriff
├── commit
├── PR
├── deployment
└── health

Todo queda asociado:

workflow_id
task_id
goal_id
commit_id


---

28. Hermes entra después de la ejecución

Hermes recibe:

Goal
+
Task
+
Code
+
Tests
+
Evidence
+
Deployment result

Y realiza su función de:

sentinela
juez
supervisor
validador
verificador

Si detecta algo incompleto:

Hermes
 ↓
Finding
 ↓
DSL DAG
 ↓
Sheriff
 ↓
Workflow


---

29. Hermes no modifica directamente

La regla es:

Hermes
   ↓
Finding / Change Proposal
   ↓
Workflow
   ↓
Impact Analysis
   ↓
DAG Patch

Así Hermes puede detectar y proponer sin romper la ejecución.


---

30. OpenClaw

OpenClaw queda como interfaz superior.

Puede decir:

> "Agregar autenticación OAuth al backend."



El flujo sería:

OpenClaw
 ↓
Change Request
 ↓
Workflow
 ↓
Goals
 ↓
Research
 ↓
Council
 ↓
Agent
 ↓
Validate
 ↓
Hermes
 ↓
GitHub
 ↓
Deploy

OpenClaw no necesita controlar cada comando técnico.


---

31. Reanudación después de GitHub

Si el proceso muere después del commit:

CHECKPOINT
state = COMMIT_CREATED

Al reiniciar:

Recovery
 ↓
GitHub inspection
 ↓
commit exists?
 ↓
YES
 ↓
continue PR

No crea otro commit innecesario.


---

32. Reanudación después del PR

Si ya existe:

PR #123

el Workflow detecta:

existing PR

y continúa con él.

No crea:

PR #124
PR #125

por un simple reinicio.


---

33. Reanudación después del deploy

Si el proceso muere justo después del despliegue:

Deployment checkpoint

Al volver:

Deployment status query

Si ya terminó:

continue validation

No vuelve a desplegar innecesariamente.


---

34. Contratos Sheriff

La cadena queda protegida por varios contratos:

InputSheriff
ResearchSheriff
ArchitectureSheriff
AgentSheriff
RepositorySheriff
GitHubSheriff
DeploymentSheriff
FinalSheriff

Cada uno tiene un ámbito.

No hay un Sheriff gigante con toda la lógica.


---

35. Resultado

La responsabilidad queda muy clara:

AGENTS
    ↓
pensar / investigar / programar / reparar

WORKFLOW
    ↓
orquestar / controlar estados / recuperar

SHERIFF
    ↓
autorizar / bloquear

VALIDATOR
    ↓
comprobar

HERMES
    ↓
auditar / detectar faltantes / proponer cambios

GITHUB GATEWAY
    ↓
commit / push / PR

DEPLOYMENT GATEWAY
    ↓
deploy / health / rollback

MEMORY
    ↓
recordar


---

36. La regla fundamental

El agente no tiene que saber cómo desplegar el proyecto.

Tampoco tiene que conocer:

el token de GitHub;

las credenciales de producción;

la política de ramas;

el mecanismo de rollback;

el sistema de deployment.


Solo produce el resultado solicitado.

El Workflow convierte ese resultado en una operación controlada.


---

37. Estado del diseño

Con esta salida ya están definidos los grandes bloques:

WORKFLOW
├── Goals
├── Architecture Council
├── Research Engine
├── Skills
├── Long Loop
├── Priority Engine
├── Checkpoints
├── Watchdog
├── Recovery
├── Dynamic DAG Patch
├── Memory Router
├── Hermes
├── Agent Harness
├── Sandbox
├── GitHub Gateway
├── Credential Broker
├── Commit
├── Push
├── PR
├── Deployment Gateway
├── Validation
└── Rollback

Siguiente — Salida 10/10: integración final de todo el sistema: OpenClaw + Hermes + Frontend + Backend + agentes intercambiables + Harness universal + Sandbox + Council + Research + Memory + Long Loop + GitHub + Deploy, incluyendo la estructura de carpetas y los contratos principales para convertir este diseño en una implementación real.

WORKFLOW — Salida 10/10

Arquitectura final integrada

Esta es la integración de las 9 capas anteriores en un único sistema. La idea es mantener el núcleo pequeño y determinista, mientras los agentes, memoria, sandbox, modelos y herramientas son intercambiables.


---

1. Arquitectura completa

OPENCLAW
                              │
                    ┌─────────┴─────────┐
                    │                   │
              Usuario / UI         Chat / Commands
                    │                   │
                    └─────────┬─────────┘
                              ▼
                       WORKFLOW API
                              │
                              ▼
                    CONTROL / STATE CORE
                              │
       ┌──────────────┬───────┼────────┬──────────────┐
       ▼              ▼       ▼        ▼              ▼
     GOALS         COUNCIL  RESEARCH  MEMORY       PRIORITY
       │              │       │        │              │
       └──────────────┴───────┼────────┴──────────────┘
                              ▼
                         DSL DAG
                              │
                              ▼
                      LONG LOOP ENGINE
                              │
                  ┌───────────┼───────────┐
                  ▼           ▼           ▼
               FRONTEND    BACKEND     OTHER
                  │           │           │
                  ▼           ▼           ▼
               HARNESS      HARNESS     HARNESS
                  │           │           │
                  ▼           ▼           ▼
               SANDBOX      SANDBOX     SANDBOX
                  │           │           │
                  ▼           ▼           ▼
               AGENTS       AGENTS      AGENTS
                  │           │           │
                  └───────────┼───────────┘
                              ▼
                         VALIDATOR
                              │
                              ▼
                           HERMES
                              │
                  ┌───────────┴───────────┐
                  ▼                       ▼
               PASS                    FINDING
                  │                       │
                  ▼                       ▼
               GITHUB                 DAG PATCH
                  │                       │
                  ▼                       └──────► LOOP
              DEPLOYMENT
                  │
                  ▼
               VERIFY
                  │
                  ▼
              COMPLETED


---

2. Los dos grupos ejecutores

Se conserva exactamente el roster que definiste.

Backend

BACKEND
│
├── Architecture Council
│
├── OpenCode
│      └── ejecutor principal
│
├── OpenHands
│      └── recuperación / problemas complejos
│
├── Codex CLI
│      └── reparación / verificación
│
└── Claude Code CLI
       └── reparación / refactor / ejecución final

Frontend

FRONTEND
│
├── Architecture Council
│
├── Cline
│      └── ejecutor principal
│
├── OpenHands
│      └── recuperación / tareas complejas
│
├── OpenCode
│      └── reparación / refactor
│
├── Codex CLI
│      └── revisión
│
├── Kimi Code CLI
│      └── especialista frontend / recuperación final
│
└── Mimo Code
       └── especialista frontend / recuperación final

La importante mejora arquitectónica es que estos agentes no están codificados dentro del núcleo.

Se describen mediante contratos.

Por eso posteriormente puedes sustituir:

OpenCode → agente nuevo

sin reescribir el Workflow.


---

3. Harness universal

El Harness es el adaptador que resuelve el problema que detectaste anteriormente: cada agente puede tener CLI, API, UI o mecanismo de ejecución diferente.

AGENT HARNESS
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
        CLI            API             UI
          │              │              │
     OpenCode         Agent X        Agent Y
     Codex CLI
     Claude Code
     Cline

Interfaz conceptual:

prepare()
load_context()
execute()
collect_result()
validate_output()
cleanup()

El Workflow solamente conoce el Harness.

No necesita conocer la implementación interna de cada agente.


---

4. Agent Contract

Cada agente tiene una definición:

AgentContract
├── agent_id
├── name
├── group
├── capabilities
├── interface
├── harness
├── sandbox
├── required_skills
├── allowed_repositories
├── allowed_operations
├── resource_policy
└── validation_policy

Por ejemplo:

agent_id:
  backend-opencode

El Workflow lo resuelve mediante:

AgentRegistry


---

5. Agente intercambiable

El DAG no contiene:

"ejecutar OpenCode"

como dependencia rígida.

Contiene algo conceptualmente como:

role:
  backend_primary_executor

El Registry resuelve:

backend_primary_executor
        ↓
OpenCode

Si mañana decides:

backend_primary_executor
        ↓
Agent-X

el DAG no cambia.


---

6. Sandbox intercambiable

La misma filosofía:

SandboxManager
       │
       ├── Docker
       ├── gVisor
       ├── Firecracker
       └── Other

El Workflow solicita:

create_sandbox()

No necesita saber cómo se implementa.

Cada grupo puede tener políticas diferentes.


---

7. Separación de memoria y Sandbox

El Sandbox puede desaparecer:

SANDBOX CRASH

pero:

MEMORY
CHECKPOINT
SOURCE MIRROR
DOCUMENTS
EVENTS

permanecen.

Entonces:

Sandbox destroyed
       ↓
new sandbox
       ↓
restore workspace
       ↓
restore context
       ↓
resume


---

8. Memory Engine

La memoria sigue siendo intercambiable:

MemoryRouter
│
├── Graphiti
├── GraphRAG
├── Graphify
├── Vector DB
└── SQL / other

El Workflow no depende de una tecnología concreta.


---

9. Document Anchors

Todo elemento importante puede quedar anclado:

PROJECT
│
├── Goal
├── Document
├── Decision
├── Research
├── Repository
├── Skill
├── Agent execution
├── Failure
├── Repair
├── Commit
└── Deployment

Esto permite trazabilidad completa.


---

10. Hermes

Hermes queda fuera del grupo ejecutor.

Es un componente independiente:

HERMES
                       │
       ┌───────────────┼────────────────┐
       ▼               ▼                ▼
   SENTINELA          JUEZ          SUPERVISOR
       │               │                │
       ├───────────────┼────────────────┤
                       ▼
                   VALIDATOR
                       │
                       ▼
                   VERIFIER

Su función es revisar:

objetivo
documentación
arquitectura
código
tests
evidencia
resultado


---

11. Hermes no rompe el Workflow

Hermes nunca modifica directamente el DAG.

Produce:

HermesFinding

o:

HermesChangeProposal

Después:

Hermes
 ↓
Workflow
 ↓
Impact Analyzer
 ↓
Sheriff
 ↓
DAG Patch


---

12. OpenClaw + Hermes

OpenClaw puede recibir el resultado de Hermes:

OpenClaw
   ▲
   │
Hermes
   ▲
   │
Workflow

Por ejemplo:

Faltan:
- test X
- documentación Y
- validación Z

OpenClaw puede mostrarlo al usuario y solicitar una nueva instrucción.


---

13. Architecture Council

El Council puede utilizar varios agentes:

OpenClaw
   ↓
"Prepara Council"
   ↓
Council Registry
   ↓
Agent 1
Agent 2
Agent 3
Agent 4
Agent 5
   ↓
debate
   ↓
evidence
   ↓
synthesis
   ↓
Architecture Decision

También puede asignarse una API/modelo diferente por participante.

El usuario puede definir:

agent 1 → API/modelo A
agent 2 → API/modelo B
agent 3 → API/modelo C

El Workflow controla esas credenciales.


---

14. El sistema de investigación

Antes de construir cuando corresponda:

TASK
 ↓
Research Engine
 ↓
20+ candidates
 ↓
filter
 ↓
compare
 ↓
license
 ↓
security
 ↓
architecture
 ↓
Council
 ↓
Sheriff
 ↓
Source Mirror

Los repositorios aprobados quedan disponibles como fuente.


---

15. Source Mirror

SOURCE_MIRROR
│
├── BACKEND
│   ├── repository-A
│   ├── repository-B
│   └── ...
│
└── FRONTEND
    ├── repository-A
    ├── repository-B
    └── ...

Cada uno tiene:

source
manifest
metadata
evidence
analysis

Y versión fijada mediante commit/tag/hash.


---

16. Skills

Antes de ejecutar:

Task
 ↓
Skill Resolver
 ↓
Required Skills
 ↓
Skill Registry
 ↓
Context
 ↓
Agent

Si falta un Skill:

STOP
 ↓
Research
 ↓
Skill creation/registration
 ↓
Sheriff
 ↓
resume


---

17. Loop completo

El loop definitivo:

01 GOALS
      ↓
02 RESEARCH
      ↓
03 ARCHITECTURE COUNCIL
      ↓
04 CONTEXT + SKILLS
      ↓
05 EXECUTION
      ↓
06 VALIDATION
      ↓
07 HERMES AUDIT
      ↓
08 REPAIR / CHANGE
      ↓
09 EVIDENCE + GITHUB
      ↓
10 FINAL VERIFICATION

Y puede repetirse indefinidamente mediante checkpoints.


---

18. Long Loop

No hay:

for i in range(3)

como mecanismo de recuperación.

Existe un estado persistente:

WorkflowState

que puede permanecer:

RUNNING
WAITING
PAUSED
RECOVERING

durante horas o días.


---

19. Recuperación

CRASH
 │
 ▼
CHECKPOINT
 │
 ▼
RECOVERY ENGINE
 │
 ├── same agent
 ├── different agent
 ├── repair
 ├── research
 ├── council
 ├── rollback
 └── wait

La selección es determinada por RecoveryPolicy.


---

20. Cambio dinámico

Nuevo documento:

DocumentAdded
      ↓
Impact Analysis
      ↓
Hermes
      ↓
Change Proposal
      ↓
Sheriff
      ↓
DAG Patch
      ↓
Resume

No se reconstruye el Workflow.


---

21. Prioridad

Cada tarea tiene:

priority
dependency
deadline
blocking
resource

El Priority Engine puede reorganizar tareas independientes.

Ejemplo:

P3 ──────┐
P2 ──────┼──► queue
P1 ──────┤
P0 ──────┘

Las tareas bloqueantes reciben prioridad según política.


---

22. Paralelismo

ROOT
                │
        ┌───────┼───────┐
        ▼       ▼       ▼
       A        B        C
        │       │       │
        └───────┼───────┘
                ▼
                D

A/B/C pueden ejecutarse simultáneamente si no comparten recursos incompatibles.


---

23. GitHub

El agente no hace:

push
merge
deploy

El Workflow hace:

Agent
 ↓
Workspace
 ↓
Validator
 ↓
Sheriff
 ↓
GitHub Gateway
 ↓
Branch
 ↓
Commit
 ↓
Push
 ↓
PR
 ↓
Merge


---

24. Credenciales

Workflow
 ↓
Credential Broker
 ↓
GitHub App
 ↓
temporary credential

Los agentes no reciben el token.


---

25. Deployment

GitHub
 ↓
Deployment Gateway
 ↓
Staging
 ↓
Health Check
 ↓
Smoke Tests
 ↓
Production

Si falla:

FAIL
 ↓
Recovery
 ↓
Rollback


---

26. Rollback

Se conserva:

known_good_commit

Por tanto:

version A = known good
version B = deployed
version B = failure

rollback → A


---

27. Contratos Sheriff

La arquitectura final utiliza contratos especializados:

InputSheriff
ResearchSheriff
ArchitectureSheriff
SkillSheriff
AgentSheriff
RepositorySheriff
ExecutionSheriff
GitHubSheriff
DeploymentSheriff
FinalSheriff

Cada uno controla solamente su dominio.


---

28. DSL DAG

El DAG es la representación declarativa del trabajo:

workflow
│
├── goals
├── nodes
├── dependencies
├── agents
├── skills
├── resources
├── policies
├── recovery
├── memory
├── repository
└── deployment

Los agentes no tienen que reconstruir este DAG.

Hermes puede proponer un DAG Patch.


---

29. Estructura de proyecto recomendada

workflow/
│
├── core/
│   ├── state/
│   ├── transitions/
│   ├── scheduler/
│   └── policies/
│
├── contracts/
│   ├── goals/
│   ├── agents/
│   ├── memory/
│   ├── research/
│   ├── github/
│   └── deployment/
│
├── dag/
│   ├── parser/
│   ├── validator/
│   ├── patch/
│   └── versions/
│
├── agents/
│   ├── registry/
│   ├── harness/
│   └── adapters/
│
├── sandbox/
│   ├── manager/
│   └── adapters/
│
├── memory/
│   ├── router/
│   ├── adapters/
│   ├── context/
│   └── anchors/
│
├── research/
│   ├── engine/
│   ├── repository/
│   ├── mirror/
│   └── evidence/
│
├── skills/
│   ├── registry/
│   ├── resolver/
│   └── validation/
│
├── hermes/
│   ├── sentinel/
│   ├── judge/
│   ├── supervisor/
│   └── validator/
│
├── github/
│   ├── gateway/
│   ├── credentials/
│   ├── branches/
│   ├── commits/
│   └── pull_requests/
│
├── deployment/
│   ├── gateway/
│   ├── validator/
│   └── rollback/
│
├── recovery/
│   ├── checkpoint/
│   ├── watchdog/
│   └── policies/
│
├── observability/
│
└── config/
    ├── frontend.yaml
    ├── backend.yaml
    └── policies.yaml


---

30. Configuración de los grupos

Conceptualmente:

groups:
  backend:
    primary: backend_primary_executor

    recovery:
      - backend_complex_recovery
      - backend_repair
      - backend_final_repair

  frontend:
    primary: frontend_primary_executor

    recovery:
      - frontend_complex_recovery
      - frontend_refactor
      - frontend_review
      - frontend_specialist_1
      - frontend_specialist_2

Los nombres reales de agentes se resuelven en AgentRegistry.


---

31. Por qué esta arquitectura es intercambiable

Puedes cambiar:

Temporal

por otro motor de ejecución.

Puedes cambiar:

Docker

por Firecracker.

Puedes cambiar:

Graphiti

por otra memoria.

Puedes cambiar:

OpenCode

por otro agente.

Puedes cambiar:

GitHub

por otro proveedor.

Y el núcleo conceptual sigue siendo:

Contracts
+
State
+
DAG
+
Policies
+
Adapters


---

32. Temporal

Si posteriormente utilizas Temporal, no debe convertirse en el núcleo conceptual.

Temporal puede ejecutar:

Workflow State

y:

Activities

para:

run_agent
research
validate
github
deploy
memory

Pero el diseño contractual permanece independiente.

Por eso el sistema no queda atado a Temporal.


---

33. El principio más importante

La arquitectura final separa cinco cosas:

WORKFLOW
                    │
       ┌────────────┼─────────────┐
       ▼            ▼             ▼
     DECIDE       EXECUTE       REMEMBER
       │            │             │
    policies      agents        memory
       │            │
       ▼            ▼
     CONTROL      HARNESS
                    │
                    ▼
                  SANDBOX

Los modelos razonan.

El Workflow controla.

Los contratos restringen.

Los Validators comprueban.

Hermes audita.

Memory recuerda.

GitHub Gateway publica.

Deployment Gateway despliega.


---

34. Resultado final

La arquitectura completa queda:

┌─────────────┐
                         │  OPENCLAW   │
                         └──────┬──────┘
                                │
                                ▼
                    ┌─────────────────────┐
                    │       WORKFLOW      │
                    │                     │
                    │ Goals               │
                    │ DAG                 │
                    │ Policies            │
                    │ Priority            │
                    │ Recovery             │
                    │ Checkpoints          │
                    └──────────┬──────────┘
                               │
          ┌────────────────────┼─────────────────────┐
          ▼                    ▼                     ▼
     ARCHITECTURE          RESEARCH                MEMORY
       COUNCIL              ENGINE                 ENGINE
          │                    │                     │
          └────────────────────┼─────────────────────┘
                               ▼
                         CONTEXT BUILDER
                               │
                               ▼
                         SKILL RESOLVER
                               │
                               ▼
                           LONG LOOP
                               │
                  ┌────────────┴────────────┐
                  ▼                         ▼
              FRONTEND                   BACKEND
                  │                         │
               CLINE                    OPENCODE
                  │                         │
              OPENHANDS                  OPENHANDS
                  │                         │
              OPENCODE                   CODEX CLI
                  │                         │
              CODEX CLI                CLAUDE CODE
                  │
             KIMI CODE
                  │
              MIMO CODE
                  │
                  └────────────┬────────────┘
                               ▼
                           VALIDATOR
                               │
                               ▼
                            HERMES
                               │
                         ┌─────┴─────┐
                         ▼           ▼
                       PASS       FINDING
                         │           │
                         ▼           ▼
                      GITHUB      DAG PATCH
                         │           │
                         ▼           └──────► LOOP
                     DEPLOYMENT
                         │
                         ▼
                       VERIFY
                         │
                         ▼
                      MEMORY
                         │
                         ▼
                     COMPLETED


---

35. Qué queda pendiente para pasar de arquitectura a código

La arquitectura ya está suficientemente definida para empezar la implementación. Lo siguiente no debería hacerse todo simultáneamente.

Orden recomendado:

FASE 1
Contracts + State + DAG

FASE 2
Agent Registry + Universal Harness

FASE 3
Sandbox

FASE 4
Long Loop + Checkpoint + Recovery

FASE 5
Memory Router + Context Builder

FASE 6
Research Engine + Source Mirror + Skills

FASE 7
Hermes

FASE 8
GitHub Gateway + Credential Broker

FASE 9
Deployment + Rollback

FASE 10
OpenClaw integration

FASE 11
Frontend / Backend group policies

FASE 12
Stress tests + failure recovery

Punto clave: no empezaría instalando Temporal, Graphiti, todos los agentes y todos los servicios a la vez. Primero construiría el núcleo determinista de contratos + estado + DAG + adapters, porque ese núcleo es precisamente lo que permite cambiar posteriormente de agente, memoria, sandbox u orquestador sin reconstruir todo el sistema.

Sí. Hice una auditoría en 4 pasadas, tomando como referencia todo lo que aparece disponible del historial/contexto de esta conversación y las decisiones que fuimos fijando. No voy a inventar elementos que no estén respaldados.

Auditoría 4 pasadas — WORKFLOW

PASADA 1 — Arquitectura y componentes

Confirmado e incluido

OpenClaw como interfaz superior.

Workflow como capa de control.

DSL DAG.

Architecture Council.

Goals de entrada: 10.

Goals de salida: 10.

Council de arquitectura: 12.

Loop principal de 10 etapas.

Loops largos, no limitados a 3 intentos.

Checkpoints persistentes.

Watchdog.

Recovery después de reinicio.

Recovery por agotamiento de API/saldo.

Recovery por crash/interrupción.

Ejecución paralela.

Sistema de prioridades.

Dynamic DAG Patch.

Incorporación de documentos nuevos sin reconstruir el Workflow.

Incorporación de correcciones/mejoras de OpenClaw.

Incorporación de propuestas de Hermes.

Memory Router intercambiable.

Graphiti.

GraphRAG.

Graphify, según la denominación que utilizaste.

Vector/relational storage como posibles backends.

Document Anchors.

trazabilidad de decisiones, tareas y ejecuciones.

Hermes como componente independiente.

Hermes como sentinela/juez/supervisor/validador/verificador.

Hermes generando propuestas DSL DAG.

Hermes informando a OpenClaw.

Hermes incorporando Skills en paralelo.

Architecture Council investigando soluciones.

Investigación de repositorios.

mínimo de 20 investigaciones por sistema.

descarga obligatoria de código fuente aprobado.

Source Mirror aislado.

Skills obligatorios.

Sheriff estricto.

contratos separados por función.


Veredicto

La arquitectura principal está cubierta.


---

PASADA 2 — Agentes y ejecución

Aquí revisé especialmente los agentes porque anteriormente hubo errores de roster.

BACKEND — roster correcto

BACKEND
│
├── Architecture Council
│
├── OpenCode
│     └── ejecutor principal
│
├── OpenHands
│     └── recuperación / problemas complejos
│
├── Codex CLI
│     └── reparación / verificación
│
└── Claude Code CLI
      └── reparación / refactor / ejecución final

FRONTEND — roster correcto

FRONTEND
│
├── Architecture Council
│
├── Cline
│     └── ejecutor principal
│
├── OpenHands
│     └── recuperación / tareas complejas
│
├── OpenCode
│     └── reparación / refactor
│
├── Codex CLI
│     └── revisión
│
├── Kimi Code CLI
│     └── especialista frontend / recuperación final
│
└── Mimo Code
      └── especialista frontend / recuperación final

También queda confirmado:

agentes intercambiables;

Agent Registry;

Harness universal;

agente mediante CLI/API/UI;

OpenClaw con UI;

OpenClaw sin UI;

Hermes independiente con/sin UI;

mismo agente ejecutable en diferentes grupos mediante Harness;

aislamiento de workspace;

Sandbox por grupo;

agentes sin acceso directo al token de GitHub.


Council desde OpenClaw

También estaba solicitado y debe permanecer:

OpenClaw
   ↓
"crea un Council"
   ↓
agente 1
agente 2
agente 3
agente 4
agente 5
   ↓
debate
   ↓
conclusión
   ↓
Hermes
   ↓
DSL DAG

Y OpenClaw debe poder especificar qué API/modelo utiliza cada agente.

Veredicto

Roster corregido y conservado.


---

PASADA 3 — Investigación, memoria y modificación dinámica

Aquí encontré varios elementos que deben quedar explícitamente como obligatorios, no como características opcionales.

Investigación

El flujo correcto es:

TASK
 ↓
RESEARCH ENGINE
 ↓
buscar soluciones/repos
 ↓
mínimo 20 candidatos/investigaciones
 ↓
filtrar
 ↓
Council
 ↓
Sheriff
 ↓
aprobar
 ↓
descargar código fuente
 ↓
SOURCE MIRROR
 ↓
Agent

El agente debe poder utilizar ese código como fuente de referencia, evitando construir todo desde cero cuando exista una implementación útil.

Source Mirror

Debe estar separado del código principal:

source-mirror/
├── frontend/
│   ├── repo-001/
│   ├── repo-002/
│   └── ...
│
└── backend/
    ├── repo-001/
    ├── repo-002/
    └── ...

Y debe conservar:

repositorio;

versión;

commit/hash;

licencia;

procedencia;

análisis;

evidencia.



---

Cursor / Ask Preview

Este punto no debe desaparecer.

Solicitaste un sistema tipo:

ASK / PREVIEW
      ↓
análisis
      ↓
plan
      ↓
tokens mínimos
      ↓
ejecución

Su finalidad es reducir consumo innecesario de modelos y evitar construir antes de comprender.

Debe ser parte del contrato del Council/Planning y no una simple función informal.


---

Cambios dinámicos

El sistema debe reconocer:

nuevo documento
nuevo objetivo
corrección
mejora
sugerencia de OpenClaw
hallazgo de Hermes
cambio de requisito

y hacer:

CHANGE EVENT
     ↓
IMPACT ANALYZER
     ↓
determina nodos afectados
     ↓
DAG PATCH
     ↓
Sheriff
     ↓
actualiza Workflow
     ↓
continúa

No:

destruir Workflow
↓
crear Workflow nuevo


---

Memoria

La memoria debe ser desacoplada:

MemoryRouter
│
├── Graphiti
├── GraphRAG
├── Graphify
├── Vector DB
├── Graph DB
└── SQL

Y los documentos deben poder quedar anclados a:

Goal
Task
Decision
Agent
Research
Skill
Commit
Failure
Repair
Deployment

Esto permite reconstruir el contexto después de un reinicio.

Veredicto

Estos elementos deben quedar explícitos en la especificación final.


---

PASADA 4 — Operación, recuperación, GitHub y despliegue

Esta es la pasada más importante porque aquí estaban varias de las mejoras que tú incorporaste.

Long Loop

No debe ser:

intento 1
intento 2
intento 3

Debe ser:

STATE
 ↓
CHECKPOINT
 ↓
EXECUTE
 ↓
VALIDATE
 ↓
RECOVER / CONTINUE
 ↓
CHECKPOINT
 ↓
NEXT STATE

Puede durar:

horas;

días;

después de reinicios;

después de interrupciones;

después de agotamiento temporal de API.



---

Watchdog

Debe detectar:

crash
timeout
worker perdido
API agotada
saldo agotado
servidor reiniciado
sandbox muerto
agente detenido

Y convertirlo en un estado recuperable.

También queda incluida tu condición:

> si un proceso queda pendiente, el Workflow puede retomarlo automáticamente después de la 1 a. m.



Eso debe implementarse como Recovery/Schedule Policy, no como lógica especial dentro del agente.


---

GitHub

La mejora que aportaste de Claude sí encaja, excepto cualquier referencia a nombres que tú marcaste como alucinados.

Queda:

Agent
 ↓
Workspace
 ↓
Validator
 ↓
Sheriff
 ↓
GitHub Gateway
 ↓
branch
 ↓
commit
 ↓
push
 ↓
PR
 ↓
validation
 ↓
merge

Y:

Credential Broker

En vez de entregar un PAT permanente al agente:

Credential Broker
       ↓
GitHub App
       ↓
token temporal
       ↓
GitHub Gateway

El agente nunca recibe el token.


---

Idempotencia

También queda incorporada la mejora que mencionaste:

Si el Workflow se reinicia después de:

branch creada

no crea otra.

Si ya existe:

commit

no duplica.

Si ya existe:

PR

continúa sobre ella.

Si ya existe:

deployment

consulta su estado antes de repetirlo.


---

Failure Contract

No debe existir:

success = true/false

como único resultado.

Debe existir algo conceptualmente equivalente a:

Failure
├── type
├── detail
├── retryable
├── evidence
├── affected_node
├── recovery_policy
└── timestamp

Esto permite que:

Validator
Sheriff
Recovery
Hermes
Observability

entiendan el mismo fallo.


---

Chain Budget

También debe permanecer la mejora:

ChainBudget
├── time
├── API calls
├── tokens
├── cost
└── resources

No solamente límite individual de cada agente.

Esto es especialmente importante para tus cadenas de recuperación.


---

Observability

El print() no es suficiente.

Debe existir:

Event Store

con:

workflow_id
task_id
node_id
agent
state
event
timestamp
evidence

Así Recovery puede reconstruir lo sucedido.


---

Sandbox

También queda:

SandboxManager
│
├── Docker
├── gVisor
├── Firecracker
└── otro adapter

No se fija el núcleo a una tecnología.

Y la memoria/checkpoint queda fuera del sandbox para poder recuperar el trabajo si el sandbox muere.


---

Auditoría final

Después de las cuatro pasadas, la estructura completa queda:

WORKFLOW
│
├── 1. Input / 10 Goals
│
├── 2. Research
│      └── mínimo 20 investigaciones
│
├── 3. Architecture Council
│      └── 12 participantes
│
├── 4. Ask / Preview / Planning
│
├── 5. Context + Memory + Skills
│
├── 6. Execution
│      ├── Frontend
│      └── Backend
│
├── 7. Validation
│
├── 8. Hermes Audit
│
├── 9. Repair / Dynamic DAG Patch
│
├── 10. GitHub / Deploy / Final Verification
│
├── Long Loop
├── Checkpoints
├── Watchdog
├── Recovery
├── Priority
├── Parallel Execution
├── Agent Registry
├── Universal Harness
├── Sandbox Manager
├── Memory Router
├── Source Mirror
├── Skill Registry
├── Sheriff Contracts
├── Failure Contracts
├── Chain Budget
├── Event Store
└── Rollback

Lo que NO voy a introducir

En esta auditoría también eliminé conceptos que aparecieron anteriormente pero que no fueron parte de tu diseño confirmado:

ningún roster N00–N13;

Plandex/Goose/PydanticAI como agentes obligatorios;

un supuesto sistema "MAVIS M3";

cambiar OpenClaw;

convertir Hermes en ejecutor de código;

convertir Control Layer en un segundo orquestador;

imponer Temporal como dependencia del núcleo;

imponer Docker como único Sandbox;

imponer Graphiti como única memoria.


Resultado de la auditoría

No detecto una contradicción estructural importante con lo que has ido definiendo.

La corrección más importante respecto de mis respuestas anteriores es esta:

> El Workflow debe ser un sistema de control declarativo y persistente; los agentes, memoria, sandbox, motor de ejecución y proveedores externos deben entrar mediante contratos/adapters.



Eso es lo que permite que el sistema sea realmente modificable sin reconstruir todo el Workflow.


Sí. Y tienes razón en señalarlo: hasta ahora te entregué principalmente la arquitectura, no el código completo del Workflow.

Si preguntas cuántos “loops” tendrá realmente el sistema, no lo limitaría a 10. Los 10 pasos son el loop lógico principal, pero dentro de ellos existirán subloops deterministas.

La estructura sería aproximadamente:

WORKFLOW PRINCIPAL
│
├── 10 pasos principales
│
├── Council Loop
│   └── 12 pasos
│
├── Goals Input
│   └── 10 validaciones
│
├── Goals Output
│   └── 10 validaciones
│
├── Research Loop
│   └── ≥20 investigaciones
│
├── Skill Loop
│   └── descubrir → validar → incorporar
│
├── Agent Execution Loop
│   └── ejecutar → validar → reparar
│
├── Validation Loop
│   └── test → failure → recovery
│
├── Hermes Loop
│   └── auditar → encontrar → DSL DAG patch
│
├── Memory Loop
│   └── guardar → anclar → recuperar
│
├── Change Loop
│   └── documento/cambio → impacto → parche DAG
│
├── Recovery Loop
│   └── checkpoint → recuperar → continuar
│
├── GitHub Loop
│   └── branch → commit → push → PR → validate
│
└── Deployment Loop
    └── deploy → health → rollback/recovery

Por tanto, no estamos hablando de un solo loop de 10 pasos, sino de un loop jerárquico.

Y sí: se puede programar

La implementación debería comenzar por el núcleo:

workflow/
├── core/
│   ├── engine/
│   ├── state/
│   ├── transitions/
│   └── scheduler/
├── dag/
├── contracts/
├── policies/
├── recovery/
├── agents/
├── harness/
├── sandbox/
├── research/
├── skills/
├── memory/
├── hermes/
├── github/
├── deployment/
└── tests/

Y el principio de programación sería:

Event
  ↓
State
  ↓
Policy
  ↓
Transition
  ↓
Checkpoint
  ↓
Next State

No un enorme while con cientos de condiciones.

Eso es importante porque hace que el sistema sea determinista, reanudable y auditable.

Lo que te propongo hacer ahora

En lugar de seguir describiendo arquitectura, puedo pasar a la implementación real, empezando por:

Parte 1: WorkflowState + contratos + máquina de estados + DSL DAG + checkpoint/recovery.

Después construimos encima:

Parte 2: Long Loop + prioridades + paralelismo + watchdog.

Parte 3: Agent Registry + Universal Harness.

Y así sucesivamente hasta GitHub, Hermes, memoria y deployment.

Eso sí sería ya programar el Workflow, no solamente diseñarlo.








