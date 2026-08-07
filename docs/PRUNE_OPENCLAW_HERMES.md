# Inventario poda · OpenClaw + Hermes

**Modo Evolution 2** — descapitar planner/loop libre; Conservar tools/workers/UI.
**No ejecutar poda aún** — solo inventario. control-layer intacto.

## Roles TEAM SEALS
| Componente | Rol |
|------------|-----|
| Wordflow / ControlBus | mando: goals, budget, sheriff, events |
| OpenClaw | UI + tools/skills/MCP |
| Hermes | workers + cola + memoria ejecución |
| Code runtimes | Codex, Claude-Code, Mimo, Kimi, Cline, OpenCode… |
| KER extensions | parallel/swarm/harness (fuera del núcleo) |

## OpenClaw — PODAR (libre)
- agent-loop autónomo / planner LLM libre
- auto-goal sin Goal del ControlBus
- presupuesto modelo sin ResourceGovernor

## OpenClaw — CONSERVAR
- UI / TUI / host
- tools, skills, MCP connectors
- adapters de runtime

## Hermes — PODAR (libre)
- planner LLM de alto nivel
- decisión de cadena sin ContractEngine

## Hermes — CONSERVAR
- workers, cola, job execution
- memoria de ejecución / trajectories
- integración control-layer/hermes/

## Entry TEAM
OpenClaw/Hermes reciben **jobs** desde ControlBus (no inventan goals).
Sheriff + Budget + ModelSlots limitan concurrente.

## Cadenas code (parche)
Backend: OpenCode → OpenHands → Codex → Claude Code  
Frontend: Cline → OpenHands → OpenCode → Codex → Kimi → Mimo

## Siguiente
G0 contratos formales YAML en `groups/` o wire entrypoints (solo con OK).
