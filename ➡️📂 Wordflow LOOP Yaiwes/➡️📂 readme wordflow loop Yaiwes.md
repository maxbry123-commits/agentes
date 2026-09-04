# ➡️📂 readme wordflow loop Yaiwes

## REGLA DE REGISTRO VIGENTE

- Este README es la bitácora canónica del trabajo del **Wordflow LOOP Yaiwes**.
- **No se escribe, modifica, integra ni programa nada en GitHub hasta que el Director diga `APROBADO`, `INTÉGRALO` o autorice explícitamente esa acción.**
- Cuando exista autorización, primero se registra el INPUT BLOCK del Director **literal 1:1**, sin resumir ni reinterpretar.
- Después se registra la salida/decisión correspondiente.
- Cada segmento aprobado se convierte solo en su propia capa/módulo; arquitectura no monolítica.
- Todo es determinista por defecto. LLM solo puede entrar en decisiones o razonamiento que no puedan resolverse determinísticamente.
- Cada capa con razonamiento llevará un **skill pequeño específico de esa capa**.
- Todo archivo de código que se cree posteriormente deberá llevar contrato/ficha y conexión mediante plugin/Enchufe Universal.
- Raíz de trabajo: `➡️📂 Wordflow LOOP Yaiwes/`.

---

## INPUT BLOCK 010 — DIRECTOR — LITERAL

Ok necesito que hagas 2 tareas 

Tarea 1. 
Acruliza el code del wordflow Github acción 

Con este skills ya que se tubo que hacer mejoras por algunos problemas repetidos de el code que se usaba para el Github acción 

https://github.com/maxbry123-commits/agentes/tree/c789e5fe635e220230ffc759d86dc3bbb8e261d4/skills/skills%20Github%20acci%C3%B3n

Tarea 2
Reciclas el mismo code del wordflow para no reescribir solo copiar con code Github y lo mandas al archivo destino 

Dime qué entiendes de las 2 tareas 

---

## INPUT BLOCK 011 — DIRECTOR — LITERAL

Inicia y usas el sistema de trabajo de flujo que te di

---

## EJECUCIÓN BLOQUE 010–011

- Se leyó el skill canónico en el commit `c789e5fe635e220230ffc759d86dc3bbb8e261d4`.
- Regla fuente confirmada: `DO_NOT_REWRITE_CODE`; política `COPY_THEN_SURGICAL_EDIT`.
- Se tomaron los locks exactos del mecanismo Descargar+Extraer:
  - `gha-download-extract.yml` → `4e64ca02c2bc970dc4cd246a2a43ec2fdb7b4e62`
  - `FORENSIC-PASS-research-download-chain-final.yml` → `9ffd682ec9491741a8f49e4a7f8bb385aa62c2ee`
  - `FORENSIC-PASS-research_download_chain.py` → `b629f9a7844a4752ff7c28b844b83e7f1d99ccb1`
  - `research_download_chain.py` → `1504bbc7ec780a351beb105df884180c9ae2c666`
  - `ADVERTENCIA-CODE.json` → `f62bee5aa59d25721be6e075778ab670b5525b7a`
- El archivo `gha-download-extract.yml` del destino ya coincidía exactamente con el lock fuente.
- Los cuatro artefactos restantes se copiaron al destino mediante referencias de blob GitHub, sin reescribir contenido.
- Destino: `➡️📂 Wordflow LOOP Yaiwes/📂 Capa workflow GitHub Action/`.
- Commit de sincronización preparado: `159810dc09d77bd5ab24bca06ea261ac293aada5`.

## MÉTODO LOOP APLICADO

0. 12 goals de entrada/salida: verificar fuente exacta, commit, destino, locks, no reescritura, integridad y read-back.
1. Analizar tarea.
2. Priorizar actualización segura y copia exacta.
3. Planificar por locks SHA.
4. Ejecutar una tarea a la vez.
5. Verificar/refutar cada copia contra SHA fuente.
6. Pasar a la siguiente tarea solo tras PASS.
7. Verificar objetivos completos; si falla, LOOP con investigación de alternativas.
8. Salida solo con checklist PASS/GAP real.

