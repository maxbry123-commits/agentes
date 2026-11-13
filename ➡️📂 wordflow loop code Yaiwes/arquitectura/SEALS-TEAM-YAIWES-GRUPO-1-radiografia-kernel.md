# SEALS TEAM YAIWES — GRUPO 1: Radiografía del Kernel

**Documento de diseño técnico — basado en evidencia real del repositorio `maxbry123-commits/agentes`**
Fecha: 2026-09-19
Autor: Claude (agente de documentación) para el Director

---

## 0. Método y fuentes consultadas

Este documento se basa **únicamente** en artefactos reales leídos del repositorio público `maxbry123-commits/agentes` durante esta sesión:

1. `Core kernel Yaiwes/CORE-KERNEL-COMPONENT-INVENTORY.md` (y su espejo `.json`) — inventario de 248 componentes.
2. `Core kernel Yaiwes/Readme de integración de componentes arquitectura Yaiwes.md` — metodología de integración.
3. `.gitmodules` (raíz del repo) — patrón real de montaje de submódulos (MiniMax-AI, MoonshotAI).
4. Listado de directorio de `Core kernel Yaiwes/` y de la raíz del repo vía GitHub Contents API.
5. Búsqueda de código (`GitHub code search API`, autenticada) y búsqueda web para el término "Enchufe Universal Fables" — 0 resultados en ambas.

---

## 1. Seals Team YAIWES no es un subagente — usa/replica su propio kernel

### (a) Mecanismo concreto, con base real
El README de integración establece una cadena de responsabilidad clara y **no jerárquica-de-subagente**:

> `Componente ➡️ adapter ➡️ contrato/Ficha v2 ➡️ WIRING/registry ➡️ Universal Plugin Bus`

En la arquitectura YAIWES tal como está documentada, un componente (o un agente como Seals Team) **no se "cuelga" de otro agente como hijo/subagente**; se conecta al **bus** a través de un contrato (Ficha v2) y un registro (WIRING/registry). Es decir, la arquitectura ya está diseñada, en su propio README oficial, como un modelo de **bus + registro + contrato**, no como un árbol de subagentes con un "padre" que delega y un "hijo" que ejecuta.

Esto da fundamento directo al requisito del Director: Seals Team YAIWES debe registrarse en el `WIRING/registry` del kernel con su propia Ficha v2 — un contrato que declara su identidad, su pool/rol dentro del Wordflow, y sus capacidades — en lugar de recibir instrucciones como si fuera un subagente de otro proceso. El inventario (`CORE-KERNEL-COMPONENT-INVENTORY.md`) usa exactamente esta lógica para clasificar cada uno de los 248 componentes por `Kernel Flag` (`YES` / `NO` / `HOLD_KERNEL_MATERIAL`), lo que confirma que la pertenencia al kernel es una propiedad **declarada y registrada**, no una relación de subordinación de ejecución.

Adicionalmente, la clasificación tipo A/B/C del README (A = agentes autónomos con ciclo de ejecución propio; B = orquestadores de workflows/DAGs; C = servicios deterministas modulares) da un vocabulario ya existente para declarar a Seals Team como **Tipo A** (agente autónomo con estado y ciclo propios) en su Ficha v2 — lo cual, por definición documental, excluye tratarlo como subagente de otro proceso.

### (b) Qué falta construir
- No existe todavía una Ficha v2 real y completa para Seals Team YAIWES.
- Falta un mecanismo runtime explícito que impida a otro proceso invocar a Seals Team como si fuera una llamada de subagente (p. ej. un guard en el registry que rechace invocaciones que no pasen por el bus).
- Falta definir explícitamente qué significa "activar un plugin/wordflow como extensión del kernel" en términos de código.

### (c) Flag honesto
Ninguno crítico; este punto tiene buena base documental real. El único vacío es que no vi el schema exacto de "Ficha v2" (solo su nombre y posición en la cadena).

---

## 2. Radiografía nativa de la raíz de YAIWES (dónde va cada archivo y por qué)

### (a) Mecanismo concreto, con base real
El inventario `CORE-KERNEL-COMPONENT-INVENTORY.md` **ya es**, literalmente, una radiografía de la raíz de `Core kernel Yaiwes/`. Su esquema de campos, confirmado por lectura directa:

| Campo | Ejemplo real observado |
|---|---|
| Índice | 1…248 |
| Nombre de componente | `A2A-Protocol`, `anydoc` |
| Ruta | `Core kernel Yaiwes/<nombre>` |
| Grupo | `ROOT`, `Componentes recuperados A/B` |
| Función | descripción del README del componente, o `README_FUNCTION_NOT_FOUND` |
| Kernel Flag | `YES` / `NO` / `HOLD_KERNEL_MATERIAL` |
| Crazy Wall Node | p.ej. `nodo 36, paso 1`, o sin nodo registrado |
| Estado | `PENDING_STEP1`, `IN_PROGRESS_STEP2_PROVENANCE`, `GAP` |
| Destino | ruta destino o `None` |

