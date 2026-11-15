---
name: wordflow-code-deploy-router
description: Contrato P01-P08 + 3 salidas deploy + plugin I/O + X-Ray + council12 + operaciones seguras COPY/MOVE por lotes. Trigger on Download code, Download N, Desplegar N, OP1 parte, OP2 repo completo, Maxbry_123_tokens, UOOS, Fables enchufe, copiar lotes, mover archivos. Copiar INPUT BLOCK literal. No rewrite.
metadata:
  type: workflow
  version: "0.5.0-file-transfer-safe"
  status: EDIT_UNTIL_WIRED
  repo: maxbry123-commits/agentes
---

# Wordflow Code Deploy Router

AI lee INPUT BLOCK literal. No omitir opcion. STOP si gate falla. LLM no declara PASS.

## INPUT BLOCK (copiar literal / cruzar checklist)

1. Buscar sistema zip como se saca el archivo y como se copia el archivo.
2. Buscarlo en repo agentes AND repo TAREA-1 AND repo Agentes-motores-Wordflow-YAIWES.
3. Cablear todo.
4. Cable 1 skills de descarga de repo.
5. Cable 2 Refactoria.
6. Cable 3 Download code.
7. Cable 4 Desplegar.
8. Mini prompt tipo DAG de programacion (sin URLs en el flujo).
9. Auditar cada path fuente antes de usarlo.
10. Paso 1 usar skills de descarga en GitHub Action. Poner la lista de todos los repo que se van a descargar.
11. Paso 2 crear carpeta Download code. Luego Download 1 o 2 o 3 = tarea en curso.
12. Paso 2 OP1 usar solo parte del code de descarga. Enrutar a Download code 1 o 2 o 3.
13. Paso 2 OP2 si se usa todo el repo (software completo o repo completo de un agente) enrutar a una raiz nueva en main de fork y se cablea.
14. Verificacion cruzada con el repo fuente. Validar que no falte ningun archivo.
15. Paso 3 si se usa solo parte del code usar sistema de extraccion de la guia de extraccion de archivos que estan en los zip. Enviar COPIA a la raiz donde va a vivir el archivo. Se copia no se reescribe.
16. Usar sistema plugins de Fables. Si es JSON o prompt se convierte en python. YAML solo si es para reglas o skills.
17. Buscar en Desplegar 1 UOOS parte 1 y 2, Enchufe universal de Fables y la ficha de conexion para que la AI sepa como se usa, como se hace la extension code y el plugins.
18. Luego el mismo metodo con los demas archivos.
19. Paso 4 copiar archivos con GitHub Action checkout source + checkout target + cola + metodo COPY seguro + un commit + un push. Token dest. GITHUB_TOKEN no cruza repo.
20. Destino = raiz organizada solo en el repo y estructura destino. Project files en raiz. src/ code. config/ config. scripts/ tools. tests/ tests. Distribuir por funcion no llenar la raiz.
21. Cada archivo debe tener plugins obligatorios de entrada y salida. Prohibido editar mas ni tocar el archivo registrado.
22. Paso 5 en raiz Desplegar / Desplegar 1 analizar arquitectura de cada archivo del lote.
23. Nombre = estado. No modificar contenido interno. pipeline.yaml pendiente. process prefix = IA trabajando. done prefix = auditado y convertido.
24. Si requiere reescribir ORIGINAL READ-ONLY SHA256 AI trabaja COPIA DIFF VALIDACION aprobado reemplazo atomico. Falla = conservar original.
25. Paso 6 sistema de despliegue en Desplegar/Desplegar 1. Incorporar metodo determinista de esos archivos. Regla no JSON runtime. Todo en python y yaml.
26. Paso 7 buscar prompt de code en Desplegar 1 / lote deploy. Copiar dentro los estandares de programacion de alto nivel como regla.
27. Paso 8 enrutar repos A B C ya cableados por token secreto GitHub. Poner ruta de cada repo. Registry SOURCE WORK DEST. Token Maxbry_123_tokens para todos los repos Wordflow Code.
28. Enrutar token en Wordflow Code y en el sistema de despliegue al final del code path. Verificar que el deploy este activo.
29. Skill en 2 cables. Cable A arquitectura de programacion en Wordflow Code. Cable B sistema de despliegue del code.
30. Deploy 3 salidas. OUT1 UOOS parte 1 y 2 en el chat como .py o json ficha o yaml. OUT2 directo a repo destino de la cuenta indicada (docs o preguntar en chat cuenta+repo). Si no existe lo creas. OUT3 raiz organizada cuenta A + evidence.
31. Auditoria forense X-Ray de documentos que recibe Wordflow Code. Convertir documentos en code ejecutable EXTRACT_LITERAL. Luego consenso ask council 12 pasos. Si no existe se crea.
32. Tarea 3 poner skill en Metodo de trabajo AND Download code AND Desplegar AND Refactoria AND cable a Wordflow Code raiz de programacion.

