# PIPELINE 10 — KERNEL THOUGHT PROTOCOL (KTP)
## Sistema nativo de pensamiento del kernel
**Versión:** 1.0  
**Estado:** Diseño ejecutable  
**Fecha:** 2026-08-09

---

## 1. Qué es

El Kernel Thought Protocol (KTP) es el **sistema de pensamiento nativo** del kernel.  
Cada vez que el kernel piensa, decide o actúa, lo hace a través de esta máquina de estados determinista basada en emojis.

No es decoración.  
Es el protocolo obligatorio de razonamiento del sistema.

**Principio:** 90% determinista (YAML + Python) / 10% LLM (solo cuando el estado lo exige).

---

## 2. Máquina de estados (Emoji FSM)

```
🎯 OBJETIVO
    ↓
🏗️ TAREA
    ↓
💡 PLANIFICAR  ← aquí consulta Resource Brain
    ↓
📌👣 PRÓXIMOS
    ↓
👣 PASO        ← aquí selecciona y carga capacidades
    ↓
🧩 RESULTADOS
    ↓
┌─────────────┬─────────────┬─────────────┐
│ ⚠️ PENDIENTES │ 🔒 CERRADO   │ ⁉️ FALTA    │
└─────────────┴─────────────┴─────────────┘
    ↓               ↓               ↓
📂 ARCHIVAR     ✅ INTEGRADO    (pregunta Director)
    ↓
🆕 NUEVO (si llegó input externo)
```

### Estados y reglas (YAML)

```yaml
# ktp/states.yaml
states:
  OBJETIVO:
    emoji: "🎯"
    tipo: D          # Determinista
    entrada: [input_block, documento, mensaje_chat]
    salida: goal_struct
    microflujo: extract_goal
    resource_brain: false

  TAREA:
    emoji: "🏗️"
    tipo: D
    entrada: [goal_struct]
    salida: task_list
    microflujo: decompose_tasks
    resource_brain: false

  PLANIFICAR:
    emoji: "💡"
    tipo: D
    entrada: [goal_struct, task_list]
    salida: execution_plan
    microflujo: plan_and_select
    resource_brain: true      # ← consulta Resource Brain
    resource_query: "capabilities needed for current goal"

  PROXIMOS:
    emoji: "📌👣"
    tipo: D
    entrada: [execution_plan]
    salida: next_step
    microflujo: select_immediate_step
    resource_brain: false

  PASO:
    emoji: "👣"
    tipo: D+H        # D por defecto, H solo si el paso lo requiere
    entrada: [next_step, selected_capabilities]
    salida: step_result
    microflujo: execute_one_step
    resource_brain: true      # ← carga y usa capacidades
    llm_allowed: conditional

  RESULTADOS:
    emoji: "🧩"
    tipo: D
    entrada: [step_result]
    salida: formatted_output
    microflujo: format_output

  PENDIENTES:
    emoji: "⚠️"
    tipo: D
    entrada: [blockers]
    salida: blocker_list
    microflujo: manage_blockers

  CERRADO:
    emoji: "🔒"
    tipo: D
    entrada: [step_result]
    salida: evidence_hash
    microflujo: close_and_hash

  FALTA:
    emoji: "⁉️"
    tipo: H          # Solo aquí se permite pregunta al Director
    entrada: [missing_info]
    salida: director_question
    microflujo: ask_director

  ARCHIVAR:
    emoji: "📂"
    tipo: D
    entrada: [closed_steps]
    salida: archive_path
    microflujo: archive

  INTEGRADO:
    emoji: "✅"
    tipo: D
    entrada: [evidence_hash]
    salida: integrated_flag
    microflujo: mark_integrated

  NUEVO:
    emoji: "🆕"
    tipo: D
    entrada: [new_input]
    salida: classification
    microflujo: classify_new_input

  INGENIERIA:
    emoji: "🚨"
    tipo: D_STRICT   # 0% LLM, solo código + Sheriff
    entrada: [any]
    salida: deterministic_result
    microflujo: pure_code_mode
```

---

## 3. Integración con Resource / Capability Brain

Flujo obligatorio en cada ciclo de pensamiento:

```
descubre → registra → mapea → verifica → selecciona → prepara → carga → ejecuta
```

Se invoca en dos puntos:

| Estado KTP     | Acción Resource Brain                          |
|----------------|------------------------------------------------|
| 💡 PLANIFICAR  | Descubre y selecciona capacidades necesarias   |
| 👣 PASO        | Prepara + carga solo las capacidades autorizadas |

Estados de un recurso:

```
DISCOVERED → REGISTERED → CONFIGURED → REACHABLE → HEALTHY → AUTHORIZED → AVAILABLE
```

Solo los recursos en estado **AVAILABLE** pueden usarse.

---

## 4. Manejo de inputs nuevos (chat o documento)

```yaml
# ktp/input_handler.yaml
on_new_input:
  1. Leer literal (input_block)
  2. Clasificar: cambio | mejora | correccion | nuevo_documento | prioridad
  3. Mapear impacto (qué tareas/documentos se ven afectados)
  4. Decidir:
       - si prioridad_alta → pausar proceso actual
       - si no → encolar
  5. Convertir en tareas nuevas o actualizar existentes
  6. Re-ejecutar solo micro-flujos dependientes
  7. Actualizar TRACEABILITY.md
```

El Wordflow **nunca se reescribe completo**. Solo se actualiza lo afectado.

---

## 5. Ejecución determinista

- **Reglas:** YAML (`ktp/states.yaml` + `ktp/transitions.yaml`)
- **Ejecutor:** Python puro (`ktp/engine.py`)
- **LLM:** Solo cuando el estado tiene `tipo: H` o `llm_allowed: conditional`
- **Evidencia:** Cada transición genera hash + timestamp en state.json

---

## 6. Trazabilidad

Cada ciclo de pensamiento deja registro:

```json
{
  "cycle_id": "uuid",
  "from_state": "💡",
  "to_state": "📌👣",
  "resources_used": ["codegraph", "memory.search"],
  "input_hash": "sha256:...",
  "output_hash": "sha256:...",
  "timestamp": "2026-08-09T..."
}
```

---

## 7. Ubicación en el kernel

```
kernel/
└── thought/
    ├── ktp/
    │   ├── states.yaml
    │   ├── transitions.yaml
    │   ├── engine.py
    │   └── input_handler.py
    └── resource_brain/
        ├── registry.py
        ├── health.py
        ├── selector.py
        └── preload.py
```

**Estado:** listo para auditoría e integración con F-1→F9.
