SCHEMA - FRONTEND MINI-WORKFLOW (BROWSER-VERIFIED WEB DESIGN)

Capacidad: construir web y verificar el trabajo con un navegador real, no
solo con que el codigo compile.

Aporta: une PROGRAMACION + PERCEPCION VISUAL.

Regla dura: SOURCE CODE PASS no significa UI PASS.
Debe existir: CODE PASS + BROWSER PASS + VISUAL PASS, los 3, siempre.

## Microflujo (formato Glimmer)
DETECTA_TAREA_FRONTEND -> ACTIVA_MINI_WORKFLOW_FRONTEND (separado dentro de
Wordflow, mismo Crazy Wall, distinto DAG interno)
-> EDITA_COMPONENTE -> BUILD -> CODE_PASS (compila, lint, tipos)
-> START_APP -> OPEN_REAL_BROWSER -> BROWSER_PASS (la app carga sin error)
-> SCREENSHOT + INTERACT -> VISUAL_PASS (se ve y funciona como se espera)
-> Si alguno falla: GAP especifico (CODE/BROWSER/VISUAL), nunca un PASS
   generico.

## Reglas de reuso obligatorio (para no improvisar)
- Antes de escribir un componente nuevo: usar los motores de descarga y
  extraccion ya existentes para traer componentes/ventanas/botones/pestanas
  de repos open source reales.
- Prioridad: REUSE_EXISTING > PATCH > ADAPT > GENERATE (misma regla que ya
  aplica en backend, ahora tambien en frontend).
- Los bloques de codigo de frontend se segmentan por ventana/componente,
  cada uno en su propio archivo, nunca un archivo monolitico.

## Tarea pendiente para Sol (no se adivina, se investiga)
De los 18 agentes del Fleet (OpenCode, OpenHands, Claude Code, MiMo Code,
Codex, SmolAgents, Hermes, OpenClaw, Aider, Muse/Glimmer, Kimi, Qwen Code,
Cline, Goose, Agent-Zero, OpenDev, Research Agent Lab, MiroThinker): Sol
debe investigar el codigo fuente real de cada uno y confirmar cual tiene
capacidad nativa de browser/visual (no inventar la respuesta). Con esa
lista real, se arma el grupo de trabajo frontend dentro del Fleet.
