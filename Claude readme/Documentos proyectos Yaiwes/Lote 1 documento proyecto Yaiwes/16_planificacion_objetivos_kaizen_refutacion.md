# DOCUMENTO 2/4 — Sistema avanzado de planificación de objetivos, tareas y refutación
**Fusiona: gestión de proyectos open source + PDCA/Kaizen (Toyota) + cadenas de refutación formal + tu propio sistema de emojis (GOALS/TASKS/WORKFLOW/PIPELINE ya diseñado)**

## 1. La base: PDCA de Toyota es literalmente tu propio ciclo, ya con 70 años de uso probado

**Plan → Do → Check → Act (PDCA / Ciclo de Deming)** es el origen real de "definir objetivo → ejecutar → verificar → ajustar y repetir". Tu propio sistema de emojis (🎯 OBJETIVO → 🏗️ TAREA → 💡 PLANIFICAR → 👣 PASO → 🧩 RESULTADOS) ya es una implementación de PDCA, solo que sin el nombre. Vale la pena saberlo porque significa que tu diseño **ya está alineado con el sistema de mejora continua más probado en la historia de la manufactura** — no hay que rediseñarlo, hay que completarlo.

## 2. Diez componentes de Toyota/Kaizen convertidos a código, con ubicación exacta

| # | Concepto Toyota | Qué hace | Cómo se convierte en código | Dónde vive |
|---|---|---|---|---|
| 1 | **PDCA** | El ciclo completo de mejora | Es tu `persistent_solver` completo (Prelude=Plan, Recurrente=Do+Check, Coda=Act) — ya lo tienes | `reasoning-kernel/persistent_solver/` |
| 2 | **Andon (cordón de parada)** | Cualquier trabajador puede detener toda la línea si ve un defecto | Tu `fail_closed.py` ya existente + `circuit-breaker` — cualquier validador puede parar el pipeline completo, no solo advertir | `resource-governance/circuit-breaker/` |
| 3 | **Jidoka (automatización con toque humano)** | Detente y arregla la causa raíz de inmediato, no dejes pasar el defecto "para después" | Aplica el algoritmo "5 Whys" (ya en tu catálogo de 105) automáticamente cuando `Andon` se activa, antes de reintentar | `control-governance/forensic-core/` |
| 4 | **Poka-yoke (a prueba de errores)** | Diseña el proceso para que sea físicamente imposible cometer el error | Tus validadores de schema (PydanticAI, jsonschema) — rechazan la entrada antes de que pueda causar daño, no después | `definition-registry/schema-contracts/` |
| 5 | **Kanban (tablero visual con límite de trabajo en curso)** | Visualiza el flujo, limita cuántas tareas están "en proceso" a la vez | **Wekan**, **Focalboard**, o **Taiga** (open source, con API REST real) — tu `Scheduler.max_parallel` ya es el límite de WIP (Work In Progress), solo falta la vista | `execution-orchestration/state-machine-executor/` |
| 6 | **Heijunka (nivelación de producción)** | Reparte la carga de trabajo de forma pareja, no en picos | Tu `Time-Wheel` + `resource-broker-gate` ya diseñados — asegúrate de que no todas las tareas lleguen a la misma ventana de tiempo | `kernel-principal/resource-governance/` |
| 7 | **Kaizen (mejora continua incremental)** | Pequeñas mejoras constantes, registradas y medidas | Es literalmente tu `selector_ruleta.py` subiendo la probabilidad de lo que funciona — cada ciclo del kernel ya practica Kaizen automáticamente | `persistent_solver/selector_ruleta.py` |
| 8 | **Value Stream Mapping** | Mapea cada paso de principio a fin, identificando cuáles agregan valor y cuáles son desperdicio | Tu grafo de dependencias (`networkx`) + análisis de qué pasos casi nunca fallan (candidatos a eliminar/simplificar) | `execution-orchestration/dag-executor/` |
| 9 | **5S (clasificar, ordenar, limpiar, estandarizar, sostener)** | Organización física del espacio de trabajo | Aplicado a código: elimina placeholders muertos, estandariza nombres de archivo, automatiza el chequeo (ya lo hicimos con la auditoría forense) | Aplica a todo el repo, revisar en cada auditoría periódica |
| 10 | **KPI en cascada (Hoshin Kanri)** | Los objetivos generales se descomponen en metas medibles por nivel | Tu `goal-dual-driver` (objetivo primario/secundarios) + una métrica de éxito numérica por cada nivel de la jerarquía | `reasoning-kernel/goal-dual-driver/` |

