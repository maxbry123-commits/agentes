# Acomodado — Agent Identity + Project Identity

## Hecho
- schemas: project · agent · workflow · execution_context · memory_scope
- discovery/agent_discovery + bootstrap
- registry/agent_registry (por capabilities)
- sheriff/agent_validate + build_execution_context
- templates: B1 (agents_source) · B3_agent.yaml · B2 solo estado · RECETA universal

## Flujo
nodes/*.yaml → Discovery → validate_agent → Registry → Router(capabilities) → ExecutionContext → Adapter

## Separación
NODE=quién · DAG=qué flujo · LOOP=cómo repetir · MEMORY=scopes · SHERIFF=permitido

## Siguiente
Investigación + mejora 100× plantillas D1→D10 (una salida por documento)
