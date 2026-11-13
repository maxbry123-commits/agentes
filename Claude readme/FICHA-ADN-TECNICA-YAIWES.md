# FICHA ADN TÉCNICA — AGENTE YAIWES
**Documento vivo. Marca: ✅ operativo con evidencia · 🆘🚩 pendiente**
**Última actualización: 2026-09-14, Claude (orquestador)**

---

## 0. Qué es YAIWES (identidad, en una frase)

Un equipo persistente que investiga, propone en paralelo, se refuta a sí mismo, mide con evidencia externa, y no se rinde ante un fallo — con reglas: 90% código determinista decide, 10% LLM solo razona dentro de una cápsula acotada.

---

## 1. Los 6 planos de la arquitectura (dónde vive todo)

```
CAPA 5 — INTERFAZ           🆘🚩 UI dual (repo frontend, en construcción)
CAPA 4 — ORQUESTACIÓN       ✅ Crazy Wall (35 nodos, 34 cerrados) + 🆘🚩 DSL/DAG Engine (sin código)
CAPA 3 — COORDINACIÓN       ✅ Enchufe Universal (real) · 🆘🚩 Cognitive Control Plane (en construcción hoy)
CAPA 2 — COGNICIÓN          🆘🚩 Reasoning Kernel R24 (especificado, sin código) · ✅ dataset Mythos/YAIWES/Meta (en construcción)
CAPA 1 — PERSISTENCIA       ✅ ledger/checkpoint (legacy, 27 tests) · 🆘🚩 Goal Lock (sin código)
CAPA 0 — INFRAESTRUCTURA    🆘🚩 Ray/sandbox (recomendado, sin montar)
```

---

## 2. Núcleo determinista (Grupo A — mecanismo, nunca cambia de forma)

| Primitiva | Estado |
|---|---|
| Event Loop (`DeterministicLoopEngine`) | ✅ código real, 🆘🚩 sin tests, sin conectar al entrypoint |
| Scheduler | ✅ código real, 🆘🚩 sin tests |
| Registry (Engine/Extension) | ✅ código real |
| Router | 🆘🚩 import roto (`adapter.py` referencia modelo externo no resuelto) |
| Policy Engine (Sheriff) | ✅ código real, fail-closed confirmado, 🆘🚩 sigue siendo reglas de texto, falta máquina de estados (`transitions`) |
| State Manager (StateStore+StateAuthority) | ✅ código real |
| DSL/DAG Engine | 🆘🚩 no existe como código — decisión: parser propio con PyYAML+jsonschema |
| Mission/Goal Lock | 🆘🚩 no existe — decisión: extender StateAuthority ya existente |
| Ledger/Checkpoint/Evidencia | ✅ completo en `extensions/wordflow_kernel` (27 tests), 🆘🚩 no expuesto desde `kernel-principal` |

---

## 3. Capa de razonamiento (Grupo B — contenido que el núcleo invoca, nunca es el núcleo)

| Contenido | Estado |
|---|---|
| Mythos 40 pasos / EURS / DRE | ✅ especificado a detalle (Fables) · 🆘🚩 sin código propio, ~12k LOC estimadas pendientes |
| Reasoning Kernel R24 (24 etapas nombradas) | ✅ especificado a detalle · 🆘🚩 sin código |
| Banco de módulos tipo Self-Discover | ✅ probado end-to-end (`expert_panel_router.py` + `decision_on_demand.py`, 1 módulo real) |
| Catálogo de 105 algoritmos deterministas | ✅ catalogado con librería real por cada uno · 🆘🚩 solo 1 registrado con ficha |
| Selector/Rotador = Cognitive Lottery Router | ✅ especificado (multi-armed bandit) · 🆘🚩 sin código |
| Director (señal de rotar) | ✅ decisión tomada: fusionar con Consistency Engine (evita 6to módulo) |
| Patrones de videojuego (Behavior Trees, GOAP, AI Director) | ✅ investigados, con librería real cada uno · 🆘🚩 ninguno integrado aún |
| Kaizen/PDCA/refutación formal (Dung Framework) | ✅ mapeado, sin código |

---

## 4. Cognitive Control Plane (en construcción activa por Sol GPT hoy)

```
Source of Truth → Context Composer → Consistency Engine → Agent Router → Policy Guard
```
🆘🚩 En construcción — repo `router-universal-router-inteligente-`, dataset compacto (~1.100 registros, 30-35 archivos, Tier A/B/C).
⚠️ Decisión pendiente registrada: Context Composer y el "Input Shark" (repo `osquestador-auditor`) van en **pipeline secuencial** (Input Shark investiga → Context Composer ensambla), no fusionados.

---

## 5. Gobernanza (Sheriff/Sentinel/Validador — 20 componentes identificados)

✅ 36 invariantes del Enchufe Universal, código real y probable-mente ejecutable.
🆘🚩 10 componentes adicionales identificados (Rebuff, LLM Guard, Semgrep, Schemathesis, OPA Gatekeeper, Great Expectations, Detoxify, Constitutional AI pattern, OpenTelemetry+alertas, Anti-Corruption+contract testing) — ninguno instalado todavía.

---

## 6. Explícitamente FUERA del núcleo (para no volver a mezclar)

Wordflow de negocio, Tools/capabilities de ejecución, investigación web, UI, pool de agentes externos (Codex/Aider/Cline vía Fleet Manager). Usan al kernel — no son el kernel.

---

## 7. Auditoría en vivo (Crazy Wall, `agentes`, 2026-09-13/14)

✅ 34/35 nodos PASS/VERIFIED_CLOSED
🆘🚩 1 GAP activo — Nodo 33 (BullMQ), escalado, ver `Claude readme/Escalacion GAP N33 BullMQ.md`
✅ `Core kernel Yaiwes/` confirmado como staging de librerías vendorizadas (con procedencia real: SOURCE_URL/COMMIT/SHA256), no código propio — no bloquea el cierre.
