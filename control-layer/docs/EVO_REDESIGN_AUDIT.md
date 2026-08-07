# Evolution Engine v2 · Rediseño (auditoría)

## Objetivo
No instalar agentes. **Absorber conocimiento operativo → Universal Plugin → kernel.**

## Flujo implementado (código)
```
SOURCE hints/components
  → EvoIR
  → Authority classification (cognitive|execution|control|state|presentation)
  → Policy Engine (code_agent|workflow|skill|default)
  → TransformationPlan
  → Placement Engine (extensions/<domain>/...)
  → UniversalPlugin + CapabilityContract (UCC)
  → SimulationEngine (load/health/invoke/unload)
  → EvolutionManifest (receta reproducible)
```

## Módulos nuevos
| Módulo | Rol |
|--------|-----|
| evo_ir.py | IR única |
| authority.py | Authority graph + señales |
| policy.py | Policy DSL + CODE_AGENT_POLICY |
| placement.py | Taxonomía extensions/ |
| universal_plugin.py | ABI plugin + UCC |
| simulation.py | Gate estructural |
| compiler.py | Orquestador |

## Qué NO está aún (honesto)
- AST/callgraph real sobre repo clonado
- License auditor / scout / donor cache (S27)
- Generación de código de handlers (code workers)
- Capability Registry wiring + discovery
- Opportunity/Watchdog proactivo
- Research Registry internet
- Recipe learning automático

## Reglas codificadas
1. Kernel solo consume UniversalPlugin
2. Code agent: preserve cognitive, subordinate control
3. Simulación > trust_score arbitrario
4. Placement por capability namespace, no por path del donante
