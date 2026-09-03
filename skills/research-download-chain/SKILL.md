---
name: research-download-chain
description: Copia, descarga+extrae, reubica y verifica componentes mediante GitHub Actions con deduplicación, fuente fijada, SHA, ZIP por partes, manifiesto y recuperación aislada de GAPS. Úsalo cuando YAIWES, Luna u otro agente deba incorporar código sin reescribirlo.
metadata:
  type: workflow
  version: "3.0.0"
---

# Research Download Chain

Ejecuta, no te limites a explicar. Conserva el alcance literal y usa una sola modalidad por componente: `COPY`, `DOWNLOAD` o `RELOCATE`.

## 1. Entrada obligatoria

Antes de mutar, construye este objeto y detente con `INPUT_GAP` si falta un campo:

```yaml
destination_repository: owner/repo
destination_branch: main
destination_root: ruta/exacta
components:
  - name: nombre-canónico
    source_url: https://github.com/owner/repo
    source_ref: commit_sha_o_tag
    mode: COPY|DOWNLOAD|RELOCATE
    selected_paths: []
rules:
  overwrite: false
  delete: false
  reactivate_old_workflows: false
  single_writer: true
```

Normaliza URL eliminando `.git`, barra final, parámetros de rastreo y diferencias de mayúsculas solo para comparar. No cambies nombres o destinos proporcionados.

## 2. Preflight determinista

Busca antes de descargar en:

1. árbol completo de la rama destino;
2. manifiestos `*.jsonl`, `*.json`, `*.yaml` y `SOURCE_*.txt`;
3. URL normalizada, slug, nombre canónico y SHA;
4. ZIP y partes existentes;
5. runs nuevos activos o terminados para el mismo destino.

Clasificación:

- mismo origen y mismo contenido: `VERIFIED_EXISTING`;
- mismo origen en ruta distinta: `RELOCATE`;
- ausente: modalidad solicitada;
- ruta ocupada con contenido diferente: `COLLISION_BLOCKED`;
- evidencia insuficiente: `INSUFFICIENT_EVIDENCE`.

Nunca uses existencia de carpeta como prueba suficiente.

## 3. Plantillas autorizadas

No redactes de memoria workflows extensos. Copia y edita quirúrgicamente:

- `assets/FORENSIC-PASS-research-download-chain-final.yml`;
- `assets/FORENSIC-PASS-research_download_chain.py`;
- `gha-copy-files.yml`;
- `gha-move-files.yml`;
- `gha-move-root-or-files.yml`.

Cambios permitidos: nombre nuevo, trigger del archivo nuevo, fuentes, ref fijada, rutas seleccionadas, destino, contadores y nombres de manifiesto/checkpoint.

## 4. Reglas por modalidad

### COPY

Usa `actions/checkout@v4` para destino y origen. Fija `ref` al SHA resuelto. Copia con `cp -a`. Para cada archivo:

```bash
if test -e "$out"; then
  cmp -s "$src" "$out" || exit 31
else
  cp -a "$src" "$out"
fi
```

Código mayor de 100 líneas se copia desde el origen; no se reescribe.

### DOWNLOAD

Usa la plantilla y script existentes. Registra URL, ref/SHA, licencia, destino, estado, partes y hash. Divide ZIP solo si el límite real del repositorio lo exige. Verifica cada parte y la reconstrucción antes de PASS.

### RELOCATE

Mismo repositorio: `git mv` solo si la orden permite mover; si no, `cp -a` conservando origen. Entre repositorios: checkout separado y token ya configurado. No elimines el original sin autorización literal.

## 5. Concurrencia y escritura

- Un destino tiene un solo escritor.
- No permitas jobs paralelos que hagan push a la misma rama.
- Para varios componentes, copia/verifica en paralelo solo dentro de áreas temporales y realiza un único commit/push secuencial.
- Si usas jobs separados, el job final único recoge artefactos y escribe.
- `concurrency.group` debe incluir repositorio y destino; no uses un grupo global compartido por tareas no relacionadas.
- `cancel-in-progress: false`.
- Antes del push: `git pull --rebase origin <branch>`.
- Reintenta push como máximo tres veces con espera creciente. Una colisión de contenido nunca se reintenta.

## 6. Trazabilidad mínima por componente

En la raíz del componente crea sin sobrescribir:

- `SOURCE_URL.txt`;
- `SOURCE_COMMIT.txt`;
- `SOURCE_LICENSE.txt`;
- `SOURCE_SHA256SUMS.txt`;
- entrada en manifiesto/checkpoint.

Genera hashes con rutas relativas y excluye el propio manifiesto:

```bash
(cd "$root" && find . -type f ! -name SOURCE_SHA256SUMS.txt -print0 |
  sort -z | xargs -0 sha256sum > SOURCE_SHA256SUMS.txt)
(cd "$root" && sha256sum -c SOURCE_SHA256SUMS.txt)
```

## 7. GitHub Actions

Crea un workflow nuevo; nunca reactives uno fallido. Debe continuar entre componentes independientes, pero el push será único. Incluye:

1. checkout destino;
2. checkout/fetch de fuentes con SHA fijado;
3. preflight y deduplicación;
4. copia/descarga/reubicación;
5. manifiestos y hashes;
6. verificación antes de commit;
7. commit único y push seguro;
8. read-back en un job posterior cuando sea necesario.

Un job activo no es PASS. `skipped` solo es aceptable cuando el manifiesto prueba `VERIFIED_EXISTING`.

## 8. Recuperación de GAPS

Inspecciona primero job, paso y logs. Crea `repair-NN` nuevo exclusivamente para el GAP comprobado. No reejecutes ni edites el workflow viejo para ocultar historial.

Mapa de fallos:

- `fetch first/non-fast-forward`: nuevo repair con escritor único;
- `404`: comprobar fuente oficial; no sustituir sin evidencia;
- `COLLISION`: bloquear y reportar ambas huellas;
- SHA incorrecto: regenerar desde archivos reales y verificar read-back;
- parte ZIP ausente: reparar solo esa fuente/componente;
- timeout/red: retry acotado; después GAP;
- dependencia ausente: registrar, no declarar PASS.

## 9. Gate de autoevolución YAIWES

La investigación produce propuesta y estado `AWAITING_DIRECTOR`. Solo tras autorización explícita se adquiere código. Después deben pasar: licencia, sandbox, Sheriff, pasaporte, ABI/adapter, pruebas, hot-swap y rollback. El LLM propone; nunca autoriza mutaciones ni declara PASS.

## 10. Cierre obligatorio

Entrega URLs de workflow/run, destino, manifiesto y checkpoint; además:

```yaml
expected_components: N
verified_components: N
gaps: 0
skipped_without_evidence: 0
collisions: 0
active_jobs: 0
sha_check: PASS
read_back: PASS
verdict: VERIFIED_CLOSED
```

No declares `100% PASS` si hay job activo, GAP, colisión, SHA no verificado, enlace roto o evidencia incompleta.