Confirmado por listado real: la raíz de `Core kernel Yaiwes/` contiene, entre otros, `A2A-Protocol`, `AIOS`, `AgentGuard`, `CAMEL`, `Claude-Code`, `Letta`, `LangGraph`, `Ray`, `Temporal`, `Semantic-Kernel`, `gVisor`, `seL4` (los últimos 3 marcados `HOLD_KERNEL_MATERIAL`), además de `Componentes recuperados A/B`, dos carpetas duplicadas de método de trabajo, y los README de integración e índice.

El campo **`Destino`** es el mecanismo de "dónde va cada archivo y por qué": cada fila del inventario es una instrucción de destino para un motor de movimiento de archivos. El campo `Estado` indica en qué paso del pipeline se encuentra cada componente antes de ser movido.

**Radiografía nativa = `CORE-KERNEL-COMPONENT-INVENTORY.json` (fuente de verdad estructurada) → un motor de movimiento (familia `➡️📂motores de descarga extracción copiado movimiento archivos agentes/`, confirmada real en la raíz del repo) que lee el campo `Destino` de cada entrada JSON y ejecuta el movimiento físico, actualizando `Estado` a completado.**

### (b) Qué falta construir
- Confirmar que el motor de movimiento específico consume el JSON del inventario campo por campo (aún no verificado línea por línea del código del motor).
- Falta un paso de "dry-run": aplicar el `Destino` de cada fila contra el sistema de archivos real, generando un plan antes de ejecutar, comparando contra `Estado`.
- Los 248 componentes no están 100% resueltos: hay entradas `README_FUNCTION_NOT_FOUND`, `GAP`, y sin nodo registrado — cerrar estos vacíos antes de operar con confianza total.

### (c) Flag honesto
El esquema del inventario y el listado real de la raíz están 100% verificados. El contenido interno exacto del motor de movimiento no se leyó línea por línea en esta sesión.

---

## 3. Convertir una skill en un schema — criterios y modelos de ejemplo

### (a) Mecanismo concreto, con base real
El README de integración describe el "X-Ray" que se aplica a cada componente antes de integrarlo, con tres ejes:

- **Función real**: ejecución de código real, clases y flujos de datos observables.
- **Objetivo**: problema que resuelve y capacidad que aporta a YAIWES.
- **Microflujo**: cadena horizontal entrada → procesamiento → salida.

Combinados con el esquema del inventario (Grupo, Kernel Flag, Estado, Destino) y la clasificación A/B/C, esto da un schema mínimo grounded en dos fuentes reales:

```json
{
  "skill_id": "string (único)",
  "nombre": "string",
  "tipo": "A | B | C",
  "funcion_real": "string",
  "objetivo": "string",
  "microflujo": { "entrada": "string", "procesamiento": "string", "salida": "string" },
  "kernel_flag": "YES | NO | HOLD_KERNEL_MATERIAL",
  "ficha_v2": { "...": "contrato de adapter, ver punto 1" },
  "wiring_registry_ref": "string | null",
  "estado": "PENDING_STEP1 | IN_PROGRESS_STEP2_PROVENANCE | GAP | DONE",
  "destino": "ruta | null"
}
```

**Modelos de ejemplo** (poblados con datos reales del inventario donde se confirmaron, placeholders explícitos donde no):

```json
{
  "skill_id": "anydoc",
  "tipo": "C",
  "funcion_real": "Librería Rust que convierte documentos (Word, PowerPoint, Excel, OpenDocument, RTF, EPUB, CSV, PDF) a Markdown GFM limpio",
  "objetivo": "Normalización de documentos heterogéneos a un formato único consumible por el kernel",
  "microflujo": { "entrada": "documento binario", "procesamiento": "parseo Rust", "salida": "Markdown GFM" },
  "kernel_flag": "SIN_CONFIRMAR",
  "estado": "SIN_CONFIRMAR_EN_ESTA_SESION",
  "destino": null
}
```

```json
{
  "skill_id": "seL4",
  "tipo": "C",
  "funcion_real": "Microkernel verificado formalmente",
  "objetivo": "Aislamiento y seguridad de bajo nivel para componentes críticos",
  "kernel_flag": "HOLD_KERNEL_MATERIAL",
  "estado": "SIN_CONFIRMAR_EN_ESTA_SESION",
  "destino": null
}
```

