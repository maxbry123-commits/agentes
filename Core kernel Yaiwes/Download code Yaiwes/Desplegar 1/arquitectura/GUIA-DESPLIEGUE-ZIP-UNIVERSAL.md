# GUÍA UNIVERSAL — DESPLIEGUE DE SOFTWARE DESDE ZIP

**Versión:** 1.0  
**Uso:** agentes, motores, software, SDKs, aplicaciones y cualquier paquete entregado como ZIP.  
**Ubicación:** raíz principal del repositorio.  
**Regla de oro:** **ZIP → inventario → staging → extracción → verificación → raíz del software → auditoría → publicación.**

---

## 0. Propósito

Esta guía define un método reproducible para recibir un ZIP de cualquier software y convertirlo en una raíz organizada del repositorio sin perder archivos, mezclar software, sobrescribir una raíz protegida ni declarar una tarea terminada sin evidencia.

El método es genérico. Para un agente se usa:

```text
ROOTS/<agente>/
```

Para otro software se usa una raíz hermana:

```text
ROOTS/<software>/
```

Nunca se coloca un segundo software dentro de `ROOTS/openclaw/` ni se usa OpenClaw como plantilla de otro agente.

---

# 1. DAG / DSL MAESTRO

```text
ZIP_RECEIVED
    |
    v
SNAPSHOT_REPO
    |
    v
SOURCE_INVENTORY
    |
    +--> SOURCE_SHA256
    |
    +--> ZIP_INTEGRITY
    |
    v
IDENTIFY_SOFTWARE
    |
    v
CREATE_STAGING
    |
    v
EXTRACT_ZIP
    |
    v
EXTRACTED_MANIFEST
    |
    v
NORMALIZE_ROOT
    |
    +--> preserve relative paths
    +--> preserve symlinks
    +--> reject path traversal
    |
    v
BUILD_ROOTS/<software>
    |
    v
DEST_MANIFEST
    |
    v
CROSSCHECK_1_STRUCTURE
    |
    v
CROSSCHECK_2_CONTENT_SHA256
    |
    v
CROSSCHECK_3_OFFICIAL_UPSTREAM
    |
    v
CROSSCHECK_4_POST_PUBLISH_READBACK
    |
    v
MISSING / EXTRA / MODIFIED ?
   |             |
  YES            NO
   |              |
   v              v
FIX + RECHECK   PASS
                  |
                  v
REMOVE_TEMPORARIES
                  |
                  v
COMMIT
                  |
                  v
FINAL_XRAY_AUDIT
                  |
                  v
DONE
```

**No se salta un nodo crítico.** Si un nodo falla, el estado es `FAIL` o `BLOCKED`, se conserva evidencia y se repite desde la causa correspondiente.

Estados válidos:

```text
PLANNED | RUNNING | PASS | FAIL | BLOCKED | DONE
```

`DONE` exige evidencia de GitHub. Una intención, un YAML creado o una respuesta del agente no son evidencia de ejecución.

---

# 2. REGLA FUNDAMENTAL SOBRE EL ZIP

**Extraer un ZIP NO vacía el ZIP.**

Después de:

```bash
unzip -q software.zip -d .staging/software
```

el ZIP original sigue conteniendo sus archivos.

Por tanto existen dos operaciones independientes:

```text
EXTRACT_ZIP
      !=
DELETE_ZIP
```

El ZIP solo puede eliminarse si es un temporal y después de que la extracción y las verificaciones tengan estado `PASS`.

Si el ZIP es evidencia, fuente de auditoría o único respaldo, **se conserva**.

---

# 3. PASO 1 — IDENTIFICAR LA FUENTE

Registrar antes de extraer:

```text
source_name
source_url / origen
ref o versión, si existe
ZIP filename
ZIP size
ZIP SHA-256
fecha/hora de recepción
software esperado
raíz destino
```

Si procede de un repositorio oficial, registrar también:

```text
upstream_repository
canonical_ref
canonical_commit
```

**No sustituir silenciosamente un commit por `main`, un tag o una release distinta.** Si cambia la fuente, cambia la evidencia.

