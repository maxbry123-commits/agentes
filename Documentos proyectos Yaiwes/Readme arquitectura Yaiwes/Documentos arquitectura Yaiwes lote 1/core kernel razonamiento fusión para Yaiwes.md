Sistema del nuevo kernel de Yaiwes usando los mejores kernel open soure y el kernel que hizo Fables 


Sí. Lo que describes no es simplemente “pensar más”. Es un conjunto de operadores cognitivos que puede convertirse en una arquitectura explícita para tu agente de investigación.

Tu lista actual ya contiene varias familias cognitivas, pero está mezclando:

1. operaciones de razonamiento,


2. operaciones de búsqueda,


3. operaciones de verificación,


4. operaciones de memoria,


5. operaciones de convergencia,


6. y operaciones metacognitivas.



La mejora importante para YAIWES sería formalizarlas como un sistema ejecutable, no dejarlas como una lista dentro de un prompt.


---

1. Sistemas de pensamiento más avanzados para añadir

Tu lista tiene cosas como:

> Refinar → refutar → analizar → desenredar → triangular → calibrar → cristalizar.



Eso puede convertirse en una taxonomía cognitiva.

A. Razonamiento estructural

Descomponer

Reagrupar

Abstraer

Concretar

Jerarquizar

Mapear dependencias

Detectar invariantes

Detectar restricciones

Encontrar cuellos de botella

Identificar causa raíz

Construir árbol causal

Construir grafo causal

Encontrar ciclos

Detectar contradicciones

Resolver ambigüedad

Separar correlación de causalidad



---

B. Razonamiento adversarial

Este grupo falta parcialmente en tu lista.

Refutar

Intentar falsificar

Buscar contraejemplos

Devil's Advocate

Red Team

Steelman

Hipótesis alternativa

Ataque de supuestos

Ataque de evidencia

Ataque de causalidad

Ataque de consistencia

Ataque de completitud

Buscar evidencia negativa

Buscar información que invalide la hipótesis


Esto es especialmente importante para investigación.

Patrón

HIPÓTESIS
   ↓
EVIDENCIA A FAVOR
   ↓
GENERAR ATAQUE
   ↓
BUSCAR CONTRAEJEMPLOS
   ↓
BUSCAR FUENTES CONTRARIAS
   ↓
RECALCULAR CONFIANZA


---

2. Operadores cognitivos avanzados que te faltan

Yo ampliaría tu lista con estos.

Exploración

Sondear

Explorar

Ramificar

Expandir hipótesis

Generar alternativas

Buscar anomalías

Detectar huecos

Descubrir variables ocultas


Compresión

Resumir

Destilar

Cristalizar

Extraer invariantes

Reducir ruido

Eliminar redundancia

Consolidar


Expansión

Elaborar

Simular

Proyectar

Extrapolar

Generar escenarios

Construir alternativas


Verificación

Confirmar

Refutar

Triangular

Corroborar

Reproducir

Validar

Testear

Auditar

Comparar fuentes


Metacognición

Este bloque es uno de los más importantes para tu kernel.

¿Qué sé?

¿Qué no sé?

¿Qué estoy suponiendo?

¿Qué evidencia falta?

¿Qué puede estar mal?

¿Cuál es mi confianza?

¿Debo seguir investigando?

¿Debo cambiar de estrategia?

¿Debo detenerme?


Esto puede funcionar como un Meta-Controller.


---

3. El sistema que realmente recomiendo para tu agente

No usaría una cadena fija como:

Pensar
↓
Analizar
↓
Refutar
↓
Responder

Eso desperdicia recursos.

Usaría un grafo dinámico de operadores cognitivos.

┌───────────────┐
                    │ INPUT / TASK  │
                    └───────┬───────┘
                            │
                    ┌───────▼───────┐
                    │ UNDERSTANDING │
                    │ DESCOMPOSER   │
                    └───────┬───────┘
                            │
             ┌──────────────┼──────────────┐
             ▼              ▼              ▼
        INVESTIGATE      REASON        RETRIEVE
             │              │              │
             └──────────────┼──────────────┘
                            ▼
                    ┌───────────────┐
                    │ HYPOTHESIS    │
                    │ GRAPH         │
                    └───────┬───────┘
                            │
                  ┌─────────┴─────────┐
                  ▼                   ▼
             SUPPORT              REFUTATION
             SEARCH               SEARCH
                  │                   │
                  └─────────┬─────────┘
                            ▼
                    TRIANGULATION
                            │
                            ▼
                    CONFIDENCE ENGINE
                            │
                ┌───────────┼───────────┐
                ▼           ▼           ▼
              RETRY       DEEPEN      FINALIZE

