# PIPELINE 14 — PERFIL MVP + 4 OBJETIVOS
## Documento maestro de alcance, estado y trazabilidad
**Versión:** 1.0  
**Fecha:** 2026-08-09  
**Estado:** Activo — memoria de trabajo del MVP

---

## 1. PERFIL DEL MVP

**Nombre:** MAXBRY / TEAM YAIWES — Control Layer + Wordflow MVP  
**Tipo:** Extensión kernel + Wordflow determinista  
**Principio:** 90% determinista / 10% LLM  
**Objetivo de esta fase:** Entregar un mínimo viable funcional de 4 capacidades, no el sistema completo.

**Qué es:**
- Capa de control universal que se monta como extensión kernel
- Wordflow continuo (fusión MiniMax + Kimi)
- Sistema nativo de documentos de proyecto
- Publicación determinista a GitHub
- Adquisición determinista de código/repos/binarios (pendiente de recibir)

**Qué NO es:**
- Un agente más
- Un chatbot
- Un reemplazo completo de OpenClaw
- Un sistema que reescribe todo en cada cambio

---

## 2. LOS 4 OBJETIVOS DEL MVP

### Objetivo 1 — Conexión universal como extensión kernel
**Estado:** PARCIAL  
**Qué ya tengo:**
- Enchufe Universal v2.0 (Fables)
- Documentos nativos (PIPELINE 12 FULL + 13)
- Diseño de KTP + Resource Brain + Normalizer

**Qué falta:**
- Parte del kernel con código real (el Director lo va a pasar)
- Módulo de loops que el Director va a dar
- Adaptar y conectar lo existente

**Resultado esperado:**  
Cualquier agente puede montar esta extensión y usar el Wordflow + documentos nativos sin modificar su núcleo.

---

### Objetivo 2 — Wordflow funcional (fusión MiniMax+Kimi + documentos nativos)
**Estado:** PARCIAL  
**Qué ya tengo:**
- Documentos de la fusión MiniMax + Kimi (F-1→F9) en attachments
- PIPELINE 12 FULL + 13 (capa de documentos nativos completa)

**Qué falta:**
- Integración real del Wordflow F-1→F9 con la capa de documentos
- Código ejecutable de las fases que aún están solo en diseño

**Resultado esperado:**  
El Wordflow corre de forma continua, usa los documentos nativos y puede recibir inputs nuevos sin reiniciarse.

---

### Objetivo 3 — Downloader / Installer determinista
**Estado:** PENDIENTE DE RECEPCIÓN  
**Qué ya tengo:** Nada aún  
**Qué falta:** El Director va a pasar el sistema completo (ya está listo)

**Resultado esperado:**  
Descargar código fuente, repos, binarios o agentes e instalarlos en el repositorio de forma 100% determinista.

---

### Objetivo 4 — GitHub Publisher determinista
**Estado:** POR CONSTRUIR (responsabilidad mía)  
**Qué ya tengo:**
- Contrato completo definido por el Director
- Diseño del módulo (`github_publisher/`)
- Preferencia de Git Data API (blob → tree → commit → ref)
- Regla de token vía `token_ref` + Credential Store

**Qué falta:**
- Implementar el módulo Python
- Integrarlo como capacidad del Wordflow

**Resultado esperado:**  
El Wordflow entrega un contrato `github_publish` y el módulo publica los archivos de forma determinista en el repositorio indicado.

---

## 3. TRAZABILIDAD DE INFORMACIÓN USADA

| ID | Documento / Fuente | Origen | Usado en | Estado |
|----|--------------------|--------|----------|--------|
| SRC-01 | Enchufe Universal v2.0 (Fables) | Director | Obj 1 | Disponible |
| SRC-02 | DESPLIEGUE-DETERMINISTA-UNIVERSAL-v2 | Director | Base | Disponible |
| SRC-03 | P1-CONVERTIDOR | Director | Base | Disponible |
| SRC-04 | Fusión MiniMax + Kimi (varios .md) | Director | Obj 2 | Disponible |
| SRC-05 | G1 completo (P1/P2/P3 + CORE) | Director | Obj 1+2 | Incorporado en 12+13 |
| SRC-06 | Plantillas emoji + micro-flujos | Director | Obj 1+2 | Incorporado en 12+13 |
| SRC-07 | Resource Brain (Ruflo analysis) | Director | Obj 1+2 | Incorporado en 12+13 |
| SRC-08 | Project Normalizer + Input Handler | Director | Obj 1+2 | Incorporado en 12+13 |
| SRC-09 | Contrato GitHub Publisher | Director | Obj 4 | Disponible |
| SRC-10 | PIPELINE 12 FULL | Este chat | Obj 1+2 | Creado |
| SRC-11 | PIPELINE 13 (piezas faltantes) | Este chat | Obj 1+2 | Creado |
| SRC-12 | Parte del kernel con código | Director | Obj 1 | Pendiente de recibir |
| SRC-13 | Módulo de loops | Director | Obj 1 | Pendiente de recibir |
| SRC-14 | Downloader/Installer determinista | Director | Obj 3 | Pendiente de recibir |

---

## 4. REGLA DE ACTUALIZACIÓN DE TRAZABILIDAD

Cada vez que el Director entregue un documento nuevo:
1. Se registra en esta tabla con nuevo SRC-XX
2. Se indica en qué objetivo se usa
3. Se actualiza el estado del objetivo correspondiente
4. Se hace commit en este mismo archivo

---

## 5. ORDEN DE TRABAJO INMEDIATO

1. S1 — Este documento (PERFIL + 4 objetivos + trazabilidad) ← **ACTUAL**
2. S2 — Reorganizar estructura PIPELINE en GitHub
3. S3 — Actualizar trazabilidad de 12 y 13 dentro de este perfil
4. Esperar material Obj 1 (kernel + loops) y Obj 3 (downloader)
5. Construir Obj 4 (GitHub Publisher)

---

**Estado S1:** COMPLETO  
**Siguiente:** S2 — Reorganizar PIPELINE en GitHub