---

# 4. PASO 2 — INVENTARIO DEL ZIP

Sin modificar el ZIP:

```bash
unzip -Z1 software.zip > zip-manifest.txt
```

Integridad:

```bash
unzip -t software.zip
```

Hash del contenedor:

```bash
sha256sum software.zip
```

Inspeccionar nombres sospechosos antes de extraer:

```bash
unzip -Z1 software.zip | grep -E '(^/|\.\./|^\.git/)'
```

Si aparecen rutas absolutas, `../` o contenido Git no esperado, detener y revisar.

---

# 5. PASO 3 — STAGING AISLADO

Nunca extraer inicialmente sobre la raíz definitiva.

```bash
rm -rf .staging/software
mkdir -p .staging/software
unzip -q software.zip -d .staging/software
```

Inventario extraído:

```bash
find .staging/software -type f -print | sort > extracted-manifest.txt
```

Para incluir symlinks y directorios en una inspección completa:

```bash
find .staging/software -print | sort > extracted-tree.txt
```

Comparar cantidades como primera señal:

```bash
wc -l zip-manifest.txt extracted-manifest.txt
```

**El conteo por sí solo no demuestra equivalencia.**

---

# 6. PASO 4 — PRESERVAR LA ESTRUCTURA

Determinar si el ZIP contiene:

```text
software/
  package.json
  src/
```

o directamente:

```text
package.json
src/
```

El objetivo es producir:

```text
ROOTS/<software>/
  package.json
  src/
```

No crear accidentalmente:

```text
ROOTS/<software>/software/package.json
```

si esa carpeta superior solo era el contenedor del ZIP.

La decisión debe quedar registrada como `MAP_RELATIVE_PATHS`.

---

# 7. PASO 5 — CREAR LA RAÍZ DEL SOFTWARE

Arquitectura multi-software:

```text
ROOTS/
├── openclaw/
├── <agente-2>/
├── <agente-3>/
└── <otro-software>/
```

Cada software conserva su árbol independiente.

**No mezclar raíces.**

Para una publicación controlada desde staging:

```bash
mkdir -p ROOTS/<software>
rsync -a --exclude='.git/' .staging/software/ ROOTS/<software>/
```

**No utilizar `rsync --delete` sobre una raíz protegida.**

Antes de copiar una raíz que ya existe, crear snapshot y comprobar qué archivos cambiarían.

---

# 8. PASO 6 — MANIFEST Y HASH DEL DESTINO

Crear el manifest del destino:

```bash
find ROOTS/<software> -type f -print | sort > destination-manifest.txt
```

Hash de todos los archivos:

```bash
find ROOTS/<software> -type f -print0 | sort -z | xargs -0 sha256sum > destination-sha256.txt
```

Para archivos críticos, registrar individualmente:

```text
ruta
sha256
size
```

---

# 9. LAS 4 PASADAS DE VERIFICACIÓN

## PASADA 1 — ESTRUCTURA

Comparar:

```text
ZIP manifest
      ↕
EXTRACTED manifest
      ↕
DESTINATION manifest
```

Buscar:

```text
MISSING
EXTRA
RENAMED
DUPLICATED
WRONG_PATH
```

---

## PASADA 2 — CONTENIDO

Comparar SHA-256:

```text
SOURCE → STAGING → DESTINATION
```

Un mismo nombre no demuestra que el contenido sea igual.

Un mismo hash demuestra igualdad del contenido del archivo.

---

## PASADA 3 — ORIGEN OFICIAL

Cuando exista repositorio upstream:

```text
DESTINATION
     ↕
OFFICIAL REPOSITORY
     ↕
CANONICAL COMMIT / TAG / RELEASE
```

La fuente oficial tiene prioridad para decidir qué corresponde al software cuando el ZIP es una pieza de recuperación o distribución.

No se debe inventar que un archivo coincide con upstream sin haberlo comprobado.

---

## PASADA 4 — POST-PUBLICACIÓN

Después del commit:

