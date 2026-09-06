# PLAN DE PROGRAMACIÓN — WORDFLOW LOOP YAIWES — 11 OBJETIVOS + AGENTES

## ESTADO
Contrato: `tel.workflow/v3`
Modo: `FAIL_CLOSED_LOOP`
Naturaleza: plan canónico de programación y auditoría del Wordflow LOOP Yaiwes.

## OBJETIVO FINAL DEL WORDFLOW LOOP YAIWES
El Wordflow LOOP Yaiwes existe para tomar los documentos del proyecto como fuente de verdad, extraer de ellos requisitos, arquitectura, tareas y criterios de aceptación, convertirlos en trabajo de programación trazable, producir o reutilizar código ejecutable, integrarlo físicamente dentro de la estructura YAIWES y su microkernel, cablearlo mediante contratos/Fichas/plugins/registry, ejecutarlo, probarlo, repararlo y auditarlo hasta que el sistema descrito en los documentos exista realmente en código y pueda verificarse de extremo a extremo.

El LOOP no es el producto final por sí mismo: es el sistema persistente que mantiene en ejecución el trabajo de análisis, programación, reparación, integración y auditoría hasta cerrar el proyecto sin perder estado ni declarar éxito falso.

## LOS 11 OBJETIVOS OPERATIVOS CANÓNICOS
1. **Investigar y localizar todo el código fuente necesario** para construir el Wordflow LOOP Yaiwes, priorizando repositorios autorizados y código existente antes de generar código nuevo.
2. **Copiar/reutilizar el código faltante** en el destino correcto del Wordflow/YAIWES con trazabilidad de origen, ruta y SHA, preservando lógica y aplicando solo cambios quirúrgicos cuando sean necesarios.
3. **Cablear todo mediante Ficha/contrato → adapter/plugin → registry → health/evidence**, sin acoplamientos monolíticos ni bypass del microkernel.
4. **Verificar documentalmente en múltiples pasadas** que lo implementado corresponde a los documentos, arquitectura, README, HANDOFF, STATE, CHECKPOINT, RECOVERY y Crazy Wall.
5. **Analizar GAPs y convertirlos en trabajo programable**, incorporando tareas nuevas al backlog del Wordflow sin perder trazabilidad de qué documento/requisito las originó.
6. **Generar la lista de tareas de programación para los agentes**, con ID, objetivo, contexto, archivos/rutas, dependencias, criterio de éxito, tests y evidencia esperada.
7. **Integrar y cablear los agentes de programación** dentro del Wordflow como capacidades registradas, con roles separados de ejecución, reparación, revisión, auditoría y consenso.
8. **Cablear los repositorios autorizados con Hugging Face/compute autorizado** cuando corresponda, usando los procesadores permitidos y registrando health, límites y evidencia real.
9. **Integrar almacenamiento/memoria del Wordflow y agentes** con los sistemas autorizados previstos por arquitectura (Graphiti/Grapify/SQL/Hugging Face storage cuando estén autorizados y disponibles), sin inventar conexiones no existentes.
10. **Integrar acceso a modelos mediante secret_ref y contratos**, con health, presupuesto, timeout y fallback, sin exponer secretos ni hardcodear endpoints sensibles.
11. **Ejecutar auditoría, tests y cierre E2E**, demostrando que documentos → tareas → código → integración → ejecución → reparación → auditoría → evidencia funciona de extremo a extremo antes de `VERIFIED_CLOSED`.

## ARQUITECTURA DE TRABAJO DE PROGRAMACIÓN
`DOCUMENTOS PROYECTO → INPUT_BLOCK literal → extracción de requisitos → clasificación por capa → GOAL_LOCK → DSL/DAG/Schema/Contrato → backlog 1×1 → Council12 → selección de código/reuse → ejecutor de código → reparación → wiring plugin/registry → test → auditoría multiagente → embudo → consenso → STATE/CHECKPOINT/EVIDENCE → siguiente nodo → cierre E2E`

## CAPAS DESTINO DEL CÓDIGO
Cada pieza se clasifica antes de copiar/programar en una de estas responsabilidades:
- `code-programming-engine/`: compilación de tareas de programación, ejecución y herramientas de código.
- `kernel-principal/`: microkernel TEAM/YAIWES 0% LLM, control, registry, router, state y extension-kernel.
- `execution-orchestration/`: DAG/state-machine, cola 1×1, programación y dispatch.
- `control-governance/`: Sheriff, Validator, Verifier, Sentinel, Supervisor, Judge, Guardian y GAP registry.
- `state-events-durability/`: STATE, checkpoint, event log, reinyección, recovery e idempotencia.
- `execution-engine-pool/`: adapters de agentes, capability matching, aislamiento y normalización.
- `reasoning-kernel/`: Council/consensus/reasoning on demand; nunca sustituye el control determinista.
- `research-evidence/`: investigación, provenance, SHA, evidencia, dedup/rank.
- `tools-models-memory-knowledge/`: modelos, herramientas, memoria y conocimiento autorizados.
- `module-tests/` / tests de cada capa: pruebas unitarias, integración, regresión, estabilidad y cierre.

