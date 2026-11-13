# Investigación: dónde vive el razonamiento del kernel, y componentes de ventaja avanzada
**Basado en literatura y repos reales de 2025-2026, verificados por búsqueda — no solo lo que ya discutimos en este chat**

---

## PARTE 1 — Otros lugares/formas donde puede vivir el sistema de razonamiento

Tenías 4 (capa de razonamiento tipo Fables, README/CLAUDE.md, Self-Discover, system prompt DSL/DAG). Aquí hay 8 más, todas reales y en uso hoy:

5. **Como archivo de Skill** (formato `SKILL.md`) — el mismo estándar que yo uso internamente para saber cuándo aplicar una habilidad. Ya es un formato de producción real, no solo una idea de Fables.
6. **Como servidor MCP** — expones el módulo de razonamiento como una herramienta que cualquier agente compatible con MCP puede consumir (Claude Code, Codex, Cursor, Hermes). Esto significa que un módulo de razonamiento que hagas para tu kernel también podría venderse/compartirse como MCP independiente.
7. **Como banco de trayectorias pasadas (no reglas, sino experiencia)** — esto es exactamente **ReasoningBank** (investigación real, Ouyang et al. 2025): en vez de escribir la regla a mano, el sistema extrae automáticamente qué patrón de razonamiento funcionó (o falló) en tareas anteriores, y lo guarda para reutilizarlo. Es la versión "que aprende sola" de lo que hicimos hoy a mano.
8. **Como grafo de conocimiento causal** — no lista plana, sino relaciones ("esta estrategia funciona bien cuando la tarea tiene esta característica").
9. **Como política entrenada por refuerzo (RL)** que decide *cuándo* pensar vs. cuándo usar una herramienta — esto es lo que hace **ReTool** (2025-2026): el modelo aprende, durante el entrenamiento, a interrumpirse a sí mismo y decir "necesito ejecutar código aquí" en vez de seguir razonando en texto. Más avanzado que un prompt, pero requiere entrenamiento, no solo arquitectura.
10. **Como modelo juez separado y pequeño**, especializado solo en evaluar (no en generar) — evita el sesgo de auto-evaluación que ya vimos con Anthropic.
11. **Como memoria multi-alcance (multi-scope)** — cada recuerdo se etiqueta con a quién pertenece: `user_id` (persiste entre sesiones de un usuario), `agent_id` (pertenece a una instancia de agente), `run_id` (solo a esta tarea), `org_id` (compartido en toda la organización). Es el patrón que usa Mem0 en 2026 para no mezclar memoria de un usuario con la de otro.
12. **Como parte de un fine-tuning/LoRA propio** — si algún día entrenan su propio modelo pequeño, el razonamiento deja de ser un archivo externo y se hornea directamente en los pesos. Es el nivel más "permanente" posible, pero también el más caro y el que menos se puede ajustar sin reentrenar.

---

## PARTE 2 — Componentes de ventaja por área

### 1. Razonamiento lógico avanzado
- **Self-Discover** (ya cubierto) — sigue siendo tu mejor punto de partida, es barato y ya lo implementamos.
- **Modelos open-weight razonadores de 2026** que puedes usar como proveedores en tu Multi-API Fabric sin entrenar nada: **Kimi K2 Thinking** (200-300 llamadas a herramientas consecutivas sin intervención), **GLM-5.2** (744B parámetros, MIT license, fuerte en benchmarks de razonamiento como GPQA Diamond), **DeepSeek V4**, **MiniMax M1** (eficiente en cómputo de "pensar mucho").
- **Google ADK-Python** (Agent Development Kit) — framework oficial de Google para construir agentes, vale la pena revisarlo junto a LangGraph como alternativa/complemento.
- **ReTool** — como referencia de hacia dónde va la industria (razonamiento entrenado, no solo prompteado), aunque implementarlo tú mismo requiere entrenar un modelo, no solo ensamblar componentes.

### 2. Investigación avanzada por web
- **GPT Researcher** (`assafelovic/gpt-researcher`) — el más maduro y plug-and-play: ~28.000 estrellas, 240+ contribuidores, hace crawling paralelo (no secuencial) y reportes con citas. Es tu primera opción.
- **Stanford STORM** (`stanford-oval/storm`) — su ventaja específica: genera 3-5 "personas" con perspectivas distintas ANTES de investigar, evitando que toda la investigación converja en un solo sesgo de consenso. Encaja perfecto con tu idea de "múltiples formas de pensar".
- **Tongyi DeepResearch** (Alibaba) — un modelo open-weight entrenado específicamente para búsqueda multi-hop, no solo un framework.
- **LangChain Open Deep Research** y **DeerFlow** (ByteDance) — alternativas si prefieres algo ya integrado con LangGraph.

### 3. Reconocimiento de patrones
Ya está resuelto en gran parte por el catálogo de 105 algoritmos que te di (PCA, clustering, DBSCAN, LDA, Apriori). Lo que añade valor nuevo de esta investigación:
- **Graph Neural Networks (GNN)** — para patrones *relacionales* (cómo se conectan las cosas), no solo tabulares. Literalmente ya tenías `gnnService` en tu propio documento YAIWES — ahora confirmado como técnica real y vigente.
- **Embeddings + similitud vectorial** — ya cubierto por Letta/Mem0/Graphiti, es la forma moderna de "reconocer que esto se parece a aquello".

### 4. Persistencia — el "100x más persistente que OpenMythos"
Aquí una aclaración honesta: **"100 veces más persistente" no es una unidad de medida real** — pero sí existen benchmarks reales contra los que puedes medir avance de verdad, en vez de una cifra inventada:
- **LoCoMo** (1.540 preguntas, recall de un solo salto, multi-salto y temporal)
- **LongMemEval** (500 preguntas, incluye actualización de conocimiento y recall multi-sesión)
- **BEAM** (evalúa a escala de 1 millón y 10 millones de tokens acumulados)

Componentes reales que apuntan a "más persistente" de verdad:
- **EverMemOS** — memoria que se auto-organiza como un sistema operativo, pensada para razonamiento de largo horizonte.
- **ReasoningBank** — igual que en la Parte 1, aprende de éxitos Y de fracasos, no solo guarda hechos.
- **Multi-scope memory de Mem0** — la forma correcta de que la memoria crezca sin mezclarse entre usuarios/agentes/sesiones.

---

## Conclusión y recomendación de orden

No adoptes las 4 áreas a la vez — es exactamente el error que ya vivimos con Mythos (mucho diseño, cero código funcionando). Orden sugerido, dado que tu kernel todavía no pasa el "Nivel A" del protocolo de cierre:

1. **Primero, cierra el Nivel A** (protocolo del documento anterior) — sin esto, ninguno de estos componentes tiene dónde conectarse todavía.
2. **Luego, GPT Researcher** — es el de instalación más simple y da valor inmediato en investigación web.
3. **Luego, Self-Discover** (ya construido hoy) + STORM para diversidad de perspectivas.
4. **Al final, ReasoningBank/EverMemOS** para persistencia — porque necesitan que el sistema ya esté generando trayectorias reales de las cuales aprender; instalarlos antes de tener uso real del kernel no tiene nada de qué aprender todavía.
