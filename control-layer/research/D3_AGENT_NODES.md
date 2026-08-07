# D3 · nodes/*.yaml (Agent) — Salida investigación

## Fuentes
- Microsoft AgentSchema / Foundry: AgentDefinition, tools, resources, parameters secrets
- dabit3/agent-manifest: capabilities[{name,input,output}], requirements, behaviors.autonomy
- Hovborg multi-agent catalog: name, version, tools, cost_profile, safety, orchestration, protocols.a2a
- CrewAI agents.yaml: role, goal, backstory, tools, memory, allow_delegation, max_iter
- Open Agent Spec: agent + intelligence + tasks depends_on
- Claude Code agents: flat .md + frontmatter name/description/tools/model
- agent-contracts: can_invoke_agents, handoffs, artifacts
- Router by capability (nuestro modelo) vs hardcode agent id

## Gaps plantilla B3_agent
1. Sin description/purpose legible
2. capabilities como strings simples (OK) pero sin nivel de confidence
3. Sin budget tokens/time
4. Sin safety.side_effect_risk
5. Sin model preference opcional
6. Sin entrypoint / adapter_id
7. Sin denied_tools explícito

## Principios 100×
- type: agent obligatorio
- id único en proyecto
- capabilities → índice Router
- memory.global default false + Sheriff
- permissions.tools allowlist
- Discovery solo lee YAML; autorización = Sheriff
