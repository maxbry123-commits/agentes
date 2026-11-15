# Memoria parcial · lista de tareas y salidas

Fuente: S12-DOC2 (4 tiers + KG) · **alcance parcial** para 100+ documentos.
No cierra memoria full (Dream/Distill/KG autoridad/Postgres).

## Principio

MEMORY.md = índice 2-5 KB. Contenido en storage. Buscar → rankear → top-N → liberar.

## Lista de tareas / salidas

| ID | Tarea | Salida | Estado |
|----|--------|--------|--------|
| **M01** | MEMORY.md índice | `memory/MEMORY.md` | HECHO |
| **M02** | Doc registry Tier3 parcial + chain | `memory/doc_registry.py` + session | HECHO |
| **M03** | Integridad chain heads (tier0/1/3) | `memory/integridad.py` | PENDIENTE |
| **M04** | Ondemand top-N (ya base) + límites YAML | `memory/limits.yaml` + mejora rank | PENDIENTE |
| **M05** | Writer compact umbral 70% (stub) | `memory/writer_subagent.py` stub | PENDIENTE |
| **M06** | Registrar S12-DOC2 + docs previos en registry | script/register | PENDIENTE |
| **M07** | Enganche bootstrap: al ingerir doc → registry | wiring ligero | PENDIENTE |
| **M08** | KG lateral mínimo (aristas version_de/contradice) | cuando más docs | ESPERA DOCS |
| **M09** | autoridad_sobre + C60 CONFLICT | espera docs | ESPERA DOCS |
| **M10** | Distill diario / Dream semanal | espera docs | ESPERA DOCS |
| **M11** | Tier2 strategic store | espera docs | ESPERA DOCS |
| **M12** | Auditoría memoria parcial vs S12 | doc final parcial | PENDIENTE |

## Hecho ahora
- Índice MEMORY.md
- Registry append-only con chain (idempotente por hash)
- Session store Tier1 parcial
- Rank lexical top-N base

## No cerrado (falta más documentación)
KG completo · Dream/Distill · Writer real · Postgres · 4 chain Sentinel full
