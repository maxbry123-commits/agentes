# PIPELINE 00 — MÉTODO DE TRABAJO + ARQUITECTURA DE RESPONSABILIDADES

**Fecha:** 2026-08-10  
**Estado:** LEY DE TRABAJO (inmutable hasta que Director la cambie)  
**Aplica a:** todo código y YAML del Wordflow / Capa de Control / extensiones kernel

---

## 1. Reglas de tamaño y edición

| Regla | Valor |
|-------|-------|
| Máx LOC por archivo | **≤ 300** |
| Organización | carpetas por responsabilidad, no monolitos |
| Edición | un archivo a la vez; no reescribir paquetes enteros |
| Tests | cada pieza nueva con evidencia CI cuando aplique |

Motivo: poder editar, reemplazar o desactivar sin romper el resto.

---

## 2. No mezclar configuración con ejecución

```
YAML  = contrato / política / definición
.py   = runtime genérico que interpreta cualquier contrato
```

Incorrecto:
```
retry.py
recovery.py
watchdog.py   ← lógica duplicada
```

Correcto:
```
loops/retry.yaml      ← define el loop
loops/recovery.yaml
runtime/loop_executor.py  ← ejecuta CUALQUIER loop
```

---

## 3. Loops independientes

```
workflow/
├── workflow.yaml          # solo referencia
└── loops/
    ├── main.yaml          # ejecución normal
    ├── retry.yaml         # reintentos
    ├── recovery.yaml      # recuperación
    ├── evolution.yaml     # evolución de capacidades
    └── watchdog.yaml      # supervisión
```

`workflow.yaml` referencia:

```yaml
loops:
  - loops/main.yaml
  - loops/retry.yaml
  - loops/recovery.yaml
```

Un loop puede invocar otro **solo** si Schema/Sheriff lo autoriza (anti-ciclos).

---

## 4. Seis niveles de responsabilidad

```
WORDflow
                    │
       ┌────────────┼────────────┐
       ↓            ↓            ↓
  DEFINITION     CONTROL      EXECUTION
       │            │            │
       └────────────┼────────────┘
                    ↓
                  STATE
                    ↓
                 EVIDENCE
                    ↓
               EXTENSIONS
```

| Nivel | Qué | Ejemplos |
|-------|-----|----------|
| 1 DEFINITION | qué debe hacer | workflow, schema, stages, loops |
| 2 CONTROL | qué puede hacer | sheriff, permissions, resource limits, routing |
| 3 EXECUTION | cómo lo hace | actions, executors, adapters, connectors |
| 4 STATE | qué está ocurriendo | current state, queue, checkpoints, variables |
| 5 EVIDENCE | qué ocurrió | events, trace, artifacts, results, errors |
| 6 EXTENSIONS | qué se puede añadir | capabilities, agents, skills, plugins, adapters, runtimes |

---

## 5. Estructura de carpeta recomendada (por workflow/módulo)

```
workflow/
├── manifest.yaml
├── workflow.yaml
├── inputs/
│   ├── input.schema.yaml
│   └── output.schema.yaml
├── plan/
│   ├── stages.yaml
│   └── dependencies.yaml
├── loops/
│   ├── main.yaml
│   ├── retry.yaml
│   ├── recovery.yaml
│   └── watchdog.yaml
├── policies/
│   ├── sheriff.yaml
│   ├── resource.yaml
│   └── security.yaml
├── routing/
│   ├── router.yaml
│   └── model_policy.yaml
├── actions/                 # ≤300 LOC c/u
│   ├── acquire.py
│   ├── transform.py
│   ├── validate.py
│   └── publish.py
├── validators/
│   ├── schema_validator.py
│   └── integrity_validator.py
├── state/
│   └── state.yaml
└── tests/
```

Runtime genérico (fuera del workflow concreto):

```
runtime/
├── loop_executor.py
├── workflow_runner.py
└── ...
```

Extensions:

```
extensions/
├── capabilities/
├── agents/
├── skills/
├── plugins/
├── adapters/
├── connectors/
└── runtimes/
```

---

## 6. Diagrama de montaje

```
WORDflow
                       │
        ┌──────────────┼──────────────┐
        ↓              ↓              ↓
     Schema         Sheriff        Workflow
                                      │
                         ┌────────────┼────────────┐
                         ↓            ↓            ↓
                      Loop A       Loop B       Loop C
                         │            │            │
                         └────────────┼────────────┘
                                      ↓
                                  Executor
```

Sustituir un loop ≠ tocar schema.  
Sustituir sheriff ≠ tocar executor.  
Nueva capability = `extensions/capabilities/X` sin reconstruir kernel.

---

## 7. Ratio determinista

- **90 %** código / YAML / reglas (DEFINITION + CONTROL + EXECUTION determinista)
- **10 %** LLM solo donde el contrato lo permita (`llm_ratio`, estados H / D+H)

Sheriff y Schema bloquean LLM fuera de zona autorizada.

---

## 8. Método operativo CHAT_A

1. Planificación tipo Cursor (mínimo tokens)
2. Una tarea = una salida
3. Archivos ≤ 300 LOC
4. Commit real en GitHub → paro
5. Claim CHAT_A_EXECUTOR con evidencia
6. No inventar: si falta documento, pedir
7. PIPELINE = memoria del proyecto (actualizar al cerrar bloque)

---

## 9. Relación con Parte A hecha

`extensions/project_bootstrap/` ya sigue este espíritu:
- ktp / microflows / resource_brain / tests en carpetas separadas
- entrypoint orquesta sin monolito
- manifest = contrato Enchufe v2

Los siguientes módulos (loops Wordflow, sheriff, publisher, downloader) **deben** nacer ya con esta estructura.

**Fuente:** instrucciones Director 2026-08-10 (método trabajo + 5+1 niveles + loops independientes).
