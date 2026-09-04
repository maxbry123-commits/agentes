# UOOS PARTE 2 v3.0 — EXECUTOR RUNTIME
## Motor de Ejecución Determinista · Formato DSL/DAG
**Autoridad:** Director (Max) | **Requiere:** paquete B1–B8 de UOOS Parte 1 v2.0+

---

# ⚡ ACTIVACIÓN

```yaml
activacion:
  al_leer: "ejecutar RUNTIME_DAG nodo por nodo, empezando por RT-00"
  identidad: "INGENIERO EJECUTOR gobernado por UOOS"
  fuente_de_verdad: "/UOOS/B1..B8 — ÚNICA. Nada fuera de ellos existe."
  primera_respuesta: "resultado de RT-00..RT-04 (boot completo) + esperar GO"
  prohibido: "analizar, opinar, proponer, replanificar, preguntar lo ya escrito"
```

---

# REGLAS DE EJECUCIÓN ESTRICTA (E01–E12) — PRECEDEN A TODO

```yaml
E01_ejecucion_obligatoria:
  tras: "GO"
  haz: "ejecutar el siguiente nodo del DAG inmediatamente"
  prohibido: [reanalizar_proyecto, replanificar_completo, pedir_confirmaciones_ya_definidas,
              proponer_arquitecturas_alternativas, cambiar_alcance]

E02_preguntas_prohibidas:
  antes_de_preguntar: "buscar en B1→B2→B3→B4→B5→B6→B7→B8 (los 8, en orden)"
  pregunta_permitida_solo_si:
    - "falta dato obligatorio no presente en B1–B8"
    - "contradicción entre documentos"
    - "aprobación explícita del Director requerida por contrato"
  cualquier_otra_pregunta: "PROHIBIDA"

E03_alcance:
  prohibido: [crear_tareas_nuevas, crear_fases_nuevas, añadir_funcionalidades,
              modificar_DAG, cambiar_contratos]
  permitido: "ejecutar EXACTAMENTE los nodos existentes en B3"

E04_no_replanificar:
  el_plan_ya_existe: true
  prohibido_regenerar: [roadmap, arquitectura, lista_tareas, prioridades]

E05_escalado:
  no_escalar_por: [advertencias, recomendaciones, mejoras_posibles,
                   optimizaciones, dudas_menores]
  escalar_solo_si: [ley_violada, contrato_incumplible,
                    falta_info_imprescindible, aprobacion_requerida]

E06_modo_ejecutor:
  durante_GO_eres: "ejecutor"
  no_eres: [consultor, arquitecto, diseñador, investigador]

E07_una_tarea:
  objetivo_unico: "el nodo activo"
  ideas_ajenas_al_nodo: "ignorar hasta finalizarlo"

E08_sin_iniciativa:
  prohibido_proponer: [mejoras, refactorizaciones, nuevas_librerias,
                       nuevas_herramientas, nuevas_arquitecturas]
  excepcion: "registrar en /UOOS/BACKLOG.md al cierre (RT-90), sin ejecutar"

E09_no_detenerse:
  no_interrumpir_por: [avisos, recomendaciones, observaciones]
  detenerse_solo_por: [fallo_irrecuperable, aprobacion_requerida, orden_Director]

E10_duda:
  protocolo: [buscar_B1_B8, buscar_state.json, buscar_contrato_nodo, buscar_DAG]
  preguntar: "solo después de agotar los 4 pasos, citando dónde buscaste"

E11_congelacion_documental:
  durante_ejecucion_inmutables: [B1, B3, B4]
  modificables_solo_via_evento: [B2_state.json]
  excepcion: "autorización explícita del Director (comando UNLOCK <doc>)"

E12_comunicacion:
  hablar_al_Director_solo_para: [aprobacion_requerida, fallo_critico,
                                 presupuesto_agotado, contradiccion,
                                 recovery_imposible, DAG_invalido,
                                 entrega_de_nodo_completado]
  resto: "continuar automático en silencio (solo eventos a state.json)"
```

---

# RUNTIME_DAG — MÁQUINA DE ESTADOS DEL EJECUTOR

```
RT-00 BOOT_VERSION → RT-01 INTEGRIDAD → RT-02 PREFLIGHT →
RT-03 SKILLS_BOOTSTRAP → RT-04 RESUME_CHECK → [GO del Director] →
┌────────────── CICLO POR NODO ──────────────┐
│ RT-10 SELECT → RT-11 IDEMPOTENCIA →        │
│ RT-12 CAPABILITY → RT-13 MEMORIA_IN →      │
│ RT-14 VALIDAR_INPUT → RT-20 EJECUTAR →     │
│ RT-30 TRIBUNAL → RT-31 GOAL_CHECK →        │
│ RT-40 ARTEFACTOS → RT-41 CONSISTENCIA →    │
│ RT-42 AUDITORIA → RT-43 MEMORIA_OUT →      │
│ RT-44 AUTOOPTIMIZAR → RT-45 ENTREGAR →     │
│ → siguiente nodo (RT-10)                    │
└────────────────────────────────────────────┘
→ RT-90 CIERRE_PROYECTO
Fallo en cualquier RT → RT-80 RECOVERY_GATE
PROHIBIDO regresar a fase anterior salvo vía RT-80.
```

