CRITICO 2026-09-18 - Confusion real de 3 carpetas casi identicas, con
contenido total mente distinto. Requiere decision del Director, no
resolucion unilateral de Claude.

CARPETA 1: "wordflow loop code Yaiwes" (con emoji al inicio, minuscula w)
= el kernel Python real que llevo auditando. DAGEngine, governance/,
uek/, tribunal.py, etc. TODO lo documentado en "arquitectura wordflow
loop code Yaiwes/" describe ESTA carpeta.

CARPETA 2: "Wordflow loop code Yaiwes" (SIN emoji, W mayuscula)
= un proyecto completo, ajeno, descargado por Sol (casi seguro big-AGI,
Electron+Next.js: tiene package.json, next.config.mjs, Dockerfile,
electron/, flake.nix, CHANGELOG.md de 2.7MB, .env.example de 184KB,
package-lock.json de 1.4MB). Tiene su PROPIA carpeta skills/ con ~30
skills nativos del proyecto descargado (omni-auth, omni-cache, cli-mcp,
omni-budget, etc que vienen con el software, no los pedimos nosotros).

DENTRO de esa Carpeta 2, MEZCLADOS con los 30 skills nativos del
proyecto ajeno, estan los 3 skills reales que SI pedimos:
frontend-design/, impeccable/, skill-creator/ (confirmado via listado
real, todas vacias/size 0 - solo carpetas, contenido interno sin
verificar todavia).

CARPETA 3: "Skills agente/" (donde Claude busco primero) = solo tiene
skill-design-anthropic/ vacia. Los otros 3 skills NO estan aqui.

DECISION REQUERIDA DEL DIRECTOR (no la toma Claude solo):
A) Mover los 3 skills reales (frontend-design, impeccable, skill-creator)
   desde la Carpeta 2 hacia "Skills agente/" (la raiz oficial de skills
   segun las reglas ya aprobadas)
B) Decidir que hacer con el resto del proyecto ajeno (Carpeta 2) -
   es un proyecto entero (potencialmente cientos de MB), no un
   componente - podria ser exactamente uno de los 14 de T1_ACQUIRE_14
   (big-AGI) que aterrizo con un nombre casi identico al kernel real,
   causando toda la confusion de rutas de los ultimos turnos.
C) Confirmar si la Carpeta 2 debe renombrarse a algo sin relacion con
   "wordflow" (ej. "big-AGI-descargado/") para eliminar la ambiguedad
   de raiz, antes de continuar cualquier otra tarea.

NO SE EJECUTA NADA DE ESTO SIN APROBACION EXPLICITA - mover/renombrar
un proyecto de este tamano sin confirmar primero seria repetir el mismo
error que ya corregimos varias veces esta sesion.
