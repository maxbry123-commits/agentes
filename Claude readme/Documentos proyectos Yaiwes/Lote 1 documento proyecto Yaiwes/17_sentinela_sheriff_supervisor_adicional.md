# DOCUMENTO 3/4 — Sentinela, Sheriff, Supervisor, Validador: 10 componentes adicionales
**Objetivo: que el LLM nunca pueda desviar al agente de los pasos definidos — control real, no una sugerencia**

Ya tenías: Open Policy Agent, Cerbos, Casbin, Guardrails AI, NeMo Guardrails, Llama Guard, Presidio. Aquí hay 10 más, con foco específico en **detectar cuando el LLM se desvía**, que es justo lo que tu propio sistema P1 ("Anti-Deriva") ya busca hacer a mano.

| # | Componente | Qué detecta/controla | Cómo se integra | Dónde vive |
|---|---|---|---|---|
| 1 | **Rebuff** | Inyección de prompt — detecta cuando una entrada intenta manipular las instrucciones del sistema | Se coloca como filtro obligatorio ANTES de `decision-on-demand` — si detecta inyección, rechaza sin llamar al LLM | `control-governance/sheriff-sentinel-council/` |
| 2 | **LLM Guard** (Protect AI) | Suite de escáneres para prompts Y salidas — detecta fugas de secretos, toxicidad, y más en ambos lados | Se coloca en dos puntos: antes de enviar el prompt, y después de recibir la respuesta del LLM | `control-governance/llm-control-deny/` |
| 3 | **Vigil** | Detección de inyección de prompt con firmas y modelos de clasificación | Alternativa/complemento a Rebuff — puedes correr ambos y exigir que los dos aprueben | `control-governance/sheriff-sentinel-council/` |
| 4 | **OPA Gatekeeper** (la variante de Kubernetes de Open Policy Agent) | Valida Y modifica (mutating admission) una acción antes de dejarla pasar, no solo la aprueba/rechaza | Úsalo cuando necesites que el gate no solo diga sí/no, sino que corrija automáticamente algo pequeño antes de aprobar | `control-governance/policy-engine/` |
| 5 | **Semgrep** | Análisis estático de código — detecta patrones peligrosos (inyección SQL, `eval`, secretos hardcodeados) en el código que el agente genera | Corre automáticamente sobre cualquier código generado ANTES de ejecutarlo, no después | `execution-engine-pool/mount-guard/` (o un paso previo a la ejecución) |
| 6 | **Great Expectations** | Validación de datos — define "expectativas" formales sobre qué forma deben tener los datos en cada paso de un pipeline | Úsalo en cualquier punto donde el LLM produzca datos estructurados que alimentan el siguiente paso — detecta si "inventó" un campo o cambió un formato | `execution-orchestration/deterministic-execution/` |
| 7 | **Detoxify** | Clasificador de toxicidad open source, alternativa ligera a APIs de moderación comerciales | Filtro rápido y barato antes de escáneres más pesados como LLM Guard | `control-governance/sheriff-sentinel-council/` |
| 8 | **Constitutional AI (patrón, no librería)** | El propio modelo se autocritica contra una "constitución" escrita explícitamente, antes de responder | Escribe tu propia constitución corta (tus 13 Leyes de Sonnet ya son literalmente esto) y pide una segunda pasada del LLM que verifique cumplimiento antes del Coda | `reasoning-kernel/decision-on-demand/` (paso final, antes de entregar) |
| 9 | **OpenTelemetry + alertas (Prometheus/Grafana)** | No detecta contenido — detecta COMPORTAMIENTO anómalo: de repente el agente tarda 10x más, o llama a una herramienta con 10x más frecuencia de lo normal | Esto es tu "supervisor" en el sentido más literal: observa métricas, no texto, y dispara alertas cuando algo se sale de rango | `observability/trace-history/` |
| 10 | **Anti-Corruption Layer + Contract Testing combinados (Schemathesis)** | Verifica que cada respuesta del LLM cumple EXACTAMENTE el contrato de salida declarado, generando casos de prueba automáticamente | Es tu último filtro antes de que cualquier salida del LLM se considere válida — si no cumple el contrato exacto, se rechaza sin excepciones | `definition-registry/schema-contracts/` |

## Cómo se ordenan estos 10 + los 7 que ya tenías (la cadena completa de sentinelas)

```
Prompt entra
  → Rebuff + Vigil (detectan inyección) — rechaza si hay ataque
  → LLM Guard (escanea el prompt) — rechaza si hay fuga de secretos
  → [LLM genera respuesta]
  → LLM Guard (escanea la salida) — rechaza si hay toxicidad/fuga
  → Detoxify (segunda opinión rápida sobre toxicidad)
  → Constitutional AI check (¿cumple las Leyes/Constitución declarada?)
  → Schemathesis / Great Expectations (¿cumple el contrato de datos exacto?)
  → Semgrep (si generó código: ¿tiene patrones peligrosos?)
  → OPA / OPA Gatekeeper (¿la acción está permitida por política?)
  → OpenTelemetry (registra todo, alerta si el patrón de uso es anómalo)
  → Solo si TODO pasó: se ejecuta / se entrega
```

Esta cadena es tu **Sheriff Council** completo — cada eslabón puede rechazar sin que los siguientes se ejecuten (fail-closed real), y ninguno de estos 10 necesita que tú escribas su lógica interna: todos son librerías reales, instalables hoy.

## Resumen

Tu propio sistema P1 ("Anti-Deriva": comparar objetivo declarado vs respuesta generada, detectar trabajo no solicitado) ya identificó el problema correcto — estos 10 componentes son las herramientas reales que hacen exactamente eso, con código probado en producción por otros, en vez de que tengas que escribir cada detector desde cero.
