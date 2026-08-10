# PIPELINE 12 — PROJECT DOCUMENTS NATIVE SYSTEM (FULL)
## Extensión kernel nativa: documentos + KTP + Resource Brain + Normalizer + G1 Control
**Versión:** 3.0 FULL  
**Estado:** Diseño ejecutable  
**Fecha:** 2026-08-09  
**Trazabilidad:** Reconstrucción 1:1 de todo el material entregado por Director sobre documentos nativos + G1 (P1/P2/P3) + plantillas + Resource Brain + Input Handler

---

## 0. TRAZABILIDAD COMPLETA DE FUENTES

| Fuente | Contenido incorporado |
|--------|-----------------------|
| Bloque G1 completo | P1 (21), P2 (19), P3 (20), CORE, RECOVERY_STATE, MAPA, DECISIONES, GRAFO, modos, 9 archivos control |
| Plantillas emoji | 🎯🏗️💡📌👣🧩⚠️🔒📂🚨⁉️✅🆕 + micro-flujos originales |
| Resource Brain | descubre→registra→mapea→verifica→selecciona→prepara→carga→ejecuta + estados de recurso |
| Project Normalizer | Discovery→Classification→Extraction→Project Model |
| Input Handler | chat/documento → InputBlock → clasificación → prioridad → pause → tareas |
| Estructura PIPELINE | Densidad técnica + micro-diagramas + trazabilidad |

---

## 1. PROPÓSITO

Sistema nativo del kernel que:

1. Posee plantillas deterministas de los documentos mínimos de cualquier proyecto.
2. Normaliza documentos externos de cualquier formato.
3. Usa el Kernel Thought Protocol (emoji FSM) en cada decisión.
4. Consulta Resource Brain antes de usar capacidades.
5. Actualiza de forma incremental (nunca reescribe todo el sistema).
6. Recibe mensajes de chat, los convierte en InputBlock y los transforma en tareas con prioridad (puede pausar procesos).
7. Aplica las reglas G1 (P1/P2/P3) para que el modelo no improvise, no olvide y no mienta.

---

## 2. CONJUNTO NATIVO DE DOCUMENTOS (9)

```
PROJECT/
├── README.md
├── PROJECT_PROFILE.md
├── MASTER_PROJECT.md
├── ARCHITECTURE.md
├── WORKFLOW.md
├── PIPELINE.md
├── CAPABILITIES.md
├── TRACEABILITY.md
└── CHANGELOG.md
```

---

## 3. ARCHIVOS DE CONTROL (9)

```
control/
├── TASKS.md
├── DECISIONES.md
├── GRAFO.md
├── SEGMENTO_X.md
├── DSL.md
├── FAB.md
├── INVARIANTES.md
├── SELF_CHECK.md
└── CONTRATOS.md
```

---

## 4. ESTADO FORMAL (CORE adaptado)

```yaml
META:
  proyecto: "PROJECT_DOCUMENTS_NATIVE"
  version: "3.0"
  director: "HUMANO"
  segmento_activo: "DOCS_NATIVE"

README_IA:
  que_es: "Sistema nativo de documentos + control G1"
  capa_A: "Método de trabajo (P1/P2/P3)"
  capa_B: "Plantillas + Normalizer + KTP"

LEY:
  reglas:
    - No inventar
    - No avanzar sin aprobación
    - Actualizar JSON/state
    - No modificar aprobado
    - No mezclar segmentos
    - PROHIBIDO crear archivos sin permiso
    - Auditar cada 4 secciones
  prohibiciones:
    - Saltar pasos
    - Sintetizar
    - Crear archivos sin permiso

FSM:
  estado_actual: "CONSTRUIR"
  estados_permitidos: ["CONSTRUIR", "VALIDAR", "AUDITAR", "ESPERAR_APROBACION", "REPAIR", "DETENIDO"]

MODO_OPERATIVO:
  permite_crear: true
  permite_modificar: true
  permite_auditar: true
  permite_aprobar: false
  requiere_aprobacion_director: true

PERMISOS:
  crear_segmento: true
  modificar_aprobado: false
  aprobar: false
  crear_archivos: false

PROTOCOLO_RESPUESTA:
  orden:
    - 1_LEER_CORE
    - 2_LEER_TASKS
    - 3_VALIDAR_PERMISOS
    - 4_VALIDAR_PRECONDICIONES
    - 5_JUEZ
    - 6_EJECUTAR
    - 7_VALIDAR_POST
    - 8_ACTUALIZAR_STATE

JUEZ:
  preguntas:
    - ¿Violación de LEY?
    - ¿Autorizado?
    - ¿Evidencia?
    - ¿Precondiciones?
    - ¿State actualizado?

GOBERNANZA_IA:
  director: "HUMANO"
  ejecutor: "modelo"
  auditor: "cualquier_modelo"
  conflicto: "DIRECTOR_DECIDE"

REPAIR_PIPELINE:
  "01": "Retry 3"
  "02": "Comprimir"
  "03": "Nuevo chat"
  "04": "Checkpoint"
  "05": "Director"

ACTIVE_TRUTH: "CORE.ESTADO + SEGMENTO_ACTIVO"
jerarquia_verdad: ["CORE", "CONTRATOS", "DECISIONES", "SEGMENTO", "GRAFO"]
```

