# FORENSE PASADA 03 — BEHAVIOR

CORE-08..11: comportamiento, tests, regresión, error path.  
Pregunta: si llamo el entry, ¿hace lo que el inbox / HANDOFF / ficha promete?

---

## 1. Contratos de comportamiento vs runtime

| Contrato | Comportamiento medido |
|----------|------------------------|
| Inbox reception: leo → gaps → ubico ruta fase → PLUGIN | `convert` strip + keys. **No** escribe fase. **No** PLUGIN. |
| T2 convert(input_block) → normalized | SÍ (ok, text, branch, sdpa, max_context) |
| T21 handle_message ping/echo/status | SÍ |
| T21 + ingest | SÍ dispatch; no side-effect de colocación |
| KernelExtMotor reception_link | SÍ URL + ahora locate kernel |
| `run_code_path` sin context | BLOCK + `llm_control=DENY` |
| `run_code_path` measures vacíos | FAIL (default False) |
| OPEN→CLOSED en GapRegistry | ValueError |
| force_push | reject |
| path protegido | HOLD |
| PAT en body | token_ref only |
| Gateway vendor import | no; stub o ROUTER_URL |
| bootstrap_fake | ok Fake; **no** es C-19 PASS |
| WordflowKernel.audit_to_plan | RuntimeError sin inject |

## 2. E2E que existe vs E2E que se vende

### Fake E2E (T13/T14) — sí corre

```
bootstrap → goal_lock try → code_path_dry → deploy Fake
loop_bridge.bridge_run_fake: intake / code_path_dry / loop_fake / publish_fake
```

No exige context_verified. No evalúa CORE-01..14. No es evidencia de sistema cerrado.

### C-19 E2E — corre solo si el caller es honesto

`auto_measure_core` ayuda, pero PASS todavía pide:

- context + handoff
- 14 CORE True
- 4 passes
- counters 0
- evidence_complete
- final_clean_reaudit
- quality_dag_ok

Un caller que pone flags True sin medir miente. El enforcer **no** llama GitHub para CORE-13.

## 3. Tests (efectividad, no existencia)

Hay muchos `extensions/wordflow/tests/test_*.py` y `wordflow_kernel/tests/`.  
Eso cubre unidades. No cubre:

- reception → input_compiler → fase
- loop → run_code_path → publish real
- KernelExtMotor → kernel.reception (test nuevo **ausente** en este commit)
- mutation / impact AST (MASTER ya lo marcó NO)

CORE-09 TEST EFFECTIVENESS a nivel repo = no medido.

## 4. Error paths (sí existen)

| Input | Output observado en code |
|-------|--------------------------|
| msg no dict | INVALID_MSG |
| action chat | UNKNOWN_ACTION |
| reception impl missing | RECEPTION_IMPL_MISSING |
| ficha inválida | fail_closed |
| context False | BLOCK |
| force | reject |
| capability gateway desconocida | DENY |

Error path de colocación de reception: **no hay**, porque esa rama no existe.

## 5. Regresión / impacto

No hay motor único de impacto. `component_catalog` desactualizado es regresión documental: un agente puede creer que kernel está `pending_mount`.

## 6. Veredicto pasada 3

| CORE | Repo |
|------|------|
| 08 BEHAVIOR/EDGE | PARCIAL (entradas Fake/C-19 sí; inbox fase no) |
| 09 TEST EFFECTIVENESS | NO a escala sistema |
| 10 REGRESSION/IMPACT | NO motor |
| 11 ERROR PATH | PARCIAL (fail-closed en gates; no en reception-fase) |

**BEHAVIOR sistema = FAIL.**  
No se puede decir “todo está cableado”: el comportamiento de reception→fase y loop→C-19 no se ejecuta.
