DECISION DE DISENO - OBJETIVO DEL OSQUESTADOR + ORCA COMO BACKEND INTERNO
2026-09-17, corregido tras error real de destino ambiguo en prompt anterior

## CONCEPTO CENTRAL (verbatim del Director, confirmado por Claude)
El Director decide el objetivo (el jugador). Quien opera el "joystick" -
quien ejecuta y controla cualquier interfaz o componente - es YAIWES,
nunca el Director directamente.

## APLICACION A ORCA (corregido, ya no va como componente de kernel)
Orca NO se instala como carpeta de componente. Se investiga su logica de
coordinacion interna y ESA LOGICA se extrae/adapta hacia:
- agent_fleet/agent_fleet_adapter.py, o
- Seals team YAIWES/Comand Center/comandante_tactico_seal.py
El Director nunca ve ni opera Orca directamente - es backend invisible.

## OBJETIVO DE PERSISTENCIA DEL OSQUESTADOR - 2 propuestas, sin decidir
1. Aprender a ejecutar y dar ordenes
2. Eliminar friccion total - el agente opera todo internamente
PENDIENTE DE DECISION FINAL DEL DIRECTOR.

## ERROR CORREGIDO (para no repetir)
Omniroute -> wordflow_loop/runtime/src/conn/
Orca -> NO se descarga, se investiga y extrae logica
Omarchy -> NO APLICA como componente de repo, es infraestructura
Anydoc -> Motores de descarga y extraccion/anydoc/
Skill Design Anthropic -> Skills agente/skill-design-anthropic/