## PREFLIGHT

```
FOR item in INPUT BLOCK 1..32: mark UNCHECKED
READ references/BATCH-COPY-MOVE-SAFETY.md
READ METODO_ZIP_COPY_DETERMINISTA
READ GUIA-DESPLIEGUE-ZIP-UNIVERSAL
READ PIPELINE/07 Enchufe Universal = Fables
READ PIPELINE/08 determinista + apply_push
READ PIPELINE/57 EXTRACT_LITERAL
READ GUIA_REGISTRO_PLUGINS
READ UOOS parte 1
READ UOOS parte 2
READ external_accounts.yaml
READ code_path_runner.py  # no rewrite
READ research-download-chain assets  # blob lock
TOKEN_REF in {env:Maxbry_123_tokens, env:EXTERNAL_GH_B_TOKEN, env:EXTERNAL_GH_C_TOKEN, env:HF_TOKEN, env:TARGET_REPO_TOKEN}
IF token matches ghp_ THEN FAIL
```

## FILE OPS GLOBAL — LUNA + AGENTE (OBLIGATORIO)

Antes de tocar archivos:

```
CLASSIFY operation in {COPY, MOVE_SAME_REPO, MOVE_CROSS_REPO, MIRROR, API_TRANSFER}
READ references/BATCH-COPY-MOVE-SAFETY.md
SET shell: set -euo pipefail
QUOTE every path
USE -- before pathname operands when supported
VALIDATE src is under SRC_ROOT
VALIDATE dst is under DST_ROOT
REJECT absolute dst, .. traversal, symlink escape
BUILD deterministic manifest src_rel -> dst_rel + type + size + sha256/symlink_target
IF destination exists:
  SAME hash/type -> SKIP_IDENTICAL
  DIFFERENT -> FAIL unless explicit OVERWRITE gate
NO delete source before destination verify
NO commit/push before manifest verify
NO LLM PASS
```

Metodo de copia se elige por necesidad; no usar siempre `cp` por costumbre:

```
A exact small queue/custom mapping -> Bash array + cp -- / cp -a --
B rule-selected files -> find -print0 + NUL-safe loop or find -exec
C recursive/many files -> rsync -a; first rsync -ain --checksum
D full local tree, rsync unavailable -> tar stream source/. -> target/
E partial repo -> actions/checkout sparse checkout, then A/B/C
F few remote text files -> GitHub Contents API serial PUT/GET verify/DELETE
```

Movimiento:

```
MOVE_SAME_REPO tracked -> git mv -- SRC DST; git diff --check
MOVE_LOCAL exact path -> mv -T -- SRC DST when supported
MOVE_CROSS_REPO -> COPY -> VERIFY -> COMMIT/PUSH DEST -> VERIFY REMOTE -> DELETE SOURCE -> COMMIT/PUSH SOURCE
API_TRANSFER move -> GET source SHA -> PUT dest -> GET+verify -> DELETE source serially
NEVER parallel create/update + delete for same API move
```

## PASO 1 — DOWNLOAD (GitHub Action)

```
REPOS = lista lock skill research-download-chain (20 slugs orden fijo)
RUN workflow research-download-chain-final.yml
CMD python3 scripts/research_download_chain.py 'Download code/archivos' '_work/research-download'
DEST Download code/archivos
MANIFEST Download code/archivos/RESEARCH_DOWNLOAD_MANIFEST.jsonl
GATE count status COMPLETE == 20
GATE zip bytes <= 17000000
GATE unzip -tq == 0
SKIP slug COMPLETE
FORBID rewrite packer, cambiar SPLIT_TARGET MAX_ZIP, add/remove repos
```

## PASO 2 — BANDEJA Download code / Download N

```
MKDIR Download code
MKDIR Download code/Download N     # N = 1|2|3 tarea en curso
SRC_ZIP = Download code/archivos/{slug}_{part}.zip
```

