CONFIRMACION 4x - MECANISMO DE BIBLIOTECA/REUSO ANTES DE ESCRIBIR CUALQUIER
SCHEMA O BLOQUE DE CODIGO (no solo componentes completos) - 2026-09-17

ACLARACION DEL DIRECTOR: el mecanismo de pip install git+ y biblioteca de
plantillas no es solo para evitar el ZIP corrupto - es la solucion
integral. Antes de escribir UN SCHEMA o UN BLOQUE DE CODIGO, usar este
sistema, no escribir de memoria del LLM. Despues: analizar arquitectura,
integrar, cablear (eso si es razonamiento/refactor).

## LOS 4 LUGARES VERIFICADOS

1. RESOLUCION-3-pendientes.md (formato template RAG) - correcto
   conceptualmente, corregido para aplicar a cualquier escritura, no solo
   componentes grandes.
2. SCHEMA-refactorizacion.md - faltaba un paso 0 explicito:
   BUSCAR_EN_BIBLIOTECA_PRIMERO, antes de VERIFY_BEHAVIOR_FIRST. Corregido.
3. SCHEMA-plantillas-RAG.md - ya decia consultar biblioteca antes de
   generar codigo, aclarado que aplica tambien a schemas.
4. runtime/src/core/reuse_selector.py (codigo real, 6.1KB) - implementa
   REUSE>PATCH>ADAPT>GENERATE historicamente para componentes completos.
   PENDIENTE: verificar si acepta schemas individuales como unidad de
   reuso - si no, es GAP de codigo real, no solo de documentacion.

## REGLA UNIFICADA

ANTES_DE_ESCRIBIR aplica a: schema nuevo, bloque de codigo, componente
completo.
Paso 0: BUSCAR_EN_BIBLIOTECA_RAG_Y_GITHUB, nunca escribir de memoria del LLM.
Si existe: REUSE o PATCH o ADAPT, nunca GENERATE directo.
Si no existe: GENERATE, y GUARDAR el resultado en la biblioteca.
Despues de escribir: ANALIZAR_ARQUITECTURA -> INTEGRAR -> CABLEAR (esto
si es razonamiento del agente, no busqueda).

## GAP DE CODIGO REAL DETECTADO
reuse_selector.py necesita confirmarse/extenderse para operar a nivel de
schema individual. Item de CODE real, lo resuelve Claude, no Sol.
