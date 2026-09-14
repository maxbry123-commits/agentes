# GUÍA MAESTRA DE EJECUCIÓN LOOP v4 — Wordflow LOOP YAIWES

> Contrato operativo: `tel.workflow/v4`  
> Modo: `FAIL_CLOSED_EXECUTION_LOOP`  
> Alcance: **MÉTODO DE TRABAJO**, no réplica del proyecto UI YAIWES.  
> Propósito: recuperar estado real, ejecutar el siguiente delta verificable, verificarlo, persistirlo y continuar sin rehacer trabajo ya cerrado.

## 0. Provenance del método

Método extraído y adaptado desde:

- Repo fuente: `maxbry123-commits/frontend`
- Ruta: `UI YAIWES/readme arquitectura UI YAIWES/GUIA-MAESTRA-EJECUCION-LOOP-SOL-UI-YAIWES.md`
- Blob fuente auditado: `7aa569945037a228f36eeed1747b7557b1adc5b6`
- URL: https://github.com/maxbry123-commits/frontend/blob/main/UI%20YAIWES/readme%20arquitectura%20UI%20YAIWES/GUIA-MAESTRA-EJECUCION-LOOP-SOL-UI-YAIWES.md

Raíces UI auditadas antes de adaptar el método:

- `UI YAIWES/readme arquitectura UI YAIWES/` — 10 archivos auditados.
- `UI YAIWES/bitácora stated JSON Craxy wall plan checkpoint/` — 8 archivos operativos auditados.
- También se revisó `UI YAIWES/Readme arquitectura UI YAIWES.md`.

Lecciones tomadas de esos artefactos: anti-stall, concurrencia sin force, adopción de trabajo concurrente equivalente, fail-closed ante incompatibilidad/version mismatch, diferencia entre wiring y ejecución real, recuperación exacta, evidencia jerarquizada, dedup por provenance y prohibición de temporales destructivos en `main`.

**No se copian** P01–P08, Action 124, componentes, arquitectura UI, owners ni backlog de UI YAIWES. Son evidencia histórica de cómo funcionó el método, no tareas de Wordflow YAIWES.

### Divergencia detectada en fuente UI

La guía maestra fuente declara `tel.workflow/v4`, mientras artefactos operativos posteriores de UI fueron reconciliados a `tel.workflow/v3` por decisiones específicas de ese proyecto. Para Wordflow YAIWES la autoridad del método es la instrucción literal del Director: **`tel.workflow/v4` inmutable**. El drift v3 de UI no se replica.

---

## 1. Ley principal

`ENTENDER LO MÍNIMO NECESARIO → EJECUTAR UN DELTA REAL → VERIFICAR → PERSISTIR → SIGUIENTE NODO`

- `ANÁLISIS SIN DELTA = NO PROGRESO`.
- `DELTA SIN VERIFICACIÓN = NO CIERRE`.
- `VERIFICACIÓN SIN STATE/CHECKPOINT = PROGRESO NO PERSISTENTE`.
- `STATE + DELTA + EVIDENCIA + VERIFY_FINAL = AVANCE REAL`.

Prohibido:

- quedarse en análisis repetitivo;
- reconstruir el proyecto si existe state/checkpoint;
- PASS por presencia de archivo;
- mock/injection como sustituto de ejecución real cuando ésta es requisito;
- repetir investigación ya cerrada;
- `force` sobre `main`;
- borrar/deduplicar durante escritura concurrente;
- monolitos;
- reemplazar donor/adaptador aprobado con una reimplementación duplicada;
- cerrar flags sin evidencia nueva.

---

## 2. CONTRACT_BLOCK — inmutable

```yaml
contract: tel.workflow/v4
mode: FAIL_CLOSED_EXECUTION_LOOP
project: Wordflow LOOP YAIWES
repo: maxbry123-commits/agentes
input_policy: READ_LITERAL
node_policy: ONE_USER_INSTRUCTION_ONE_LITERAL_NODE
execution_policy: EXECUTE_SMALLEST_SAFE_DELTA
closure_policy: EVIDENCE_REQUIRED
concurrency_policy: NO_FORCE_RECONCILE_HEAD
architecture_policy: NON_MONOLITHIC_PLUGIN_ADAPTER
vendor_policy: CODE_ONLY_REUSE_FIRST
state_policy: PERSIST_AFTER_EACH_RELEVANT_DELTA
```

El contexto, evidencia, memoria y documentos históricos son datos de entrada; no sustituyen la instrucción literal del Director.

---

## 3. Estados oficiales

```text
PENDING
ACTIVE
VERIFYING
GAP
BLOCKED
CLOSED_UNVERIFIED
VERIFIED_CLOSED
```