### OP1 — solo parte del code

```
SELECT paths
EXTRACT those paths only
COPY -> Download code/Download N/<path>
ROUTE usando skill de descarga todos los repo hacia Download N
NO rewrite bytes
```

### OP2 — repo / software / agente completo

```
IF software_completo OR agente_completo:
  CREATE raiz nueva en main
  OR fork y cablear
COPY tree completo SRC -> DEST_ROOT
```

### Verificacion cruzada (obligatoria OP1 y OP2)

```
COMPARE source_repo vs dest
MISSING -> FAIL
EXTRA unexpected -> FAIL
SHA_MISMATCH -> FAIL
```

## PASO 3 — EXTRACCION ZIP + FABLES + COPY

```
READ guia extraccion zip (agentes = TAREA-1 = YAIWES misma guia)
unzip -t ZIP
unzip -q ZIP -d .staging/<slug>
FILTER __MACOSX .DS_Store Thumbs.db path-traversal
FOR file:
  sha256(src)
  COPY to live_root using FILE OPS method A/B/C/D
  sha256(dst) == sha256(src) else FAIL
PLUGIN I/O obligatorio (Fables = Enchufe Universal v2 + ficha conexion)
  plugin_id, contrato, inputs[], outputs[], extension_point, estado
IF JSON or prompt DSL -> emit .py EXTRACT_LITERAL
IF reglas or skill -> .yaml
FORBID rewrite auto-fix regenerar
REPEAT same method remaining files
READ Desplegar/Desplegar 1 + UOOS 1 + UOOS 2 + ficha.v2 antes de plugin
```

## PASO 4 — GITHUB ACTION COPY / MOVE QUEUE

```yaml
# Batch Copy/Move (contrato Director)
# usar actions/checkout@v7 en workflows nuevos salvo pin SHA/politica superior
on: workflow_dispatch

# Checkout side-by-side: source y target en paths separados.
# Repo privado secundario requiere token propio con minimo permiso.
- uses: actions/checkout@v7
  with:
    path: source
    fetch-depth: 1

- uses: actions/checkout@v7
  with:
    repository: OWNER/TARGET_REPO
    token: ${{ secrets.TARGET_REPO_TOKEN }}
    path: target
    fetch-depth: 1
```

Contrato de ejecucion:

```
SRC_ROOT=source
DST_ROOT=target
READ references/BATCH-COPY-MOVE-SAFETY.md

# Seleccion de metodo
IF exact names <= small lote OR custom MAPPED paths:
  METHOD=A queue + cp -- / cp -a --
ELIF recursive tree OR many files:
  METHOD=C rsync
ELIF selected by find rule:
  METHOD=B find NUL-safe
ELIF full tree AND rsync unavailable:
  METHOD=D tar stream

# NO generar cola insegura con `for f in $(find ...)` ni `ls |`.
# Para nombres arbitrarios usar NUL delimiters.

MAP organico:
  project README pyproject -> raiz
  app code -> src/
  config -> config/
  tools -> scripts/
  tests -> tests/

PREVIEW / DRY RUN
  rsync method -> rsync -ain --checksum
  queue method -> print manifest src_rel -> dst_rel

COPY/MOVE
  quote every path
  mkdir -p destination parent
  reject path traversal
  preserve dotfiles
  preserve symlink as symlink unless policy explicitly dereferences
  collision different hash -> FAIL by default

VERIFY
  expected count == actual declared scope
  every regular file SHA256 matches
  symlink target/type matches
  unexpected extra -> FAIL in exact-scope operation
  git diff --check
  git status --short reviewed

working-directory target
git add .
IF diff --cached --quiet THEN no commit ELSE
  commit "Batch copy/move files from source repository"
git push
NO force

IF MOVE_CROSS_REPO:
  VERIFY destination commit remotely
  ONLY THEN delete source paths
  commit source deletion separately
  push source
  evidence records DEST_COMMIT_SHA + SOURCE_DELETE_COMMIT_SHA

TOKEN = dest secret
  A env:Maxbry_123_tokens
  B env:EXTERNAL_GH_B_TOKEN
  C env:EXTERNAL_GH_C_TOKEN
  alias env:TARGET_REPO_TOKEN si Director lo crea
GITHUB_TOKEN del workflow source NO se asume valido para repo privado distinto
NEVER print token
```