Esto es mucho más adecuado para YAIWES.


---

4. ¿Esto debe estar dentro del Kernel?

Mi conclusión: parcialmente.

No pondría todos esos procesos directamente dentro del kernel del modelo.

Separaría tres niveles.


---

NIVEL 1 — Kernel cognitivo

Debe ser pequeño y estable.

COGNITIVE KERNEL
│
├── State Machine
├── Goal Manager
├── Cognitive Scheduler
├── Confidence Engine
├── Stop Conditions
├── Memory Interface
├── Tool Interface
└── Policy / Safety Gates

El kernel no piensa directamente.

El kernel decide:

QUÉ proceso cognitivo ejecutar
CUÁNDO ejecutarlo
CUÁNTAS veces
CON QUÉ recursos
CUÁNDO detenerlo


---

5. Nivel 2 — Cognitive Operators

Aquí pondría exactamente tu lista.

COGNITIVE OPERATORS
│
├── ANALYZE
├── DECOMPOSE
├── INVESTIGATE
├── RETRIEVE
├── REFUTE
├── TRIANGULATE
├── CALIBRATE
├── WEIGH
├── FILTER
├── COMPARE
├── SIMULATE
├── VISUALIZE
├── CRYSTALLIZE
├── VERIFY
├── RECALL_MEMORY
└── UPDATE_CONTEXT

Cada uno debería ser un módulo.

Por ejemplo:

/operators/
    analyze
    refute
    triangulate
    investigate
    calibrate
    synthesize
    crystallize

Pero no necesariamente cada módulo necesita un LLM.

Algunos pueden ser 100 % deterministas.


---

6. Nivel 3 — Modelo de IA

El modelo entra como motor cognitivo intercambiable.

COGNITIVE KERNEL
        │
        ▼
COGNITIVE OPERATOR
        │
        ▼
MODEL ROUTER
        │
 ┌──────┼──────────┐
 ▼      ▼          ▼
LLM A  LLM B     LOCAL

Esto coincide bastante con la arquitectura moderna de agent harness: Anthropic describe la separación entre el loop del agente, runtime, MCP y biblioteca de Skills, donde el loop decide, el runtime ejecuta, MCP conecta y las Skills aportan conocimiento procedimental. 

Para tu arquitectura:

YAIWES KERNEL
      ↓
Cognitive Scheduler
      ↓
Operator Selection
      ↓
Skill / Tool / Model Selection
      ↓
Execution
      ↓
Verification
      ↓
Memory


---

7. Lo que hace Claude/Fable 5 y por qué no debes copiar literalmente el CoT

Hay una distinción importante.

La documentación actual de Claude Fable 5/Mythos 5 indica que el pensamiento adaptativo está activado, pero el chain of thought crudo no se devuelve; se pueden obtener resúmenes o bloques omitidos según la configuración. 

Por eso, intentar reconstruir literalmente:

Claude piensa:
Paso 1
Paso 2
Paso 3
...

no es la mejor arquitectura.

Lo que la comunidad está haciendo es copiar el comportamiento observable, no necesariamente el razonamiento interno.

Ejemplos:

ACKNOWLEDGE → OBSERVE → EXECUTE → VERIFY

Un repositorio reciente llamado Fable5res intenta destilar patrones observables de sesiones de Fable 5 y empaquetarlos como Skills reutilizables, enfatizando lectura antes de editar, ejecución y verificación posterior. Eso debe tratarse como una implementación comunitaria, no como una reproducción oficial de la arquitectura interna de Anthropic. 

Otro proyecto de orquestación de Skills usa explícitamente delegación, lectura, verificación de premisas y selección de workers según la carga. 


---

8. Los principales sistemas de razonamiento externos disponibles

1. Chain of Thought

Problema
↓
Paso A
↓
Paso B
↓
Conclusión

Útil para:

matemáticas

análisis

planificación


Limitación: lineal.


---

2. Self-Consistency

