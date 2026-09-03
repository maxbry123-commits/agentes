# YAIWES — Constitución del workflow de autoevolución

Este archivo delimita el corral de trabajo de `source-evolution-workflow`. No concede autorización automática ni permite modificar otros sistemas fuera de una propuesta aprobada.

## Objetivo

Descubrir, evaluar, solicitar autorización, adquirir, adaptar, probar e incorporar capacidades sin reescribir el código fuente original.

## Flujo obligatorio

1. Watchdog recibe una orden explícita de evolución o una señal KPI comprobada.
2. Sheriff fija alcance, prohibiciones y destino.
3. Auditor X-Ray inventaría capacidades actuales y evita duplicados.
4. Investigador consulta GitHub, Hugging Face, documentación oficial y comunidad; reúne al menos 100 candidatos/señales por carril activo.
5. Validator verifica fuente, commit, licencia, seguridad, SHA y evidencia.
6. Consilio responde 12 preguntas, ejecuta 3 simulaciones y 3 refutaciones.
7. Judge clasifica la pieza: `extension-kernel`, `new-workflow`, `tools-pool` o `knowledge-skill-dataset`.
8. Sentinel crea `AWAITING_DIRECTOR`. Ninguna adquisición o montaje ocurre antes de autorización explícita.
9. GitHub Actions usa `skills/research-download-chain/SKILL.md`, escritor único, origen fijado y sin sobrescritura.
10. Sandbox prueba con red/secretos denegados; después Registry → Adapter → BUS → Schema.
11. Supervisor ejecuta pruebas individuales y E2E, hot-swap y rollback.
12. Guardian solo emite `VERIFIED_CLOSED` con cero GAPS, cero colisiones y evidencia completa.

## Límites del LLM

El LLM propone, resume evidencia y desempata como máximo el 5 %. No autoriza, descarga, monta, declara PASS ni altera la política. Las decisiones materiales deben ser reproducibles desde reglas y evidencia.

## Aprendizaje de errores

Se registran eventos estructurados, no conversaciones crudas:

- instrucción esperada y resultado observado;
- evidencia del incumplimiento o queja;
- causa raíz;
- corrección propuesta;
- prueba que evita recurrencia;
- autorización del Director;
- estado de rollback.

No se almacenan secretos, credenciales ni datos personales sin consentimiento. La memoria solo se promueve después de verificación y puede revocarse.

## Escalamiento a NCT

Si no existe código reutilizable y la corrección requiere más de 100 líneas, YAIWES no lo inventa silenciosamente. Produce arquitectura, contratos, pruebas y evidencia; solicita autorización y entrega el paquete al workflow externo NCT/Wordflow Code.

## Archivos normativos

- `EVOLUTION_GOALS_50.yaml`: 50 goals de entrada, 12 salidas, Consilio y KPI.
- `evolution_dag.yaml`: estados y transiciones.
- `EXTENSION_KERNEL_WIRING.json`: cableado con el plugin bus.
- `CAPABILITY_INDEX.json`: índice generado por auditoría.
- `CHECKPOINT-EVOLUTION.md`: historial append-only de ejecución.

## Fuentes incorporables

- SIA: lazo meta-agente → agente objetivo → feedback/mejora, MIT.
- MemOS: memoria persistente, recuperación y reutilización de skills, Apache-2.0.
- Agenvoy: tool forge, sandbox, MCP y scheduling, Apache-2.0.
- HyperAgents (Meta): solo referencia arquitectónica; CC BY-NC-SA 4.0 impide incorporarlo como dependencia general sin aprobación jurídica/directiva específica.