## PASO 5 — DESPLEGAR N ESTADO + ATOMIC WRITE

```
IN Desplegar/Desplegar 1 (lote docs runtime tambien Desplegar 2)
FOR each file in lote:
  ANALYZE architecture
NO modificar contenido interno para marcar estado
NOMBRE = estado:
  archivo.yaml            ORIGINAL / PROTEGIDO / pendiente
  process_archivo.yaml    COPIA EN PROCESAMIENTO
  done_archivo.yaml       PROCESADO Y VALIDADO
Emoji en filename es senal externa NO mecanismo de seguridad

IF Dee requiere reescribir:
  ORIGINAL READ-ONLY
  SHA256
  AI trabaja sobre COPIA / TEMP
  DIFF
  SYNTAX CHECK
  IF fail KEEP original
  ELSE ATOMIC RENAME
READ-BEFORE-WRITE + checksum
Probar que la version leida no cambio mientras se trabajaba
```

## PASO 6 — SISTEMA DESPLIEGUE DETERMINISTA

```
DOCS = Desplegar/Desplegar 1 + Desplegar 2 + PIPELINE/08
INCORPORAR metodo determinista de esos archivos
RUNTIME python + yaml
JSON solo ficha/contrato ya registrado
TAIL Wordflow Code:
  reception.convert -> goals -> planner -> code_path_runner
  -> loop_bridge -> evidence -> DEPLOY
VERIFY deploy engine activo al final del code path
DRY_RUN default
REAL iff GITHUB_DEPLOY_REAL=1
```

## PASO 7 — PROMPT CODE + ESTANDARES

```
LOAD prompt de code del lote Desplegar
LOAD PIPELINE ADVANCED_ENGINEERING_STANDARD
COPY estandares como REGLA dentro del prompt/runtime
EXTRACT_LITERAL gana sobre mejorar
```

## PASO 8 — ROUTER REPOS + TOKENS

```
REGISTRY
  SOURCE_01 SOURCE_02  read
  WORK_01              process
  DESTINATION_01       write

ACCOUNT A owner=maxbry123-commits  token=env:Maxbry_123_tokens
  repos disponibles Wordflow Code / agentes / TAREA-1 / YAIWES / frontend / etc
ACCOUNT B owner=abc1tienda-web     token=env:EXTERNAL_GH_B_TOKEN
ACCOUNT C owner=HOLD               token=env:EXTERNAL_GH_C_TOKEN
  STOP write C hasta username Director
ACCOUNT D process-only si docs lo declaran

SKILL -> Repository Router -> Repo Registry -> GitHub API/Git -> TOKEN
leer -> procesar -> validar -> escribir

CABLE A = arquitectura programacion Wordflow Code (no editar code_path_runner)
CABLE B = sistema despliegue apply_push
```

## 3 SALIDAS DEPLOY (obligatorias)

```
OUT1 chat
  emitir UOOS parte 1 y parte 2
  formato .py o yaml
  json solo si es ficha

OUT2 dest remoto
  owner+repo desde docs proyecto
  ELSE preguntar en chat cuenta y repo destino
  IF repo no existe CREATE luego apply_push

OUT3 cuenta A
  raiz organizada en maxbry123-commits/agentes
  + evidence.json
```

## X-RAY + COUNCIL12

```
Docs inbound -> extensions/audit_forensic
MD -> code EXTRACT_LITERAL PIPELINE/57
THEN ask council 12 pasos
  12 goals in -> council -> 12 goals out
NO council PASS -> NO deploy
IF council module missing CREATE in sandbox then register plugin
```

## DESTINOS COPIA SKILL (Tarea 3)

```
skills/wordflow-code-deploy-router/          canonical
Metodo de trabajo/wordflow-code-deploy-router/
Download code/wordflow-code-deploy-router/
Desplegar/wordflow-code-deploy-router/
Refactoria/wordflow-code-deploy-router/
Wordflow Code/Readme/Readme1/                parche cable only
```

## GATES

```
INPUT BLOCK 1..32 checked
FILE_OP_CLASS classified
FILE_OP_METHOD selected
PATH containment validated
COLLISION policy satisfied
EXPECTED_COUNT == ACTUAL_COUNT
SHA/type/symlink manifest match
MOVE never deletes source before verified destination
Cross-repo move verifies remote destination commit before source delete
GitHub Contents API create/update + delete serialized
EvidenceGate exit 0
LLM never prints PASS
```
