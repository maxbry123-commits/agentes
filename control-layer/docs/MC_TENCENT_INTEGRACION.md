# MC · Integración Tencent determinista

## Source

- URL: https://github.com/TencentCloud/TencentDB-Agent-Memory.git
- Tag: **v2.0.0**
- SHA: **0aff21a2d9f2b8a0354aaa80a2e586aab4054562**
- Script: `memory/providers/tencent/download_deterministic.sh`

```bash
bash control-layer/memory/providers/tencent/download_deterministic.sh
# -> sources/tencent/TencentDB-Agent-Memory @ v2.0.0
```

**Nunca modificar** archivos dentro de `sources/tencent/`.

## Arquitectura

```
Wordflow Memory Control Plane
  MemoryContext + Namespace + Router
       |
       +-- LocalProvider (nativo: doc_registry + session)  [siempre]
       |
       +-- TencentAdapter (HTTP)  [opcional si servicio up]
              |
              v
        TencentDB-Agent-Memory (engine externo)
```

## Uso

```python
from memory.api import build_memory_stack, default_context
rt = build_memory_stack(state_dir="./state", enable_tencent=False)
ctx = default_context(project_id="JARVIS", agent_id="backend")
rt.capture(ctx, "hecho...", type="fact")
rt.recall(ctx, "query", top_n=10)
```

## Estado

- MC01 contratos: HECHO
- MC02 LocalProvider: HECHO
- MC03 Tencent adapter + manifest: HECHO
- MC04 MemoryGuard aislamiento duro: pendiente
- Osquestador kernel memoria: espera docs usuario
