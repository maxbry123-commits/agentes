# R6 — Auditoría forense X-Ray de `Wordflow Code/`

**Índice maestro:** [Auditoría X-Ray de las seis raíces](https://github.com/maxbry123-commits/agentes/blob/main/INDICE-AUDITORIA-XRAY-SEIS-RAICES-YAIWES-2026-09-01.md)  
**Fuentes Grok:** [v2](https://github.com/maxbry123-commits/agentes/blob/main/FUENTE-GROK-YAIWES-CRAZY-WALL-v2.html) · [v3](https://github.com/maxbry123-commits/agentes/blob/main/FUENTE-GROK-YAIWES-CRAZY-WALL-v3.html) · [v4](https://github.com/maxbry123-commits/agentes/blob/main/FUENTE-GROK-YAIWES-CRAZY-WALL-v4.html)  
**Método:** árbol Git recursivo + archivos reales + comparación contra Crazy Wall. No se modificó código.

## Ubicación correcta

La etiqueta exacta `Wordflow Code/` **no existe** actualmente en `agentes@main`.

- Runtime vivo: [`extensions/wordflow/`](https://github.com/maxbry123-commits/agentes/tree/main/extensions/wordflow)
- Hot path: [`code_path_runner.py`](https://github.com/maxbry123-commits/agentes/blob/main/extensions/wordflow/engine/code_path_runner.py)
- Raíz documental trasladada: [`nct-core/Wordflow Code`](https://github.com/maxbry123-commits/nct-core/tree/main/Wordflow%20Code)
- Espejo lógico: `agente-yaiwes/code-programming-engine/`.

## Huella runtime

- `extensions/wordflow/`: 403 entradas, 379 archivos.
- 310 Python, 134 tests, 13 YAML y 20 Markdown.
- Es la raíz con mayor evidencia ejecutable del sistema.

## Errores y faltantes

1. Dualidad entre runtime en `agentes`, documentos en `nct-core` y espejo en `agente-yaiwes`.
2. Los módulos p01–p12 sí existen, pero p01–p11 miden 108–109 bytes y p12 157 bytes: son stubs, no pipeline modular completo.
3. `code_path_runner.py` es real; su espejo no alcanza paridad funcional.
4. Pool/adapters reales incompletos; OpenClaw/Hermes son stubs.
5. Estado/ledger/checkpoint no son obligatorios en toda ejecución.
6. No hay E2E único misión→runner→tests→evidence→output-consumed.
7. El README de nct-core todavía apunta al repo `agentes`, confirmando raíz documental copiada.
8. La etiqueta ausente rompe enlaces que esperen `main/Wordflow Code`.

## Estado

**RUNTIME REAL Y MADURO PARCIAL; ARQUITECTURA DISTRIBUIDA INCOMPLETA.**  
No mover ni reescribir el hot path hasta paridad de imports, tests, evidencia y rollback.