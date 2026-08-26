# Yaiwes wordflow — README base

**Raíz autorizada en main:** `Yaiwes wordflow/`  
**Repo:** maxbry123-commits/agentes · **rama:** `main`  
**Este archivo no se reescribe.** Parche siguiente: `Yaiwes wordflow/Readme/Readme1/`

## Enlace exacto de esta raíz

https://github.com/maxbry123-commits/agentes/tree/main/Yaiwes%20wordflow

## Qué es

Wordflow del **agente YAIWES**. Producto / sistema agente.  
No es el motor de programación de code (eso es `Wordflow Code`).

## Plan de trabajo vivo (no es este README)

https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/PLAN_YAIWES_AGENTE_WORDFLOW.md

`PLAN_100_ESTRUCTURA_DEFINITIVA.md` = mapa de árbol. **No** es el plan de trabajo.

## Cuerpo actual (hasta cutover S2)

El árbol materializado sigue en `agente-yaiwes/` (LEGACY de nombre).  
Arquitectura: `agente-yaiwes/PLAN_100_ESTRUCTURA_DEFINITIVA.md` + `agente-yaiwes/STRUCTURE.md`.  
S2/GPT mueve el cuerpo a esta raíz. Hasta entonces no se duplica code.

Mapa: [SOURCE.md](../SOURCE.md)

## Main — únicas raíces vivas

| Raíz | Rol |
|---|---|
| `Desplegar/` | Inbox. `Desplegar N/` = docs/code del Plan X-N. No hardcodear N=1. |
| `PIPELINE/` | Plan vivo de la misión + molde (S3). Plan actual no se toca. |
| `Método de trabajo/` | Reglas. Base no se reescribe; falta = parche. |
| `Refactoria/` | `refactoria-plan-x-N/` = versión VIEJA a modificar de ese plan. |
| `Yaiwes wordflow/` | Esta raíz. |
| `Wordflow Code/` | Motor de programación / hot path. |
| `notas-trabajo-grock/` | Solo estado Grok. No es Wordflow. |

Cableado ejemplo (N variable):

```text
Plan X-N  →  Desplegar/Desplegar N/  →  Refactoria/refactoria-plan-x-N/
```

## Árbol que debe tener esta raíz (mapa PLAN_100, recorte)

```text
Yaiwes wordflow/
├── kernel-principal/
├── input-layer/
├── definition-registry/
├── control-governance/
├── multi-workflow-engine/
├── execution-orchestration/
├── execution-engine-pool/
├── agent-fleet-parallelism/
├── deploy-publish/
├── observability/
├── extensions/          ← REFs; no dump. extension-kernel = UN nodo ejemplo
├── Readme/             ← este README + parches Readme1, Readme2
└── SOURCE.md
```

Hot path de code **no** vive aquí. Vive en Wordflow Code.

## Microkernel / Plugin Architecture

El sistema sigue el patrón de **Microkernel Architecture** (también conocido como Plugin Architecture): un núcleo mínimo (`kernel-principal`) que expone puntos de extensión y un registro de plugins, permitiendo añadir capacidades nuevas sin modificar el núcleo. `wordflow/abi.py` (`ExtensionABI`) es la implementación concreta de ese punto de extensión en este repositorio.

- Extension point / plugin contract
- Plugin Registry
- Ciclo de vida del núcleo

`extension-kernel` (abi-mount, capability-registry, mount-guard) es **un nodo ejemplo**. Prohibido meter todo lo nuevo ahí.

## Prohibido

- Crear archivos sin autorización del Director.
- Crear archivos fuera de las raíces vivas.
- Reescribir este README. Parche = `Readme/Readme1/`.
- Inventar nombres de raíz.
- Editar archivo base de code/docs: se cablea parche + registro.
- Apagar el hot path.
- Declarar PASS sin evidencia GitHub.
