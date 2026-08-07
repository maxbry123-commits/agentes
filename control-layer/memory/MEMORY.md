# MEMORY INDEX · Wordflow control-layer

> Índice 2-5 KB. El contenido vive en storage; aquí solo punteros.
> Regla: buscar → rankear → top-N → liberar. Nunca cargar miles de archivos.

## Meta
- version: 0.1.0-partial
- scope: continuidad entre 100+ documentos (no 4 tiers full)
- updated: 2026-08-07

## Tiers (parcial)
| Tier | Estado parcial | Path |
|------|----------------|------|
| 0 RAW | InputBlock store | inputblock/ |
| 1 SESSION | session.jsonl | memory/session/ |
| 2 STRATEGIC | stubs / distill pending | memory/strategic/ |
| 3 PROJECT | doc registry permanente | memory/project/docs.jsonl |

## Docs registrados
Ver `project/docs.jsonl` (append-only).

## Chain heads
- tier0: inputblock chain tip
- tier1: session chain tip
- tier3: docs registry chain tip

## Próximo
M03 chain integrity · M04 ondemand top-N · KG/Dream/Distill cuando lleguen más docs