```text
GitHub main
    ↓
READ-BACK
    ↓
MANIFEST
    ↓
SHA
    ↓
PRE/POST SNAPSHOT
```

Clasificar cualquier diferencia como:

```text
MISSING
EXTRA
MODIFIED
EXPECTED
UNEXPECTED
```

Solo después de esta pasada se puede marcar `DONE`.

---

# 10. ZIP EN LOTES

Cuando el software llegue dividido en varios ZIP:

```text
ZIP_01 ─┐
ZIP_02 ─┼─> GLOBAL_INVENTORY
ZIP_03 ─┘          |
                   v
                BATCH_i
                   |
             manifest + SHA
                   |
                   v
             MERGE_LÓGICO
                   |
                   v
              ROOTS/<software>
```

Cada lote debe registrar:

```text
batch_id
source_zip
file_count
sha256
paths
destination
status
```

**No asumir que dos ZIP con nombres diferentes son piezas diferentes.** Comparar contenido/hash para detectar duplicados.

Si dos ZIP son idénticos, conservar uno como fuente y marcar el otro como duplicado; eliminarlo solo después de la auditoría.

Si tienen solapamientos parciales, comparar archivo por archivo antes de fusionar.

---

# 11. ARCHIVOS DUPLICADOS

Nunca eliminar únicamente porque dos archivos tienen el mismo nombre.

Clasificación:

```text
SAME_PATH + SAME_HASH      → duplicado exacto
DIFFERENT_PATH + SAME_HASH → copia/duplicado de contenido
SAME_PATH + DIFFERENT_HASH → conflicto
```

Un conflicto requiere revisión. **No sobrescribir automáticamente.**

---

# 12. RAÍCES PROTEGIDAS

GitHub no hace una carpeta físicamente imborrable.

La protección correcta es:

```text
ROOTS/<agente>
   ↓
CODEOWNERS
   ↓
PR / branch protection
   ↓
CI guard
   ↓
manifest + SHA
   ↓
snapshot
   ↓
auditoría pre/post
```

Una limpieza general del repositorio **no debe tocar** una raíz de agente protegida sin:

```text
snapshot
+ manifest
+ autorización
+ comparación
+ auditoría
```

Si posteriormente se desea borrar una raíz protegida:

```text
UNLOCK_REQUEST
 → SNAPSHOT
 → MANIFEST
 → AUTORIZACIÓN
 → BORRADO
 → READ-BACK
 → XRAY
 → COMMIT
 → VOLVER A PROTEGER
```

---

# 13. LIMPIEZA DEL ZIP

Después de `PASS`:

```text
¿ZIP es evidencia?
 ├─ SÍ → conservar
 └─ NO
     ↓
¿Extracción completa?
 ├─ NO → conservar y corregir
 └─ SÍ
     ↓
¿Hashes correctos?
 ├─ NO → conservar y corregir
 └─ SÍ
     ↓
¿Read-back PASS?
 ├─ NO → conservar
 └─ SÍ → puede eliminarse como temporal
```

**Eliminar el ZIP no significa que "se vació". Significa que se eliminó el contenedor después de completar la extracción y verificación.**

---

# 14. QUÉ NO HACER

```text
NO subir el ZIP como sustituto de los archivos extraídos.
NO extraer directamente sobre una raíz protegida.
NO usar rsync --delete sobre una raíz protegida.
NO borrar por nombre sin comparar contenido.
NO mezclar dos agentes en una raíz.
NO sustituir un commit canónico por main sin registrarlo.
NO poner tokens en ZIP, JSON, payload, YAML o código.
NO marcar DONE porque el workflow existe.
NO marcar PASS sin evidencia.
NO afirmar que un archivo fue descargado si no existe el archivo real.
```

---

# 15. GITHUB: PUBLICACIÓN

La publicación debe producir un commit verificable:

```text
STAGING
  ↓
VALIDATE
  ↓
ROOTS/<software>
  ↓
GIT COMMIT
  ↓
GITHUB
  ↓
READ-BACK
```

Si se usa GitHub Actions, el workflow debe guardar manifests y resultados como artifacts cuando corresponda.

