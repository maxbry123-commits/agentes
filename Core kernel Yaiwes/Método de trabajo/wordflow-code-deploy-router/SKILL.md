---
name: wordflow-code-deploy-router
description: "Camino de entrada determinista del wordflow YAIWES. Da al agente acceso nativo al repo maxbry123-commits/agentes vía el secret Maxbry_123_tokens y gobierna en qué raíz entra el código (Download code, Desplegar, Refactoria) antes de cualquier despliegue. Usar SIEMPRE ante Download code, Download N, Desplegar N, OP1, OP2, Refactoria source/new, Maxbry_123_tokens, UOOS, Fables, enchufe universal, plugin I/O, X-Ray, council12, PASO 0 a PASO 8, o cualquier pedido de descargar repos en partes sin LFS, extraer ZIP, copiar archivos entre repos con GitHub Actions, o auditar forense/cruzado código descargado. No confundir con el skill hermano research-download-chain, que cubre solo PASO 1."
metadata:
  type: workflow
  version: "2.0.0-consolidated"
  status: CANONICAL
  repo: maxbry123-commits/agentes
  supersedes: "wordflow-paso-control, wordflow-paso-full, wordflow-paso-v3 (nombres retirados, mismo pipeline)"
  sibling_skill: research-download-chain
---

# Wordflow Code Deploy Router

## Propósito

Este skill es el **camino de entrada determinista** del wordflow: le da al agente acceso nativo al repo `maxbry123-commits/agentes` vía el secret `Maxbry_123_tokens`, y gobierna en cuál de las 3 raíces (`Download code`, `Desplegar`, `Refactoria`) entra cada pieza de código antes de llegar al despliegue. No es un checklist suelto — es el enrutador que decide qué PASO corre, con qué evidencia, y qué GATE tiene que cerrar antes de avanzar.

## Mapa de este skill (qué leer y cuándo)

| Archivo | Cuándo leerlo |
|---|---|
| `references/METODO-DE-TRABAJO.md` | Al arrancar — mini-prompt con el DAG completo y todos los enlaces del repo, para seguir leyendo en cadena |
| `references/RULES.yaml` | Ancla. **Si este SKILL.md y el YAML discrepan, gana el YAML** |
| `references/INPUT-BLOCK.md` | Checklist de los 32 ítems citados en las tarjetas de abajo |
| `references/COUNCIL-12.md` | Cadena forense S1→S12, gate final antes del router |
| `references/SOURCE-MAP.md` | Detalle completo de qué hace cada una de las 3 raíces |
| `references/EXTRACCION-FORENSE-AVANZADA.md` | Los 22 bloques oficiales de extracción + auditoría, y la arquitectura de 2 workflows encadenados |
| `references/PLUGIN-REGISTRY.yaml` | Registro único de cableado entre documentos — si un documento y este registro discrepan, gana el registro |
| `assets/*.yml` | GitHub Actions workflows verificados, listos para copiar tal cual |
| `scripts/*.py` `scripts/*.sh` | Código verificado de descarga y extracción, no reescribir |

## Seguridad de tokens (leer antes de tocar cualquier PASO)

GitHub nunca expone el **valor** de un secret una vez guardado — ni por UI ni por API, por diseño. Este skill solo referencia **nombres**, nunca valores. No pegar `ghp_...` en ningún mensaje, commit ni archivo.

| Alias | Cuenta | Uso |
|---|---|---|
| `Maxbry_123_tokens` | A — `maxbry123-commits` | Acceso nativo del agente a todo el wordflow code |
| `EXTERNAL_GH_B_TOKEN` | B | Router PASO 8 |
| `EXTERNAL_GH_C_TOKEN` | C — **HOLD** | Router PASO 8, escritura bloqueada |
| `TARGET_REPO_TOKEN` | genérico | PASO 4, autenticación al repo destino (nunca el token del origen) |
| `HF_TOKEN` | — | Hugging Face Spaces (compute backend) |

## Arranque

1. Validar este directorio con el validador de skills disponible en el entorno (no es un archivo propio de este skill). Si FAIL, no ejecutar el pipeline.
2. Cruzar `references/INPUT-BLOCK.md` (32 ítems).
3. Cargar `references/COUNCIL-12.md` como gate final.
4. Identificar `PASO_EN_CURSO` en `{0, ITEM3, 1, 1b, 2, 3, 4, 5, 6, 7, 8}` y `OUT` en `{OUT1, OUT2, OUT3, none}`.
5. Ejecutar **UNA** tarjeta por turno. Emitir EVIDENCE. Gate rojo = STOP.
6. El LLM no imprime "PASS" por su cuenta — el PASS lo determina el GATE de la tarjeta.

