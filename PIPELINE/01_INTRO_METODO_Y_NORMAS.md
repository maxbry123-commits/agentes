# PIPELINE 01 — Introducción + Método de Trabajo + Normas

**Fecha:** 2026-08-09  
**Estado:** ACTIVO  
**Commit de nacimiento:** se registrará en el siguiente claim  
**Autoridad:** Director (usuario) + CHAT_B_SHERIFF_AUDITOR

---

## 1. Qué es el proyecto

Sistema dual:

- **Wordflow** → cara de trabajo diario (code + cualquier tarea)
- **Capa de control externa** → núcleo determinista (contratos, Sheriff, Sentinela, Durable runtime, Council)
- **Extensión de kernel** → mismo motor montable vía ABI (sin tocar el kernel)

Objetivo: orquestación multi-agente determinista donde el LLM solo razona y el código decide cómo ejecutar.

Principio central:  
**Todo lo que se puede resolver con reglas fijas se resuelve con código, nunca con un modelo de lenguaje.**

---

## 2. Qué es el PIPELINE

El PIPELINE es el **master project vivo**.

Características obligatorias (según especificación NCT v2):

- Prompt viviente (se lee y funciona como instrucción ejecutable)
- Trazabilidad total de origen de cada afirmación
- Raíz estructural extendida (fuente + fase anterior + fase siguiente)
- Micro-diagrama horizontal + micro-diagrama transversal
- DEBE / NO DEBE explícito
- Explicación técnica + explicación simple (mismo contenido)
- Fuentes verificadas (nunca inventadas)
- Se divide en documentos pequeños (nunca un solo archivo gigante)
- Permite auditar y reemplazar partes

El PIPELINE es la memoria adicional del proyecto.  
GitHub es la memoria persistente.  
Cualquier instancia de Grok puede retomar el trabajo solo leyendo los archivos de `/PIPELINE/` + el último commit.

---

## 3. Normas de trabajo (inmutables)

1. **Una tarea = una salida**  
   Nunca se mezclan objetivos.

2. **Planificación primero (Cursor style)**  
   Mínimo tokens. Se planifica antes de escribir código.

3. **Materialización real**  
   Todo archivo debe existir en el repo `maxbry123-commits/agentes` con commit real.  
   Stubs no cuentan como 100%.

4. **Stop obligatorio**  
   Después de cada tarea: commit + push → se detiene → espera "Ok" del Director.

5. **Prohibido quedarse procesando**  
   Límite de tiempo y de tokens. Trabajo determinista.

6. **Formato de salida de tarea**  
   Solo:  
   `A1 100% terminada siguiente tarea A2`  
   Sin más comentarios.

7. **Al final de cada lista de tareas**  
   Se emite el claim completo en formato **CHAT_A_EXECUTOR v4** (yaml entregado por el Director).

8. **Auditoría**  
   CHAT_B_SHERIFF_AUDITOR es la única autoridad de verificación.  
   Claims falsos (archivos que no existen, SHA inventados, commits inventados) = desconexión.

9. **Sin alucinación**  
   Si no se puede obtener evidencia real (blob SHA, tree, contenido) → se deja el campo vacío o se marca `NO_DISPONIBLE`.

10. **GitHub = memoria**  
    No se confía en el contexto de la conversación. Solo en lo que está commiteado.

---

## 4. Formato de entrega obligatorio (CHAT_A_EXECUTOR v4)

Al final de cada lista de tareas el ejecutor debe emitir exactamente el DSL:

- E1 CONTEXT (task_id, repo, branch, base_commit, final_commit)
- E2 TASK_RESULT (status, result, incomplete_items)
- E3 CHANGES (files_added/modified/deleted + loc reales)
- E4 CODE_AND_TRACE (por cada archivo: path, blob_sha, size, origin, is_stub, functions)
- E5 DEPENDENCIES (si aplica)
- E6 TESTS (comandos reales + salida cruda)
- E7 ACQUISITION (si se descargó algo)
- E8 EVIDENCE_RAW (salida cruda de git log, ls-tree, rev-parse, etc.)
- E9 CLOSURE (campos machine + HUMAN_SUMMARY)

Nunca inventar SHA, size, path o resultado de comando.

---

## 5. Método de trabajo detallado

```
Director entrega input block
        ↓
Ejecutor planifica (Cursor style, mínimo tokens)
        ↓
Una sola tarea
        ↓
Escribe / modifica archivos
        ↓
Commit + push real en maxbry123-commits/agentes
        ↓
Actualiza el PIPELINE correspondiente (trazabilidad)
        ↓
Se detiene
        ↓
Espera "Ok"
        ↓
Siguiente tarea
```

Si la tarea es larga → se divide en partes (A1a, A1b...).

Al cerrar un bloque completo de tareas → claim CHAT_A_EXECUTOR v4 + espera auditoría.

---

## 6. Micro-diagrama horizontal del método

```
input_block → plan → tarea_unica → materializar_en_github → actualizar_PIPELINE → stop → await_Ok
```

## 7. Micro-diagrama transversal (gobierno)

```
DSL · DAG · Schema · Sheriff · Sentinela · Juez · Supervisor · Validador · Verificador · Orquestador
```

(Todos activos sobre cada tarea y sobre el claim final)

---

## 8. Trazabilidad de este documento

- Origen: instrucciones del Director (2026-08-09) + especificaciones PIPELINE NCT v2 + CHAT_A_EXECUTOR v4
- Creado por: ejecutor actual
- Próximo documento: PIPELINE 02 (cuando el Director entregue más información del perfil principal)

---

**Estado de este archivo:** listo para auditoría.