---

## INPUT BLOCK 012 — DIRECTOR — LITERAL

Te voy a pasar partes del flujo de las capas que vamos a diseñar 

En varias partes vas hacer un flujo de diagrama en cascada 

Cada capa del flujo debe tener 

Ejemplo 

➡️➡️📂 Capa de tarea 
goals 12/12 → 1 analiza → 2 prioridades → 3 planifica → 4 cola 1×1 → 5 verifica/refuta + 20 soluciones si falla → 6 siguiente → 7 verificación global/LOOP → 8 checklist + salida.


2 vas a buscar en 3 lugares code y información para reciclar code analizas que necesitas para el wordflow LOOP y lo copias no puedes reescribrir solo copiar en capas y cablear usando los plugins 

1. En el repo ➡️ agentes ➡️📂core kernel Yaiwes 

2.  En el repo ➡️ nct core 🔌📂 wordflow code 
Hay varios archivos revisa donde hay información de code que necesitas 

3. En el repo ➡️ agentes motores Wordflow YAIWES ➡️ en todas las carpetas raíces hay cientos en agente revisas hasta encontrar lo que necesitas ➡️ 

puedes usar dagu o cualquier osquestador pero hagasno esto minimalista un 
Un micro kernel de flujo con un LOOP y bucle persistente bien estructurado solo para las tareas que vamos hacer 

Dime si entendiste está instruccion y anotas en ➡️ 📂 readme wordflow loop Yaiwes 

---

## INTERPRETACIÓN OPERATIVA DEL BLOQUE 012 — PENDIENTE DE PROGRAMACIÓN

1. El Wordflow LOOP se diseña por **capas separadas** y varias capas usarán **flujo en cascada**.
2. Cada capa aplicará el patrón: `12/12 goals → analiza → prioridades → planifica → cola 1×1 → verifica/refuta → 20 alternativas si falla → siguiente → verificación global/LOOP → checklist/salida`.
3. Para cada capa se debe buscar primero código reutilizable en tres fuentes: `agentes/Core kernel Yaiwes`, `NCT core/wordflow code` y `Agentes-motores-Wordflow-YAIWES`.
4. Regla de implementación: **no reescribir código existente**; copiar el mecanismo necesario, ubicarlo en su capa y cablearlo mediante plugin/Enchufe Universal.
5. Se permite Dagu u otro orquestador solo si encaja; objetivo: **microkernel de flujo pequeño, modular, persistente y no monolítico**, limitado a las tareas del Wordflow LOOP.
6. Este bloque queda registrado; todavía no se programan nuevas capas hasta recibir el siguiente segmento o autorización específica del Director.

---

## INPUT BLOCK 013 — DIRECTOR — LITERAL — PARTE 1

Parte 1 

Vamos a construir el loop wordflow por capas no monolítico
Cada capa del proceso en archivos separados y sobre esta clase vas a crear el code phyton 95% deteminetista y 5% llm
Skills y system promt DSL Dag shema sheriff validador verificación sentinela supervisor juez guardián todo como un contrato vas a y el sistema readme.md tipo OPEN claw

➡️ Ejemplo ➡️
📂 Capa 1 investigación
📂 Capa 2 auditoría forense x Ray De documentos reliza 12 gosls de entrada y salida ➡️ y 12 pasos de ask consil ➡️ realiza una conclusión de que code debe existir en la raíz del code fuente en la arquitectura en el cualquier parte de la cadena del wordflow del proyecto ➡️ busca en toda la raíz del proyecto le pones la ruta ➡️➡️📂 de la raíz del proyecto ➡️➡️auditoría forense x Ray a ver si eso existe en la capa o fase o en alguna parte de la raíz del proyecto  ➡️➡️➡️ si no existe lo convierte en un nuevo objetivo busca en otros documentos Información relacionados para ver si falta complementar más información o parte del flujo o si hay más información o si existe una mejor versión todos tarea 
Cada paso lleva 12 goals de entrada y salida que vas a hacer para cada paso todo en un contrato shema DSL Dag determinetista sheriff validador verificación sentinela supervisor juez guardián y verificación cruzada ➡️ Luego identifica el objetivo y realiza una lista de tareas pendientes para buscar el code que necesito o hacerlo ✅ todas las tareas deben tener trazabilidad de cada documento para saber de dónde salida debe tener un ID ➡️ define los objetivos antes de continuar como ➡️
Varios ejemplos 
De lo que dice Claude 

