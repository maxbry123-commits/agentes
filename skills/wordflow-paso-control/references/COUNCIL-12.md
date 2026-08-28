# Council 12 — analisis instrucciones Director

Correr esto ANTES de editar skill o cablear.

## 12 goals in

1. Localizar el sistema zip extract+copy en agentes, TAREA-1 y Agentes-motores-Wordflow-YAIWES.
2. Cablear skill de descarga + Refactoria + Download code + Desplegar.
3. PASO 1 = GitHub Action con lista fija de repos (research-download-chain lock).
4. PASO 2 = carpeta Download code / Download N como bandeja de tarea.
5. OP1 = parte del code hacia Download N. OP2 = repo/agente completo a raiz nueva o fork.
6. Verificacion cruzada fuente vs dest. Cero archivos faltantes. SHA match.
7. PASO 3 = extract de guia zip. COPY no rewrite. Fables plugin I/O. JSON/prompt -> py. YAML = reglas/skills.
8. Cargar UOOS 1+2 + Enchufe Universal + ficha para que la AI sepa extension y plugin.
9. PASO 4 = Actions cola + cp + un commit + token dest + raiz organizada src/config/scripts/tests.
10. PASO 5 = estado por nombre + write atomico READ HASH TEMP DIFF VALIDATE RENAME.
11. PASO 6-8 = deploy py/yaml, estandares inyectados, router A/B/C con Maxbry_123_tokens, 2 cables, 3 OUT.
12. X-Ray + EXTRACT_LITERAL + council12. Copias Tarea 3 solo post-evidencia.

## Fallo del skill anterior (council)

- Era un dump del INPUT BLOCK, no un protocolo de ejecucion.
- No decia QUE leer, QUE comando, QUE gate, QUE artifact, QUE NEXT.
- Mezclaba requisitos con operador.
- skill-creator pide instrucciones imperativas + references para el bloque largo.
- Control = una tarjeta IN/DO/FORBID/GATE/OUT/NEXT por PASO.

## 12 goals out

1. Skill nuevo `wordflow-paso-control` inicializado con skill-creator.
2. SKILL.md = tarjetas de control PASO 1-8 + OP1 + OP2 + 3 OUT.
3. INPUT BLOCK 1-32 en references, no como cuerpo del skill.
4. Council 12 in/out en references.
5. SOURCE-MAP con paths reales auditados (gap si falta).
6. Token solo env alias. C = HOLD.
7. Download lock delegado a research-download-chain. No reescribir packer.
8. Copy = Actions queue. Dest token. Map organico.
9. Plugin I/O obligatorio. Origen intocable.
10. Deploy tail del Wordflow Code. DRY_RUN default.
11. OUT1 chat UOOS. OUT2 crear dest. OUT3 raiz A + evidence.
12. Tarea 3 copias listadas, no ejecutadas hasta evidencia de este skill.

## Verdict council

GO escribir skill de control.
NO GO declarar PASS de cableado Tarea 3.
HOLD owner C y valor del secret Maxbry_123_tokens (Director pega en GitHub UI).
