---
name: research-download-chain
description: Copia, descarga+extrae o mueve componentes mediante GitHub Actions con deduplicación, manifiesto, SHA, ZIP por partes, trazabilidad y recuperación de GAPS. Úsalo cuando YAIWES, Luna u otro agente deba incorporar repositorios sin reescribir código.
metadata:
  type: workflow
  version: "2.0.0"
---

# Research Download Chain

Ejecuta una sola modalidad por solicitud. No inventes un empaquetador ni reactives workflows viejos.

## Contrato de entrada obligatorio

Obtén literalmente: repositorio destino, rama, carpeta destino, modalidad (copy, download, move) y lista nombre + URL. Antes de crear el workflow, busca por URL normalizada, slug y manifiesto. Si ya existe, marca RELOCATE; no lo descargues otra vez.

## Modalidades

### copy

Copia el asset gha-copy-files.yml. Usa checkout@v4 y cp -a. No Python ni LFS.

### download

Copia sin reescribir:

- assets/FORENSIC-PASS-research-download-chain-final.yml
- assets/FORENSIC-PASS-research_download_chain.py

Edita únicamente la lista de repositorios, el destino y los contadores. En repos grandes usa filter: blob:none, sparse checkout del script/manifiesto y git add --sparse.
Cada componente registra URL final, commit/SHA o revisión, destino, estado y partes ZIP. Verifica extracción, límites y SHA antes de PASS. Un 404 se registra como GAP; solo cambia a una fuente oficial alternativa con evidencia explícita.

### move

Copia gha-move-files.yml. Mismo repo: git mv o cp -a. Entre repos: token configurado + cp -a. Nunca borres documentos ni sobrescribas colisiones.

## Cola y recuperación

Usa siempre concurrency.group: research-download-chain-final. En un repo, más de dos lotes son jobs encadenados con needs e if: always(); cada lote conserva nombre y destino propios. Si falla un lote, deja continuar los demás. Al terminar, crea una reparación nueva solo con GAPS reales; no reejecutes el flujo antiguo.

## Gate YAIWES

La autoevolución solo prepara una propuesta y se detiene en AWAITING_DIRECTOR. Tras autorización explícita, este skill adquiere el componente; luego sandbox, sheriff, pasaporte, ABI y verificación deciden el montaje. El LLM no autoriza mutaciones.

## Salida mínima

Devuelve enlaces de workflow/run, manifiesto, destino y checkpoint; conteos PASS/GAP/SKIPPED; duplicados reubicados; evidencia de SHA/ZIP. No declares 100% PASS mientras exista un GAP o job activo.
