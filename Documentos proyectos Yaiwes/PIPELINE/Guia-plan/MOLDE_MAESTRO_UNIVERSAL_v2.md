# MOLDE MAESTRO UNIVERSAL v2.0 — PLANTILLA + GUÍA DE INSTRUCCIONES

**Repo:** `maxbry123-commits/agentes` · **rama:** `main`
**Basado en auditoría 5-pasadas de:** Molde Universal v1, PLAN_YAIWES_AGENTE_WORDFLOW (S1–S12, funcionó bien), PIPELINE-HUGGINGFACE (Salidas 1–10, funcionó bien), Guía ZIP, METODO_ZIP_COPY_DETERMINISTA, GITHUB-ESTRUCTURA-DESTINOS, TAREA-GITHUB-FINAL v1.2 + addendum, Guía Maestra de Distribución.
**GitHub = única verdad. FAIL-CLOSED. LLM no declara PASS. HTTP 200 ≠ PASS.**

Este documento es dos cosas a la vez:
1. **Guía** — explica qué es cada pieza y por qué existe.
2. **Plantilla** — cada bloque `{{VARIABLE}}` se llena al instanciar un plan real en `PIPELINE/PLAN_{{PLAN_ID}}.md`.

---

## ÍNDICE

0. Principios fijos
1. INPUT BLOCK (instanciable)
2. DSL / DAG maestro del plan
3. Schema obligatorio por nodo
4. Roles de control: Sheriff · Guardián · Watchdog · Verdict Authority
5. GOAL IN → GOAL OUT en 12 pasos
6. Consejo de cierre — 12-ask council
7. Auditoría forense X-Ray (fin de cada segmento)
8. Sistema LOOP / NO-STOP / resolución de fallos (10 formas)
9. Checkpoint y parche de recuperación (recuperable en chat y por archivo)
10. Anexo de plugins de extensión (estructura de carpetas)
11. DESPLIEGUE — qué es y cómo funciona (ejemplo 19 documentos)
12. REFACTORIA — qué es y cómo funciona (con plugin de conexión)
13. Plantilla completa instanciable (copiar y llenar)
14. Checklist de cierre final

---

## 0. PRINCIPIOS FIJOS

```text
1. GitHub = única verdad. Una intención, un YAML creado, o una respuesta del LLM no son evidencia.
2. 1 tarea = 1 salida. No mezclar clases de trabajo ni lotes distintos.
3. PASS solo con evidencia verificable (hash, commit, read-back, test real).
4. FAIL-CLOSED: ante duda, HOLD. Nunca inventar para avanzar.
5. Regla de lego: nada se duplica, todo se referencia. Un módulo compartido vive en un solo lugar.
6. Monolito/hot path intocable hasta paridad de tests demostrada.
7. Microkernel/Plugin Architecture: el núcleo consulta un registro; capacidad nueva = fila nueva,
   nunca edición del núcleo. (wordflow/abi.py → ExtensionABI es la implementación real).
8. Anotar = aditivo. Nunca se reescribe un archivo base: se crea un archivo nuevo / parche.
9. NO-STOP: un GAP no detiene el plan. Se diagnostica, se resuelve, se registra, se continúa.
10. Todo hallazgo se etiqueta: CHAT_APROBADO | PIPELINE_EXISTENTE | INVESTIGACION_NUEVA | GAP | DESCARTADO.
```

---

## 1. INPUT BLOCK (instanciable)

Todo plan nace de este bloque. Sin esto no hay plan — es el `goal_in` de nivel plan completo.

```text
PLAN_ID:            {{PLAN_ID}}
AGENTE:              {{AGENTE}}
TAREA:               {{TAREA}}
OBJETIVO:            {{OBJETIVO}}
FUENTE:              {{FUENTE}}                 ← docs, ZIP, repo, chat aprobado
DESTINOS:            {{DESTINOS}}                ← raíces vivas donde puede escribir
ALCANCE:             {{ALCANCE}}
FUERA_DE_ALCANCE:    {{FUERA}}
CRITERIO_PASS:       {{PASS}}
CRITERIO_100%:       {{CIERRE}}
N_DESPLEGAR:         {{N}}                       ← WAIT si no hay lote. No crear carpeta vacía.
HOT_PATH_SE_TOCA:    {{SI_NO}}                   ← si SI: paridad de tests obligatoria
```

