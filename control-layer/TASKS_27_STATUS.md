# Estado de las 27 tareas — Control Layer Wordflow
Branch: workflow/A1-nucleo

## Bloque A · UOOS nativo — 100%
1. schemas/project_docs.yaml ✅
2–9. templates/uoos/B1…B8 ✅
10. templates/uoos/RECETA_AGENTE.md ✅
11. config/leyes_l01_l15.yaml ✅
12. runtime/rt_states.yaml ✅
13. gates/g30_determinismo.py ✅
14. reasoning/ frontera ✅
15. contracts/evidence_l11.yaml ✅
20. uoos/INTEGRACION.md ✅

## Bloque B · Install + Despliegue — 100%
16. install/source_resolver.py ✅
17. install/policy.yaml ✅
18. despliegue/deploy_config.yaml ✅
19. despliegue/organizador.py + verificar.py ✅

## Bloque C · Contratos — 100% motor + seed
21. control/{normalizer,fingerprint,threat,rules,graph,reverse,compiler,engine}.py ✅
22. rules/routing.yaml ✅
23. contracts/C00 + INDEX + L1 C03 + L4 C33 + L5 C47 + L11 ✅ (estructura; resto on-demand)
24. sheriff/states.py ✅

## Bloque D
25. HF routing — DIFERIDO (orden Director)
26. sandbox/pool.py + api_slots.py ✅ stubs
27. gates g28 + g31 + g30 ✅ críticos IA 0%

## Nota
Los 85 contratos YAML completos se agregan por demanda (1 archivo = 1 contrato).
El motor ya selecciona por routing.yaml sin necesitar los 85 archivos presentes.
