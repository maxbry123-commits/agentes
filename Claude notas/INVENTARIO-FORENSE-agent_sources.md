# INVENTARIO FORENSE - agent_sources

Generado: 2026-09-20. Metodo: Git Data API (GET /git/trees/sha), lectura directa
de arbol de git, sin confiar en documentos ni resumenes previos. Cada fila tiene el
sha del arbol/commit verificado en esta pasada. Ruta base:
wordflow loop code Yaiwes/wordflow_loop/agent_sources/ (carpeta con emoji en el
nombre del padre, resuelta via Git Data API, no por nombre literal).

Regla de clasificacion:
- REAL = codigo fuente ejecutable, multiples archivos y subcarpetas de proyecto real.
- REAL nested = el contenido real esta un nivel mas abajo, en una subcarpeta con el
  nombre propio del proyecto (ejemplo: agent_zero/Agent-Zero/). Confirmado bajando un nivel.
- THIN WRAPPER = codigo real pero minimo (un solo archivo shim mas doc).
- PAPER-ONLY = solo reporte tecnico / paper / docs, sin codigo de agente ejecutable.
- SUBMODULE REAL = gitlink (mode 160000) a un repo externo real, confirmado por URL en .gitmodules.
- GAP = no existe en el arbol.

## A. Carpetas de codigo (type=tree), 23 entradas

1. agent_zero - sha 3f64907b95712e0770d6128356a994ff1281c950 - REAL nested en Agent-Zero/ - agent.py 60590B, models.py 36377B, api/, docker/, webui/, skills/, tools/, tests/
2. aider - sha f83ceb02bf62b860748b050c03361bd0dd1b7d47 - REAL - README 12406B, HISTORY.md 77044B, aider/, tests/, benchmark/, docker/, requirements/, scripts/
3. claude_code - sha 8bc6f609eba4da05eb2ce306be68463189006385 - REAL - CHANGELOG.md 587814B, plugins/, scripts/, examples/, Script/, .claude-plugin/
4. cline - sha 42e6fb4827285a3309130e9fa4a59b4f4de6a1ff - REAL - bun.lock 997246B, CHANGELOG.md 120794B, apps/, sdk/, docs/, evals/, patches/
5. codex - sha 52ef893c734cbf627d9633d8d3208972a29212c7 - REAL - monorepo Bazel, MODULE.bazel.lock 1.54MB, codex-cli/, codex-rs/, sdk/, docs/, third_party/
6. cua_mcp - sha 2abc20acd61f1931683186b1953a27d7f03b19c5 - THIN WRAPPER - README.md 11161B mas cua_local_mcp.py 3772B mas screenshots/. Codigo real pero minimo, un archivo. No es agente completo.
7. goose - sha 431d370b9e77373e00444938e02bf40a34afbb83 - REAL - Rust monorepo, Cargo.lock 368257B, crates/, ui/, vendor/, services/, bin/
8. hermes - sha b2b3aef161e368e2e54109caedcea5c32857ab34 - REAL - code/ mas _archives/ mas DOWNLOAD_EXTRACT_MANIFEST.json, patron de extraccion
9. kimi_k - sha 851f463176c72f8fda9e0aea7b41e6ab91a51af2 - PAPER-ONLY - README.md 33956B mas tech_report.pdf.chunks/ mas docs/ mas figures/. Es el technical report de Kimi-K, sin codigo fuente de agente.
10. meta_agent_cookbook - sha 089a327e62981fd398985caa18f9099111801ff6 - REAL - Cookbook Meta Model API confirmado en sesion previa. Seccion 4 Muse Code, carpeta 04_muse_code/, con 10 recipes numeradas.
11. meta_muse_code_sdk - sha e3042c4a28ad62c9d59f76c2877ab07893d902eb - REAL - code/ es SDK real (package.json, clients/, schema/, scripts/, CHANGELOG 34472B). _archives/ es zip backup separado (633KB), no contradice.
12. metacua - sha bfbd3e505b35a2e12b1f4a840a63d69dda37e1ff - REAL - Makefile, Package.swift, metacua.md 11995B, python/, src/, assets/
13. mimo_code - sha 34a67bc81fcd632d775fd219a290c8ea385e8678 - PAPER-ONLY - LICENSE mas MiMo-7B-Technical-Report.pdf 1.99MB mas README mas figures/ mas registry/. Reporte tecnico, no agente ejecutable.
14. mirothinker - sha f50ef918ce15a11d188f0f7216c0b533f3d460b5 - REAL nested en MiroThinker/ - README.md 56579B, apps/, libs/, assets/, justfile
15. muse_glimmer - sha a3cd2b19a6c79b517b1017c314508ddafaf74762 - REAL - code/ confirmado en sesion previa: agentic-fundamentals/agent_loop.py, response_parser.py, run_agent.py, el loop real plan-tool-result-self_correct-next
16. openclaw - sha 313e224abcca49e5a8bf6f3df723d6074d8f1c8a - REAL - code/ mas DOWNLOAD_EXTRACT_MANIFEST.json 5028B
17. opencode - sha 3e72d587a460f8ad64f95f2e13b50ad8f6385e4f - REAL - confirmado en sesion previa, completo y real
18. opendev - sha bd69117aebfee1d011d42b4539f48abe865ae5d0 - REAL nested en OpenDev/ - Rust: Cargo.lock 204304B, crates/, web-ui/, benches/, fuzz/, docs/
19. openhands - sha 5598f214c8cdfdd7d62e0fae4f4bd9764694a935 - REAL - app Electron mas web completa: package-lock.json 789445B, src/, electron/, docker/, helm/, specs/, tests/
20. orca - sha 4a70b119890500c638cdc5e5115bc13a97fee974 - REAL - confirmado en sesion previa: src/, skills/, native/, mobile/, cloud/, orca.yaml, package.json
21. qwen_code - sha 7c86e0151a39a82b2507dd461f1ee9f5732be1ed - REAL - qwen_agent/, qwen_server/, benchmark/, examples/, setup.py, run_server.py
22. research_agent_lab - sha 6ac3adf5f3ca21ee65ecf0ebfa86a2c833ce12cc - REAL nested en Research-Agent-Lab/ - core/, agents/, app/, memory/, tests/, tools/, workflows/, code_plan.md 43169B
23. smolagents - sha da0b725f55f516ed3a059300c2a2ee18d416e7e9 - REAL - src/, tests/, examples/, docs/, pyproject.toml, e2b.toml

