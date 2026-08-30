---
name: research-download-chain
description: Repository-neutral deterministic download, archive, extraction, integrity, and forensic verification chain. Trigger on research-download-chain or audited download/extraction tasks. Lock to forensic assets. Do not rewrite the packer.
metadata:
  type: workflow
  version: "1.4.0"
---

# Research Download Chain — generic forensic model

## Scope
Reusable skill. It MUST NOT contain a concrete target repository, organization, project codename, workflow run, job ID, or copied repository catalog that could be mistaken for the destination of a future task. Target-specific values belong only in the task contract, manifest, or LOCK assets.

## Fuente de verdad LOCK
Leer siempre antes de ejecutar:
- `assets/FORENSIC-PASS-research-download-chain-final.yml`
- `assets/FORENSIC-PASS-research_download_chain.py`
- `references/RESEARCH-DOWNLOAD-CHAIN-AI-PLAYBOOK.json`
- `references/METODO-DE-TRABAJO.md`

Preflight obligatorio: calcular el git-blob SHA1 de los dos assets LOCK y detenerse si no coincide. Nunca reescribir el packer LOCK para resolver un fallo de ejecución.

## Parámetros
Los valores efectivos deben provenir del LOCK o del contrato de la tarea; no inventarlos ni copiarlos desde otro repositorio.
- DEST = `<TARGET_ROOT>`
- WORK = `<WORK_ROOT>`
- SRC = `<SOURCE_ROOT>`
- PACK = `<PACK_ROOT>`
- MANIFEST = `<MANIFEST_PATH>`
- ZIP pattern = `<SLUG>_<PART>.zip`

## Contrato de ejecución
1. Leer Contrato 2.
2. Leer este skill.
3. Leer los dos LOCK.
4. Comparar código real contra el contrato y el skill.
5. Ejecutar únicamente la cadena declarada por el LOCK.
6. No introducir paralelismo si el LOCK exige orden secuencial.
7. No usar Git LFS.
8. No declarar PASS por inferencia del LLM.

## Absolute no-LFS policy
- Nunca ejecutar, instalar, configurar, desinstalar o invocar LFS.
- Nunca usar `git lfs`, `GIT_LFS_*`, smudge/clean hooks, track, migrate o filtros LFS.
- Checkout: `lfs: false`.
- Las firmas `git-lfs.github.com/spec/` y `filter=lfs` pueden existir únicamente como patrones de detección forense.
- Si material generado contiene un puntero o configuración LFS: FAIL CLOSED. No sanitizarlo para convertirlo en PASS.

## Clean-room extraction
Antes de una reconstrucción auditada:
- eliminar ZIP generados anteriores;
- eliminar todos los roots de extracción declarados por el manifest;
- eliminar estado temporal de la tarea;
- impedir que `SKIP EXISTING` sea evidencia de PASS.

Una extracción existente nunca demuestra que la nueva descarga fue extraída correctamente.

## EvidenceGate
PASS exige simultáneamente:
1. manifest existente;
2. cardinalidad esperada;
3. IDs continuos según el manifest/contrato;
4. todas las filas `COMPLETE`;
5. cantidad real de partes ZIP = `manifest.parts`;
6. límite de tamaño por ZIP respetado;
7. `unzip -tq`/CRC PASS;
8. extracción realizada desde cero;
9. cada root esperado existe y contiene archivos;
10. protección contra path traversal PASS;
11. ausencia de material LFS en outputs;
12. reporte final generado por el verificador;
13. workflow final `success` en un run NUEVO posterior a la reparación;
14. commit SHA ejecutado por el run = commit reparado.

Green workflow alone != EvidenceGate PASS.

## X-RAY cross-verification
Cada objetivo debe auditarse en cinco capas independientes:
A. Código: el script implementa el comportamiento esperado.
B. Workflow: YAML llama al script y rutas correctas.
C. Commit: el run ejecuta el SHA reparado.
D. Runtime: el job ejecuta realmente los pasos previstos.
E. Resultado: manifest, ZIP, CRC, extracción, ubicación y reporte concuerdan.