### (b) Qué falta construir
- Un validador de schema (JSON Schema formal) que rechace una skill sin los tres ejes del X-Ray completos.
- Regla explícita "skill sin Función documentada → Estado: GAP" (el valor existe en el inventario, pero no vi la regla automática).
- Formalizar el schema exacto de "Ficha v2" (mencionado pero sin schema propio localizado).

### (c) Flag honesto
Los tres ejes del X-Ray y los campos del inventario son 100% reales. El JSON de arriba es síntesis propia combinando ambos artefactos — no es cita de un schema ya escrito.

---

## 4. Uso exclusivo del plugin universal "Enchufe Universal Fables"

### (a) Lo que sí encontré
El README de integración tiene una sección explícita, **"Enchufe universal obligatorio"** (Sección 7):

> "Toda capacidad integrada se conecta mediante el patrón YAIWES de enchufe universal"
> `Componente ➡️ adapter ➡️ contrato/Ficha v2 ➡️ WIRING/registry ➡️ Universal Plugin Bus`
> "Universal Plugin Bus ➡️ destino arquitectónico ➡️ health/evidence"
> "el bus v2 contiene rutas de inspección dinámica; código no confiable se revisa"

### (b) Flag honesto — búsqueda exhaustiva del término exacto, CONFIRMADA con acceso completo al repo
**"Enchufe Universal Fables" NO existe en el repositorio**, confirmado con:
1. Búsqueda de texto completo del README de integración → 0 ocurrencias de "Fables".
2. Listado completo de la raíz del repo Y de `Core kernel Yaiwes/` → ningún archivo/carpeta contiene "enchufe", "fable" ni "universal" además de la sección ya citada.
3. GitHub Code Search API, con autenticación completa, `q: "Fables" repo:maxbry123-commits/agentes` → **0 resultados** (búsqueda real ejecutada, no bloqueada).

**Conclusión**: no existe evidencia de que "Enchufe Universal Fables" sea un componente o documento ya creado en este repo. Lo único real con ese espíritu es el **"Enchufe universal"** (Sección 7) apoyado en el **"Universal Plugin Bus"/"bus v2"**.

**PREGUNTA DIRECTA AL DIRECTOR**: ¿"Fables" es (i) un nombre en clave que vive fuera de este repo (otro repo, otra cuenta, o un documento aún no subido), o (ii) el nombre que quieres darle tú al "Enchufe universal" ya documentado en la Sección 7? Mientras no se aclare, Seals Team YAIWES debe usar el "Enchufe universal"/Universal Plugin Bus ya real como el mecanismo único de conexión.

### (c) Qué falta construir
- Resolver la pregunta anterior con el Director.
- Si se confirma que "Fables" = alias del bus ya existente, renombrar/documentar formalmente.
- Si es un componente nuevo, diseñarlo desde cero usando el patrón de la Sección 7 como base.

---

## 5. Podar, decapitar y convertir el wordflow

### (a) Mecanismo concreto, con base real
No encontré un procedimiento explícito de "poda" o "decapitación" en los README leídos. Base real aplicable por analogía directa:

- El campo **`Kernel Flag`** (`YES`/`NO`/`HOLD_KERNEL_MATERIAL`) es, en la práctica, un mecanismo de poda ya operativo: `NO` es candidato directo a poda; `HOLD_KERNEL_MATERIAL` es poda temporal/condicionada (así están `Semantic-Kernel`, `seL4`, `gVisor`).
- El patrón `Componente ➡️ adapter ➡️ Ficha v2 ➡️ WIRING/registry ➡️ Universal Plugin Bus` implica una "decapitación" natural: si un componente pierde su Ficha v2 o su entrada en el registry, queda automáticamente desconectado del bus. "Decapitar" un wordflow (quitarle su cabeza orquestadora Tipo B) equivaldría a retirar su Ficha v2 del registry sin borrar el código fuente, dejándolo como componente Tipo C (servicio pasivo) reutilizable.

### (b) Qué falta construir
- Criterios escritos de cuándo podar (¿duplicados? ¿componentes `GAP` sin avance tras N días?).
- Un motor que ejecute la poda (mover a cuarentena/archivo, no borrar, coherente con el patrón `Destino`).
- Procedimiento escrito de "decapitación" (convertir Tipo B en Tipo C) — diseñar desde cero usando la clasificación A/B/C ya real.

### (c) Flag honesto
Los términos "podar" y "decapitar" no aparecen literalmente en ningún archivo leído. La propuesta de mecanismo es una inferencia razonada del `Kernel Flag` y del patrón de conexión reales, no una cita textual.

---

## 6. Partes críticas del kernel: solo Claude (orquestador) las toca