---

## 5. P1 — EL MODELO SIGUE EL CARRIL (21 ítems)

**Grupo 1 · Ubicación y puntero**
1. IP visible en cada mensaje (modo + tarea + paso N de X)
2. Cada mensaje muestra estado actual antes de actuar
3. No puede avanzar sin completar el paso anterior

**Grupo 2 · Carga mínima de contexto**
4. Solo carga la state card del modo activo
5. Archiva lo que ya no necesita antes de cargar lo nuevo
6. Límite configurable por modelo — no valor fijo

**Grupo 3 · Gates y checklist**
7. Gate = checklist booleano ✅/❌ — nunca texto libre
8. Contrato define la regla exacta — no el modelo
9. Si gate falla → PARA + registra motivo + paso + timestamp
10. No continúa hasta que Director resuelve el fallo

**Grupo 4 · Visibilidad de estado**
11. Header fijo (FSM/TASKS/JUEZ) en cada respuesta
12. Mapa mental visible en cada segmento
13. Footer con siguiente acción siempre explícito

**Grupo 5 · FSM + Permisos + Precondiciones**
14. FSM define qué acciones están permitidas en cada estado
15. Verificar permisos antes de ejecutar — si NO → gate falla
16. Verificar precondiciones del GRAFO antes de arrancar
17. Registro de rechazo: motivo + paso + timestamp

**Grupo 6 · Anti-Deriva**
18. Comparar objetivo declarado vs respuesta generada
19. Detectar trabajo no solicitado
20. Detectar contenido fuera del segmento activo
21. Si hay deriva → HALT + reportar al Director

---

## 6. P2 — EL MODELO NO OLVIDA (19 ítems)

**Grupo 1 · Medir lo que queda**
1. Sabe cuántos tokens le quedan en tiempo real
2. Alerta a 80% de uso — no espera a llenarse
3. Umbral configurable por modelo

**Grupo 2 · Dividir el trabajo**
4. Divide objetivo en micro-tareas ≤ límite configurable
5. Una micro-tarea a la vez — no mezcla
6. Cada micro-tarea tiene contrato: entrada/salida/criterio

**Grupo 3 · Trazar y detectar invención**
7. Registra input_hash + output_hash por tarea
8. Mide fidelidad — si baja de umbral → HALT
9. Detecta síntesis automática antes de que ocurra

**Grupo 4 · Archivar lo que no necesita**
10. A 80% tokens → archiva traces antiguos
11. Solo mantiene activo: kernel + state card + tarea actual
12. Lo archivado es recuperable — no se pierde

**Grupo 5 · Recuperarse solo**
13. Lee último checkpoint al arrancar
14. Reconstruye IP + modo + estado en menos de 3 mensajes
15. 1 segmento = 1 MD = puntero — no vive en memoria
16. Pegar CORE + SEGMENTO activo → continúa sin explicar de 0

**Grupo 6 · Arrastre mínimo**
17. Solo arrastra: estado actual + frontera activa (3-5 piezas)
18. No arrastra todo lo aprobado — solo resumen por rama
19. Pendientes clasificados: READY / BLOCKED / WAITING

---

## 7. P3 — EL MODELO NO MENTE NI CONTRADICE (20 ítems)

**Grupo 1 · Fuente única de verdad activa**
1. ACTIVE_TRUTH = CORE.ESTADO + SEGMENTO_ACTIVO
2. Todo se valida contra eso — no opiniones ni inferencias
3. Jerarquía: CORE > CONTRATOS > DECISIONES > SEGMENTO > GRAFO

**Grupo 2 · Detección de contradicciones**
4. Compara DECISIONES.json vs GRAFO.json vs SEGMENTO_X vs CORE.estado
5. Tipos de conflicto: dato / regla / estado
6. Si hay conflicto → NO avanza — gate falla

**Grupo 3 · Resolución formal P3-A/B/C/D**
7. P3-A Detección: identificar qué archivos contradicen
8. P3-B Validación: clasificar tipo de conflicto
9. P3-C Resolución: aplicar jerarquía — CORE gana siempre
10. P3-D Confirmación: estado validado antes de continuar