Pregunta
 ├── Reasoning A
 ├── Reasoning B
 ├── Reasoning C
 └── Reasoning D
          ↓
      VOTACIÓN
          ↓
       RESULTADO


---

3. Tree of Thoughts

TASK
               │
      ┌────────┼────────┐
      A        B        C
      │        │        │
    A1 A2    B1 B2    C1 C2
               │
            PRUNING
               │
           BEST PATH

Hay implementaciones open source plug-and-play para agentes ToT. 


---

4. Graph of Thoughts

Más adecuado para tu sistema.

A
      / \
     B---C
      \ /
       D
       │
       E

Permite:

fusionar ramas

reutilizar conclusiones

detectar contradicciones

mantener dependencias


Para investigación compleja, prefiero Graph of Thoughts sobre una cadena.


---

9. Reflexion

Muy importante para tu arquitectura.

EXECUTE
   ↓
OBSERVE
   ↓
EVALUATE
   ↓
FAILURE?
 ┌─────┴─────┐
 NO         YES
 │            │
 FINAL      REFLECT
              │
           UPDATE
              │
            RETRY

Las implementaciones comunitarias de Reflexion con LangGraph siguen precisamente el patrón de ejecutar, evaluar el resultado, analizar fallos, reflexionar, actualizar conocimiento y volver a intentar. 


---

10. LATS — Language Agent Tree Search

Este es particularmente interesante.

Combina:

Tree Search
+
Planning
+
Reflection
+
Evaluation
+
External Feedback

LangGraph documenta implementaciones donde se generan trayectorias, se evalúan mediante reflexión y feedback del entorno, y se continúa expandiendo el árbol hasta resolver la tarea o alcanzar un límite. 

Para YAIWES:

PLAN
 ↓
EXECUTE
 ↓
OBSERVE
 ↓
SCORE
 ↓
REFLECT
 ↓
BRANCH?
 ↓
BEST PATH


---

11. Self-Refine

DRAFT
  ↓
CRITIC
  ↓
REFINE
  ↓
CRITIC
  ↓
REFINE
  ↓
FINAL

Esto encaja directamente con:

Refinando

Afinando

Tamizando

Cristalizando



---

12. Decomposition / Least-to-Most

OBJETIVO GRANDE
      ↓
DIVIDIR
      ↓
SUBPROBLEMAS
      ↓
ORDENAR DEPENDENCIAS
      ↓
RESOLVER
      ↓
INTEGRAR

Oracle documenta una capa open source de "Agent Reasoning" que agrupa CoT, Self-Consistency, Tree of Thoughts, ReAct, Self-Reflection, Decomposition/Least-to-Most y loops de refinamiento. 

Esto es muy cercano a lo que estás describiendo.


---

13. Investigación: cómo la comunidad convierte razonamiento en código

La tendencia que encontré se puede dividir en cinco enfoques.

A. Reasoning como workflow

Prompt
↓
Reason
↓
Critique
↓
Improve


---

B. Reasoning como grafo

StateGraph
│
├── Research
├── Analyze
├── Refute
├── Verify
└── Finalize


---

C. Reasoning como agentes especializados

Research Agent
       │
       ▼
Analyst Agent
       │
       ▼
Critic Agent
       │
       ▼
Verifier Agent


---

D. Reasoning como Skills

Esto es probablemente el mejor enfoque para tu proyecto.

Skill:
REFUTATION

Trigger:
contradictory evidence

Inputs:
hypothesis
evidence

Process:
search counter evidence
score confidence

Output:
updated belief

Las Skills modernas pueden cargarse progresivamente: las instrucciones se activan cuando una Skill es relevante y recursos adicionales se cargan sólo cuando son necesarios. 

Esto encaja exactamente con tu objetivo de no cargar todo el sistema ni todas las librerías al mismo tiempo.


---

14. Reasoning datasets disponibles

Sí existen datasets.

Encontré, por ejemplo:

Claude Reasoning Dataset

Dataset comunitario con aproximadamente 132k filas que incluye:

question
answer
thought

y mezcla razonamiento, matemáticas y código. 

Advertencia importante

Yo no usaría esos traces como verdad absoluta ni como memoria de producción.

Los usaría para:

investigar patrones

extraer operadores

entrenar clasificadores

construir Skills

generar benchmarks


No para copiar literalmente cadenas de pensamiento.


---

Verified Reasoning Data