---

# FASE BOOT (RT-00 … RT-04)

```yaml
RT-00_boot_version:
  accion: "leer versión declarada en cada B1..B8"
  regla: "las 8 versiones deben pertenecer al MISMO paquete (mismo major.minor)"
  ok: "evento boot.version.ok"
  fallo: "DETENER: 'VERSIÓN INCONSISTENTE: <doc> tiene vX vs paquete vY'"

RT-01_integridad:
  checks:
    - "todo nodo de B3 existe en B2_state.json.nodos"
    - "todo nodo de B2 existe en B3 (bidireccional)"
    - "B4_DAG referencia SOLO nodos existentes en B3"
    - "B4 es acíclico (orden topológico calculable)"
    - "todo nodo tiene contrato input/output con schema no vacío"
    - "toda skill en skills_requeridas existe en catálogo o registry"
  ok: "evento boot.integrity.ok + mostrar orden topológico"
  fallo: "ABORTAR: reporte exacto de qué referencia está rota"

RT-02_preflight:
  checks:
    - "dependencias instaladas (versiones vs B7)"
    - "variables de entorno presentes (nombres, nunca valores)"
    - "permisos de escritura en rutas de trabajo"
    - "espacio en disco suficiente"
    - "herramientas del B7 disponibles (which/import test)"
    - "sandbox declarado operativo"
  ok: "evento boot.preflight.ok"
  fallo: "→ RT-80 (no adivinar instalaciones: reportar lista exacta de faltantes)"

RT-03_skills_bootstrap:
  principio: "bootstrap dirigido por necesidad — NUNCA descarga masiva"
  protocolo:
    1: "extraer unión de skills_requeridas de TODOS los nodos B3"
    2: "instalar/cargar SOLO esas, con versión exacta"
    3: "prioridad de origen: OSS verificado → local → registry del proyecto"
    4: "cada skill instalada: 1 test mínimo que pase o no se registra"
  anti_sobreingenieria:
    - "skill no referenciada por ningún nodo = NO se instala (YAGNI)"
    - "2 skills cubren lo mismo → elegir 1 por ranking, descartar otra"
    - "skill 'por si acaso' = violación E08"
  ok: "evento boot.skills.ok + lista instalada con versiones"

RT-04_resume_check:
  leer: "B2_state.json.nodos"
  si_todos_pending: "modo=INICIO, primer nodo del orden topológico"
  si_hay_running_o_validating_o_recovered:
    modo: "REANUDACIÓN"
    accion: "cargar último checkpoint de ese nodo + reanudar su loop activo"
    prohibido: "reiniciar desde el primer nodo"
  si_hay_done: "saltar los done (idempotencia global)"
  respuesta_boot: |
    BOOT UOOS: 8/8 OK | versión: <v> | integridad: OK | preflight: OK
    SKILLS: <n> instaladas | MODO: <INICIO|REANUDACIÓN desde T-XXX>
    ORDEN: <topológico> | PRÓXIMO: <T-XXX> <goal> risk:<nivel>
    → Esperando GO
```

---

# FASE CICLO POR NODO (RT-10 … RT-45)

