# 🧠 100 Mejoras de Memoria Extendida

> Documento canónico: prompt M3 DSL DAG SHERIFF V7, sección C.
> Owner: M3. Status: SPEC (sin deploy). Aplica a `08-memory` registry.

## Mecanismo de scoring

```
score = recency * 0.3 + importance * 0.4 + reusability * 0.3
```

- **recency**: 1.0 si <7d, 0.5 si 7-30d, 0.2 si >30d (decae exponencial).
- **importance**: assigned por el Sheriff (sheriff.py) cuando un success/failure ocurre:
  - 0.9-1.0: cambio de arquitectura, bug crítico, ahorro >$100.
  - 0.6-0.8: bug normal, decisión de diseño, cambio de tool.
  - 0.3-0.5: preferencia de UX, micro-fix.
- **reusability**: cuántas veces la memory fue consultada y resultó útil. Subida cada vez que el sheriff la matchea con un task. Saturación 1.0.

## Política de retención

- **Permanente** (score ≥ 0.7): nunca se purga.
- **1 año** (score 0.4-0.7): purga tras 365d sin uso.
- **90 días** (score 0.1-0.4): purga tras 90d.
- **Inmediato** (score < 0.1): purga en próximo GC.

GC corre semanal (domingo 03:00 UTC).

## Recovery

Si una memory con score ≥ 0.7 se referencia y NO está en el store, el sheriff la pide al `ai-registry/cards` cache antes de calcular.

## Las 100 mejoras (seed)

### 1-20 · Agent preferences (Max)
1. Max quiere respuestas de máx 6 líneas por default.
2. Max prefiere español en chat; inglés en código.
3. Max NO quiere que toques el VPS sin orden explícita.
4. Max trabaja con TZ America/New_York.
5. Max usa `<deliver-assets>` para archivos locales.
6. Max espera bucle infinito sin pedir permiso.
7. Max aprueba con "dale", "ok", "aprobado" — no requiere confirmación adicional.
8. Max lee BLOCKLOG después de merges importantes.
9. Max prefiere commits con prefijo `feat(M3):` o `fix(M3):`.
10. Max NO quiere que el sistema use <think> visible en respuestas finales.
11. Max aprueba reintentos automáticos (no le avises cada uno).
12. Max aprueba instalación en HF Space, NO en VPS.
13. Max prefiere squash-merge en PRs.
14. Max NO quiere que OpenClaw pida instalación de paquetes pesados.
15. Max espera TODOs persistentes en `~/.openclaw/state/todos.json`.
16. Max usa `ghp_*` tokens rotados regularmente.
17. Max quiere summary en BITACORA-MAXBRY al cerrar tareas grandes.
18. Max NO quiere que generes archivos >2MB sin avisar.
19. Max aprueba usar web-search cuando el knowledge registry no alcanza.
20. Max quiere fail-fast (no retry infinito) en tareas bloqueantes.

### 21-40 · Tool / skill patterns
21. Daytona > E2B para code tasks con workspace persistente.
22. E2B > Daytona para skills aisladas <30min.
23. HF Space > Cloudflare para GPU.
24. Cloudflare > HF para edge HTTP <1s.
25. Sandbox default = Sandbank (rutea a los otros).
26. `web-search` → Serper si `SERPER_API_KEY`; sino DDG stub.
27. `url-reader` → trafilatura en v0.2; hoy strip simple.
28. `terminal` blacklist: rm -rf /, mkfs, dd, fork bomb, curl|bash, shutdown.
29. `git` siempre scopea `--force` con policy.
30. `task-manager` state en `~/.openclaw/state/todos.json`.
31. `test-runner` default timeout 120s.
32. Agentes en español usan menos tokens si Max hace la pregunta en español.
33. OpenClaw gateway tiene 11 agentes; usar `model: "openclaw/m3"` para tareas generales.
34. Claude Code > Mimo Code para tareas de código críticas.
35. LiteLLM como fallback cuando un agente directo está caído.
36. Memory entries se consultan con `agent_id` + `task_type` antes de buscar en registries.
37. `agentregistry-dev` = upstream primario para catálogos.
38. `agent-skills-hub` (790+ skills) = upstream secundario.
39. `hol.org/registry` = 72k+ agents, federated.
40. `openagentskill.com` = decision+install layer.

