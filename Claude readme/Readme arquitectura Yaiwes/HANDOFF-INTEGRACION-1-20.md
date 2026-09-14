# HANDOFF — YAIWES — INTEGRACIÓN ESTRICTA DE 3 PASOS

**Repositorio único:** `maxbry123-commits/agentes`  
**Rama:** `main`  
**Estado:** `ACTIVE_3_STEP_STRICT`  
**Para:** Grok / GPT-5.6 Sol / Astra / Claude

## 0. TRES INVARIANTES — NO INTERPRETAR

1. **Único lugar de trabajo:** `Core kernel Yaiwes/`
2. **Único destino del código integrado:** `Agente Yaiwes principal/`
3. **Único sistema autorizado para descargar, extraer, copiar o mover:** `➡️📂motores de descarga extracción copiado movimiento archivos agentes/`

Todo cambio fuera de esas reglas está **NO_AUTORIZADO**.

## 1. CRAZY WALL ANTES DE CUALQUIER CAMBIO

Fuente compartida: `📂 Bitácora stated JSON Craxy wall.json`.

Antes de tocar un componente:

```text
READ Crazy Wall fresco desde main
→ comprobar owner/lock
→ si CLAIMED por otra IA: NO TOCAR, elegir otro nodo ya existente
→ si FREE: owner=<IA> + lock=CLAIMED + checkpoint.before
→ ejecutar solamente el paso actual
→ evidence + checkpoint.after
→ PASS/GAP
→ liberar lock cuando corresponda
```

**Prohibido crear trabajo nuevo por iniciativa propia.** Solo se trabaja sobre componentes/nodos ya presentes en `Core kernel Yaiwes/` o ya registrados en Crazy Wall.

## 2. CONTRATO ÚNICO — EXACTAMENTE 3 PASOS

```text
PASO 1 — ANALIZAR A/B/C + DESTINO
PASO 2 — MOVER CON MOTOR AUTORIZADO
PASO 3 — CABLEAR + PODA MÍNIMA SI ES NECESARIA + MICROTEST
```

**No existe Paso 4.**

### PASO 1 📌 — ANALIZAR A/B/C + DESTINO

Leer solo el código/README mínimo necesario del componente dentro de `Core kernel Yaiwes/`.

- **A = AGENTE/SUBAGENTE:** autonomía, goal/lifecycle/tools/context propio.
- **B = MOTOR DE TRABAJO:** workflow, DAG, scheduler, queue, worker, durable runtime, loop/orquestación.
- **C = CAPACIDAD MODULAR:** memoria, storage, schema, policy, router, sandbox, validator, herramienta u otra capacidad reutilizable.

Salida obligatoria:

```text
component -> A|B|C -> destino exacto dentro de Agente Yaiwes principal/ -> motivo corto
```

En Paso 1 está prohibido mover, cablear, podar, testear, crear adapters, crear motores o diseñar arquitectura nueva.

Si no se demuestra A/B/C o destino: `GAP_DESTINATION`. No adivinar.

### PASO 2 📌 — MOVER CON EL MOTOR

Mover únicamente desde `Core kernel Yaiwes/` hacia `Agente Yaiwes principal/` usando exclusivamente:

`➡️📂motores de descarga extracción copiado movimiento archivos agentes/`

Para MOVE usar el motor canónico de movimiento allí existente. Para descarga/extracción/copia, usar únicamente los motores de esa misma raíz cuando el nodo explícitamente lo requiera.

Salida obligatoria:

```text
source -> motor autorizado -> target -> hash/read-back
```

Si el componente ya está físicamente en el destino correcto y existe evidencia: **NO repetir MOVE**.

En Paso 2 está prohibido cablear, podar, testear, usar LFS/force, escribir scripts alternativos o crear motores nuevos.

### PASO 3 📌 — CABLEAR + PODA MÍNIMA + MICROTEST

Objetivo único: hacer que la capacidad real funcione dentro de YAIWES.

