# EVIDENCIA — DESCARGA DE 5 COMPONENTES — AGENTE YAIWES

> Discrepancia documental: la misión contiene **5 componentes**, pero por instrucción se conserva exactamente el nombre solicitado del archivo `EVIDENCIA-DESCARGA-4-COMPONENTES.md`.

## Identificación de la misión

- Schema: `yaiwes.component-ops/v1`
- Repo: `maxbry123-commits/agentes`
- Branch: `main`
- Modo: `FAIL_CLOSED_STRICT_3_STEPS`
- Flujo ejecutado: `RESEARCH → EXECUTE → VALIDATE`
- Manifest canónico: `Core kernel Yaiwes/Download code Yaiwes/RESEARCH_DOWNLOAD_MANIFEST.jsonl`
- GitHub Actions run de ejecución: `35275508914`
- Job de ejecución: `105385047076` (`download-validate-publish`)
- Commit de publicación de los componentes y manifest: `8ce131735ee82e0b5ed7451a8abd5a423b2c5fea`

## PASO 1 — RESEARCH

Los cinco componentes se investigaron individualmente antes de la descarga. No se aceptó una coincidencia únicamente por nombre.

### 1. Omniroute

- Repositorio verificado: `https://github.com/diegosouzapw/OmniRoute.git`
- Propietario: `diegosouzapw`
- Verificación funcional: gateway de IA con una interfaz para múltiples proveedores/modelos.
- HEAD fijado: `9688032451fc52017df537fd6f7b86baa49503fc`
- Clasificación: `VERIFIED`

### 2. Orca

- Repositorio verificado: `https://github.com/stablyai/orca.git`
- Propietario/organización: `stablyai`
- Verificación funcional: ADE/entorno para trabajar con una flota de agentes paralelos, con superficies desktop/móvil/runtime remoto; se descartaron otros proyectos homónimos.
- HEAD fijado: `8e8a9b38ea2b9a2a621bc891304efa072826e7d5`
- Clasificación: `VERIFIED`

### 3. Omarchy

- Repositorio verificado: `https://github.com/omacom/omarchy.git`
- Organización: `omacom`
- Verificación funcional: distribución Linux de DHH basada en Arch/configuración de sistema operativo; no es una simple librería.
- HEAD fijado: `9c5482c58dbe4974de337450754885083c91eada`
- Clasificación: `VERIFIED`

### 4. Anydoc

- Repositorio verificado: `https://github.com/firecrawl/anydoc.git`
- Organización: `firecrawl`
- Verificación funcional: conversión de Word, PowerPoint, Excel, OpenDocument, RTF, EPUB, CSV y PDF a Markdown; implementación principal en Rust.
- HEAD fijado: `261fc257d17c3eab0f673be31c408fd9fdc2171a`
- Clasificación: `VERIFIED`

### 5. Skill Design de Anthropic — `skill-creator`

- Fuente oficial verificada: `https://github.com/anthropics/skills.git`
- Organización oficial: `anthropics`
- Capacidad exacta verificada: `skills/skill-creator/`, incluyendo `SKILL.md` con `name: skill-creator`.
- HEAD fijado: `34040c9c568585f6929bedeaad110ad08f079624`
- Clasificación: `VERIFIED`
- No se aceptaron forks, mirrors ni recopilaciones de terceros.

## PASO 2 — EXECUTE

La ejecución se hizo de forma fail-closed sobre los cinco componentes verificados:

1. Se comprobó que los cinco destinos solicitados no existían previamente.
2. Se clonó cada fuente por su SHA completo fijado y se comprobó el `HEAD` de la copia descargada.
3. Se materializó únicamente el árbol solicitado en su destino, excluyendo únicamente los metadatos transitorios `.git` de las copias de trabajo.
4. Para Anthropic se materializó exclusivamente el subárbol oficial `skills/skill-creator/` en `Skills agente/skill-design-anthropic/`.
5. Antes de marcar `COMPLETE`, se comparó cada árbol descargado contra su destino.
6. Solo después de pasar esas validaciones se actualizaron las cinco entradas del manifest canónico.
7. El runner temporal usado para ejecutar esta operación se autoeliminó en el mismo commit de publicación.

Incidencia operativa corregida: un intento inicial de materialización mediante gitlink/árbol GitHub devolvió HTTP `422` antes de escribir contenido. No se marcó ningún componente `COMPLETE` por ese intento. La ejecución válida se realizó posteriormente mediante clonación a SHA fijado, materialización, comparación y publicación en GitHub Actions.

## PASO 3 — VALIDATE

Criterios aplicados a cada componente:

- `SOURCE COMMIT == DOWNLOADED COMMIT`.
- El destino existe físicamente en `main`.
- El contenido materializado corresponde al árbol de la fuente fijada.
- La entrada del manifest contiene la URL real `.git`, el SHA real y `status: COMPLETE`.
- No se movió ningún componente a `Agente Yaiwes principal`.
- No se modificó el código fuente de los componentes durante esta misión.

