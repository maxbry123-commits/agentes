# Componentes open source a integrar — investigación completa

## 1. Arquitectura de sesión/harness (recomendación directa de Anthropic, 2026)

- **Patrón a copiar:** "Managed Agents" — sesión (log append-only) separada del harness (bucle+router). No es un paquete que se instale; es un patrón que debes aplicar a `state-events-durability/` (sesión) vs `kernel-principal/` (harness).
- **Para implementar la sesión persistente:** **Temporal** (event history nativo) o **LangGraph** con checkpointer (más ligero).
- **Para el harness de 3 agentes (Planificador → Generador → Evaluador) que Anthropic documentó para tareas largas:** este es el patrón exacto de **Mixture-of-Agents** ya identificado, o puedes implementarlo directo con **DSPy** (3 módulos encadenados con roles distintos).

## 2. Multi-API Fabric — RACE / QUORUM / SPLIT (tu pedido de "20-30-50 APIs")

- **LiteLLM Router** — el más directo: registras N proveedores/API keys como una lista de "deployments" y el Router hace fallback, balanceo de carga y reintentos entre todos ellos de forma nativa. Cubre `SINGLE` y parcialmente `RACE`.
- **`asyncio.wait(..., return_when=FIRST_COMPLETED)`** (nativo de Python) — la primitiva exacta para implementar `RACE` puro: lanzas la misma pregunta a varios proveedores y usas el primero que responde.
- **Mixture-of-Agents (Together AI)** — implementa `QUORUM` de forma nativa: varios proponentes, un agregador que exige coincidencia.
- **`asyncio.gather` + LiteLLM Router** — para `SPLIT`: divides el input en partes, cada parte va a un proveedor distinto en paralelo, se combinan los resultados al final.

## 3. Time-Wheel (tu "loop tipo calendario/agenda")

- **Netty `HashedWheelTimer`** (Java) — la implementación de referencia del algoritmo O(1), si quieres portarlo.
- **`APScheduler`** (Python) — no es O(1) puro pero cubre el 95% del caso de uso real: tareas recurrentes por hora/cron/intervalo, con persistencia de jobs.
- **Celery Beat** — si ya vas a usar colas de tareas (recomendado más abajo), Beat te da el scheduler periódico integrado gratis.
- **`croniter`** — para traducir "cada tanto tiempo" en lenguaje natural/cron a triggers reales (esto es lo que usa MiniMax Agent para sus "Scheduled Tasks con lenguaje natural").

## 4. Input Block Reader — cola de entrada con hash-chain + TTL (tu pedido "input en cola como Grok")

- **NATS JetStream** — deduplicación nativa por hash de mensaje + políticas de retención por TTL, exactamente el patrón que describes.
- **Redis Streams** — alternativa más simple si ya usas Redis, con consumer groups y expiración.
- Cualquiera de las dos te da "el sistema sigue procesando mientras llegan más inputs" sin escribir tu propio hash-chain desde cero.

## 5. Fleet Manager — pool de agentes externos completos

- **Ray** (actors) — ya identificado antes, sigue siendo la mejor opción para correr Aider/Cline/Codex/Hermes como workers paralelos reales.
- **Grok Build** (`xai-org/grok-build`, Apache-2.0) — worktrees aislados ya listos para extraer (visto en la auditoría anterior).

## 6. Sistema de memoria — el "archivo de 20 millones de parámetros" (contexto persistente)

- **Letta (MemGPT)** — bloques de memoria por agente + memoria archival vectorial; cubre Nivel 1-2 de tu esquema (`reasoningBank`, `hierarchicalMemory`, `vectorBackend`).
- **Mem0** — alternativa más ligera para `tieredCache` y `hybridSearch`.
- **Graphiti** — grafo de conocimiento temporal; cubre Nivel 2 y 4 (`memoryGraph`, `causalGraph`, `gnnService`).
- **LlamaIndex** (Property Graph Index) — alternativa a Graphiti si prefieres algo más maduro para `contextSynthesizer` y `mmrDiversityRanker` (MMR — Maximal Marginal Relevance — ya viene implementado nativo en LlamaIndex y en LangChain retrievers).
- **DVC (Data Version Control)** — para `attestationLog` y `memoryConsolidation`, ya que DVC versiona y da fingerprint a artefactos de forma nativa.

## 7. Sistema de chat / multi-canal

- **OpenClaw 2.0** (`2026.8.1`, agosto 2026) — reescribió su app de navegador, agregó sesiones multiplayer compartidas en la nube y movió el almacenamiento de sesión; es hoy la referencia más completa de "gateway multicanal" (933 contribuidores activos).
- **Hermes Agent v0.20.6** (27 agosto 2026) — agregó navegación con perfil real con consentimiento, un motor de actualización remota por SSH, un "fleet profile rail" (várias instancias gestionadas como flota) y un catálogo de 50+ servidores MCP verificados — el "fleet profile rail" es directamente aplicable a tu Fleet Manager.
- **n8n** — sigue siendo la opción más simple si prefieres montar el gateway multicanal tú mismo con nodos visuales en vez de adoptar OpenClaw completo.

## 8. Elicitación estructurada — "rutas por listas previas" (lo que Claude usa para preguntarte antes de iniciar)

- **JSON Schema con `enum`** + **PydanticAI** — la forma más simple: cada pregunta de ruta es un campo con opciones fijas, nunca texto libre.
- **Rasa Open Source** — si quieres un framework dedicado de "slot-filling" conversacional con formularios de varios pasos, es la referencia más madura en open source para exactamente este patrón.

## 9. System prompt / documentos de memoria (recomendación del creador de Claude Code)

- **Convención `CLAUDE.md`** (memoria de proyecto, ya cubierta) + **`AGENTS.md`** (estándar más nuevo, multi-agente, adoptado por varios harnesses en 2026).
- **Claude Agent SDK** — su función de "compactación automática" de contexto es la referencia oficial más reciente para manejar contexto largo sin el patrón antiguo de "reinicio manual" — vale la pena revisar su documentación de compactación antes de escribir la tuya propia.
- Patrón de harness recomendado por Anthropic en 2026 (3 principios): usar lo que el modelo ya sabe hacer bien (no scaffolding innecesario), preguntarte qué scaffolding puedes **quitar** con cada mejora de modelo, y fijar los límites del harness con el entorno (permisos) con mucho cuidado — los tres aplican directo a decidir cuándo un paso de tus 40 debe seguir siendo código y cuándo ya puede confiarse al LLM sin cápsula.

## 10. Comparación de veredicto: qué mantener vs qué reemplazar de OpenClaw/Hermes

| Aspecto | OpenClaw 2.0 | Hermes v0.20.6 | Recomendación para YAIWES |
|---|---|---|---|
| Arquitectura | Gateway separado de los agentes | Todo en una sola clase de agente | Copiar el patrón de OpenClaw (ya alineado con tu `kernel-router`) |
| Escalamiento multi-usuario | Sesiones multiplayer en la nube (nuevo) | No es su fuerte | Adoptar si YAIWES tendrá más de un usuario |
| Memoria/auto-mejora | Más débil en este punto | Memoria procedural que convierte workflows exitosos en skills reutilizables | Adoptar el patrón de Hermes para tu `native-learning/` |
| Flota de instancias | No nativo | "Fleet profile rail" (nuevo, agosto 2026) | Estudiar su código directamente para tu `agent-fleet-parallelism/` |
| Catálogo de herramientas | Amplio (plugins) | 50+ servidores MCP verificados (nuevo) | Cualquiera sirve como fuente para tu `capability-registry/` |