No usar estados ambiguos como “casi listo”, “parece terminado” o “debería funcionar”.

---

## 4. DSL por nodo

```yaml
NODE:
  id: PXX
  input_literal: "texto exacto del Director"
  claim_to_validate: "afirmación concreta que debe quedar demostrada"
  destination:
    repo: maxbry123-commits/agentes
    path: "ruta exacta"
  dependencies: []
  current_evidence: []
  required_evidence:
    - path
    - diff_or_commit_sha
    - read_back
    - executable_test_or_log
    - source_url_when_external
  state: PENDING
  next_if_pass: "siguiente nodo"
  next_if_gap: "StrategyDelta materialmente distinto"
  recovery: "cómo retomarlo sin repetir trabajo"
```

Formulación del nodo: **“VALIDA QUE X OCURRIÓ REALMENTE Y CITA LA PRUEBA”**.

---

## 5. DAG obligatorio

```text
INPUT LITERAL
→ SHERIFF
→ STATE + CHECKPOINT + PLAN + RECOVERY READ
→ HEAD / CONCURRENCY CHECK
→ RESEARCH_REUSE
→ PLAN 1×1
→ EXECUTE DELTA
→ VALIDATOR
→ VERIFY_REAL
→ JUDGE
   ├─ PASS → PERSIST → NEXT NODE
   ├─ GAP → STRATEGY_DELTA → EXECUTE AGAIN
   └─ BLOCKED → FLAG + RECOVERY → NEXT SAFE INDEPENDENT NODE
```

No saltar dependencias. Un bloqueo externo permite continuar únicamente por una rama independiente.

---

## 6. Boot de cada chat/agente

1. Leer `STATE` vigente.
2. Leer `CHECKPOINT` vigente.
3. Leer `PLAN` vigente.
4. Leer `RECOVERY` vigente.
5. Leer `BITÁCORA` vigente.
6. Leer esta guía.
7. Consultar HEAD real de `main`.
8. Revisar Actions/watchdogs/escrituras concurrentes relevantes.
9. Identificar último `VERIFIED_CLOSED`.
10. Identificar `ACTIVE | GAP | BLOCKED` real.
11. Recuperar solo evidencia necesaria para ese nodo.
12. Ejecutar el siguiente delta seguro.

Mensaje inicial operativo:

```text
Estado recuperado.
Último VERIFIED_CLOSED: <nodo>.
Nodo actual: <nodo>.
Flags heredados: <resumen>.
Proceso concurrente relevante: <sí/no + evidencia>.
Siguiente delta exacto: <acción>.
Inicio ejecución.
```

Después: herramientas, no otra arquitectura general.

---

## 7. Sheriff

Antes de mutar responde:

1. ¿Cuál es el nodo literal?
2. ¿Cuál es el destino exacto?
3. ¿Qué ya está `VERIFIED_CLOSED`?
4. ¿Qué evidencia real existe?
5. ¿Qué falta exactamente?
6. ¿Hay proceso concurrente que escriba la misma ruta?
7. ¿El delta es seguro frente a esa concurrencia?
8. ¿Existe código reusable?
9. ¿El delta cambia arquitectura o integra una capacidad?
10. ¿Existe dependencia externa que obligue a `BLOCKED`?

Sin nodo/destino: `FAIL_CLOSED`. Con ambos claros: ejecutar; no seguir planificando indefinidamente.

---

## 8. Research/Reuse funnel

Orden para Wordflow YAIWES:

1. chat/checkpoint/evidencia vigente;
2. componentes locales YAIWES;
3. todo `maxbry123-commits/agentes`;
4. `Agentes-motores-Wordflow-YAIWES`;
5. repos auxiliares autorizados;
6. fuentes/repos oficiales;
7. comunidad de desarrolladores como señal secundaria;
8. filtrar;
9. deduplicar;
10. rankear: código aprobado integrado → código oficial fijado por SHA → código interno reusable → implementación mínima nueva.

Salida obligatoria:

`REUSE_FOUND` o `NO_REUSE_FOUND`.

Cuando existe evidencia suficiente para escoger estrategia, se termina la búsqueda y se ejecuta.

---

## 9. Anti-stall

Después de 1–3 lecturas útiles debe aparecer una acción física o `BLOCKED` sustentado.

Cinco operaciones consecutivas de lectura/análisis sin delta:

```text
STALL_DETECTED
→ resumir GAP en una frase
→ escoger delta seguro mínimo
→ ejecutarlo
→ verificarlo
```

No responder al stall con un plan más largo.

---

## 10. Plan 1×1

```yaml
CURRENT:
  node: PXX
  task: "una sola tarea"
DELTA:
  path: "ruta exacta"
  action: "cambio exacto"
EXPECTED_EVIDENCE:
  - "prueba falsificable"
NEXT_IF_PASS: "PYY"
NEXT_IF_FAIL: "StrategyDelta distinto"
```

