# Repo `agentes` — NCT

| Subagente | Grupo | Tipo | Modelo |
|---|---|---|---|
| openclaw/ | - | orquestador | gpt-oss-120b / gemma-4-31b |
| **claude-code-vps-A** | A | coder (principal) | gemma-4-31b |
| **claude-code-vps-B** | B | verifier (principal) | gpt-oss-120b |
| **mimo-code-vps-A** | A | coder (principal) | gemma-4-31b |
| **mimo-code-vps-B** | B | verifier (principal) | gpt-oss-120b |
| **claude-code-vps-C** | C | coder (backup) | gemma-4-31b |
| **mimo-code-vps-C** | C | coder (backup) | gemma-4-31b |
| **claude-code-vps-D** | D | verifier (backup) | gpt-oss-120b |
| **mimo-code-vps-D** | D | verifier (backup) | gpt-oss-120b |

## Distribucion de trabajo
- **GitHub** (codigo, docs): claude-code-vps-A (coder) + claude-code-vps-B (verifier)
- **VPS** (instalar, monitorear): mimo-code-vps-A (coder) + mimo-code-vps-B (verifier)
- **Backups**: C y D se activan cuando A o B estan ocupados

## Skill Router
Todos consultan skills en /opt/nct/skills/vault/approved/.
Ninguno descarga skills por su cuenta.
