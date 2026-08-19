# FORENSE PASADA 01 — STRUCTURE

**Repo:** maxbry123-commits/agentes  
**Ref:** main post KernelExtMotor→reception  
**Método:** mismas 4 pasadas que `standards/forensic_core.py`  
**C100 = NO.** Claim ≠ evidence.

Esta pasada solo pregunta: ¿el archivo existe y tiene la responsabilidad que el doc le asigna?

---

## 1. Qué es STRUCTURE aquí

En `forensic_core`, STRUCTURE exige CORE-01..06 y CORE-13.  
A escala repo: cada plano tiene un home en git, no solo un párrafo en PIPELINE.

```
DOCUMENT → CONTEXT → REQUIREMENT → CODE → TEST → EVIDENCE → VERDICT
```

---

## 2. Planos (homes reales)

| Plano | Home GitHub | ¿Presente? |
|-------|-------------|-------------|
| Producto Wordflow | `extensions/wordflow/` | SÍ |
| Kernel extension | `extensions/wordflow_kernel/` | SÍ |
| Loop continuo | `extensions/maxbry_loop/` | SÍ |
| Deploy | `extensions/github_deploy/` | SÍ |
| Publisher 2º | `extensions/github_publisher/` | SÍ (duplicado) |
| Forense 2º | `extensions/audit_forensic/` | SÍ (duplicado) |
| Knowledge 2º | `extensions/knowledge/` | SÍ (duplicado) |
| Acquire/evolución | `extensions/source_evolution/` | SÍ |
| Bootstrap KTP | `extensions/project_bootstrap/` | SÍ |
| Contratos adapter | `extensions/adapters/` | SÍ |
| Inbox reception | `extensions/wordflow/reception/` | SÍ |
| LINK reception kernel | `extensions/wordflow_kernel/reception/` | SÍ |
| Hot path C-19 | `extensions/wordflow/engine/code_path_runner.py` | SÍ (17742 B) |
| Enforcer | `extensions/wordflow/standards/forensic_core.py` | SÍ |
| Policy docs | `PIPELINE/` | SÍ (muchos; no es code) |

---

## 3. Kernel — inventario de responsabilidad

| Módulo | Responsabilidad declarada | Archivo existe |
|--------|---------------------------|----------------|
| `ficha.v2.json` | enchufe kernel, `llm_control: DENY` | SÍ |
| `ficha_loader.py` | load/validate ABI | SÍ |
| `bootstrap_multi.py` / `spawn.py` | instancia | SÍ |
| `bootstrap_fake.py` | E2E Fake | SÍ |
| `fail_closed.py` | cierre si ficha mala | SÍ |
| `preflight.py` | checks | SÍ |
| `context_pack.py` | pack por instancia | SÍ |
| `knowledge_index.py` | índice sin embeddings | SÍ |
| `memory.py` + `memory_slot/` | memoria local | SÍ |
| `engine_registry.py` + `engines/*_stub` | attach engines | SÍ |
| `handle_message.py` | ping/echo/status/ingest | SÍ |
| `llm_control.py` | ban vendor | SÍ |
| `gateway/intelligence.py` | único path LLM | SÍ |
| `repo_truth.py` | FakeRepoTruth | SÍ |
| `workflow.py` | WordflowKernel | SÍ (skeleton) |
| `reception/convert.py` | LINK a inbox | SÍ |
| `slots/kimi_minimax.ficha.v2.json` | PLACEHOLDER | SÍ |

## 4. Wordflow producto — bloques

| Bloque | Path | Existe |
|--------|------|--------|
| Engine | `engine/` ~90 py | SÍ |
| Standards / control | `standards/` | SÍ |
| Reception inbox | `reception/` | SÍ |
| Motors | `motors/{send,call,download,kernel_ext}` | SÍ |
| Accounts | `accounts/` | SÍ |
| Codegen | `codegen/dag.py` | SÍ |
| Schemas | `schemas/` | SÍ |
| Tests | `tests/` (volumen alto) | SÍ |
| Catalogs | `component_catalog.json`, `connect_catalog.json` | SÍ |

## 5. Hallazgos STRUCTURE (no son CONNECTIVITY)

1. **Dos hogares** en forense, knowledge, publisher, goal_bridge, stage hooks. Estructura válida como archivos; no es un solo plano.
2. `component_catalog.json` marca `wordflow_kernel` y `maxbry_loop` como `pending_mount` aunque los directorios ya existen. **DOC_CODE_MISMATCH**.
3. `acquire_engine` apunta a `control-layer/subsheriffs/acquire_os` — path **no** está en el tree de `extensions/` auditado.
4. `loop.fusion_minimax_kimi` apunta a `wordflow_kernel/loops/fusion_minimax_kimi.yaml` — **no** aparece en el tree del kernel (sí hay `slots/` PLACEHOLDER).
5. PIPELINE tiene decenas de arquitectura/status. Eso no sustituye homes de code.

## 6. Veredicto pasada 1

| Criterio | Resultado |
|----------|-----------|
| Homes de los 4 planos runtime (kernel/wordflow/loop/deploy) | PASS |
| Reception inbox + LINK kernel | PASS |
| C-19 + forensic_core presentes | PASS |
| Catálogos alineados con tree | FAIL (pending_mount / paths fantasma) |
| Un solo home por concepto | FAIL (duplicados) |

**STRUCTURE repo = FAIL** (archivos hay; inventario declarativo miente).  
Siguiente pasada: quién importa a quién.
