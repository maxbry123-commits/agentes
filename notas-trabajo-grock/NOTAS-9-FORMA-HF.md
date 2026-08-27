# NOTAS-9 A — forma PIPELINE-HF sin tareas HF

Fuente: Grupo-Trabajo-1/PIPELINE-HUGGINGFACE.md @ e0b5e7ae
Copiado: la FORMA. No modelos, no Spaces, no datasets, no HF1/2/3.

## Forma que se copia al molde
- Un archivo vivo. Anotar = aditivo (leer → append → read-back; lo viejo sigue).
- Cabecera: proyecto, estado, fecha.
- REGLA UNIVERSAL + ciclo por salida: investigar → verificar → deduplicar → GAP → 2ª pasada → X-Ray → registrar → PASS → siguiente.
- Salidas numeradas con PASS / EN CURSO / NO PASS. No 200 = PASS.
- BLOQUES A,B,C… para no mezclar tareas.
- Tags: CHAT APROBADO / EXISTENTE / NUEVO / GAP / DESCARTADO.
- LOOP: inventario → auditoría → dedupe → verify → xray → registrar → siguiente GAP.
- NO-STOP. GAP no cierra el archivo.
- Preflight 1.a.1. Ficha de cierre (id, commit, read-back, errores, STATUS).
- Procedimiento operador: recibir → leer → planificar → enviar → monitorizar → GAP → validar → registrar.