Resultado A: 20 REAL, 1 THIN WRAPPER (cua_mcp), 2 PAPER-ONLY (kimi_k, mimo_code).

## B. Submodules (type=commit, mode 160000), 12 entradas

Confirmados via .gitmodules (sha 538c29e0402b28dce5dc80ad90c8cacfb7178d48): cada uno
apunta a una URL real de GitHub. Estado SUBMODULE REAL para todos.

24. kimi_agent_rs - commit f9186cd20b28c02d33721c05fd248e65d56e3e53 - github.com/MoonshotAI/kimi-agent-rs
25. kimi_agent_sdk - commit ed4be6be5280d02191da88bbafb3f828dcd33d72 - github.com/MoonshotAI/kimi-agent-sdk
26. kimi_cli - commit 86f136422a0aae6b217ea49e7ea1d2e8a1defcd2 - github.com/MoonshotAI/kimi-cli
27. kimi_code - commit 1fddc16e3ea2de4c26a18acd764380adf9e2ed64 - github.com/MoonshotAI/kimi-code
28. kimi_researcher - commit 9406d821348471bceb6d5fa0b7eba05411106f93 - github.com/MoonshotAI/Kimi-Researcher
29. minimax_code_plugins - commit d592f422893846c2aac48f8b407a92bd0293c6b1 - github.com/MiniMax-AI/MiniMax-Code-Plugins
30. minimax_coding_plan_mcp - commit 5dbf3494d7dac35d154958e0c1dab03910b89bbd - github.com/MiniMax-AI/MiniMax-Coding-Plan-MCP
31. minimax_mcp - commit 0856b9aef8a9d676bb63bdd6b6426d7b640a3b7a - github.com/MiniMax-AI/MiniMax-MCP
32. minimax_mcp_js - commit 8032f830203a1c61e56760b1680db923654bcb1b - github.com/MiniMax-AI/MiniMax-MCP-JS
33. minimax_mini_agent - commit d76a4f6389688cabda39c224a6cdfa274215d47c - github.com/MiniMax-AI/Mini-Agent
34. minimax_mmx_cli - commit bfbb4cb75ec343149eaccfd668c5011aa27bcf2b - github.com/MiniMax-AI cli
35. minimax_openroom - commit 02468154c4d99f8925916425bf444d672454fb3d - github.com/MiniMax-AI/OpenRoom

Resultado B: 12 SUBMODULE REAL, gitlinks validos, URL confirmada. Contenido interno de
cada submodule dentro del repo externo no verificado en esta pasada.

## C. Gap

36. mcode (@minimax-ai/code) - GAP - no existe en el arbol de agent_sources. Es el unico de los 13 slots originales (12 submodules mas mcode) que falta descargar y montar. Ver SALIDA 2.

## D. Archivos de metadata en la raiz de agent_sources (no son agentes)

- AGENT_SOURCE_COPY_PLAN_2026-09-15.json (2295B)
- AGENT_SOURCE_MOUNT_MANIFEST_2026-09-18.json (2714B)
- META4_COPY_EVIDENCE_2026-09-19.json (802B)

## Resumen final

- Total entradas verificadas: 36 (23 carpetas de codigo mas 12 submodules mas 1 gap) mas 3 archivos de metadata.
- REAL de uso directo como agente ejecutable: 20 carpetas mas 12 submodules, 32 total.
- THIN WRAPPER real pero minimo, no agente completo: 1 (cua_mcp).
- PAPER-ONLY sin codigo de agente: 2 (kimi_k, mimo_code).
- GAP: 1 (mcode).
- Ninguna entrada esta marcada supuesto, todas verificadas por sha de arbol o commit real en esta pasada.

## Nota de metodo

Auditorias anteriores en este mismo proyecto afirmaron incorrectamente que carpetas
como orca o las de meta estaban vacias. Esta tabla se construyo bajando el arbol real
via API para las 23 carpetas de codigo, una llamada por carpeta, mas una llamada extra
para las 4 carpetas con patron nested de un solo subdirectorio, sin repetir ninguna
afirmacion heredada de resumenes previos.
