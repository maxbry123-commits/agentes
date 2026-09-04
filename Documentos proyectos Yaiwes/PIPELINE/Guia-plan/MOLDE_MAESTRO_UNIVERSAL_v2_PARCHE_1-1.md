# MOLDE_MAESTRO_UNIVERSAL_v2 — PARCHE 1 (solo lo que faltaba)

**No reescribe** `MOLDE_MAESTRO_UNIVERSAL_v2.md`. Es anexo aditivo.
Resultado de auditoría 5-pasadas: chat completo (10 documentos + diagnóstico CI) vs. el molde v2 ya construido.

---

## MÉTODO DE LA AUDITORÍA

```text
Pasada 1 — Requisitos explícitos del pedido original vs. molde v2   → completos, sin faltantes
Pasada 2 — Cada documento fuente (1–9) vs. molde v2, sección por sección
Pasada 3 — Consistencia interna del propio molde v2 (plantilla §13 vs. secciones 1–12)
Pasada 4 — Lecciones operativas surgidas en el chat (diagnóstico CI) vs. molde v2
Pasada 5 — Consolidación: qué falta es real (existe en fuente, no en molde) vs. qué es
           específico de un plan (HF, YAIWES) y no pertenece al molde universal
```

**Criterio de inclusión:** solo entra aquí lo que es genérico (aplica a cualquier plan) y estaba
en al menos una fuente ya indexada pero ausente del molde v2. Lo específico de HF (6 áreas,
ficha de modelo AI, contrato HF↔GitHub completo) se queda fuera por ser de un plan, no del molde.

---

## GAP 1 — Fichas y tablas instanciables que faltaban en la Plantilla (§13)

El molde v1 y el README YAIWES usaban estas tablas y el v2 las mencionó pero no las dejó
copiables. Van aquí completas:

### Ficha de cierre (por nodo/salida)
```text
SALIDA:
COMMIT:
READBACK:
ENLACE_GITHUB:
ERRORES:
TAG:
STATUS: PASS|FAIL|OPEN|BLOCKED
```

### Tabla ESTADO AUDITADO (por plan completo)
```text
| Salida | Estado | Checkpoint |
|---|---|---|
| S1 | | PIPELINE/checkpoints/{{PLAN_ID}}/S1.md |
| Sn | | PIPELINE/checkpoints/{{PLAN_ID}}/Sn.md |
```

### Tabla GAPS (registro vivo, no se borra al cerrar)
```text
| ID | Gap | Destino | Estado |
|---|---|---|---|
| G1 | | | OPEN|CLOSED |
```

### Tabla RAÍCES VIVAS (genérica, se llena por repo)
```text
| Raíz | Rol |
|---|---|
| Desplegar/ | Inbox del lote. No hardcodear N. |
| PIPELINE/ | Plan vivo + molde. |
| Método de trabajo/ | Reglas. Base no se reescribe. |
| Refactoria/ | Mesa: source/ viejo, new/ reescritura. |
| {{raíz_producto}}/ | Destino canónico del producto. |
| {{raíz_motor}}/ | Hot path / motor de ejecución. |
| notas-trabajo-{{colaborador}}/ | Solo estado de ese colaborador. No es fuente de verdad. |
```

---

## GAP 2 — Principios faltantes en §0 (Principios Fijos)

Estos 6 estaban en las fuentes (Guía Maestra, METODO_ZIP_COPY_DETERMINISTA,
GITHUB-ESTRUCTURA-DESTINOS) y no quedaron en el molde v2:

```text
11. Nombres funcionales, no de producto ni marca: los nodos del árbol describen
    función operativa, nunca nombre comercial ni de agente.

12. COPY-FIRST / REUSE-FIRST, jerarquía obligatoria y en este orden exacto:
    COPY / MOVE / REUSE  →  LINK / CONNECT  →  PATCH  →  ADAPT  →  GENERATE LAST.
    Generar código desde cero es el ÚLTIMO recurso, no el primero.

13. Ningún secreto/credencial en texto plano: nunca en logs, checkpoints,
    wire_trace, ZIP, JSON, YAML ni código. Token siempre por referencia
    (`secret://...` / `env:...`), nunca PAT en claro.

14. Sin force-push. Usar `expected_head` cuando exista, para detectar
    condiciones de carrera antes de escribir sobre `main`.

