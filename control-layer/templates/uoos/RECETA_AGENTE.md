# RECETA_AGENTE — Contrato universal (D10)
# SOURCE: cualquier agente compatible · no receta de un agente concreto
# El Wordflow entrega ExecutionContext; el agente ejecuta y devuelve evidencia.

## Contrato (8 pasos obligatorios)

1. **Recibir ExecutionContext**  
   tenant_id · project_id · agent_id · agent_version · workflow_id · task_id · session_id · memory scopes

2. **Verificar identidad**  
   agent_id del contexto == el declarado en nodes/*.yaml registrado

3. **Leer instrucciones del workflow**  
   DAG / recipe del workflow_id (QUÉ FLUJO), no improvisar

4. **Consultar memoria autorizada**  
   Solo private_scope y project_scope del contexto. Nunca namespace ajeno.

5. **Ejecutar tarea**  
   Dentro de permisos/tools del agent YAML y sandbox declarado

6. **Validar resultado**  
   criterio_exito verificable por máquina

7. **Registrar experiencia**  
   evidencia + delta (L11); no definir agentes en state.json

8. **Entregar resultado al Control Layer**  
   stdout/stderr/exit_code/artifacts + evidence_output del Adapter

## Separación

| Pieza | Significa |
|-------|-----------|
| NODE (nodes/*.yaml) | QUIÉN |
| DAG | QUÉ FLUJO |
| LOOP | CÓMO REPETIR |
| MEMORY | QUÉ RECORDAR (scopes del contexto) |
| SHERIFF | QUÉ ESTÁ PERMITIDO |

## Prohibido
- Inventar agent_id no descubierto/registrado
- Acceder memoria de otro project/agent
- Escribir secretos en repo
- Saltar DAG o Sheriff
- Código from-scratch si existe source

## Checklist
- [ ] ExecutionContext presente y completo
- [ ] capabilities cubren required_capabilities del paso DAG
- [ ] evidence con campos L11
- [ ] memory solo scopes autorizados
