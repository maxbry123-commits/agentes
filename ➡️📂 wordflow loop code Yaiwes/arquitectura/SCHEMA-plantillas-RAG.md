SCHEMA - PLANTILLAS DE PYTHON VIA RAG/BIBLIOTECA (no escribir todo desde 0)

Recordatorio del sistema ya discutido en esta conversacion: en vez de que
el agente escriba codigo linea por linea, primero consulta una biblioteca
de plantillas/bloques ya probados (tipo RAG - retrieval antes de generar).

## Microflujo
NECESIDAD_DE_CODIGO -> BUSCAR_EN_BIBLIOTECA_DE_PLANTILLAS (RAG sobre
patrones ya usados/probados) -> SI_EXISTE: reusar/adaptar bloque ->
SI_NO_EXISTE: generar nuevo Y guardarlo en la biblioteca para la proxima vez

## Donde vive esto en Wordflow
Mapea directo a REUSE_SELECTOR.py (ya confirmado real en la auditoria) -
la biblioteca de plantillas seria la fuente que reuse_selector.py consulta
ANTES de decidir GENERATE. Si reuse_selector.py no tiene todavia esta
fuente conectada, es un GAP a cerrar (ver Anexo).

## Regla
Mismo orden de siempre: REUSE_EXISTING (de la biblioteca de plantillas) >
PATCH > ADAPT > GENERATE. Generar desde cero es la ULTIMA opcion, nunca la
primera, ni en backend ni en frontend.
