ACLARACIONES DEL DIRECTOR 2026-09-17 - Docfile y contexto compartido entre agentes

## DOCFILE (aclarado por el Director, verbatim de su explicacion)
"Docfile para cerrar todo al final del proyecto" - es un documento de
CIERRE FINAL, no un manifiesto de trabajo en curso.

DECISION DE DISENO (Claude, basado en la aclaracion):
- Se escribe UNA VEZ, solo cuando VERIFIED_CLOSED es real (todos los PASS
  del proyecto con evidencia, no antes).
- Ubicacion: raiz de cada proyecto, nombre
  DOCFILE-CIERRE-nombre-proyecto.md
- Contenido obligatorio: que se construyo, que paso (con evidencia real,
  path+sha256+test), limitaciones conocidas, y GAPs que quedaron
  deliberadamente fuera de alcance (no ocultos, documentados).
- Regla: nunca se escribe un Docfile de un proyecto que todavia tiene
  GAPs abiertos en su Crazy Wall - seria un cierre falso.

## CONTEXTO COMPARTIDO ENTRE AGENTES (VSCode) - interpretacion, no certeza

El Director describe: "es como se comparten contexto los agentes, una
funcion que deberia existir, lo usa Codex Claude code y otros".

INTERPRETACION DE CLAUDE (a confirmar por el Director, no asumida como
hecho): esto describe el Model Context Protocol MCP, protocolo real
creado por Anthropic, adoptado por Claude Code, y que Codex y otros
agentes de codigo vienen incorporando para compartir herramientas y
contexto entre si de forma estandar.

SI ES MCP: la integracion correcta seria un servidor MCP propio de
Wordflow/Seals Team que exponga estado del Crazy Wall, contexto de la
mision actual, y herramientas del Enchufe Universal, para que cualquier
agente compatible con MCP pueda conectarse sin cablear a mano cada uno.

PENDIENTE DE CONFIRMACION DEL DIRECTOR antes de disenar el servidor MCP
completo - interpretacion razonada, no verificada por busqueda en este
turno (web_search sin disponibilidad).

## AUDITORIA DE AMBIGUEDADES RESTANTES (revision de los 11 archivos)

1. SCHEMA-plantillas-RAG.md sigue siendo conceptual, no especifica el
   formato real del template. PENDIENTE definir antes de construir la
   biblioteca vacia.
2. La fusion de los 2 Crazy Wall sigue sin prompt de ejecucion, solo
   senalada como pendiente.
3. No se ha decidido si Omniroute/Orca/Omarchy/Anydoc van a Fase 1 o
   Fase 2 del Plan de Adquisicion - solo anotados, sin clasificar.