**Regla:** sin `N_DESPLEGAR` resuelto (o `WAIT` explícito), no se abre `Desplegar/Desplegar N/`.

---

## 2. DSL / DAG MAESTRO DEL PLAN

Todo plan sigue este DAG fijo, sin saltar nodos:

```text
INPUT_BLOCK
    |
    v
BIND (fuentes canónicas + raíces vivas + molde)
    |
    v
SHERIFF_PREFLIGHT ──(FAIL)──> HOLD + registrar
    |(PASS)
    v
LOOP POR SEGMENTO (S1..Sn):
    |
    v
  GOAL_IN (declarado, ver sección 5)
    |
    v
  EJECUCIÓN DEL NODO (según su propio schema, sección 3)
    |
    v
  VERIFICACIÓN CRUZADA ×3 (diff / tests / checklist)
    |
    v
  GUARDIAN_GATE ──(FAIL/GAP)──> LOOP NO-STOP (sección 8) ──> vuelve a EJECUCIÓN
    |(PASS)
    v
  X-RAY DE SEGMENTO (sección 7)
    |
    v
  CHECKPOINT + FICHA (sección 9)
    |
    v
  GOAL_OUT (con evidencia)
    |
    v
  ¿queda segmento siguiente? → SI: siguiente Sn / NO: continúa
    |
    v
CONSEJO DE CIERRE — 12-ASK (sección 6)
    |
    v
VEREDICTO FINAL (PASS | FAIL | BLOCKED)
    |
    v
DONE (solo con evidencia GitHub)
```

Estados válidos en todo el sistema: `PLANNED | RUNNING | PASS | FAIL | BLOCKED | GAP | DONE`.

---

## 3. SCHEMA OBLIGATORIO POR NODO

Cada nodo/segmento del plan debe declararse con este schema exacto antes de ejecutarse:

```yaml
id: S{{n}}
objetivo: ""
goal_in: ""
goal_out_esperado: ""
enlace_desplegar: Desplegar/Desplegar {{N}}/
enlace_refactoria: Refactoria/refactoria-plan-{{PLAN_ID}}/
destino_canonico: ""
tag: CHAT_APROBADO | PIPELINE_EXISTENTE | INVESTIGACION_NUEVA | GAP | DESCARTADO
sheriff: extensions/wordflow/standards/sheriff.py
guardian: mount-guard + VerdictAuthority
watchdog: extensions/wordflow/engine/watchdog.py
verificacion_cruzada: [diff, tests, checklist]
hot_path_afectado: true|false
paridad_tests: PASS|FAIL|N/A
plugin_asociado: plugins-extension/plugin-S{{n}}.yaml | N/A
checkpoint: PIPELINE/checkpoints/{{PLAN_ID}}/S{{n}}.md
estado: PLANNED
```

Ningún nodo se ejecuta sin este bloque completo. Un campo vacío o `UNKNOWN` sin resolver = `HOLD`.

---

## 4. ROLES DE CONTROL

### Sheriff — `extensions/wordflow/standards/sheriff.py`
Se ejecuta **antes** de cada nodo (preflight). Verifica reglas estáticas:
```text
1. rama = main
2. plan + checklist existen
3. enlace resuelto o WAIT (no carpeta vacía)
4. hot path identificado y con plan de paridad si se toca
5. alcance del nodo dentro del ALCANCE del plan
6. evidencia previa disponible (no hay PASS colgante sin ficha)
```
Si el Sheriff falla → el nodo ni se abre.

### Guardián — `mount-guard + VerdictAuthority`
Se ejecuta **al cerrar** el nodo. Es el gate de PASS. No permite:
```text
- PASS sin las 3 verificaciones cruzadas
- PASS sin checkpoint escrito
- PASS con hot path tocado sin paridad
- PASS por autodeclaración del LLM sin evidencia real
```

### Watchdog — `extensions/wordflow/engine/watchdog.py`
Corre **durante** la ejecución. Detecta:
```text
- loops infinitos sin avance real (mismo GAP repetido N veces sin nueva evidencia)
- edición directa de hot path sin pasar por Refactoria
- archivos creados fuera de raíces vivas
- tiempo/lote mezclado (dos N_DESPLEGAR distintos en un mismo nodo)
```
Si el Watchdog dispara → el nodo pasa a `BLOCKED`, no a `FAIL` silencioso.

