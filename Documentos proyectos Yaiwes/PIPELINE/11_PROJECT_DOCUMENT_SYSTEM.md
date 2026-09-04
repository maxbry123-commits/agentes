# PIPELINE 11 — PROJECT DOCUMENT SYSTEM
## Plantillas nativas + Normalizer + Actualización incremental
**Versión:** 1.0  
**Estado:** Diseño ejecutable  
**Fecha:** 2026-08-09

---

## 1. Qué es

Sistema nativo del kernel que:

1. Posee **plantillas deterministas** de los documentos mínimos de cualquier proyecto.
2. Puede **recibir cualquier documento externo** (PDF, MD, código, wiki…) y normalizarlo.
3. Mantiene el proyecto vivo mediante **actualización incremental** (sin rehacer el Wordflow).
4. Se conecta directamente con el **Kernel Thought Protocol (KTP)** y el **Resource Brain**.

---

## 2. Conjunto mínimo de documentos nativos (9)

```
PROJECT/
├── README.md                 # Qué es (humano)
├── PROJECT_PROFILE.md        # Identidad operativa del agente
├── MASTER_PROJECT.md         # Índice maestro + estado global
├── ARCHITECTURE.md           # Componentes + dependencias + diagramas
├── WORKFLOW.md               # Método de trabajo (entrada → proceso → salida)
├── PIPELINE.md               # Procesos repetibles (INPUT → TRANSFORM → OUTPUT)
├── CAPABILITIES.md           # Qué sabe hacer (fichas de capacidad)
├── TRACEABILITY.md           # Origen de cada decisión / fuente
└── CHANGELOG.md              # Historial de cambios
```

Todo documento adicional que el usuario suba se normaliza y se referencia, no se copia.

---

## 3. Micro-flujos de cada plantilla (deterministas)

Cada plantilla tiene un micro-flujo D (Python) definido en YAML.

### 3.1 PROJECT_PROFILE.md
```yaml
microflujo: build_profile
pasos:
  - extraer_proposito
  - extraer_alcance
  - extraer_entradas_salidas
  - extraer_restricciones
  - generar_ficha_identidad
resource_brain: false
```

### 3.2 ARCHITECTURE.md
```yaml
microflujo: build_architecture
pasos:
  - escanear_componentes
  - mapear_dependencias
  - clasificar_capas
  - generar_mermaid
resource_brain: true   # puede usar codegraph, dependency_scanner
```

### 3.3 WORKFLOW.md
```yaml
microflujo: build_workflow
pasos:
  - identificar_fases_repetibles
  - definir_entrada_salida_por_fase
  - asignar_herramientas
  - emitir_yaml_ejecutable
resource_brain: true
```

### 3.4 PIPELINE.md
```yaml
microflujo: build_pipeline
pasos:
  - detectar_procesos_etl
  - definir_input_transform_output
  - asignar_triggers
  - emitir_schema
resource_brain: false
```

### 3.5 CAPABILITIES.md
```yaml
microflujo: build_capabilities
pasos:
  - escanear_funciones_exportadas
  - generar_fichas_capability
  - registrar_en_capability_registry
resource_brain: true
```

### 3.6 TRACEABILITY.md
```yaml
microflujo: append_trace
pasos:
  - registrar_decision
  - enlazar_commit_o_paso
  - ordenar_cronologico_inverso
resource_brain: false
```

---

## 4. Project Normalizer (capacidad nativa)

Convierte cualquier entrada externa al modelo estándar de 9 documentos.

```
DOCUMENTOS DEL PROYECTO (cualquier formato)
          ↓
     DISCOVERY
          ↓
    CLASSIFICATION
          ↓
      EXTRACTION
          ↓
   PROJECT NORMALIZER
          ↓
 ┌────────────────────┐
 │ PROFILE             │
 │ MASTER              │
 │ ARCHITECTURE        │
 │ WORKFLOW            │
 │ PIPELINE            │
 │ CAPABILITIES        │
 │ TRACEABILITY        │
 │ CHANGELOG           │
 └────────────────────┘
          ↓
      PROJECT MODEL
          ↓
     SCHEMA + DAG
          ↓
       SHERIFF
          ↓
  EXECUTABLE CAPABILITY
```

---

## 5. Actualización incremental (sin rehacer Wordflow)

```yaml
# project/updater.yaml
on_document_change:
  1. Detectar hash anterior vs nuevo
  2. Identificar partes afectadas (dependencias inversas)
  3. Pausar solo los micro-flujos dependientes
  4. Re-ejecutar únicamente esos micro-flujos
  5. Actualizar TRACEABILITY.md y CHANGELOG.md
  6. Continuar el resto del sistema sin reinicio
```

Ejemplo:
- Cambia GOALS → se re-ejecutan TASK y WORKFLOW que dependen de él.
- Cambia ARCHITECTURE → se re-ejecuta CAPABILITIES.
- El resto no se toca.

---

## 6. Conexión con Kernel Thought Protocol

| Evento en documentos          | Estado KTP que se activa |
|-------------------------------|--------------------------|
| Nuevo documento subido        | 🆕 NUEVO                 |
| Cambio detectado              | 💡 PLANIFICAR            |
| Falta información             | ⁉️ FALTA                 |
| Documento cerrado con hash    | 🔒 CERRADO               |
| Documento integrado al sistema| ✅ INTEGRADO             |

El KTP usa el Resource Brain para decidir qué capacidades del kernel se necesitan al procesar el cambio.

---

## 7. Ubicación en el kernel

```
extensions/
└── project_bootstrap/
    ├── schemas/              # JSON Schema de cada documento
    ├── templates/            # Plantillas base Markdown
    ├── microflows/           # YAML + Python de cada micro-flujo
    ├── normalizer/           # Conversor de documentos externos
    ├── updater/              # Actualización incremental
    ├── manifest.yaml         # Ficha de la extensión
    └── entrypoint.py
```

---

## 8. Reglas de diseño (anti-sobreingeniería)

- Solo 9 documentos nativos. Todo lo demás se normaliza.
- Micro-flujos en YAML + Python. LLM solo cuando el estado KTP lo permite.
- Actualización siempre incremental.
- Toda decisión deja rastro en TRACEABILITY.md.
- El sistema debe poder arrancar un proyecto solo con estos 9 documentos + el normalizer.

---

**Estado:** listo para auditoría.  
Cuando el Director apruebe, se conecta con el Wordflow F-1→F9 (fusión MiniMax + Kimi K).
