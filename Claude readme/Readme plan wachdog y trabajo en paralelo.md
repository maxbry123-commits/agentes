# 📂 WATCHDOG YAIWES — MÉTODO ESTRICTO DE 3 PASOS

**Repositorio:** `maxbry123-commits/agentes`  
**Coordinador:** `➡️ sol osquestador plan`  
**Estado:** `ACTIVE_STRICT_3_STEPS`

## REGLAS DE ALCANCE

```text
WORK_ROOT = Core kernel Yaiwes/
DESTINATION_ROOT = Agente Yaiwes principal/
MOTOR_ROOT = ➡️📂motores de descarga extracción copiado movimiento archivos agentes/
```

No hay otro lugar de trabajo, destino ni motores autorizados.

## AL ACTIVAR CUALQUIER WATCHDOG

```text
READ Crazy Wall fresco
→ READ notas de ➡️ sol osquestador plan
→ revisar owner/lock/current_step/next_action
→ CLAIM solo nodo existente FREE
→ ejecutar SOLO current_step
→ checkpoint.after + evidence
→ PASS/GAP
→ RELEASE
```

Crazy Wall fresco manda sobre notas antiguas. Si no existe nota nueva del coordinador, continuar `current_step/next_action`; no esperar ni inventar trabajo.

## PASO 1 📌 — ANALIZAR A/B/C + DESTINO

Analizar función real y decidir destino exacto bajo `Agente Yaiwes principal/`.

- **A** = candidato agente/subagente SOLO si existe valor único de kernel aprobado.
- **B** = workflow/DAG/scheduler/queue/worker/runtime/orquestación determinista.
- **C** = tool/microservicio/adapter/memoria/policy/router/componente/capacidad modular.

### Regla DE-KERNEL para componentes que vienen como agentes

YAIWES no adopta otra cabeza/kernel por defecto.

```text
AGENTE UPSTREAM
→ identificar valor real
→ ¿puede extraerse como workflow/tool/microservicio/componente?
   SÍ → podar/descapitar kernel y clasificar B o C
   NO  → 🤯🤯🧠🧠🧠 KERNEL_VALUE_REVIEW
```

`KERNEL_VALUE_REVIEW` debe incluir componente + valor único + evidencia + razón por la que no puede reducirse a B/C. Se envía a `➡️ sol osquestador plan`, que lo presenta al usuario. No integrar otro kernel sin decisión del usuario.

Prohibido mover/cablear/testear en Paso 1.

## PASO 2 📌 — MOVER CON MOTOR

Mover desde `Core kernel Yaiwes/` al target decidido usando únicamente `MOTOR_ROOT`.

Si MOVE ya está verificado, **NO repetir**.

Cierre mínimo: `source -> motor canónico -> target -> hash/read-back`.

Prohibido cablear/podar/testear, LFS, force, scripts alternativos y motores nuevos.

## PASO 3 📌 — CABLEAR + PODA MÍNIMA + MICROTEST

Cablear la capacidad real. FABLES/Enchufe Universal donde aplique. Podar solo por causa concreta.

### Microtest correcto

Probar la **frontera funcional mínima** que YAIWES realmente usará; no compilar/testear todo el proyecto upstream salvo que esa sea la frontera real.

FAIL:
`causa exacta -> edición quirúrgica -> repetir MISMO microtest`.

PASS solo con evidencia real.

### No confundir fallos

- `COMPONENT_FAIL` → reparar componente/adaptador dentro de STEP3.
- `PUBLISH/WORKFLOW_FAIL` con microtest PASS → reparar únicamente publicación/orquestación; **NO reabrir el componente**.

## FAST PATH — LECCIÓN DEL CIERRE 1–20

1. Leer estado físico fresco.
2. Saltar pasos ya verificados; nunca rehacer MOVE válido.
3. Atacar solo el GAP exacto del paso actual.
4. Microtest mínimo específico de la capacidad real.
5. Reparación quirúrgica; no refactor global.
6. PASS funcional y persistencia son gates distintos: arreglar el que falló, no ambos.

## TODO LO DEMÁS = NO_AUTORIZADO

- Paso 4 o fases nuevas;
- otra arquitectura/kernel/cabeza sin aprobación;
- refactor global;
- benchmark/100x;
- investigación lateral sin GAP concreto;
- nodos/componentes nuevos por iniciativa propia;
- motores nuevos o movimiento manual;
- wrappers genéricos;
- poda masiva;
- tocar nodo `CLAIMED` por otra IA;
- PASS por presencia/import/source_probe;
- escribir integración fuera de las tres raíces autorizadas.

## LOOP DEL WATCHDOG

```text
CRAZY WALL → NOTA COORDINADOR → PICK FREE → CLAIM
→ STEP1 | STEP2 | STEP3 según current_step
→ EVIDENCE → PASS/GAP → RELEASE → NEXT FREE
```

El Watchdog supervisa y ejecuta; no inventa trabajo.

## ESTADO DE LA COLA NUEVA

Después de los 20 cerrados existen **7 nodos N21–N27**:
- PASS: N22 Hatchet, N24 Redis.
- GAP/PENDIENTES: N21 Dagu, N23 PostgreSQL, N25 Workalendar, N26 gVisor, N27 pgvector.

Total pendiente actual: **5 componentes**.

## ENLACES

- Work root: https://github.com/maxbry123-commits/agentes/tree/main/Core%20kernel%20Yaiwes
- Destination: https://github.com/maxbry123-commits/agentes/tree/main/Agente%20Yaiwes%20principal
- Motors: https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82motores%20de%20descarga%20extracci%C3%B3n%20copiado%20movimiento%20archivos%20agentes
- Handoff 1–20: https://github.com/maxbry123-commits/agentes/blob/main/Readme%20arquitectura%20Yaiwes/HANDOFF-INTEGRACION-1-20.md
- Crazy Wall: https://github.com/maxbry123-commits/agentes/blob/main/%F0%9F%93%82%20Bit%C3%A1cora%20stated%20JSON%20Craxy%20wall.json
- Machine plan: https://github.com/maxbry123-commits/agentes/blob/main/Core%20kernel%20Yaiwes/Crack%20wall%20bit%C3%A1cora%20stated%20JSON/PLAN-WATCHDOG-PROGRAMMING-V2.json
- Notas coordinador SOL 1/2/3: https://github.com/maxbry123-commits/agentes/blob/main/Core%20kernel%20Yaiwes/Crack%20wall%20bit%C3%A1cora%20stated%20JSON/NOTAS-ENCARRILAMIENTO-SOL-1-2-3.md

**Nota:** los dos parches de recuperación solicitados para Grok/Sol y Astra/Claude fueron entregados en el chat; no se usa un enlace a un parche Astra/Claude inexistente en el repo.
