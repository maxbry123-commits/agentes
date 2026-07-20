# Agent Skills Hub — ⭐⭐⭐⭐☆

## Datos básicos
- **URL canónica**: `github.com/agent-skills-hub/hub` (a confirmar)
- **Tipo**: comunidad + voting
- **Tier**: 1 estrella menos que los dos anteriores (madurez media)

## Qué aporta vs los otros 3
- **Voto comunitario**: cada skill tiene upvotes/downvotes.
- **Comentarios**: hilo de discusión por skill.
- **Trending**: detección rápida de skills nuevas populares.

## Plan de integración
1. Pull diario de `trending` (top 50).
2. Para cada uno: si tiene >100 votes positivos, considerar para incluir.
3. Si no, solo archivar metadata (no descargar).
4. Upsert en `02-skill` con tag `source:agent-skills-hub` y `votes:N`.

## Pendiente
- [ ] Verificar si expone RSS o solo web.
- [ ] Política anti-spam: ¿cómo distinguir una skill real de una con votos comprados?
- [ ] Rate limit del scraper (no más de 1 req/2s).
