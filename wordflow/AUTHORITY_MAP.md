# G0.01 AUTHORITY MAP — TEAM SEALS / Wordflow
Fecha: 2026-08-09
Commit: materializado en repo

## JERARQUÍA DE AUTORIDAD (fija)

1. Wordflow / ControlBus          → MANDO SUPREMO
   - Goals, Budget, Sheriff, Events, State, Recovery
   - Única fuente de verdad de decisión
   - Puede abortar / pausar / reasignar cualquier job

2. OpenClaw                       → UI + CAPABILITIES
   - Interfaz, tools, skills, MCP, canales
   - NO decide goals ni prioriza
   - Solo ejecuta lo que Wordflow autoriza
   - Agent-loop libre = PODAR

3. Hermes                         → MÚSCULO
   - Workers, colas, memoria de ejecución
   - Planner libre = PODAR
   - Solo recibe jobs ya autorizados por Wordflow

4. KER Extensions                 → CAPACIDADES EXTENDIDAS
   - Parallel / Swarm / Harness / Connectivity / Evolution
   - Nunca en el núcleo de autoridad
   - Se montan vía ABI (DUAL.02)

## REGLA DE ORO
Wordflow decide → OpenClaw presenta → Hermes ejecuta → KER amplía.
Nadie por encima de Wordflow.