### EVIDENCE (emitir después de cada tarjeta)

```
paso: N
op: OP1|OP2|none
out: OUT1|OUT2|OUT3|none
in_leidos: []
cmds: []
sha_src: ...
sha_dst: ...
gate: OK|FAIL
next: ...
gaps: []
```

## Las 3 raíces (resumen — detalle completo en `references/SOURCE-MAP.md`)

- **Download code** — inbox de código bajado. Acá se extrae. No se refactoriza, no se despliega.
- **Desplegar** — inbox del lote nuevo de un plan. Acá se marca estado y se cablea el deploy. No se edita el origen in-place.
- **Refactoria** — versión vieja. `source/` intocable, `new/` se escribe, cruzado x3 antes de integrar.

## ITEM 3 — bisagra (pre-PASO 1)

```
IN     destino GitHub (owner/repo) aún no confirmado
DO     1. diseñar destino en GitHub y buscar el repo
       2. montar el GitHub Action
       3. extraer del ZIP los archivos del repo EN LA MISMA RAÍZ DEL ZIP
       4. auditar el mismo GitHub Action (self-audit del workflow)
FORBID crear destino sin confirmar owner/repo
GATE   destino existe + workflow montado + extracción en raíz correcta + auditoría del workflow OK
OUT    destino listo para recibir PASO 1
NEXT   PASO 0
```

## PASO 0 — Auditar fuentes (ítems 1-2, 9)

```
IN     repo agentes
       repo TAREA-1
       repo Agentes-motores-Wordflow-YAIWES
       references/SOURCE-MAP.md
DO     abrir en los 3 repos:
         docs/METODO_ZIP_COPY_DETERMINISTA.md
         docs/GUIA-DESPLIEGUE-ZIP-UNIVERSAL.md
       confirmar que los 3 usan el mismo método extract+copy
       auditar cada path de SOURCE-MAP.md
FORBID inventar contenido de guía si el path da 404
GATE   los 3 repos muestran la misma guía zip
       paths de SOURCE-MAP existen, o quedan listados como gap
OUT    lista path+sha de las guías auditadas
NEXT   PASO 1
```

## PASO 1 — Download Action + lista de 20 repos (ítems 4, 10)

Código verificado: `assets/research-download-chain-final.yml` (blob `5950933b...`) + `scripts/research_download_chain.py` (blob `bfc7634f...`). Ambos son el PASS real, run `33134420445` / job `98731080894`.

```
IN     skills/research-download-chain/SKILL.md
       assets/research-download-chain-final.yml
       scripts/research_download_chain.py
DO     copiar la lista 01-20 al input del workflow:
         SearchOS SearXNG OpenDeepResearch GPT-Researcher STORM
         Shandu Vane Haystack Crawl4AI Perplexica
         Dagu Conductor Temporal Argo-Workflows Kestra
         LangGraph Hatchet Windmill Dagster Prefect
       disparar el workflow
FORBID reescribir el packer
       cambiar SPLIT_TARGET=12000000 o MAX_ZIP=17000000
       agregar/quitar slugs o cambiar el orden
GATE   grep -c '"status": "COMPLETE"' MANIFEST == 20
       cada zip <= 17000000 bytes
       unzip -tq == 0 en todos
OUT    Download code/archivos/{slug}_{part}.zip
       RESEARCH_DOWNLOAD_MANIFEST.jsonl
NEXT   PASO 1b
```

## PASO 1b — Reconstruir + X-Ray (método CORREGIDO — reemplaza extracción por-ZIP)

**Auditoría importante:** dos métodos quedaron **retirados** — (1) "una carpeta por archivo ZIP" (`unzip -d ${zip%.zip}`), que rompe repos partidos en varias partes porque `Repo_0001.zip` y `Repo_0002.zip` son el MISMO repo y terminaban en carpetas separadas; (2) `extractall()` sobre una carpeta compartida entre los 61 ZIP, que mezcla/pisa archivos de repos distintos con el mismo nombre (ej. `README.md`). El método correcto agrupa por `slug` del manifest y extrae todas las partes de un repo en una sola carpeta.

