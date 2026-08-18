# PIPELINE 00 — MÉTODO DE TRABAJO + ARQUITECTURA DE RESPONSABILIDADES

**Fecha:** 2026-08-17 (actualizado LEY audit-5)  
**Estado:** LEY DE TRABAJO (inmutable hasta que Director la cambie)  
**Aplica a:** todo código y YAML del Wordflow / Capa de Control / extensiones kernel  
**Plan activo V1:** PIPELINE/52_V1_PLAN_49_TAREAS_METODO_Y_XRAY.md

---

## 1. Reglas de tamaño y edición

| Regla | Valor |
|-------|-------|
| Máx LOC por archivo | **≤ 300** |
| Organización | carpetas por responsabilidad, no monolitos |
| Edición | un archivo a la vez; no reescribir paquetes enteros |
| Tests | cada pieza nueva con evidencia CI cuando aplique |
| Almacenamiento | **GitHub = única verdad; prohibido sandbox como storage** |

---

## 2. Arquitectura canónica (no monolítica)

```
KERNEL (estable, pequeño)
  │
  ├── WordflowInstance A
  ├── WordflowInstance B
  └── WordflowInstance N

EXTENSIONS / CAPABILITIES (ficha.v2 enchufe)
```

- **WordflowInstance** = ejecución/proyecto aislado (goals, state, loops, evidence).
- **Extensión / Capability** = paquete cargable (motor, adapter, skill, connector). No es una instancia.
- Crear otro Wordflow **no** exige reescribir el kernel; solo config/DNA + registry.

---

## 3. Operación COPY-FIRST (código existente)

```
COPY/MOVE → HASH OK
IMPORTS / CONTRACT / DEPENDENCY
        ↓ FAIL
AGENT → PATCH / ADAPT / GENERATE (mínimo)
```

Prioridad: **COPY/MOVE → LINK/CONNECT → PATCH → ADAPT → GENERATE LAST**.  
Nunca regenerar código que ya existe y es compatible.

---

## 4. No mezclar configuración con ejecución

```
YAML  = contrato / política / definición
.py   = runtime genérico que interpreta cualquier contrato
```

Loops independientes bajo `loops/*.yaml`; executor genérico los interpreta.

---

## 5. Seis niveles de responsabilidad

```
WORDflow
       ┌────────────┼────────────┐
  DEFINITION     CONTROL      EXECUTION
       └────────────┼────────────┘
                  STATE → EVIDENCE → EXTENSIONS
```

| Nivel | Qué |
|-------|-----|
| 1 DEFINITION | workflow, schema, stages, loops |
| 2 CONTROL | sheriff, permissions, routing |
| 3 EXECUTION | actions, adapters, connectors |
| 4 STATE | queue, checkpoints, instance state |
| 5 EVIDENCE | events, trace, artifacts |
| 6 EXTENSIONS | capabilities, agents, skills, plugins |

---

## 6. Forensic X-Ray + mapa mental

- Todo componente con **ID único** (`WF.xx`, `FILE.xxx`, `CONN.xxx`, …).
- Estados: IMPLEMENTED | PARTIAL | MISSING | PENDING | PLACEHOLDER | DEPRECATED | EXTERNAL | UNKNOWN.
- Mapa mental cascada (estilo NCT/APEX): `→ Para qué` / `→ Sin esto`.
- HTML en GitHub al cerrar bloques de mapa (plan T41–T42).

---

## 7. Ratio determinista

- **90 %** código / YAML / reglas  
- **10 %** LLM solo vía IntelligenceGateway / Router (nunca vendor directo en loop)

---

## 8. Método operativo CHAT_A + LEY AUDIT-5 (2026-08-17)

1. Planificación tipo Cursor (mínimo tokens)  
2. Una tarea = una salida  
3. Archivos ≤ 300 LOC  
4. Commit real en GitHub → paro  
5. Claim con path + evidencia; enlaces que abren el archivo  
6. No inventar archivos ni commits  
7. PIPELINE = memoria del proyecto  
8. Formato CONTROL DE TRABAJO en cada salida  

### LEY AUDIT-5 (obligatoria)
- Cada **5 tareas terminadas** (o antes si la tarea es grande / multipart):
  1. Auditar método de trabajo + PIPELINE completo
  2. Auditoría forense de las 5 tareas (100%)
  3. Detectar gaps → corregir → mejorar 10x
  4. Actualizar arquitectura + historia + bitácora
  5. **NO avanzar** a la siguiente tarea de la lista hasta que la revisión y gaps estén 100% resueltos
  6. Esta auditoría se inserta como **tarea adicional** en la lista
- Si la tarea es grande o tiene muchas partes → aplicar la auditoría + refutación + mejora 10x **inmediatamente**, sin esperar a la 5ª.

### Lista de tareas — formato obligatorio
- Debe llevar **trazabilidad de documentos** (origen, ancla, path, doc fuente) por cada tarea.
- El formato de *salida* (CONTROL DE TRABAJO) **no es** la lista de tareas.
- La lista completa vive en PIPELINE (52 o TAREAS_ACTUAL) y se presenta con trazabilidad cuando se pide.

---

## 9. V1 vs V1.1

| En V1 (49 tareas) | En V1.1 |
|-------------------|--------|
| Kernel multi-instancia + extensions | Fusión Minimax/Kimi NCT completa |
| C100 puntos Director 100% | Fetch real masivo HF |
| Code path + deploy contrato + mapa X-Ray | Expansión 85 contratos literales |

**Fuente:** Director 2026-08-10 + ampliación 2026-08-17 (multi-instancia, COPY-FIRST, X-Ray, plan 52, LEY AUDIT-5).
