# SkillHub — ⭐⭐⭐⭐⭐

## Datos básicos
- **URL canónica**: `github.com/skillhub/skillhub` (a confirmar)
- **Tipo**: marketplace de skills curadas
- **Tier**: igual que AgentRegistry
- **Diferenciador**: curaduría humana + ranking editorial

## Qué aporta vs los otros 3
- **Curaduría**: cada skill pasa por un humano antes de listarse.
- **Ranking editorial**: top semanal, top mensual, featured.
- **Categorías explícitas**: `code`, `research`, `data`, `ops`, `ui`.

## Plan de integración
1. Pull de su `top-300` semanal.
2. Filtrar por categorías que nos interesan.
3. Hacer `git clone` por skill (cuando aplique) y correr validador estático.
4. Upsert en `02-skill` con tag `source:skillhub`.

## Pendiente
- [ ] Confirmar si tiene API pública o solo scrappeable.
- [ ] Política de licencia de las skills (¿MIT? ¿Apache?).
- [ ] Identificar cuáles de los "Top 100 herramientas" del prompt M3 ya están en SkillHub.
