# Handoff seals team.md

## Que es esto
El primer agente ejecutor determinista del enjambre Seals Team. Un solo
codigo, N copias (Seals team 1, 2, 3 YAIWES), cada una diferenciada solo
por su task_contract.json.

## Donde esta cada cosa
- Seals team.md -> constitucion (reglas duras, nunca cambian)
- dag_schema.yaml -> el flujo fijo de nodos, sin LLM decidiendo el flujo
- seals_core/ejecutor.py -> el router 90/10 (if/elif real)
- seals_core/instalador_deterministico.py -> git clone + pip install, 0% LLM
- seals_core/consultor_experto.py -> el 5-10% LLM via Cerebras
- seals_core/verificador.py -> gate final, puede pasar por Claude (bajo volumen)
- watchdog.py -> se activa si no hay tareas, revisa el inventario
- Seals team 1 YAIWES/task_contract.json -> que nodo reclama esta copia
- _fuentes_extraidas/ -> mecanismos extraidos de Muse-Agent y MUSE-KnowledgeXLab (evidencia en EXTRACTION_EVIDENCE_MUSE.json)

## Fuentes de tareas
Lee siempre fresco antes de reclamar:
- Inventario oficial: Core kernel Yaiwes/CORE-KERNEL-COMPONENT-INVENTORY.json
- Crazy Wall: raiz del repo, Bitacora stated JSON Craxy wall.json

## Estado (2026-09-15)
Agente base creado. Pendiente: escribir seals_core/*.py, probar 1 copia
contra 1 nodo real del inventario, validar con evidencia, luego clonar.

## Como retomar si se pierde el contexto
Lee este archivo + Seals team.md + Claude readme/Readme Claude.md (memoria
del orquestador). No se ha activado ninguna copia todavia - primero se
prueba 1 sola.
