# OpenAgentSkill — capa de selección automática

## Datos básicos
- **URL canónica**: `github.com/openagentskill/oas` (a confirmar)
- **Tipo**: capa, NO un registry más
- **Función**: envolver N bibliotecarios y elegir automáticamente

## Cómo funciona
OpenAgentSkill no es un registry independiente: es un **selector**. Dado:
- Un agente con un `agent_card` (qué sabe hacer, qué tools tiene).
- Una tarea entrante.

Devuelve: "cargá esta skill de este bibliotecario, con este confidence score".

## Diferencia con el AI Registry
- **AI Registry** (nuestro) = capa intermedia sobre los 12 registries locales.
- **OpenAgentSkill** = capa que mira registries **externos** (los 4 bibliotecarios + otros).

Son ortogonales. OpenAgentSkill alimenta a nuestro `02-skill` registry, y el AI Registry consume ese registry local.

## Plan de integración
1. Correr OpenAgentSkill en HF Space (no en sandbox).
2. Apuntarlo a los 4 bibliotecarios como fuentes.
3. Su output → JSON Lines en `02-skill/incoming/`.
4. Nuestro sync engine los procesa y decide upsert.

## Pendiente
- [ ] Confirmar si OpenAgentSkill usa OpenAI function-calling o un esquema propio.
- [ ] Evaluar la calidad de sus recomendaciones vs las nuestras (comparar top-5).
- [ ] Latencia: ¿es sub-100ms por recomendación?
