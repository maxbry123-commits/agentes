# Repo `agentes` — NCT

| Subagente | Grupo | Tipo | Modelo Cerebras |
|---|---|---|---|
| openclaw/ | - | orquestador | gpt-oss-120b / gemma-4-31b |
| **claude-code-vps-A** | A | coder | gemma-4-31b |
| **claude-code-vps-B** | B | verifier | gpt-oss-120b |
| **mimo-code-vps-A** | A | coder | gemma-4-31b |
| **mimo-code-vps-B** | B | verifier | gpt-oss-120b |

## Distribución de trabajo

| Trabaja en | Responsable |
|---|---|
| **GitHub** (código, docs, configs) | claude-code-vps-A (coder) + claude-code-vps-B (verifier) |
| **VPS** (instalar, monitorear, mantener) | mimo-code-vps-A (coder) + mimo-code-vps-B (verifier) |
| **Orquestación** | OpenClaw + Mavis (router) |

## Flujo coder→verifier
1. coder (A) escribe código o docs
2. verifier (B) audita: lista 3 puntos OK/BUG
3. Si BUG: el coder reescribe
4. Si OK: commit + push

## Skill Router
Todos los agentes consultan skills en `/opt/nct/skills/vault/approved/`.
Ninguno descarga skills por su cuenta.