## 3. La cadena de refutación formal (revisión → respuesta → resultado → refutación → repetición)

Esto que pediste tiene nombre real en lógica formal: **Argumentación Computacional** — específicamente el **Abstract Argumentation Framework de Dung** (1995), la base teórica de cómo representar ataques y defensas entre argumentos de forma que un sistema pueda decidir cuál "gana" sin ambigüedad. Y hay una versión ya aplicada a IA: **"AI Safety via Debate"** (Irving et al., OpenAI/DeepMind) — dos agentes argumentan posiciones opuestas, un tercero (juez) decide, exactamente tu patrón CRITIC→COUNTER_CRITIC→JUDGE.

**Estructura formal recomendada para tu cadena R (Revisión-Respuesta-Resultado-Refutación-Repetición):**

```
R1 REVISIÓN:    Un módulo propone una solución con evidencia declarada.
R2 RESPUESTA:   Un segundo módulo (nunca el mismo) ataca la solución citando
                exactamente qué evidencia o supuesto considera débil.
R3 RESULTADO:   Se clasifica el ataque: refutado / parcialmente válido / fatal.
R4 REFUTACIÓN:  Si es fatal, la solución original se descarta — no se "arregla
                a medias", se regresa a generar una nueva.
R5 REPETICIÓN:  Máximo N ciclos (usa tu REPLANNER_LOOP ya definido, límite 3-5).
                Si tras N ciclos ninguna sobrevive, sube el score de dificultad
                y activa persistent_solver con más presupuesto.
```

Esto es una extensión directa de tu `BLOQUE_X` (Critic→Counter-Critic→Failure Simulator→V1/V2/V3→Judge) que ya tenías diseñado — solo le da nombre formal (Dung Framework) y un límite de repetición explícito para que no sea infinito.

## 4. Diez componentes open source de gestión de proyectos para fusionar

| # | Herramienta | Fortaleza específica | Cómo integrar |
|---|---|---|---|
| 1 | **OpenProject** | Gantt, WBS (work breakdown structure), API REST completa | Usa su modelo de "work packages" como inspiración directa para tu `task-definition/` — ya resuelve descomposición jerárquica de tareas |
| 2 | **Taiga** | Scrum/Kanban ágil, se integra con GitHub/GitLab nativamente | Si tu flujo de trabajo se parece a sprints, usa su API para sincronizar el estado de tus TASKS.md automáticamente |
| 3 | **Focalboard** | Kanban tipo Notion, vistas múltiples (tabla, galería, calendario) | Buena opción si quieres una interfaz visual ligera sin montar infraestructura pesada |
| 4 | **Plane** | Moderno, hackeable, con capacidades de IA emergentes en 2026 | El más fácil de extender con código propio si planeas modificarlo |
| 5 | **Redmine** | Muy extensible via plugins, veterano y estable | Bueno si prefieres algo probado por años sobre algo moderno |
| 6 | **Vikunja** | Ligero, self-hosted, mínimo esfuerzo de instalación | Para empezar rápido sin infraestructura compleja |
| 7 | **NetworkX** | Grafo de dependencias entre tareas (ya lo tienes) | El motor matemático detrás de cualquiera de las herramientas de arriba |
| 8 | **Leantime** | Alinea estrategia con ejecución, seguimiento de objetivos (goal tracking) nativo | Bueno específicamente para tu capa de `goal-dual-driver` |
| 9 | **PyHop / GTPyhop** | Planificación jerárquica de tareas (HTN, ya mencionado en documento 14) | El motor "inteligente" que decide CÓMO descomponer, mientras las herramientas de arriba solo muestran el resultado |
| 10 | **`python-constraint`** | Resolver de restricciones (CSP, ya en tu catálogo de 105) | Para cuando la planificación tiene restricciones duras (fechas límite, recursos compartidos) que un simple grafo no resuelve solo |

## Resumen

Tu propio sistema de emojis (GOALS/TASKS/WORKFLOW) ya implementa PDCA sin saberlo — lo que le faltaba era: (1) el nombre formal de la cadena de refutación (Dung Framework + AI Safety via Debate, con límite explícito de repetición), y (2) una herramienta real de gestión de proyectos (OpenProject o Taiga) detrás para no reinventar Gantt/WBS/Kanban desde cero. Todo vive bajo `definition-registry/`, `reasoning-kernel/goal-dual-driver/`, y `execution-orchestration/` — ninguna carpeta nueva, solo llenar lo que ya existe con estas piezas reales.
