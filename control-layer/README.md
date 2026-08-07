# Control Layer (Wordflow)

Capa de control determinista · 90% código / 10% LLM.  
Compatible con Temporal, OpenClaw, Hermes o cualquier agente vía **Adapter + ENCHUFE**.  
**Inmutable por tarea**: token, repo y backup viven en la carpeta del **proyecto** (B1–B8 + config/).

## Árbol

```
control-layer/
├── control/           # Contract Engine (fingerprint→Sheriff)
├── contracts/         # C00–C85 catalog + seeds
├── schemas/           # project_docs + validate_project
├── templates/uoos/    # B1–B8 + RECETA_AGENTE + config_*
├── install/           # source_resolver · no-from-scratch
├── despliegue/        # pipeline 5 pasos
├── gates/             # G30 G28 G31
├── runtime/           # RT-00→RT-90
├── sheriff/           # 5 estados
├── enchufe/           # validator v2
├── adapters/          # AgentAdapter + Temporal
├── sandbox/           # pool + api_slots
├── registry/          # agents · extensions
├── extensions/        # MetaExtension
├── reasoning/         # zona LLM aislada
├── uoos/              # INTEGRACION
├── config/            # leyes L01–L15
└── tests/
```

## Flujo por proyecto
1. Validar carpeta con `schemas.validate_project`
2. Agente rellena plantillas UOOS (RECETA_AGENTE)
3. Gates G31→G30→G28
4. Contract Engine + Sheriff
5. Install source (si aplica)
6. Ejecutar vía Adapter
7. Despliegue: `despliegue.run_deploy` lee config/ del proyecto

## Conectar agente nuevo
1. Implementar `AgentAdapter` (7 funciones)
2. Registrar en `registry/agents.yaml`
3. Validar ficha con `enchufe.validar()`

HF Spaces: **diferido**.
Branch: `workflow/A1-nucleo`
