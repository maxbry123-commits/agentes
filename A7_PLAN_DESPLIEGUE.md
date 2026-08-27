# A7_PLAN_DESPLIEGUE.md — B7 (UOOS v2.0, Modo A)

## Auditoría inicial

Antes de desplegar el motor genérico (A4) dentro de Wordflow, se audita
el código de referencia (`acquire.py`, instancia OpenClaw) contra las
leyes L01-L15:

```yaml
auditoria_inicial:
  L02_200_lineas: "acquire.py excede 200 líneas — NO CONFORME. El motor
                    GENÉRICO (no acquire.py) debe partirse según los 28
                    nodos de A4: core.py (run/sha/log/checkpoint),
                    verify.py (01_RECEIVE_CHECKOUT–11_VERIFY_LOCK_
                    UNCHANGED, condicionales por source_type), build.py
                    (12_BUILD–17_RUNTIME_VERIFY, lee comandos de la
                    Recipe), promote.py (18_PROVENANCE–28_DONE, incluye
                    LICENSE_GATE/SECRET_SCAN) — cada uno ≤200 líneas, 1
                    responsabilidad. acquire.py queda como Recipe de
                    ejemplo (OpenClaw) que corre SOBRE este motor, no
                    como el motor."
  flags: "no existe config.py con feature flags — NO CONFORME. Se crea
          en el despliegue: ACQUIRE_OS_ENABLED=false por defecto."
  secretos: "GITHUB_AUTH/HF_AUTH ya declaran 'nunca en disco' — CONFORME,
             pendiente confirmar que el runtime real de Grok usa env
             vars y no un archivo de config con el token embebido."
  veredicto: "2 NO CONFORMES de 3 checks. Deben resolverse en el código
              final antes de F5, no después."
```

## Fases

```yaml
fases:
  F5_desplegar:
    accion: "deploy con flag apagado (dark launch)"
    equivalente_en_ACQUIRE-OS: "cada misión nueva se registra con
      ficha.estado='testing' — el módulo existe y está registrado bajo
      Contract Router/Council of 12, pero NINGÚN agente Wordflow puede
      invocarlo como nativo hasta que estado pase a 'active'"
    checklist_f5:
      - "[ ] rama nueva en el repo del kernel (nunca main)"
      - "[ ] config.py con ACQUIRE_OS_ENABLED=false"
      - "[ ] secretos confirmados en env vars del runtime de Grok"
      - "[ ] A2 (state.schema.json) desplegado como plantilla, sin misión real corriendo"
      - "[ ] smoke test definido: correr T-000→T-011 completo contra
             AL MENOS 2 source_type distintos en dry-run (ej. un
             git_native con build, y un hf_hub sin build), para probar
             que el motor genérico realmente generaliza y no solo
             reproduce el caso OpenClaw"

  F6_activar:
    accion: "smoke test OK + aprobación del Director → flag=true"
    equivalente_en_ACQUIRE-OS: "el Director ejecuta manualmente 2
      misiones reales de prueba de tipos distintos. Si T-000→T-011
      completan con AUDIT_DINAMICO PASS y Tribunal PASA en los 3 puntos
      críticos en AMBOS casos → ACQUIRE_OS_ENABLED=true, ficha pasa a
      'active' SOLO tras confirmar gpg_key_id real"
    condicion_de_bloqueo: "si solo se prueba con un source_type (ej. solo
      git_native), NO se activa — la universalidad no queda demostrada
      con un solo caso"

  F7_observar:
    accion: "métricas 24h, rollback listo"
    equivalente_en_ACQUIRE-OS: "monitorear heartbeat de mission_lock, TTL
      de fichas testing (30 días), journal.jsonl de las primeras
      misiones reales buscando patrones (alimenta L07)"
    metricas_a_observar:
      - "tasa de éxito T-000→T-011 sin recovery, DESGLOSADA por source_type"
      - "número de ASK_COUNCIL disparados por misión"
      - "locks huérfanos liberados por TTL (deberían ser 0)"
```

## Reversibilidad

```yaml
reversibilidad: "TODO revertible en <60s apagando ACQUIRE_OS_ENABLED=false
                 — ninguna misión nueva se acepta, las misiones en curso
                 terminan su nodo activo y quedan en checkpoint limpio."
plan_rollback_si_no_reversible_en_60s:
  trigger: "una misión está a mitad de T-009 (Publisher, push en curso)
            cuando se apaga el flag"
  accion: "el flag apagado NO cancela T-009 en curso — completa su lote
           actual o hace DELETE_BRANCH si falla, según su propio rollback
           (A3). El flag solo bloquea MISIONES NUEVAS."
```
