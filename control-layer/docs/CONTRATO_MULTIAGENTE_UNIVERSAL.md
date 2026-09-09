# Contrato multiagente universal Wordflow

Objetivo: cualquier proyecto + cualquier orquestador + cualquier coder, sin reescribir la capa.

## Roles

| Rol | Quién | Cómo entra |
|-----|--------|------------|
| **Interface / Orquestador** | OpenClaw, temporal, Hermes, custom OS | `adapter.id` + entrypoint en `nodes/*.yaml` |
| **Coder / Specialist** | Claude Code, Codex, Cursor agent, Kimi CLI, OpenHands, Aider, Mimo, etc. | mismo: capability + adapter |
| **Human gate** | Director | `type: human_gate` o policy HUMAN_GATE |

## Regla de oro
La capa de control **nunca** hardcodea Claude/Cursor/OpenClaw.
Solo conoce:
1. `PROJECT/` declarativo (D1–D10)
2. `nodes/*.yaml` → capabilities + adapter.id
3. `dag/*.yaml` → required_capabilities
4. LoopEngine pide **capability** → Router elige nodo

## Añadir un agente nuevo (1 archivo)

```yaml
# nodes/claude_code.yaml
schema_version: "2.0"
kind: AGENT_NODE
id: claude_code
capabilities: [code_generation, debugging, review]
adapter:
  id: generic          # o openclaw si va por ese bridge
  entrypoint: "./bin/claude-code-wrapper"  # CLI que habla JSON stdin/stdout
```

Sin tocar engine, router, sheriff ni plantillas globales.

## Contrato de ejecución (todos los wrappers)

**stdin JSON:**
```json
{"capability": "code_generation", "payload": {...}, "agent_id": "claude_code"}
```

**stdout JSON:**
```json
{"ok": true, "output": {...}, "error": null, "tokens_used": 0}
```

Implementado en `runtime_factory._subprocess_fn`.

## OpenClaw como interface

```yaml
id: openclaw_ui
capabilities: [orchestration, planning, user_interface]
adapter:
  id: openclaw
  entrypoint: openclaw   # OPENCLAW_BIN
```

Orquestador planifica; coders en otros nodes con `code_generation`.

## Autonomía por proyecto (D1)

```yaml
policy:
  autonomy_max: supervised | semi | autonomous
  human_gates: [deploy_production]
```

Sheriff + tribunal + recovery limitan daño; no dependen del vendor del agente.

## Superior a Cursor/Copilot/Replit (diseño)

| Dimensión | Wordflow |
|-----------|----------|
| Multiagente | N nodos por capability |
| Proyecto portátil | carpeta D1–D10 |
| Vendor lock | cero |
| Despliegue | scripts 0% LLM |
| Recovery | 11 acciones + policy |
| Auditoría | evidence + event hash |

(La ventaja es **arquitectura**; el binario/CLI real de cada vendor es wrapper en el proyecto.)