15. Código simulado o de relleno se marca explícitamente `FAKE` o
    `fusion:false` en el archivo/registro correspondiente. Nunca se deja
    ambiguo si algo es implementación real o placeholder.

16. Autorización del Director: crear un archivo nuevo, o integrar código
    diseñado en una fase de "diseño" (no auditoría automática), requiere
    aprobación humana explícita — el Guardián valida evidencia técnica,
    pero no sustituye esta aprobación.
```

---

## GAP 3 — Protocolo de extracción segura (falta dentro de §11 Despliegue)

De la Guía ZIP universal, ausente en el molde v2:

```text
Antes de copiar el contenido extraído al destino:
1. Preservar rutas relativas exactas del ZIP/fuente.
2. Preservar symlinks tal cual (no resolverlos ni duplicarlos).
3. Rechazar cualquier entrada con path traversal (`../`) o ruta absoluta (`^/`).
4. Decidir y registrar MAP_RELATIVE_PATHS: si el ZIP trae una carpeta
   contenedora de más (ej. `software/package.json`), no crear
   `destino/software/package.json` por accidente — el contenedor del ZIP
   no es parte de la estructura final salvo que corresponda.
```

Inspección previa obligatoria:
```bash
unzip -Z1 archivo.zip | grep -E '(^/|\.\./|^\.git/)'
```
Si aparece algo sospechoso → detener y revisar antes de extraer.

---

## GAP 4 — Lotes ZIP múltiples (falta dentro de §11 Despliegue)

Cuando el lote llega en más de un ZIP (ausente del molde v2):

```text
ZIP_01 ─┐
ZIP_02 ─┼─> INVENTARIO GLOBAL → por lote: manifest + sha256 → MERGE_LÓGICO → destino
ZIP_03 ─┘

Reglas:
- No asumir que dos ZIP con nombre distinto son contenido distinto — comparar hash.
- Si dos ZIP son idénticos: conservar uno como fuente, marcar el otro duplicado,
  eliminar solo después de auditoría.
- Si hay solapamiento parcial: comparar archivo por archivo antes de fusionar.
- Cada lote registra: batch_id, source_zip, file_count, sha256, paths, destino, status.
```

---

## GAP 5 — Borrado de duplicados fail-closed (falta como protocolo explícito)

De GITHUB-ESTRUCTURA-DESTINOS, aplica tanto a Despliegue como a Refactoria y no
estaba en el molde v2 como secuencia obligatoria:

```text
1. Localizar duplicados por ruta y/o hash.
2. Identificar cuál es el canónico por su ruta oficial (nunca por intuición).
3. Borrar SOLO el path duplicado, nunca el canónico.
4. Verificar que el duplicado desaparece (404 / missing confirmado).
5. Verificar que el canónico sigue existiendo intacto.
6. Registrar commit_sha + paths + resultado.

Si no se puede determinar cuál es el canónico → HOLD.
Si el path está protegido → HOLD (ver GAP 6).
```

---

## GAP 6 — Raíces protegidas: protocolo de desbloqueo (ausente del molde v2)

De la Guía ZIP universal:

```text
Protección de una raíz (agente/producto):
ROOTS/<x> → CODEOWNERS → PR/branch protection → CI guard → manifest+SHA →
snapshot → auditoría pre/post

Si hay que tocar una raíz protegida, el ÚNICO flujo válido es:
UNLOCK_REQUEST → SNAPSHOT → MANIFEST → AUTORIZACIÓN (Director) → BORRADO/CAMBIO
→ READ-BACK → X-RAY → COMMIT → VOLVER A PROTEGER

Una limpieza general del repo nunca toca una raíz protegida sin este flujo completo.
```

---

## GAP 7 — Limpieza del ZIP: árbol de decisión (ausente del molde v2)

De la Guía ZIP universal — regla exacta para saber cuándo se puede borrar el
ZIP temporal (el molde v2 solo decía "conservar o eliminar según regla" sin el árbol):

```text
¿El ZIP es evidencia (única fuente, auditoría, respaldo)?
 ├─ SÍ → conservar, no eliminar nunca.
 └─ NO
     ↓
   ¿La extracción está completa?
    ├─ NO → conservar y corregir.
    └─ SÍ
        ↓
      ¿Los hashes (fuente vs. destino) coinciden?
       ├─ NO → conservar y corregir.
       └─ SÍ
           ↓
         ¿El read-back post-commit dio PASS?
          ├─ NO → conservar.
          └─ SÍ → recién aquí puede eliminarse como temporal.
