# Guía de decisión: cómo integrar un bloque de código nuevo al kernel
**Basado en el Enchufe Universal v2.0 que ya construyó Fables (código real, no solo diseño)**

## 0. Lo que ya tienes construido (no lo repitas, úsalo)

Revisé los 3 archivos que subiste. Contienen un sistema ya funcional:

- **`ficha_contract_v2.py` / el schema JSON** — la "hoja de requisitos" que todo código nuevo debe rellenar antes de entrar al kernel.
- **`validator_v2.py`** — 36 reglas (22 antiguas + 14 nuevas) que comprueban automáticamente si esa hoja de requisitos está bien llena.
- **`UniversalPluginBus.enchufar()`** — el método que de verdad conecta el código nuevo al sistema, sin tocar nada existente.
- **`ContractGenerator.generate()`** — lee el código fuente que le des y extrae solo, automáticamente: qué funciones exporta, qué eventos emite/escucha, de qué depende.
- **`AdapterFactory.create()`** — genera el archivo puente (adaptador) que traduce ese código a las convenciones del kernel, sin modificar el original.
- **`PluginRegistry`** — asigna un "slot" numerado a cada plugin nuevo; nunca reescribe el slot de otro. Esto es, literalmente, tu idea de "Kernel 1 → Kernel 2 → Kernel 3 sin tocar el anterior", ya construida.

## 1. Los requisitos mínimos que un bloque de código debe cumplir (versión simple del schema)

Antes de decidir cómo integrarlo, necesitas poder responder estas 8 preguntas sobre el bloque de código:

1. **¿Qué hace?** → un identificador único (`artifact_id`) y una versión (`version`).
2. **¿En qué categoría cae?** → `pipeline` (procesa datos en una cadena), `transversal` (sirve a todo el sistema, ej. logging), o `acelerador` (optimiza algo puntual).
3. **¿Qué rol cumple?** → `source` (solo produce), `sink` (solo consume), `transform` (ambos), o `service`.
4. **¿Qué tipo de ejecución es?** → `code` / `llm` / `db` / `api` / `tool` / `agent`, y si es puramente determinista o mezcla LLM (`llm_ratio`).
5. **¿Es seguro correrlo?** → necesita declarar un sandbox (`container`/`process`/`none`) y un timeout máximo. Sin esto, se rechaza automáticamente (regla `I11_timeout` del validador).
6. **¿Se puede repetir sin romper nada?** → si se puede llamar más de una vez, debe declararse `idempotente: true`, o el validador lo rechaza (`V09`).
7. **¿Qué pasa si falla?** → necesita al menos pensar en un `failover.sustituible_por` (una alternativa) o una compensación.
8. **¿Cómo se sabe que sigue vivo?** → un método de salud (`ping`/`http`/`exec`) y cada cuánto se revisa.

Si no puedes responder las preguntas 1, 4 y 5 con confianza, **el bloque no está listo para entrar todavía** — antes hay que investigarlo más, no forzarlo.

## 2. La instrucción de decisión (para dártela a ti mismo o a cualquier IA)

Copia esto tal cual como instrucción cuando le des un bloque de código a una IA para que decida cómo integrarlo:

