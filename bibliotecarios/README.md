# 📚 Bibliotecarios de Skills — 4 proyectos + 2 capas

> Documento canónico: prompt M3 DSL DAG SHERIFF V7, sección G.

## Comparativa rápida

| # | nombre | tier | url/ubicación | foco | madurez |
|---|--------|------|---------------|------|---------|
| 1 | **AgentRegistry** | ⭐⭐⭐⭐⭐ | github.com/agentregistry/registry | el más completo, registry universal | alta |
| 2 | **SkillHub** | ⭐⭐⭐⭐⭐ | github.com/skillhub/skillhub | marketplace de skills curadas | alta |
| 3 | **Agent Skills Hub** | ⭐⭐⭐⭐☆ | github.com/agent-skills-hub/hub | comunidad, voting | media |
| 4 | **skills-registry** | ⭐⭐⭐⭐☆ | github.com/skills-registry/registry | estandar JSON Schema | media |
| + | **OpenAgentSkill** | capa | github.com/openagentskill/oas | selección automática basada en OpenAI function-calling | nueva |
| + | **HOL Registry** | capa | universal-agentic-registry.org | registry universal multi-vendor | experimental |

## Estrategia de integración

M3 **no se casa con uno solo**. Mantiene los 4 bibliotecarios como **fuentes upstream** que se sincronizan a nuestro `02-skill` registry local con cadencia diaria, y un motor de **deduplicación + scoring** que decide qué skills conservar.

```
┌────────────┐ ┌────────────┐ ┌──────────────┐ ┌──────────────┐
│ AgentReg.  │ │ SkillHub   │ │ AgentSkillH. │ │ skills-reg.  │
└─────┬──────┘ └─────┬──────┘ └──────┬───────┘ └──────┬───────┘
      │              │              │                │
      └─────┬────────┴──────┬───────┘                │
            │               │                        │
            ▼               ▼                        ▼
        ┌──────────────────────────────────────────────────┐
        │   Sync engine (cron diario) + dedupe + scoring   │
        └─────────────────────────┬────────────────────────┘
                                  │
                                  ▼
                  ┌──────────────────────────┐
                  │  02-skill registry (local)│
                  └──────────────────────────┘
```

## OpenAgentSkill (capa de selección automática)
Capa que envuelve los 4 bibliotecarios + nuestro registry local y decide, dada una tarea, **qué skill cargar primero**. Usa los `agent_card` y `skill_card` del AI Registry como input.

## HOL Registry (Universal Agentic Registry)
Estándar propuesto para que un agent registry pueda federarse con otro. Nuestro `01-agent` se publicará como `hol` entry para que otros sistemas nos descubran.

## Tareas pendientes
- [ ] Levantar un sync engine mínimo en HF Space (no VPS).
- [ ] Política de dedupe: hash de (name + entry) → mismo skill de distintas fuentes = 1 entry.
- [ ] Política de scoring inicial: favor aquellos con >100 estrellas en GitHub.
- [ ] Publicar nuestro `01-agent` en formato HOL.
