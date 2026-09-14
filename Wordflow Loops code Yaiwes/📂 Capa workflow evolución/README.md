# Autoevolución nativa YAIWES

Motor de propuesta determinista conectado al módulo existente `source-evolution-module`.
No instala ni modifica componentes por sí solo: termina obligatoriamente en
`AWAITING_DIRECTOR`. Tras autorización explícita, el DAG delega la adquisición al
skill canónico `skills/research-download-chain/SKILL.md`, verifica fuente/SHA/ZIP,
ejecuta sandbox y monta mediante ABI.

## Decisión de ubicación

1. Capacidad determinista: `kernel-principal/extension-kernel/`.
2. Secuencia fija: `multi-workflow-engine/instances/`.
3. Razonamiento o memoria autónoma: `execution-engine-pool/` aislado.
4. Conocimiento sin ejecución: `skills/` o dataset.

El modo poda elimina el bucle decisor externo y conserva la capacidad detrás de
un adaptador ABI. Está prohibido importar código externo directamente en el kernel.

## Uso

`python evolution_engine.py "evolucionar X" facts.json --out proposal.json`

El resultado incluye huella, 12 objetivos de entrada, 12 de salida, 12 preguntas
de Consilio, destino, modo, evidencia faltante y el gate del director.

## Cableado

`watchdog → schema/sheriff → reuse_12 → research → Consilio-12 → classify →
proposal → AWAITING_DIRECTOR → research-download-chain → sandbox → ABI mount → verify`.
