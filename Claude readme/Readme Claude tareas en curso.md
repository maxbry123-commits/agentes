# HANDOFF — CONEXIÓN ENTRE PROYECTOS (por repo)
**Última actualización: 2026-09-13 20:23 hora de Colombia**
**Este archivo responde: si pierdo el contexto, ¿dónde está todo?**

---

## Repo 1/3 activo: `agentes` (Agente Yaiwes)
- **URL:** https://github.com/maxbry123-commits/agentes
- **Rama:** main
- **Rol:** el núcleo del agente Yaiwes — kernel, razonamiento, workflow loop de código.
- **Archivos clave ya localizados:**
  - `AGENTS.md` (raíz) — reglas de gobierno (COPY-FIRST, VerdictAuthority, skill wordflow-code-deploy-router)
  - `Bitácora stated JSON Craxy wall.json` (raíz, 56KB) — Crazy Wall operativo de este proyecto — **pendiente de lectura completa en Paso 1**
  - `Core kernel Yaiwes/` — advertencia: mayormente repos open source vendorizados (APScheduler, smolagents, Hamilton, redun, DBOS, Hatchet, Redis, Postgres, taskiq, Cline, OpenHands, rustfs), no código propio del kernel
  - `➡️📂 Wordflow LOOP Yaiwes/` — código propio real: `wordflow_loop/governance/` (sheriff, sentinel, validator, verifier, judge, supervisor, guardian), `wordflow_loop/agent_fleet/` (memoria por agente externo: aider, claude_code, cline, codex, goose, hermes, kimi_k, mimo_code, openclaw, opencode, openhands, qwen_code, smolagents...), `ledger.py`, `llm_gate.py`, `model_api_router_mvp.py`, `contracts.py`, `contracts/` (ficha.agent_fleet.v2.json, workflow.dsl.yaml, workflow.schema.json), `evidence/` (G001-G013, CG01, FINAL_3STEP_CLOSURE_TEST), `prompts/` (DIRECTOR-CODE-GRAPH-METHODS.md, SYSTEM_PROMPT.md), `research/` (community_sources.json, reuse_catalog_g005.json), `skills/SKILL-WORDFLOW-LOOP.md`, `workflows/wordflow-agent-fleet-step3.yml`
  - `Claude readme/` (esta misma carpeta) — memoria persistente de Claude como orquestador
- **Estado auditoría:** EN CURSO — Paso 1 (auditoría forense) es la próxima acción.

## Repo 2/3 activo: `frontend` (Fábrica de UI)
- **URL:** https://github.com/maxbry123-commits/frontend
- **Rama:** main
- **Rol:** fábrica de interfaces web del proyecto; independiente porque Grok/GPT no lograron construir la UI según instrucciones.
- **Archivos clave ya localizados (vía el prompt de ejemplo del Director, no auditados directamente todavía):**
  - `UI YAIWES/bitácora stated JSON Craxy wall plan checkpoint/CRAZY-WALL-TASK-NODES-DYNAMIC-V5-2026-09-12.json` — Crazy Wall operativo propio, con nodos N03 a N33
  - `UI YAIWES/readme arquitectura UI YAIWES/HANDOFF-DYNAMIC-NODES-UI-YAIWES-V8-2026-09-12.md` — Handoff propio
  - `UI YAIWES/readme arquitectura UI YAIWES/ARQUITECTURA-WORDFLOW-PYTHON-DSL-DAG-96-4-V7-2026-09-12.md` — arquitectura
  - Nodos mencionados como prioritarios por el Director: N03 (evidence/auditor), N21 (worker adapter), N32 (guest installer), N33 (mirror transport); GAPs abiertos: N14, N16, N18, N22, N24, N26, N28
- **Estado auditoría:** NO INICIADA POR CLAUDE TODAVÍA — pendiente, viene después de cerrar Paso 1-4 en `agentes`.

## Repo 3/3 activo: `router-universal-router-inteligente-` (Router Inteligente Universal)
- **URL:** https://github.com/maxbry123-commits/router-universal-router-inteligente-
- **Rama:** main
- **Descripción oficial del repo:** "Router universal para agentes NCT — nodos + conectores + sandbox + cost tracking"
- **Rol:** controla flujo, conexiones API, clientes procesador, mini-orquestadores de IA locales, plugins.
- **Dato relacionado:** el repo `TAREA-1` (en pausa por ahora) contiene la arquitectura de Hugging Face (LLM locales, cómputo, almacenamiento) que se revisará cuando se llegue a este paso.
- **Estado auditoría:** NO INICIADA — es el Paso 5 del plan de 9 pasos.

---

## Regla de no confusión entre proyectos
Cada uno de los 3 repos activos tiene (o tendrá) su PROPIO Crazy Wall/bitácora/Handoff — nunca se fusionan. Este documento (`Claude readme/`) es la memoria de Claude como orquestador *sobre* los 3, no reemplaza ninguno de los 3 documentos operativos propios de cada proyecto.
