# R5 — Auditoría forense X-Ray de `Yaiwes wordflow/` y Agente TEAM

**Índice maestro:** [Auditoría X-Ray de las seis raíces](https://github.com/maxbry123-commits/agentes/blob/main/INDICE-AUDITORIA-XRAY-SEIS-RAICES-YAIWES-2026-09-01.md)  
**Fuentes Grok:** [v2](https://github.com/maxbry123-commits/agentes/blob/main/FUENTE-GROK-YAIWES-CRAZY-WALL-v2.html) · [v3](https://github.com/maxbry123-commits/agentes/blob/main/FUENTE-GROK-YAIWES-CRAZY-WALL-v3.html) · [v4](https://github.com/maxbry123-commits/agentes/blob/main/FUENTE-GROK-YAIWES-CRAZY-WALL-v4.html)  
**Método:** árbol Git recursivo + archivos reales + comparación contra Crazy Wall. No se modificó código.

## Ubicación correcta

La etiqueta exacta `Yaiwes wordflow/` **no existe** en main. Su cuerpo declarado está en:

- [`agente-yaiwes/`](https://github.com/maxbry123-commits/agentes/tree/main/agente-yaiwes)
- [`extensions/wordflow_kernel/`](https://github.com/maxbry123-commits/agentes/tree/main/extensions/wordflow_kernel)
- [`extensions/wordflow/`](https://github.com/maxbry123-commits/agentes/tree/main/extensions/wordflow)
- `control-layer/`
- Documentos TEAM en `PIPELINE/03_TEAM_KERNEL_PARTE1.md` y `06_PERFIL_MAESTRO_TEAM_SEALS.md`.

## Huella real

### `agente-yaiwes/`
- 586 entradas, 430 archivos, 156 directorios.
- 234 Python, 142 Markdown, 13 YAML.
- **124 rutas PLACEHOLDER/PENDIENTE**.
- Solo 2 tests Python dentro de esta nueva raíz.

### Kernel real más cercano
- `extensions/wordflow_kernel/`: 94 Python, 27 tests.
- `agente-yaiwes/kernel-principal/`: 49 Python, 18 placeholders, 0 tests propios.
- `runtime.py` y `workflow.py` del nuevo kernel son blobs idénticos a los de `extensions/wordflow_kernel`: espejo, no kernel independiente.

## Agente TEAM/Fables

No existe paquete o raíz ejecutable `Agente TEAM`. No aparece una marca verificable de autoría “Fables 5”. TEAM existe como diseño documental y como piezas distribuidas.

## Errores y faltantes

1. No existe `python -m agente`, `__main__.py` ni puerta CLI canónica.
2. Reception→misión→cierre no está demostrado como un solo proceso dueño.
3. Reasoning kernel contiene placeholders en decision-on-demand, consensus, goals y capacity.
4. Ask-Consil 12 no aparece como FSM ejecutable.
5. OpenClaw/Hermes continúan como stubs.
6. Hay FakeRepoTruth/FakeGitDataPort/GATEWAY_STUB en rutas de demostración.
7. No existe DecisionEngine SDPA único, Merkle state global ni logger determinista integral.
8. Los 502 ZIP de `Agente core kernel Yaiwes principal/` son almacén, no capacidades montadas.

## Estado

**TEAM/YAIWES KERNEL: PARCIAL, aproximadamente consistente con el 30–40% funcional indicado por Grok.**  
La base es reutilizable, pero no hay agente TEAM autónomo ni cierre E2E.