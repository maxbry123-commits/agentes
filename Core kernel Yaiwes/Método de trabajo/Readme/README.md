# Método de trabajo — README parche S1 (no reescribe el base)

**Raíz autorizada:** `Método de trabajo/`  
Base que NO se toca:

- https://github.com/maxbry123-commits/agentes/blob/main/README_METHOD.md
- https://github.com/maxbry123-commits/agentes/blob/main/M%C3%A9todo%20de%20trabajo/GUIA_REGISTRO_PLUGINS_Y_CABLEADO.md

Este archivo es parche. Siguiente: `Método de trabajo/Readme/Readme1/`.

## Regla de archivos (obligatoria)

No reescribir el archivo base (docs o code).  
Archivo nuevo = parche + enlace al anterior.  
Si ya no sirve → se borra el parche. No “reparar” el base en un bucle commit/push.

```text
…/Readme/
…/Readme/Readme1/
…/Readme/Readme2/
```

## Microkernel / Plugin Architecture

El sistema sigue el patrón de **Microkernel Architecture** (también conocido como Plugin Architecture): un núcleo mínimo (`kernel-principal`) que expone puntos de extensión y un registro de plugins, permitiendo añadir capacidades nuevas sin modificar el núcleo. `wordflow/abi.py` (`ExtensionABI`) es la implementación concreta de ese punto de extensión en este repositorio.

`extension-kernel` es un nodo ejemplo. No es destino de todo lo nuevo.

## Cableado de un plan

```text
Plan X-N → Desplegar/Desplegar N/ → Refactoria/refactoria-plan-x-N/
```

## Prohibido

Crear archivos sin autorización o fuera de las raíces vivas de main.
