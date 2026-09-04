# Protocolo de cierre del Kernel — versión simple

## ¿Qué significa "el kernel está cerrado"?

Significa UNA sola cosa, no diez: **que puedas escribir una tarea, dársela al sistema, y que llegue de principio a fin sin que nadie tenga que arreglar nada a mano.**

No significa que estén las 40 fases de Mythos. No significa que esté el pool de 8 agentes en paralelo. Eso viene después. Cerrar el kernel es solo esto:

```
Entra una tarea → el sistema decide qué hacer → lo hace → guarda evidencia → termina
```

Si eso no pasa todavía, el kernel no está cerrado, sin importar cuántos archivos bonitos existan alrededor.

---

## Los 2 niveles de cierre (para no confundir "mínimo" con "completo")

### NIVEL A — Cierre mínimo (esto es lo que persigues AHORA)
Una tarea simple entra y sale completa, una sola vez, sin intervención manual.

### NIVEL B — Cierre completo (esto es la visión de Fables, para más adelante)
Todo lo del Nivel A, más: razonamiento de 40 pasos, pool de agentes en paralelo, memoria de 5 niveles, multi-API.

**No intentes B antes de tener A.** Es la razón por la que hoy sientes que "nada cierra" — se está apuntando al Nivel B sin haber probado el Nivel A ni una sola vez.

---

## Los 6 pasos exactos para llegar al Nivel A

1. **Arregla los 5 imports rotos** que ya identificamos (la Categoría A de la auditoría: `entrypoint.py`, `entrypoint_v1.py`, `bootstrap.py`, `execution_facade.py`, `orchestrator_v1.py` apuntan a archivos que existen, pero en otra carpeta). Esto es copiar-pegar una ruta correcta, nada más.

2. **Escribe SOLO 4 archivos de los que faltan de verdad** (no los 28, solo estos 4, porque son los únicos que bloquean el camino mínimo):
   - `mission.py` (qué es una tarea)
   - `goal_lock.py` (que el objetivo no cambie a mitad de camino)
   - `bootstrap.py` de `execution-orchestration/` (arranca el sistema)
   - `recovery.py` (qué hacer si algo falla — puedes reusar `checkpoint.py` que ya existe, no escribir de cero)

3. **Elige UNA tarea de prueba, la más simple posible.** Ejemplo: "lee este archivo de texto y cuenta cuántas palabras tiene." Nada de Mythos, nada de 40 pasos. Lo más aburrido posible.

4. **Corre esa tarea desde el entrypoint real** (`python -m agente`). Si se cae, anota exactamente en qué línea se cae — esa es tu próxima tarea a arreglar, ninguna otra.

5. **Repite el paso 4** hasta que la tarea de prueba llegue de principio a fin sin caerse.

6. **Cuando llegue de principio a fin una vez: para. Eso es el Nivel A cerrado.** No sigas agregando cosas todavía.

---

## Cómo validar que de verdad está cerrado (no "creo que sí")

Usa exactamente el mismo mini-prompt de auditoría forense que ya usamos antes, sin cambiar nada, y compara los resultados:

```
ANTES (auditoría vieja):
- Traza desde el entrypoint: CADENA INTERRUMPIDA
- Cobertura de tests: 0 en casi todo

DESPUÉS (vuelve a correr el mismo mini-prompt):
- Traza desde el entrypoint: ¿llega hasta el final ahora? (sí/no)
- ¿La tarea de prueba del paso 3 aparece en el log de ejecución con resultado exitoso? (sí/no)
```

Si las dos respuestas son "sí", el Nivel A está cerrado — con evidencia, no con la sensación de que "ya debería funcionar".

Si alguna es "no", ya sabes exactamente dónde se rompió, porque la auditoría te lo señala línea por línea, igual que la vez pasada.

---

## Qué NO hacer todavía (para no repetir el mismo error)

- No escribas `sentinel.py`, `council.py`, `supervisor.py`, `watchdog.py` todavía — son parte del Nivel B, y es exactamente lo que generó el desorden anterior: gobernanza sofisticada sin un camino simple que funcione debajo.
- No actives Mythos de 40 pasos en la tarea de prueba — usa la ruta más corta posible (score bajo, sin LLM si se puede).
- No sigas generando documentos de diseño nuevos hasta que el Nivel A esté cerrado y validado. Un documento más de arquitectura no te acerca al cierre — ejecutar sí.

---

## Resumen en una frase

**El kernel se cierra cuando una tarea aburrida corre de principio a fin una sola vez, comprobado por la misma auditoría — no cuando el diseño se ve completo en un documento.**