```text
cablear capacidad real
→ FABLES / Enchufe Universal obligatorio donde aplique
→ crear/corregir solo adapter/port/WIRING mínimo necesario
→ podar SOLO si existe una causa concreta
→ microtest funcional mínimo
→ PASS | GAP
```

Reglas:
- `REUSE > PATCH > ADAPT > GENERATE`.
- Conservar upstream salvo necesidad demostrada.
- `source_probe`, carpeta presente o import aislado NO son PASS.
- Si el microtest falla: localizar causa exacta → edición quirúrgica / poda mínima / fork solo si es necesario → repetir el mismo microtest.
- Si la evidencia demuestra que el destino o MOVE era incorrecto, volver únicamente al paso responsable; nunca crear una fase nueva.

## 3. NORMA ANTI-SOBREINGENIERÍA

Queda expresamente **NO_AUTORIZADO**:

- Paso 4 o fases adicionales;
- arquitecturas nuevas no requeridas por el nodo;
- refactor global;
- benchmarks o “100x”;
- investigación lateral sin GAP concreto;
- crear nuevos motores/downloader/copier/mover;
- crear nuevos nodos/tareas por iniciativa de la IA;
- documentación extensa en lugar de ejecutar;
- wrappers genéricos para simular integración;
- poda masiva;
- tocar un nodo CLAIMED por otra IA;
- cambiar código fuera de `Core kernel Yaiwes/` y `Agente Yaiwes principal/` como parte de esta integración.

## 4. CHECKPOINT MÍNIMO

```json
{
  "node_id": "...",
  "component": "...",
  "owner": "GROK|SOL|ASTRA|CLAUDE|null",
  "lock": "FREE|CLAIMED",
  "current_step": 1,
  "abc": null,
  "target": null,
  "checkpoint": {"before": null, "after": null},
  "evidence": [],
  "status": "PENDING|PASS|GAP",
  "next_action": null
}
```

## 5. ESTADO Y CONTINUIDAD

Los primeros 20 ya tuvieron un MOVE histórico verificado; **no repetir ese MOVE salvo evidencia física de pérdida o destino incorrecto**.

Evidencia histórica de MOVE 20/20:
- run `34445710787`
- job `102771861495`
- commit `a3cf705f58f95cce65d1c230cb00abcab39732b2`

Dagu fue trabajado posteriormente por Grok y el Crazy Wall fresco debe prevalecer sobre cualquier estado escrito aquí.

Regla de verdad:
`main físico + evidencia > Crazy Wall > Handoff histórico > inferencia`.

## 6. ARRANQUE PARA CUALQUIER IA

```text
1 READ 📂 Bitácora stated JSON Craxy wall.json
2 READ este HANDOFF
3 READ el parche de recuperación de su rol
4 elegir nodo EXISTENTE y FREE
5 CLAIM + checkpoint.before
6 ejecutar PASO 1, PASO 2 o PASO 3 según current_step
7 evidence + checkpoint.after
8 PASS/GAP + RELEASE
9 siguiente nodo FREE
```

## 7. ENLACES CANÓNICOS

- Trabajo: https://github.com/maxbry123-commits/agentes/tree/main/Core%20kernel%20Yaiwes
- Destino: https://github.com/maxbry123-commits/agentes/tree/main/Agente%20Yaiwes%20principal
- Motores: https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82motores%20de%20descarga%20extracci%C3%B3n%20copiado%20movimiento%20archivos%20agentes
- Crazy Wall: https://github.com/maxbry123-commits/agentes/blob/main/%F0%9F%93%82%20Bit%C3%A1cora%20stated%20JSON%20Craxy%20wall.json
- Handoff: https://github.com/maxbry123-commits/agentes/blob/main/Readme%20arquitectura%20Yaiwes/HANDOFF-INTEGRACION-1-20.md
- Recovery Grok/Sol: https://github.com/maxbry123-commits/agentes/blob/main/PARCHE-RECUPERACION-CORE-INTEGRACION-WATCHDOG.md
- Recovery Astra/Claude: https://github.com/maxbry123-commits/agentes/blob/main/PARCHE-RECUPERACION-ASTRA-CLAUDE-YAIWES-3-PASOS.md
