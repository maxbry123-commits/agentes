---
# REFUTACIONES — 3 roles atacan la propuesta

## R1 — Adversario (romper seguridad)

**Ataques:**

1. **Scope Lock se rompe** si el agente hace `docker exec` desde adentro.
   → Solución: capability drop + seccomp profile + red `none` por default.

2. **Hash de goal_lock no detecta prompt injection** del usuario.
   → Solución: el Director (Max) tiene un canal separado; el input del usuario se trata como data, no como instrucción. La plantilla se valida contra esquema, no se interpreta libre.

3. **Sandbox escape** vía volumen compartido o variable de entorno.
   → Solución: docker `--read-only` salvo `/work`, `--tmpfs /tmp:size=100m`, env pass-through explícito (whitelist), scrub de secrets en logs.

4. **Consenso 2-de-3** puede ser manipulado si 2 modelos comparten el mismo proveedor.
   → Solución: consensus.py exige modelos de proveedores distintos (Claude + Mimo + OpenCode, todos backends diferentes).

5. **Telegram + DLQ** exponen el goal a un canal externo.
   → Solución: el mensaje de escalation solo contiene `node_id + attempts + last_error`, nunca el código fuente.

**Gaps residuales:** ninguno bloqueante; quedan como P1 (hardening continuo).

---

## R2 — Escéptico (romper determinismo)

**Ataques:**

1. **G7 dice "misma entrada = misma salida"**, pero Claude/Mimo son estocásticos.
   → Solución: el output se valida contra **contrato** (required_fields, status, schema), no se exige bit-exact. El Juez mide cumplimiento de constraints, no igualdad textual.

2. **Baseline regression** compara `status` no payload → cambios cosméticos pasan.
   → Solución: añadir hash del diff al baseline; regression compara `diff_hash` y rechaza si cambia sin GO explícito del Director.

3. **Sandbox no determinista**: mismo código puede dar output distinto por clock/temp files.
   → Solución: docker `--env TZ=UTC`, `--read-only`, `/work` es un tmpfs con hash determinista por contenido.

4. **Replay** desde workflow_state puede diverger si cambió el código del orquestador.
   → Solución: versionar el orquestador (git SHA) en el state; rechazar replay si SHA difiere.

5. **Loop repair** no acotado si Mimo entra en bucle.
   → Solución: F15 con counter==2 escala; F14 con counter<2 siempre va a F7 con prompt que incluye "this is repair attempt N of 2, if you fail again, escalate".

**Gaps residuales:** stochasticidad acotada por contrato, no eliminada. Aceptable por diseño.

---

## R3 — Pragmático (romper economía)

**Ataques:**

1. **16 pasos de razonamiento por nodo × N nodos = latencia y tokens brutales.**
   → Solución: el loop R1-R16 se ejecuta **UNA vez por goal** (no por nodo). Los nodos individuales solo pasan por R8-R13 (assign + inject + await + collect + validate + verify). R4 carga memoria, no razona.

2. **3 sandboxes paralelos en consensus** = 3× costo de inferencia.
   → Solución: consensus opcional (`consensus: "single" | "fast" | "full"` en input). `fast` usa 2 modelos; `single` salta consensus. Default `fast` para MVP.

3. **Tests completos en cada verify** = lento.
   → Solución: smoke tests primero (10s), full suite solo si smoke pasa. Caching de `pytest --co` para detectar tests sin ejecutarlos.

4. **Repair con Mimo Code** re-llama al modelo más caro cada vez.
   → Solución: Mimo es el más barato de los 3 en el setup; repair usa el mismo sandbox, no instancia uno nuevo (ahorra cold start).

5. **Sentinel escribe 5000 eventos** → I/O constante.
   → Solución: write-behind cada 5s, flush on shutdown. health.json refrescado solo en transiciones de estado, no cada nodo.

6. **Persistencia atómica en cada nodo** = I/O constante.
   → Solución: write-behind de workflow_state.json (cada nodo, pero asíncrono con throttle de 1s).

**Gaps residuales:** con `consensus: "single"` y sin repair, MVP corre en ~30s para un objetivo pequeño. Aceptable.

---

## Conclusión

Las refutaciones identifican 16 gaps. 14 tienen mitigación implementada en el MVP.
2 quedan como P1 backlog: replay con SHA check y consensus multi-provider enforcement.

Ningún gap bloquea el MVP funcional.
