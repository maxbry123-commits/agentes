# BRIDGE · Continuidad entre chats Grok
**Fecha:** 2026-08-07  
**Repo:** maxbry123-commits/agentes  
**Uso:** pegar §0 al inicio de otro chat con saldo disponible.

---

## §0 PEGAR EN EL OTRO CHAT

```text
PROYECTO: MAXBRY TEAM SEALS / Wordflow control-layer
Repo GitHub: maxbry123-commits/agentes

HECHO (no rehacer):
- control-layer W01–W17 (goals, budget, change, events, sheriff, input…)
- memory parcial: router, guard, local_provider, tencent adapter, tiers 0–3 incompletos
- agents/ sources: OpenClaw, Hermes, Claude-Code, Codex, Mimo-Code, Kimi, OpenClaw-headless
- docs/RECOVERY_PATCH_MEMORIA_PODA_2026-08-07.md
- docs BRIDGE, MEMORIA_GRAPH_OSQUEST, EVOLUTION_SYSTEM, CHECKPOINT_TAREAS

AUTORIDAD:
OpenClaw = UI + tools/skills/MCP (podar agent-loop libre)
Hermes = workers/cola/memoria ejecución (podar planner libre)
Wordflow ControlBus = mando (goals, budget, sheriff, events)
KER extensions = parallel/swarm/harness/connectivity/evolution (NO en núcleo)

CADENAS CODE CONFIRMADAS:
Backend:  OpenCode → OpenHands → Codex CLI → Claude Code CLI
Frontend: Cline → OpenHands → OpenCode → Codex → Kimi Code CLI → Mimo

REGLAS:
- 300 capabilities registradas ≠ 300 jobs concurrentes
- No tocar código existente sin preguntar si no mejora 10x
- Nunca from-scratch si hay source OS en manifest
- Graphiti/Grapify/OCR/n8n = nativos vía Evolution, no apps externas obligatorias
- Secrets solo CredentialBroker

ORDEN TAREAS:
G0 → DUAL → G1 → G2 → G3 → G4 → EVO → DOC → IO → G5 → G8 → DEP → G7 → G9

SIGUIENTE CONCRETA: leer CHECKPOINT_TAREAS_PENDIENTES.md y continuar G0.01 o EVO.01 según prioridad usuario.
Leer también: EVOLUTION_SYSTEM.md + MEMORIA_GRAPHITI_OSQUESTADOR.md
```

---

## Qué estamos haciendo

Construir **TEAM SEALS**: agente que fusiona Wordflow (control determinista) + OpenClaw (UI/capabilities) + Hermes (músculo), con **evolución nativa** (agentes, skills, software OS, datasets) y memoria Control Plane sin depender de Obsidian/Graphiti como SaaS obligatorio.

## Docs ancla en repo

| Doc | Path |
|-----|------|
| Recovery memoria/poda | `control-layer/docs/RECOVERY_PATCH_MEMORIA_PODA_2026-08-07.md` |
| Este bridge | `control-layer/docs/BRIDGE_OTRO_CHAT_GROK.md` |
| Memoria Graphiti/OCR/Osquest | `control-layer/docs/MEMORIA_GRAPHITI_OSQUESTADOR.md` |
| Evolución 5 modos + binarios | `control-layer/docs/EVOLUTION_SYSTEM.md` |
| Checkpoint tareas | `control-layer/docs/CHECKPOINT_TAREAS_PENDIENTES.md` |
