# D1 · PROJECT_MANIFEST — Salida investigación

## Fuentes (síntesis)
- Microsoft AgentSchema / Foundry agent.yaml: name, version, metadata, parameters(secrets), resources
- Agent Identity Protocol (manifest.yaml): identity, permissions, behavior_profile, trust
- nakurian/agent-architect: manifest = single source of truth; local overrides gitignored
- OpenAPM apm.yml: name+version required; policy; x- extensions reserved
- dabit3/agent-manifest: capabilities with I/O schemas; requirements; behaviors.autonomy
- CrewAI CN: agents.yaml separado de tasks.yaml (quién ≠ qué)
- agent-contracts: system.id + default_workflow_order + guardrails
- Cursor: AGENTS.md / project-context corto; no secretos; reglas <500 líneas
- Composio AO: proyecto con key estable + path; config global vs per-project
- India/Medium CrewAI: role/goal/backstory en agents; tasks con expected_output

## Gaps de nuestra plantilla actual
1. Falta schema_version explícito
2. Falta quality_gates / success medible
3. Falta policy (autonomy max, human gates)
4. Falta tenant_id default formal
5. Falta lista de forbidden_paths para Sheriff
6. what_it_is_not débil vs limits.hard duplicados
7. No declara control_layer_min version
8. No hay provenance (created_at, owner_id)

## Mejoras 100× (principios)
- Manifest = contrato de interpretación de la carpeta (no runtime state)
- Solo IDs y globs; agentes viven en nodes/
- Secrets solo por ref (env names)
- success_criteria verificables por máquina
- memory isolation formula fija
- Sheriff lee: agents_source, workflows_source, limits.hard, forbidden_paths
