# PIPELINE como guía de plan (NO runtime)

## Dónde vive
```
PROJECT/
  plan/
    pipeline/
      AUDIT_INDEX.md
      PIPELINE_00.md
      PIPELINE_01_02.md
      ...
  PROJECT_MANIFEST.md          # D1 apunta docs.plan
```

## Qué es
Mapa verificable de las **21 fases** del roadmap + trazabilidad de documentos.
Apoyo a programación y auditoría. **No** se ejecuta en loops.

## Cómo Wordflow lo “sabe diseñar”
1. Lee `templates/pipeline/FASE_TEMPLATE.md` + `AUDIT_INDEX_TEMPLATE.md`
2. Exige índice verificado antes de fases
3. Cada fase: raíz extendida · DEBE/NO DEBE · sello 10 roles · técnica+simple
4. Docs pequeños (nunca un solo archivo gigante)
5. Mapeo opcional → UOOS B1–B4 (documental, no auto-ejecuta)

## Roadmap 21 fases (índice fijo)
00 núcleo · 01 idea · 02 requisitos · 03 arquitectura · 04 UX · 05 desarrollo ·
06 testing · 07 seguridad · 08 DevOps · 09 ops · 10 mantenimiento · 11 IA/agentes ·
12 biblioteca · 13 gobernanza · 14 mejora · 15 producto · 16 datos · 17 UX research ·
18 docs · 19 automatización · 20 analítica

## Relación con D1–D10
D1 declara `docs.plan: plan/` · D7 plan/ aloja pipeline · D2/D3/D4 no se mezclan con fases narrative.
