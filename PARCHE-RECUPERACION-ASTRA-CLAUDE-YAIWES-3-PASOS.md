# PARCHE DE RECUPERACIÓN — ASTRA / CLAUDE — YAIWES 3 PASOS

**Repositorio:** `maxbry123-commits/agentes`  
**Rama:** `main`  
**Estado:** `READY_TO_RESUME_STRICT_3_STEPS`

## 1. PRIMERA ACCIÓN OBLIGATORIA

Antes de tocar código:

1. Leer `📂 Bitácora stated JSON Craxy wall.json` FRESCO desde `main`.
2. Leer `Readme arquitectura Yaiwes/HANDOFF-INTEGRACION-1-20.md`.
3. Leer este parche.
4. Confirmar que el nodo está `FREE`.
5. Reclamarlo con `owner=ASTRA` o `owner=CLAUDE`, `lock=CLAIMED`, `checkpoint.before`.

Si el nodo está reclamado por Grok, Sol, Astra o Claude: **NO TOCARLO**.

## 2. RAÍCES ÚNICAS

```text
ÚNICO LUGAR DE TRABAJO = Core kernel Yaiwes/
ÚNICO DESTINO DE CODE = Agente Yaiwes principal/
ÚNICOS MOTORES = ➡️📂motores de descarga extracción copiado movimiento archivos agentes/
```

No escribir integración en otro repo o raíz.

## 3. SOLO 3 PASOS

### PASO 1 📌 — ANALIZAR A/B/C + DESTINO

Analizar únicamente el componente reclamado.

- A = agente/subagente.
- B = workflow/DAG/scheduler/queue/worker/runtime/orquestación.
- C = capacidad modular.

Salida:
`component -> A|B|C -> destino exacto dentro de Agente Yaiwes principal/ -> motivo corto`.

No mover, cablear, testear, investigar componentes nuevos ni diseñar arquitectura.

### PASO 2 📌 — MOVER CON MOTOR

Mover solo el componente reclamado desde `Core kernel Yaiwes/` hacia el destino aprobado dentro de `Agente Yaiwes principal/` usando únicamente la raíz canónica de motores de `agentes`.

No crear motor. No LFS. No force. No script alternativo.

Si ya está movido con evidencia, verificar y no repetir.

### PASO 3 📌 — CABLEAR + PODA MÍNIMA + MICROTEST

Cablear únicamente lo mínimo para usar la capacidad real dentro de YAIWES.

- Reutilizar código existente primero.
- FABLES/Enchufe Universal obligatorio donde aplique.
- Crear/corregir solo adapter/port/WIRING mínimo.
- Podar solo si un archivo/duplicado causa un problema concreto.
- Ejecutar un microtest funcional mínimo.

Si FAIL:
`causa exacta -> edición quirúrgica/poda mínima/fork solo si necesario -> mismo microtest otra vez`.

PASS requiere evidencia real.

## 4. DIFERENCIA ASTRA / CLAUDE

La diferencia es solo de especialidad, **no de proceso**:

- ASTRA: puede hacer el análisis funcional A/B/C, compatibilidad y destino del nodo reclamado.
- CLAUDE: puede hacer revisión/corrección quirúrgica del código, adapter/port/FABLES y microtest del nodo reclamado.

Ambos siguen exactamente los mismos 3 pasos y no generan trabajo lateral.

## 5. TODO LO DEMÁS ESTÁ PROHIBIDO

No autorizado:
- inventar nuevos nodos;
- buscar nuevos componentes OSS por iniciativa propia;
- modificar frontend u otro repo;
- crear arquitectura, motor, framework o workflow nuevo;
- refactor global;
- benchmark/100x;
- documentación extensa;
- nuevas APIs salvo que el nodo explícitamente lo exija para su microtest;
- cambiar componentes que no sean el nodo reclamado;
- tocar versiones previas funcionales sin necesidad del nodo;
- declarar PASS por presencia/import/source_probe.

## 6. CIERRE DE CADA NODO

```text
checkpoint.after
+ evidence [ruta, commit/run, microtest, read-back]
+ status PASS|GAP
+ next_action concreto
+ release lock
```

Si no puede cerrar, dejar GAP concreto y liberar el nodo cuando otra IA pueda continuarlo.

## 7. ENLACES

- Work root: https://github.com/maxbry123-commits/agentes/tree/main/Core%20kernel%20Yaiwes
- Destination: https://github.com/maxbry123-commits/agentes/tree/main/Agente%20Yaiwes%20principal
- Motors: https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82motores%20de%20descarga%20extracci%C3%B3n%20copiado%20movimiento%20archivos%20agentes
- Crazy Wall: https://github.com/maxbry123-commits/agentes/blob/main/%F0%9F%93%82%20Bit%C3%A1cora%20stated%20JSON%20Craxy%20wall.json
- Handoff: https://github.com/maxbry123-commits/agentes/blob/main/Readme%20arquitectura%20Yaiwes/HANDOFF-INTEGRACION-1-20.md
- Grok/Sol recovery: https://github.com/maxbry123-commits/agentes/blob/main/PARCHE-RECUPERACION-CORE-INTEGRACION-WATCHDOG.md
- This Astra/Claude recovery: https://github.com/maxbry123-commits/agentes/blob/main/PARCHE-RECUPERACION-ASTRA-CLAUDE-YAIWES-3-PASOS.md
