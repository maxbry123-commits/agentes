# Sistema de trabajo — Router / Command Center / Agentes / Orquestación / Auditoría

## Propósito

Este documento define las responsabilidades operativas que deben quedar cableadas al Wordflow sin crear una segunda autoridad de ejecución.

## Componentes

### 1. Router
Recibe la intención, clasifica el tipo de tarea y selecciona la ruta canónica. No ejecuta cambios fuera de las autoridades del Kernel.

### 2. Command Center
Es el punto de coordinación de la misión: mantiene contexto, estado, dependencias, handoff, evidencias y siguiente nodo del DAG.

### 3. Agentes
Los agentes se resuelven por capacidad mediante el AgentRegistry existente. El registro actual usa `id`, `name`, `capabilities`, `group`, `cost_weight`, `priority`, `healthy` y `meta`; una entrada sin capacidades es inválida. La resolución debe ser por capacidad y salud, no por nombre fijo.

### 4. Orquestador Auditor
Coordina ejecución y auditoría. Debe separar ejecución de verificación y no puede escribir el veredicto final. `VerdictAuthority` conserva la autoridad de PASS.

### 5. Frontend
Presenta estado, progreso, artefactos, evidencias y veredictos. No debe convertirse en autoridad de ejecución ni modificar el estado persistente sin pasar por la ruta canónica.

### 6. Tubería Router
Conecta Router → Command Center → AgentRegistry/Agente → Workflow/Kernel → Verification → Evidence → Sheriff → VerdictAuthority.

### 7. Orquestador
Ejecuta el DAG respetando dependencias, idempotencia, gates y loops de reparación. No debe saltar COPY-FIRST, WIRE, FORENSIC VERIFY ni VERDICT AUTHORITY.

## Flujo canónico

```text
INPUT
  ↓
ROUTER
  ↓
COMMAND CENTER
  ↓
AGENT REGISTRY / CAPABILITY RESOLUTION
  ↓
ORCHESTRATOR
  ↓
WORDflow KERNEL
  ↓
EXECUTION
  ↓
EVIDENCE
  ↓
FORENSIC AUDIT
  ↓
SHERIFF
  ↓
VERDICT AUTHORITY
  ↓
CLOSED | FIX LOOP
```

## Reglas duras

- GitHub es fuente persistente de verdad.
- Sandbox no es memoria persistente ni prueba de DONE.
- COPY-FIRST antes de GENERATE.
- Un handoff sin trazabilidad completa no equivale a DONE.
- El LLM puede analizar y proponer; no puede declarar PASS.
- Toda publicación requiere verificación remota.
- Todo cambio de estado relevante debe quedar trazado.
- No crear autoridades paralelas.
