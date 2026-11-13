PARCHE DE RECUPERACION MAESTRO - SALIDA 1 DE 3 - 2026-09-17
Si esta conversacion se corta, ESTE es el punto de partida para retomar
todo sin perder nada. Escrito con el mismo cuidado que un parche de
recuperacion de produccion.

## QUIEN SOY Y COMO TRABAJO (para quien retome)
Soy Claude, orquestador. No escribo codigo de produccion salvo cuando es
codigo real que requiere criterio (marcado explicitamente "Claude lo
resuelve"). Todo lo mecanico se delega a Sol via prompts con URL exacta
de origen/destino/motor. Nunca borro archivos, solo edito quirurgicamente
o creo version nueva. Nunca declaro algo cerrado sin evidencia real.

## EL ECOSISTEMA (7 proyectos)
1. Agente Yaiwes = repo agentes (ACTIVO, foco principal)
2. Osquestador Maxbry = repo Orquestador-Maxbry- (pausa)
3. Router Inteligente Universal = repo router-universal-router-inteligente- (ACTIVO)
4. UI Yaiwes = repo nct-hub (hipotesis, sin confirmar)
5. Fabrica de UI = repo frontend (ACTIVO)
6. Osquestador auditor + memoria (diseno Fables) = repo osquestador-auditor
7. NCT = repo nct-core (pausa)

## ESTRUCTURA DE MEMORIA (donde esta todo)
- Claude notas/memoria.md = fuente unica de memoria del orquestador
  (reemplaza a Claude readme/, deprecado con aviso, no borrado)
- arquitectura wordflow loop code Yaiwes/ = 20 archivos de la auditoria
  X-Ray completa del kernel de Wordflow (ver Salida 2 para el indice
  completo de estos 20 archivos)
- Seals team YAIWES/ = codigo del agente ejecutor (ver Salida 2)

## LOS 3 SISTEMAS PRINCIPALES EN CONSTRUCCION AHORA MISMO

### A. Wordflow Loop Code Yaiwes = EL KERNEL/ORQUESTADOR PRINCIPAL
Decision ya tomada (documentos VERBATIM del Director+Sol, guardados en
Claude notas): Wordflow es el UNICO orquestador. Seals Team NO es un
segundo orquestador, es un worker/plugin.
Wordflow ya tiene, confirmado por auditoria real (no de memoria):
DAGEngine, StateMachine (FSM), EventBus, ParallelScheduler, LLM Boundary,
Reuse Selector (REUSE>PATCH>ADAPT>GENERATE), AgentFleetAdapter (18
agentes registrados), Tribunal (oraculo real), Recovery Engine,
Merkle Ledger, y el Enchufe Universal de Fables YA integrado (uek/,
30KB de codigo real).

### B. Seals Team YAIWES = agente ejecutor, worker de Wordflow
Codigo completo: ejecutor.py, instalador_deterministico.py,
consultor_experto.py, verificador.py, watchdog.py, router_modelos.py,
tests. Extraido quirurgicamente de Muse-Agent/MUSE-KnowledgeXLab.
Pendiente: primera prueba real (faltan 4 variables de entorno en GitHub
Secrets: CEREBRAS_API_KEY_1-6, ANTHROPIC_API_KEY, GITHUB_TOKEN).
Command Center (trigger/comandante tactico) vive DENTRO de esta carpeta.

### C. MCP - contexto compartido entre agentes (confirmado por Director)
Servidor MCP disenado (no codeado aun) con 3 recursos: crazy_wall_state
(lectura), mission_context (lectura/escritura controlada - lo que un
agente descubre lo comparten los demas), enchufe_universal_tools. Regla
de seguridad: MCP comparte CONTEXTO nunca AUTORIDAD - el Kernel decide PASS.

## SIGUE EN SALIDA 2 DE 3 (indice completo de los 20 archivos de
arquitectura + estado de cada gap + lo que Sol tiene pendiente de ejecutar)