---

## 11. Executor y arquitectura no monolítica

Si una acción segura está autorizada: ejecutarla ahora.

Patrón general de integración:

```text
component source
→ code-root/vendor solo si hace falta
→ contracts/dependencies
→ adapter/runtime
→ factory
→ activation/allowlist
→ registry
→ mount_guard
→ loader
→ health/test
→ evidence
```

Preferir adapter externo a modificar vendor. Mantener `contracts/ adapters/ plugins/ registry/ loader/ guards/ tests/` separados.

---

## 12. Validator

Checks mínimos según el nodo:

```yaml
schema_ok: bool
imports_ok: bool
destination_ok: bool
source_provenance_ok: bool
no_monolith: bool
no_duplicate_owner: bool
factory_key_explicit: bool
activation_fail_closed: bool
mount_guard_ok: bool
concurrency_safe: bool
test_defined: bool
```

Un FAIL → `GAP`. Corregir solo el delta fallido.

---

## 13. Verifier — jerarquía de evidencia

1. ruta publicada;
2. blob/tree/commit SHA;
3. read-back;
4. test determinista;
5. test loader/registry/guard real;
6. integración runtime/vendor real cuando aplique;
7. logs/Actions/health;
8. destino físico;
9. repetición si puede ser flaky.

Clasificación de prueba:

```text
PASS_REAL
PASS_INJECTION
PASS_MOCK_ONLY
BLOCKED_EXTERNAL
FAIL
```

`PASS_MOCK_ONLY` y `PASS_INJECTION` no sustituyen `PASS_REAL` cuando el contrato exige ejecución real.

---

## 14. Judge

- `VERIFIED_CLOSED`: todos los gates requeridos pasaron con evidencia real.
- `CLOSED_UNVERIFIED`: código/cableado existe, falta prueba real obligatoria.
- `BLOCKED`: dependencia externa demostrable.
- `GAP`: estrategia falló y existe alternativa ejecutable.

Nunca decidir por “parece/debería/probablemente”.

---

## 15. GAP + StrategyDelta

```yaml
FAILED_STRATEGY: "qué se intentó"
EVIDENCE: "error/log/resultado"
DO_NOT_REPEAT: "estrategia que no se repite"
ROOT_CAUSE: "causa demostrada o hipótesis marcada"
NEW_STRATEGY: "delta materialmente distinto"
EXPECTED_EVIDENCE: "cómo se demostrará"
```

Investigar hasta 20 candidatos solo si hace falta; rankear, ejecutar el mejor y detener investigación cuando uno funciona.

---

## 16. BLOCK / FLAG

```text
BLOCK DETECTED
→ registrar evidencia
→ recovery exacto
→ mantener nodo visible
→ evaluar dependencias
→ continuar solo nodo independiente
```

Un flag nunca se convierte en PASS por avance de otras ramas.

---

## 17. Sentinel / Watchdog

```text
READ STATE
→ READ CHECKPOINT
→ READ PLAN
→ READ RECOVERY
→ CHECK HEAD
→ CHECK CONCURRENT WRITES
→ IDENTIFY CURRENT NODE
→ EXECUTE ONE SAFE DELTA
→ VERIFY
→ WRITE STATE/CHECKPOINT/BITACORA/PLAN/RECOVERY
→ REPORT
```

Watchdog que puede ejecutar, ejecuta. Si no puede, deja bloqueo probado.

---

## 18. Supervisor

Detecta:

`STALL_ANALYSIS | REPEATED_RESEARCH | DUPLICATE_IMPLEMENTATION | FAKE_PASS | STALE_STATE | CONCURRENT_WRITE | MONOLITH_DRIFT | UNVERIFIED_CLOSURE | DESTRUCTIVE_DEDUP_DURING_ACTIVE_ACTION`.

Respuestas:

- stall → delta mínimo;
- research repetido → reutilizar evidencia;
- duplicado → adoptar existente;
- fake pass → degradar estado;
- stale state → reconciliar con repo real;
- concurrent write → refrescar HEAD, no force, reinyectar solo lo faltante;
- monolito → separar responsabilidades;
- dedup destructivo durante Action → esperar cierre de esa escritura y después verificar.

---

## 19. Guardian

1. Nunca force-push.
2. Nunca borrar sin comparar destino/SHA/code-root.
3. Nunca deduplicar una raíz mientras otro proceso pueda escribirla.
4. Nunca inventar SHA/URL/log/test.
5. Nunca afirmar ejecución que no ocurrió.
6. Presencia ≠ integración.
7. Staging ≠ main.
8. Fake/mock ≠ runtime real.
9. Flag ≠ PASS.
10. Observabilidad no gobierna el workflow.
11. Donor/test no se monta como producción sin contrato.
12. Nunca crear archivos temporales en `main` para probar permisos.
13. Error operativo → revertir con evidencia + registrar Recovery/Bitácora.