PASS solo si A+B+C+D+E = PASS.

## Retry model
Un helper de retry debe ejecutar la operación real; nunca debe llamarse directamente a sí mismo.

Patrón obligatorio:
- limpiar destino temporal;
- ejecutar operación subyacente;
- `return` en éxito;
- capturar únicamente errores esperados;
- backoff acotado;
- límite de intentos;
- propagar el último error.

Preflight AST:
- localizar funciones `retry`, `retry_*`, `clone_retry` y equivalentes;
- rechazar llamada directa a sí mismas;
- ejecutar `py_compile`.

Nunca reintentar una aserción de integridad hasta convertir FAIL en PASS.

## Fresh-run rule
Después de reparar un workflow o script:
- NO usar un re-run histórico como prueba principal;
- crear un run nuevo desde el commit reparado;
- registrar `run_id`, `run_attempt` y `commit_sha`;
- comprobar que el job realmente ejecutó ese SHA.

## Failure Ledger
Antes de cada nuevo intento conservar:
```yaml
failure:
  target: "<OWNER>/<REPOSITORY>"
  workflow: "<WORKFLOW_FILE>"
  run_id: "<RUN_ID>"
  run_attempt: "<ATTEMPT>"
  commit_sha: "<SHA>"
  failed_step: "<STEP>"
  root_cause: "<ROOT_CAUSE>"
  repair_commit: "<SHA>"
  next_run_id: "<RUN_ID>"
  status: "OPEN|RESOLVED"
```

No depender únicamente de artefactos temporales de un re-run.

## Static preflight
Antes del dispatch:
1. validar YAML;
2. verificar que cada script llamado existe;
3. `py_compile` de scripts;
4. AST retry-recursion check;
5. comprobar `lfs: false`;
6. comprobar ausencia de comandos/env operativos LFS;
7. comprobar limpieza de roots;
8. comprobar que no existe `SKIP EXISTING` como condición de PASS;
9. validar esquema del manifest;
10. validar rutas de salida;
11. comprobar que no hay archivos Python bytecode generados que contaminen el scanner;
12. verificar que el scanner no se auto-bloquea por las firmas que necesita detectar.

## False-positive scanner rule
Un scanner debe distinguir entre:
- comportamiento prohibido;
- firma literal utilizada para detectar comportamiento prohibido.

Nunca hacer un `grep` ciego de una firma contra el propio detector si eso provoca que el detector se marque a sí mismo como infracción. Preferir análisis de contexto, AST o exclusiones explícitas del archivo detector.

## Archive verification
Para cada ZIP:
- existe;
- tamaño dentro del límite;
- cantidad coincide con manifest;
- CRC PASS;
- `unzip -tq` PASS;
- no contiene rutas que escapen del root;
- se extrae en root limpio.

Si cualquiera falla: FAIL CLOSED.

## Repository-neutrality rule
Este documento debe permanecer genérico. No insertar aquí:
- nombres de repositorios concretos;
- URLs de repositorios destino;
- IDs históricos de runs/jobs;
- nombres de proyectos específicos;
- rutas absolutas específicas de otro proyecto;
- catálogos copiados de una tarea anterior.

Los valores específicos deben vivir en `<MANIFEST_PATH>`, contrato o LOCK correspondiente.

## LOOP operativo
```text
inspect
→ evidence
→ root cause
→ patch
→ static validation
→ commit
→ fresh run
→ wait
→ X-RAY
→ EvidenceGate
→ PASS?
   NO → volver al primer fallo
   SÍ → siguiente objetivo
```

El LOOP termina únicamente cuando todos los objetivos declarados por el contrato tienen EvidenceGate PASS. No escalar ni declarar finalización prematura.