Para uso simple: `scripts/extract_reconstruct.sh`. Para la cadena forense completa con las 12 guardas oficiales (Zip Slip, duplicados, cruce contra upstream real) y la arquitectura de 2 workflows encadenados: **`references/EXTRACCION-FORENSE-AVANZADA.md`** + `scripts/xray_extract_audit.py` + `assets/download-extract.yml` + `assets/audit-xray.yml`.

```
IN     zips en Download code/archivos
       RESEARCH_DOWNLOAD_MANIFEST.jsonl
DO     bash scripts/extract_reconstruct.sh "Download code/archivos"
       -- agrupa {slug}_0001.zip + {slug}_0002.zip + ... -> {slug}/
       -- unzip -tq antes de extraer cada parte
       -- genera inventario de paths + SHA-256 por repo
       (o, para el pipeline forense completo, disparar el Workflow 1
       "Download Extract" -- ver EXTRACCION-FORENSE-AVANZADA.md)
FORBID auditar cada parte por separado
       comparar contra main actual (usar siempre source_commit del manifest)
       extraer distintos repos a una carpeta compartida
GATE   Download code/archivos/{slug}/ no vacío
       inventario + SHA-256 generados por repo
OUT    árbol reconstruido + {slug}.paths.txt + {slug}.sha256.txt
NEXT   PASO 2
```

## PASO 2 — Bandeja Download code / Download N (ítems 11-14)

```
IN     N en {1, 2, 3} = tarea en curso
       árbol reconstruido de PASO 1b
DO     mkdir -p "Download code/Download N"
       elegir OP1 o OP2
FORBID mezclar OP1 y OP2 en el mismo N sin evidencia
GATE   "Download code/Download N" existe
OUT    bandeja N lista
NEXT   OP1 o OP2
```

### OP1 — solo parte del code

```
DO     enrutar todos los repos a Download N
       seleccionar SOLO el subset de paths que se van a usar
       extraer ese subset y COPY -> Download code/Download N/<mapped>
FORBID reescribir bytes del ZIP ni del origen
GATE   cada path pedido existe en N
       paths no pedidos no se copian a live_root
NEXT   cruzado
```

### OP2 — repo o agente completo

```
DO     si es software_completo o agente_completo:
         crear raíz nueva en main del destino, O fork y cablear esa raíz
       COPY del tree completo fuente -> DEST_ROOT
FORBID destino owner/repo no declarado
GATE   tree destino cubre el tree fuente
NEXT   cruzado
```

### Cruzado fuente (obligatorio, cierra PASO 2)

```
DO     comparar repo fuente vs destino archivo a archivo
GATE   MISSING=0, EXTRA_inesperado=0, SHA_MISMATCH=0
OUT    evidencia de paths + sha
NEXT   PASO 3 si fue OP1; PASO 4 si OP2 ya vive en destino
```

## PASO 3 — Extract COPY + Fables + UOOS (ítems 15-18)

```
IN     METODO_ZIP_COPY_DETERMINISTA
       GUIA-DESPLIEGUE-ZIP-UNIVERSAL
       Desplegar/Desplegar 1
       UOOS parte 1 y parte 2
       PIPELINE/07 Enchufe Universal (Fables)
       Wordflow Code/FICHAS/07_ENCHUFE_UNIVERSAL.ficha.v2.yaml
       GUIA_REGISTRO_PLUGINS
       PIPELINE/57 EXTRACT_LITERAL
DO     unzip -t ZIP
       unzip -q ZIP -d .staging/<slug>
       filtrar __MACOSX, .DS_Store, Thumbs.db, path-traversal
       COPY (no reescribir) a la raíz donde va a VIVIR el archivo
       verificar sha256(src) == sha256(dst)
       registrar plugin I/O obligatorio: plugin_id, contrato, inputs,
         outputs, extension_point, estado
       JSON o prompt -> emitir .py EXTRACT_LITERAL
       reglas o skill -> .yaml
       leer UOOS + ficha ANTES de armar cualquier extensión/plugin
       repetir el MISMO método con los demás archivos
FORBID editar el origen
       auto-fix o regenerar
       tocar un archivo ya registrado
GATE   sha coincide
       plugin I/O presente
       UOOS 1 y 2 leídos
       ficha leída
OUT    copia en live_root + registro de plugin
NEXT   PASO 4
```

