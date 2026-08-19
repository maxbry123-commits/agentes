# ARQUITECTURA 02 — WORDFLOW KERNEL (extensión)

**Path:** `extensions/wordflow_kernel/`  
**Ficha:** `extensions/wordflow_kernel/ficha.v2.json`  
**artifact_id:** `wordflow.kernel.extension`  
**abi_version:** `2.0`  
**llm_control:** `DENY` en paths deterministas.

---

## 1. Qué es

Plano de control. No es el producto Wordflow. No escribe el plan de programación.  
Hace: validar ficha, spawn instancia, fail-closed, preflight, pack de contexto, memoria local, ban LLM, gateway stub, verdad de repo Fake, gaps enqueue Fake.

## 2. Arranque (orden real de módulos)

```
ficha_loader.validate / load
        |
fail_closed  (ficha inválida → stop)
        |
spawn + bootstrap_multi / bootstrap_v1 / bootstrap_fake
        |
preflight
        |
context_pack (hash por instance_id)
        |
knowledge_index (sin embeddings; vacío OK)
        |
memory get/set
        |
handle_message  (ping|echo|status|convert|ingest|reception)
        |
        +-- reception.ingest → wordflow.reception.convert
```

| Archivo | Tarea | Contrato |
|---------|-------|----------|
| `ficha_loader.py` | T10 | load/validate/register abi |
| `bootstrap_multi.py` | T11 | load_into_memory multi-id |
| `spawn.py` | T11 | crea instancia |
| `fail_closed.py` | T12 | no sigue si ficha rota |
| `bootstrap_fake.py` | T13 | E2E Fake |
| `preflight.py` | T15 | checks mínimos |
| `context_pack.py` | T16 | pack + hash |
| `knowledge_index.py` | T17 | indexa md/json/yaml en instance/knowledge |
| `resources/registry.py` | T18 | register |
| `memory.py` | T19 | get/set |
| `engine_registry.py` | T20 | attach policy |
| `handle_message.py` | T21 | UI ping + reception |
| `llm_control.py` | T22 | scan_paths_for_llm_ban |
| `slots/` | T40 | kimi_minimax PLACEHOLDER fusion:false |

## 3. Gateway e engines (sin vendor)

```
maxbry_loop.model.generate
        → wordflow_kernel.gateway.intelligence.IntelligenceGateway.complete   [STUB]
        → opcional RouterHTTPGateway /v1/route

engine_registry.reason
        → engines/openclaw_stub.py | hermes_stub.py
        → SIEMPRE via IntelligenceGateway
```

Archivos:
- `gateway/intelligence.py` (4181 B)
- `gateway/router_http.py`
- `engines/port.py`
- `llm_control.py` — DENY si aparece cliente vendor en paths kernel.

## 4. Recursos HF

`resources/`:
- `contract.py` `factory.py` `registry.py`
- `skill_loader.py` `dataset_loader.py` `space_loader.py`
- `validate_resource.py` (T35)

Default: PLAN_ONLY. Fetch no habilitado.

Router pipeline T37: `router_slot/pipeline.py` (discover→map→select→load) stubs.

## 5. Forense kernel

| Archivo | Rol |
|---------|-----|
| `repo_truth.py` | FakeRepoTruth (T31) |
| `crosscheck.py` | cruza claims |
| `forensic.py` / `forensic_api.py` | API forense |
| `gap_tasks.py` | enqueue Fake (T29) |
| `bridge/gap_bridge.py` `bridge/goal_bridge.py` | puentes loop |

Claim ≠ evidence. Un archivo que diga DONE no cuenta.

## 6. Reception LINK (este commit)

```
handle_message(action=convert|ingest|reception)
        → wordflow_kernel.reception.convert.ingest
                → extensions.wordflow.reception.convert.convert
                → locate() paths canónicos
```

Si el import de Wordflow falla → `RECEPTION_IMPL_MISSING` (fail-closed).
No se copia la lógica de convert al kernel.

Inbox sigue aquí (usuario sube .md/.py):
`extensions/wordflow/reception/`

## 7. Stages kernel

`stages/engine.py` + `default_handlers.py` + `kernel_hook.py`  
Hooks por instancia. Loop concreto vive en `extensions/maxbry_loop/` (`stage_hooks.py` 1816 B).

## 8. UI plugin

`ui_gateway/plugin.py` + `ui_gateway/ficha.v2.json`  
No es un front. Es enchufe de plugin.

## 9. Entradas de la ficha

```
entry_points:
  workflow: wordflow_kernel.workflow:WordflowKernel
  forensic: wordflow_kernel.forensic:ForensicEngine
  gateway:  wordflow_kernel.gateway:build_gateway_from_env
provides:
  forensic.audit, repo_truth, gap_to_task, checkpoint, ledger, trace,
  resource_registry, intelligence_gateway, engine.openclaw, engine.hermes
```

`WordflowKernel.audit_to_plan` **exige** inject de audit_engine+compiler. Sin inject → RuntimeError. Eso es estado real, no 100%.

## 10. Tests kernel

`extensions/wordflow_kernel/tests/` — unittest offline (c100_01, vf01–vf03, vg, vh, vk, vl, vr).  
No demuestran vendor ni publish real.
