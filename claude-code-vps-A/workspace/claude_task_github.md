# TAREA DE GITHUB PARA CLAUDE-CODE-VPS-A

Eres claude-code-vps-A (coder, gemma-4-31b via LiteLLM).
Trabajas en los 16 repos de NCT en /opt/nct/repos/*

## Tu responsabilidad
1. Auditar qué repos no tienen README.md, LICENSE, .gitignore
2. Crear los archivos faltantes (mínimos, 5-10 lineas)
3. Commit + push a una rama feat/mavis-doc-<repo>
4. NO modificar codigo existente, solo agregar docs basicas

## Reglas
- Una rama por repo
- Mensaje de commit: docs: <archivo> via Claude Code (gemma coder) [mavis-validate]
- Si un archivo ya existe, NO sobrescribir (skip)

## Repos a auditar
agentes frontend Command-Center Cerebro Fichas Auditoria Orquestador
Grupo-Trabajo-1 Grupo-Trabajo-2 Grupo-Trabajo-3 Maxbry-AGI
openclaw-install claude-code-config mimo-code-config nct-router nct-mcp-gateway

## Reporte al final
Imprime una tabla con: repo, archivos creados, rama, push status (OK/FAIL)