### (a) Mecanismo concreto, con base real
El inventario distingue explícitamente la categoría **`HOLD_KERNEL_MATERIAL`**, aplicada a: **`gVisor`**, **`seL4`**, **`Semantic-Kernel`** — componentes de aislamiento/seguridad de muy bajo nivel. Es el candidato natural y ya documentado para "partes críticas que solo el orquestador toca".

**Regla concreta**: todo componente con `Kernel Flag: HOLD_KERNEL_MATERIAL` requiere revisión/aprobación de Claude antes de cualquier cambio de `Estado` o `Destino`; otros agentes (incluido Seals Team) pueden preparar el adapter/Ficha v2, pero no pueden ejecutar el `Destino` final sobre estos componentes. Coherente con la Sección 7: "el bus v2 contiene rutas de inspección dinámica; código no confiable se revisa".

### (b) Qué falta construir
- Un gate técnico (no solo convención de proceso) que impida a un agente no-Claude ejecutar el movimiento final de un componente `HOLD_KERNEL_MATERIAL`.
- Decidir si "crítico" = solo estos 3, o si se extiende a cualquier componente Tipo B orquestador central del propio kernel.

### (c) Flag honesto
La categoría y sus 3 miembros son reales y verificados. La regla "solo Claude toca, otros preparan" es interpretación mía del propósito de la categoría — no una política ya escrita con esas palabras exactas.

---

## 7. Descarga de componentes con los motores: reciben URL + nombre y estudian su colocación

### (a) Mecanismo concreto, con base real
El inventario confirma que cada uno de los 248 componentes ya tiene una `Ruta` real bajo `Core kernel Yaiwes/<nombre>` y un `Grupo` — exactamente el resultado esperado de "un motor que recibe URL + nombre y estudia su colocación": el resultado de ese estudio ya está serializado componente por componente.

- **Entrada**: URL del repo origen (patrón real confirmado en `.gitmodules`: 12 submódulos MiniMax-AI/MoonshotAI, montados bajo `➡️📂 wordflow loop code Yaiwes/wordflow_loop/agent_sources/<nombre>`) + nombre de componente.
- **Salida esperada**: fila nueva en `CORE-KERNEL-COMPONENT-INVENTORY.json` con `Ruta`, `Grupo`, `Función` (o `README_FUNCTION_NOT_FOUND` si falla la extracción), `Kernel Flag` inicial, `Estado: PENDING_STEP1`, `Destino: null` hasta decisión final.

El patrón `.gitmodules` (real, confirmado, 100% verificado) es la forma actual en producción de declarar "esta URL, con este nombre, va en esta ruta": `[submodule "<nombre>"]`, `path = <ruta>`, `url = <repo origen>`.

### (b) Qué falta construir
- El patrón `.gitmodules` solo cubre componentes montados como submódulo (MiniMax/Kimi); los 248 componentes de `Core kernel Yaiwes/` parecen vendorizados directamente, no como submódulos — no hay entradas `.gitmodules` para ellos.
- Confirmar el contenido interno exacto de los motores de descarga/extracción (carpeta real confirmada en la raíz: `➡️📂motores de descarga extracción copiado movimiento archivos agentes/`).
- Regla explícita de reintento/escalado cuando el README del componente no permite extraer `Función` automáticamente (hoy solo se registra `README_FUNCTION_NOT_FOUND`).

### (c) Flag honesto
El esquema resultante (inventario) y el patrón `.gitmodules` son 100% reales y verificados. El código interno de los motores no fue leído línea por línea en esta sesión.

---

## Resumen de trazabilidad

| # | Punto | Estado de grounding |
|---|---|---|
| 1 | No-subagente / propio kernel | Verificado (bus + Ficha v2 + clasificación A/B/C) |
| 2 | Radiografía de la raíz | Verificado (schema del inventario + listado real) |
| 3 | Skill → schema | Verificado (ejes del X-Ray) + síntesis propia del JSON |
| 4 | "Enchufe Universal Fables" | **NO encontrado, confirmado con code search autenticado** — solo existe "Enchufe universal"/Universal Plugin Bus (Sección 7) — pregunta directa al Director pendiente |
| 5 | Podar / decapitar wordflow | No encontrado literalmente — inferido del Kernel Flag y patrón de conexión |
| 6 | Partes críticas, solo Claude toca | Verificado el dato base (HOLD_KERNEL_MATERIAL, 3 componentes); regla de acceso es interpretación |
| 7 | Descarga con motores (URL + nombre) | Verificado el resultado esperado (inventario + .gitmodules) |

**Siguiente paso**: confirmar con el Director el significado de "Fables" (punto 4) antes de implementar el mecanismo de conexión definitivo, y decidir los criterios formales de poda (punto 5).
