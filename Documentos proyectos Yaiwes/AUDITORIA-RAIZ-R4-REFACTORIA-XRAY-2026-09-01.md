# R4 — Auditoría forense X-Ray de `Refactoria/`

**Índice maestro:** [Auditoría X-Ray de las seis raíces](https://github.com/maxbry123-commits/agentes/blob/main/INDICE-AUDITORIA-XRAY-SEIS-RAICES-YAIWES-2026-09-01.md)  
**Fuentes Grok:** [v2](https://github.com/maxbry123-commits/agentes/blob/main/FUENTE-GROK-YAIWES-CRAZY-WALL-v2.html) · [v3](https://github.com/maxbry123-commits/agentes/blob/main/FUENTE-GROK-YAIWES-CRAZY-WALL-v3.html) · [v4](https://github.com/maxbry123-commits/agentes/blob/main/FUENTE-GROK-YAIWES-CRAZY-WALL-v4.html)  
**Método:** árbol Git recursivo + archivos reales + comparación contra Crazy Wall. No se modificó código.

## Lo declarado

`vivo → source → new → verificación ×3 → canónico`. Debe guardar clasificación, copias y evidencia sin tocar el runtime vivo.

## Huella real

- 70 entradas: 43 archivos, 27 directorios.
- 15 Python, 24 Markdown, 3 tests Python.
- Directorios G1–G7, Refactoria 2–5 y copias de skills.
- `Refactoria/inventario.csv` declarado por Crazy Wall: **no existe**.
- `Refactoria Yaiwes/`: solo `.keep`.

## Errores y faltantes

1. Falta el inventario CSV que debe clasificar los restos.
2. Múltiples subraíces numeradas no tienen un índice de autoridad único.
3. No se demuestra paridad ×3 para todos los elementos movidos.
4. No hay matriz completa source SHA→new SHA→tests→destino.
5. Solo 3 tests Python para una raíz con 15 módulos.
6. Las copias de skills pueden divergir de sus fuentes canónicas.
7. La raíz no demuestra cutover ni rollback global.

## Estado

**PARCIAL.** Hay material de refactor y recuperación, pero la clasificación y trazabilidad no están cerradas.