# PIPELINE 07 — ENCHUFE UNIVERSAL v2.0
## Contrato Final de Fichas (Base Crítica)

**Fecha:** 2026-08-09  
**Estado:** BASE CRÍTICA — REPLICAR 1:1  
**Sustituye:** v1.5 (compatibilidad total)

---

## 1. Qué es

El Enchufe Universal es el **contrato estándar** que permite conectar cualquier pieza (código, prompt DSL, agente, API, MCP, herramienta, base de datos) como una **ficha** reutilizable.

Cada ficha declara:
- qué consume
- qué produce
- cómo se ejecuta
- bajo qué reglas puede conectarse
- permisos, límites, sandbox, recovery

Resultado: pipelines DAG donde cada módulo es una neurona reutilizable.

---

## 2. 12 mejoras vs v1.5

| # | Campo nuevo | Para qué |
|---|-------------|----------|
| 1 | categoria | pipeline / transversal / acelerador |
| 2 | etapa | E / P / S / T / A |
| 3 | perfiles | comportamiento por nivel cognitivo 0-5 |
| 4 | repeticion | cuántas veces y bajo qué condición |
| 5 | activacion | triggers (eventos, wake_words, condiciones) |
| 6 | presupuesto | tokens/tiempo/costo máx por nivel |
| 7 | telemetria | métricas + spans OTel |
| 8 | evidencia | niveles L1-L4 |
| 9 | failover | sustituible_por + compensación |
| 10 | firma | GPG key + revocation_list |
| 11 | salud | health + heartbeat |
| 12 | repite_en | puntos de re-verificación de memoria |

Regla: todo campo nuevo tiene default. Una ficha v1.5 válida es v2.0 válida.

---

## 3. Campos obligatorios v2.0

```
artifact_id, version, estado, categoria, etapa,
contrato, ejecucion, seguridad, firma
```

**contrato.rol:** source | transform | sink | service  
**ejecucion.kind:** code | llm | db | api | tool | agent  
**ejecucion.runtime_type:** compute | hybrid | llm | agent  
**categoria:** pipeline | transversal | acelerador

---

## 4. Validador v2.0 (invariantes)

- 22 invariantes v1.5 + 14 nuevas v2.0
- normalizar_v15() aplica defaults
- compatibles(a, b) = a.expone.datatype == b.consume.datatype (autoensamblaje)

Reglas clave:
- active requiere contract_hash real + gpg_key_id
- compute no puede tener llm_ratio > 0.10
- repetición > 1 exige idempotente
- agent exige max_steps + allowed_actions

---

## 5. Trazabilidad

- Origen: input block Director — “ENCHUFE UNIVERSAL v2.0” + schema JSON completo
- Base crítica del PIPELINE. Debe replicarse 1:1.

**Estado:** listo para auditoría.
