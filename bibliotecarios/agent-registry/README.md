# AgentRegistry — ⭐⭐⭐⭐⭐

## Datos básicos
- **URL canónica**: `github.com/agentregistry/registry` (a confirmar en próximo turno con research)
- **Tipo**: registry universal de agents + skills + tools
- **Tier**: el más completo según el prompt M3
- **Schema**: propio (JSON), no estándar HOL todavía

## Qué aporta vs los otros 3
- **Cobertura**: lista los 4 ejes (agent, skill, tool, mcp) en un solo registro.
- **Métrica**: expone `popularity`, `last_release`, `health_score`.
- **API**: REST + CLI (`arctl`).

## Plan de integración
1. Clonar repo upstream en `~/research/agent-registry/` (no en este repo).
2. Comparar su schema con el nuestro (`01-agent`).
3. Mapping 1-a-1 + lista de gaps.
4. Sincronizar daily: fetch remote → transformar → upsert en `02-skill` local.

## Pendiente
- [ ] Confirmar URL y licencia.
- [ ] Probar `arctl list` con API key.
- [ ] Medir latencia de su API pública.