## PASO 4 — GitHub Action copy queue (ítems 19-21)

Código completo en `assets/batch-copy-root-files.yml` (incluye la variante de cola controlada explícita).

```
IN     owner/repo destino
       secret destino TARGET_REPO_TOKEN (o alias de cuenta)
       cola controlada o find -maxdepth 1
DO     on workflow_dispatch
       checkout source (path=source, fetch-depth 1)
       checkout target (path=target, token=env dest, fetch-depth 1)
       GITHUB_TOKEN del source NUNCA cruza al dest
       for FILE in QUEUE: test -f source/$FILE || exit 1; cp source/$FILE target/$MAPPED
       mapeo: README/pyproject -> raíz, app code -> src/,
              config -> config/, tools -> scripts/, tests -> tests/
       git add + UN commit + UN push (sin --force)
       después del copy, registrar plugin I/O de entrada y salida
FORBID llenar la raíz sin mapeo
       editar un archivo ya registrado
       usar el token del source contra el dest
GATE   cada FILE de la cola existe en dest, mapeado
       plugin I/O presente en cada archivo nuevo
OUT    commit en el dest
NEXT   PASO 5
```

## PASO 5 — Estado por nombre + write atómico (ítems 22-24)

```
IN     Desplegar/Desplegar 1 (lote)
       también Desplegar 2 si el runtime vive ahí
DO     analizar la arquitectura de CADA archivo del lote
       el NOMBRE indica el estado; el contenido interno NO se toca para marcarlo:
         pipeline.yaml         -> pendiente, ORIGINAL PROTEGIDO
         ♾️_pipeline.yaml      -> IA trabajando / conversión en proceso
         ✅_pipeline.yaml      -> auditado y convertido
       la seguridad NO es el emoji -- es COPY + HASH + DIFF + VALIDATE + RENAME ATÓMICO
       si hay que reescribir:
         ORIGINAL read-only -> SHA-256 -> IA trabaja en TEMP ->
         DIFF + syntax check -> falla = conservar original ->
         ok = rename atómico -> confirmar que la versión leída no cambió
FORBID editar los bytes del original solo para marcar estado
GATE   original intacto, O (sha_pre == sha_leída AND syntax ok)
OUT    lote nombrado por estado + temp limpio
NEXT   PASO 6
```

## PASO 6 — Deploy determinista + tokens (ítem 25)

```
IN     Desplegar/Desplegar 1 (documentos)
       Desplegar/Desplegar 2 (lote runtime)
       PIPELINE/08_DESPLIEGUE_APPLY_PUSH.md
       PIPELINE/08_DESPLIEGUE_DETERMINISTA_v2.md
       Wordflow Code/core/code_path_runner.py
       Maxbry_123_tokens + aliases del destino
DO     incorporar el método determinista de esos archivos, sin reescribir el runner
       cablear el deploy al FINAL de la cola:
         reception.convert -> goals -> planner -> code_path_runner ->
         loop_bridge -> evidence -> DEPLOY
       verificar que el motor de deploy está activo al final de esa cola
       DRY_RUN por default; REAL solo si GITHUB_DEPLOY_REAL=1
FORBID JSON como runtime (usar Python o YAML)
       editar code_path_runner.py
GATE   la cola del runner termina en DEPLOY
       docs de Desplegar 1 leídos
OUT    ruta de deploy activa
NEXT   PASO 7
```

## PASO 7 — Prompt de code + estándares (ítem 26)

```
IN     prompt de code en el lote de Desplegar 1 / Desplegar 2
       PIPELINE ADVANCED_ENGINEERING_STANDARD
DO     buscar el archivo de prompt de code
       copiar dentro los estándares de programación de alto nivel; quedan como REGLA
       EXTRACT_LITERAL gana sobre "mejorar" el código fuente
FORBID inventar un prompt nuevo si el lote ya trae uno
GATE   el prompt carga el estándar (verificable con grep)
OUT    prompt con estándares inyectados
NEXT   PASO 8
```

## PASO 8 — Router A/B/C + 3 OUT + X-Ray + council12 (ítems 27-32)

