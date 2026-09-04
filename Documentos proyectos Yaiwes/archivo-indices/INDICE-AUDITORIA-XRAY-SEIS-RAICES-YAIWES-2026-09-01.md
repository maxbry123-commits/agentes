# Índice maestro — Auditoría forense X-Ray de las seis raíces YAIWES

**Corte:** 2026-09-01 · **Repo:** `maxbry123-commits/agentes@main`  
**Alcance:** auditoría separada por cada raíz definida en los tres Crazy Wall de Grok. Este índice solo cablea documentos; no implementa código.

## Fuentes recibidas

- [Crazy Wall v2](https://github.com/maxbry123-commits/agentes/blob/main/FUENTE-GROK-YAIWES-CRAZY-WALL-v2.html)
- [Crazy Wall v3](https://github.com/maxbry123-commits/agentes/blob/main/FUENTE-GROK-YAIWES-CRAZY-WALL-v3.html)
- [Crazy Wall v4](https://github.com/maxbry123-commits/agentes/blob/main/FUENTE-GROK-YAIWES-CRAZY-WALL-v4.html)
- [Arquitectura fusionada YAIWES](https://github.com/maxbry123-commits/agentes/blob/main/README-ARQUITECTURA-FUSIONADA-YAIWES-XRAY-2026-09-01.md)

## Auditorías por raíz

| Raíz declarada | Auditoría | Estado verificado |
|---|---|---|
| R1 `Desplegar/` | [Abrir](https://github.com/maxbry123-commits/agentes/blob/main/AUDITORIA-RAIZ-R1-DESPLEGAR-XRAY-2026-09-01.md) | No existe; alternativa vacía |
| R2 `PIPELINE/` | [Abrir](https://github.com/maxbry123-commits/agentes/blob/main/AUDITORIA-RAIZ-R2-PIPELINE-XRAY-2026-09-01.md) | Existe; documental, sin owner ejecutable |
| R3 `Método de trabajo/` | [Abrir](https://github.com/maxbry123-commits/agentes/blob/main/AUDITORIA-RAIZ-R3-METODO-TRABAJO-XRAY-2026-09-01.md) | Existe; dual home y enforcement parcial |
| R4 `Refactoria/` | [Abrir](https://github.com/maxbry123-commits/agentes/blob/main/AUDITORIA-RAIZ-R4-REFACTORIA-XRAY-2026-09-01.md) | Parcial; falta inventario y paridad |
| R5 `Yaiwes wordflow/` | [Abrir](https://github.com/maxbry123-commits/agentes/blob/main/AUDITORIA-RAIZ-R5-YAIWES-TEAM-KERNEL-XRAY-2026-09-01.md) | Etiqueta ausente; cuerpo distribuido; TEAM incompleto |
| R6 `Wordflow Code/` | [Abrir](https://github.com/maxbry123-commits/agentes/blob/main/AUDITORIA-RAIZ-R6-WORDFLOW-CODE-XRAY-2026-09-01.md) | Etiqueta ausente; runtime vivo en extensions |

## Diagnóstico global

- 2 de 6 raíces autorizadas no existen con el nombre exacto: R1 y las etiquetas R5/R6.
- R5 y R6 tienen cuerpos reales en otras rutas, creando dual homes y enlaces frágiles.
- TEAM no existe como paquete ejecutable único.
- El kernel principal nuevo conserva 18 placeholders y no tiene tests propios.
- La arquitectura `agente-yaiwes/` contiene 124 placeholders.
- Wordflow Code posee el runtime más fuerte, pero continúa distribuido entre dos repositorios y un espejo.
- Los PASS históricos deben leerse por alcance; no cierran el producto integral.

## Veredicto

**GLOBAL: FAIL-CLOSED / PARCIAL.** Cada raíz conserva arriba su inventario, errores, faltantes y ubicación real.