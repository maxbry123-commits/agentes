DISENO - MCP CONTEXTO COMPARTIDO ENTRE AGENTES - 2026-09-17
Confirmado por el Director: es MCP (Model Context Protocol, Anthropic).
Requisito adicional confirmado: el contexto que tiene un agente debe
poder compartirse con los demas, no solo con el kernel.

## QUE RESUELVE
Hoy, cada agente del Fleet (OpenCode, OpenHands, Codex, Claude Code, etc.)
tendria que integrarse a mano, uno por uno, con su propio adaptador. Con
un servidor MCP propio de Wordflow, cualquier agente COMPATIBLE con MCP
se conecta sin cableado adicional.

## ARQUITECTURA PROPUESTA

wordflow_loop/wordflow_loop/mcp_server/ (carpeta nueva a crear)
  - server.py: expone 3 recursos MCP
    1. crazy_wall_state (lectura): estado actual de nodos, tareas PENDING/
       CLAIMED/RUNNING/BLOCKED/VERIFIED_CLOSED
    2. mission_context (lectura/escritura controlada): el contexto de la
       mision actual - lo que UN agente descubrio (ej. "este componente
       ya fue investigado, aqui esta la evidencia") pasa a estar
       disponible para CUALQUIER OTRO agente conectado, sin que tengan
       que repetir la misma investigacion.
    3. enchufe_universal_tools (herramientas): expone las capacidades ya
       registradas en el UEK (universal_plugin_bus_v2_integrated.py) como
       tools MCP estandar.

## FLUJO
AGENTE_A (ej Codex) descubre algo -> ESCRIBE en mission_context via MCP
-> AGENTE_B (ej Claude Code, sesion distinta) SE CONECTA al mismo server
MCP -> LEE mission_context -> ya tiene la informacion sin repetir trabajo

## REGLA DE SEGURIDAD (aplicando lo ya establecido en toda la arquitectura)
El servidor MCP es SOLO LECTURA de decisiones de autoridad (nunca un
agente conectado via MCP puede escribir directo al Crazy Wall o cambiar
un estado FSM) - eso sigue siendo autoridad exclusiva del Kernel. MCP
comparte CONTEXTO (lo que se sabe), nunca AUTORIDAD (lo que se decide).
Mantiene la regla ya establecida: LLM propone, runtime autoriza.

## ESTADO
DISENO PROPUESTO, CODIGO NO ESCRITO TODAVIA. Es un item de codigo real
(no mecanico) - Claude lo construye cuando el Director lo apruebe, no
se le da a Sol por ser justamente la pieza que requiere criterio de
arquitectura, no ejecucion simple.
