# AUDIT 10 PASADAS · Evolution vs Input · 2026-08-07

## PASADA 1 — Objetivo
Input exige: absorber → Universal Plugin → kernel, NO instalar agentes.
Código: `EvolutionController.evolve_path` + `UniversalPlugin` + `CapabilityRegistry`.
Estado: **CUMPLE (núcleo)**

## PASADA 2 — Universal Plugin único contrato
Input: kernel solo `plugin.invoke`.
Código: `plugin/universal_plugin.py` + bridge `bridge_abi.py` → `extension.abi.execute`.
Estado: **CUMPLE** (puente ABI añadido esta pasada)

## PASADA 3 — EVO-IR
Input: IR única para agent/software/skill/dataset/adapter.
Código: `evo_ir.py` ComponentIR + CapabilityIR + EvoIR.
Estado: **CUMPLE**

## PASADA 4 — Authority Graph + CODE_AGENT_POLICY
Input: cognitive preserve, control subordinate, no borrar reasoning de code agents.
Código: `authority_graph.py` + `policy_engine.py` policy `code_agent`.
Test: generate_code→preserve, agent_loop→subordinate.
Estado: **CUMPLE**

## PASADA 5 — License antes de análisis (S27)
Input: licencia STOP antes de gastar análisis.
Código: `license_auditor.py` en cabeza de `evolve_path`.
Estado: **CUMPLE**

## PASADA 6 — Placement + Source Store ≠ runtime
Input: sources/ staging vs extensions/ runtime; placement por capability.
Código: `source_store.py` + `placement.py`.
Estado: **CUMPLE (paths lógicos)** — aún no escribe archivos adapter.py en disco extensions/

## PASADA 7 — Simulation > trust_score
Input: simulación estructural, no score arbitrario.
Código: `simulation/engine.py` load/health/invoke/unload.
Estado: **CUMPLE**

## PASADA 8 — Capability Registry + UCC + discovery
Input: registry + contract + resolve + ownership priority.
Código: `capability_registry.py` register/resolve/invoke.
Estado: **PARCIAL** — falta Capability Graph requires/provides routing multi-hop

## PASADA 9 — Extensión kernel (enchufe)
Input: Wordflow como extensión kernel; Universal Plugin vía enchufe.
Código previo: `extension/abi.py`, `plugin_adapter.py` SIN evolution.
Código nuevo: `bridge_abi.py` + `extension/evolution_mount.py` + capability `evolution.evolve`.
Estado: **CUMPLE puente** — falta wiring automático en PluginAdapter.on_mount por defecto

## PASADA 10 — Gaps vs input completo (NO 100%)
| Requisito input | Estado |
|-----------------|--------|
| AST + Architecture Map | SÍ (Python) |
| Authority + Policy DSL | SÍ |
| Universal Plugin + UCC | SÍ |
| Simulation gate | SÍ |
| License auditor | SÍ |
| Registry + invoke | SÍ |
| Bridge ABI extensión | SÍ (nuevo) |
| Clone git remoto + SHA pin release | NO |
| Transplant código real adapter.py | NO |
| AST quirúrgico 1 función | NO |
| Compatibility Genome / benchmark M3 | NO |
| Quarantine branch EV-#### | NO |
| Scout + watchlist S27 | NO |
| Skill compile → DAG files | PARCIAL (plan only) |
| Dataset → bench suites | NO |
| Opportunity/Watchdog/Research | NO |
| Experience/Strategy memory | NO |
| Recipe fingerprint auto-match runtime | PARCIAL (yaml estático) |
| Capability Graph multi-hop | NO |
| Enchufe fichas HTML flujo total | NO |
| team.absorb eventos bus | NO |

## Veredicto
**Núcleo de evolución (compilador de capacidades → Universal Plugin → Registry → ABI) ≈ 70–75% del diseño operativo mínimo.**
**Sistema Transformer/Absorption S5 + PES proactivo del input largo ≈ 25–35%.**
**NO está al 100% del input completo.**

## Mejoras 100× prioritarias (orden)
1. `PluginAdapter.on_mount` auto-llama `mount_evolution`
2. Escribir package real en `extensions/<domain>/<id>/` (manifest.yaml + adapter stub)
3. Git acquire pinneado + SOURCE_MANIFEST
4. Capability Graph (requires/provides)
5. Skill → DSL/DAG files + tests path
6. team.absorb event bus hooks
7. Quarantine + ledger EV-####
8. Opportunity engine (fase posterior)
