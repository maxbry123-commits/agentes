PROMPT PARA SOL - Investigar capacidad frontend real de los 18 agentes
Corregido 2026-09-17: antes solo se mencionaba, nunca se escribio el prompt.

SOL GPT - INVESTIGACION CAPACIDAD FRONTEND FLEET - AGENTE YAIWES

schema: yaiwes.component-ops/v1
repo: maxbry123-commits/agentes
branch: main
modo: FAIL_CLOSED_STRICT_3_STEPS

FUENTE OBLIGATORIA (leer fresh):
wordflow_loop/wordflow_loop/agent_fleet/agent_fleet_registry.json (15.9KB,
ya contiene los 18 agentes: OpenCode, OpenHands, Claude Code, MiMo Code,
Codex, SmolAgents, Hermes, OpenClaw, Aider, Muse/Glimmer, Kimi, Qwen Code,
Cline, Goose, Agent-Zero, OpenDev, Research Agent Lab, MiroThinker)

OBJETIVO
Para CADA uno de los 18 agentes: investigar su codigo fuente/documentacion
REAL (no adivinar) y confirmar si tiene capacidad nativa de:
1. browser_use (puede abrir y controlar un navegador real)
2. screenshot_capability (puede tomar capturas de pantalla)
3. visual_verification (puede comparar resultado visual esperado vs real)

PASOS (maximo 3)
1. RESEARCH: para cada agent_id del registry, buscar su repo/documentacion
   oficial. Fuentes: GitHub del proyecto, HuggingFace si aplica, comunidad
   de desarrolladores.
2. EXECUTE: escribir el resultado como campo nuevo en cada entrada del
   agent_fleet_registry.json: "frontend_capability": {"browser_use": bool,
   "screenshot": bool, "visual_verify": bool, "evidence_url": "..."}
3. VALIDATE: cada campo debe tener evidence_url (no se acepta "creo que
   si" sin fuente).

REGLAS
- No inventar la respuesta si no se encuentra evidencia - marcar
  "unknown": true en ese caso, nunca asumir true ni false.
- No modificar ningun otro campo del registry existente.

REPORTA EN: Crazy Wall de este repo (el de la raiz principal, no el de
Crazy Wall Orquestador - ver Anexo sobre la duplicidad detectada).

INICIA AHORA.
