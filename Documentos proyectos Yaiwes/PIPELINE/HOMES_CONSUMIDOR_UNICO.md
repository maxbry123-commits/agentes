# HOMES — consumidor único (dual paths, no merge)

Append-only: no se unifican paquetes en este corte. Se nombra el consumidor canónico.

| Concepto | Home canónico (usar) | Home secundario (no orquestar desde aquí) |
|----------|----------------------|-------------------------------------------|
| Reception inbox | `extensions/wordflow/reception/` | — |
| Reception API | `extensions/wordflow_kernel/reception/` | wordflow convert es impl |
| Programming PASS | `extensions/wordflow/standards/forensic_core.py` | `extensions/audit_forensic/` |
| Repo truth V1 | `extensions/wordflow_kernel/repo_truth.py` | audit_forensic/engine/repo_truth.py |
| Goal lock | `extensions/wordflow/engine/goal_lock.py` | — |
| Goal bridge loop | `extensions/maxbry_loop/goal_bridge.py` | `wordflow_kernel/bridge/goal_bridge.py` |
| Stage hooks loop | `extensions/maxbry_loop/stage_hooks.py` | `wordflow_kernel/stages/` |
| Publish deploy | `extensions/github_deploy/` | `extensions/github_publisher/` y `wordflow/engine/github_publisher.py` |
| Knowledge index instancia | `extensions/wordflow_kernel/knowledge_index.py` | `extensions/knowledge/` |
| Acquire | `extensions/source_evolution/` | path viejo control-layer/... no existe |
| Kimi/Minimax | `extensions/wordflow_kernel/slots/kimi_minimax.ficha.v2.json` | loops/fusion yaml no existe |

Regla: un caller nuevo importa el home canónico. El secundario no se borra.