**Grupo 4 · Rollback obligatorio**
11. Si inconsistencia crítica → volver a último checkpoint válido
12. Reconstruir desde CORE + SEGMENTO activo
13. Registrar: qué falló + motivo + timestamp

**Grupo 5 · Flujo global del kernel**
14. INPUT → P1 ejecuta → P2 guarda → P3 valida → OUTPUT estable
15. Si P3 falla → rollback a P2 → re-ejecutar desde P1
16. El sistema solo avanza si P3 valida consistencia

**Grupo 6 · Conexión con los 10 archivos**
17. SELF_CHECK ejecuta P3 antes de cada respuesta
18. INVARIANTES define las reglas que P3 verifica
19. CONTRATOS define postcondiciones que P3 confirma
20. DECISIONES registra cada resolución de conflicto

---

## 8. MODOS OPERATIVOS

```
/arquitecto  → Diseña estructura, tecnologías, módulos, dependencias y planos.
               No genera código de implementación.

/ejecutor    → Implementa, escribe código concreto, ejecuta pruebas, genera artefactos.
               No diseña arquitectura.
```

---

## 9. KERNEL THOUGHT PROTOCOL (KTP) — Emoji FSM

```
🎯 OBJETIVO
    ↓
🏗️ TAREA
    ↓
💡 PLANIFICAR  ← Resource Brain
    ↓
📌👣 PRÓXIMOS
    ↓
👣 PASO        ← Resource Brain (carga)
    ↓
🧩 RESULTADOS
    ↓
┌──────────────┬──────────────┬──────────────┐
│ ⚠️ PENDIENTES │ 🔒 CERRADO    │ ⁉️ FALTA     │
└──────────────┴──────────────┴──────────────┘
    ↓                ↓                ↓
📂 ARCHIVAR      ✅ INTEGRADO     (Director)
    ↓
🆕 NUEVO
```

### Definición de estados

```yaml
OBJETIVO:
  emoji: "🎯"
  tipo: D
  descripcion: >
    Extraer meta principal, verbo de acción, criterios de éxito y de fallo.
    Formato: [Verbo] + [Objeto] + [Restricción]
  salida: goal_struct

TAREA:
  emoji: "🏗️"
  tipo: D
  descripcion: >
    Descomponer en pasos atómicos (1 verbo). Ordenar por dependencias.
    Prioridad CRITICAL|HIGH|MEDIUM|LOW. Estado inicial PENDING.
  salida: task_list

PLANIFICAR:
  emoji: "💡"
  tipo: D
  resource_brain: true
  descripcion: Verificar objetivo + tareas completos. Seleccionar capacidades AVAILABLE.
  salida: execution_plan

PROXIMOS:
  emoji: "📌👣"
  tipo: D
  descripcion: Solo el siguiente paso inmediato (no lista).
  salida: next_step

PASO:
  emoji: "👣"
  tipo: D+H
  resource_brain: true
  llm_allowed: conditional
  descripcion: Ejecutar UN paso. PENDING → RUNNING → DONE.
  salida: step_result

RESULTADOS:
  emoji: "🧩"
  tipo: D
  descripcion: Formato exacto de salida (código, YAML, texto, hash).
  salida: formatted_output

PENDIENTES:
  emoji: "⚠️"
  tipo: D
  descripcion: Bloqueos activos con dueño y fecha límite.
  salida: blocker_list

CERRADO:
  emoji: "🔒"
  tipo: D
  descripcion: Paso completado + hash de evidencia + timestamp.
  salida: evidence_hash

FALTA:
  emoji: "⁉️"
  tipo: H
  descripcion: Único estado que pregunta al Director. Pregunta concreta.
  salida: director_question

ARCHIVAR:
  emoji: "📂"
  tipo: D
  descripcion: Mover a históricos cuando el ciclo termina.
  salida: archive_path

INTEGRADO:
  emoji: "✅"
  tipo: D
  descripcion: Marcar como parte del sistema después de todos los checks.
  salida: integrated_flag

NUEVO:
  emoji: "🆕"
  tipo: D
  descripcion: Documento o capacidad recién incorporada, pendiente de revisión.
  salida: classification

INGENIERIA:
  emoji: "🚨"
  tipo: D_STRICT
  llm_allowed: false
  descripcion: 0% LLM. Solo código + validación Sheriff.
  salida: deterministic_result
```

---

## 10. RESOURCE BRAIN

```
descubre → registra → mapea → verifica → selecciona → prepara → carga → ejecuta
```

Estados de un recurso:

```
DISCOVERED → REGISTERED → CONFIGURED → REACHABLE → HEALTHY → AUTHORIZED → AVAILABLE
```