```

---

## GAP 8 — Trazabilidad y licencia de fuente externa (ausente del molde v2)

El molde v2 exige REUSE-FIRST (GAP 2, punto 12) pero no exigía registrar licencia.
Sin esto, "reusar" código OSS de terceros queda sin control legal ni de origen.
Nuevo campo obligatorio cuando la fuente de un nodo/Refactoria es OSS externo:

```yaml
fuente_externa:
  source_repo: ""
  source_ref: ""              # branch/tag/commit — nunca sustituir silenciosamente por main
  source_commit: ""
  source_license: ""          # UNKNOWN si no se verificó — nunca inventar
  source_zip_sha256: ""       # si llegó como ZIP
```

Regla: un nodo no puede declarar `PASS` de integración de código externo sin
`source_license` verificado o explícitamente `UNKNOWN` + `HOLD`.

---

## GAP 9 — Gate de tamaño / LFS antes de elegir método de copia (ausente del molde v2)

De TAREA-GITHUB-FINAL v1.2, aplica a cualquier copia de archivo grande:

```text
CHECK SIZE
 ↓
<= límite del método elegido (Contents API, etc.) → usar esa API
 ↓
> límite → usar Git Data API / ZIP / runner según corresponda
 ↓
si ninguna ruta es viable → HOLD + solicitar ZIP completo al Director

No usar Git LFS si el plan lo prohíbe. No inventar un límite operativo:
verificar la restricción real del método antes de asumirla.
```

---

## GAP 10 — Verificación de que el CI realmente corrió (lección de este mismo chat, ausente del molde v2)

Esto no vino de un documento sino del diagnóstico real hecho en esta conversación
(`workflow_runs: []` para un commit). El molde v2 exige "commit + read-back" como
evidencia, pero no cubre el caso de que el commit exista y el CI **nunca se haya disparado**.
Se agrega como paso obligatorio dentro del Guardián (§4) y del X-Ray (§7):

```text
Antes de aceptar un commit como evidencia de que un test/gate corrió:

1. Verificar que existe un run real para ese SHA exacto (no asumir por push).
2. Si `workflow_runs` está vacío para ese SHA, diagnosticar antes de reintentar:
   a. ¿El autor del commit es un bot/Action con GITHUB_TOKEN del propio repo?
      → protección anti-loop de GitHub: ese push NO dispara CI por diseño.
      Solución: commit vacío hecho por autor humano, o PAT distinto — nunca
      reintentar el mismo push esperando otro resultado.
   b. ¿El workflow solo tiene `workflow_dispatch` (sin `push:`)?
      → no hay run automático posible; disparar manualmente.
   c. ¿Hubo una interrupción real de la plataforma CI en la ventana de ese commit?
      → verificar fecha/hora contra el historial de incidentes antes de asumir
      que el evento se perdió sin razón.
3. Los artifacts de un run expiran por política de retención — un run_id viejo
   puede no ser recuperable. No se reutiliza evidencia caducada como si
   siguiera siendo válida; se genera un run nuevo y se referencia ese.
```

---

## RESUMEN — QUÉ SE AGREGA Y DÓNDE ENCAJA EN v2

```text
GAP 1  → extiende §13 (Plantilla)              — tablas/fichas copiables
GAP 2  → extiende §0 (Principios)              — 6 principios nuevos (11–16)
GAP 3  → extiende §11 (Despliegue)             — extracción segura
GAP 4  → extiende §11 (Despliegue)             — lotes múltiples
GAP 5  → nuevo protocolo, referenciado desde §11 y §12
GAP 6  → nuevo protocolo, referenciado desde §11
GAP 7  → extiende §11 (Despliegue)             — árbol de decisión limpieza ZIP
GAP 8  → extiende §12 (Refactoria)             — licencia de fuente externa
GAP 9  → nuevo gate, referenciado desde §4 (Sheriff preflight)
GAP 10 → extiende §4 (Guardián) y §7 (X-Ray)   — verificación de CI real
```

**No se declaran nuevos GAP fuera de estos 10** — la auditoría de 5 pasadas no encontró
más divergencias entre lo pedido/recibido en el chat y lo construido en el molde v2.
