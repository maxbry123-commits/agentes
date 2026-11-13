# YAIWES Wordflow — Azure Durable Functions

Clasificación: B — orquestador durable / state-machine executor.

Capacidad integrada: runtime DurableTask para registrar orchestrators, activities y entities, seleccionar proveedor de durabilidad, operar TaskHubWorker, mantener historial/checkpoints y servir protocolos HTTP/gRPC según el worker.

Flujo: `evento ➡️ orchestrator ➡️ DurableTask history/state ➡️ activity/entity ➡️ checkpoint/replay ➡️ resultado/evidencia`.

El código upstream útil fue movido al Wordflow; README, tests, samples y artefactos de distribución permanecen fuera. YAIWES conecta únicamente mediante adapter + Ficha v2 + Universal Plugin Bus, fail-closed.