---

## 5. GOAL IN → GOAL OUT EN 12 PASOS

Operador canónico de cada nodo (reconcilia el operador de 13 pasos del molde v1 y el de 15 pasos de HF en una secuencia única):

```text
1. RECIBIR       — goal_in registrado literal, sin interpretar
2. LEER          — fuentes canónicas del nodo (no asumir contenido)
3. PLANIFICAR    — DAG local del nodo + schema (sección 3) completo
4. COMPROBAR     — Sheriff preflight (sección 4)
5. PREPARAR      — staging aislado (source/ congelado si aplica Refactoria)
6. EJECUTAR      — la acción real (escribir, mover, investigar, copiar)
7. REGISTRAR     — SHA / commit / ID de la acción
8. MONITOREAR    — esperar resultado real, no asumir 200/202 = terminado
9. DIAGNOSTICAR  — si hay GAP/FAIL, clasificar causa
10. RESOLVER     — LOOP de 10 formas (sección 8), sin salir del nodo
11. VALIDAR      — verificación cruzada ×3 + Guardián
12. CERRAR       — ficha + checkpoint + goal_out con evidencia
```

`goal_out` solo se declara cumplido si el paso 12 tiene evidencia GitHub adjunta.

---

## 6. CONSEJO DE CIERRE — 12-ASK COUNCIL

Antes del veredicto final del **plan completo** (no de cada nodo), se responde este cuestionario. Puede ser multi-AI (Claude + GPT + Grok) o un solo agente actuando como consejo, pero las 12 preguntas son obligatorias y deben responderse con evidencia, no con opinión:

```text
1.  ¿El goal_in original se cumplió literalmente, sin reinterpretarlo a mitad de camino?
2.  ¿Existe evidencia verificable en GitHub (commit + read-back) para cada nodo cerrado?
3.  ¿Se tocó el hot path? Si sí, ¿la paridad de tests quedó documentada?
4.  ¿Algún módulo lego (goal_lock, cognitive_loop, evidence_packet, etc.) se duplicó en vez de referenciarse?
5.  ¿Se inventó algún path, commit, hash, resultado o número no verificado?
6.  ¿Las 3 verificaciones cruzadas (diff / tests / checklist) están documentadas por cada Refactoria?
7.  ¿El checkpoint permite recuperar la tarea al 100% en un chat nuevo, sin contexto previo?
8.  ¿Quedaron ZIP/temporales sin limpiar fuera de lo permitido por la guía de despliegue?
9.  ¿Cada hallazgo tiene su tag correcto (CHAT_APROBADO / PIPELINE_EXISTENTE / INVESTIGACION_NUEVA / GAP / DESCARTADO)?
10. ¿Algún GAP quedó abierto sin diagnóstico + plan de resolución + próximo paso?
11. ¿Cada archivo nuevo de Refactoria tiene su plugin de extensión anotado y listo para conectar?
12. ¿El veredicto final está firmado por Sheriff + Guardián + Watchdog, o es solo autodeclaración del LLM?
```

Si cualquiera de las 12 falla → el plan no cierra `DONE`, vuelve a `RUNNING` sobre el nodo responsable.

---

## 7. AUDITORÍA FORENSE X-RAY (fin de cada segmento)

Al cerrar cada segmento Sn (no solo al final del plan), correr esta X-Ray de 14 puntos:

```text
[ ] Fuente del segmento identificada y verificable
[ ] Manifest (path + sha256) generado antes de mover cualquier archivo
[ ] Duplicados clasificados: SAME_PATH+SAME_HASH / DIFFERENT_PATH+SAME_HASH / SAME_PATH+DIFFERENT_HASH
[ ] Hot path: tocado = NO, o tocado = SI con paridad PASS
[ ] Regla de lego respetada (sin duplicar módulos compartidos)
[ ] Verificación cruzada ×3 completa y con evidencia
[ ] Checkpoint escrito y recuperable (sección 9)
[ ] Plugin de extensión anotado si el nodo generó/reescribió un archivo
[ ] Ningún archivo se creó fuera de las raíces vivas del plan
[ ] Ningún temporal/ZIP quedó sin resolver (conservado o eliminado según regla)
[ ] Commit sin force-push, con read-back confirmado
[ ] GAP registrados con diagnóstico + solución aplicada, no solo listados
[ ] Ningún dato UNKNOWN se convirtió en dato afirmado sin verificar
[ ] Ficha de cierre del segmento completa (sección 13)
```