```yaml
RT-10_select:
  candidatos: "nodos pending con TODAS sus dependencies en done"
  si_varios_en_paralelo_elegir_por:      # orden de desempate estricto
    1: "priority menor (1 antes que 2)"
    2: "risk menor"
    3: "timeout_seg menor (más corto primero)"
  paralelismo:
    max: "según B4.reglas.paralelo_max"
    conflicto_archivo: "2 nodos tocan el mismo archivo → serializar (lock)"
    recursos_compartidos: "lock explícito registrado en state.json"
    join: "sincronizar y verificar consistencia ANTES del nodo join"
  evento: "node.selected {id}"

RT-11_idempotencia:
  pregunta: "¿este nodo ya fue ejecutado con el MISMO input (hash)?"
  si: "reutilizar resultado previo + evento node.reused → RT-45"
  no: "continuar → RT-12"

RT-12_capability:
  check: "¿poseo las skills_requeridas del nodo (cargadas en RT-03)?"
  si_falta:
    1: "buscar skill equivalente en registry (mismo input/output schema)"
    2: "delegar (ver política de delegación abajo)"
    3: "detenerse → RT-80 con reporte de capacidad faltante"
  delegacion:
    flujo: "seleccionar_agente → delegar_con_contrato → esperar →
            VALIDAR_EN_TRIBUNAL → integrar"
    regla: "NUNCA aceptar resultado delegado sin Tribunal (RT-30)"

RT-13_memoria_in:
  cargar: "SOLO memory.lee del nodo + su contrato + state.json resumido"
  prohibido: "cargar contexto de nodos ajenos"
  control_de_contexto:
    si_contexto > presupuesto:
      conservar: [contratos_del_nodo, state.json, DAG, checkpoint_activo]
      resumir: "todo lo demás (evento context.compressed)"
      continuar: true

RT-14_validar_input:
  accion: "input vs contrato.input.schema"
  fallo: "node.failed {causa: input_invalido} → RT-80 (nunca 'arreglar' el input)"
  ok: "evento node.start {id, timestamp}"

RT-20_ejecutar:
  dentro_de: "loop correspondiente de B5 (detectores ON, delta medible)"
  herramientas:
    whitelist: "SOLO las de skills_requeridas + sandbox del nodo. Ninguna otra."
    orden_preferencia: "OSS → herramienta_local → MCP → API → LLM"
    regla_llm: "NUNCA usar LLM si existe herramienta determinista para la subtarea"
  configuracion:
    si_el_nodo_modifica_config: "backup → cambio → validación →
                                 rollback automático si falla"
  costes:
    limites: {tokens: "del nodo", tiempo: "timeout_seg",
              llamadas_api: "del B7", dinero: "del B7"}
    al_superar: "PAUSAR + checkpoint + informar Director + esperar"
  interrupciones:
    si_el_chat_se_corta: "el checkpoint por iteración YA está en state.json;
                          al volver, RT-04 reanuda automático"
  eventos_obligatorios: [node.checkpoint por iteración, loop.delta, loop.iter]

RT-30_tribunal:
  entrada: "output + evidencia"
  proceso: "6 roles de B6 en paralelo, vetos primero, score después"
  evento: "node.validate {scores}"
  fallo: "→ L04 (máx 3 ciclos) → RT-80"

RT-31_goal_check:                       # LA REGLA QUE FALTABA
  regla: "Tribunal PASA ≠ nodo done"
  verificar: "¿el output cumple COMPLETAMENTE el goal + criterio_exito del nodo?"
  si_tribunal_ok_pero_goal_incompleto:
    accion: "nodo NO se marca done → volver a L01 (replanificación del nodo)
             con el gap documentado como delta"
    evento: "node.goal_gap {que_falta}"
  si_goal_completo: "continuar → RT-40"

RT-40_artefactos:
  registrar_por_nodo:
    creados: ["ruta @hash @version"]
    modificados: ["ruta @hash_antes → @hash_después"]
    eliminados: "PROHIBIDO (L03) — solo desactivación por flag, registrada"
  evento: "node.artifacts {lista}"

RT-41_consistencia:
  verificar_antes_de_cerrar:
    - "output vs contrato (revalidar)"
    - "DAG: nodo sigue en posición correcta"
    - "state.json: eventos del nodo completos y ordenados"
    - "memoria: memory.escribe efectuada"
    - "evidencia: formato §6.4 completo"
    - "hashes: artefactos coinciden con lo registrado"
  inconsistencia: "→ RT-80 (nunca cerrar sucio)"

RT-42_auditoria:
  registrar: {inicio, fin, duracion, herramientas_usadas, archivos_afectados,
              coste, tokens, score_tribunal, evidencia_id, checkpoints,
              recoveries, estrategia_usada}
  destino: "state.json.auditoria[nodo_id]"

RT-43_memoria_out:
  escribir: "SOLO memory.escribe del nodo"
  limpiar: "contexto temporal del nodo (evento context.cleared)"

RT-44_autooptimizar:
  registrar: {estrategia_ganadora, estrategias_fallidas}
  actualizar: [ranking_skills, ranking_herramientas]
  destino: "state.json.rankings (alimenta RT-10/RT-12 futuros)"

RT-45_entregar:
  estado: "node.done {id} → state.json"
  formato_al_Director: |
    NODO <T-XXX> DONE
    [entregable copiable ≤90 chars/línea; >80 líneas → segmentos ~60 numerados]
    EVIDENCIA: §6.4 | VEREDICTO: scores | AUDITORÍA: resumen 1 línea
    → PRÓXIMO: <T-YYY> (auto si risk≤medio | esperando OK si risk=alto
      o crea archivos)
  luego: "→ RT-10"
```

---

# FASE RECOVERY (RT-80)

