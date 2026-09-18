Handoff seals team.md

## Estado real (corregido 2026-09-18, P2-31 - version anterior tenia drift)
CODIGO SUSTANCIALMENTE MEJORADO tras auditoria externa de 5 pasadas (32
gaps P0/P1/P2 encontrados). 27 de 32 gaps cerrados con CODE+TEST+EVIDENCE
en 8 salidas. Pendientes explicitos abajo. NO se declara VERIFIED_CLOSED
hasta que el veredicto final de esta misma salida lo confirme.

## Numeros reales (la version anterior decia 229 componentes y
## "requirements.txt aun no existe" - ambos eran drift, corregido aqui)
Inventario real: 248 componentes (verificado en vivo, campo real
wall_status, 213 en PENDING_STEP1 al momento de esta auditoria).
requirements.txt SI existe, con pyyaml agregado. requirements.lock.txt
pendiente (tarea real dada a Sol, ver PROMPT-Sol-requirements-lock.md).

## Archivos reales de seals_core/ (lista completa actualizada)
ejecutor.py, dag_engine.py, instalador_deterministico.py,
consultor_experto.py, verificador.py, evidence.py, goal_tracking.py,
crazy_wall_adapter.py, idempotencia.py, tool_result.py, sheriff_policy.py,
stuck_detector.py, research_real.py, work_surface.py, worker_bootstrap.py,
isolation.py, recovery_types.py, llm_output_schema.py, crash_resume.py,
router_modelos.py, tests/ (8 archivos de test).

## Variables de entorno requeridas (GitHub Secrets, nunca en codigo)
CEREBRAS_API_KEY_1 a 6 (SOLO PARA PRUEBAS - en produccion via Router
Inteligente Universal, ver Claude notas/REQUISITO-50-mundos-y-Router-
Universal.md), ANTHROPIC_API_KEY, GITHUB_TOKEN.

## Pendiente explicito, no oculto (no bloquea la primera prueba)
- P1-24 (MetaCua/CUA-MCP): no verificado, no integrado - la propia
  auditoria exige no declarar esto sin leer implementacion real primero.
- P1-30 parcial: faltan tests especificos de crash/recovery end-to-end
  y de wrong-source-commit con git real (los actuales usan mocks).
- Meta-Muse-Code-SDK-2026 y Meta-Agent-Cookbook-2026: descargados fuera
  de alcance por Sol, pausados sin usar.
- Requisito de 50+ mundos independientes: arquitectura base lista
  (task_contract.json por worker, worker_bootstrap.py valida identidad),
  pero el generador de Readme+Handoff+Crazy Wall+System prompt POR
  WORKER (para los 50+) todavia no esta escrito - es la ultima pieza
  antes de escalar de 1 a 50+ copias.

## Como retomar si se pierde el contexto
Leer, en este orden: Claude notas/memoria.md (fuente unica autoritativa)
-> este Handoff -> Seals team.md -> dag_schema.yaml.