Existe también trabajo comunitario de reasoning traces donde la salida final se conserva únicamente si pasa un verificador determinista. 

Este enfoque me parece mucho más compatible contigo:

GENERATE
   ↓
REASON
   ↓
EXECUTE VERIFIER
   ↓
PASS?
  /    \
YES     NO
 │       │
STORE   REFUTE / RETRY

Para tu arquitectura, esto es superior a almacenar simplemente texto de razonamiento.


---

15. Sobre OpenMythos

Sí: existe código descargable llamado OpenMythos.

El repositorio principal que encontré es:

[OpenMythos — GitHub](https://github.com/kyegomez/OpenMythos?utm_source=chatgpt.com)

Hay que hacer una precisión crítica:

> OpenMythos NO es la arquitectura oficial liberada por Anthropic.



El propio proyecto se define como una reconstrucción teórica comunitaria basada en investigación pública y especulación, sin afiliación con Anthropic. 

La arquitectura implementada es:

INPUT
  ↓
PRELUDE
  ↓
RECURRENT BLOCK
  ↻
  ↻
  ↻
  ↓
CODA
  ↓
OUTPUT

Utiliza una arquitectura denominada Recurrent-Depth Transformer, donde un bloque se reutiliza en múltiples iteraciones. 

Tiene características como:

bucle recurrente

profundidad variable

parada adaptativa

MoE

GQA / MLA

LoRA por profundidad

inyección repetida del input





---

16. ¿OpenMythos debe entrar en tu Kernel?

Mi respuesta: NO directamente.

OpenMythos está en otra capa.

┌─────────────────────────────────────┐
│         YAIWES COGNITIVE OS         │
├─────────────────────────────────────┤
│ Cognitive Kernel                    │
│                                     │
│ Goal Manager                        │
│ Cognitive Scheduler                 │
│ Confidence Engine                   │
│ Stop Controller                     │
├─────────────────────────────────────┤
│ Cognitive Operators                 │
│                                     │
│ Analyze                             │
│ Refute                              │
│ Triangulate                         │
│ Investigate                         │
│ Verify                              │
│ Crystallize                         │
├─────────────────────────────────────┤
│ Reasoning Engines                   │
│                                     │
│ ReAct                               │
│ ToT                                 │
│ Reflexion                           │
│ LATS                                │
│ Self-Refine                         │
│ Graph Reasoning                     │
├─────────────────────────────────────┤
│ MODEL ABSTRACTION                   │
│                                     │
│ Local LLM                           │
│ API LLM                             │
│ OpenMythos experimental             │
│ Future reasoning models             │
└─────────────────────────────────────┘

OpenMythos sería un Reasoning Model / Experimental Backend, no tu controlador central.


---

17. Arquitectura que recomiendo para tu agente investigador

La llamaría:

Cognitive Research Loop Engine

USER OBJECTIVE
                      │
                      ▼
             CONTEXT UNDERSTANDING
                      │
                      ▼
             MEMORY RETRIEVAL
                      │
                      ▼
             QUESTION DECOMPOSER
                      │
                      ▼
              HYPOTHESIS GRAPH
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
      INVESTIGATE   REASON      RETRIEVE
          │           │           │
          └───────────┼───────────┘
                      ▼
                 TRIANGULATE
                      │
                      ▼
                    REFUTE
                      │
                      ▼
               VERIFY EVIDENCE
                      │
                      ▼
              CONFIDENCE SCORE
                      │
            ┌─────────┴─────────┐
            │                   │
         LOW CONF.           HIGH CONF.
            │                   │
            ▼                   ▼
     EXPAND / RETRY        CRYSTALLIZE
            │                   │
            └──────────┬────────┘
                       ▼
                   SYNTHESIS
                       │
                       ▼
                    MEMORY
                       │
                       ▼
                    OUTPUT


---

18. Tu lista reorganizada como sistema ejecutable

Tu lista original puede convertirse en estas 10 fases.

F1 — Comprensión

Entender
Contextualizar
Recuperar memoria
Identificar objetivo

F2 — Exploración

Sondear
Investigar
Buscar
Descubrir

F3 — Descomposición

Desenredar
Separar
Clasificar
Indexar

F4 — Análisis

Analizar
Calcular
Descifrar
Relacionar

F5 — Hipótesis

Contemplar
Visualizar
Modelar
Proponer alternativas

F6 — Adversarial

Refutar
Contraargumentar
Buscar contradicciones
Falsificar

F7 — Verificación

Confirmar
Triangular
Corroborar

F8 — Evaluación

Sopesar
Tamizar
Calibrar
Puntuar confianza

F9 — Convergencia

Afinar
Refinar
Alinear
Cristalizar

F10 — Metacognición

¿Está resuelto?
¿Falta evidencia?
¿Hay contradicción?
¿Debo investigar más?
¿Debo detenerme?


---

Conclusión

Para YAIWES, yo no implementaría una “cadena de pensamiento” textual.

Implementaría:

DETERMINISTIC COGNITIVE KERNEL
            +
DYNAMIC COGNITIVE OPERATORS
            +
REASONING ENGINE REGISTRY
            +
EXTERNAL VERIFIERS
            +
HYPOTHESIS / EVIDENCE GRAPH
            +
MEMORY
            +
MODEL-AGNOSTIC ROUTER

La pieza central sería un Cognitive Scheduler determinista que decide qué operador activar según estado, evidencia, incertidumbre, contradicción y presupuesto de recursos. El LLM razona dentro de tareas concretas; el sistema externo controla el proceso.

Puedo continuar con una segunda investigación centrada exclusivamente en repositorios open source descargables de reasoning engines, cognitive operators, Reflexion, LATS, Graph/Tree of Thoughts, datasets y capas externas, y .clasificarlos por compatibilidad directa con el kernel de YAIWES



taxonomía cognitiva.

A. Razonamiento estructural

B. Razonamiento adversarial

C. Sistema coda
INPUT
  ↓
PRELUDE
  ↓
RECURRENT BLOCK
  ↻
  ↻
  ↻
  ↓
CODA
  ↓
OUTPUT

Repetición — URLs completas y visibles de cada repositorio

1. Workflow / Kernel de investigación

Repositorio: deep-research-agent-langchain

URL visible completa:

[https://github.com/waqasraza123/deep-research-agent-langchain](https://github.com/waqasraza123/deep-research-agent-langchain?utm_source=chatgpt.com)

Cubre principalmente:

IDENTIFICAR OBJETIVO
↓
SOURCE DISCOVERY
↓
RETRIEVAL
↓
HYPOTHESIS
↓
EVIDENCE
↓
VERIFICATION
↓
EVALUATION
↓
SYNTHESIS

Artefactos/workflow:

workflow_template
workflow_compiled
workflow_execution_plan
workflow_dependency_graph
workflow_artifact_contracts
verification_tasks
verification_results
confidence_calibration


---

2. Workflow de investigación estructurada

Repositorio: wshuyi/deep-research

URL visible completa:

[https://github.com/wshuyi/deep-research](https://github.com/wshuyi/deep-research?utm_source=chatgpt.com)

Workflow:

IDENTIFICAR PROBLEMA
↓
CLASIFICAR
↓
DESCOMPONER
↓
BUSCAR FUENTES
↓
EXTRAER EVIDENCIA
↓
COMPARAR
↓
ALINEAR
↓
CONCLUIR
↓
VERIFICAR
↓
VALIDAR

Útil para:

F1 Identificar objetivo
F2 Exploración
F3 Descomposición
F4 Análisis
F7 Verificación
F9 Convergencia


---

3. Workflow adversarial / contradicciones / confianza

Repositorio: HadiFrt20/deepresearch

URL visible completa:

[https://github.com/HadiFrt20/deepresearch](https://github.com/HadiFrt20/deepresearch?utm_source=chatgpt.com)

Workflow:

OBJETIVO
↓
DESCOMPONER
↓
RESEARCH
↓
VALIDATE
↓
PROVENANCE
↓
ADVERSARY
↓
CONTRADICTION SEARCH
↓
CROSS REFERENCE
↓
TRUST SCORE
↓
REPORT

Cubre directamente:

F6 ADVERSARIAL

Refutar
Contraargumentar
Buscar contradicciones
Falsificar

F7 VERIFICACIÓN

Confirmar
Triangular
Corroborar

F8 EVALUACIÓN

Sopesar
Tamizar
Calibrar
Puntuar confianza


---

4. Graph of Thoughts — grafo de razonamiento

Repositorio oficial: spcl/graph-of-thoughts

URL visible completa:

[https://github.com/spcl/graph-of-thoughts](https://github.com/spcl/graph-of-thoughts?utm_source=chatgpt.com)

Workflow:

INPUT
↓
GENERATE
↓
BRANCH
├── HIPÓTESIS A
├── HIPÓTESIS B
└── HIPÓTESIS C
↓
AGGREGATE
↓
EVALUATE
↓
REFINE
↓
OUTPUT

Útil para:

F3 Desenredar
F4 Relacionar
F5 Proponer alternativas
F8 Evaluar
F9 Afinar


---

5. LATS — Language Agent Tree Search

Repositorio oficial: lapisrocks/LanguageAgentTreeSearch

URL visible completa:

[https://github.com/lapisrocks/LanguageAgentTreeSearch](https://github.com/lapisrocks/LanguageAgentTreeSearch?utm_source=chatgpt.com)

Workflow:

TASK
↓
GENERATE
↓
EXPAND
↓
EVALUATE
↓
REFLECT
↓
SELECT
↓
CONTINUE / STOP

Aporta:

Exploración
Ramificación
Evaluación
Reflexión
Selección
Stop conditions


---

6. Reflexion — metacognición y memoria

Repositorio oficial: noahshinn/reflexion

URL visible completa:

[https://github.com/noahshinn/reflexion](https://github.com/noahshinn/reflexion?utm_source=chatgpt.com)

Workflow:

EXECUTE
↓
OBSERVE RESULT
↓
EVALUATE
↓
REFLECT
↓
STORE REFLECTION
↓
RETRY

Corresponde directamente a:

F10 METACOGNICIÓN

¿Está resuelto?
↓
NO
↓
¿Qué salió mal?
↓
¿Qué evidencia falta?
↓
¿Qué cambiar?
↓
MEMORY
↓
RETRY


---

7. Self-Refine — convergencia y refinamiento

Repositorio oficial: madaan/self-refine

URL visible completa:

[https://github.com/madaan/self-refine](https://github.com/madaan/self-refine?utm_source=chatgpt.com)

Workflow:

GENERATE
↓
FEEDBACK
↓
REFINE
↓
FEEDBACK
↓
REFINE
↓
FINAL

Útil para:

F9

Afinar
Refinar
Alinear
Cristalizar


---

8. MindMap — clasificación, relación y grafo de conocimiento

Repositorio: wyl-willing/MindMap

URL visible completa:

[https://github.com/wyl-willing/MindMap](https://github.com/wyl-willing/MindMap?utm_source=chatgpt.com)

Útil para:

F3

Clasificar
Indexar

F4

Relacionar

F5

Visualizar
Modelar


---

9. OpenMythos — Prelude → Recurrent Block → Coda

Repositorio: vegafoundation/openmythos

URL visible completa:

[https://github.com/vegafoundation/openmythos](https://github.com/vegafoundation/openmythos?utm_source=chatgpt.com)

Arquitectura:

INPUT
  ↓
PRELUDE
  ↓
RECURRENT BLOCK
  ↻
  ↻
  ↻
  ↓
CODA
  ↓
OUTPUT

Esto corresponde a una capa diferente del workflow F1–F10.

YAIWES COGNITIVE WORKFLOW
          ↓
MODEL REASONING BACKEND
          ↓
PRELUDE
          ↓
RECURRENT BLOCK
          ↻
          ↻
          ↻
          ↓
CODA
          ↓
OUTPUT


---

10. Workflow completo objetivo para YAIWES

Los repositorios anteriores cubren conjuntamente este workflow:

F1 — IDENTIFICAR OBJETIVO
        │
        ▼
F2 — EXPLORACIÓN
Sondear
Investigar
Buscar
Descubrir
        │
        ▼
F3 — DESCOMPOSICIÓN
Desenredar
Separar
Clasificar
Indexar
        │
        ▼
F4 — ANÁLISIS
Analizar
Calcular
Descifrar
Relacionar
        │
        ▼
F5 — HIPÓTESIS
Contemplar
Visualizar
Modelar
Proponer alternativas
        │
        ▼
F6 — ADVERSARIAL
Refutar
Contraargumentar
Buscar contradicciones
Falsificar
        │
        ▼
F7 — VERIFICACIÓN
Confirmar
Triangular
Corroborar
        │
        ▼
F8 — EVALUACIÓN
Sopesar
Tamizar
Calibrar
Puntuar confianza
        │
        ▼
F9 — CONVERGENCIA
Afinar
Refinar
Alinear
Cristalizar
        │
        ▼
F10 — METACOGNICIÓN
¿Está resuelto?
¿Falta evidencia?
¿Hay contradicción?
¿Debo investigar más?
¿Debo detenerme?
        │
        ├── NO → volver dinámicamente a F2/F4/F5/F6
        │
        ▼
      OUTPUT

URLs visibles completas — lista limpia

1. [https://github.com/waqasraza123/deep-research-agent-langchain](https://github.com/waqasraza123/deep-research-agent-langchain?utm_source=chatgpt.com)


2. [https://github.com/wshuyi/deep-research](https://github.com/wshuyi/deep-research?utm_source=chatgpt.com)


3. [https://github.com/HadiFrt20/deepresearch](https://github.com/HadiFrt20/deepresearch?utm_source=chatgpt.com)


4. [https://github.com/spcl/graph-of-thoughts](https://github.com/spcl/graph-of-thoughts?utm_source=chatgpt.com)


5. [https://github.com/lapisrocks/LanguageAgentTreeSearch](https://github.com/lapisrocks/LanguageAgentTreeSearch?utm_source=chatgpt.com)


6. [https://github.com/noahshinn/reflexion](https://github.com/noahshinn/reflexion?utm_source=chatgpt.com)


7. [https://github.com/madaan/self-refine](https://github.com/madaan/self-refine?utm_source=chatgpt.com)


8. [https://github.com/wyl-willing/MindMap](https://github.com/wyl-willing/MindMap?utm_source=chatgpt.com)


9. [https://github.com/vegafoundation/openmythos](https://github.com/vegafoundation/openmythos?utm_source=chatgpt.com)



Puedo hacer ahora la auditoría forense archivo por archivo de estos repositorios y marcar únicamente las funciones, clases y workflows que realmente existen en el código para F1–F10.



📌🛑🛑🛑🛑🛑
Metes solo los que aparecen en esta lista en la siguiente dirección 

Destino ubicación. En el repo de agentes motores Wordflow YAIWES 

Creas una raíz nueva llamado =
Core kernel razonamiento repo para Yaiwes

Metes todo eso dentro de en la lista de descarga 

Incluye esto a la lista de descarga 
Del wordflow github acción los 86 que te faltan + 

La siguiente lista

deep-research-agent-langchain — el más completo para tu arquitectura
GitHub — deep-research-agent-langchain⁠�

wshuyi/deep-research — workflow completo de investigación con verificación independiente
GitHub — Deep Research 8-step⁠�




completas
https://github.com/RightNow-AI/ouroboros⁠�
https://github.com/ccapps42/CART⁠�
https://github.com/OpenCoven/open-fable⁠�
https://github.com/duongtrongnguyen123/recurrent-depth-ttc⁠�
https://github.com/rd-vla/rd-vla⁠�



HadiFrt20/deepresearch — adversarial + provenance + confidence
GitHub — deepresearch⁠�


lapisrocks/LanguageAgentTreeSearch — planificación + evaluación + búsqueda
GitHub — LATS oficial ICML 2024⁠�



madaan/self-refine — refinamiento iterativo
GitHub — Self-Refine oficial⁠�


wyl-willing/MindMap — conocimiento estructurado + Graph of Thoughts
GitHub — MindMap⁠�


Graph of Thoughts — grafo de razonamiento
Repositorio oficial: spcl/graph-of-thoughts
URL visible completa:
https://github.com/spcl/graph-of-thoughts⁠�

LATS — Language Agent Tree Search
Repositorio oficial: lapisrocks/LanguageAgentTreeSearch
URL visible completa:
https://github.com/lapisrocks/LanguageAgentTreeSearch⁠�


Reflexion — metacognición y memoria
Repositorio oficial: noahshinn/reflexion
URL visible completa:
https://github.com/noahshinn/reflexion⁠�


MindMap — clasificación, relación y grafo de conocimiento
Repositorio: wyl-willing/MindMap
URL visible completa:
https://github.com/wyl-willing/MindMap⁠�

OpenMythos — Prelude → Recurrent Block → Coda
Repositorio: vegafoundation/openmythos
URL visible completa:
https://github.com/vegafoundation/openmythos⁠�











ByteDance — DeerFlow 2.0

https://github.com/bytedance/deer-flow



OpenManus / MetaGPT ecosystem
URL COMPLETA
https://github.com/FoundationAgents/OpenManus⁠�

CAMEL-AI — Multi-Agent Kernel
URL COMPLETA
https://github.com/camel-ai/camel⁠�



Revisa que no está repetido en lanlista de los más de 90


Chain-of-Thought
Repositorio de referencia:
https://github.com/openai/simply-code⁠�

Tree of Thoughts
Código
https://github.com/kyegomez/tree-of-thoughts⁠�



Graph of Thoughts
Código
https://github.com/spcl/graph-of-thoughts⁠�

Reflexion
Repositorio oficial
https://github.com/noahshinn/reflexion⁠�

LATS — Language Agent Tree Search
Repositorio oficial
https://github.com/lapisrocks/LanguageAgentTreeSearch⁠�


Self-Refine
Repositorio original
https://github.com/madaan/self-refine⁠�


Self-Refine como runtime reutilizable
https://github.com/Birfy/agentdescent⁠�


FABLE 5 — REPOSITORIOS CON CÓDIGO / DATOS ÚTILES
Fable5res
https://github.com/ahmdd4vd/Fable5res⁠�


Fable-5-traces
https://huggingface.co/datasets/Kuberwastaken/Fable-5-traces⁠�


Fable5 Methodology
https://github.com/UnpaidAttention/fable5-methodology⁠�


OPENMYTHOS — AUDITORÍA DEL CÓDIGO
REPOSITORIO PRINCIPAL
https://github.com/kyegomez/OpenMythos⁠�


central auditado
Archivo:
https://github.com/kyegomez/OpenMythos/blob/main/open_mythos/main.py⁠�


OpenMythos — variantes con código
Fork con material adicional
https://github.com/Bananefre/OpenMythos⁠�


MLX
https://github.com/DeadByDawn101/OpenMythos-MLX⁠�
Skill
https://github.com/SarthakDz/OpenMythos-Skill⁠�

Dagu.
Repositorio / descarga directa:
https://github.com/dagu-org/dagu⁠�


DeepDive — el más cercano a tu flujo de investigación
Repositorio:
https://github.com/Socialpranker/deepdive⁠


Binex — workflow determinista de razonamiento
Repositorio:
https://github.com/Alexli18/binex⁠�


pi-task — refine → research → grill → compose → critique
Repositorio:
https://github.com/mjasnikovs/pi-task⁠�





LoomFlow — colección ejecutable de patrones
Repositorio:
https://github.com/Anurich/LoomFlow⁠�



UX Research Pipeline — triangulación + casos disconfirmatorios
Repositorio:
https://github.com/shipaleks/ux-research-pipeline⁠


Reflexion — loop de aprendizaje/verificación
Repositorio oficial:
https://github.com/noahshinn/reflexion⁠�

Graph of Thoughts — razonamiento como grafo
Repositorio:
https://github.com/spcl/graph-of-thoughts⁠�

Framework of Thoughts
Repositorio:
https://github.com/fjfricke/framework-of-thoughts⁠


Self-Refine
Repositorio:
https://github.com/madaan/self-refine⁠�

Self-Consistency
Repositorio:
https://github.com/akpe12/Self-consistency⁠�


VeriTrace — evidencia como grafo verificable
Repositorio:
https://github.com/noah-art3mis/veritrace⁠�

Repositorio adicional: AI-Agent-Skills
Repositorio:
https://github.com/sreerevanth/AI-Agent-Skills⁠�

cognitivas, no de documentos:
https://github.com/ejentum⁠�





Metes en la raíz de los agentes descargados en esa raíz 

Open hand 
Open code 
Dabo 
Grock 
Open claw que ya está en el repo 
Temporal está en el repo de agentes lo mueves con los demás agentes en ese repo en la raíz de download code con los demás agentes sin tocar los repo los code de los buscadores de información que están en ese repo de los 20 que se descargaron puedes verificar con el github acción anteriores de la descarga o revisando el code de github acción en el skills que se uso hay sale la lista 
No tocas los programas de búsqueda 


Metes a esta lista sentir de 

Destino ubicación. En el repo de agentes motores Wordflow YAIWES 

Creas una raíz nueva llamado =
Core kernel razonamiento repo para Yaiwes 