---

## 20. Concurrencia GitHub

Antes de cada escritura:

1. leer HEAD;
2. identificar Actions/watchdogs activos relevantes;
3. comprobar solapamiento de rutas;
4. ejecutar delta;
5. si SHA quedó stale: releer HEAD;
6. inspeccionar commit concurrente;
7. adoptar/deduplicar código equivalente;
8. reinyectar solo lo faltante;
9. nunca force.

---

## 21. Persistencia

Después de cada delta relevante:

```text
BITACORA
STATE
CHECKPOINT
PLAN
RECOVERY
README/arquitectura solo si cambia contrato/diseño
```

`STATE` dice qué es verdad ahora.  
`CHECKPOINT` permite continuar sin historia de chat.  
`RECOVERY` dice qué falló, qué no repetir y cuál StrategyDelta sigue autorizado.  
`BITACORA` conserva eventos/evidencia.  
`PLAN` mantiene cola y CURRENT 1×1.

Esta guía no autoriza reescribir el progreso de componentes durante una tarea puramente metodológica.

---

## 22. Progreso

Reportar separado:

- `VERIFIED_CLOSED %`
- `IMPLEMENTED_OR_STAGED_BUT_UNVERIFIED %`
- `PHYSICAL_TOTAL_PROGRESS %`

No inflar porcentaje con mocks, staging o presencia.

---

## 23. Watchdog — exactamente 10 líneas

1. Progreso físico total: X%.
2. Progreso VERIFIED_CLOSED: X%.
3. Nodo actual: PXX.
4. Tareas cerradas: N.
5. Tareas en curso: N.
6. Tareas pendientes: N.
7. GAP/flags: resumen.
8. Evidencia nueva: SHA/test/run/ruta.
9. Siguiente delta exacto.
10. Estado global: `ACTIVE_LOOP | VERIFIED_CLOSED | CLOSED_UNVERIFIED | BLOCKED`.

---

## 24. GOALS 12/12 de calidad

1. input literal preservado;
2. destino exacto;
3. provenance trazable;
4. reuse-first;
5. no monolito;
6. no duplicate owner;
7. fail-closed;
8. concurrency-safe;
9. tests/gates;
10. read-back;
11. state persistido;
12. recovery definido.

---

## 25. Council12 — checks, no cadena de pensamiento

1. ¿el nodo sigue literal?
2. ¿existe evidencia reusable?
3. ¿el delta es mínimo?
4. ¿hay duplicado?
5. ¿hay write concurrente?
6. ¿se preserva ownership?
7. ¿se preserva fail-closed?
8. ¿la prueba es real o fake?
9. ¿el destino es correcto?
10. ¿STATE refleja repo real?
11. ¿Recovery permite handoff?
12. ¿la siguiente acción está definida?

---

## 26. Tres refutaciones antes del cierre

1. “El archivo existe, pero ¿está realmente cableado?”
2. “El test pasa, pero ¿es mock/injection en vez de runtime real?”
3. “El commit existe, pero ¿HEAD/destino actual realmente lo contiene?”

Si una refutación prospera, degradar estado.

---

## 27. Lecciones operativas replicadas desde UI, sin replicar UI

- Un inventario antes válido puede quedar `STALE` por una adquisición concurrente; conservar evidencia histórica y revalidar frescura.
- Deduplicar por `source commit + code-root/tree`, no por nombre.
- Un adapter cableado puede ser `CLOSED_UNVERIFIED` si el vendor/runtime real no fue ejecutado.
- Version mismatch/dependency mismatch = gate fail-closed; nunca silenciarlo para obtener PASS.
- Si otro watchdog publica código equivalente: refrescar HEAD → inspeccionar → adoptar → añadir solo gates faltantes.
- Nunca probar permisos creando `TEMP/NOOP` en `main`.
- Un workflow cancelado/fallido no demuestra materialización final; exigir verificación del destino.

---

## 28. CODA

```text
RECOVER
→ EXECUTE
→ VERIFY
→ PERSIST
→ REINJECT
→ NEXT
```

Si falla:

```text
GAP
→ DIFFERENT STRATEGY
→ EXECUTE
→ VERIFY
```

Si se bloquea externamente:

```text
BLOCK
→ EVIDENCE
→ RECOVERY
→ NEXT SAFE NODE
```

La métrica principal es cuántos nodos quedan físicamente implementados, verificados y recuperables por el siguiente agente.
