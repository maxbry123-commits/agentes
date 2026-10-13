# RECETA_AGENTE — Contrato universal D10 v2.0
# SOURCE: ExecutionContext · AgentAdapter · D1–D9 · 0% inventar identidad
# Universal: cualquier agente (temporal, openclaw, custom) usa el mismo contrato.

```yaml
schema_version: "2.0"
kind: RECETA_AGENTE
```

## Contrato (8 pasos obligatorios)

1. **Recibir ExecutionContext**  
   `tenant_id · project_id · agent_id · task_id · run_id · goal_id · loop_id ·
   workflow_id · session_id · memory scopes · capability · strategy`

2. **Verificar identidad**  
   `agent_id` del contexto ∈ nodes/*.yaml registrados (NodesLoader / Registry)

3. **Leer flujo**  
   DAG paso actual (`required_capabilities`) + plan del loop si aplica — no improvisar orden

4. **Memoria autorizada**  
   Solo scopes del contexto (loop/task/agent/project/strategy). Nunca namespace ajeno.

5. **Ejecutar**  
   Dentro de `permissions.tools` + sandbox + budget del agent YAML / phase_handlers

6. **Validar**  
   Criterio de éxito **verificable por máquina** (tests, schema, sheriff)

7. **Registrar experiencia**  
   evidence + delta; StrategyMemory/ResultCache vía engine — no defs en state.json

8. **Entregar al Control Layer**  
   `AgentExecResult{ok, output, error, tokens_used}` + artifacts/evidence

## Separación de responsabilidades

| Pieza | Significa |
|-------|-----------|
| D1 Manifest | identidad proyecto |
| D2 state | estado vivo |
| D3 nodes | QUIÉN |
| D4 DAG | QUÉ FLUJO |
| D5 loops | CÓMO REPETIR |
| D6 council | gobierno/voto |
| D8 recovery | qué hacer al fallar |
| D9 config | token/repo/backup/deploy |
| D10 RECETA | contrato de trabajo del agente |
| MEMORY | scopes del contexto |
| SHERIFF | qué está permitido |

## Prohibido
- Inventar `agent_id` no registrado
- Acceder memoria de otro project/agent
- Secretos en repo
- Saltar DAG / Sheriff / fases required
- Código from-scratch si existe source en sources/
- Decidir despliegue (solo scripts D9/despliegue)

## Checklist pre-ejecución
- [ ] ExecutionContext completo
- [ ] capabilities ⊇ required_capabilities del paso DAG
- [ ] evidence campos mínimos (run_id, timestamps, archivos, tests)
- [ ] memory solo scopes autorizados
- [ ] budget no exhausted
