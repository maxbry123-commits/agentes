# Wordflow Code — README base

**Raíz autorizada en main:** `Wordflow Code/`  
**Repo:** maxbry123-commits/agentes · **rama:** `main`  
**Este archivo no se reescribe.** Parche siguiente: `Wordflow Code/Readme/Readme1/`

## Enlace exacto de esta raíz

https://github.com/maxbry123-commits/agentes/tree/main/Wordflow%20Code

## Qué es

Motor de **programación / code path**. Ciclo reception → goals → pipeline → evidence.  
No es el agente YAIWES (eso es `Yaiwes wordflow`).

## Hot path (no apagar, no reescribir sin paridad de tests)

https://github.com/maxbry123-commits/agentes/blob/main/extensions/wordflow/engine/code_path_runner.py

También: `extensions/wordflow/engine/programming_pipeline.py`

S1 **no** mueve este árbol. Mover el path rompe imports/CI. Cutover de nombre = S2 con tests.

## Arquitectura (README de referencia)

https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/ARQUITECTURA_03_WORDFLOW.md

Fronteras V1: `extensions/wordflow/README_V1_FRONTIERS.md`

## Cuerpo actual

```text
extensions/wordflow/
├── reception/
├── planner/
├── engine/          code_path_runner.py  HOT PATH
├── motors/
├── codegen/
├── connectors/
├── contracts/
├── schemas/
├── standards/
├── state/
├── store/
├── policies/
├── accounts/
├── tests/
├── component_catalog.json
├── connect_catalog.json
├── ficha.v2.json
└── manifest.yaml
```

Flujo:

```text
reception.convert → goals → mission/planner → task_classifier
  → programming_pipeline / code_path_runner
  → loop_bridge → evidence → publish
```

Espejo C-19 (no sustituye hot path): `code-programming-engine/` — candidato S2 (integrar o marcar basura hermana).

`wordflow/` en raíz (ABI) ≠ esta raíz. ABI = extension point. Ver frase Microkernel abajo.

## Main — únicas raíces vivas

`Desplegar/` · `PIPELINE/` · `Método de trabajo/` · `Refactoria/` · `Yaiwes wordflow/` · `Wordflow Code/`  
+ `notas-trabajo-grock/` (estado Grok).

```text
Plan X-N  →  Desplegar/Desplegar N/  →  Refactoria/refactoria-plan-x-N/
```

## Microkernel / Plugin Architecture

El sistema sigue el patrón de **Microkernel Architecture** (también conocido como Plugin Architecture): un núcleo mínimo (`kernel-principal`) que expone puntos de extensión y un registro de plugins, permitiendo añadir capacidades nuevas sin modificar el núcleo. `wordflow/abi.py` (`ExtensionABI`) es la implementación concreta de ese punto de extensión en este repositorio.

No se edita el archivo base del runner para “agregar una capacidad”. Se registra el plugin.  
`extension-kernel` es un nodo ejemplo en Yaiwes, no el basurero de este motor.

## Prohibido

- Crear archivos sin autorización / fuera de raíz viva.
- Reescribir este README (parche = `Readme/Readme1/`).
- Reescribir `code_path_runner.py` sin paridad de tests + Refactoria source/new.
- Inventar adapters/schemas para cerrar gaps.
- Fake PASS.