### 41-60 · Failure patterns
41. SI un test pytest no está instalado → error claro "no module named", NO fake_pass.
42. SI una skill `validate.py` falla → NO la subas a HF Space.
43. SI `GITHUB_PAT_MAXBRY` devuelve 401 → rotar antes de seguir.
44. SI Daytona p95 > 5s → switch a E2B automáticamente.
45. SI E2B excede 24h → kill + reintentar.
46. SI un workflow tiene ciclo → abort, NO ejecutar.
47. SI una policy NO está en el registry → default deny.
48. SI un agent_id NO está en `01-agent` → 404, no inventar.
49. SI una URL de MCP devuelve 404 → marcar como unhealthy + warning.
50. SI el budget diario se excede → bloquear nuevas tasks costosas.
51. SI un PR tiene >20 archivos → dividir en sub-PRs.
52. SI una memoria se borra y tenía score ≥ 0.7 → log warning en `audit.log`.
53. SI un agent repite el mismo error 3 veces → escalar a M3-research.
54. SI un hook crashea con `failure_mode: deny` → bloquear la action.
55. SI OpenClaw está en bucle infinito → kill after 5min con log.
56. SI un sync engine externo devuelve 5xx → reintentar 3 veces, luego skip.
57. SI un MCP `list_tools` devuelve vacío → marcar unhealthy, no remover.
58. SI un test es flaky >10% → reescribir o marcar como warning.
59. SI una query al AI Registry demora >2s → usar caché local.
60. SI un PR toca `core/sheriff.py` → requerir 2 reviewers.

### 61-80 · Cost & budget
61. Default `max_duration_s` por skill: 30s.
62. `web-search` cap N=10 (no más).
63. `url-reader` cap max_chars=50k.
64. `test-runner` cap max_duration_s=120s.
65. Agentes cheap primero (cerebras/groq), heavy solo si necesario.
66. Claude 3.7 Sonnet reservado para code-tasks críticas.
67. `MiniMax-M3` default para chat general.
68. Batch small tasks en 1 request al gateway.
69. Cachear resultados de `web-search` por 1h.
70. Cachear `url-reader` por 24h.
71. Evitar `git push --force` (cuenta doble contra API limit).
72. LiteLLM: max 100 req/min por API key.
73. OpenClaw: max 1 chat simultáneo por sesión.
74. No crear HF Space sin antes confirmar con el orquestador.
75. Cloudflare Pages: deploys max 5/día.
76. `hol.org` publish: solo en release (no en PR).
77. Railway free tier: max 2 servicios activos.
78. VPS CPU: alerta si >80% por 10min.
79. VPS RAM: alerta si >85% por 5min.
80. VPS disk: alerta si >90%.

### 81-100 · UX & workflow
81. Skills prioritarias siempre disponibles (sin install manual).
82. Hooks con `failure_mode: deny` por default (safety first).
83. `/new` borra scratchpad pero NO memory persistente.
84. `/reset` borra TODO incluido memory de la sesión.
85. `before-agent-reply` trunca a 6 líneas para Max.
86. AI Registry: top-3 candidatos, no top-10 (ruido).
87. Cards refresh cada 5min para `agent_card`, 1min para `mcp_card`.
88. Recommender: si score <0.5, NO ejecutar (pedir clarificación).
89. Cada task debe tener un `owner` declarado.
90. Cada TODO bloqueado >7d → escalar al director (Max).
91. Logger JSON estructurado en todos los servicios.
92. Métricas: latencia p50/p95/p99 por servicio.
93. Métricas: success_rate por skill.
94. Métricas: cost_per_task por agent.
95. Audit log: quién-qué-cuándo inmutable.
96. Timeouts: timeout_s siempre declarado, nunca "infinito".
97. Errores legibles: human-readable, no solo stack trace.
98. Doc por skill: SKILL.md con descripción + 1 ejemplo mínimo.
99. Doc por registry: README.md con schema + catálogo seed.
100. Doc por workflow: DAG visual + test de acceptance.

## Tareas pendientes
- [ ] Implementar `score(recency, importance, reusability)` en `08-memory/score.py`.
- [ ] Implementar GC con la política de retención.
- [ ] Cargar las 100 entradas como seed inicial (pueden ser auto-derivadas de los registries).
- [ ] Backfill desde `core/memory/` si existe data histórica.
