# PIPELINE 08 — DESPLIEGUE DETERMINISTA UNIVERSAL v2.0
## 0% LLM — Base Crítica

**Fecha:** 2026-08-09  
**Estado:** BASE CRÍTICA — REPLICAR 1:1  
**Principio:** el agente NUNCA decide cómo desplegar. Reglas fijas → script.

---

## 1. Flujo v2.0 (6 pasos)

```
[cualquier carpeta de proyecto]
   │
   ▼ PASO 0 · deploy_config.yaml   ← reglas fuera del código
   │   repos + protected_patterns (bloqueo secrets)
   │
   ▼ PASO 1 · organizar --dry-run  ← PLAN sin tocar nada
   │   plan.json · SIN_REGLA → EXIT 1 · BLOQUEADOS → EXIT 2
   │   → Director aprueba
   │
   ▼ PASO 2 · organizar + desplegar (copiar + git, idempotente)
   │
   ▼ PASO 3 · detector_version (semver por hash + CHANGELOG.md)
   │
   ▼ PASO 4 · subir (gh repo create + push)
   │
   ▼ PASO 5 · verificar (evidencia post-push)
       evidence.json {repo: {ok, hash, archivos, tag}}
       un solo ok:false → reporte exacto
```

Sin evidence.json válido → no está desplegado.

---

## 2. Orden universal al agente

```
1. python3 despliegue/organizador.py --dry-run .
   [ESPERA OK sobre plan.json]
2. python3 despliegue/desplegador.py . ./repos_listos
3. python3 despliegue/detector_version.py ./repos_listos
4. bash despliegue/subir_a_github.sh MI_USUARIO
5. python3 despliegue/verificar.py ./repos_listos
6. pega evidence.json y detente.
```

NO analizar. NO opinar. NO proponer. Solo ejecutar y reportar.

---

## 3. Delta mínimo v2.0 (~260 LOC nuevos)

- deploy_config.yaml + loader
- --dry-run + EXIT por SIN_REGLA / BLOQUEADOS
- escaneo protected_patterns
- CHANGELOG.md automático
- verificar.py (evidencia post-push)

El patrón de Sonnet (organizador + desplegador + detector + push) se reutiliza intacto.

---

## 4. Trazabilidad

- Origen: input block Director — DESPLIEGUE-DETERMINISTA-UNIVERSAL-v2.md
- Base crítica del PIPELINE. Debe replicarse 1:1.

**Estado:** listo para auditoría.