La existencia del workflow **no demuestra que la tarea se ejecutó**. La evidencia es el `run`, `job`, `artifact`, commit o lectura posterior correspondiente.

---

# 16. REGISTRO EN BITÁCORA

Por cada despliegue registrar:

```text
TASK_ID
software
source
source_ref
zip_size
zip_sha256
file_count_source
file_count_extracted
file_count_destination
destination_root
canonical_upstream
canonical_commit
batch_ids
missing
extra
modified
duplicate_files
verification_pass_1
verification_pass_2
verification_pass_3
verification_pass_4
commit_sha
readback_status
final_status
```

Estados:

```text
PLANNED
RUNNING
PASS
FAIL
BLOCKED
DONE
```

---

# 17. AUDITORÍA DE LAS NOTAS Y MÉTODO — 4 PASADAS

Esta guía consolida y cruza las reglas existentes en:

1. `BITACORA-ACR-XRAY.md` — método ZIP→ROOTS, staging, hashes, lotes, cuatro pasadas y regla anti-alucinación.
2. `PIPELINE-ACR-CONSOLIDATED.md` — DAG maestro, publicación, read-back, protección de raíces y checklist de cierre.
3. `ACR-RECOVERY-PATCH-ZIP.md` — fuente canónica, descarga oficial, extracción, symlinks, límites GitHub y evidencia.
4. `PIPELINE/08_DESPLIEGUE_APPLY_PUSH.md` del Wordflow Core — separación entre payload del agente y ejecución determinista del despliegue.

### Resultado del cruce

```text
PASADA A — extracción:
PASS → extraer no vacía el ZIP.

PASADA B — integridad:
PASS → inventario + SHA + manifest antes de publicar.

PASADA C — arquitectura:
PASS → ROOTS/<agente> son raíces hermanas y no deben mezclarse.

PASADA D — cierre:
PASS → read-back + XRAY + commit son necesarios antes de DONE.
```

Si alguna fuente futura contradice esta guía, **no se debe elegir por intuición**: registrar el conflicto, verificar el código/documentación de origen y actualizar la guía y la bitácora conjuntamente.

---

# 18. CHECKLIST OPERATIVO

```text
[ ] fuente identificada
[ ] ref/versión registrada
[ ] ZIP real disponible
[ ] tamaño registrado
[ ] SHA-256 registrado
[ ] ZIP integrity PASS
[ ] manifest fuente creado
[ ] staging aislado
[ ] extracción completada
[ ] manifest extraído
[ ] path mapping validado
[ ] symlinks revisados
[ ] ROOTS/<software> correcto
[ ] manifest destino
[ ] SHA destino
[ ] pasada 1 estructura PASS
[ ] pasada 2 contenido PASS
[ ] pasada 3 upstream PASS / N/A justificado
[ ] pasada 4 read-back PASS
[ ] MISSING = 0
[ ] EXTRA inesperados = 0
[ ] MODIFIED inesperados = 0
[ ] duplicados tratados
[ ] raíz protegida respetada
[ ] temporales eliminados solo después de PASS
[ ] commit SHA registrado
[ ] bitácora actualizada
[ ] XRAY final
[ ] DONE
```

---

# 19. REGLA DE CONTINUIDAD PARA GPT / GROK / OTROS AGENTES

Cuando otro agente reciba una tarea de despliegue:

```text
1. LEER esta guía.
2. LEER BITACORA-ACR-XRAY.md.
3. LEER PIPELINE-ACR-CONSOLIDATED.md.
4. TOMAR snapshot.
5. INVENTARIAR.
6. TRABAJAR EN STAGING.
7. VERIFICAR.
8. PUBLICAR.
9. LEER DE VUELTA DESDE GITHUB.
10. AUDITAR.
11. ACTUALIZAR BITÁCORA.
12. SOLO ENTONCES declarar DONE.
```

**Fuente de verdad operacional:** evidencia verificable del repositorio y del origen oficial. El contexto conversacional sirve como instrucción, no como evidencia.
