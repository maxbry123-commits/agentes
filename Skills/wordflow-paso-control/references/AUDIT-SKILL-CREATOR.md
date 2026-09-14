# AUDIT skill-creator vs wordflow-paso-control 1.1.0

## skill-creator hard rules

- name kebab = dir name PASS
- description unquoted no colon-space no angle PASS
- frontmatter only spec keys PASS (custom under metadata)
- body imperative PASS
- SKILL.md < 500 lines target
- long lists in references PASS
- scripts referenced from body PASS 1.1.0
- no README/CHANGELOG PASS

## gaps 1.0.0 (cerrados en 1.1.0)

1. PASO 0 audit 3 repos zip guia AUSENTE -> agregado
2. PASO 1 sin lista 01-20 explicita -> agregada + blob lock
3. PASO 2 no creaba Download code antes de Download N -> ahora mkdir ambos
4. OP1 no decia enrutar TODOS los repo y usar PARTE -> ahora si
5. OP2 no decia fork+raiz nueva en main -> ahora si
6. PASO 3 no exigia UOOS+ficha antes de plugin -> ahora si
7. PASO 4 sin workflow_dispatch / fetch-depth / token dest / plugin post-copy -> PASO-DETALLE + tarjeta
8. PASO 5 habia reemplazado emojis Director por prefix -> alias restaurados + hash security
9. PASO 6 no verificaba deploy al FINAL del runner ni docs Desplegar 1 -> ahora si
10. PASO 7 no BUSCABA el prompt para COPIAR estandares dentro -> ahora si
11. PASO 8 mezclaba OUT y X-Ray -> tarjetas separadas + registry
12. Overview y EVIDENCE schema ausentes (plantilla skill-creator) -> agregados

## still HOLD

- owner C username
- valor secret Maxbry_123_tokens (UI)
- Tarea 3 copias
- UOOS paths exactos si 404 en SOURCE-MAP
