# NOTAS-10 — SALIDA 1 / PASO 1
# Copia FORMA de PIPELINE-HUGGINGFACE.md sin tareas HF

Fuente: Grupo-Trabajo-1/PIPELINE-HUGGINGFACE.md @ e0b5e7ae SHA 1c7f97f0  
Quitado: salidas 1–10 de investigación, lista AI, datasets, adapters, TAREA 3 Meta/NVIDIA, HF1/HF2/HF3, aceleradores.

---

# PIPELINE (FORMA)

**Proyecto:** {{PROYECTO}}  
**Estado:** {{ESTADO}}  
**Actualización:** {{FECHA}}

## REGLA UNIVERSAL

Cada salida: investigar → verificar → deduplicar → resolver GAP → segunda pasada → X-Ray → registrar → PASS → siguiente salida.

## SALIDAS — PLANTILLA (vacía)

| Salida | Estado |
|---|---|
| S{{n}} | QUEUED / EN CURSO / PASS / NO PASS |

HTTP 200 ≠ PASS.

## PLAN DE TAREAS — NO MEZCLAR

BLOQUE A / B / C / … cada uno una clase de trabajo. No mezclar bloques.

## REGLA DE REGISTRO

Cada hallazgo indica origen:

**CHAT APROBADO** → decisión explícita del Director.  
**PIPELINE EXISTENTE** → ya registrado.  
**INVESTIGACIÓN NUEVA** → LOOP actual.  
**GAP** → falta verificación.  
**DESCARTADO** → no seguir.

Nunca convertir inferencia en aprobado. Nunca radar → aprobado sin verificación.

## NO-STOP

GAP → DIAGNOSTICAR → RESOLVER → VERIFICAR → REGISTRAR → CONTINUAR LOOP.  
No inventar. No detener por GAP. No mezclar. No ampliar alcance.

## LOOP

```text
INVENTARIO → AUDITORÍA → DEDUPLICACIÓN → INVESTIGACIÓN
 → VERIFICACIÓN INMEDIATA → SEGUNDA PASADA
 → X-RAY → REGISTRO → SIGUIENTE GAP → REPETIR
```

## ANOTAR = ADITIVO

1 Leer archivo completo  
2 SHA  
3 Conservar todo  
4 Añadir solo la sección nueva  
5 Commit  
6 Volver a leer  
7 El anterior sigue + lo nuevo está  
8 Solo entonces informar

## FICHA DE CIERRE

- tarea  
- Job/commit/ID  
- repositorio  
- estado final  
- comandos  
- prueba  
- logs  
- errores  
- correcciones  
- resultado  
- fecha  
- PASS o FAIL  

## PREFLIGHT 1.a.1 (antes de ejecutar)

1 Identidad/rama  
2 Permisos  
3 Objetivo sin ambigüedad  
4 Estado inicial registrado  
5 Si GAP de recurso: LOOP antes de continuar  

## PROCEDIMIENTO OPERADOR 1 A 1

1 RECIBIR instrucción literal  
2 INVESTIGAR (doc oficial si aplica)  
3 PLANIFICAR  
4 COMPROBAR estado  
5 PREPARAR  
6 ENVIAR  
7 REGISTRAR ID/SHA  
8 ESPERAR  
9 MONITORIZAR  
10 DIAGNOSTICAR  
11 RESOLVER  
12 REINTENTAR solo la unidad fallida  
13 VALIDAR evidencia  
14 REGISTRAR  
15 CERRAR solo con evidencia  

No inventar ID. No declarar hecho sin read-back. No borrar para simplificar. No 200 = terminado.

## VERIFICACIÓN DESPUÉS DE CADA CAMBIO

LEER → PREPARAR → ENVIAR → ID → VOLVER A LEER → COMPARAR → VALIDAR

## ESCRIBIR EN PARALELO

ORQUESTADOR lanza A/B/C independientes. Monitor por ID. Reintentar solo el que falló.

## PASO 1 RESULTADO

ESPECIFICACIÓN → ORQUESTADOR → API → MONITOR → LOGS → GAP → REINTENTO → VALIDACIÓN → EVIDENCIA
