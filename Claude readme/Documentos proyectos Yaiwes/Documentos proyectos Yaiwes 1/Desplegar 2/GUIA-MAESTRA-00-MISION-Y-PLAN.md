# GUÍA MAESTRA — MISIÓN Y PLAN DE EJECUCIÓN
**Lee esto primero, antes de cualquier Guía de Despliegue por salida. Aquí está qué vas a construir, por qué, y en qué orden vas a recibir la información.**

---

## 1 · Qué vas a construir

Vas a construir **YAIWES Wordflow** — un sistema de orquestación de agentes de IA para programar software, determinista en su control y con IA solo donde es estrictamente necesaria (objetivo: 90% código determinista / 10% LLM).

En una frase: **una Capa de Control decide qué se puede hacer, Temporal ejecuta lo aprobado, agentes reales escriben el código, y todo termina en GitHub.**

## 2 · Arquitectura general (el mapa completo, resumido)

```
Director (Máx) → OpenClaw (HF1)
                     │
              CAPA DE CONTROL
        DSL · Schema · Registry · Sheriff (22 checks, 5 estados)
        Contract Router · Goals(12 campos) · Council(12) · Tribunal(6)
                     │
              ¿Sheriff aprueba?
                 NO → rechazo, se reporta
                 SÍ → TEMPORAL (único motor de ejecución, HF1, nunca en HF2-5)
                     │
        ┌────────────┴────────────┐
        ▼                         ▼
  BACKEND (HF2 core / HF3 agentes)   FRONTEND (HF4 core / HF5 agentes)
  Seed-Coder→Nemotron→Nanbeige→Gemma→DeepSeek(externo, último recurso)
  Harness · Sandbox · Research Engine (≥20 fuentes antes de construir)
        └────────────┬────────────┘
                     ▼
              VALIDACIÓN (Tribunal 6 roles, veto primero, score después)
                     │
                  GITHUB (repo `agentes`) → branch → PR → merge (nunca directo a main)
                     │
              DEPLOYMENT GATEWAY → HF (Storage Bucket, modelos GGUF)
```

No memorices esto en detalle — cada pieza tiene su propia salida con el detalle completo. Esto es solo para que sepas dónde encaja cada cosa que vas a construir.

## 3 · Cómo vas a recibir el trabajo — 6 salidas

Vas a recibir **6 salidas**, en este orden. Cada salida trae 2 documentos: uno de **contenido** (arquitectura/código/contratos de esa parte) y uno de **ejecución** (nodos T-0XX con goal/dependencias/contrato/criterio_exito — el que realmente sigues paso a paso).

```yaml
Salida 1: "Núcleo + DAG + Sheriff + Capa de Control + Temporal (integración)"
  estado: ENTREGADA
  documentos: [SALIDA-01-NUCLEO-DAG-CONTROL.md, GUIA-DESPLIEGUE-GROK-PARTE-01-FINAL.md, GUIA-DESPLIEGUE-GROK-PARTE-02.md]
  nodos: T-001 a T-013

Salida 2: "Long-Running Loop Engine + Sistema de Recuperación"
  estado: pendiente
  cubre: el motor que ejecuta los 10-11 loops ya definidos como tipo en Salida 1 (C11),
    Checkpoint/Watchdog/Resume
  nota: "Research Engine, Goals y Council YA están completos (A2 y Salida 1, secciones C9/C10)
    — no se repiten aquí, corrección aplicada tras auditoría"

Salida 3: "Harness + Router (5 HF) + Sandbox/Paralelismo + Puente HF"
  estado: pendiente
  cubre: adapters por agente, el Router completo (no solo LiteLLM — Decision Engine, Cache 4 niveles,
    Activation Manager de HF3/HF5), Resource Governor, qué código va en cada uno de los 5 HF

Salida 4: "GitHub + Deployment Gateway"
  estado: pendiente (la más cercana a estar lista — ya existe la mecánica de Git completa)
  cubre: branch/commit/push/PR/merge/rollback, Credential Broker, despliegue a HF

Salida 5: "Memoria (10M tokens) + Hermes + Change Engine + Workflow Gateway"
  estado: pendiente
  cubre: memoria de proyecto de 4 capas, Hermes como Sentinel independiente, versionado del Workflow

Salida 6: "Comunicación entre agentes por nodo (autonomía) + Observability + Integración final"
  estado: pendiente
  cubre: niveles de autonomía 0-3, Event Store, estructura de carpetas final, backup a Drive
```

## 4 · Regla de dependencia entre salidas

No puedes ejecutar nodos de una salida si sus dependencias declaradas señalan a una salida anterior sin terminar. El orden de arriba no es sugerido — es el orden real de dependencia (ej. Salida 3 necesita el Sheriff de Salida 1 para autorizar qué corre en cada HF; Salida 4 necesita agentes de Salida 3 para tener algo que subir a GitHub).

## 5 · Cómo trabajas en cada salida

Ya tienes el runtime completo (UOOS Parte 1 para cómo se especifica, Parte 2 para cómo ejecutas: RT-00→RT-90, Tribunal de 6, vocabulario del Director, eventos obligatorios — todo definido en `GUIA-DESPLIEGUE-GROK-PARTE-01-FINAL.md`, no se repite en cada salida). Cada salida nueva solo añade nodos nuevos al mismo patrón.

## 6 · Prioridad de todo el proyecto

```
1º GitHub — código funcionando y probado (Salidas 1-2-3, luego formaliza en 4)
2º HF — despliegue a los 5 Spaces (Salida 3 da el diseño, se ejecuta al final)
3º Documentos explicativos para el Director — al final de todo
```

---

*Con esto ya sabes qué construyes, por qué, y qué viene después de la Salida 1. Ahora sí: `GUIA-DESPLIEGUE-GROK-PARTE-01-FINAL.md` es donde arrancas.*
