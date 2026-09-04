# XRAY_MATRIX_POST — T43

**Fecha:** 2026-08-19  
**Ref:** HEAD al publicar este archivo. STATUS por existencia + cableado auditado. No C100.

| ID | Path | STATUS | Nota |
|----|------|--------|------|
| WF.core | extensions/wordflow | IMPLEMENTED | paquete |
| WF.kernel | extensions/wordflow_kernel | PARTIAL | engines stub |
| WF.reception_link | extensions/wordflow_kernel/reception | IMPLEMENTED | ingest fail-closed plugin |
| WF.loop | extensions/maxbry_loop | PARTIAL | code_path WIRED_NO_PASS |
| WF.C19 | engine/code_path_runner.py | IMPLEMENTED | BLOCK sin context |
| WF.audit_to_plan | workflow.py | IMPLEMENTED | auto_inject default |
| WF.gateway | kernel/gateway | STUB | no vendor |
| WF.engines | openclaw/hermes | STUB | |
| WF.fusion | slots/kimi_minimax | PLACEHOLDER | |
| WF.ci | .github/workflows/test-wordflow-code-path.yml | IMPLEMENTED | archivo |
| T41 HTML | docs/mapa_mental_v1.html | IMPLEMENTED | archivo |
| T42 HTML | docs/xray_ids_v1.html | IMPLEMENTED | archivo |
| T49 claim | — | MISSING | bloqueado mientras forense FAIL |

No IMPLEMENTED de runtime vendor ni git apply desde ingest.
