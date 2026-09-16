# Wordflow LOOP YAIWES — Workspace

Estado: `ACTIVE_WORKSPACE_ROOT`
Contrato: `tel.workflow/v4`

Esta raíz separa los artefactos de trabajo, memoria del proyecto y perfiles de agentes del código de runtime de Wordflow.

## Estructura canónica

```text
workspace/
├── code/                 # archivos de trabajo; no sustituye runtime/src
├── incoming/             # entradas normalizadas antes de arquitectura/código
├── runs/                 # artefactos por run_id / command_id
├── memory/
│   ├── project/          # memoria de proyecto no autoritativa
│   └── agents/           # memoria operativa de agentes
└── profiles/             # perfiles declarativos tipo CLAUDE.md
```

## Autoridad y límites

1. `Crazy Wall Orquestador/STATE.json` y `CHECKPOINT.json` siguen siendo la verdad operativa autoritativa.
2. `wordflow_loop/wordflow_loop/agent_fleet/agent_fleet_registry.json` sigue siendo el registro canónico de la flota.
3. `workspace/memory/**` es contexto recuperable; memoria != PASS y no puede cerrar nodos.
4. `workspace/profiles/**` describe capacidades, transporte permitido, skills y reglas; no concede autoridad de ejecución.
5. Todo side effect sigue `StructuredAction → Sheriff → Adapter/Sandbox/Executor → Observation`.
6. Los archivos de `workspace/code/` deben conservar `project_id`, `source/provenance`, `command_id`, `target_path` y evidencia del run antes de promoción.
7. No se copian secretos, tokens ni credenciales a esta raíz.

## Flujo

```text
INPUT/FILES
→ workspace/incoming
→ proyecto/destino identificado
→ análisis + arquitectura + Code Graph/DAG
→ workspace/code
→ Sheriff + tests/gates
→ destino real
→ evidence
→ STATE/CHECKPOINT
```

## Perfiles y memoria

Los perfiles deben derivar del registry de agentes para evitar una segunda fuente de verdad. Un perfil tipo `CLAUDE.md` puede añadir instrucciones específicas del agente, pero `agent_id`, roles, transporte y estado deben reconciliarse con el registry fresco.

La memoria de agente registra como mínimo: `agent_id`, `project_id`, `node_id`, `goal`, `command_id`, `observations[]`, `evidence_refs[]`, `last_verified_sha`, `updated_at`.

No registrar chain-of-thought privada; sólo decisiones, observaciones, resultados y evidencia verificable.