Este X-Ray es el mismo espíritu de las "4 pasadas" de la guía ZIP y los "12 goals" de Fase 2 — unificado aquí para no repetir auditorías distintas por documento.

---

## 8. SISTEMA LOOP / NO-STOP / RESOLUCIÓN DE FALLOS

Si un nodo no pasa el Guardián (FAIL o GAP), **no se escala ni se detiene el plan**. Se ejecuta este loop dentro del mismo nodo:

```text
NODO FAIL/GAP
    |
    v
DIAGNOSTICAR causa exacta (no genérica)
    |
    v
BUSCAR 10 FORMAS DE SOLUCIONARLO (obligatorio, en este orden):
    1. Documentación oficial del componente/repo (README, docs)
    2. Issues cerrados del repo oficial (mismo error/patrón)
    3. Discussions / Wiki del repo oficial
    4. Stack Overflow (búsqueda específica del error)
    5. Foros/comunidad del framework (Reddit, Discord vía búsqueda web, blogs técnicos)
    6. CHANGELOG / release notes — ¿hubo breaking change?
    7. PRs abiertos o recientes relacionados con el mismo síntoma
    8. Otros proyectos que usan la misma librería/patrón — cómo lo resolvieron
    9. Comparar contra el ejemplo oficial / quickstart del proyecto
    10. Consultar a otro colaborador AI (GPT/Grok/Fable) con el mismo INPUT BLOCK y comparar diagnóstico
    |
    v
APLICAR la solución más verificable (no la primera, la más evidenciada)
    |
    v
RE-EJECUTAR el nodo desde el paso 6 del operador (sección 5)
    |
    v
¿PASS?  → SI: continuar DAG normal
        → NO: registrar intento + causa + qué se descartó → repetir loop
    |
    v
Watchdog corta el loop SOLO si detecta que se repite el mismo GAP sin ninguna
solución nueva probada (evidencia de estancamiento real) → pasa a BLOCKED,
nunca se declara FAIL silencioso ni se salta el nodo.
```

**No se escala fuera del nodo** hasta que: (a) hay PASS real, o (b) Watchdog certifica estancamiento y lo marca `BLOCKED` para decisión del Director — nunca decidido por el LLM solo.

---

## 9. CHECKPOINT Y PARCHE DE RECUPERACIÓN

Requisito: la tarea debe poder retomarse **al 100%** en un chat nuevo (pegando el checkpoint) o desde el archivo guardado en el repo — sin ambigüedad, nivel ingeniería SaaS.

### Schema del checkpoint (obligatorio, sin campos libres sueltos)

```yaml
checkpoint:
  plan_id: {{PLAN_ID}}
  segmento: S{{n}}
  nodo: ""
  timestamp_utc: ""
  goal_in: ""
  goal_out_esperado: ""
  estado: RUNNING|PASS|FAIL|BLOCKED|GAP
  archivos_tocados:
    - path: ""
      sha256_antes: ""
      sha256_despues: ""
  commit_sha: ""
  intentos_realizados: N
  soluciones_probadas:
    - metodo: "1..10 (ver sección 8)"
      resultado: descartado|aplicado_parcial|aplicado
  ultima_accion_confirmada: ""
  siguiente_accion_planeada: ""
  contexto_para_reanudar: |
    <resumen literal del estado exacto — qué se hizo, qué falta,
     qué archivo se estaba editando, qué verificación falta —
     escrito para que otro chat/agente lo retome sin preguntar nada más>
  evidencia:
    - tipo: commit|read-back|test|hash
      referencia: ""
  firmado_por: sheriff|guardian|watchdog
```

