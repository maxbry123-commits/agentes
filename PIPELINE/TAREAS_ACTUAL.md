# TAREAS_ACTUAL.md — post-audit chat (2026-08-17 21:20)
**Total salidas hasta ahora:** 12+

## Estado por tarea

| ID | Tarea | Estado | Notas |
|----|-------|--------|-------|
| T0 | 4 motors nativos + reception + knowledge + método | **PARCIAL (90%)** | motors+reception+knowledge DONE. Residual: bridge full + method copy más repos |
| T2 | Reception/conversion motor (leo literal → gaps → ruta exacta + PLUGIN + md→py/json) | PENDIENTE | Depende T0 residual |
| T2.1 | SDPA (vía T2) | PENDIENTE | |
| T2.2 | MCR (vía T2) | PENDIENTE | |
| T2.3 | 20M contexto (vía T2) | PENDIENTE | |
| CG | Code-gen DSL/DAG/schema desde todos los prompts | PENDIENTE | |
| ARCH | Tarea arquitectura final (última) | PENDIENTE | |
| DEL | Delete mavis-deploy-keys (workflow) | PENDIENTE | |

## Orden de ejecución
1. Cerrar residual T0 (bridge + method)
2. T2
3. T2.1 / T2.2 / T2.3 (en paralelo o secuencia vía T2)
4. CG
5. ARCH (última)
6. DEL cuando se autorice

## Enlaces clave T0
- ARQUITECTURA live: https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/ARQUITECTURA_WORDFLOW_LIVE.md
- Motors: https://github.com/maxbry123-commits/agentes/tree/main/extensions/wordflow/motors
- Knowledge links: https://github.com/maxbry123-commits/agentes/blob/main/extensions/wordflow/reception/KNOWLEDGE_RECEPTION_LINKS.md
