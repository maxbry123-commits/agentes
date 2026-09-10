# PARCHE DE RECUPERACIÓN — GROK / SOL — YAIWES 3 PASOS

**Repositorio:** `maxbry123-commits/agentes`  
**Rama:** `main`  
**Estado:** `READY_TO_RESUME_STRICT_3_STEPS`

## 1. LEER EN ESTE ORDEN

1. `📂 Bitácora stated JSON Craxy wall.json` — SIEMPRE FRESCO DESDE `main`.
2. `Readme arquitectura Yaiwes/HANDOFF-INTEGRACION-1-20.md`.
3. Este parche.
4. Estado físico del componente en `Core kernel Yaiwes/` y `Agente Yaiwes principal/`.

Si el texto histórico contradice el estado físico, manda `main` + evidencia.

## 2. LÍMITES ABSOLUTOS

```text
WORK_ROOT = Core kernel Yaiwes/
DESTINATION_ROOT = Agente Yaiwes principal/
MOTOR_ROOT = ➡️📂motores de descarga extracción copiado movimiento archivos agentes/
```

No escribir integración fuera de esas raíces. No usar motores de otro repo.

## 3. ÚNICO CONTRATO

```text
PASO 1 = ANALIZAR A/B/C + DESTINO
PASO 2 = MOVER CON MOTOR AUTORIZADO
PASO 3 = CABLEAR + PODA MÍNIMA SI HACE FALTA + MICROTEST
```

No existe Paso 4.

### Paso 1
Solo analizar función real y decidir A/B/C + destino exacto dentro de `Agente Yaiwes principal/`.

- A: agente/subagente.
- B: workflow/DAG/scheduler/queue/worker/runtime/orquestación.
- C: capacidad modular.

No mover. No cablear. No test. No arquitectura nueva.

### Paso 2
Mover exclusivamente con los motores canónicos de `➡️📂motores de descarga extracción copiado movimiento archivos agentes/`.

No LFS. No force. No script alternativo. No nuevo motor.

Si el componente ya fue movido y existe evidencia, no repetir.

### Paso 3
Cablear la capacidad real. Usar FABLES/Enchufe Universal donde corresponda. Podar solo con causa demostrada. Ejecutar el microtest funcional mínimo.

Si FAIL:
`causa exacta -> edición quirúrgica/poda mínima/fork solo si necesario -> repetir microtest`.

No convertir el error en una fase nueva.

## 4. PROTOCOLO CRAZY WALL

```text
READ fresh
→ nodo existente FREE?
→ YES: owner=GROK|SOL + lock=CLAIMED + checkpoint.before
→ ejecutar SOLO current_step
→ evidence + checkpoint.after
→ PASS/GAP
→ release
```

Si CLAIMED por otra IA: saltar. **No crear un nodo nuevo por iniciativa propia.**

## 5. NO AUTORIZADO

- nuevas fases;
- nuevas arquitecturas;
- refactor global;
- investigación sin GAP concreto;
- benchmarks;
- “100x”;
- nuevos motores;
- wrappers genéricos;
- poda ciega;
- documentación que sustituya ejecución;
- tocar nodo ajeno;
- PASS por carpeta/import/source_probe;
- mover otra vez un componente ya movido sin evidencia de pérdida.

## 6. CHECKPOINT DE SALIDA

Cada unidad termina con:

```text
node_id
owner
current_step
status PASS|GAP
classification A|B|C
source
target
evidence: ruta + commit/run/test/read-back
next_action
lock FREE cuando corresponda
```

## 7. ARRANQUE

```text
READ CRAZY WALL
→ READ HANDOFF
→ elegir primer nodo EXISTENTE + FREE
→ CLAIM
→ ejecutar su current_step
→ checkpoint/evidence
→ PASS o GAP
→ RELEASE
→ siguiente FREE
```

## 8. ENLACES

- Work root: https://github.com/maxbry123-commits/agentes/tree/main/Core%20kernel%20Yaiwes
- Destination: https://github.com/maxbry123-commits/agentes/tree/main/Agente%20Yaiwes%20principal
- Motors: https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82motores%20de%20descarga%20extracci%C3%B3n%20copiado%20movimiento%20archivos%20agentes
- Crazy Wall: https://github.com/maxbry123-commits/agentes/blob/main/%F0%9F%93%82%20Bit%C3%A1cora%20stated%20JSON%20Craxy%20wall.json
- Handoff: https://github.com/maxbry123-commits/agentes/blob/main/Readme%20arquitectura%20Yaiwes/HANDOFF-INTEGRACION-1-20.md
- This recovery: https://github.com/maxbry123-commits/agentes/blob/main/PARCHE-RECUPERACION-CORE-INTEGRACION-WATCHDOG.md
- Astra/Claude recovery: https://github.com/maxbry123-commits/agentes/blob/main/PARCHE-RECUPERACION-ASTRA-CLAUDE-YAIWES-3-PASOS.md