Resultado global de validación: **5/5 COMPLETE**.

## Evidencia por componente

### COMPONENTE 1

COMPONENT: Omniroute  
SOURCE: https://github.com/diegosouzapw/OmniRoute.git  
SOURCE VERIFIED: YES — gateway multi-proveedor de IA verificado  
SOURCE COMMIT: 9688032451fc52017df537fd6f7b86baa49503fc  
DESTINATION: Core kernel Yaiwes/omniroute/  
DESTINATION EXISTS: YES  
DOWNLOADED COMMIT: 9688032451fc52017df537fd6f7b86baa49503fc  
STATUS: COMPLETE  
GAP: NONE

### COMPONENTE 2

COMPONENT: Orca  
SOURCE: https://github.com/stablyai/orca.git  
SOURCE VERIFIED: YES — ADE/entorno gráfico para flota de agentes paralelos; homónimos descartados  
SOURCE COMMIT: 8e8a9b38ea2b9a2a621bc891304efa072826e7d5  
DESTINATION: Core kernel Yaiwes/orca/  
DESTINATION EXISTS: YES  
DOWNLOADED COMMIT: 8e8a9b38ea2b9a2a621bc891304efa072826e7d5  
STATUS: COMPLETE  
GAP: NONE

### COMPONENTE 3

COMPONENT: Omarchy  
SOURCE: https://github.com/omacom/omarchy.git  
SOURCE VERIFIED: YES — distribución/configuración Linux de DHH basada en Arch; no es una librería  
SOURCE COMMIT: 9c5482c58dbe4974de337450754885083c91eada  
DESTINATION: Core kernel Yaiwes/omarchy/  
DESTINATION EXISTS: YES  
DOWNLOADED COMMIT: 9c5482c58dbe4974de337450754885083c91eada  
STATUS: COMPLETE  
GAP: NONE

### COMPONENTE 4

COMPONENT: Anydoc  
SOURCE: https://github.com/firecrawl/anydoc.git  
SOURCE VERIFIED: YES — conversor de documentos/archivos a Markdown con implementación principal en Rust  
SOURCE COMMIT: 261fc257d17c3eab0f673be31c408fd9fdc2171a  
DESTINATION: Core kernel Yaiwes/anydoc/  
DESTINATION EXISTS: YES  
DOWNLOADED COMMIT: 261fc257d17c3eab0f673be31c408fd9fdc2171a  
STATUS: COMPLETE  
GAP: NONE

### COMPONENTE 5

COMPONENT: Skill Design de Anthropic — skill-creator  
SOURCE: https://github.com/anthropics/skills.git  
SOURCE VERIFIED: YES — fuente oficial Anthropic y subárbol exacto `skills/skill-creator/` verificado  
SOURCE COMMIT: 34040c9c568585f6929bedeaad110ad08f079624  
DESTINATION: Skills agente/skill-design-anthropic/  
DESTINATION EXISTS: YES  
DOWNLOADED COMMIT: 34040c9c568585f6929bedeaad110ad08f079624  
STATUS: COMPLETE  
GAP: NONE

## Manifest registrado

```jsonl
{"number": 1, "parts": 1, "slug": "Omniroute", "source": "https://github.com/diegosouzapw/OmniRoute.git", "source_commit": "9688032451fc52017df537fd6f7b86baa49503fc", "status": "COMPLETE"}
{"number": 2, "parts": 1, "slug": "Orca", "source": "https://github.com/stablyai/orca.git", "source_commit": "8e8a9b38ea2b9a2a621bc891304efa072826e7d5", "status": "COMPLETE"}
{"number": 3, "parts": 1, "slug": "Omarchy", "source": "https://github.com/omacom/omarchy.git", "source_commit": "9c5482c58dbe4974de337450754885083c91eada", "status": "COMPLETE"}
{"number": 4, "parts": 1, "slug": "Anydoc", "source": "https://github.com/firecrawl/anydoc.git", "source_commit": "261fc257d17c3eab0f673be31c408fd9fdc2171a", "status": "COMPLETE"}
{"number": 5, "parts": 1, "slug": "Skill Design de Anthropic", "source": "https://github.com/anthropics/skills.git", "source_commit": "34040c9c568585f6929bedeaad110ad08f079624", "status": "COMPLETE"}
```

## Cierre

- Fuente verificada: **5/5**
- SHA de fuente fijado: **5/5**
- Descarga real a SHA fijado: **5/5**
- `SOURCE COMMIT == DOWNLOADED COMMIT`: **5/5**
- Destino confirmado: **5/5**
- Árbol fuente/destino validado: **5/5**
- Manifest actualizado: **5/5**
- Estado final: **100% COMPLETE**
- Gaps abiertos de esta misión: **NONE**