### Reglas de recuperación
```text
- El checkpoint se guarda en DOS lugares: PIPELINE/checkpoints/{{PLAN_ID}}/S{{n}}.md
  y como copia dentro del plugin de extensión del plan (sección 10).
- Nunca se sobrescribe un checkpoint anterior: cada intento crea checkpoint-N nuevo.
- Un checkpoint sin "contexto_para_reanudar" completo no es válido — es evidencia
  incompleta y el Guardián debe rechazarlo.
- Para retomar en un chat nuevo: se pega el YAML completo del último checkpoint
  como primer mensaje. Eso reemplaza cualquier explicación adicional.
```

---

## 10. ANEXO DE PLUGINS DE EXTENSIÓN (estructura de carpetas)

Todo plan lleva un anexo físico donde viven los checkpoints y los plugins de conexión — no se mezclan con el cuerpo del plan.

### Checkpoints del plan

```text
📂 Plan X/
└── 📂 checkpoint/
    ├── 📄 checkpoint-1.yaml
    ├── 📄 checkpoint-2.yaml
    └── 📄 checkpoint-3.yaml
```

### Plugins de extensión (registro de enchufes, no el código del núcleo)

```text
📂 Plan X/
└── 📂 plugins-extension/
    └── 📄 plugin-S{{n}}.yaml     ← declara: capability_registration, destino canónico,
                                     ficha v2, autoridad lego, fusion:true|false
```

### Refactoria (mismo principio, aplicado a cada archivo reescrito)

```text
📂 Refactoria/refactoria-plan-x-N/
├── 📂 archivo-para-refactoria-x.py/
│   ├── 📄 source/x.py              ← copia exacta, congelada, NUNCA se edita
│   ├── 📄 new/x.py                 ← reescritura real, hecha en loop hasta acceptance
│   ├── 📄 plugin/x.plugin.yaml     ← enchufe listo para conectar (contrato + autoridad)
│   └── 📂 verificacion/
│       ├── 📄 diff.md
│       ├── 📄 tests.md
│       └── 📄 checklist.md
└── 📂 archivo-para-refactoria-ABC.yaml/
    ├── 📄 source/ABC.yaml
    ├── 📄 new/ABC.yaml
    ├── 📄 plugin/ABC.plugin.yaml
    └── 📂 verificacion/
```

**Por qué existe el `plugin/`:** el archivo `new/` nunca se vuelve a editar directamente en el futuro. Cualquier cambio posterior se hace registrando una fila nueva en el plugin (capability_registration), igual que el núcleo microkernel: se extiende, no se reescribe.

---

## 11. DESPLIEGUE — QUÉ ES Y CÓMO FUNCIONA

**Despliegue = inbox del lote + fuente de verdad temporal para verificación cruzada.**
No es destino final. No es Wordflow. No es Refactoria.

### Ejemplo concreto (19 documentos)

```text
1. El Director sube 19 documentos (.md y/o .py/.yaml) a:
   Desplegar/Desplegar N/
   (N = número de plan; nunca mezclar con otro N)

2. Si viene como ZIP:
   HASH del ZIP → EXTRAER a staging (el ZIP no se vacía) → INVENTARIO (19 archivos, cada uno con sha256)

3. FASE 1 — Inventario y lectura literal:
   Cada uno de los 19 archivos se lee completo, sin resumir, y se clasifica:
   - ¿ya existe igual en el code vivo? → PIPELINE_EXISTENTE, no se toca
   - ¿es nuevo y no pisa nada? → se mueve intacto al destino canónico
   - ¿pisa un archivo vivo? → se deriva a Refactoria (sección 12)
   - ¿falta información para decidir? → GAP, se registra y sigue el loop (sección 8)

4. FASE 2 — X-Ray cruzado (12 goals, ver documento Fase 2):
   Compara los 19 documentos contra el code vivo del Wordflow:
   qué está en Desplegar y no en el code, qué está en el code y no en Desplegar,
   qué está incompleto, qué rompe, qué bloquea, qué falta, hot path ¿se toca?

5. Cada archivo de los 19 termina en uno de tres caminos:
   a) Destino canónico directo (no requiere reescritura)
   b) Refactoria (requiere reescritura porque pisa un archivo vivo)
   c) GAP registrado (no se puede resolver todavía — falta dato/fuente)

6. Ningún archivo de los 19 puede declararse "integrado" sin manifest + hash +
   verificación cruzada + checkpoint.
```

