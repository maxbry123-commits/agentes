# HANDOFF — CONEXIÓN ENTRE PROYECTOS (por repo)
**Última actualización: 2026-09-14 hora de Colombia**
**Este archivo responde: si pierdo el contexto, ¿dónde está todo?**

---

## 📌 NUEVO — Plan de adquisición de componentes
Ver `Claude readme/PLAN-ADQUISICION-COMPONENTES.md` — Fase 1 (23 componentes
aprobados, listos para Sol GPT) + Fase 2 (22 en reserva, no descargar aún).
Extensión del Crazy Wall, no lo reemplaza.

---

## Repo 1/3 activo: `agentes` (Agente Yaiwes)
- **URL:** https://github.com/maxbry123-commits/agentes
- **Rama:** main
- **Rol:** el núcleo del agente Yaiwes — kernel, razonamiento, workflow loop de código.
- **Archivos clave ya localizados:**
  - `AGENTS.md` (raíz) — reglas de gobierno (COPY-FIRST, VerdictAuthority, skill wordflow-code-deploy-router)
  - `Bitácora stated JSON Craxy wall.json` (raíz, 90KB) — Crazy Wall operativo: 34/35 nodos cerrados, 1 GAP activo (N33 BullMQ, escalado)
  - `Core kernel Yaiwes/` — repos open source vendorizados con procedencia real (SOURCE_URL/COMMIT/SHA256), no código propio del kernel
  - `➡️📂 Wordflow LOOP Yaiwes/` — código propio real: governance/ (sheriff, sentinel, validator, verifier, judge, supervisor, guardian), agent_fleet/, ledger.py, llm_gate.py, model_api_router_mvp.py, contracts.py, HANDOFF.md
  - `Readme arquitectura Yaiwes/README.md` (74KB, sin tocar) + `FICHA-ADN-TECNICA-YAIWES.md` (nuevo) + Enchufe Universal (ya subido, 2 archivos .py + 1 .md)
  - `Claude readme/` — memoria persistente de Claude: Readme Claude.md, instrucciones, bitácora/mapa mental, este Handoff, Escalación GAP N33, Plan de adquisición de componentes
- **Estado auditoría:** 34/35 nodos PASS. Cognitive Control Plane en construcción activa (Sol GPT) en repo hermano.

## Repo 2/3 activo: `frontend` (Fábrica de UI)
- **URL:** https://github.com/maxbry123-commits/frontend
- **Rama:** main
- **Rol:** fábrica de interfaces web del proyecto.
- **Archivos clave (vía prompt de ejemplo del Director, no auditados directamente):**
  - `UI YAIWES/bitácora stated JSON Craxy wall plan checkpoint/CRAZY-WALL-TASK-NODES-DYNAMIC-V5-2026-09-12.json`
  - `UI YAIWES/readme arquitectura UI YAIWES/HANDOFF-DYNAMIC-NODES-UI-YAIWES-V8-2026-09-12.md`
  - `UI YAIWES/readme arquitectura UI YAIWES/ARQUITECTURA-WORDFLOW-PYTHON-DSL-DAG-96-4-V7-2026-09-12.md`
  - Nodos prioritarios: N03, N21, N32, N33; GAPs: N14, N16, N18, N22, N24, N26, N28
- **Estado auditoría:** NO iniciada por Claude todavía.

## Repo 3/3 activo: `router-universal-router-inteligente-` (Router Inteligente Universal)
- **URL:** https://github.com/maxbry123-commits/router-universal-router-inteligente-
- **Rama:** main
- **Rol:** flujo, conexiones API, mini-orquestadores locales, plugins.
- **En construcción activa hoy:** Cognitive Control Plane (Source of Truth → Context Composer →
  Consistency Engine → Agent Router → Policy Guard) + dataset compacto (~1.100 registros,
  30-35 archivos, Tier A/B/C).
- **Decisión registrada:** Context Composer e Input Shark (repo `osquestador-auditor`) van en
  pipeline secuencial, no fusionados.
- **Dato relacionado:** repo `TAREA-1` (en pausa) contiene arquitectura de Hugging Face.

---

## Regla de no confusión entre proyectos
Cada uno de los 3 repos activos tiene (o tendrá) su PROPIO Crazy Wall/bitácora/Handoff — nunca se fusionan. Este documento (`Claude readme/`) es la memoria de Claude como orquestador *sobre* los 3, no reemplaza ninguno de los 3 documentos operativos propios de cada proyecto.
