# PIPELINE — Master Project NCT / Wordflow

## Qué es el PIPELINE

El PIPELINE es el **documento vivo (prompt ejecutabile)** del proyecto.

No es una explicación estática. Es la radiografía completa y verificable de todo el sistema:

- Wordflow (cara de trabajo diario)
- Capa de control externa
- Extensión de kernel (montable vía ABI)

Cada archivo dentro de `/PIPELINE/` tiene trazabilidad total de origen.
Cualquier instancia de Grok puede retomar el proyecto leyendo solo estos documentos + el commit actual.

**Regla de oro:**  
Lo que está DENTRO del PIPELINE = aprobado.  
Lo que falta = pendiente de auditoría.

## Estructura

```
PIPELINE/
├─ README.md                    ← este archivo
├─ 01_INTRO_METODO_Y_NORMAS.md  ← normas + método de trabajo
├─ 02_...                       ← se añaden uno a uno
└─ ...
```

## Cómo se usa

1. El Director entrega información por bloques (input block).
2. El ejecutor construye **una sola tarea** por salida.
3. Hace commit real en este repo.
4. Se detiene y espera "Ok".
5. Al final de cada lista de tareas emite claim CHAT_A_EXECUTOR v4.
6. CHAT_B_SHERIFF_AUDITOR verifica con evidencia real (tree, blob SHA, contenido).

## Memoria del proyecto

GitHub es la única memoria persistente.
No se confía en el contexto de la conversación.
Todo lo construido debe existir como commit real.