Solo **AVAILABLE** puede usarse.  
Invocado en 💡 PLANIFICAR y 👣 PASO.

---

## 11. PROJECT NORMALIZER

```
DOCUMENTOS EXTERNOS (PDF/MD/código/wiki/DOCX/…)
          ↓
     DISCOVERY
          ↓
    CLASSIFICATION
          ↓
      EXTRACTION
          ↓
   PROJECT NORMALIZER
          ↓
 9 Documentos Nativos
          ↓
 PROJECT MODEL → SCHEMA → DAG → SHERIFF → EXECUTABLE CAPABILITY
```

---

## 12. INPUT HANDLER

```yaml
on_new_input:
  1. Leer literal → InputBlock
  2. Clasificar: cambio | mejora | correccion | nuevo_documento | prioridad
  3. Mapear impacto (dependencias inversas)
  4. si prioridad_alta → PAUSAR proceso actual
  5. Convertir en tareas nuevas o actualizar existentes
  6. Re-ejecutar SOLO micro-flujos afectados
  7. Actualizar TRACEABILITY.md + CHANGELOG.md
```

---

## 13. MICRO-FLUJOS DE PLANTILLAS (detalle)

### 🎯 OBJETIVO
```
PASO 1 (D): Extraer meta principal (frecuencia palabras clave + posición)
PASO 2 (D): Verificar verbo de acción
PASO 3 (H): Si ambigüedad → pregunta concreta al Director
PASO 4 (D): Redactar [Verbo] + [Objeto] + [Restricción]
PASO 5 (D): Asignar 🎯 + guardar con timestamp + hash
```

### 🏗️ TAREA
```
PASO 1 (D): Descomponer en pasos atómicos (1 verbo)
PASO 2 (D): Estado inicial PENDING
PASO 3 (D): Ordenar por dependencias
PASO 4 (D): Asignar prioridad CRITICAL > HIGH > MEDIUM > LOW
PASO 5 (D): Guardar con 🏗️ + enlace al objetivo padre
```

### 🏛️ ARQUITECTURA
```
PASO 1 (D): Identificar componentes
PASO 2 (D): Mapear dependencias (grafo dirigido)
PASO 3 (D): Clasificar capas (Controller/Service/Repository/Model…)
PASO 4 (P): Si hay código, LLM puede sugerir mejoras (estructura base es D)
PASO 5 (D): Generar Mermaid + guardar
```

### ⚙️ WORKFLOW
```
PASO 1 (D): Extraer fases repetibles
PASO 2 (D): Definir entrada/salida/herramientas por fase
PASO 3 (D): Emitir YAML ejecutable para DAG engine
PASO 4 (D): Guardar con trazabilidad a GOALS
```

### 🔄 PIPELINE
```
PASO 1 (D): Identificar procesos ETL/repetibles
PASO 2 (D): Definir INPUT → TRANSFORM → OUTPUT
PASO 3 (D): Asignar triggers
PASO 4 (D): Guardar esquema de cada paso
```

### 🧩 CAPACIDADES
```
PASO 1 (D): Escanear funciones exportadas / endpoints / CLI
PASO 2 (D): Generar ficha capability (nombre, entrada, salida)
PASO 3 (D): Registrar en CAPABILITIES.md + Capability Registry
```

### 🔗 TRAZABILIDAD
```
PASO 1 (D): Registrar decisión (qué, por qué, cuándo, quién)
PASO 2 (D): Enlazar con commit o paso de workflow
PASO 3 (D): Orden cronológico inverso
```

---

## 14. ACTUALIZACIÓN INCREMENTAL

```yaml
algoritmo:
  1. Hash documento anterior vs nuevo
  2. Si igual → ignorar
  3. Si diferente:
       a. Identificar dependientes
       b. Pausar solo esos micro-flujos
       c. Re-ejecutar únicamente afectados
       d. Nueva evidencia (hash + timestamp)
       e. Continuar resto sin reinicio
```

---

## 15. UBICACIÓN EN KERNEL

```
extensions/project_bootstrap/
├── schemas/
├── templates/
├── microflows/
├── normalizer/
├── updater/
├── ktp/
├── resource_brain/
├── control/
├── manifest.yaml
└── entrypoint.py
```

---

## 16. REGLAS ANTI-SOBREINGENIERÍA

1. Solo 9 documentos nativos + 9 archivos de control.
2. YAML + Python. LLM solo en estados tipo H o conditional.
3. Actualización siempre incremental.
4. Toda decisión → TRACEABILITY.md.
5. Resource Brain es gate obligatorio.
6. Input de chat = InputBlock.
7. P1/P2/P3 son reglas obligatorias de comportamiento del modelo.

---

**Estado:** FULL — listo para auditoría Director.
