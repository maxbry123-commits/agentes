# Repo `agentes` — 4 subagentes de NCT

Este repo contiene los 4 subagentes que viven dentro del VPS:

| Subagente | Rol | Modelo Cerebras | Función |
|---|---|---|---|
| **claude-code-A** | coder | `gemma-4-31b` | Escribe código |
| **claude-code-B** | verifier | `gpt-oss-120b` | Revisa y corrige |
| **mimo-code-A** | coder | `gemma-4-31b` | Escribe código |
| **mimo-code-B** | verifier | `gpt-oss-120b` | Revisa y corrige |

## Flujo de trabajo
1. coder (A) escribe el código
2. verifier (B) lo revisa y corrige
3. Se commitea y pushea a la rama
4. OpenClaw orquesta ambos

## Skill Router
Los 4 subagentes consultan skills únicamente desde `/opt/nct/skills/vault/approved/`. Nunca descargan skills por su cuenta.

## Memoria
Cada subagente tiene su BD SQLite independiente en `/opt/nct/memory/<subagente>/state.db` con permisos 600.
