# ✅ NOTA X-RAY — Claude 08

**Fuente:** `Readme arquitectura Yaiwes/Claude instrucciones Yaiwes/08_protocolo_cierre_kernel_simple.md`
**Blob SHA fuente:** `66f1cf4f051e3198170c83f5161f3cefc9c6de6e`
**Estado:** AUDITADO / PROPUESTA, no integrado.

## 4 pasadas
1. **Literal/método:** prioridad absoluta Nivel A: `tarea → decisión → ejecución → evidencia → fin`; una tarea aburrida E2E antes de Mythos/pool/watchdog.
2. **Código que falta / cómo conseguirlo:** arreglar primero imports y únicamente el bloqueador real encontrado; reutilizar `checkpoint.py`; cada caída exacta define el siguiente delta y nada más.
3. **Integración:** correr desde entrypoint real, repetir hasta E2E, detener expansión al primer cierre verificable.
4. **Cruce YAIWES:** hay una corrección documental: Claude ordena crear `goal_lock.py`, pero el README canónico y `PLAN_YAIWES_AGENTE_WORDFLOW.md` dicen que `goal_lock.py` ya es REAL y debe referenciarse/reutilizarse, no duplicarse.

## 6 lentes
Literal PASS · Arquitectura PRIORIDAD ALTA · Código DOCUMENTO PARCIALMENTE DESACTUALIZADO · Integración DELTA ÚNICO · Seguridad scope mínimo · Cierre E2E falsificable.

**Conclusión:** este documento define la secuencia de trabajo más rápida: cerrar primero Nivel A y usar evidencia del primer fallo para decidir exclusivamente el siguiente cambio.
