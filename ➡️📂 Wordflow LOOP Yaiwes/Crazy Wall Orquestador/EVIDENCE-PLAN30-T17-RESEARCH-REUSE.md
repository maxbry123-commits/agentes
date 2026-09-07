# EVIDENCE PLAN30 T17 — RESEARCH_REUSE Capability Registry

Fecha: 2026-09-07.
Contrato: `tel.workflow/v4`.
Modo: `FAIL_CLOSED_EXECUTION_LOOP`.
Nodo: `PLAN30_T17_PLUGIN_REGISTRY_WIRING`.
Paso Director: 2 — SOLO COPIAR código ya seleccionado.
HEAD pre-delta: `426ec76e849ce3f8f10382a0c11a5148ad3cbe9d`.

## Sheriff / alcance
- VERIFIED_CLOSED previos preservados: T01–T16; no se reescribió trabajo cerrado.
- Objetivo del delta: localizar un Capability Registry runtime reutilizable antes de copiar/cablear.
- Regla aplicada: RESEARCH_REUSE primero; sin donor probado no se copia ni se genera registry.

## Vías verificadas
1. `maxbry123-commits/agentes`: búsqueda `Capability Registry registry plugin slot mount_guard loader` → sin donor runtime reutilizable demostrado.
2. `maxbry123-commits/agentes`: búsqueda `engine_registry CapabilityRegistry PluginRegistry mount_guard wordflow_kernel` → 0 resultados.
3. `Agente Yaiwes principal/definition-registry`: revisado como candidato; la presencia de definiciones no demuestra runtime registry/binding.
4. Árbol recursivo de `maxbry123-commits/Agentes-motores-Wordflow-YAIWES`: revisado para `registry.py`; no se confirmó donor runtime compatible en esta pasada.
5. README arquitectura: referencia candidata `extensions/wordflow_kernel/engine_registry.py`; el archivo no quedó confirmado en HEAD actual por búsqueda de código, por lo que se clasifica `STALE_ARCH_REFERENCE_CANDIDATE` hasta inspeccionar historial Git.

## Resultado fail-closed
- `RUNTIME_REGISTRY_DONOR_NOT_PROVEN`.
- `STALE_ARCH_REFERENCE_CANDIDATE` para `extensions/wordflow_kernel/engine_registry.py`.
- No COPY, no MOVE, no REWRITE, no bus paralelo, no cambio de porcentaje.
- T17 permanece `EN_CURSO`; T18 no se habilita.

## StrategyDelta siguiente
Inspeccionar historial Git del repo principal para la ruta/referencia `extensions/wordflow_kernel/engine_registry.py` y nombres equivalentes; si aparece donor válido, registrar repo+ruta+URL+commit SHA+blob SHA+función+destino antes de COPY_ONLY. Si no existe, continuar con el siguiente repo autorizado sin inventar destino.

Estado: `ACTIVE_LOOP`.
