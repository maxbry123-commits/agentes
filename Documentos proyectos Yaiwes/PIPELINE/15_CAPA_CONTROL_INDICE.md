# PIPELINE 15-17 — CAPA DE CONTROL (SALIDA 1/8)
## Recuperación total del Input Block · 3 partes
**Fecha:** 2026-08-09  
**Estado:** Materializado en PIPELINE

---

## Qué es

Recuperación **literal** (1:1, sin resumir) de todo el input block de la **Capa de Control** entregado por el Director.

Esta capa **no es un agente ni un orquestador**. Es una capa tipo prompt de controlador que convierte todo lo posible en determinista.

- Nombre: OpenClaw Control Plane Lightweight Layer
- Ubicación: antes de OpenClaw
- Tipo: capa Python/YAML de control
- Principio: 90% determinista / 10% LLM

---

## Estructura de las 3 partes

| PIPELINE | Contenido | Secciones |
|----------|-----------|-----------|
| **15** (Parte 1) | Identidad · Prohibiciones · Arquitectura · DSL formal · Nodos · Catálogos · Código real | 1–16 |
| **16** (Parte 2) | Sheriff · Estados · R21-R30 · Errores · Determinismo · Búsqueda · Memoria · Zona razonamiento | 17–31 |
| **17** (Parte 3) | Goals · Council · Tribunal · Loops · Constitución · 44 gates · Contratos · Despliegue | 32–52 |
| **18** | MYTHOS Motor de Razonamiento (40 pasos D/P/H) | Completo |

---

## Contenido clave recuperado

### Parte 1 (Identidad + DSL)
- Identidad de la capa (no kernel, no orquestador, no scheduler)
- Prohibiciones duras
- Función (validar, decidir, enrutar, registrar)
- Arquitectura de 3 archivos (YAML + JSON + Registry)
- Flujo de ejecución formal
- Por qué falló el formato de prompt
- 12 mejoras para 100% determinista
- 18 problemas de diseño detectados
- Estructura de nodo (10 campos fijos)
- Catálogos cerrados
- Código real de producción: controller.py, sheriff.yaml, task_schema.yaml, workflow.yaml
- Plantilla V7 completa

### Parte 2 (Sheriff + Estados + Memoria)
- Sheriff completo (22 checks)
- Matriz de control (7 preguntas SI/NO)
- Máquinas de estados (nodo, programa, motor)
- STOP vs WAIT_EVENT
- R21–R30 anti-escalamiento
- Política del ejecutor y de determinismo
- Códigos de error normalizados
- Schema de salida fijo
- Separación de responsabilidades del lenguaje
- Motor de búsqueda doble pasada
- Memoria extendida (RAM → SSD → GitHub)
- Execution Knowledge Layer (10 módulos)
- 20 mejoras de refuerzo
- Separación zona determinista / zona razonamiento

### Parte 3 (Goals + Council + Loops)
- 4 microcapas de Goals (Entrada / Refutación / Validación / Formato)
- Goals en formato campo fijo (12 + 12 + 7 + 25 research)
- Council 12 · Council único · Councils múltiples
- Tribunal 6 roles (UOOS B6) con veto
- 4 sistemas de loop (12 pasos, 16 pasos, L01-L11)
- Constitución de análisis (11 pasos)
- Método de 9 pasos para cada salida
- Método de trabajo en chat
- 44 gates de razonamiento
- Contratos de frontera + Contract Router
- Límite de líneas / estructura de carpetas
- Schema ficha de componente
- Modos y niveles de autonomía
- Prompt superior de control
- Entidades del sistema
- DAG de flujo de ejecución
- Criterio de aceptación
- Despliegue determinista
- Fases de implementación

### PIPELINE 18 — MYTHOS
- 40 pasos clasificados D/P/H
- Mapeo a fases F0–F5 + CHEF
- LISTA_GLOBAL + DRE + hybrid_split + REPLANNER + CHEF + BLOQUE_X
- Integración con Capa de Control

---

## Trazabilidad

| Fuente | Destino |
|--------|--------|
| SALIDA_1_CAPA_CONTROL_PARTE_1.md (47107 bytes) | PIPELINE/15 + este índice |
| SALIDA_1_CAPA_CONTROL_PARTE_2.md (40697 bytes) | PIPELINE/16 |
| SALIDA_1_CAPA_CONTROL_PARTE_3.md (54256 bytes) | PIPELINE/17 |
| MYTHOS (14749 bytes) | PIPELINE/18 |

Los documentos completos literales están en los attachments del Director.  
Este índice + los archivos PIPELINE sirven como memoria de trabajo del proyecto.

---

**Estado:** Capa de Control recuperada e indexada en PIPELINE.  
**Siguiente:** Objetivo 1 (conexión como extensión kernel).