Condiciones 
90% código determinista, 10% LLM máximo
Núcleo del kernel: 0% LLM
Mismo input → mismo output (reproducibilidad, Ley L15)

Planifica antes del proceso 
🎯 OBJETIVO     → Extraer meta principal, verbo de acción, criterios de éxito/fallo.
🏗️ TAREA        → Descomponer en pasos atómicos, ordenar por dependencias, asignar prioridad.
💡 PLANIFICAR   → Antes de ejecutar, verificar que el objetivo y la tarea están completos.
📌👣 PRÓXIMOS   → Siguiente paso concreto (no una lista, solo el inmediato).
👣 PASO         → Ejecutar UN paso y actualizar estado (PENDING→RUNNING→DONE).
🧩 RESULTADOS   → Formato exacto de salida: código, texto, YAML, lo que el paso requiera.
⚠️ PENDIENTES   → Bloqueos activos con dueño y fecha límite.
🔒 CERRADO      → Pasos completados con hash de evidencia.
📂 ARCHIVAR     → Mover a carpeta de históricos cuando el ciclo termina.
🚨 INGENIERIA   → Modo determinista estricto, 0% LLM, solo código y validación Sheriff.
⁉️ FALTA        → Información que el agente no pudo extraer y debe preguntar al Director.
✅ INTEGRADO    → Marcar como parte del sistema después de pasar todos los checks.
🆕 NUEVO        → Documento o capacidad recién incorporada, pendiente de revisión.


extensions/project_bootstrap/
    schemas/           # Schemas JSON de cada documento
    templates/         # Plantillas base (Markdown con placeholders)
    microflows/        # Micro-flujos D para cada plantilla
    updater/           # Módulo de actualización incremental
    manifest.yaml      # Ficha de la extensión
    entrypoint.py      # Punto de entrada


➡️➡️➡️➡️ Capa 3
📂 Buscar auditoría forense x Ray del code en todos los repos de la cuenta de Github Maxbry 123 especialmente en ➡️ agente motores Wordflow YAIWES ➡️ router inteligente ➡️ agentes ➡️
📂 Capa 3.1copiar y mover archivo
📂 Capa 3.2 Investigar en Github code fuente listo de repos open soure que ya tienen el code que se necesita y iniciar el sistema de Github acción extracción
Ubicas en la raíz de ➡️ yaiwes existen 2 wordflow que tú hiciste 📌1. Sistema de descarga y extracción de archivos 📌 2. Sistema de evolución copias solo el sistema de readme.md tipo OPEN claw para añadirlo al wordflow 

Skills para copiar y descargar y extracción de componentes 

https://github.com/maxbry123-commits/agentes/tree/c789e5fe635e220230ffc759d86dc3bbb8e261d4/skills/skills%20Github%20acci%C3%B3n

➡️➡️➡️➡️➡️
📂 wordflow mecanismos 
Esto es la capa que da "latido" (heartbeat) al sistema — permite que el kernel siga vivo entre inputs, tome snapshots periódicos, y detecte si algún nivel del loop se quedó colgado.
LEVEL 1: reasoningBank, hierarchicalMemory, learningBridge, hybridSearch, tieredCache
LEVEL 2: memoryGraph, agentMemoryScope, vectorBackend, mutationGuard, gnnService
LEVEL 3: skills, explainableRecall, reflexion, attestationLog, batchOperations, memoryConsolidation
LEVEL 4: causalGraph, nightlyLearner, learningSystem, semanticRouter
LEVEL 5: graphTransformer, sonaTrajectory, contextSynthesizer, rvfOptimizer, mmrDiversityRanker, guardedVectorBackend

