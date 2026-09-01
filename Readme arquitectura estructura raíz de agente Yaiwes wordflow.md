# Readme arquitectura estructura raiz de agente Yaiwes wordflow

Repo: `maxbry123-commits/agentes` · rama `main`  
Uso: llenar `schema: tel.workflow/v3` (`workflow.yaml`) con paths literales.  
Lock: no mover `.github` / `control-layer` / `extensions`. No reescribir packer.

## Indice raiz (agentes) — explicacion extendida

1. `.github` — YAML GitHub Actions. Arranca runners, checkout, python packer, commit. No es el agente. Infra CI. Queda.

2. `control-layer` — kernel de control Python: contratos, loops, sheriff, inputblock, runtime. El Wordflow YAIWES lee reglas aqui. Code core. Lock.

3. `extensions` — plugins (adapters, audit_forensic, github_deploy, wordflow_kernel). Code enchufable. Lock.

4. `scripts` — `research_download_chain.py` y variantes. Bajan OS a zip 12MB. Herramienta, no runtime Wordflow. No reescribir.

5. `memory` — `ledger.jsonl`. Bitacora de estado. Dato, no LLM.

6. `tools` — `wordflow_verification.py`. Test del wordflow. Code test.

7. `docs` — markdown metodo/zip/Hermes. No ejecuta. Destino: `Documentos proyectos Yaiwes/documentos proyecto Yaiwes 1/docs`.

8. `groups` — `roles.yaml`. Roles del fleet. Config. Queda en main.

9. `Yaiwes wordflow` — SOURCE.md vacio. Fusion a Documentos Yaiwes.

10. `Agente Yaiwes/Agente core kernel Yaiwes` — NO es kernel: zips Dagster/Kafka/crewAI/Temporal. Destino `Download code Yaiwes`.

11. `Agente core kernel Yaiwes principal` — raiz kernel vacia (.keep). Arbol vivo: `agente-yaiwes/`.

12. `agente-yaiwes` — estructura real YAIWES. Code Wordflow agente.

13. `despliegue` — py pool/metering funcional → `agente-yaiwes/deploy-publish`. md → Documentos Yaiwes. Distinto de `Desplegar`.

14. `TASK-GAPS` — forense 01-09. Evidencia. Queda.

15. `code-programming-engine` — motor programar. Destino nct-core.

16. `Download code` + `Download code Yaiwes` — zips OS.

17. `Documentos proyectos Yaiwes/documentos proyecto Yaiwes 1` — docs inbox.

18. `Desplegar` / `Desplegar Yaiwes` — inbox Director.

19. `PIPELINE` / `Refactoria` / `Método de trabajo` / `skills` — plan y skills.

20. `Wordflow Code` — anexos copiados a nct-core/skills agente nct.

## Contrato tel.workflow/v3

```yaml
schema: tel.workflow/v3
repo: maxbry123-commits/agentes
branch: main
agent_root: agente-yaiwes
kernel_alias: Agente core kernel Yaiwes principal
docs_root: Documentos proyectos Yaiwes/documentos proyecto Yaiwes 1
download_root: Download code Yaiwes
lock: [".github", "control-layer", "extensions"]
```
