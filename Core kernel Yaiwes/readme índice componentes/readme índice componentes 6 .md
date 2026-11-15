# 📂 README ÍNDICE COMPONENTES 6 — YAIWES CORE KERNEL

Repositorio: `maxbry123-commits/agentes` · Rama: `main` · Bloque: **YAIWES 26–30** · Inventario fresh: **229**.

## YAIWES 26 — CPython ➡️ Runtime/intérprete Python
**URL raíz / ubicación:** `Core kernel Yaiwes/Componentes recuperados B/CPython/`  
**Handoff:** nodo `156`, `PENDING_STEP1`, paso 1, target `NO REGISTRADO`.  
**Fuente seleccionada:** `Python/ceval.c`; `Py_GetRecursionLimit()` y `Py_SetRecursionLimit()` verificadas.  
**Determinista:** Sí — ≈99% para misma versión/estado/entradas; I/O, concurrencia y código externo pueden variar.  
**¿Es agente?:** No.  
**Cómo funciona el kernel/core para tomar decisiones:** no decide objetivos; ejecuta semántica Python y sirve de runtime a planners/tools/validadores.  
**Microflujo horizontal:** `fuente → parse/compile → code object/bytecode → evaluation runtime → objetos/llamadas/excepciones → resultado`  
**Contexto estructural:** runtime C, object model, memoria, threads, stdlib y extensiones.  
**Nivel seleccionado:** language runtime / execution substrate.  
**Qué aporta a un agente:** sustrato para ejecutar lógica del kernel, herramientas y adaptadores Python.

## YAIWES 27 — crewAI ➡️ Orquestación multiagente con Crews y Flows
**URL raíz / ubicación:** `Core kernel Yaiwes/Componentes recuperados A/crewAI/crewAI/`  
**Handoff:** nodo `157`, `PENDING_STEP1`, paso 1, target `NO REGISTRADO`.  
**Fuente seleccionada:** `README.md` físico verifica Crews y Flows event-driven; símbolo interno único `NO VERIFICADO`.  
**Determinista:** No — ≈35%; wiring/flow es programático y decisiones semánticas dependen de LLMs.  
**¿Es agente?:** No como componente global; framework que crea/coordina agentes.  
**Cómo funciona el kernel/core para tomar decisiones:** configura roles/goals/tools/LLMs/memory/guardrails, asigna tareas y coordina resultados/eventos.  
**Microflujo horizontal:** `objetivo → Flow/Crew → tasks → agente → LLM + tools + memory → resultado → evento/siguiente tarea → salida`  
**Contexto estructural:** agents, crews, tasks, flows, tools, memoria, guardrails, structured output, human review.  
**Nivel seleccionado:** multi-agent orchestration framework.  
**Qué aporta a un agente:** composición de especialistas y automatizaciones multiagente con flujo explícito.

## YAIWES 28 — CRITIC ➡️ Autocorrección mediante crítica interactiva con herramientas
**URL raíz / ubicación:** `Core kernel Yaiwes/Componentes recuperados B/CRITIC/CRITIC/`  
**Handoff:** nodo `158`, `PENDING_STEP1`, paso 1, target `NO REGISTRADO`.  
**Fuente seleccionada:** `CRITIC/README.md`; verifica validación y rectificación progresiva con herramientas; función interna única `NO VERIFICADA`.  
**Determinista:** No — ≈25%; generación/crítica/revisión dependen del LLM.  
**¿Es agente?:** No como runtime general; método/framework agentic de self-correction.  
**Cómo funciona el kernel/core para tomar decisiones:** genera respuesta, consulta herramientas para comprobarla, critica usando evidencia y rectifica.  
**Microflujo horizontal:** `query → respuesta inicial → tool → evidencia → crítica → rectificación → respuesta revisada`  
**Contexto estructural:** QA, commonsense, matemática, hallucination detection, safety; búsqueda web, Python y APIs.  
**Nivel seleccionado:** tool-interactive critique/self-correction.  
**Qué aporta a un agente:** contrastar salidas con evidencia externa y corregir errores antes de aceptar respuesta.

## YAIWES 29 — Cronie ➡️ Ejecución temporal determinista de procesos UNIX
**URL raíz / ubicación:** `Core kernel Yaiwes/Componentes recuperados B/Cronie/`  
**Handoff:** nodo `159`, `PENDING_STEP1`, paso 1, target `NO REGISTRADO`.  
**Fuente seleccionada:** `readme.md` verifica `crond`; función interna única `NO VERIFICADA`.  
**Determinista:** Sí — ≈99% en calendario/configuración; proceso hijo depende del entorno.  
**¿Es agente?:** No.  
**Cómo funciona el kernel/core para tomar decisiones:** evalúa crontab contra tiempo/calendario y dispara el programa correspondiente.  
**Microflujo horizontal:** `crontab → parse → crond tick → coincide? → contexto → proceso → exit/log → siguiente tick`  
**Contexto estructural:** crond, crontab, anacron, cronnext, PAM, SELinux y logging.  
**Nivel seleccionado:** OS time scheduler.  
**Qué aporta a un agente:** disparadores temporales deterministas para mantenimiento/watchdogs/tareas recurrentes.

## YAIWES 30 — CycloneDX-Python ➡️ SBOM verificable de dependencias Python
**URL raíz / ubicación:** `Core kernel Yaiwes/Componentes recuperados B/CycloneDX-Python/`  
**Handoff:** nodo `160`, `PENDING_STEP1`, paso 1, target `NO REGISTRADO`.  
**Fuente seleccionada:** `README.md`; verifica CLI `cyclonedx-py` y SBOM desde environments, requirements, Pipenv y Poetry; función interna única `NO VERIFICADA`.  
**Determinista:** Sí — ≈99% para misma fuente/configuración/versión.  
**¿Es agente?:** No.  
**Cómo funciona el kernel/core para tomar decisiones:** inspecciona fuente Python, normaliza componentes/relaciones y serializa CycloneDX; no decide objetivos agentic.  
**Microflujo horizontal:** `environment|requirements|Pipenv|Poetry → parse → componentes/relaciones → modelo CycloneDX → serialización → SBOM`  
**Contexto estructural:** CLI, entornos virtuales, manifests/lockfiles, taxonomías y formatos SBOM.  
**Nivel seleccionado:** supply-chain inventory / provenance primitive.  
**Qué aporta a un agente:** trazabilidad de dependencias para auditoría, provenance, seguridad y reproducibilidad.

## Estado del bloque
`COMPONENTES_DOCUMENTADOS = 30` · `RANGO = 26-30` · `TOTAL_COMPONENTES_INVENTARIO_FRESH = 229` · `SIGUIENTE_BLOQUE = 31-35` · `ARCHIVO_SIGUIENTE = readme índice componentes 7 .md`
