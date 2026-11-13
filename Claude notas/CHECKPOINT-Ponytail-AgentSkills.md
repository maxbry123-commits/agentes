HALLAZGO REAL - Orca stablyai/orca MIT - 2026-09-18

Orca es real: Electron multi-plataforma, AI Orchestrator. Corre Claude
Code/Codex/OpenCode/Grok cada uno en su propio git worktree aislado,
compara resultados, fusiona el ganador. CLI programable. SSH remoto.
Account switcher con usage tracking y hot-swap de cuentas sin re-login.

MECANISMO A EXTRAER (no la app Electron completa):
1. Worktree aislado por agente coincide con isolation.py ya construido
   (1 writer = 1 scope) - confirma que el diseno va bien.
2. Account/API key rotation + usage tracking + hot-swap aplica directo
   a router_modelos.py para las 50+ API keys.
3. CLI scriptable como contrato de automatizacion externa.

DECISION: no correr Orca GUI como parte del backend. Extraer mecanismos
como funciones Python dentro de isolation.py y router_modelos.py, patron
DSL/DAG acordado con Fables.

PENDIENTE: mismo analisis con omniroute.