**Regla de oro:** Despliegue es donde se **descubre** qué falta entre documentación y código real — no es donde se decide arbitrariamente qué hacer con cada archivo. Esa decisión sale de la X-Ray, no de la intuición del agente.

---

## 12. REFACTORIA — QUÉ ES Y CÓMO FUNCIONA

**Refactoria = mesa de trabajo para todo archivo que necesita reescribirse porque pisa uno vivo.**
Nunca se edita el archivo vivo directamente.

```text
Paso 1 — AISLAR
  Copiar el archivo vivo, exacto, sin tocar, a:
  Refactoria/refactoria-plan-x-N/archivo-.../source/

Paso 2 — IMPLEMENTAR (loop)
  Escribir la versión nueva en new/, usando source/ como referencia permanente
  (para entender contratos, imports críticos, comportamiento esperado).
  Se itera en loop (sección 8) hasta cumplir acceptance: mismos contratos,
  mismos tests, sin pérdida de API pública.

Paso 3 — PLUGIN DE CONEXIÓN
  El archivo nuevo (new/) se acompaña siempre de un plugin/*.plugin.yaml que
  declara cómo se enchufa al registro del núcleo — para que en el futuro
  cualquier extensión sea una fila nueva en ese plugin, nunca una edición
  directa de new/.

Paso 4 — VERIFICACIÓN CRUZADA ×3
  1. diff.md      → source/ vs new/ (APIs, imports, comportamiento)
  2. tests.md     → tests corridos contra new/
  3. checklist.md → checklist del gap/task + evidencia

Paso 5 — INTEGRACIÓN
  Solo si las 3 pasadas son PASS: new/ se copia al destino canónico del PASO3.
  source/ NUNCA se borra en el mismo task (queda como evidencia).
  Borrar el archivo vivo original solo con autorización del Director +
  las 3 verificaciones documentadas.
```

**Para qué sirve el archivo `source/`:** es la referencia de lectura para escribir el nuevo — nunca se edita, solo se lee. El archivo `new/` es el que se escribe desde cero usando `source/` como espejo de verdad, y siempre lleva su plugin de extensión listo para conectar antes de integrarse al destino final.

---

## 13. PLANTILLA COMPLETA INSTANCIABLE (copiar y llenar)

```markdown
# PLAN_{{PLAN_ID}} — {{TAREA}}

## INPUT BLOCK
[pegar sección 1 completa, llenada]

## SEGMENTOS
[uno por cada Sn, con el schema de la sección 3 completo]

## X-RAY POR SEGMENTO
[sección 7 corrida por cada Sn al cerrarlo]

## CHECKPOINTS
[uno por intento relevante, schema sección 9]

## PLUGINS DE EXTENSIÓN
[uno por archivo nuevo de Refactoria, sección 10]

## CONSEJO DE CIERRE — 12-ASK
[sección 6 respondida con evidencia, al final del plan completo]

## VEREDICTO FINAL
ESTADO: PASS | FAIL | BLOCKED
FIRMADO_POR: sheriff + guardian + watchdog
EVIDENCIA: [commits, read-backs, tests]
```

---

## 14. CHECKLIST DE CIERRE FINAL (plan completo)

```text
[ ] INPUT BLOCK completo, sin campos UNKNOWN sin resolver
[ ] Todos los segmentos declarados con su schema (sección 3)
[ ] Sheriff preflight PASS en todos los segmentos abiertos
[ ] Guardián PASS en todos los segmentos cerrados
[ ] Watchdog sin BLOCKED sin resolver
[ ] X-Ray de 14 puntos corrido en cada segmento
[ ] Checkpoints existen y son recuperables al 100% (probado: se puede pegar en chat nuevo)
[ ] Plugins de extensión anotados para cada archivo nuevo de Refactoria
[ ] Despliegue: los N documentos del lote tienen destino final (canónico/Refactoria/GAP explícito)
[ ] Ningún GAP quedó sin diagnóstico + solución aplicada o BLOCKED explícito
[ ] Hot path intacto, o con paridad de tests documentada si se tocó
[ ] 12-ask council respondido con evidencia, no con opinión
[ ] Commit final sin force-push + read-back confirmado
[ ] DONE declarado solo con evidencia GitHub verificable
```
