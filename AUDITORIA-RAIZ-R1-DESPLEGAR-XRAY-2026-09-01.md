# R1 — Auditoría forense X-Ray de `Desplegar/`

**Índice maestro:** [Auditoría X-Ray de las seis raíces](https://github.com/maxbry123-commits/agentes/blob/main/INDICE-AUDITORIA-XRAY-SEIS-RAICES-YAIWES-2026-09-01.md)  
**Fuentes Grok:** [v2](https://github.com/maxbry123-commits/agentes/blob/main/FUENTE-GROK-YAIWES-CRAZY-WALL-v2.html) · [v3](https://github.com/maxbry123-commits/agentes/blob/main/FUENTE-GROK-YAIWES-CRAZY-WALL-v3.html) · [v4](https://github.com/maxbry123-commits/agentes/blob/main/FUENTE-GROK-YAIWES-CRAZY-WALL-v4.html)  
**Método:** árbol Git recursivo + archivos reales + comparación contra Crazy Wall. No se modificó código.

## Lo declarado

`lote → destino canónico → si pisa vivo: Refactoria`. Debía existir una bandeja `Desplegar/inbox/`.

## Lo encontrado

- `Desplegar/`: **no existe**.
- `Desplegar/inbox/`: **no existe**.
- `Desplegar Yaiwes/`: existe únicamente con `.keep`.
- Hay otras raíces nominales `Desplegar nct/` y `Desplegar osquestador auditor memoria/`, pero no sustituyen el contrato YAIWES.
- Código de publicación aparece disperso bajo `agente-yaiwes/deploy-publish/` y documentación en `PIPELINE/`.

## Errores y faltantes

1. El nombre autorizado del Crazy Wall no coincide con el árbol.
2. No existe inbox de lote ni estado WAIT materializado.
3. No hay manifest único lote→destino→SHA→evidence.
4. El selector de destino permanece parcial/placeholder.
5. Los workflows de GitHub no convierten por sí solos esta raíz en pipeline de despliegue.
6. No se demuestra rollback ni witness posterior al push.

## Estado

**NO EXISTE como raíz funcional.** Existe una raíz alternativa vacía.  
**GAP bloqueante:** contrato de entrada, destino y evidencia no materializado.