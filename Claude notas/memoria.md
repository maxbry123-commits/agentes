# CLAUDE NOTAS - memoria.md
RAIZ UNICA Y REAL DE MEMORIA DESDE 2026-09-16. Reemplaza a Claude readme/,
que queda deprecado con aviso de redireccion, sin borrar (regla del proyecto).
Este archivo NUNCA se resume. Se actualiza anadiendo, nunca borrando historia.

## 1. QUE ES ESTO

Soy Claude, orquestador central del ecosistema Maxbry/NCT. No escribo codigo
de produccion - escribo instrucciones, audito evidencia, y mantengo este
archivo como memoria de trabajo persistente entre sesiones de chat.
Sol GPT queda retirado del rol de orquestador.

## 2. EL ECOSISTEMA COMPLETO (7 proyectos)

1. Agente Yaiwes - repo agentes - Confirmado
2. Osquestador Maxbry - repo Orquestador-Maxbry- - no confirmado
3. Router Inteligente Universal - repo router-universal-router-inteligente- - Confirmado
4. UI Yaiwes - repo nct-hub (hipotesis)
5. Fabrica de UI - repo frontend - Confirmado
6. Osquestador auditor + memoria - repo osquestador-auditor
7. NCT - repo nct-core - Confirmado

Repos activos AHORA: agentes, frontend, router-universal-router-inteligente-

## 3. METODO DE TRABAJO

1. Un paso por salida.
2. Micro-mundos aislados por proyecto.
3. Contrato de nodo: maximo 3 pasos.
4. Reglas duras de ejecutores: read fresh, solo FREE, REUSE_EXISTING primero,
   no PASS sin evidencia, GAP investiga 20 formas, nunca detenerse.
5. Escalera: Sol GPT -> Haiku -> Sonnet -> Opus -> GPT/Astra -> Fables 5.1
6. Nunca resumir en documentos de trabajo.
7. COPY-FIRST antes de generar codigo nuevo.

### 3.1 REGLA DE PRESENTACION (nueva, 2026-09-16)

Formato de agente: Capacidad, Patron microflujo horizontal en texto, LOOP,
Aporta, Usa, Reglas, Fallos, Test. Sin imagenes salvo pedido explicito.
Formato de componente: component_id, name, objective, responsibility,
input, output, dependencies, files, status, failure, recovery.

### 3.2 REGLA DE ORGANIZACION DE RAIZ (nueva, 2026-09-16)

3 componentes por proyecto: Readme arquitectura + Crazy Wall + Handoff.
Cada proyecto es una raiz con nombre completo, nunca readme.md suelto.
Formato: Proyecto/Readme arquitectura Proyecto.md
Versionado: version nueva 1.1, comparar, borrar vieja solo si es copia fiel.
Archivo en raiz equivocada se mueve a su proyecto real.
Basura real se elimina, previa revision de contenido.

### 3.3 RAICES OFICIALES DE main (aprobado 2026-09-16)

AGENTS.md, .github, .cursor (se quedan sueltos)
Agente Yaiwes principal/
Core kernel Yaiwes/
Seals team YAIWES/ (incluye Command Center/, seals_core/, Seals team 1 YAIWES/, _fuentes_extraidas/)
Componente open source Yaiwes/
Claude notas/ (esta raiz)
Motores de descarga y extraccion/
Skills agente/
Wordflow Loops Yaiwes/
Conecciones router inteligente universal/

Pendiente de auditar: Documentos proyectos Yaiwes, forensics, scripts, _work.

## 4. PRIORIDAD ACTUAL

1. Limpieza y organizacion de raiz de agentes - EN CURSO, auditoria en 6 salidas.
2. Cerrar ficha/componentes/integracion del Agente Yaiwes.
3. Wordflow Loop code de Yaiwes.
4. Activar Router Inteligente Universal.
5. Wordflow loops automatizados tipo SDK.

## 5. AGENTE SEALS TEAM

