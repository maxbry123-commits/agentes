# Verificación Cruzada — 5 Mejores Proyectos Open Source vs. Objective Engine v2

> **Fecha:** 2026-08-16  
> **Metodología:** Análisis comparativo de patrones arquitectónicos  
> **Proyectos analizados:** Open-Sable, PlanDB, M-APPLE-OS, Conductor, Open-Multi-Agent

---

## Proyecto 1: Open-Sable (IdeoaLabs)

**Repositorio:** https://github.com/IdeoaLabs/Open-Sable  
**Licencia:** Open Source  
**Enfoque:** Agentes autónomos con cognición avanzada

### Patrones Extraídos

| Patrón | Descripción en Open-Sable | Adopción en OE v2 |
|--------|---------------------------|-------------------|
| **Goal Hierarchy** | Árboles de objetivos padre/hijo con prioridades | ✅ ObjectiveGraph con jerarquía compuesta |
| **Deep Multi-Step Planner** | LLM descompone en DAGs de 5-15 pasos con dependencias | ✅ Plan Compiler genera DAG determinista |
| **Replanning Automático** | Hasta 3 reintentos con re-planificación | ✅ Failure Classifier + Global Replanning |
| **Ultra-Long-Term Memory** | Consolidación periódica de semanas/meses en patrones duraderos | ✅ Strategy Memory con consolidación |
| **Self-Benchmark** | 8 suites de benchmark interno cada 25 ticks | ✅ Evaluator con métricas de ejecución |
| **Inter-Agent Bridge** | Vault JSONL compartido entre agentes | ✅ Objective Memory compartible |

### Lecciones Clave

> "Open-Sable demuestra que un agente autónomo necesita no solo objetivos, sino **metacognición** (auto-benchmark, auto-mejora). OE v2 debe incluir hooks para auto-evaluación continua."

### Diferenciador de OE v2

Open-Sable es un agente completo; OE v2 es un **kernel reutilizable**. OE v2 se enfoca exclusivamente en el motor de objetivos, sin acoplar UI, voz, visión, etc.

---

## Proyecto 2: PlanDB (AgentField)

**Repositorio:** https://github.com/Agent-Field/plandb  
**Licencia:** Apache 2.0  
**Enfoque:** Issue tracker para agentes AI con grafo compuesto

### Patrones Extraídos

| Patrón | Descripción en PlanDB | Adopción en OE v2 |
|--------|-----------------------|-------------------|
| **Compound Graph** | Jerarquía + dependencias cruzadas (containment + flow) | ✅ ObjectiveGraph con cross-branch deps |
| **Pre/Postconditions** | `--pre` y `--post` en cada tarea | ✅ TaskContract con conditions verificables |
| **Atomic Claiming** | `plandb go` previene conflictos entre agentes | ✅ Worker assignment con locking |
| **Context Surfacing** | BM25 auto-surfacing de contexto relevante | ✅ Evidence Engine con retrieval |
| **Plan Adaptation** | `split`, `insert`, `pivot` mid-flight | ✅ Objective Evolution + replanning |
| **Critical Path** | `plandb critical-path` para priorizar cuellos de botella | ✅ Plan Analyzer con critical path detection |

### Lecciones Clave

> "PlanDB demuestra que los agentes necesitan **infraestructura de planificación**, no solo prompts. El concepto de 'compound graph' donde las dependencias cruzan fronteras de jerarquía es fundamental para paralelismo real."

### Diferenciador de OE v2

PlanDB es una herramienta CLI/infraestructura; OE v2 es una **biblioteca embebible** con runtime integrado. OE v2 compila a ejecución determinista, no solo rastrea tareas.

---

## Proyecto 3: M-APPLE-OS / ALAS

**Repositorio:** https://github.com/genglongling/M-APPLE-OS  
**Licencia:** MIT  
**Enfoque:** Sistema operativo multi-agente para planificación dinámica

### Patrones Extraídos

| Patrón | Descripción en M-APPLE-OS | Adopción en OE v2 |
|--------|---------------------------|-------------------|
| **Three-Layer Architecture** | Specification → Coordination → Execution | ✅ Discovery → Plan Compiler → Runtime |
| **Self-Validation** | Validación estructural, de constraints y compensación en cada paso | ✅ Plan Validator + Execution Observer |
| **Local Compensation** | Arreglo a nivel de agente sin afectar el workflow completo | ✅ Gap Analyzer con local repair |
| **Global Replanning** | Reconstrucción completa del workflow cuando la compensación local falla | ✅ Global Replanning con subgraph rebuild |
| **Rollback Support** | Reversión a estados previos válidos | ✅ Checkpoint + Rollback en Recovery |
| **Context Management** | Query/restore de contexto de ejecución por agente | ✅ Context snapshot en checkpoints |

### Lecciones Clave

> "M-APPLE-OS demuestra que la **resiliencia** no es opcional. La combinación de compensación local + replanificación global + rollback es la única forma de manejar disruption en sistemas reales. OE v2 debe implementar las tres capas."

### Diferenciador de OE v2

M-APPLE-OS está optimizado para JSSP (Job Shop Scheduling); OE v2 es **dominio-agnóstico** y diseñado para agentes LLM generalistas.

---

## Proyecto 4: Conductor OSS (Netflix)

**Repositorio:** https://github.com/conductor-oss/conductor  
**Licencia:** Apache 2.0  
**Enfoque:** Motor de workflows durable a escala de internet

### Patrones Extraídos