Flujo completo de punta a punta
Mermaid
graph TD
    A[Input] --> B[InputBlockReader hash-chain+TTL]
    B --> C[MissionBuilder GOAL_LOCK]
    C --> D[DSL→DAG Compiler]
    D --> E[ContractSelector]
    E --> F[Sheriff 5 estados]
    F -->|PASS| G[Scheduler + Time-Wheel]
    G --> H[Multi-API Fabric RACE/QUORUM/SPLIT]
    G --> I[Fleet Manager]
    H --> J[Ejecución paralela worktrees]
    I --> J
    J --> K[Auditoría 3 capas Maker-Checker]
    K --> L[MYTHOS 40 pasos por score]
    L --> M[Recovery 5 niveles]
    M --> N[Witness + evidence_hash]
    N --> O[Certificación 30/30]
    O --> P[Output final]


Implementar goal-dual-driver real
"Crea un schema Pydantic para objetivo primario + lista de objetivos secundarios, con validación de que siempre haya exactamente un primario."
reasoning-kernel/goal-dual-driver/
Pydantic
GPT
17
Implementar decision-on-demand
"Implementa un módulo DSPy tipo ChainOfThought que reciba una tarea y el template Mythos seleccionado, y devuelva una decisión estructurada."
reasoning-kernel/decision-on-demand/
DSPy
GPT

Mover los prompts de Fables a contenido versionado
"Extrae el texto de los 40 pasos Mythos, EURS Standard, EURS Turbo y DRE de los documentos originales y guárdalos como archivos .md independientes, sin lógica de código."
reasoning-kernel/decision-on-demand/prompts/
—
MiniMax
19
Implementar el score de complejidad
"Implementa la fórmula: score = (dependencias×2) + pasos_estimados + (5 si ambiguo) + (5 si alto riesgo), y clasifica en LOW/MEDIUM/HIGH/EXTREME."
execution-orchestration/classifier-scheduler/
—
Codex
20
Conectar score → selección de plantilla
"Usa el score de la tarea 19 para elegir automáticamente entre dre_by_score.md, eurs_standard.md, eurs_turbo.md o mythos_40.md."
reasoning-kernel/decision-on-demand/
—
Codex
21
Implementar expert-panel-router
"Implementa un comparador que reciba una tarea nueva y la compare contra workflow-definition/ existentes, devolviendo el mejor match y su score de confianza."
reasoning-kernel/expert-panel-router/
semantic-router
GPT
22
Implementar consensus-trigger
"Implementa el patrón Mixture-of-Agents: varios proponentes generan candidatos en paralelo, un agregador elige o fusiona."
reasoning-kernel/consensus-trigger/
Mixture-of-Agents (Together AI)
Grok
23
Implementar workflow-capacity
"Define cuántos workflows pueden correr concurrentemente según recursos disponibles, y expón esa cifra como config, no hardcodeada."
reasoning-kernel/workflow-capacity/
—
Codex
24
Definir schema-contracts (contrato cerrado)
"Define con Pydantic el esquema exacto de entrada/salida que cualquier capacidad, workflow o agente debe cumplir para ser aceptado por el kernel."
definition-registry/schema-contracts/
PydanticAI
GPT
25
Implementar validador de contrato cerrado
"Implementa un validador que rechace cualquier capacidad que no cumpla el schema de la tarea 24, antes de que llegue a mount-guard."
kernel-principal/contracts/validator.py
jsonschema / PydanticAI
Codex
26
Implementar deadline/timeout en el Scheduler
"Añade un timeout configurable por tarea; si se excede, cancela y reporta al Policy Engine."
kernel-principal/scheduler.py
asyncio.wait_for
Codex
27
Implementar idempotencia en el State Manager
"Añade una clave de deduplicación por mission_id para que reintentar una tarea no duplique efectos."
kernel-principal/state_manager.py
—
Codex
28
Implementar concurrencia segura del State Manager
"Añade bloqueo optimista (versión por registro) para que dos réplicas paralelas no se pisen al escribir el mismo estado."
kernel-principal/state_manager.py
—
Claude Code
29
Implementar sheriff-sentinel-council
"Implementa reglas duras (deny-list de acciones) usando un motor de políticas declarativo."
control-governance/sheriff-sentinel-council/
Open Policy Agent (OPA)
GPT
30
Implementar verdict-authority (Judge)
"Implementa un evaluador que compare dos o más soluciones candidatas y elija según criterios objetivos, no preferencia arbitraria."
control-governance/verdict-authority/
Prometheus (modelo juez OSS) / TruLens
Grok
31
Implementar forensic-core
"Implementa un log append-only que registre cada decisión del kernel con timestamp, mission_id y resultado."
control-governance/forensic-core/
OpenTelemetry
Codex
32
Implementar llm-control-deny
"Define una lista explícita de acciones que el LLM nunca puede ejecutar directamente sin pasar por Policy Engine, y valida contra ella cada llamada."
control-governance/llm-control-deny/
Guardrails AI
GPT
33
Tests unitarios de reasoning-kernel
"Escribe tests unitarios para goal-dual-driver, decision-on-demand, expert-panel-router y consensus-trigger (hoy: 0 tests)."
reasoning-kernel/tests/
pytest
Codex
34
Tests unitarios de extension-kernel
"Escribe tests unitarios para capability-registry, abi-mount y mount-guard (hoy: 0 tests)."
extension-kernel/tests/
pytest
Codex
35
Cerrar gap-registry
"Actualiza el registro de huecos pendientes marcando qué tareas de este bloque quedaron resueltas y cuáles no."
control-governance/gap-registry/
—
MiniMax
Ejemplo 
CHECKPOINTS — rellenar al cerrar cada tarea
📝 Checkpoint tarea número — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___

