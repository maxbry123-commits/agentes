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
Seals team YAIWES/ (incluye Comand Center/, seals_core/, Seals team 1 YAIWES/, _fuentes_extraidas/)
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
Comand Center ubicado DENTRO de Seals team YAIWES (correccion 2026-09-16).

## 6. CORRECCIONES DE PROCESO REGISTRADAS

- 2026-09-15: cree Claude notas duplicando Claude readme sin buscar primero.
- 2026-09-16: Claude notas es ahora el nombre oficial, reemplaza a Claude readme.
- 2026-09-16: cree Comand Center como raiz suelta indebida, corregido dentro de Seals team YAIWES.
- 2026-09-16: raiz completa tenia duplicados reales por hash y variantes con emoji, en consolidacion via Sol.