| Patrón | Descripción en Conductor | Adopción en OE v2 |
|--------|--------------------------|-------------------|
| **Durable Execution** | Cada paso persistido. Sobrevive crashes, restarts, network failures | ✅ Checkpointing en cada paso del DAG |
| **Deterministic by Design** | JSON definitions separan orquestación de implementación | ✅ ExecutionDAG inmutable compilado |
| **Full Replayability** | Restart desde inicio, desde tarea específica, o retry de fallo | ✅ Replay desde cualquier checkpoint |
| **Saga + Compensation** | Undo automático en orden inverso ante fallo | ✅ Rollback con compensación ordenada |
| **Dynamic at Runtime** | Dynamic forks, tasks, sub-workflows resueltos en runtime | ✅ Dynamic subgraph injection |
| **Polyglot Workers** | Workers en Java, Python, Go, JS, C#, Ruby, Rust | ✅ Worker interface agnóstica de lenguaje |
| **AI Agent Orchestration** | 14+ LLM providers, MCP, function calling, human-in-the-loop | ✅ LLM-agnostic + MCP-ready |

### Lecciones Clave

> "Conductor demuestra que **durabilidad y determinismo** son propiedades arquitectónicas, no disciplina del desarrollador. Separar orquestación (JSON/DAG) de implementación (workers) elimina toda una clase de bugs. OE v2 debe copiar esta separación."

### Diferenciador de OE v2

Conductor es un servidor de workflows; OE v2 es un **kernel embebible** con planificación LLM nativa. OE v2 puede generar planes dinámicamente desde objetivos de lenguaje natural, no solo ejecutar workflows predefinidos.

---

## Proyecto 5: Open-Multi-Agent (OMA)

**Repositorio:** https://github.com/open-multi-agent/open-multi-agent  
**Licencia:** MIT  
**Enfoque:** Orquestación multi-agente dinámica con TypeScript

### Patrones Extraídos

| Patrón | Descripción en OMA | Adopción en OE v2 |
|--------|--------------------|-------------------|
| **Dynamic Orchestration** | El coordinador construye el DAG en runtime desde el goal | ✅ Objective Discovery → Graph Builder |
| **Controlled Execution** | Preview, approve, suspend plans; freeze approved plans | ✅ Signal-driven con pause/resume/approve |
| **Resume from Checkpoints** | Reanudar ejecuciones interrumpidas | ✅ Checkpointing + Recovery |
| **Observability** | Run Viewer offline, OpenTelemetry, execution receipts | ✅ Execution traces + audit log |
| **Task DAG Scheduling** | Tasks con dependencias esperan; independientes corren en paralelo | ✅ Topological sort + nivelación + workers |
| **Synthesis** | Agregación de resultados de múltiples agentes | ✅ Evaluator con synthesis de resultados |

### Lecciones Clave

> "OMA demuestra que la **orquestación dinámica** no significa caos. Se puede generar un DAG en runtime y aún así tener control, observabilidad y recuperación. La clave es que el DAG generado sea datos (inspectables) no código (opaco)."

### Diferenciador de OE v2

OMA está en TypeScript/Node.js; OE v2 es **Python-first** para integración con el ecosistema ML/AI. OE v2 incluye memoria de estrategias, que OMA no tiene.

---

## Matriz de Verificación Cruzada Consolidada

| Capacidad | Open-Sable | PlanDB | M-APPLE-OS | Conductor | OMA | OE v2 |
|-----------|:----------:|:------:|:----------:|:---------:|:---:|:-----:|
| Goal Hierarchy | ✅ | ✅ | ⚠️ | ❌ | ⚠️ | ✅ |
| Compound Graph | ❌ | ✅ | ⚠️ | ⚠️ | ✅ | ✅ |
| Pre/Postconditions | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ |
| Plan Compiler | ⚠️ | ❌ | ❌ | ✅ | ⚠️ | ✅ |
| Durable Execution | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| Failure Classification | ⚠️ | ❌ | ✅ | ✅ | ⚠️ | ✅ |
| Strategy Memory | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Checkpoint/Rollback | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| Parallel Execution | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Signal-Driven | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| Dynamic Replanning | ✅ | ✅ | ✅ | ⚠️ | ⚠️ | ✅ |
| Observability | ✅ | ✅ | ⚠️ | ✅ | ✅ | ✅ |
| AI-Native Planning | ✅ | ⚠️ | ⚠️ | ✅ | ✅ | ✅ |
| **Total ✅** | 6 | 6 | 7 | 8 | 7 | **13** |

> **Conclusión:** OE v2 no copia ningún proyecto. **Sintetiza** los patrones más valiosos de cada uno y añade capacidades diferenciadoras (Strategy Memory, Objective Evolution, Plan Compiler con validación multi-capa).

---

## Recomendación de Integración

Para el kernel de YAIWES/MAXBRY, se recomienda:

1. **Adoptar OE v2 como motor de objetivos central** — Reemplaza el pipeline lineal actual.
2. **Integrar con Conductor** (opcional) — Para deployments que requieran durabilidad a escala de cluster, OE v2 puede exportar su ExecutionDAG a Conductor.
3. **Aprender de PlanDB** — El CLI de PlanDB puede usarse como herramienta de debugging/visualización del ObjectiveGraph.
4. **No depender de Open-Sable** — Es un agente completo, no una biblioteca. Extraer patrones, no código.
5. **Monitorear OMA** — Para futura integración TypeScript si el proyecto crece a multi-runtime.

---

*Verificación cruzada generada por Kimi K3 — Análisis de 5 proyectos open source de referencia*