Hacer obligatorio mission_id/trace/ledger
"Modifica el Event Loop para que ninguna ejecución pueda iniciar sin un mission_id, trace_id y entrada de ledger asociados."
kernel-principal/event_loop.py
—
Claude Code
58
Implementar ledger/checkpoint durable
"Envuelve la ejecución de workflows críticos en un motor de ejecución durable que sobreviva reinicios."
state-events-durability/
Temporal (o LangGraph checkpointer si se prefiere más ligero)
Claude Code
59
Implementar retry-policy con reintentos deterministas
"Implementa reintentos con backoff exponencial conectados al circuit-breaker."
resource-governance/retry-policy/
Tenacity
Codex
60
Implementar circuit-breaker real
"Implementa un breaker que abra el circuito tras N fallos consecutivos de una capacidad y la marque como no disponible temporalmente."
resource-governance/circuit-breaker/
Tenacity / pybreaker
Codex
61
Implementar resource-broker-gate + lease-management
"Implementa un control de cuántas ejecuciones concurrentes puede sostener el sistema, con préstamo (lease) de recursos por tarea."
resource-governance/resource-broker-gate/
—
Codex
62
Implementar watchdog
"Implementa un proceso que detecte tareas colgadas más allá de su deadline (tarea 26) y las cancele forzosamente."
resource-governance/watchdog/
—
Codex
63
Reemplazar Fake/Stub por contract-testing real
"Sustituye los stubs de prueba detectados por la auditoría por tests de contrato reales contra los esquemas de schema-contracts/."
ubicación original de cada stub detectado
Schemathesis o Pact
Codex
64
Generar Estado Merkle global
"Genera una prueba verificable del estado del ledger completo."
state-events-durability/merkle/
pymerkle (o usar Git como Merkle DAG)
MiniMax
65
Prueba E2E completa
"Escribe y ejecuta una prueba que cubra: reception → mission → decision → execution → evidence → closure, de principio a fin, sin mocks en los puntos críticos."
execution-orchestration/tests/test_e2e_completo.py
pytest + utilidades de testing de Temporal
Claude Code
66
SBOM + secret scan final de todo el repo
"Ejecuta un escaneo de secretos y dependencias sobre el repositorio completo antes de declarar cerrada la v1."
raíz del repo
detect-secrets + syft
MiniMax
67
Consolidar manifest final de las 8 primitivas
"Verifica que las 8 primitivas del manifest de la tarea 14 digan nativo o delegado documentado — ninguna puede quedar sin estado."
kernel-principal/MIGRATION_MANIFEST.yaml
—
GPT
68
Cerrar los 18 placeholders restantes
"Vuelve a correr mypy --strict sobre kernel-principal/ y confirma cero placeholders restantes."
kernel-principal/
mypy
Codex
69
Auditoría final completa
"Repite exactamente el mismo formato de la Auditoría X-Ray original (conteo de archivos, Python, tests, placeholders) sobre todo agente-yaiwes/."
raíz del repo, nuevo documento de auditoría
—
MiniMax
70
Redactar veredicto de cierre v1
"Compara la auditoría de la tarea 69 contra la original y redacta el veredicto final: qué cambió de PARCIAL a COMPLETO, con evidencia de cada cambio."
raíz del repo, VEREDICTO_CIERRE_V1.md
—
GPT
➡️➡️➡️➡️
📌📌📌
📂Equipo auditor revisa las tareas realizadas que revisa 
1. Tarea realizada usando la trazabilidad de la tarea y de los documentos cuáles documentos los del proyecto y lo que identifica el equipo investigador auditoría de documentos y que mandó para hace la tarea revisa que documentos se audito y hace verificación cruzada entre el documento y el code para ver si está 100% todo pass ✅ si no reenvía la tarea de nuevo para repetir el proceso 
2.revisa si el código que se uso debe ser lo suficientemente para que cumpla los objetivos de los documentos del proyecto si no manda a buscar más code o crear el code que falta 
Cada proceso debe llevar 12 goals de entrada y 12 de salida con contrato y ask cónsil 