Ubicacion: Seals team YAIWES/. Estado: codigo completo (8 archivos +
requirements + tests + router_modelos.py + Tenacity + mission_id), sin
placeholders, pendiente de primera prueba real.
Arquitectura: DAG determinista, 95% codigo puro / 5% LLM via Cerebras,
Claude solo verificacion final bajo volumen.
Extraido quirurgicamente de Muse-Agent y MUSE-KnowledgeXLab.
Pendiente decision: Meta-Muse-Code-SDK-2026 y Meta-Agent-Cookbook-2026
(descargados fuera de alcance, pausados).
Variables de entorno pendientes en GitHub Secrets: CEREBRAS_API_KEY_1 a 6,
ANTHROPIC_API_KEY, GITHUB_TOKEN.
Command Center ubicado DENTRO de Seals team YAIWES (correccion 2026-09-16).

## 6. CORRECCIONES DE PROCESO REGISTRADAS

- 2026-09-15: cree Claude notas duplicando Claude readme sin buscar primero.
- 2026-09-16: Claude notas es ahora el nombre oficial, reemplaza a Claude readme.
- 2026-09-16: cree Command Center como raiz suelta indebida, corregido dentro de Seals team YAIWES.
- 2026-09-16: raiz completa tenia duplicados reales por hash y variantes con emoji, en consolidacion via Sol.

## 7. AUDITORIA COMPLETA WORDFLOW LOOP + PENDIENTES NUEVOS (2026-09-17)

Cobertura 100% lograda: 21/21 carpetas de Wordflow Loop auditadas.
Documentos creados en "arquitectura wordflow loop code Yaiwes/" (16
archivos): indice general, Parte 1-5 (formato Glimmer por fase), Anexo
1-4, 3 SCHEMAS (refactorizacion con 15 reglas fuente, frontend
browser-verified con texto verbatim del Director, plantillas RAG con
formato YAML definido), 2 PROMPTS para Sol (investigar capacidad
frontend del Fleet de 18 agentes, descargar 4 componentes nuevos sin
Crazy Wall), 1 RESOLUCION de 3 pendientes, 1 DISENO de servidor MCP.

Hallazgos mayores: Enchufe Universal YA integrado en uek/ (30KB), 2do
sistema de Crazy Wall completo en "Crazy Wall Orquestador/" (pendiente
comparar antes de fusionar, prompt ya escrito para Sol), 13 subcarpetas
de templates/skills/plugins/prompts en wordflow_loop/wordflow_loop/
TODAS VACIAS, mis 20 documentos originales estan en el repo con notas
X-Ray propias marcadas "AUDITADO/PROPUESTA, no integrado" (criterio:
integrar selectivamente por gap real, nunca todo de golpe).

MCP confirmado por el Director: contexto compartido entre agentes = Model
Context Protocol de Anthropic. Requisito adicional: lo que un agente
descubre debe compartirse con los demas (no solo con el kernel). Diseno
ya escrito (DISENO-MCP-contexto-compartido.md) - servidor MCP con 3
recursos (crazy_wall_state lectura, mission_context lectura/escritura
controlada, enchufe_universal_tools). Regla de seguridad: MCP comparte
CONTEXTO nunca AUTORIDAD - el Kernel sigue siendo el unico que decide PASS.

### PENDIENTE NUEVO: sistema de preguntas previas (tipo Claude) para Yaiwes y UI Yaiwes

El Director pidio evaluar si se puede crear, para Yaiwes y para UI Yaiwes,
un sistema de preguntas aclaratorias ANTES de ejecutar una tarea (como el
que usa Claude con el usuario) - un paso previo de analisis para enfocar
y entender antes de continuar, en vez de ejecutar sobre ambiguedad.
MARCADO COMO PENDIENTE, sin disenar todavia - requiere decidir: se activa
siempre, o solo cuando el DAG detecta ambiguedad real (campo faltante,
2 interpretaciones posibles)? Pendiente de instruccion del Director para
disenarlo a fondo.

Herramientas nuevas anotadas por el Director, sin verificar (web_search
no disponible en este turno): Omniroute, Orca, Omarchy, Anydoc - prompt
de descarga ya escrito para Sol, categoria "PENDIENTE DE VERIFICACION POR
SOL AL DESCARGAR".