## COUNCIL12 — ASK CONSIL DE PROGRAMACIÓN / ARQUITECTURA / AUDITORÍA
Los 12 slots del Council son:
1. Claude Code CLI
2. OpenClaw
3. Hermes
4. Codex
5. Aider
6. OpenCode
7. OpenHands
8. Mimo Code
9. Muse/Glimmer Code
10. Kimi K Code CLI
11. Smolange
12. Qwen Code CLI — slot adicional elegido para contraste independiente; su integración física queda sujeta a evidencia real en repos/capacidades autorizadas.

Council12 no significa que los 12 escriban el mismo archivo. Cada agente entrega análisis/veredicto separado; el Wordflow filtra, deduplica, compara y registra discrepancias antes del consenso.

## ROLES FIJADOS POR EL DIRECTOR
### Ejecutor principal de código
- **OpenCode**: escribe/ejecuta el código de la tarea asignada dentro del contrato y sandbox correspondiente.

### Revisión y reparación
- **OpenHands**: inspecciona el resultado del ejecutor, reproduce fallos, propone/aplica reparación autorizada y vuelve a probar.

### Flujo, ejecución y wiring
- **Mimo Code + Claude Code CLI**: revisan que el flujo real del código corresponda al DAG/contrato, que imports/adapters/plugins/registry estén cableados y que el código sea realmente invocable desde el Wordflow.

### Auditores del proyecto
- **Claude Code CLI**
- **Mimo Code**
- **Codex**
- **Smolange**
- **Hermes**
- **OpenClaw**
Cada auditor produce un resultado independiente con PASS/GAP/INCONCLUSIVE + evidencia. El Wordflow genera un embudo de hallazgos: normaliza → deduplica → agrupa contradicciones → rankea evidencia → conserva minorías/discrepancias.

### Revisión del consenso de auditoría
- **OpenHands + OpenCode** revisan el embudo final de auditoría antes de aceptar una resolución técnica.
- Un consenso de agentes no reemplaza Sheriff/Validator/Verifier ni evidencia real.

## RESTO DE AGENTES
Todos los demás agentes/capacidades encontrados en los repos autorizados pueden pertenecer al Wordflow LOOP Yaiwes, pero deben entrar mediante Ficha/contrato, capability registry, adapter/plugin, health y evidencia. No se considera integrado por existir como carpeta o repositorio.

## LOOP 1 — BACKLOG GLOBAL DEL PROYECTO
`11 objetivos → tareas por objetivo → dependencias → cola 1×1 → LOOP2 por tarea → cierre con evidencia → siguiente tarea → cross-check global → repetir hasta que 11/11 objetivos estén VERIFIED_CLOSED o queden GAP/INCONCLUSIVE explícitos`

## LOOP 2 — CADA TAREA
`INPUT literal → 12 goals entrada → prioridades → plan → cola 1×1 → ejecutar un delta → Sheriff → Validator → Verifier → Sentinel/Supervisor → refutar → GAP? investigación con alternativas distintas → ejecutar delta distinto → Council12 cuando aplique → auditoría instrucciones ×3 → 12 goals salida → 3 refutaciones → cross-check → tests reales → evidence_hash/checkpoint/state → PASS/GAP/INCONCLUSIVE`

Regla: un GAP nunca se transforma en PASS por repetición verbal. Si una estrategia ya falló, el siguiente intento debe cambiar materialmente. Si no hay solución segura en la corrida actual, se registra 🚩 con evidencia y se continúa con la siguiente tarea segura sin declarar cerrado el objetivo afectado.

## CONTRATO DE PROGRAMACIÓN POR TAREA
Cada tarea que llegue a un agente debe incluir como mínimo:
- `task_id`
- `objective_id` (1–11)
- INPUT literal / requisito de origen
- documento/ruta/URL/SHA de origen
- archivos destino exactos
- dependencias
- agente/rol asignado
- capability requerida
- contrato I/O y schema
- restricciones de determinismo/LLM
- imports/plugins/registry esperados
- tests obligatorios
- evidencia esperada
- checkpoint/recovery
- criterio `PASS | GAP | INCONCLUSIVE`

## REGLAS DE CÓDIGO
1. REUSE > COPY/MOVE > PATCH QUIRÚRGICO > ADAPTER > GENERATE.
2. No reescribir hot-path existente sin prueba de paridad.
3. Código modular; separar contratos, adapters, plugins, registry, loaders, guards, runtime y tests.
4. Kernel/control = 0% LLM.
5. LLM solo para razonamiento, investigación o generación no resoluble de forma determinista.
6. Ningún agente productor puede autocertificar su propia salida como cierre final.
7. Código presente ≠ código integrado; integración exige import/call-path/registry/health/test/evidence.
8. Sin ruta + SHA/diff + test/log/evidencia no existe `VERIFIED_CLOSED`.

## DEFINICIÓN DE TERMINADO DEL PROYECTO
El proyecto se considera terminado solamente cuando los 11 objetivos están cubiertos con evidencia real y existe una prueba E2E que demuestre al menos esta cadena:
`documento del proyecto → requisito extraído → tarea programable → agente ejecutor → código creado/reutilizado → reparación si falla → wiring al microkernel/plugin registry → ejecución real → auditoría multiagente → consenso/embudo → test/verificación independiente → STATE/CHECKPOINT/evidence → salida verificable`.

Estados finales permitidos por nodo/objetivo: `VERIFIED_CLOSED | CLOSED_UNVERIFIED | INCONCLUSIVE`; el cierre global exige evidencia suficiente para `VERIFIED_CLOSED` de los objetivos obligatorios.
