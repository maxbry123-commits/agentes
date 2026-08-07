# WORKFLOW MAESTRO · Control Layer

**Regla:** un solo sistema de control. No segundo orquestador.
**LLM** = razonamiento · **Workflow** = coordinación determinista · **Adapters** = intercambiables.

## Mapa a código (`control-layer/`)

| Bloque arquitectura | Path actual / destino |
|---------------------|----------------------|
| Control Kernel | `bootstrap.py` + `config.py` |
| Contract Engine | `contract_engine/` + `contracts/` |
| Sentinela schemas | `contract_engine/sentinela_router.py` |
| Sheriff 5 + domain | `sheriff/` |
| Memory Control Plane | `memory/` (MC01–MC08) |
| Durable / loops | `runtime/` + `loops/` |
| Dual entry | `wordflow/` + `extension/` |
| Goals 10/10 | `contracts/goals_*.yaml` |
| Failure | `contracts/failure.py` |
| Budget / Priority | `contracts/budget.py` |
| Input gateway | `input/` |
| Change Engine | `change/` |
| Agents / Harness | `agents/` |
| Skills | `skills/` |
| Source Mirror | `source_mirror/` |
| Events | `observability/` |
| GitHub broker | `github/` (interface) |

## Principios inmutables
1. No reconstruir Workflow por cambio de agente/memoria/sandbox.
2. Agente no recibe token GitHub.
3. NEW_TASK no mezcla misión en curso.
4. 0% LLM en selección de contratos / Sheriff.
5. Checkpoint > restart from zero.

## Diferido
HF · binario · Graphiti obligatorio · Temporal como núcleo · osquestador kernel memoria full