Auditoría adversarial → Auditoría cruzada → Maker-Checker
RETRY → ROLLBACK → CHECKPOINT → REPLAN → ESCALATE

flujo está completo en el papel. La auditoría real encontró que la mayoría de los archivos que deberían conectar estas capas (sentinel.py, council.py, supervisor.py, watchdog.py, capability_brain.py...) existen solo como nombres importados, no como código. El diseño de arriba es correcto — lo que falta es escribirlo o fusionarlo desde las librerías de la siguiente lista.

Nada se considera "hecho" sin un evidence_hash — toda tarea genera evidencia

---

## CAPAS EXPLICATIVAS — PARTE 1 — SIN CÓDIGO

1. **Capa 1 — Investigación:** recibe el objetivo, fija 12 goals de entrada/salida, identifica documentos y fuentes relacionadas, define qué información falta y prepara una conclusión verificable antes de permitir cualquier tarea de código.
2. **Capa 2 — Auditoría forense X-Ray de documentos:** cada documento pasa por contrato, schema/DSL/DAG, Sheriff, Validator, Verifier, Sentinel, Supervisor, Judge, Guardian, 12 Ask Consil y verificación cruzada; concluye qué código debería existir, busca su ruta real en el proyecto y convierte cada ausencia en objetivo/tarea trazable con ID y evidence_hash.
3. **Capa 3 — Auditoría X-Ray de código y adquisición:** busca primero código existente en los repos Maxbry; si existe, se reutiliza/copia; si falta, 3.1 copia/mueve con trazabilidad y 3.2 busca OSS y usa el workflow GitHub Action de descarga/extracción. El workflow de evolución se usa para decidir incorporación sin reescritura arbitraria.
4. **Capa mecanismos/heartbeat:** mantiene el LOOP vivo entre inputs mediante estado, memoria jerárquica, snapshots, watchdog, retry/recovery/checkpoints y detección de tareas colgadas. Los niveles 1–5 descritos son inventario funcional a validar antes de implementar.
5. **Cadena de ejecución:** Input → InputBlockReader → Mission/GOAL_LOCK → DSL/DAG → ContractSelector → Sheriff → Scheduler/Time-Wheel → Multi-API/Fleet → ejecución → Maker-Checker → razonamiento por score → Recovery → Witness/evidence_hash → certificación → salida.
6. **Equipo auditor/cierre:** toda tarea vuelve a auditoría adversarial + cruzada + Maker-Checker; compara documento↔código↔objetivos, exige suficiencia del código y si falla reenvía a RETRY/ROLLBACK/CHECKPOINT/REPLAN. Ninguna tarea se marca hecha sin `evidence_hash`.