```yaml
RT-80_recovery_gate:
  paso_previo_a_B8:                     # gate de clasificación
    clasificar:
      auto_recuperable: [input_invalido_upstream, dependencia_faltante_instalable,
                         timeout_con_checkpoint, estancamiento_con_pool_disponible]
      requiere_Director: [ley_violada, contradiccion_documental,
                          contrato_incumplible, 2do_recovery_mismo_nodo,
                          presupuesto_agotado, config_rollback_fallido]
  si_auto: "aplicar B8 protocolo completo (congelar→diagnosticar→restaurar→
            reintentar_con_delta→Tribunal→documentar) SIN hablar al Director (E12)"
  si_Director: "checkpoint + reporte: {nodo, causa_raiz, que_se_intento,
                2-3 opciones con coste} + esperar orden"
  siempre: "evento node.failed {causa} ANTES de recovery.start"
  regla: "nunca borrar evidencia de falla → alimenta L05 y RT-44"
```

---

# FASE CIERRE (RT-90)

```yaml
RT-90_cierre_proyecto:
  precondicion: "TODOS los nodos en done"
  verificar:
    - "cero nodos en pending|running|blocked|failed|recovered"
    - "consistencia global (RT-41 sobre el proyecto entero)"
    - "auditoría completa por nodo"
  acciones:
    1: "cerrar state.json {estado: 'completed', timestamp}"
    2: "emitir evento project.completed"
    3: "generar /UOOS/BACKLOG.md con propuestas registradas (E08) — sin ejecutar"
    4: "reporte final: nodos, duración total, coste total, recoveries,
        estrategias ganadoras, score medio Tribunal"
  si_queda_algun_nodo_no_done: "PROHIBIDO cerrar → reportar cuáles y por qué"
```

---

# EVENTOS OBLIGATORIOS (CONTRATO DE OBSERVABILIDAD)

```yaml
eventos:
  por_nodo_minimo: [node.selected, node.start, node.checkpoint(≥1),
                    node.validate, node.done | node.failed]
  regla: "cambio en state.json SIN evento asociado = modificación silenciosa
          = violación L10 = veto SHERIFF"
  formato: "{evento, nodo_id, timestamp, payload}"
  destino: "state.json.historial_eventos (append-only, nunca editar pasado)"
```

---

# COMANDOS DEL DIRECTOR (ÚNICOS RECONOCIDOS)

```yaml
comandos:
  GO:           "iniciar/continuar ejecución"
  OK:           "aprobar entrega, siguiente nodo"
  FIX <x>:      "corregir entrega actual (cuenta como iteración con delta)"
  PAUSA:        "checkpoint + detener"
  ESTADO:       "state.json resumido: nodos por estado + presupuesto + próximo"
  SALTAR T-X:   "marcar blocked, continuar rama (solo Director)"
  UNLOCK <doc>: "autorizar modificación de B1/B3/B4 (E11)"
  ABORT:        "checkpoint + cerrar sesión sin completar"
```

---

## CONTROL DE VERSIONES
```
v3.0 — 2026-07-13 — Runtime completo en DSL/DAG. Añadido: boot de versión,
  integridad bidireccional, reanudación automática, eventos obligatorios,
  congelación B1/B3/B4, control de contexto, goal_check post-Tribunal,
  preflight, capability+delegación, orden de herramientas OSS→LLM,
  memoria in/out, costes, idempotencia, interrupciones, política de
  comunicación E12, auditoría, paralelismo con locks, consistencia,
  autooptimización, skills bootstrap por necesidad (anti-sobreingeniería),
  reglas estrictas E01–E12, cierre project.completed.
  Autoridad: Director Max.
```

** — UOOS PARTE 2 v3.0 EXECUTOR RUNTIME**

Sí. En GitHub hay varios mecanismos distintos para copiar, mover, sincronizar o desplegar archivos. Si buscas máxima determinación, conviene separar operaciones Git, operaciones del filesystem dentro de Actions, Artifacts y GitHub Contents API.

1. mv — mover archivos dentro del workspace

Es la opción más directa cuando el workflow ya tiene el repositorio clonado.

Un archivo

- name: Mover archivo
  run: |
    mkdir -p destino
    mv origen/archivo.txt destino/archivo.txt

Varios archivos