```
INSTRUCCIÓN: INTAKE DE CÓDIGO EXTERNO AL KERNEL

Te voy a dar un bloque de código o un archivo. Tu tarea NO es explicarlo.
Tu tarea es decidir, con evidencia, cómo debe entrar al kernel.

PASO 1 — ANALIZA (nunca ejecutes el código todavía):
- Extrae qué funciones/clases exporta, sus firmas, y sus docstrings.
- Extrae de qué otras librerías o archivos depende.
- Busca llamadas peligrosas: os.system, subprocess.call, eval(, exec(.
  Si encuentras alguna, márcalo como REQUIERE_SANDBOX=container obligatorio.
- Determina si el código es puramente determinista, mezcla LLM, o es 100% LLM.

PASO 2 — RELLENA LA FICHA (las 8 preguntas de la sección 1 de esta guía):
- Si falta información para responder alguna, escribe [NO_DETERMINABLE] en
  vez de inventar el valor.

PASO 3 — VALIDA:
- Si hay algún [NO_DETERMINABLE] en artifact_id, ejecucion.kind, o
  seguridad.sandbox+timeout_ms: DETENTE. No se puede integrar sin esos 3.
- Para el resto de campos, aplica los defaults del Enchufe Universal v2.0
  (categoria:pipeline, perfiles:{todos habilitados}, repeticion:{max:1}).

PASO 4 — DECIDE ENTRE LAS 2 OPCIONES:

  OPCIÓN 1 — Integrar tal cual (sin modificar el código original) SI:
    a) Sus nombres de función ya siguen la convención del kernel
       (snake_case, tipado explícito), Y
    b) Su formato de entrada/salida ya coincide con el contrato que necesita
       consumir/exponer (mismo "datatype": family+type+version), Y
    c) No tiene llamadas peligrosas sin sandbox declarado.
    → Acción: genera SOLO la ficha (manifest) + un adaptador mínimo de
      "passthrough" que simplemente importa el archivo original sin cambiar
      su lógica. El archivo original NO se toca.

  OPCIÓN 2 — Adaptar antes de integrar SI:
    a) Los nombres, el estilo async/sync, o el formato de entrada/salida
       no coinciden con el contrato del kernel, O
    b) Le faltan declaraciones obligatorias (timeout, sandbox, idempotencia)
       que sí se pueden inferir o envolver sin tocar la lógica interna, O
    c) Necesita traducirse de otro lenguaje (Rust/Go/JS) al del kernel.
    → Acción: genera la ficha + un adaptador real que traduce nombres,
      envuelve la función con el timeout/sandbox que falta, y normaliza
      el formato de entrada/salida. El archivo original tampoco se toca —
      el adaptador vive en un archivo nuevo aparte.

  Si no cumple ni siquiera las condiciones mínimas de la OPCIÓN 2 (por
  ejemplo, código sin ninguna función clara, o que requiere reescritura
  completa de su lógica para ser seguro): RECHAZAR. No es una integración,
  sería reescribir desde cero con pasos extra — repórtalo como tal.

PASO 5 — CABLEA SIN TOCAR NADA EXISTENTE:
- Crea la ficha en su propio archivo.
- Crea el adaptador (Opción 1 o 2) en su propio archivo nuevo.
- Regístralo con un slot nuevo en el registry — nunca reemplaces un slot
  existente directamente, usa el flujo de shadow-test + swap si es un
  reemplazo de algo activo.
- Coloca el archivo adaptador en la carpeta destino según la categoría
  (pipeline/transversal/acelerador) y la etapa (E/P/S/T/A).

PASO 6 — ENTREGA:
- El código original, sin modificar, en su ubicación de origen (o vendored
  sin cambios si viene de otro repo).
- La ficha nueva.
- El adaptador nuevo.
- Un reporte de una línea: "OPCIÓN 1" o "OPCIÓN 2" y por qué.
```

## 3. Por qué esto no rompe nada al crecer (tu ejemplo de Kernel 1 → 2 → 3)

`PluginRegistry` ya funciona así: cada plugin nuevo recibe un **número de slot** propio. Cuando algo se reemplaza, no se borra — pasa a `DEPRECATED` si otros dependen de él, o se desactiva limpiamente si no. El `upgrade()` ni siquiera reemplaza en caliente sin antes probar la versión nueva en un "slot sombra" (`shadow_load` + `run_shadow_tests`) — solo si esas pruebas pasan, hace el swap atómico. Es exactamente tu diagrama de "Kernel 1 ➡️ Kernel 2 ➡️ Kernel 3, sin tocar el código anterior" — ya implementado, no hay que diseñarlo de nuevo.
