# PIPELINE 13 — PROJECT DOCUMENTS NATIVE — PIEZAS FALTANTES
## Complemento obligatorio del documento 12 FULL
**Versión:** 1.0  
**Estado:** Completar 12_PROJECT_DOCUMENTS_NATIVE_FULL.md  
**Fecha:** 2026-08-09

---

## 1. RECOVERY_STATE COMPLETO

```json
{
  "RECOVERY_STATE": {
    "version": "4.0-definitiva",
    "fecha": "2026-08-09",
    "proyecto": "PROJECT_DOCUMENTS_NATIVE",
    "sistema": "Método de trabajo G1 + Documentos Nativos",
    "resumen": "Sistema operativo cognitivo que controla cómo trabaja el modelo con documentos, evitando improvisación, olvido y contradicciones.",
    "estado_global": "DOCS_NATIVE_BASE_COMPLETA",
    "siguiente_accion": "conectar_con_Wordflow_F1_F9",
    "lista_validacion": {
      "P1_21_items": true,
      "P2_19_items": true,
      "P3_20_items": true,
      "CORE_completo": true,
      "9_documentos_nativos": true,
      "9_archivos_control": true,
      "KTP_emoji_FSM": true,
      "Resource_Brain": true,
      "Project_Normalizer": true,
      "Input_Handler": true,
      "microflujos_plantillas": true,
      "modos_2": true
    },
    "modos_trabajo": {
      "/arquitecto": "Diseña estructura, tecnologías, módulos, dependencias y planos. No genera código de implementación.",
      "/ejecutor": "Implementa, escribe código concreto, ejecuta pruebas, genera artefactos. No diseña arquitectura."
    }
  },
  "MINI_STATE": {
    "modo": "final",
    "actual": "DOCS_NATIVE_FULL",
    "sigma": 0.88,
    "aprobados": 12,
    "pendientes": ["mapa_mental_10", "ejemplos_salida", "elementos_adicionales_CORE"]
  }
}
```

---

## 2. MAPA MENTAL 10 VISTAS

```
🌐 VISIÓN GLOBAL
DEFINIR MÉTODO → DISEÑAR SISTEMA → CONSTRUIR PIEZAS → INTEGRAR TODO → AUDITAR Y CERRAR
→ Para qué: ver el proyecto completo en 5 segundos
→ Sin esto: el modelo no sabe dónde termina el trabajo

🏗 ARQUITECTURA GLOBAL
Método (P1/P2/P3) → Plantillas → KTP → Resource Brain → Normalizer → Project Model
→ Para qué: entender cómo se conectan las capas
→ Sin esto: cada pieza parece independiente

📍 POSICIÓN ACTUAL
DOCS_NATIVE
├─ P1 ← control de carril
├─ P2 ← anti-amnesia
├─ P3 ← verdad única
├─ KTP ← pensamiento
├─ Resource Brain ← capacidades
└─ Normalizer ← documentos externos

🔗 ROMPECABEZAS (dependencias)
P1 → P2 → P3
         ↓
    KTP + Resource Brain
         ↓
    Normalizer + Plantillas
         ↓
    Project Model ejecutable

🎯 PROPÓSITO
Que el modelo no improvise, no olvide y no mienta al trabajar con documentos.

📥 ENTRADA / SALIDA
INPUT (chat|documento) → InputBlock → KTP → Resource Brain → Normalizer → 9 docs + control

🚀 DESBLOQUEA
Documentos nativos listos → se puede conectar Wordflow F-1→F9

📊 MADUREZ
P1/P2/P3          ██████████ 100%
KTP + Resource    ██████████ 100%
Normalizer        ██████████ 100%
Mapa + Recovery   ████░░░░░░  40%  ← este documento completa

⚙️ MICROFLUJO ACTIVO
Input → Clasificar → Planificar → Seleccionar capacidades → Ejecutar micro-flujo → Evidencia

🧩 ENSAMBLAJE FINAL
G1 Control + Plantillas + KTP + Resource Brain + Normalizer = Sistema de documentos nativo
```

---

## 3. EJEMPLOS DE SALIDA DE PLANTILLAS

### 🎯 OBJETIVO
```
🎯 OBJETIVO: Construir un sistema de autenticación OAuth2 para el backend.
   - Criterio de éxito: Login funcional con Google y GitHub.
   - Criterio de fallo: No completar en 3 iteraciones.
   - Hash: sha256:a1b2c3d4e5f6...
   - Timestamp: 2026-08-09T20:40:00Z
```

### 🏗️ TAREA
```
🏗️ TAREA_EN_CURSO: Implementar endpoint /auth/login
   - Estado: RUNNING
   - Pasos:
     1. [DONE] Crear modelo User en DB
     2. [RUNNING] Implementar lógica OAuth2 ← ACTUAL
     3. [PENDING] Escribir tests de integración
   - Prioridad: HIGH
   - Objetivo padre: sha256:a1b2c3d4e5f6...
```

### 🏛️ ARQUITECTURA
```
🏛️ ARQUITECTURA:
   - Capa 1: Controllers (auth_controller.py, user_controller.py)
   - Capa 2: Services (oauth_service.py, token_service.py)
   - Capa 3: Repositories (user_repo.py)
   - Capa 4: Models (user.py, token.py)
   - Diagrama: Controller → Service → Repository → Model
```

