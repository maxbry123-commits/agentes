# SALIDA W07 — AgentAdapter + CapabilityRouter + NodesLoader

**Estado: CERRADA 100%**

| Módulo | Path |
|--------|------|
| AgentAdapter / CallableAgent / AgentExecResult | `loops/agent_adapter.py` |
| CapabilityRouter | `loops/capability_router.py` |
| NodesLoader | `loops/nodes_loader.py` |

## Contrato
1. Loop pide **capability**, no agent_id
2. Router resuelve agente registrado con esa capability
3. NodesLoader lee `PROJECT/nodes/*.yaml` → register
4. Adapter ejecuta y devuelve `AgentExecResult{ok, output, error, tokens_used}`

## Nativo multiagente
- Un mismo engine sirve N agentes
- Nuevo agente = nuevo YAML + capabilities (sin tocar router)

## Siguiente
**W08** — runtime_factory (generic/stub sin exigir bin)