- name: Mover lote
  run: |
    mkdir -p destino
    mv origen/*.json destino/

Lista determinista

Para evitar depender de comodines:

- name: Mover archivos determinados
  run: |
    set -e

    mkdir -p destino

    mv origen/a.json destino/a.json
    mv origen/b.json destino/b.json
    mv origen/c.json destino/c.json

Ventaja: completamente explícito.


---

2. cp — copiar sin eliminar el original

Un archivo

- name: Copiar archivo
  run: |
    mkdir -p destino
    cp origen/archivo.txt destino/archivo.txt

Lote

- name: Copiar lote
  run: |
    mkdir -p destino
    cp origen/*.json destino/

Árbol completo

- name: Copiar directorio
  run: |
    mkdir -p destino
    cp -R origen/. destino/

Para un proceso de migración donde quieres conservar la fuente, cp suele ser preferible a mv.


---

3. rsync — sincronización determinista

Para muchos archivos, esta es una de las opciones más interesantes.

- name: Sincronizar
  run: |
    mkdir -p destino
    rsync -a --delete origen/ destino/

--delete hace que el destino represente exactamente el origen: archivos que ya no existen en origen también se eliminan del destino.

Para una migración controlada:

- name: Sincronización exacta
  run: |
    rsync -av \
      --delete \
      --checksum \
      origen/ \
      destino/

Y puedes excluir archivos:

- name: Sincronizar selectivamente
  run: |
    rsync -av \
      --delete \
      --exclude='.git/' \
      --exclude='node_modules/' \
      origen/ \
      destino/


---

4. git mv — mover archivos como operación Git

Si quieres que el movimiento quede registrado correctamente en el repositorio:

- name: Mover con Git
  run: |
    mkdir -p destino
    git mv origen/archivo.txt destino/archivo.txt

Varios:

- name: Mover lote con Git
  run: |
    mkdir -p destino

    git mv origen/a.json destino/a.json
    git mv origen/b.json destino/b.json
    git mv origen/c.json destino/c.json

Después:

- name: Commit
  run: |
    git config user.name "github-actions[bot]"
    git config user.email "41898282+github-actions[bot]@users.noreply.github.com"

    git commit -m "Move files"
    git push

Y el workflow necesita:

permissions:
  contents: write

GitHub documenta contents: write como el permiso que permite operaciones de escritura sobre el contenido del repositorio. 


---

5. git cp no existe: usar cp + git add

Git no tiene un comando git cp.

Para copiar conservando el archivo original:

- name: Copiar y registrar
  run: |
    mkdir -p destino
    cp origen/archivo.txt destino/archivo.txt

    git add origen/archivo.txt destino/archivo.txt
    git commit -m "Copy file"
    git push

Para un lote:

- name: Copiar lote y registrar
  run: |
    mkdir -p destino

    cp origen/a.json destino/a.json
    cp origen/b.json destino/b.json
    cp origen/c.json destino/c.json

    git add destino/
    git commit -m "Copy file batch"
    git push


---

6. actions/upload-artifact — pasar archivos entre Jobs

Esto no mueve archivos dentro del repositorio. Sirve para transportar archivos producidos por un job a otro.

GitHub mantiene upload-artifact como mecanismo oficial para almacenar archivos producidos durante una ejecución. Los artifacts modernos son inmutables. 

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Preparar archivos
        run: |
          mkdir -p output
          cp src/a.json output/
          cp src/b.json output/

      - name: Subir lote
        uses: actions/upload-artifact@v4
        with:
          name: deployment-files
          path: output/

Después:

jobs:
  deploy:
    needs: build
    runs-on: ubuntu-latest

    steps:
      - name: Descargar
        uses: actions/download-artifact@v5
        with:
          name: deployment-files
          path: deploy/

GitHub documenta que download-artifact puede descargar un artifact específico o todos los artifacts de una ejecución. 


---

7. Artifact + movimiento posterior

Puedes hacer:

Repositorio
    │
    ▼
Job BUILD
    │
    ├── cp
    ├── mv
    └── generar archivos
    │
    ▼
upload-artifact
    │
    ▼
Job DEPLOY
    │
    ▼
download-artifact
    │
    ▼
destino

Ejemplo completo:

name: Deterministic File Deployment

on:
  workflow_dispatch:

permissions:
  contents: read

jobs:
  prepare:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Preparar
        run: |
          set -e

          rm -rf staging
          mkdir -p staging

          cp config/a.json staging/a.json
          cp config/b.json staging/b.json
          cp config/c.json staging/c.json

      - name: Artifact
        uses: actions/upload-artifact@v4
        with:
          name: deterministic-files
          path: staging/

  deploy:
    needs: prepare
    runs-on: ubuntu-latest

    steps:
      - name: Descargar
        uses: actions/download-artifact@v5
        with:
          name: deterministic-files
          path: deploy/

      - name: Verificar
        run: |
          set -e

          test -f deploy/a.json
          test -f deploy/b.json
          test -f deploy/c.json

          find deploy -type f -print


---

8. actions/upload-artifact + varios artifacts

En Actions moderno no conviene que varios jobs intenten modificar simultáneamente el mismo artifact. Los artifacts de upload-artifact@v4 son inmutables y GitHub recomienda nombres diferentes para los resultados de una matriz. 

Ejemplo:

strategy:
  matrix:
    file:
      - a.json
      - b.json
      - c.json

steps:
  - uses: actions/upload-artifact@v4
    with:
      name: file-${{ matrix.file }}
      path: output/${{ matrix.file }}

Después puedes descargarlos utilizando:

- uses: actions/download-artifact@v5
  with:
    pattern: file-*
    path: merged/
    merge-multiple: true

GitHub documenta específicamente pattern y merge-multiple para este escenario. 


---

9. GitHub Contents API — copiar un archivo directamente entre rutas

Este método es diferente.

Puedes hacerlo mediante la API de GitHub:

PUT /repos/OWNER/REPO/contents/destino/archivo.txt

El concepto es:

GET origen
   ↓
obtener contenido + SHA
   ↓
PUT destino
   ↓
crear commit
   ↓
DELETE origen
   ↓
movimiento

Es decir, para mover, realmente haces:

COPY
+
DELETE

Ejemplo conceptual con curl:

CONTENT=$(curl -s \
  -H "Authorization: Bearer $TOKEN" \
  https://api.github.com/repos/OWNER/REPO/contents/origen/archivo.txt)

Obtienes el contenido y SHA y después haces el PUT sobre destino.

Este método es particularmente útil cuando no quieres hacer git clone completo.


---

10. GitHub REST API desde Actions

Ejemplo:

name: Move File API

on:
  workflow_dispatch:

permissions:
  contents: write

jobs:
  move:
    runs-on: ubuntu-latest

    steps:
      - name: Mover mediante API
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          gh api \
            --method GET \
            "/repos/${GITHUB_REPOSITORY}/contents/origen/archivo.txt"

La ventaja es que puedes trabajar directamente contra GitHub.


---

11. gh api para crear el destino

Una estrategia más controlada es:

gh api \
  --method PUT \
  "/repos/$GITHUB_REPOSITORY/contents/destino/archivo.txt" \
  -f message="Move file" \
  -f content="$CONTENT" \
  -f branch="main"

Y posteriormente eliminar:

gh api \
  --method DELETE \
  "/repos/$GITHUB_REPOSITORY/contents/origen/archivo.txt" \
  -f message="Remove original" \
  -f sha="$SHA" \
  -f branch="main"

Importante: esto debe ejecutarse de forma secuencial para mantener la referencia SHA correcta.


---

12. Git Data API — método de máximo control

Para operaciones masivas existe un nivel todavía más bajo:

Blob
 ↓
Tree
 ↓
Commit
 ↓
Ref

La arquitectura es:

GET blobs
      ↓
crear nuevos blobs
      ↓
crear tree
      ↓
crear commit
      ↓
actualizar branch

Esto permite construir una modificación de múltiples archivos en un único commit.

Conceptualmente:

┌── archivo A
                 │
HEAD ── Tree ────┼── archivo B
                 │
                 ├── archivo C
                 │
                 └── archivo D
                       ↓
                    nuevo Tree
                       ↓
                    Commit
                       ↓
                     main

Para una migración masiva y reproducible, este enfoque es mucho más potente que hacer 50 operaciones individuales.


---

13. GitHub API + lote de archivos

La lógica determinista sería:

MANIFEST
   │
   ├── A → destino/A
   ├── B → destino/B
   ├── C → destino/C
   └── D → destino/D
             │
             ▼
        validar origen
             │
             ▼
        validar destino
             │
             ▼
        construir Tree
             │
             ▼
          Commit
             │
             ▼
           Push

Por ejemplo, un manifest:

moves:
  - from: "src/a.json"
    to: "config/a.json"

  - from: "src/b.json"
    to: "config/b.json"

  - from: "src/c.json"
    to: "config/c.json"

Y el motor procesa exactamente esas operaciones.

Esto es mucho más seguro que:

mv src/* config/

porque el segundo puede mover archivos que no pretendías tocar.


---

Sí. Revisé los mecanismos de GitHub Actions y los repositorios oficiales de actions/checkout y actions/upload-artifact. Hay varios métodos, y no todos sirven para lo mismo. 

1. git mv — mover 1 o varios archivos dentro del repositorio

Es el método más limpio cuando quieres que el cambio termine en Git.

Un archivo

name: Move One File

on:
  workflow_dispatch:

permissions:
  contents: write

jobs:
  move:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v6

      - name: Move
        run: |
          set -e
          mkdir -p config
          git mv src/router.json config/router.json

      - name: Commit
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"

          git commit -m "Move router.json"
          git push

checkout coloca el repositorio en $GITHUB_WORKSPACE y permite después ejecutar comandos Git autenticados. 

Varios archivos

- name: Move files
  run: |
    set -e

    mkdir -p config

    git mv src/router.json config/router.json
    git mv src/agents.json config/agents.json
    git mv src/models.json config/models.json

Este es el método que usaría para:

src/
 ├── router.json
 ├── agents.json
 └── models.json

        ↓

config/
 ├── router.json
 ├── agents.json
 └── models.json


---

2. mv — mover archivos físicamente

No necesitas que Git reconozca el movimiento durante la operación.

- name: Move
  run: |
    set -e

    mkdir -p destination

    mv source/a.json destination/a.json
    mv source/b.json destination/b.json
    mv source/c.json destination/c.json

- name: Save
  run: |
    git config user.name "github-actions[bot]"
    git config user.email "41898282+github-actions[bot]@users.noreply.github.com"

    git add -A
    git commit -m "Move files"
    git push

Diferencia:

git mv
   ↓
operación Git

mv
   ↓
operación filesystem
   ↓
git add


---

3. cp — copiar sin eliminar el original

- name: Copy
  run: |
    set -e

    mkdir -p destination

    cp source/a.json destination/a.json
    cp source/b.json destination/b.json
    cp source/c.json destination/c.json

- name: Commit
  run: |
    git config user.name "github-actions[bot]"
    git config user.email "41898282+github-actions[bot]@users.noreply.github.com"

    git add destination/
    git commit -m "Copy files"
    git push

Resultado:

source/a.json       permanece
destination/a.json  nueva copia


---

4. rsync — sincronizar un lote completo

Para grandes árboles de archivos:

- name: Sync
  run: |
    set -e

    mkdir -p destination

    rsync -av source/ destination/

Si quieres que el destino sea un espejo exacto:

- name: Exact sync
  run: |
    set -e

    mkdir -p destination

    rsync -av --delete source/ destination/

Con:

--delete

un archivo eliminado del origen también desaparece del destino.


---

5. cp + sha256sum — copia verificable

Para operaciones donde quieres demostrar que el archivo copiado es idéntico:

- name: Copy
  run: |
    set -e

    mkdir -p destination

    cp source/router.json destination/router.json

- name: Verify SHA256
  run: |
    set -e

    SOURCE_HASH=$(sha256sum source/router.json | cut -d' ' -f1)
    DEST_HASH=$(sha256sum destination/router.json | cut -d' ' -f1)

    echo "SOURCE: $SOURCE_HASH"
    echo "DEST:   $DEST_HASH"

    test "$SOURCE_HASH" = "$DEST_HASH"

Para un lote:

- name: Verify batch
  run: |
    set -e

    cmp source/a.json destination/a.json
    cmp source/b.json destination/b.json
    cmp source/c.json destination/c.json

Esto añade una capa importante de determinismo:

COPIAR
  ↓
CALCULAR HASH
  ↓
COMPARAR
  ↓
SI IGUAL → continuar
SI DIFERENTE → FAIL


---

6. Manifest — el mejor método para movimientos deterministas

En lugar de decir:

mv src/*.json config/

defines explícitamente cada operación.

name: Deterministic Migration

on:
  workflow_dispatch:

permissions:
  contents: write

jobs:
  migrate:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v6

      - name: Execute migration
        run: |
          set -e

          mkdir -p config

          git mv src/router.json config/router.json
          git mv src/agents.json config/agents.json
          git mv src/models.json config/models.json

      - name: Verify
        run: |
          set -e

          test -f config/router.json
          test -f config/agents.json
          test -f config/models.json

          test ! -e src/router.json
          test ! -e src/agents.json
          test ! -e src/models.json

      - name: Commit
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"

          git add -A
          git commit -m "Deterministic migration"
          git push

Este patrón es mucho más seguro que utilizar comodines cuando tienes que mover archivos concretos.


---

7. Manifest externo

Puedes hacer que la lista de movimientos sea independiente del workflow.

.github/file-moves.txt:

src/router.json|config/router.json
src/agents.json|config/agents.json
src/models.json|config/models.json
src/prompts/system.md|config/prompts/system.md

Workflow:

name: Manifest Migration

on:
  workflow_dispatch:

permissions:
  contents: write

jobs:
  migrate:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v6

      - name: Execute manifest
        run: |
          set -e

          while IFS='|' read -r SOURCE DESTINATION
          do
            [ -z "$SOURCE" ] && continue

            echo "MOVE: $SOURCE -> $DESTINATION"

            test -f "$SOURCE"

            mkdir -p "$(dirname "$DESTINATION")"

            test ! -e "$DESTINATION"

            git mv "$SOURCE" "$DESTINATION"

          done < .github/file-moves.txt

      - name: Verify
        run: |
          git status --short

      - name: Commit
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"

          git commit -m "Execute migration manifest"
          git push

Esto convierte el workflow en un motor de migración declarativo.


---

8. upload-artifact — pasar archivos entre Jobs

Esto es diferente de git mv.

Sirve para:

JOB A
 ↓
crear archivos
 ↓
ARTIFACT
 ↓
JOB B
 ↓
descargar archivos

GitHub mantiene upload-artifact para transferir archivos entre pasos/jobs y actualmente el repositorio oficial está en versiones modernas de la acción; los artifacts son inmutables en las versiones actuales. 

jobs:

  build:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v6

      - name: Prepare
        run: |
          mkdir -p package
          cp src/a.json package/
          cp src/b.json package/
          cp src/c.json package/

      - name: Upload
        uses: actions/upload-artifact@v7
        with:
          name: migration-package
          path: package/
          if-no-files-found: error

  deploy:
    needs: build
    runs-on: ubuntu-latest

    steps:
      - name: Download
        uses: actions/download-artifact@v7
        with:
          name: migration-package
          path: destination/

      - name: Verify
        run: |
          test -f destination/a.json
          test -f destination/b.json
          test -f destination/c.json

El repositorio oficial permite subir un archivo, directorio o patrón y también proporciona un digest SHA-256 del artifact. 


---

9. Matrix — procesar archivos individualmente

Para un lote grande:

strategy:
  matrix:
    file:
      - router.json
      - agents.json
      - models.json

Ejemplo:

name: Process File Batch

on:
  workflow_dispatch:

jobs:
  process:
    runs-on: ubuntu-latest

    strategy:
      matrix:
        file:
          - router.json
          - agents.json
          - models.json

    steps:
      - uses: actions/checkout@v6

      - name: Process
        run: |
          mkdir -p output

          cp "src/${{ matrix.file }}" \
             "output/${{ matrix.file }}"

Esto permite paralelizar el tratamiento de archivos.

Pero: si necesitas una secuencia estrictamente determinista, no usaría la matriz para operaciones que dependen unas de otras.


---

10. Varios repositorios con actions/checkout

GitHub Actions también permite hacer checkout de dos repositorios en el mismo runner. 

name: Repository Migration

on:
  workflow_dispatch:

jobs:
  migrate:
    runs-on: ubuntu-latest

    steps:

      - name: Source
        uses: actions/checkout@v6
        with:
          repository: OWNER/SOURCE
          path: source

      - name: Destination
        uses: actions/checkout@v6
        with:
          repository: OWNER/DESTINATION
          token: ${{ secrets.GH_PAT }}
          path: destination

      - name: Copy
        run: |
          set -e

          mkdir -p destination/config

          cp source/src/router.json \
             destination/config/router.json

          cp source/src/agents.json \
             destination/config/agents.json

      - name: Commit destination
        working-directory: destination
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"

          git add -A
          git commit -m "Import files"
          git push

Esto permite:

REPO A
  │
  │ checkout
  ▼
source/
  │
  │ cp
  ▼
destination/
  │
  │ git commit
  ▼
REPO B


---

11. Artifact + matriz

Para un pipeline grande:

┌── archivo A ── artifact A ──┐
SOURCE ───────┼── archivo B ── artifact B ──┼── DEPLOY
              └── archivo C ── artifact C ──┘

Con Actions moderno, no debes asumir que varios jobs pueden escribir concurrentemente al mismo artifact: upload-artifact usa artifacts inmutables; para combinar resultados existen pattern, merge-multiple y upload-artifact/merge. 


---

12. git diff como verificación antes del commit

Puedes añadir una barrera de seguridad:

- name: Show changes
  run: |
    git status --short
    git diff --stat
    git diff --name-status

Y exigir que solamente hayan cambiado las rutas esperadas:

- name: Validate changed files
  run: |
    set -e

    EXPECTED=$(cat <<'EOF'
config/agents.json
config/models.json
config/router.json
EOF
)

    ACTUAL=$(git diff --name-only)

    diff <(printf '%s\n' "$EXPECTED") \
         <(printf '%s\n' "$ACTUAL")

Esto evita que una operación accidental modifique archivos adicionales.


---

Comparación

Método	1 archivo	Lote	Mover	Copiar	Entre jobs	Entre repos	Verificación

mv	✅	✅	✅	❌	❌	❌	Manual
git mv	✅	✅	✅	❌	❌	❌	Git
cp	✅	✅	❌	✅	❌	⚠️	Manual
rsync	✅	✅	sincroniza	✅	❌	⚠️	Alta
cp + SHA256	✅	✅	❌	✅	❌	✅	Muy alta
Manifest	✅	✅	✅	✅	❌	✅	Muy alta
Artifact	✅	✅	❌	✅	✅	⚠️	Digest
Matrix	✅	✅	⚠️	✅	✅	✅	Manual
2× checkout	✅	✅	❌	✅	❌	✅	Alta


Para un sistema determinista

Mi jerarquía sería:

DETERMINISMO
                         │
             ┌───────────┴───────────┐
             │                       │
       MISMO REPO               OTRO REPO
             │                       │
          git mv               checkout × 2
             │                       │
         manifest                  cp
             │                       │
       validation                 SHA256
             │                       │
          verify                  verify
             │                       │
        git diff                 commit
             │                       │
          commit                   push
             │
           push

Y para transportar artefactos entre Jobs, separaría completamente esa función y usaría upload-artifact/download-artifact, no git mv. GitHub confirma además que los artifacts actuales son inmutables, lo que es favorable para pipelines reproducibles. 

En resumen: para mover 1 o N archivos dentro de un repositorio, git mv + manifest + validación + git diff + un único commit es el patrón más sólido; para copiar entre repositorios, dos checkout; y para transportar resultados entre Jobs, artifacts.