```
IN     extensions/wordflow/connectors/external_accounts.yaml
       Maxbry_123_tokens        -> cuenta A (maxbry123-commits)
       EXTERNAL_GH_B_TOKEN      -> cuenta B
       EXTERNAL_GH_C_TOKEN      -> cuenta C (HOLD)
DO     registrar cada repo en el registry con ruta y modo:
         SOURCE_01, SOURCE_02 (read) / WORK_01 (process) / DESTINATION_01 (write)
       incluir agentes de TAREA-1, YAIWES, Wordflow-Code, frontend
       Maxbry_123_tokens = token paraguas para todos los repos de Wordflow Code
       CABLE A = arquitectura de programación en Wordflow Code
       CABLE B = sistema de despliegue (apply_push)
       elegir UNA sola salida (ítem 28)
FORBID escribir en cuenta C mientras esté en HOLD
       desplegar sin que X-Ray y council12 hayan corrido
GATE   registry tiene el path de cada repo
       OUT elegido
       X-Ray corrió
       council12 emitió sus 12 salidas
OUT    ver tarjetas OUT1/OUT2/OUT3
NEXT   Tarea 3 (copias solo con evidencia)
```

### OUT1 — chat UOOS

```
DO     emitir UOOS parte 1 y parte 2 en el chat, formato .py o .yaml
       JSON solo si es una ficha ya registrada
GATE   ambos documentos UOOS presentes
```

### OUT2 — destino remoto

```
DO     resolver owner+repo desde los docs del proyecto
       si no está en los docs, preguntar en el chat cuenta y repo
       si el repo no existe, crearlo y luego correr apply_push
GATE   destino resuelto Y (push o creación con evidencia)
```

### OUT3 — cuenta A

```
DO     raíz organizada en maxbry123-commits/agentes: src/ config/ scripts/ tests/ + evidence
GATE   la estructura de destino existe
```

### X-Ray + council12

Pipeline en 2 workflows encadenados (no un job único): `assets/download-extract.yml` → dispara automático vía `workflow_run` → `assets/audit-xray.yml`. Detalle completo de los 22 bloques oficiales en `references/EXTRACCION-FORENSE-AVANZADA.md`; cadena S1-S12 en `references/COUNCIL-12.md`.

```
DO     audit_forensic sobre los documentos entrantes
       MD -> code vía EXTRACT_LITERAL (PIPELINE/57)
       Workflow 1 extrae (agrupado por slug) y sube evidence/ como artifact
       Workflow 2 se dispara solo si Workflow 1 terminó en success,
         descarga con download-artifact@v8 + run-id, cruza contra upstream
       si el módulo council no existe, crearlo en sandbox y registrar el plugin
FORBID disparar "Audit" manualmente (solo workflow_run)
GATE   xray/input/EXTRACTION.json existe tal cual (ver stop: artifact_path_mismatch)
       las 12 salidas de council12 quedaron emitidas
```

## Tarea 3 — destinos (ítem 32, post-evidencia)

```
canonical  skills/wordflow-code-deploy-router/
copia      Método de trabajo/wordflow-code-deploy-router/
copia      Download code/wordflow-code-deploy-router/
copia      Desplegar/wordflow-code-deploy-router/
copia      Refactoria/wordflow-code-deploy-router/
parche     Wordflow Code/Readme/Readme1/ (cable only)
```

## Gaps declarados (no inventados)

Los ítems **5, 6, 7 y 8** de `references/INPUT-BLOCK.md` no tienen contenido fuente confirmado por el Director. No bloquean el pipeline (no son GATE) y no se completan con contenido inventado. Si aparece evidencia, se agregan sin renumerar el resto.

## STOP (cualquiera de estas detiene el pipeline)

`path` con 404 · token en claro (`ghp_...` pegado) · packer reescrito · SHA mismatch · plugin I/O ausente · lista de 20 repos alterada · escritura en cuenta C (HOLD) · council sin sus 12 salidas · falla la validación del skill · Zip Slip detectado · nombre de archivo duplicado dentro de un ZIP · extracción plana sobre carpeta compartida entre repos · path de artifact anidado (`evidence/EXTRACTION.json` en vez de `EXTRACTION.json` en la raíz) · workflow "Audit" disparado a mano en vez de por `workflow_run`.

## Cableado

Este `SKILL.md` es el nodo raíz de `references/PLUGIN-REGISTRY.yaml` — cada PASO y cada OUT tiene ahí su propio `plugin_id` con `upstream`/`downstream` explícitos. Si necesitás saber qué alimenta a qué, ese registro es la fuente única; no lo reconstruyas leyendo solo este archivo.
