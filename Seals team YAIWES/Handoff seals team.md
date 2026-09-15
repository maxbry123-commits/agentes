# Handoff seals team.md

## Estado: CODIGO COMPLETO. Solo falta prueba real.

## Que es esto
El primer agente ejecutor determinista del enjambre Seals Team. Un solo
codigo, N copias (Seals team 1, 2, 3 YAIWES), cada una diferenciada solo
por su task_contract.json.

## Archivos, todos terminados
- Seals team.md -> constitucion (reglas duras)
- dag_schema.yaml -> flujo fijo de 11 nodos, sin LLM decidiendo el flujo
- seals_core/ejecutor.py -> router 90/10 real (if/elif)
- seals_core/instalador_deterministico.py -> git clone + pip install, 0% LLM
- seals_core/consultor_experto.py -> 5-10% LLM via Cerebras, rota 6 keys por variable de entorno
- seals_core/verificador.py -> CODIGO REAL (no placeholder), llama claude_agent_sdk, model claude-sonnet-5, bajo volumen
- watchdog.py -> CODIGO REAL (no placeholder), lee inventario via GitHub API con GITHUB_TOKEN
- Seals team 1 YAIWES/task_contract.json -> lista, sin nodo reclamado
- _fuentes_extraidas/ -> mecanismos extraidos de Muse-Agent y MUSE-KnowledgeXLab (evidencia real, sha256+commit)

## Variables de entorno requeridas (GitHub Secrets, NUNCA en codigo)
- CEREBRAS_API_KEY_1 a CEREBRAS_API_KEY_6
- ANTHROPIC_API_KEY (para verificador.py)
- GITHUB_TOKEN (para watchdog.py, lectura del inventario)

## Que va a trabajar el modelo (primera prueba, en orden)
1. Director agrega las 4 variables de entorno arriba en GitHub Secrets.
2. Se asigna 1 nodo real PENDING_STEP1 del inventario (229 componentes)
   al task_contract.json de "Seals team 1 YAIWES".
3. Se corre seals_core/ejecutor.py -> loop_principal() con ese nodo como
   cola inicial.
4. Se verifica evidencia real: archivo evidencia_local.jsonl generado +
   componente movido/instalado + entrada en Crazy Wall.
5. Solo si el paso 4 cierra con evidencia real, se clona a "Seals team 2
   YAIWES" y "Seals team 3 YAIWES" (mismo codigo, distinto contrato).

## Pendiente, fuera de este agente (no bloquea la prueba)
- Meta-Muse-Code-SDK-2026 y Meta-Agent-Cookbook-2026: Sol los descargo
  completos sin que se le pidiera. Pausados, sin usar, sin aprobar.
- pyproject.toml / requirements.txt del agente: aun no creado. Dependencias
  usadas: requests, claude-agent-sdk. Crear antes de correr en un entorno
  limpio.

## Como retomar si se pierde el contexto
Leer, en este orden: Claude notas/memoria.md (fuente unica autoritativa)
-> este Handoff -> Seals team.md -> dag_schema.yaml.
