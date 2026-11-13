# TimesFM — Native Temporal Intelligence / YAIWES

Estado: `GAP_PENDING_MODEL_RUNTIME_E2E`.

Arquitectura:
`YAIWES Agent → Kernel → Capability Router → decision policy → temporal.forecast → TimesFM adapter → Router Inteligente Universal / AI Staff → TimesFM runtime → structured result → Kernel → Agent`.

Esta integración conserva solo la capa ligera oficial de `google-research/timesfm`; **no** almacena pesos del modelo.

Capacidades registradas:
- `temporal.forecast` — capability externa.
- `temporal.anomaly_from_intervals` — capability derivada; TimesFM no incorpora anomaly detection nativa.

Regla de decisión: el forecast es evidencia para el Kernel/Agente, nunca una orden automática para una acción crítica.

Transportes del adapter:
- `TIMESFM_SERVICE_URL`: API/local service JSON.
- `TIMESFM_MCP_PROXY_URL`: proxy MCP controlado por YAIWES/Router.
- `TIMESFM_LOCAL_COMMAND`: proceso local que recibe JSON por stdin.
- `TIMESFM_MODEL_ID`: metadata del runtime; default de integración `google/timesfm-3.0-pytorch`.

Fail-closed:
- historial insuficiente → no se invoca TimesFM;
- runtime no configurado/no disponible → `capability_unavailable`;
- respuesta sin `point_forecast` o `quantiles` → contrato inválido;
- la integración no se declara PASS hasta inferencia real contra el runtime del Router Inteligente Universal.