### ⚙️ WORKFLOW
```yaml
⚙️ WORKFLOW:
  fases:
    - analisis:
        entrada: "requisitos"
        salida: "especificación técnica"
        herramientas: ["code_analysis", "dependency_scanner"]
    - implementacion:
        entrada: "especificación técnica"
        salida: "código fuente"
        herramientas: ["code_generator", "linter"]
    - test:
        entrada: "código fuente"
        salida: "reporte de tests"
        herramientas: ["test_runner", "coverage_checker"]
```

### 🔄 PIPELINE
```
🔄 PIPELINE:
  pipeline_deploy:
    trigger: push a main
    pasos:
      - INPUT: código fuente
      - TRANSFORM: compilar + tests
      - OUTPUT: imagen Docker en registry
      - NOTIFICAR: si falla, alertar a #devops
```

### 🧩 CAPACIDADES
```
🧩 CAPACIDADES:
  - capability_id: auth_login
    inputs: {provider: string, token: string}
    outputs: {jwt: string, user_id: int}
    entrypoint: POST /auth/login
```

### 🔗 TRAZABILIDAD
```
🔗 TRAZABILIDAD:
  - [2026-08-09] Decisión: Usar OAuth2 en lugar de JWT propio.
    Razón: Compatibilidad con Google/GitHub.
    Fuente: Documento de requisitos v2.1, línea 45.
    Commit: a1b2c3d
```

---

## 4. DASHBOARD + LISTA DE VALIDACIÓN

```
══════════════════════════════════════
PROJECT DASHBOARD — DOCS NATIVE
══════════════════════════════════════
TOTAL APROBADOS: 12
TOTAL PENDIENTES: 3 (mapa, ejemplos, elementos CORE)
TOTAL BLOQUEADOS: 0
SIGMA: 0.88
ACTUAL: DOCS_NATIVE_FULL
SIGUIENTE: conectar Wordflow F-1→F9
══════════════════════════════════════

LISTA DE VALIDACIÓN
✅ P1: 21 ítems
✅ P2: 19 ítems
✅ P3: 20 ítems
✅ CORE base
✅ 9 documentos nativos
✅ 9 archivos de control
✅ KTP emoji FSM
✅ Resource Brain
✅ Project Normalizer
✅ Input Handler
✅ Micro-flujos plantillas
✅ Modos /arquitecto /ejecutor
⚠️ Mapa mental 10 vistas          ← este documento
⚠️ Ejemplos de salida             ← este documento
⚠️ Elementos adicionales CORE     ← este documento
```

---

## 5. FORMATO DE SALIDA ESTÁNDAR

```
[HEADER]
FSM: CONSTRUIR | MODO: /ejecutor | TAREA: X | PASO: N/M
JUEZ: ✅ permisos | ✅ precondiciones | ✅ ACTIVE_TRUTH

[CUERPO]
... contenido de la respuesta ...

[FOOTER]
SIGUIENTE: ...
ESTADO: ...
HASH: sha256:...
```

---

## 6. VMEF ANTI-SOBREINGENIERÍA

```
VMEF = Validar Mínimo Ejecutable Funcional

Reglas:
1. Solo se implementa lo que tiene contrato claro de entrada/salida.
2. Si una pieza no tiene micro-flujo D definido → no se construye.
3. Si una capacidad no está en Resource Brain como AVAILABLE → no se usa.
4. Preferir 9 documentos nativos + normalizer antes de crear nuevos tipos de documento.
5. Toda extensión debe pasar por Enchufe Universal v2 + Sheriff.
```

---

## 7. ELEMENTOS ADICIONALES DEL CORE

```yaml
ELEMENTOS_ADICIONALES:
  10_roles_modelo:
    - Estratega
    - Investigador
    - Arquitecto
    - Lógico
    - Constructor
    - Auditor
    - Verificador
    - Recovery
    - Optimizador
    - Documentador

  15_modos_MASTER:
    - Exploración
    - Investigación
    - Debate
    - Diagnóstico
    - Diseño
    - Construcción
    - Pruebas
    - Auditoría
    - Verificación
    - Recuperación
    - Documentación
    - Revisión
    - Aprobación
    - Consolidación
    - Cierre

  formula_A+X×√π=Y: "Objetivo medible = base + variable × factor de incertidumbre"

  semaforo_confianza:
    🟢 ALTA
    🟡 MEDIA
    🔴 BAJA

  palabra_clave_ANCLA: "/ancla → resetea al objetivo principal sin perder contexto"
```

---

## 8. PROPÓSITO DE CADA ARCHIVO DE CONTROL

| Archivo | Propósito |
|---------|-----------|
| TASKS.md | Lista de tareas activas, pendientes, bloqueadas y completadas con estado |
| DECISIONES.md | Registro de cada decisión tomada (qué, por qué, cuándo, quién) |
| GRAFO.md | Dependencias entre tareas y documentos (quién bloquea a quién) |
| SEGMENTO_X.md | Estado del segmento activo actual |
| DSL.md | Definiciones de lenguaje de dominio usadas en el proyecto |
| FAB.md | Fábrica de artefactos (cómo se generan outputs) |
| INVARIANTES.md | Reglas que nunca pueden romperse (P3 las verifica) |
| SELF_CHECK.md | Checklist que se ejecuta antes de cada respuesta |
| CONTRATOS.md | Postcondiciones que deben cumplirse para dar una tarea por cerrada |

---

**Estado:** Este documento completa las piezas faltantes del 12 FULL.  
Juntos forman la base completa de la capa de documentos nativos.
